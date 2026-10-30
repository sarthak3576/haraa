from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from app import config
from app.services.dashboard_service import log_waste_event
from app.services.image_utils import InvalidImageError, load_and_normalize_image, make_thumbnail_b64
from app.services.ml_classifier import ModelUnavailable, classify_image, model_is_ready
from app.services.nearby_centres_data import DASHBOARD_CATEGORY_TO_NEARBY_ID
from app.services.rekognition_service import detect_waste_type
from app.services.scan_history_service import mark_scan_logged, save_scan
from app.services.waste_categories import ALL_CATEGORIES, DEFAULT_WEIGHT_KG
from app.templating import templates

router = APIRouter()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def _empty_context(request, **overrides):
    context = {
        "request": request,
        "result": None,
        "error": None,
        "default_weight": DEFAULT_WEIGHT_KG,
        "logged": False,
        "model_ready": config.LOCAL_ML_ENABLED and model_is_ready(),
        "nearby_map": DASHBOARD_CATEGORY_TO_NEARBY_ID,
    }
    context.update(overrides)
    return context


@router.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    if not request.session.get("user_email"):
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request, "upload.html", _empty_context(request))


@router.post("/upload", response_class=HTMLResponse)
async def upload_submit(request: Request, photo: UploadFile = File(...)):
    if not request.session.get("user_email"):
        return RedirectResponse("/login", status_code=303)

    raw_bytes = await photo.read()
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        return templates.TemplateResponse(request, "upload.html", _empty_context(
            request, error="Image is too large (max 10 MB). Please upload a smaller photo."))

    try:
        image, jpeg_bytes = load_and_normalize_image(raw_bytes)
    except InvalidImageError as exc:
        return templates.TemplateResponse(request, "upload.html", _empty_context(request, error=str(exc)))

    result = None
    error = None
    if not config.LOCAL_ML_ENABLED:
        # Deployed (Lambda) mode: the local model isn't shipped here, so go
        # straight to the same Rekognition path used locally as a fallback.
        try:
            rekognition_result = detect_waste_type(jpeg_bytes)
            result = {
                "engine": "Amazon Rekognition",
                "category": rekognition_result["category"],
                "confidence": rekognition_result["confidence"],
                "matched_label": rekognition_result["matched_label"],
                "top3": [],
                "all_labels": rekognition_result["all_labels"],
            }
        except Exception as exc:  # noqa: BLE001
            error = f"Classification failed: {exc}"
    else:
        try:
            ml_result = classify_image(image)
            if ml_result["meets_threshold"]:
                result = {
                    "engine": "Local ML model (MobileNetV3)",
                    "category": ml_result["category"],
                    "confidence": ml_result["confidence"],
                    "matched_label": ml_result["class_name"],
                    "top3": ml_result["top3"],
                    "all_labels": [],
                }
            else:
                try:
                    rekognition_result = detect_waste_type(jpeg_bytes)
                    result = {
                        "engine": f"Amazon Rekognition (local model was only {ml_result['confidence']}% confident)",
                        "category": rekognition_result["category"],
                        "confidence": rekognition_result["confidence"],
                        "matched_label": rekognition_result["matched_label"],
                        "top3": ml_result["top3"],
                        "all_labels": rekognition_result["all_labels"],
                    }
                except Exception:
                    result = {
                        "engine": f"Local ML model (MobileNetV3 - {ml_result['confidence']}%)",
                        "category": ml_result["category"],
                        "confidence": ml_result["confidence"],
                        "matched_label": ml_result["class_name"],
                        "top3": ml_result["top3"],
                        "all_labels": [],
                    }
        except ModelUnavailable:
            try:
                rekognition_result = detect_waste_type(jpeg_bytes)
                result = {
                    "engine": "Amazon Rekognition (local model not trained yet)",
                    "category": rekognition_result["category"],
                    "confidence": rekognition_result["confidence"],
                    "matched_label": rekognition_result["matched_label"],
                    "top3": [],
                    "all_labels": rekognition_result["all_labels"],
                }
            except Exception as exc:  # noqa: BLE001
                error = f"Neither the local model nor Rekognition were available: {exc}"
        except Exception as exc:  # noqa: BLE001
            error = f"Classification failed: {exc}"

    if result:
        request.session["last_result"] = result
        try:
            thumbnail_b64 = make_thumbnail_b64(image)
            scan_id = save_scan(
                user_email=request.session["user_email"],
                thumbnail_b64=thumbnail_b64,
                category=result["category"],
                confidence=result["confidence"],
            )
            request.session["last_scan_id"] = scan_id
        except Exception:  # noqa: BLE001 -- scan history is a nice-to-have, never block the result
            request.session.pop("last_scan_id", None)

    return templates.TemplateResponse(request, "upload.html", _empty_context(
        request, result=result, error=error))


@router.post("/upload/log", response_class=HTMLResponse)
def log_result(request: Request, category: str = Form(...), weight_kg: float = Form(...)):
    if not request.session.get("user_email"):
        return RedirectResponse("/login", status_code=303)

    if category not in ALL_CATEGORIES:
        category = "other"

    result = request.session.get("last_result")
    confidence = result.get("confidence", 0.0) if result else 0.0

    log_waste_event(
        category=category,
        weight_kg=weight_kg,
        user_email=request.session["user_email"],
        source="photo",
        confidence=confidence,
    )

    scan_id = request.session.get("last_scan_id")
    if scan_id:
        try:
            mark_scan_logged(request.session["user_email"], scan_id)
        except Exception:  # noqa: BLE001
            pass

    request.session.pop("last_result", None)
    request.session.pop("last_scan_id", None)

    return templates.TemplateResponse(request, "upload.html", _empty_context(request, logged=True))
