"""Database migration & population script for Simulator SSOT (Single Source of Truth).

Builds 8 minimal, highly traceable tables in data/game_data.db representing:
1. sim_class_registry (Class, Growth, HP/SP constants)
2. sim_passive_milestones (Guild Blessing, Wardrobe, Titles, Battle Achievement, Card Awakening)
3. sim_equipment_catalog & sim_equipment_scales (11 Slots, Base stats, Up/Refine curves)
4. sim_enchant_catalog (City, Slot Category, Stat Name, Rate per Level)
5. sim_skills_and_buffs (Class Skills, Passives, Buffs, Consumables)
6. sim_inscriptions (Inscription, Pioneer, Bound, Engraved)
7. sim_divinity_catalog (8 Parts, Main Stat Scalings, Substats Pool)
8. sim_combat_rules (Element Matrix, Size Penalty, Awakening Tiers)
"""

import sys
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "game_data.db"
STATIC_JSON = ROOT / "src" / "rox_wiki" / "static" / "data" / "static_game_data.json"
EXCEL_PATH = ROOT / "assets" / "templates" / "arang-simulator-master.xlsx"


def init_schema(conn: sqlite3.Connection):
    cur = conn.cursor()

    # 1. Class Registry
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sim_class_registry (
        class_id TEXT PRIMARY KEY,
        class_name TEXT NOT NULL,
        primary_stat TEXT NOT NULL,
        attack_type TEXT NOT NULL,
        hp_per_vit REAL NOT NULL,
        sp_per_int REAL NOT NULL,
        growth_table_json TEXT NOT NULL
    );
    """)

    # 2. Passive Milestones
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sim_passive_milestones (
        system_type TEXT NOT NULL,
        identifier TEXT NOT NULL,
        level_or_point INTEGER DEFAULT 0,
        stats_json TEXT NOT NULL,
        PRIMARY KEY (system_type, identifier, level_or_point)
    );
    """)

    # 3. Equipment Catalog & Scales
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sim_equipment_catalog (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT UNIQUE NOT NULL,
        slot_type TEXT NOT NULL,
        weapon_type TEXT,
        quality TEXT NOT NULL,
        base_level INTEGER DEFAULT 1,
        is_two_handed BOOLEAN DEFAULT FALSE,
        base_stats_json TEXT NOT NULL,
        up_id INTEGER,
        ref_id INTEGER
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sim_equip_slot ON sim_equipment_catalog(slot_type);")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sim_equipment_scales (
        scale_type TEXT NOT NULL,
        scale_id INTEGER NOT NULL,
        level INTEGER NOT NULL,
        stats_json TEXT NOT NULL,
        PRIMARY KEY (scale_type, scale_id, level)
    );
    """)

    # 4. Enchant Catalog (Available rules and stat rates per city & category)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sim_enchant_catalog (
        city_name TEXT NOT NULL,
        slot_category TEXT NOT NULL,
        stat_name TEXT NOT NULL,
        rate_per_level REAL NOT NULL,
        max_level INTEGER DEFAULT 10,
        PRIMARY KEY (city_name, slot_category, stat_name)
    );
    """)

    # 5. Skills and Buffs
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sim_skills_and_buffs (
        id TEXT PRIMARY KEY,
        class_id TEXT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        max_level INTEGER DEFAULT 10,
        cooldown REAL DEFAULT 0.0,
        hits_per_sec REAL DEFAULT 1.0,
        formula_type TEXT NOT NULL,
        effect_json TEXT NOT NULL
    );
    """)

    # 6. Inscriptions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sim_inscriptions (
        category TEXT NOT NULL,
        name TEXT NOT NULL,
        max_level INTEGER DEFAULT 10,
        stats_per_level_json TEXT NOT NULL,
        PRIMARY KEY (category, name)
    );
    """)

    # 7. Divinity Catalog
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sim_divinity_catalog (
        part_id TEXT NOT NULL,
        divinity_name TEXT NOT NULL,
        main_stat_names_json TEXT NOT NULL,
        main_levels_json TEXT NOT NULL,
        substats_pool_json TEXT NOT NULL,
        PRIMARY KEY (part_id, divinity_name)
    );
    """)

    # 8. Combat Rules
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sim_combat_rules (
        rule_type TEXT NOT NULL,
        key_1 TEXT NOT NULL,
        key_2 TEXT NOT NULL,
        value REAL NOT NULL,
        extra_json TEXT,
        PRIMARY KEY (rule_type, key_1, key_2)
    );
    """)

    conn.commit()
    print("All 8 SSOT tables initialized successfully.")


def populate_from_static_data(conn: sqlite3.Connection):
    if not STATIC_JSON.exists():
        print(f"Warning: {STATIC_JSON} not found!")
        return

    with open(STATIC_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    cur = conn.cursor()

    # 1. Combat Rules: element_matrix
    elem_matrix = data.get("element_matrix") or {}
    for atk_elem, defenders in elem_matrix.items():
        if isinstance(defenders, dict):
            for def_elem, mult in defenders.items():
                cur.execute("""
                INSERT OR REPLACE INTO sim_combat_rules (rule_type, key_1, key_2, value)
                VALUES (?, ?, ?, ?)
                """, ("element_matrix", atk_elem, def_elem, float(mult)))

    # 2. Combat Rules: size_penalty
    size_penalty = data.get("size_penalty") or {}
    for size, mult in size_penalty.items():
        cur.execute("""
        INSERT OR REPLACE INTO sim_combat_rules (rule_type, key_1, key_2, value)
        VALUES (?, ?, ?, ?)
        """, ("size_penalty", "All", size, float(mult)))

    # 3. Combat Rules: awakening_tiers
    awk_tiers = data.get("awakening_tiers") or {}
    for sys_type, tiers in awk_tiers.items():
        if isinstance(tiers, list):
            for idx, t in enumerate(tiers):
                extra = json.dumps(t)
                bonus = float(t.get("bonus") or 0.0)
                cur.execute("""
                INSERT OR REPLACE INTO sim_combat_rules (rule_type, key_1, key_2, value, extra_json)
                VALUES (?, ?, ?, ?, ?)
                """, ("awakening_tier", sys_type, str(idx + 1), bonus, extra))

    # 4. Enchant Catalog: enchant_cities
    enchant_cities = data.get("enchant_cities") or {}
    for city, categories in enchant_cities.items():
        if isinstance(categories, dict):
            for cat, stats in categories.items():
                if isinstance(stats, dict):
                    for s_name, rate in stats.items():
                        cur.execute("""
                        INSERT OR REPLACE INTO sim_enchant_catalog (city_name, slot_category, stat_name, rate_per_level, max_level)
                        VALUES (?, ?, ?, ?, 10)
                        """, (city, cat, s_name, float(rate)))

    # 5. Equipment Catalog & Base items
    equip_base = data.get("equip_base") or {}
    for slot_type, items in equip_base.items():
        if isinstance(items, list):
            for itm in items:
                name = itm.get("name")
                if not name:
                    continue
                up_id = itm.get("up_id")
                ref_id = itm.get("ref_id")
                base_stats = json.dumps(itm.get("stats") or {})
                w_type = itm.get("weapon_type") or itm.get("type")
                quality = itm.get("quality") or "White"
                cur.execute("""
                INSERT OR REPLACE INTO sim_equipment_catalog (item_name, slot_type, weapon_type, quality, base_stats_json, up_id, ref_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (name, slot_type, w_type, quality, base_stats, up_id, ref_id))

    # 6. Equipment Scales: Upgrade & Refine
    up_tables = data.get("upgrade_tables") or {}
    for up_id_str, levels in up_tables.items():
        try:
            up_id_int = int(up_id_str)
        except ValueError:
            continue
        if isinstance(levels, dict):
            for lv_str, stats in levels.items():
                try:
                    lv_int = int(lv_str)
                except ValueError:
                    continue
                cur.execute("""
                INSERT OR REPLACE INTO sim_equipment_scales (scale_type, scale_id, level, stats_json)
                VALUES (?, ?, ?, ?)
                """, ("upgrade", up_id_int, lv_int, json.dumps(stats)))

    ref_tables = data.get("refine_tables") or {}
    for ref_id_str, levels in ref_tables.items():
        try:
            ref_id_int = int(ref_id_str)
        except ValueError:
            continue
        if isinstance(levels, dict):
            for lv_str, stats in levels.items():
                try:
                    lv_int = int(lv_str)
                except ValueError:
                    continue
                cur.execute("""
                INSERT OR REPLACE INTO sim_equipment_scales (scale_type, scale_id, level, stats_json)
                VALUES (?, ?, ?, ?)
                """, ("refine", ref_id_int, lv_int, json.dumps(stats)))

    # 7. Divinity Catalog
    div_catalog = data.get("divinity_catalog") or {}
    for name, d_info in div_catalog.items():
        if isinstance(d_info, dict):
            part_id = str(d_info.get("part") or "I")
            main_stats = json.dumps(d_info.get("stat_names") or [])
            main_levels = json.dumps(d_info.get("main_levels") or {})
            substats_pool = json.dumps(d_info.get("substats") or {})
            cur.execute("""
            INSERT OR REPLACE INTO sim_divinity_catalog (part_id, divinity_name, main_stat_names_json, main_levels_json, substats_pool_json)
            VALUES (?, ?, ?, ?, ?)
            """, (part_id, name, main_stats, main_levels, substats_pool))

    # 8. Initial Class Registry (Dragon Knight & Ranger defaults)
    classes_to_seed = [
        {
            "class_id": "dragon_knight",
            "class_name": "Dragon Knight",
            "primary_stat": "STR",
            "attack_type": "Physical",
            "hp_per_vit": 320.0,
            "sp_per_int": 25.0,
            "growth": {"formula": "swordsman_growth_standard"}
        },
        {
            "class_id": "ranger",
            "class_name": "Ranger",
            "primary_stat": "DEX",
            "attack_type": "Physical",
            "hp_per_vit": 240.0,
            "sp_per_int": 35.0,
            "growth": {"formula": "archer_growth_standard"}
        }
    ]
    for c in classes_to_seed:
        cur.execute("""
        INSERT OR REPLACE INTO sim_class_registry (class_id, class_name, primary_stat, attack_type, hp_per_vit, sp_per_int, growth_table_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (c["class_id"], c["class_name"], c["primary_stat"], c["attack_type"], c["hp_per_vit"], c["sp_per_int"], json.dumps(c["growth"])))

    # 9. Passive Milestones: Battle Achievement & Wardrobe
    cur.execute("""
    INSERT OR REPLACE INTO sim_passive_milestones (system_type, identifier, level_or_point, stats_json)
    VALUES (?, ?, ?, ?)
    """, ("battle_achievement", "standard_tier", 1, json.dumps({
        "STR": 72, "VIT": 72, "Final P.DMG Bonus": 0.24, "Fire Enhance": 0.3, "Max HP%": 0.24, "Final P.DMG RED": 0.16
    })))

    # Wardrobe Shine points standard steps
    wardrobe_milestones = [
        (20, {"P.DEF": 20, "M.DEF": 10}),
        (40, {"Max HP": 400, "Max SP": 100}),
        (60, {"P.ATK": 30, "M.ATK": 30}),
        (80, {"Hit": 20, "Flee": 20}),
        (100, {"Crit": 15, "Anti-Crit": 15}),
        (200, {"Crit": 30, "Anti-Crit": 30}),
        (500, {"P.DEF": 100, "M.DEF": 50})
    ]
    for pts, s_dict in wardrobe_milestones:
        cur.execute("""
        INSERT OR REPLACE INTO sim_passive_milestones (system_type, identifier, level_or_point, stats_json)
        VALUES (?, ?, ?, ?)
        """, ("wardrobe_shine", f"{pts}_points", pts, json.dumps(s_dict)))

    # 10. Inscriptions standard set
    inscriptions = [
        ("Inscription", "Strength I", 10, {"STR": 5}),
        ("Inscription", "Physical Damage Bonus I", 10, {"P.DMG Bonus": 20}),
        ("Inscription", "Physical Damage Reduction IV", 10, {"PVP Final P.DMG RED": 0.05}),
        ("Pioneer", "Physical Attack I", 10, {"P.ATK": 15}),
        ("Pioneer", "Physical Damage Bonus III", 10, {"Final P.DMG Bonus": 0.05}),
        ("Pioneer", "Physical Lifesteal", 10, {"Physical Lifesteal": 0.02}),
    ]
    for cat, name, max_lv, s_dict in inscriptions:
        cur.execute("""
        INSERT OR REPLACE INTO sim_inscriptions (category, name, max_level, stats_per_level_json)
        VALUES (?, ?, ?, ?)
        """, (cat, name, max_lv, json.dumps(s_dict)))

    # 11. Skills & Buffs standard
    skills_buffs = [
        ("sword_mastery", "dragon_knight", "Sword Mastery", "passive", 10, 0.0, 1.0, "stat_bonus", json.dumps({"P.ATK": 10})),
        ("cavalry_mastery", "dragon_knight", "Cavalry Mastery", "passive", 10, 0.0, 1.0, "stat_bonus", json.dumps({"P.ATK": 15})),
        ("aura_blade", "dragon_knight", "Aura Blade", "passive", 10, 0.0, 1.0, "stat_bonus", json.dumps({"Crit DMG Bonus": 0.03, "Final Crit": 0.02})),
        ("head_crush", "dragon_knight", "Head Crush", "passive", 10, 0.0, 1.0, "stat_bonus", json.dumps({"P.ATK%": 0.02, "Crit DMG Bonus": 0.02})),
        ("spear_flash", "dragon_knight", "Spear Flash", "active_buff", 1, 0.0, 1.0, "stat_bonus", json.dumps({"Final P.DMG Bonus": 0.20})),
        ("concentration", None, "Concentration", "active_buff", 10, 0.0, 1.0, "stat_bonus", json.dumps({"P.ATK%": 0.15, "Hit": 50.0})),
        ("spooky_lamp", None, "Spooky Lamp", "active_buff", 5, 0.0, 1.0, "stat_bonus", json.dumps({"Final P.DMG Bonus": 0.10})),
        ("double_blow", "dragon_knight", "Double Blow", "active_attack", 10, 0.0, 1.5, "skill_multiplier", json.dumps({"multiplier": 1.5})),
        ("ignition_break", "dragon_knight", "Ignition Break", "active_attack", 10, 0.0, 0.5, "skill_multiplier", json.dumps({"multiplier": 3.0, "scaling_stat": "STR", "scale_div": 800.0}))
    ]
    for s_id, c_id, name, cat, max_lv, cd, hps, f_type, eff in skills_buffs:
        cur.execute("""
        INSERT OR REPLACE INTO sim_skills_and_buffs (id, class_id, name, category, max_level, cooldown, hits_per_sec, formula_type, effect_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (s_id, c_id, name, cat, max_lv, cd, hps, f_type, eff))

    conn.commit()
    print("Static dataset migration completed successfully.")


def verify_ssot_counts(conn: sqlite3.Connection):
    cur = conn.cursor()
    tables = [
        "sim_class_registry",
        "sim_passive_milestones",
        "sim_equipment_catalog",
        "sim_equipment_scales",
        "sim_enchant_catalog",
        "sim_skills_and_buffs",
        "sim_inscriptions",
        "sim_divinity_catalog",
        "sim_combat_rules"
    ]
    print("\n--- SSOT Tables Verification ---")
    for t in tables:
        count = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:26s}: {count:5d} records")


def run():
    print(f"Connecting to database at: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    try:
        init_schema(conn)
        populate_from_static_data(conn)
        verify_ssot_counts(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    run()
