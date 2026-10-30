"""
Stratified 80/10/10 train/val/test split of the TrashNet dataset.

Source images live in data_raw/dataset-resized/<class>/*.jpg (downloaded,
untrusted data -- we only ever read image bytes from it, never execute
anything from inside it). Output is a copy into data_split/{train,val,test}
so torchvision.datasets.ImageFolder can load each split directly.
"""
import random
import shutil
from pathlib import Path

RANDOM_SEED = 42
SPLIT = {"train": 0.8, "val": 0.1, "test": 0.1}

ML_DIR = Path(__file__).resolve().parent
SRC_DIR = ML_DIR / "data_raw" / "dataset-resized"
DST_DIR = ML_DIR / "data_split"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def main():
    random.seed(RANDOM_SEED)

    if not SRC_DIR.exists():
        raise SystemExit(f"Expected dataset at {SRC_DIR}, but it doesn't exist.")

    if DST_DIR.exists():
        shutil.rmtree(DST_DIR)

    class_dirs = sorted(p for p in SRC_DIR.iterdir() if p.is_dir())
    summary = {}

    for class_dir in class_dirs:
        class_name = class_dir.name
        images = sorted(
            p for p in class_dir.iterdir()
            if p.suffix.lower() in IMAGE_EXTENSIONS
        )
        random.shuffle(images)

        n = len(images)
        n_train = int(n * SPLIT["train"])
        n_val = int(n * SPLIT["val"])
        # remainder goes to test so the three counts always sum to n
        splits = {
            "train": images[:n_train],
            "val": images[n_train:n_train + n_val],
            "test": images[n_train + n_val:],
        }

        for split_name, files in splits.items():
            out_dir = DST_DIR / split_name / class_name
            out_dir.mkdir(parents=True, exist_ok=True)
            for f in files:
                shutil.copy2(f, out_dir / f.name)

        summary[class_name] = {k: len(v) for k, v in splits.items()}
        print(f"{class_name:10s} total={n:4d}  train={len(splits['train']):4d}  "
              f"val={len(splits['val']):3d}  test={len(splits['test']):3d}")

    print("\nDone. Split written to", DST_DIR)
    return summary


if __name__ == "__main__":
    main()
