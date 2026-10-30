"""
Loads the locally fine-tuned MobileNetV3-Large waste classifier (trained by
ml/train.py, artifacts synced into app/ml_model/) and runs inference on an
uploaded photo. This is the FIRST classifier the upload endpoint tries;
Rekognition is used only as a fallback when this model's top confidence is
below CONFIDENCE_THRESHOLD, or when the local model isn't available at all.
"""
import json
import threading
from functools import lru_cache
from pathlib import Path

from PIL import Image

MODEL_DIR = Path(__file__).resolve().parent.parent / "ml_model"
CONFIDENCE_THRESHOLD = 60.0  # percent

_lock = threading.Lock()


class ModelUnavailable(Exception):
    pass


@lru_cache
def _load():
    import torch
    from torchvision import models, transforms

    weights_path = MODEL_DIR / "waste_classifier.pt"
    labels_path = MODEL_DIR / "labels.json"
    if not weights_path.exists() or not labels_path.exists():
        raise ModelUnavailable(
            "Local model artifacts not found -- run ml/train.py first."
        )

    labels = json.loads(labels_path.read_text())
    class_names = labels["classes"]
    image_size = labels["image_size"]

    model = models.mobilenet_v3_large(weights=None)
    in_features = model.classifier[-1].in_features
    import torch.nn as nn
    model.classifier[-1] = nn.Linear(in_features, len(class_names))

    state_dict = torch.load(weights_path, map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()

    device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
    model.to(device)

    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(image_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=labels["normalize_mean"], std=labels["normalize_std"]),
    ])

    return model, transform, device, labels


def classify_image(pil_image: Image.Image) -> dict:
    """
    Returns:
      {
        "available": True,
        "category": <dashboard category>,
        "class_name": <raw model class>,
        "confidence": <0-100 float>,
        "top3": [{"class_name":..., "category":..., "confidence":...}, ...],
        "meets_threshold": bool,
      }
    Raises ModelUnavailable if the model hasn't been trained/synced yet.
    """
    import torch

    with _lock:
        model, transform, device, labels = _load()

    image = pil_image.convert("RGB")
    tensor = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1)[0].cpu()

    class_names = labels["classes"]
    category_map = labels["class_to_dashboard_category"]

    top_probs, top_idx = torch.topk(probs, k=min(3, len(class_names)))
    top3 = [
        {
            "class_name": class_names[i],
            "category": category_map.get(class_names[i], "other"),
            "confidence": round(float(p) * 100, 1),
        }
        for p, i in zip(top_probs.tolist(), top_idx.tolist())
    ]

    best = top3[0]
    return {
        "available": True,
        "category": best["category"],
        "class_name": best["class_name"],
        "confidence": best["confidence"],
        "top3": top3,
        "meets_threshold": best["confidence"] >= CONFIDENCE_THRESHOLD,
    }


def model_is_ready() -> bool:
    return (MODEL_DIR / "waste_classifier.pt").exists() and (MODEL_DIR / "labels.json").exists()
