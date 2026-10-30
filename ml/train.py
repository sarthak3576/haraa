"""
Fine-tunes a pretrained MobileNetV3-Large on the TrashNet split produced by
split_dataset.py, using two-phase transfer learning:

  Phase 1 (head-only): backbone frozen, train the new classifier head.
  Phase 2 (fine-tune):  unfreeze the whole network, train at a lower LR.

Run inside ml/.venv (Python 3.12, has torch/torchvision installed):
    ml/.venv/bin/python ml/train.py

Outputs (all under ml/model/):
  waste_classifier.pt       - state dict of the fine-tuned model
  labels.json                - index -> class name, and class -> dashboard category
  metrics.json                - full training report (accuracy, per-class P/R/F1, etc)
  confusion_matrix.png
  training_curves.png
  sample_predictions.png
  classification_report.txt

It then copies the inference-time artifacts (weights, labels, metrics) into
app/ml_model/ and the report images into app/static/model_report/ so the
FastAPI app (running in its own venv) can use and display them without
needing scikit-learn/matplotlib itself.
"""
import json
import shutil
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import classification_report, confusion_matrix
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

ML_DIR = Path(__file__).resolve().parent
APP_DIR = ML_DIR.parent / "app"
DATA_DIR = ML_DIR / "data_split"
MODEL_DIR = ML_DIR / "model"
MODEL_DIR.mkdir(exist_ok=True)

IMAGE_SIZE = 224
BATCH_SIZE = 32
PHASE1_EPOCHS = 4
PHASE2_EPOCHS = 10
PHASE1_LR = 1e-3
PHASE2_LR = 1e-4

# TrashNet's own classes mapped onto this app's dashboard categories.
# TrashNet has no organic/e-waste class, which is a known limitation
# documented in the Model Performance page and the project report.
CLASS_TO_DASHBOARD_CATEGORY = {
    "cardboard": "paper",
    "glass": "glass",
    "metal": "metal",
    "paper": "paper",
    "plastic": "plastic",
    "trash": "other",
}


def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def build_dataloaders():
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])

    train_tfms = transforms.Compose([
        transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.75, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        normalize,
    ])
    eval_tfms = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMAGE_SIZE),
        transforms.ToTensor(),
        normalize,
    ])

    train_ds = datasets.ImageFolder(DATA_DIR / "train", transform=train_tfms)
    val_ds = datasets.ImageFolder(DATA_DIR / "val", transform=eval_tfms)
    test_ds = datasets.ImageFolder(DATA_DIR / "test", transform=eval_tfms)

    assert train_ds.classes == val_ds.classes == test_ds.classes

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    return train_loader, val_loader, test_loader, train_ds.classes


def build_model(num_classes: int):
    weights = models.MobileNet_V3_Large_Weights.DEFAULT
    model = models.mobilenet_v3_large(weights=weights)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, num_classes)
    return model


def run_epoch(model, loader, criterion, optimizer, device, train: bool):
    model.train() if train else model.eval()
    total_loss, total_correct, total_n = 0.0, 0, 0

    with torch.set_grad_enabled(train):
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            if train:
                optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            if train:
                loss.backward()
                optimizer.step()

            total_loss += loss.item() * images.size(0)
            total_correct += (outputs.argmax(1) == labels).sum().item()
            total_n += images.size(0)

    return total_loss / total_n, total_correct / total_n


def train_phase(model, train_loader, val_loader, device, epochs, lr, history):
    optimizer = torch.optim.Adam(
        [p for p in model.parameters() if p.requires_grad], lr=lr
    )
    class_counts = np.bincount([y for _, y in train_loader.dataset.samples])
    weights = torch.tensor(class_counts.sum() / (len(class_counts) * class_counts), dtype=torch.float32).to(device)
    criterion = nn.CrossEntropyLoss(weight=weights)

    best_val_acc = history.get("best_val_acc", 0.0)
    best_state = history.get("best_state")

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        train_loss, train_acc = run_epoch(model, train_loader, criterion, optimizer, device, train=True)
        val_loss, val_acc = run_epoch(model, val_loader, criterion, optimizer, device, train=False)
        dt = time.time() - t0

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

        print(f"  epoch {epoch}/{epochs}  train_loss={train_loss:.4f} train_acc={train_acc:.4f}  "
              f"val_loss={val_loss:.4f} val_acc={val_acc:.4f}  ({dt:.1f}s)")

    history["best_val_acc"] = best_val_acc
    history["best_state"] = best_state
    return history


def plot_training_curves(history, path: Path):
    epochs = range(1, len(history["train_loss"]) + 1)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    axes[0].plot(epochs, history["train_loss"], label="train")
    axes[0].plot(epochs, history["val_loss"], label="val")
    axes[0].axvline(history["phase1_epochs"], color="gray", linestyle="--", linewidth=1, label="unfreeze")
    axes[0].set_title("Loss")
    axes[0].set_xlabel("epoch")
    axes[0].legend()

    axes[1].plot(epochs, history["train_acc"], label="train")
    axes[1].plot(epochs, history["val_acc"], label="val")
    axes[1].axvline(history["phase1_epochs"], color="gray", linestyle="--", linewidth=1, label="unfreeze")
    axes[1].set_title("Accuracy")
    axes[1].set_xlabel("epoch")
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def plot_confusion_matrix(cm, class_names, path: Path):
    fig, ax = plt.subplots(figsize=(6, 5.5))
    im = ax.imshow(cm, cmap="Greens")
    ax.set_xticks(range(len(class_names)))
    ax.set_yticks(range(len(class_names)))
    ax.set_xticklabels(class_names, rotation=45, ha="right")
    ax.set_yticklabels(class_names)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Confusion matrix (test set)")

    thresh = cm.max() / 2
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                     color="white" if cm[i, j] > thresh else "black")

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def plot_sample_predictions(model, test_loader, class_names, device, path: Path, n=12):
    model.eval()
    images_shown, preds_shown, labels_shown = [], [], []

    mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)

    with torch.no_grad():
        for images, labels in test_loader:
            outputs = model(images.to(device))
            preds = outputs.argmax(1).cpu()
            for i in range(images.size(0)):
                if len(images_shown) >= n:
                    break
                images_shown.append(images[i])
                preds_shown.append(preds[i].item())
                labels_shown.append(labels[i].item())
            if len(images_shown) >= n:
                break

    cols = 4
    rows = (len(images_shown) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 2.6, rows * 2.8))
    axes = axes.flatten() if rows * cols > 1 else [axes]

    for ax, img, pred, true in zip(axes, images_shown, preds_shown, labels_shown):
        unnorm = img * std + mean
        unnorm = unnorm.clamp(0, 1).permute(1, 2, 0).numpy()
        ax.imshow(unnorm)
        correct = pred == true
        ax.set_title(f"pred: {class_names[pred]}\ntrue: {class_names[true]}",
                     color="green" if correct else "red", fontsize=9)
        ax.axis("off")

    for ax in axes[len(images_shown):]:
        ax.axis("off")

    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main():
    device = get_device()
    print(f"Using device: {device}")

    train_loader, val_loader, test_loader, class_names = build_dataloaders()
    print(f"Classes: {class_names}")
    print(f"Train/val/test sizes: {len(train_loader.dataset)}/{len(val_loader.dataset)}/{len(test_loader.dataset)}")

    model = build_model(num_classes=len(class_names)).to(device)

    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": [], "best_val_acc": 0.0, "best_state": None}

    print("\nPhase 1: training classifier head (backbone frozen)")
    for param in model.features.parameters():
        param.requires_grad = False
    history = train_phase(model, train_loader, val_loader, device, PHASE1_EPOCHS, PHASE1_LR, history)
    history["phase1_epochs"] = PHASE1_EPOCHS

    print("\nPhase 2: fine-tuning the full network")
    for param in model.features.parameters():
        param.requires_grad = True
    history = train_phase(model, train_loader, val_loader, device, PHASE2_EPOCHS, PHASE2_LR, history)

    # restore best checkpoint (by val accuracy) before final evaluation
    model.load_state_dict(history["best_state"])

    print("\nEvaluating on held-out test set...")
    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
        for images, labels in test_loader:
            outputs = model(images.to(device))
            all_preds.extend(outputs.argmax(1).cpu().tolist())
            all_labels.extend(labels.tolist())

    test_acc = float(np.mean(np.array(all_preds) == np.array(all_labels)))
    report = classification_report(all_labels, all_preds, target_names=class_names, output_dict=True)
    report_text = classification_report(all_labels, all_preds, target_names=class_names)
    cm = confusion_matrix(all_labels, all_preds)

    print(f"\nTest accuracy: {test_acc:.4f}")
    print(report_text)

    # --- save artifacts ---
    torch.save(model.state_dict(), MODEL_DIR / "waste_classifier.pt")

    labels_payload = {
        "classes": class_names,
        "class_to_dashboard_category": CLASS_TO_DASHBOARD_CATEGORY,
        "image_size": IMAGE_SIZE,
        "normalize_mean": [0.485, 0.456, 0.406],
        "normalize_std": [0.229, 0.224, 0.225],
        "architecture": "mobilenet_v3_large",
    }
    (MODEL_DIR / "labels.json").write_text(json.dumps(labels_payload, indent=2))

    metrics_payload = {
        "device_used": str(device),
        "dataset": {
            "name": "TrashNet (garythung/trashnet)",
            "classes": class_names,
            "train_size": len(train_loader.dataset),
            "val_size": len(val_loader.dataset),
            "test_size": len(test_loader.dataset),
        },
        "hyperparameters": {
            "image_size": IMAGE_SIZE,
            "batch_size": BATCH_SIZE,
            "phase1_epochs": PHASE1_EPOCHS,
            "phase2_epochs": PHASE2_EPOCHS,
            "phase1_lr": PHASE1_LR,
            "phase2_lr": PHASE2_LR,
        },
        "test_accuracy": test_acc,
        "best_val_accuracy": history["best_val_acc"],
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "history": {
            "train_loss": history["train_loss"],
            "train_acc": history["train_acc"],
            "val_loss": history["val_loss"],
            "val_acc": history["val_acc"],
            "phase1_epochs": PHASE1_EPOCHS,
        },
    }
    (MODEL_DIR / "metrics.json").write_text(json.dumps(metrics_payload, indent=2))
    (MODEL_DIR / "classification_report.txt").write_text(report_text)

    plot_training_curves(history, MODEL_DIR / "training_curves.png")
    plot_confusion_matrix(cm, class_names, MODEL_DIR / "confusion_matrix.png")
    plot_sample_predictions(model, test_loader, class_names, device, MODEL_DIR / "sample_predictions.png")

    # --- sync inference artifacts into the app ---
    app_ml_dir = APP_DIR / "ml_model"
    app_ml_dir.mkdir(exist_ok=True)
    shutil.copy2(MODEL_DIR / "waste_classifier.pt", app_ml_dir / "waste_classifier.pt")
    shutil.copy2(MODEL_DIR / "labels.json", app_ml_dir / "labels.json")
    shutil.copy2(MODEL_DIR / "metrics.json", app_ml_dir / "metrics.json")

    report_static_dir = APP_DIR / "static" / "model_report"
    report_static_dir.mkdir(parents=True, exist_ok=True)
    for name in ("training_curves.png", "confusion_matrix.png", "sample_predictions.png"):
        shutil.copy2(MODEL_DIR / name, report_static_dir / name)

    print(f"\nCopied inference artifacts into {app_ml_dir}")
    print(f"Copied report images into {report_static_dir}")
    print("\nDone.")


if __name__ == "__main__":
    main()
