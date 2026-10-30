import json
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from app.templating import templates

router = APIRouter()

ML_MODEL_DIR = Path(__file__).resolve().parent.parent / "ml_model"


@router.get("/model-performance", response_class=HTMLResponse)
def model_performance_page(request: Request):
    if not request.session.get("user_email"):
        return RedirectResponse("/login", status_code=303)

    metrics_path = ML_MODEL_DIR / "metrics.json"
    metrics = json.loads(metrics_path.read_text()) if metrics_path.exists() else None

    per_class = []
    if metrics:
        for class_name, m in metrics["classification_report"].items():
            if class_name in ("accuracy", "macro avg", "weighted avg"):
                continue
            per_class.append({
                "class_name": class_name,
                "precision": round(m["precision"], 3),
                "recall": round(m["recall"], 3),
                "f1": round(m["f1-score"], 3),
                "support": int(m["support"]),
            })

    return templates.TemplateResponse(request, "model_performance.html", {
        "request": request,
        "metrics": metrics,
        "per_class": per_class,
    })
