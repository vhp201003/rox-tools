import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "game_data.db"
CARDS_DIR = ROOT / "data" / "static" / "cards"

def migrate():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(monsters)")
    m_cols = [row[1] for row in cur.fetchall()]
    if "is_canonical" not in m_cols:
        cur.execute("ALTER TABLE monsters ADD COLUMN is_canonical INTEGER DEFAULT 0")
    if "card_id" not in m_cols:
        cur.execute("ALTER TABLE monsters ADD COLUMN card_id INTEGER")

    cur.execute("PRAGMA table_info(cards)")
    c_cols = [row[1] for row in cur.fetchall()]
    if "monster_id" not in c_cols:
        cur.execute("ALTER TABLE cards ADD COLUMN monster_id INTEGER")

    cur.execute("SELECT id, raw_json FROM cards")
    card_rows = cur.fetchall()
    card_updates = []
    monster_to_card = {}

    for cid, raw in card_rows:
        try:
            data = json.loads(raw)
            mid = int(data.get("monster_id", 0))
        except (ValueError, TypeError, json.JSONDecodeError):
            mid = 0

        card_img = f"/static/cards/{cid}.png" if (CARDS_DIR / f"{cid}.png").exists() else None
        if not card_img and mid and (CARDS_DIR / f"{mid}.png").exists():
            card_img = f"/static/cards/{mid}.png"
        if not card_img:
            card_img = "/static/items/10101000.png"

        card_updates.append((mid, card_img, cid))
        if mid > 0 and (mid not in monster_to_card or cid < monster_to_card[mid]):
            monster_to_card[mid] = cid

    cur.executemany("UPDATE cards SET monster_id = ?, icon_url = ? WHERE id = ?", card_updates)

    cur.execute("SELECT id, type, is_mvp, is_mini FROM monsters")
    monsters = cur.fetchall()
    monster_updates = []

    for mid, m_type, is_mvp, is_mini in monsters:
        is_canonical = 1 if (10001 <= mid <= 10999 or 30001 <= mid <= 30999) else 0
        card_id = monster_to_card.get(mid)

        if (CARDS_DIR / f"{mid}.png").exists():
            icon_url = f"/static/cards/{mid}.png"
        elif card_id and (CARDS_DIR / f"{card_id}.png").exists():
            icon_url = f"/static/cards/{card_id}.png"
        else:
            icon_url = f"/static/items/{mid}.png"

        monster_updates.append((is_canonical, card_id, icon_url, mid))

    cur.executemany(
        "UPDATE monsters SET is_canonical = ?, card_id = ?, icon_url = ? WHERE id = ?",
        monster_updates
    )

    cur.execute("CREATE INDEX IF NOT EXISTS idx_monsters_canonical ON monsters(is_canonical)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_monsters_card_id ON monsters(card_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_cards_monster_id ON cards(monster_id)")

    conn.commit()

    cur.execute("SELECT count(*) FROM monsters WHERE is_canonical = 1")
    canon_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM monsters WHERE card_id IS NOT NULL")
    card_linked_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM monsters WHERE icon_url LIKE '/static/cards/%'")
    card_icon_count = cur.fetchone()[0]

    conn.close()
    print(f"Migration completed successfully:")
    print(f" - Canonical monsters: {canon_count}")
    print(f" - Monsters linked to card: {card_linked_count}")
    print(f" - Monsters with card portraits: {card_icon_count}")

if __name__ == "__main__":
    migrate()
