import sys
import time
from pathlib import Path

try:
    import UnityPy
except ImportError:
    print("UnityPy required")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
BUNDLE_PATH = ROOT / "references" / "RO_SEA" / "RO_SEAGame" / "rox_Data" / "StreamingAssets" / "Bundle" / "16fc84e62a6739240765ba3516d62257.bundle"
OUTPUT_DIR = ROOT / "data" / "static" / "cards"

def extract_card_portraits() -> int:
    if not BUNDLE_PATH.exists():
        print(f"Bundle not found: {BUNDLE_PATH}")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    env = UnityPy.load(str(BUNDLE_PATH))
    saved = 0
    t0 = time.time()

    for obj in env.objects:
        if obj.type.name not in ("Sprite", "Texture2D"):
            continue
        data = obj.read()
        name = getattr(data, "m_Name", None) or getattr(data, "name", None)
        if not name:
            continue

        target = OUTPUT_DIR / f"{name}.png"
        if target.exists():
            saved += 1
            continue

        try:
            img = data.image
            img.save(target, "PNG")
            saved += 1
        except Exception:
            pass

    elapsed = time.time() - t0
    print(f"Extracted/verified {saved} card portraits in {elapsed:.2f}s -> {OUTPUT_DIR}")
    return saved

if __name__ == "__main__":
    extract_card_portraits()
