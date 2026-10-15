import json
import sqlite3
import sys
import time
from pathlib import Path

try:
    import UnityPy
except ImportError:
    print("Error: UnityPy required")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
BUNDLE_DIR = ROOT / "references" / "RO_SEA" / "RO_SEAGame" / "rox_Data" / "StreamingAssets" / "Bundle"
BUNDLE_LIST_FILE = BUNDLE_DIR / "BundleList.txt"
OUTPUT_DIR = ROOT / "data" / "static" / "monsters"
DB_PATH = ROOT / "data" / "game_data.db"


def find_monster_bundles():
    bundles = {}
    if not BUNDLE_LIST_FILE.exists():
        print(f"BundleList not found: {BUNDLE_LIST_FILE}")
        return bundles

    with open(BUNDLE_LIST_FILE, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                bname = parts[0]
                bhash = parts[1]
                if "shared_unityatlas_monster" in bname.lower() and "digital" not in bname.lower():
                    bundles[bname] = BUNDLE_DIR / f"{bhash}.bundle"
    return bundles


def extract_monster_avatars():
    t0 = time.time()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bundles = find_monster_bundles()
    print(f"Found {len(bundles)} monster atlas bundles to extract.")

    extracted_sprites = {}
    total_saved = 0

    order = sorted(bundles.items(), key=lambda x: (
        1 if "monster4" in x[0] else (2 if "monster2" in x[0] else 0)
    ))

    for bname, bpath in order:
        if not bpath.exists():
            continue
        try:
            env = UnityPy.load(str(bpath))
            for obj in env.objects:
                if obj.type.name != "Sprite":
                    continue
                data = obj.read()
                sname = getattr(data, "m_Name", None) or getattr(data, "name", None)
                if not sname or not sname.isdigit():
                    continue

                target = OUTPUT_DIR / f"{sname}.png"
                img = data.image

                if target.exists():
                    prev_w, prev_h = extracted_sprites.get(sname, (0, 0))
                    if img.width * img.height <= prev_w * prev_h:
                        continue

                img.save(target, "PNG")
                extracted_sprites[sname] = (img.width, img.height)
                total_saved += 1
        except Exception as e:
            print(f"Error extracting {bname}: {e}")

    elapsed = time.time() - t0
    print(f"Extracted {len(extracted_sprites)} unique monster avatars ({total_saved} saves) in {elapsed:.2f}s -> {OUTPUT_DIR}")
    return extracted_sprites


def update_database_monsters():
    if not DB_PATH.exists():
        print(f"DB not found: {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    cur.execute("SELECT id, card_id, raw_json FROM monsters")
    rows = cur.fetchall()

    updates = []
    head_count = 0
    resid_count = 0
    card_fallback_count = 0

    for mid, card_id, raw_json in rows:
        resid = 0
        if raw_json:
            try:
                data = json.loads(raw_json)
                resid = int(data.get("resId") or 0)
            except Exception:
                pass

        if (OUTPUT_DIR / f"{mid}.png").exists():
            icon_url = f"/static/monsters/{mid}.png"
            head_count += 1
        elif resid and (OUTPUT_DIR / f"{resid}.png").exists():
            icon_url = f"/static/monsters/{resid}.png"
            resid_count += 1
        elif card_id and (ROOT / "data" / "static" / "cards" / f"{card_id}.png").exists():
            icon_url = f"/static/cards/{card_id}.png"
            card_fallback_count += 1
        elif (ROOT / "data" / "static" / "cards" / f"{mid}.png").exists():
            icon_url = f"/static/cards/{mid}.png"
            card_fallback_count += 1
        else:
            icon_url = f"/static/items/{mid}.png"

        updates.append((icon_url, mid))

    cur.executemany("UPDATE monsters SET icon_url = ? WHERE id = ?", updates)
    conn.commit()
    conn.close()

    print(f"Database update complete:")
    print(f" - Direct monster avatars: {head_count:,}")
    print(f" - resId fallback avatars: {resid_count:,}")
    print(f" - Card fallback sprites: {card_fallback_count:,}")
    print(f" - Total avatar coverage: {(head_count + resid_count) / len(rows) * 100:.1f}%")


if __name__ == "__main__":
    extract_monster_avatars()
    update_database_monsters()
