"""ROX Game Asset Extraction Pipeline: UnityFS Sprites to Web PNGs.

Extracts UI icons, cards, equipment, and monster heads from UnityFS AssetBundles
into rox-tool/data/static/ for FastAPI and Web UI serving.
"""

import sys
import time
from pathlib import Path
from typing import Optional

try:
    import UnityPy
except ImportError:
    print("Error: UnityPy is required. Please install via: pip install UnityPy")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
RO_SEA = ROOT / "references" / "RO_SEA"
STATIC_DIR = ROOT / "data" / "static"


def find_bundle_file(bundle_name: str) -> Optional[Path]:
    """Finds the AssetBundle file by logical name from BundleList.txt."""
    streaming_assets = RO_SEA / "RO_SEAGame" / "rox_Data" / "StreamingAssets"
    for bl_path in [
        streaming_assets / "Windows" / "BundleList.txt",
        streaming_assets / "Bundle" / "BundleList.txt",
    ]:
        if not bl_path.exists():
            continue
        with open(bl_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) >= 2 and parts[0] == bundle_name:
                    hash_file = bl_path.parent / f"{parts[1]}.bundle"
                    if hash_file.exists():
                        return hash_file
    return None


def extract_sprites_from_bundle(bundle_path: Path, output_dir: Path, overwrite: bool = False) -> int:
    """Extracts all Sprite objects from a bundle as PNG files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    env = UnityPy.load(str(bundle_path))
    count = 0

    for obj in env.objects:
        if obj.type.name != "Sprite":
            continue
        data = obj.read()
        name = getattr(data, "m_Name", None) or getattr(data, "name", None)
        if not name:
            continue

        target_file = output_dir / f"{name}.png"
        if target_file.exists() and not overwrite:
            count += 1
            continue

        try:
            image = data.image
            image.save(target_file, "PNG")
            count += 1
        except Exception:
            pass

    return count


def run_asset_extraction(overwrite: bool = False) -> dict:
    """Main extraction coordinator for all game sprites."""
    print("=" * 60)
    print("ROX PC Client Game Asset Extraction Pipeline")
    print("=" * 60)

    t0 = time.time()
    results = {}

    bundles_to_extract = [
        ("shared_unityatlas_item.bundle", STATIC_DIR / "items", "Items & Cards"),
        ("shared_unityatlas_equip.bundle", STATIC_DIR / "equip", "Equipment"),
        ("shared_unityatlas_personalized_head.bundle", STATIC_DIR / "heads", "Avatars & Heads"),
    ]

    for bname, target_dir, label in bundles_to_extract:
        bpath = find_bundle_file(bname)
        if not bpath:
            print(f"[-] {label}: Bundle {bname} not found.")
            results[label] = 0
            continue

        print(f"[+] Extracting {label} from {bname} ...")
        count = extract_sprites_from_bundle(bpath, target_dir, overwrite=overwrite)
        results[label] = count
        print(f"    -> Extracted/Verified {count:,} sprites in {target_dir.relative_to(ROOT)}.")

    elapsed = time.time() - t0
    print("=" * 60)
    print(f"Asset extraction completed in {elapsed:.2f}s!")
    print(f"Static directory: {STATIC_DIR}")
    print("=" * 60)
    return results


if __name__ == "__main__":
    force = "--overwrite" in sys.argv
    run_asset_extraction(overwrite=force)
