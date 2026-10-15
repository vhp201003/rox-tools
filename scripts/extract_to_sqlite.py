"""ROX PC Client Game Data ETL Pipeline: Extract AssetBundle Lua Tables to SQLite.

Extracts monsters, cards, items, and training dummies from UnityFS AssetBundles
into a high-performance SQLite database for instant querying.
"""

import os
import re
import sys
import json
import time
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import UnityPy
except ImportError:
    print("Error: UnityPy is required. Please install via: pip install UnityPy")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
RO_SEA = ROOT / "references" / "RO_SEA"
DB_DIR = ROOT / "data"
DB_PATH = DB_DIR / "game_data.db"
STATIC_DIR = DB_DIR / "static"

ELEMENT_NAMES = {
    0: "Neutral",
    1: "Fire",
    2: "Water",
    3: "Wind",
    4: "Earth",
    5: "Poison",
    6: "Holy",
    7: "Shadow",
    8: "Ghost",
    9: "Undead",
}

RACE_NAMES = {
    1: "Angel",
    2: "Demon",
    4: "Formless",
    8: "Insect",
    16: "Fish",
    32: "Demi-Human",
    64: "Undead",
    128: "Dragon",
    256: "Plant",
    512: "Brute",
}

SIZE_NAMES = {
    0: "Large",
    1: "Medium",
    2: "Small",
    3: "Giant",
}

MONSTER_TYPE_NAMES = {
    0: "Normal",
    1: "Mini",
    2: "MVP",
    3: "Instance Boss",
    4: "Summon",
    5: "Elite",
    6: "Quest",
    7: "Instance",
}

CARD_QUALITY_NAMES = {
    1: "White",
    2: "Blue",
    3: "Purple",
    4: "Gold",
}


def safe_int(val: Any, default: int = 0) -> int:
    """Safely converts any value to int, avoiding crashes on strings/None."""
    try:
        if isinstance(val, (int, float)):
            return int(val)
        if isinstance(val, str):
            return int(float(val))
    except (ValueError, TypeError):
        pass
    return default


def safe_float(val: Any, default: float = 0.0) -> float:
    """Safely converts any value to float."""
    try:
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            return float(val)
    except (ValueError, TypeError):
        pass
    return default


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


def extract_text_asset(bundle_path: Path, asset_name: str) -> str:
    """Extracts a TextAsset script string from an AssetBundle."""
    env = UnityPy.load(str(bundle_path))
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            data = obj.read()
            m_name = getattr(data, "m_Name", getattr(data, "name", ""))
            if m_name == asset_name:
                script = getattr(data, "m_Script", getattr(data, "script", b""))
                if isinstance(script, bytes):
                    return script.decode("utf-8", errors="ignore")
                return str(script)
    return ""


def parse_language_table(lua_script: str) -> Dict[str, str]:
    """Parses en_langs flat Lua key-value mappings."""
    pattern = re.compile(r'\[\"([^\"]+)\"\]\s*=\s*\"([^\"]*)\"')
    return dict(pattern.findall(lua_script))


def parse_lua_entries(lua_script: str) -> Dict[int, Dict[str, Any]]:
    """Fast tokenizer parsing top-level entries [ID] = { ... } into dicts."""
    entries = {}
    entry_iter = list(re.finditer(r'\[(\d+)\]\s*=\s*\{', lua_script))

    for i, match in enumerate(entry_iter):
        entry_id = int(match.group(1))
        start_pos = match.end()
        end_pos = entry_iter[i + 1].start() if i + 1 < len(entry_iter) else len(lua_script)
        chunk = lua_script[start_pos:end_pos]

        fields: Dict[str, Any] = {}

        # Top-level strings: ["key"] = "value"
        str_matches = re.findall(r'\[\"([^\"]+)\"\]\s*=\s*\"([^\"]*)\"', chunk)
        for k, v in str_matches:
            fields[k] = v

        # Top-level numbers: ["key"] = 123
        num_matches = re.findall(r'\[\"([^\"]+)\"\]\s*=\s*(-?\d+\.?\d*)', chunk)
        for k, v in num_matches:
            # Prefer numeric values over string predicates
            fields[k] = float(v) if "." in v else int(v)

        entries[entry_id] = fields

    return entries


def create_database(db_path: Path):
    """Initializes the SQLite schema."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS monsters")
    cur.execute("""
    CREATE TABLE monsters (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        name_cn TEXT,
        level INTEGER,
        max_hp INTEGER,
        race INTEGER,
        race_name TEXT,
        element INTEGER,
        element_name TEXT,
        size INTEGER,
        size_name TEXT,
        p_def INTEGER,
        m_def INTEGER,
        p_dps INTEGER,
        m_dps INTEGER,
        hit INTEGER,
        flee INTEGER,
        crit INTEGER,
        anti_crit INTEGER,
        p_pen INTEGER,
        m_pen INTEGER,
        final_p_def_red REAL,
        final_m_def_red REAL,
        p_dmg_bonus REAL,
        m_dmg_bonus REAL,
        move_speed REAL,
        attack_range REAL,
        base_exp INTEGER,
        job_exp INTEGER,
        zeny INTEGER,
        type INTEGER,
        type_name TEXT,
        is_mvp INTEGER DEFAULT 0,
        is_mini INTEGER DEFAULT 0,
        drop_id INTEGER,
        mvp_drop_id INTEGER,
        icon_url TEXT,
        nav_scene_id INTEGER,
        raw_json TEXT
    );
    """)

    cur.execute("DROP TABLE IF EXISTS cards")
    cur.execute("""
    CREATE TABLE cards (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        quality INTEGER,
        quality_name TEXT,
        is_mvp INTEGER DEFAULT 0,
        card_type INTEGER,
        attr_desc TEXT,
        deposit_desc TEXT,
        icon_url TEXT,
        raw_json TEXT
    );
    """)

    cur.execute("DROP TABLE IF EXISTS dps_dummies")
    cur.execute("""
    CREATE TABLE dps_dummies (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        monster_id INTEGER,
        level INTEGER,
        desc TEXT
    );
    """)

    cur.execute("DROP TABLE IF EXISTS pets")
    cur.execute("""
    CREATE TABLE pets (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        monster_id INTEGER,
        quality INTEGER,
        quality_name TEXT,
        property INTEGER,
        property_name TEXT,
        vitality INTEGER,
        talent TEXT,
        talent_desc TEXT,
        icon_url TEXT,
        raw_json TEXT
    );
    """)

    cur.execute("DROP TABLE IF EXISTS shadow_weapons")
    cur.execute("""
    CREATE TABLE shadow_weapons (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        artifact_name TEXT,
        artifact_level INTEGER,
        task_group_id INTEGER,
        icon_url TEXT,
        raw_json TEXT
    );
    """)

    # Indices for sub-millisecond lookups
    cur.execute("CREATE INDEX idx_monsters_name ON monsters(name);")
    cur.execute("CREATE INDEX idx_monsters_type ON monsters(type);")
    cur.execute("CREATE INDEX idx_monsters_type_name ON monsters(type_name);")
    cur.execute("CREATE INDEX idx_monsters_level ON monsters(level);")
    cur.execute("CREATE INDEX idx_cards_name ON cards(name);")
    cur.execute("CREATE INDEX idx_cards_quality ON cards(quality);")
    cur.execute("CREATE INDEX idx_pets_name ON pets(name);")
    cur.execute("CREATE INDEX idx_pets_quality ON pets(quality);")
    cur.execute("CREATE INDEX idx_shadow_weapons_name ON shadow_weapons(name);")

    conn.commit()
    conn.close()


def run_etl():
    """Runs the full extraction pipeline."""
    start_time = time.time()
    print("=" * 60)
    print("ROX PC Client Game Data ETL Pipeline -> SQLite")
    print("=" * 60)

    en_bundle = find_bundle_file("lua_data_en.bundle")
    data2_bundle = find_bundle_file("lua_data_data_2.bundle")
    data1_bundle = find_bundle_file("lua_data_data_1.bundle")
    data0_bundle = find_bundle_file("lua_data_data_0.bundle")

    print(f"en_bundle: {en_bundle.name if en_bundle else 'NOT FOUND'}")
    print(f"data2_bundle: {data2_bundle.name if data2_bundle else 'NOT FOUND'}")
    print(f"data1_bundle: {data1_bundle.name if data1_bundle else 'NOT FOUND'}")
    print(f"data0_bundle: {data0_bundle.name if data0_bundle else 'NOT FOUND'}")

    if not (en_bundle and data2_bundle and data1_bundle):
        print("Error: Essential game bundles not found.")
        return False

    en_script = extract_text_asset(en_bundle, "en_langs")
    lang_map = parse_language_table(en_script)
    print(f" -> Loaded {len(lang_map):,} localization keys.")

    monster_script = extract_text_asset(data2_bundle, "data_monster_Monster")
    monsters_raw = parse_lua_entries(monster_script)
    print(f" -> Parsed {len(monsters_raw):,} monster entries.")

    card_script = extract_text_asset(data1_bundle, "data_ItemV2_ItemCard")
    cards_raw = parse_lua_entries(card_script)
    print(f" -> Parsed {len(cards_raw):,} card entries.")

    dummy_script = extract_text_asset(data0_bundle, "data_DpsTestMonster") if data0_bundle else ""
    dummy_pairs = re.findall(r'\[\"?(\d+)\"?\]\s*=\s*(\d+)', dummy_script) if dummy_script else []
    print(f" -> Parsed {len(dummy_pairs):,} training dummy mappings.")

    pet_script = extract_text_asset(data0_bundle, "data_pet_Pet") if data0_bundle else ""
    pets_raw = parse_lua_entries(pet_script) if pet_script else {}
    print(f" -> Parsed {len(pets_raw):,} pet entries.")

    sw_script = extract_text_asset(data1_bundle, "data_ShadowWeapon_ShadowWeapon") if data1_bundle else ""
    sws_raw = parse_lua_entries(sw_script) if sw_script else {}
    print(f" -> Parsed {len(sws_raw):,} shadow weapon entries.")

    create_database(DB_PATH)
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    monster_rows = []
    for mid, m in monsters_raw.items():
        name_key = m.get("name", f"MonsterName{mid}")
        eng_name = lang_map.get(name_key) or m.get("nameLocalized") or f"Monster #{mid}"
        cn_name = m.get("nameLocalized", "")

        level = safe_int(m.get("level"), 1)
        max_hp = safe_int(m.get("maxHp"), 100)
        race = safe_int(m.get("race"), 1)
        element = safe_int(m.get("property"), 1)
        size = safe_int(m.get("bodily"), 2)
        p_def = safe_int(m.get("physicDefenseLevel"), 0)
        m_def = safe_int(m.get("magicDefenseLevel"), 0)
        p_dps = safe_int(m.get("physicDps"), 0)
        m_dps = safe_int(m.get("magicDps"), 0)

        hit = safe_int(m.get("hitLevel") or m.get("hitIncrease"), 0)
        flee = safe_int(m.get("dodgeLevel") or m.get("dodgeRate"), 0)
        crit = safe_int(m.get("criticalLevel") or m.get("criticalRate"), 0)
        anti_crit = safe_int(m.get("criticalResistanceLevel") or m.get("criticalResistanceRate"), 0)
        p_pen = safe_int(m.get("physicPenetrationLevel"), 0)
        m_pen = safe_int(m.get("magicPenetrationLevel"), 0)
        final_p_def_red = safe_float(m.get("finalPhysicDefenseIncrease"), 0.0)
        final_m_def_red = safe_float(m.get("finalMagicDefenseIncrease"), 0.0)
        p_dmg_bonus = safe_float(m.get("physicDamageIncrease"), 0.0)
        m_dmg_bonus = safe_float(m.get("magicDamageIncrease"), 0.0)
        move_speed = safe_float(m.get("speed"), 0.0)
        attack_range = safe_float(m.get("attackDistance"), 0.0)

        base_exp = safe_int(m.get("baseExp"), 0)
        job_exp = safe_int(m.get("jobExp"), 0)
        zeny = safe_int(m.get("zeny"), 0)
        m_type = safe_int(m.get("type"), 0)
        nav_scene = safe_int(m.get("navSceneId"), 0)

        is_mvp = 1 if m_type == 2 else 0
        is_mini = 1 if m_type == 1 else 0

        drop_id = safe_int(m.get("DropId") or m.get("DropID"), 0)
        mvp_drop_id = safe_int(m.get("mvpDropId"), 0)

        res_id = safe_int(m.get("resId"), mid)
        icon_url = f"/static/items/{res_id}.png" if res_id > 0 else f"/static/items/{mid}.png"

        monster_rows.append((
            mid, eng_name, cn_name, level, max_hp,
            race, RACE_NAMES.get(race, f"Race_{race}"),
            element, ELEMENT_NAMES.get(element, f"Elem_{element}"),
            size, SIZE_NAMES.get(size, "Medium"),
            p_def, m_def, p_dps, m_dps,
            hit, flee, crit, anti_crit, p_pen, m_pen,
            final_p_def_red, final_m_def_red, p_dmg_bonus, m_dmg_bonus,
            move_speed, attack_range,
            base_exp, job_exp, zeny,
            m_type, MONSTER_TYPE_NAMES.get(m_type, f"Type_{m_type}"),
            is_mvp, is_mini, drop_id, mvp_drop_id, icon_url,
            nav_scene, json.dumps(m, ensure_ascii=False)
        ))

    cur.executemany("""
    INSERT INTO monsters (
        id, name, name_cn, level, max_hp, race, race_name,
        element, element_name, size, size_name, p_def, m_def,
        p_dps, m_dps, hit, flee, crit, anti_crit, p_pen, m_pen,
        final_p_def_red, final_m_def_red, p_dmg_bonus, m_dmg_bonus,
        move_speed, attack_range, base_exp, job_exp, zeny,
        type, type_name, is_mvp, is_mini, drop_id, mvp_drop_id,
        icon_url, nav_scene_id, raw_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, monster_rows)

    card_rows = []
    for cid, c in cards_raw.items():
        name_key = f"ItemName_{cid}"
        eng_name = lang_map.get(name_key) or f"Card #{cid}"
        quality = safe_int(c.get("cardQuality"), 1)
        is_mvp = safe_int(c.get("IsMvpCard"), 0)
        card_type = safe_int(c.get("cardType"), 1)

        attr_descs = []
        for suffix in ["", "1", "2", "3"]:
            k = f"CardAttributeDescription_{cid}{suffix}"
            if k in lang_map and lang_map[k]:
                attr_descs.append(lang_map[k])
        attr_desc = " | ".join(attr_descs) if attr_descs else ""

        deposit_desc = ""
        dep_key = f"CardDepositeDescription_{cid}"
        if dep_key in lang_map:
            deposit_desc = lang_map[dep_key]

        icon_url = f"/static/items/{cid}.png" if (STATIC_DIR / "items" / f"{cid}.png").exists() else "/static/items/10101000.png"

        card_rows.append((
            cid, eng_name, quality, CARD_QUALITY_NAMES.get(quality, "White"),
            is_mvp, card_type, attr_desc, deposit_desc, icon_url,
            json.dumps(c, ensure_ascii=False)
        ))

    cur.executemany("""
    INSERT INTO cards (
        id, name, quality, quality_name, is_mvp,
        card_type, attr_desc, deposit_desc, icon_url, raw_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, card_rows)

    # Insert Dps Test Dummies
    dummy_rows = []
    for slot_str, monster_id_str in dummy_pairs:
        slot_id = int(slot_str)
        m_id = int(monster_id_str)
        # Look up monster name
        m_name = lang_map.get(f"MonsterName{m_id}", f"Monster #{m_id}")
        dummy_rows.append((
            slot_id, f"Training Dummy (Target: {m_name})", m_id,
            safe_int(monsters_raw.get(m_id, {}).get("level"), 1),
            f"Mapped to Monster ID {m_id} ({m_name})"
        ))

    cur.executemany("""
    INSERT INTO dps_dummies (id, name, monster_id, level, desc)
    VALUES (?, ?, ?, ?, ?)
    """, dummy_rows)

    pet_rows = []
    for pid, p in pets_raw.items():
        name_key = p.get("Name") or p.get("name") or f"Pet_{pid}"
        eng_name = lang_map.get(name_key) or p.get("nameLocalized") or f"Pet #{pid}"
        monster_id = safe_int(p.get("Monster") or p.get("monster"), 0)
        quality = safe_int(p.get("Quality") or p.get("quality"), 1)
        prop_val = safe_int(p.get("Property") or p.get("property"), 1)
        vitality = safe_int(p.get("Vitality") or p.get("vitality"), 4000)
        talent = str(p.get("Talent") or "")
        t_desc_key = str(p.get("PetTalentDesc") or "")
        talent_desc = lang_map.get(t_desc_key, "")
        icon_id = safe_int(p.get("Icon") or p.get("icon"), pid)
        icon_url = f"/static/items/{icon_id}.png" if (STATIC_DIR / "items" / f"{icon_id}.png").exists() else "/static/items/10101000.png"

        pet_rows.append((
            pid, eng_name, monster_id, quality,
            CARD_QUALITY_NAMES.get(quality, f"Quality_{quality}"),
            prop_val, ELEMENT_NAMES.get(prop_val, f"Elem_{prop_val}"),
            vitality, talent, talent_desc, icon_url,
            json.dumps(p, ensure_ascii=False)
        ))

    cur.executemany("""
    INSERT INTO pets (
        id, name, monster_id, quality, quality_name,
        property, property_name, vitality, talent,
        talent_desc, icon_url, raw_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, pet_rows)

    sw_rows = []
    for sw_id, sw in sws_raw.items():
        name_key = sw.get("Name") or sw.get("name") or f"SW_{sw_id}"
        eng_name = lang_map.get(name_key) or f"Shadow Weapon #{sw_id}"
        art_key = sw.get("ArtifactName") or ""
        art_name = lang_map.get(art_key) or ""
        art_level = safe_int(sw.get("ArtifactLevel"), 7)
        task_group = safe_int(sw.get("TaskGroupId"), 0)
        icon_url = f"/static/items/{sw_id}.png" if (STATIC_DIR / "items" / f"{sw_id}.png").exists() else "/static/items/10101000.png"

        sw_rows.append((
            sw_id, eng_name, art_name, art_level, task_group,
            icon_url, json.dumps(sw, ensure_ascii=False)
        ))

    cur.executemany("""
    INSERT INTO shadow_weapons (
        id, name, artifact_name, artifact_level,
        task_group_id, icon_url, raw_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, sw_rows)

    conn.commit()
    conn.close()

    elapsed = time.time() - start_time
    file_size_kb = DB_PATH.stat().st_size / 1024
    print("=" * 60)
    print(f"ETL COMPLETED in {elapsed:.2f}s!")
    print(f" -> Database created at: {DB_PATH}")
    print(f" -> Database size: {file_size_kb:,.1f} KB")
    print(f" -> Monsters indexed: {len(monster_rows):,}")
    print(f" -> Cards indexed: {len(card_rows):,}")
    print(f" -> Training dummies indexed: {len(dummy_rows):,}")
    print(f" -> Pets indexed: {len(pet_rows):,}")
    print(f" -> Shadow weapons indexed: {len(sw_rows):,}")
    print("=" * 60)
    return True


if __name__ == "__main__":
    run_etl()
