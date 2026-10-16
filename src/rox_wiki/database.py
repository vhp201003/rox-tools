"""ROX Game Data Repository (SQLite).

Provides high-speed queries for monsters, cards, and training dummies.
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "game_data.db"

CARD_SLOT_NAMES = {
    1: "Weapon",
    2: "Armor",
    3: "Cloak",
    4: "Shoes",
    5: "Headgear",
    6: "Accessory",
    7: "Shield",
    8: "Backpack",
}


def get_db_connection() -> Optional[sqlite3.Connection]:
    """Returns an SQLite connection with Row factory enabled."""
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_database_summary() -> Dict[str, Any]:
    """Returns total counts of indexed entities."""
    conn = get_db_connection()
    if not conn:
        return {"status": "not_initialized", "monsters": 0, "cards": 0, "dummies": 0}

    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM monsters")
        monsters_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM cards")
        cards_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM dps_dummies")
        dummies_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM pets")
        pets_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM shadow_weapons")
        sw_count = cur.fetchone()[0]

        return {
            "status": "ready",
            "db_path": str(DB_PATH),
            "monsters": monsters_count,
            "cards": cards_count,
            "dummies": dummies_count,
            "pets": pets_count,
            "shadow_weapons": sw_count,
        }
    finally:
        conn.close()


def get_database_metadata() -> Dict[str, Any]:
    conn = get_db_connection()
    if not conn:
        return {
            "elements": [],
            "races": [],
            "sizes": [],
            "types": [],
            "card_qualities": [],
            "pet_qualities": [],
        }

    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT element_name FROM monsters WHERE element_name IS NOT NULL ORDER BY element_name ASC")
        elements = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT race_name FROM monsters WHERE race_name IS NOT NULL ORDER BY race_name ASC")
        races = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT size_name FROM monsters WHERE size_name IS NOT NULL ORDER BY size_name ASC")
        sizes = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT type_name FROM monsters WHERE type_name IS NOT NULL ORDER BY type_name ASC")
        types = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT quality, quality_name FROM cards WHERE quality IS NOT NULL AND quality_name IS NOT NULL ORDER BY quality ASC")
        card_qualities = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT quality, quality_name FROM pets WHERE quality IS NOT NULL AND quality_name IS NOT NULL ORDER BY quality ASC")
        pet_qualities = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]

        card_slots = [
            {"id": k, "name": v} for k, v in sorted(CARD_SLOT_NAMES.items())
        ]

        return {
            "elements": elements,
            "races": races,
            "sizes": sizes,
            "types": types,
            "card_qualities": card_qualities,
            "card_slots": card_slots,
            "pet_qualities": pet_qualities,
        }
    finally:
        conn.close()


def search_monsters(
    query: Optional[str] = None,
    category: Optional[str] = None,
    type_name: Optional[str] = None,
    element: Optional[str] = None,
    race: Optional[str] = None,
    is_mvp: Optional[bool] = None,
    min_level: Optional[int] = None,
    max_level: Optional[int] = None,
    sort_by: Optional[str] = None,
    canonical_only: Optional[bool] = None,
    page: int = 1,
    limit: int = 20,
) -> Dict[str, Any]:
    page = max(1, page)
    limit = min(max(1, limit), 100)

    conn = get_db_connection()
    if not conn:
        return {"total": 0, "page": page, "limit": limit, "items": []}

    try:
        conditions = []
        params = []

        if category == "monster":
            conditions.append("is_mvp = 0 AND is_mini = 0 AND type NOT IN (2, 6, 8)")
        elif category == "mvp":
            conditions.append("(is_mvp = 1 OR is_mini = 1)")

        if canonical_only is True or (canonical_only is None and not query and category != "mvp"):
            conditions.append("is_canonical = 1")
        elif canonical_only is False:
            pass

        if query:
            q_strip = query.strip()
            if q_strip.isdigit():
                conditions.append("(id = ? OR name LIKE ? OR name_cn LIKE ?)")
                params.extend([int(q_strip), f"%{query}%", f"%{query}%"])
            else:
                conditions.append("(name LIKE ? OR name_cn LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])

        if type_name:
            conditions.append("type_name = ?")
            params.append(type_name)

        if element:
            conditions.append("element_name = ?")
            params.append(element)

        if race:
            conditions.append("race_name = ?")
            params.append(race)

        if is_mvp is not None and not category:
            conditions.append("is_mvp = ?")
            params.append(1 if is_mvp else 0)

        if min_level is not None:
            conditions.append("level >= ?")
            params.append(min_level)

        if max_level is not None:
            conditions.append("level <= ?")
            params.append(max_level)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM monsters {where_clause}", params)
        total = cur.fetchone()[0]

        order_clause = "level ASC, id ASC"
        if sort_by == "level_desc":
            order_clause = "level DESC, id ASC"
        elif sort_by == "level_asc":
            order_clause = "level ASC, id ASC"
        elif sort_by == "hp_desc":
            order_clause = "max_hp DESC, id ASC"
        elif sort_by == "dps_desc":
            order_clause = "p_dps DESC, id ASC"
        elif sort_by == "name_asc":
            order_clause = "name ASC, level ASC, id ASC"

        offset = (page - 1) * limit
        cur.execute(
            f"""
            SELECT id, name, name_cn, level, max_hp, race_name, element_name,
                   size_name, p_def, m_def, p_dps, m_dps,
                   hit, flee, crit, anti_crit, p_pen, m_pen,
                   final_p_def_red, final_m_def_red, p_dmg_bonus, m_dmg_bonus,
                   move_speed, attack_range, base_exp, job_exp,
                   zeny, type_name, is_mvp, is_mini, drop_id, mvp_drop_id,
                   icon_url, nav_scene_id, is_canonical, card_id,
                   def_base, def_ext, total_def,
                   mdef_base, mdef_ext, total_mdef,
                   crit_res_base, crit_res_ext, total_crit_res,
                   flee_base, flee_ext, total_flee,
                   json_extract(raw_json, '$.resId') AS res_id
            FROM monsters {where_clause}
            ORDER BY {order_clause}
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )

        items = [dict(row) for row in cur.fetchall()]
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
            "items": items,
        }
    finally:
        conn.close()


def get_monster_variants(monster_name: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, name, level, max_hp, p_def, m_def, p_dps, m_dps,
                   hit, flee, crit, anti_crit, p_pen, m_pen,
                   final_p_def_red, final_m_def_red, p_dmg_bonus, m_dmg_bonus,
                   element_name, race_name, size_name, is_mvp, is_mini,
                   drop_id, mvp_drop_id, icon_url, is_canonical, card_id,
                   def_base, def_ext, total_def,
                   mdef_base, mdef_ext, total_mdef,
                   crit_res_base, crit_res_ext, total_crit_res,
                   flee_base, flee_ext, total_flee
            FROM monsters
            WHERE name = ?
            ORDER BY level ASC, id ASC
            """,
            (monster_name,),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_monster_by_id(monster_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM monsters WHERE id = ?", (monster_id,))
        row = cur.fetchone()
        if not row:
            return None

        data = dict(row)
        if data.get("raw_json"):
            try:
                data["raw"] = json.loads(data["raw_json"])
            except Exception:
                pass
            del data["raw_json"]
        data["variants"] = get_monster_variants(data["name"])
        data["res_id"] = data.get("raw", {}).get("resId", data["id"])

        # Fetch multi-card weather drops from monster_cards
        cur.execute(
            """
            SELECT mc.card_id AS id, mc.card_id, mc.weather_phase, mc.slot_id, mc.slot_name,
                   c.name, c.quality, c.quality_name, c.is_mvp, c.attr_desc, c.deposit_desc, c.icon_url
            FROM monster_cards mc
            JOIN cards c ON c.id = mc.card_id
            WHERE mc.monster_id = ?
            ORDER BY CASE mc.weather_phase WHEN 'Day' THEN 1 WHEN 'Night' THEN 2 WHEN 'Void' THEN 3 ELSE 4 END, mc.card_id ASC
            """,
            (monster_id,),
        )
        linked_cards = [dict(c_row) for c_row in cur.fetchall()]
        data["cards"] = linked_cards
        if linked_cards:
            data["card"] = linked_cards[0]
        else:
            card_id = data.get("card_id")
            data["card"] = get_card_by_id(card_id) if card_id else None
        return data
    finally:
        conn.close()


def search_cards(
    query: Optional[str] = None,
    quality: Optional[int] = None,
    card_type: Optional[int] = None,
    is_mvp: Optional[bool] = None,
    page: int = 1,
    limit: int = 20,
) -> Dict[str, Any]:
    page = max(1, page)
    limit = min(max(1, limit), 100)

    conn = get_db_connection()
    if not conn:
        return {"total": 0, "page": page, "limit": limit, "items": []}

    try:
        conditions = []
        params = []

        if query:
            q_strip = query.strip()
            if q_strip.isdigit():
                conditions.append("(id = ? OR name LIKE ?)")
                params.extend([int(q_strip), f"%{query}%"])
            else:
                conditions.append("name LIKE ?")
                params.append(f"%{query}%")

        if quality is not None:
            conditions.append("quality = ?")
            params.append(quality)

        if card_type is not None:
            conditions.append("card_type = ?")
            params.append(card_type)

        if is_mvp is not None:
            conditions.append("is_mvp = ?")
            params.append(1 if is_mvp else 0)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM cards {where_clause}", params)
        total = cur.fetchone()[0]

        order_clause = "quality DESC, id ASC"
        offset = (page - 1) * limit
        cur.execute(
            f"""
            SELECT id, name, quality, quality_name, is_mvp, card_type, attr_desc, deposit_desc, icon_url, monster_id
            FROM cards {where_clause}
            ORDER BY {order_clause}
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )

        items = []
        for row in cur.fetchall():
            item = dict(row)
            item["slot_name"] = CARD_SLOT_NAMES.get(item.get("card_type"), "Unknown")
            items.append(item)

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
            "items": items,
        }
    finally:
        conn.close()


def get_card_by_id(card_id: int) -> Optional[Dict[str, Any]]:
    """Returns complete details of a specific card."""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM cards WHERE id = ?", (card_id,))
        row = cur.fetchone()
        if not row:
            return None

        data = dict(row)
        if data.get("raw_json"):
            try:
                data["raw"] = json.loads(data["raw_json"])
            except Exception:
                pass
            del data["raw_json"]
        data["slot_name"] = CARD_SLOT_NAMES.get(data.get("card_type"), "Unknown")
        return data
    finally:
        conn.close()


def get_dps_dummies() -> List[Dict[str, Any]]:
    """Returns training dummy presets."""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, monster_id, level, desc FROM dps_dummies ORDER BY id ASC")
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_pet_by_id(pet_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM pets WHERE id = ?", (pet_id,))
        row = cur.fetchone()
        if not row:
            return None
        data = dict(row)
        if data.get("raw_json"):
            try:
                data["raw"] = json.loads(data["raw_json"])
            except Exception:
                pass
            del data["raw_json"]
        return data
    finally:
        conn.close()


def search_pets(
    query: Optional[str] = None,
    quality: Optional[int] = None,
    page: int = 1,
    limit: int = 20,
) -> Dict[str, Any]:
    page = max(1, page)
    limit = min(max(1, limit), 100)
    conn = get_db_connection()
    if not conn:
        return {"total": 0, "page": page, "limit": limit, "items": []}
    try:
        conditions = []
        params = []
        if query:
            q_strip = query.strip()
            if q_strip.isdigit():
                conditions.append("(id = ? OR name LIKE ?)")
                params.extend([int(q_strip), f"%{query}%"])
            else:
                conditions.append("name LIKE ?")
                params.append(f"%{query}%")
        if quality is not None:
            conditions.append("quality = ?")
            params.append(quality)
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM pets {where_clause}", params)
        total = cur.fetchone()[0]
        offset = (page - 1) * limit
        cur.execute(
            f"SELECT id, name, monster_id, quality, quality_name, property, property_name, vitality, talent, talent_desc, icon_url FROM pets {where_clause} ORDER BY quality DESC, id ASC LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
            "items": [dict(r) for r in cur.fetchall()],
        }
    finally:
        conn.close()


def get_shadow_weapon_by_id(sw_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM shadow_weapons WHERE id = ?", (sw_id,))
        row = cur.fetchone()
        if not row:
            return None
        data = dict(row)
        if data.get("raw_json"):
            try:
                data["raw"] = json.loads(data["raw_json"])
            except Exception:
                pass
            del data["raw_json"]
        return data
    finally:
        conn.close()


def search_shadow_weapons(
    query: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> Dict[str, Any]:
    page = max(1, page)
    limit = min(max(1, limit), 100)
    conn = get_db_connection()
    if not conn:
        return {"total": 0, "page": page, "limit": limit, "items": []}
    try:
        conditions = []
        params = []
        if query:
            q_strip = query.strip()
            if q_strip.isdigit():
                conditions.append("(id = ? OR name LIKE ? OR artifact_name LIKE ?)")
                params.extend([int(q_strip), f"%{query}%", f"%{query}%"])
            else:
                conditions.append("(name LIKE ? OR artifact_name LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM shadow_weapons {where_clause}", params)
        total = cur.fetchone()[0]
        offset = (page - 1) * limit
        cur.execute(
            f"SELECT id, name, artifact_name, artifact_level, task_group_id, icon_url FROM shadow_weapons {where_clause} ORDER BY id ASC LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
            "items": [dict(r) for r in cur.fetchall()],
        }
    finally:
        conn.close()


def init_profiles_table() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db_connection()
    if not conn:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                class_id TEXT NOT NULL DEFAULT 'dragon_knight',
                build_data TEXT NOT NULL,
                computed_results TEXT,
                computed_dps INTEGER DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_profiles_updated ON profiles(updated_at DESC)")
        conn.commit()
    finally:
        conn.close()


def get_profile(profile_id: str) -> Optional[Dict[str, Any]]:
    init_profiles_table()
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
        row = cur.fetchone()
        if not row:
            return None
        data = dict(row)
        try:
            data["build_data"] = json.loads(data["build_data"])
        except Exception:
            pass
        if data.get("computed_results"):
            try:
                data["computed_results"] = json.loads(data["computed_results"])
            except Exception:
                pass
        return data
    finally:
        conn.close()


def upsert_profile(
    profile_id: str,
    class_id: str,
    build_data: Any,
    computed_results: Optional[Any] = None,
    computed_dps: int = 0
) -> Dict[str, Any]:
    init_profiles_table()
    conn = get_db_connection()
    if not conn:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        build_data_str = json.dumps(build_data) if isinstance(build_data, (dict, list)) else str(build_data)
        computed_results_str = (
            json.dumps(computed_results)
            if isinstance(computed_results, (dict, list))
            else (str(computed_results) if computed_results is not None else None)
        )

        cur.execute("""
            INSERT INTO profiles (id, class_id, build_data, computed_results, computed_dps, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                class_id = excluded.class_id,
                build_data = excluded.build_data,
                computed_results = excluded.computed_results,
                computed_dps = excluded.computed_dps,
                updated_at = datetime('now')
        """, (profile_id, class_id, build_data_str, computed_results_str, computed_dps))
        conn.commit()

        cur.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
        row = cur.fetchone()
        data = dict(row)
        try:
            data["build_data"] = json.loads(data["build_data"])
        except Exception:
            pass
        if data.get("computed_results"):
            try:
                data["computed_results"] = json.loads(data["computed_results"])
            except Exception:
                pass
        return data
    finally:
        conn.close()


def delete_profile(profile_id: str) -> bool:
    init_profiles_table()
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# --- SIMULATOR SSOT QUERIES ---

def get_sim_class_registry(class_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM sim_class_registry WHERE class_id = ?", (class_id,))
        row = cur.fetchone()
        if not row:
            return None
        res = dict(row)
        res["growth_table"] = json.loads(res.get("growth_table_json") or "{}")
        return res
    finally:
        conn.close()


def get_sim_enchant_rules(city_name: Optional[str] = None, slot_category: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        query = "SELECT * FROM sim_enchant_catalog WHERE 1=1"
        params: List[Any] = []
        if city_name:
            query += " AND city_name = ?"
            params.append(city_name)
        if slot_category:
            query += " AND slot_category = ?"
            params.append(slot_category)
        query += " ORDER BY city_name ASC, stat_name ASC"
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_sim_equipment_item(item_name: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM sim_equipment_catalog WHERE item_name = ?", (item_name,))
        row = cur.fetchone()
        if not row:
            return None
        res = dict(row)
        res["base_stats"] = json.loads(res.get("base_stats_json") or "{}")
        return res
    finally:
        conn.close()


def get_sim_equipment_scale(scale_type: str, scale_id: int, level: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT stats_json FROM sim_equipment_scales WHERE scale_type = ? AND scale_id = ? AND level = ?",
            (scale_type, scale_id, level)
        )
        row = cur.fetchone()
        if not row:
            return None
        return json.loads(row["stats_json"])
    finally:
        conn.close()


def get_sim_passive_milestones(system_type: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM sim_passive_milestones WHERE system_type = ? ORDER BY level_or_point ASC", (system_type,))
        res = []
        for r in cur.fetchall():
            d = dict(r)
            d["stats"] = json.loads(d.get("stats_json") or "{}")
            res.append(d)
        return res
    finally:
        conn.close()


def get_sim_combat_rules(rule_type: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM sim_combat_rules WHERE rule_type = ?", (rule_type,))
        res = []
        for r in cur.fetchall():
            d = dict(r)
            if d.get("extra_json"):
                d["extra"] = json.loads(d["extra_json"])
            res.append(d)
        return res
    finally:
        conn.close()



