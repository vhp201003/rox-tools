import json
from pathlib import Path
import openpyxl
import re

def parse_stat_formula(f):
    if not f:
        return 0.0, 3
    s = str(f).strip()
    thresh = 3
    m_rd = re.search(r'ROUNDDOWN\(.*?/(\d+)', s)
    if m_rd:
        thresh = int(m_rd.group(1))
    else:
        m_lt = re.search(r'<(\d+)', s)
        if m_lt:
            thresh = int(m_lt.group(1))
        else:
            m_ge = re.search(r'>=(\d+)', s)
            if m_ge:
                thresh = int(m_ge.group(1))
            else:
                m_gt = re.search(r'>(\d+)', s)
                if m_gt:
                    thresh = int(m_gt.group(1)) + 1
    rate = 0.0
    m_pct = re.search(r'([+-]?\d+(?:\.\d+)?)%', s)
    if m_pct:
        rate = float(m_pct.group(1)) / 100.0
    else:
        m_num = re.search(r'=([+-]?\d+(?:\.\d+)?)\*', s)
        if m_num:
            rate = float(m_num.group(1))
        else:
            m_if_val = re.search(r',0,([+-]?\d+(?:\.\d+)?)\)', s)
            if m_if_val:
                rate = float(m_if_val.group(1))
            else:
                m_raw = re.search(r'=([+-]?\d+(?:\.\d+)?)', s)
                if m_raw:
                    rate = float(m_raw.group(1))
    return rate, thresh
EXCEL_PATH = Path("assets/templates/arang-simulator-master.xlsx")
OUT_DATA_PATH = Path("src/rox_wiki/static/data/static_game_data.json")
OUT_DK_PATH = Path("src/rox_wiki/static/data/dragon_knight_manifest.json")

def compile_all():
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    wb_formulas = openpyxl.load_workbook(EXCEL_PATH, data_only=False)
    
    # 1. Element Matrix from MasterLogic
    ws_ml = wb["MasterLogic"]
    elements = ["Neutral", "Fire", "Water", "Wind", "Earth", "Poison", "Holy", "Shadow", "Ghost", "Undead"]
    element_matrix = {}
    for r_idx, att_elem in enumerate(elements):
        row_num = 4 + r_idx
        element_matrix[att_elem] = {}
        for c_idx, def_elem in enumerate(elements):
            col_num = 31 + c_idx
            val = ws_ml.cell(row_num, col_num).value
            element_matrix[att_elem][def_elem] = float(val) if val is not None else 0.0

    # 2. Weapon Size Penalty
    size_penalty = {
        "Small": float(ws_ml.cell(4, 43).value or 0.75),
        "Medium": float(ws_ml.cell(5, 43).value or 0.75),
        "Large": float(ws_ml.cell(6, 43).value or 1.0)
    }

    # 3. Shadow Equipment Hotfix stats
    shadow_hotfix = {}
    for r in range(4, 23):
        lvl = ws_ml.cell(r, 45).value
        bonus = ws_ml.cell(r, 47).value
        if lvl is not None and bonus is not None:
            try:
                shadow_hotfix[int(lvl)] = float(bonus)
            except (ValueError, TypeError):
                pass
    # 4. Awakening Tiers
    awakening_tiers = {
        "refine": [
            {"tier": 1, "req_count": 2, "req_level": 6, "bonus": 0.10},
            {"tier": 2, "req_count": 4, "req_level": 7, "bonus": 0.20},
            {"tier": 3, "req_count": 6, "req_level": 8, "bonus": 0.30},
            {"tier": 4, "req_count": 8, "req_level": 9, "bonus": 0.40},
            {"tier": 5, "req_count": 8, "req_level": 10, "bonus": 0.50},
            {"tier": 6, "req_count": 8, "req_level": 11, "bonus": 0.60},
            {"tier": 7, "req_count": 8, "req_level": 12, "bonus": 0.70},
            {"tier": 8, "req_count": 8, "req_level": 13, "bonus": 0.80},
            {"tier": 9, "req_count": 8, "req_level": 14, "bonus": 0.90},
            {"tier": 10, "req_count": 8, "req_level": 15, "bonus": 1.00}
        ],
        "upgrade": [
            {"tier": 1, "req_count": 2, "req_weapon": 60, "req_armor": 30, "req_acc": 15, "bonus": 0.10},
            {"tier": 2, "req_count": 4, "req_weapon": 80, "req_armor": 40, "req_acc": 20, "bonus": 0.20},
            {"tier": 3, "req_count": 6, "req_weapon": 100, "req_armor": 50, "req_acc": 25, "bonus": 0.30},
            {"tier": 4, "req_count": 8, "req_weapon": 120, "req_armor": 60, "req_acc": 30, "bonus": 0.40},
            {"tier": 5, "req_count": 8, "req_weapon": 140, "req_armor": 70, "req_acc": 35, "bonus": 0.50}
        ],
        "enchant": [
            {"tier": 1, "req_count": 2, "req_total": 18, "bonus": 0.10},
            {"tier": 2, "req_count": 4, "req_total": 21, "bonus": 0.20},
            {"tier": 3, "req_count": 6, "req_total": 24, "bonus": 0.30},
            {"tier": 4, "req_count": 8, "req_total": 27, "bonus": 0.40},
            {"tier": 5, "req_count": 8, "req_total": 30, "bonus": 0.50}
        ]
    }

    # 5. Enchant Data Logic (10 Cities with weapon, armor, accessory multipliers)
    ws_enc_formula = wb_formulas["EnchantDataLogic"]
    import re
    enchant_cities = {}
    for r in range(5, 100):
        for c_offset, cat in [(37, "weapon"), (43, "armor"), (55, "accessory")]:
            c_name = ws_enc_formula.cell(r, c_offset).value
            s_name = ws_enc_formula.cell(r, c_offset + 1).value
            f_val = ws_enc_formula.cell(r, c_offset + 2).value
            if c_name and s_name and f_val:
                m = re.search(r'=([\d\.]+)\*', str(f_val))
                val = float(m.group(1)) if m else 1.0
                enchant_cities.setdefault(str(c_name).strip(), {}).setdefault(cat, {})[str(s_name).strip()] = val

    # 6. Extract All Stat Names from InputTally
    ws_tally = wb["InputTally"]
    stat_list = []
    for r in range(4, 200):
        s_val = ws_tally.cell(r, 2).value
        if s_val and not str(s_val).startswith("="):
            stat_list.append(str(s_val).strip())

    # 7. Extract Cards Catalog from SQLite & Database
    import sqlite3
    db_conn = sqlite3.connect("data/game_data.db")
    db_cur = db_conn.cursor()
    type_map = {1: "Weapon", 2: "Clothes", 3: "Cloak", 4: "Shoes", 5: "Accessory", 6: "Headgear"}
    cards_catalog = {t: [] for t in type_map.values()}
    db_cur.execute("SELECT name, card_type, attr_desc FROM cards WHERE attr_desc IS NOT NULL")

    def parse_card_desc(desc):
        st = {}
        if not desc:
            return st
        parts = re.split(r'[\r\n|]+', desc)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            clean = part.replace(',', '')
            m = re.search(r'([A-Za-z0-9\.\s%]+?)\s*([\+\-]\s*\d+(?:\.\d+)?%?)', clean)
            if m:
                sname = m.group(1).strip()
                val_s = m.group(2).replace(' ', '').strip()
                is_pct = val_s.endswith('%')
                v_num = float(val_s.replace('%', ''))
                if is_pct and not sname.endswith('%'):
                    sname = sname + '%'
                    st[sname] = v_num / 100.0
                else:
                    st[sname] = v_num
        return st

    seen_cards = set()
    for c_name, c_type, c_desc in db_cur.fetchall():
        slot_key = type_map.get(c_type)
        if not slot_key or not c_name or c_name.startswith("Any ") or c_name in seen_cards:
            continue
        c_stats = parse_card_desc(c_desc)
        if not c_stats:
            continue
        seen_cards.add(c_name)
        cards_catalog[slot_key].append({"name": c_name, "stats": c_stats})
    db_conn.close()

    # 7b. Pet & SP Pet Catalog from PetDataLogic & SPPetDataLogic
    ws_pet = wb["PetDataLogic"]
    pets_catalog = {}
    for r in range(3, 100):
        pname = ws_pet.cell(r, 10).value
        if not pname or str(pname).strip() == "None":
            continue
        pname_str = str(pname).strip()
        stats = [str(ws_pet.cell(r, c).value).strip() for c in range(11, 17) if ws_pet.cell(r, c).value]
        pets_catalog[pname_str] = stats

    ws_sppet = wb["SPPetDataLogic"]
    sp_pets_catalog = {}
    for r in range(3, 100):
        pname = ws_sppet.cell(r, 10).value
        if not pname or str(pname).strip() == "None":
            continue
        pname_str = str(pname).strip()
        stats = [str(ws_sppet.cell(r, c).value).strip() for c in range(11, 19) if ws_sppet.cell(r, c).value]
        sp_pets_catalog[pname_str] = stats

    # 7c. Divinity I-VIII Catalog with Main Stats (Levels 0-7) & Global 53 Substats Pool from MasterData
    ws_m = wb["MasterData"]
    divinity_parts = [
        "Spear of Eternity", "Thunderous Hammer", "Blade of Godslayer",
        "Wolf Shackles", "Stormrage Halberd", "Chanter's Harp",
        "Bow of Winter", "Reaper's Scythe"
    ]
    
    # Extract Main Stats per Part & Level (MasterData Cols 84-90: CF to CL)
    divinity_main_stats = {p: {"levels": {}, "stat_names": []} for p in divinity_parts}
    for r in range(4, 70):
        p_name = ws_m.cell(r, 84).value
        if not p_name or str(p_name).strip() not in divinity_main_stats:
            continue
        p_str = str(p_name).strip()
        s1 = ws_m.cell(r, 85).value
        s2 = ws_m.cell(r, 86).value
        lvl = ws_m.cell(r, 87).value
        if lvl is None:
            continue
        lvl_str = str(int(lvl))
        val_b = ws_m.cell(r, 88).value
        val_p = ws_m.cell(r, 89).value
        val_g = ws_m.cell(r, 90).value
        
        stat_names = [str(s1).strip()] if s1 else []
        if s2:
            stat_names.append(str(s2).strip())
        divinity_main_stats[p_str]["stat_names"] = stat_names
        divinity_main_stats[p_str]["levels"][lvl_str] = {
            "blue": float(val_b) if val_b is not None else 0.0,
            "purple": float(val_p) if val_p is not None else 0.0,
            "gold": float(val_g) if val_g is not None else 0.0
        }

    # Extract 53 Substats Pool (MasterData Cols 92-96: CN to CR)
    divinity_substats_pool = {}
    for r in range(4, 100):
        sn = ws_m.cell(r, 92).value
        if not sn or str(sn).strip() == "None":
            continue
        sn_str = str(sn).strip()
        val_blue = ws_m.cell(r, 94).value
        val_purple = ws_m.cell(r, 95).value
        val_gold = ws_m.cell(r, 96).value
        
        # Determine whether stat is percentage in display (e.g. 0.74 -> 74%, 0.15 -> 15%)
        # Flat stats: STR, AGI, VIT, INT, DEX, LUK, P.DMG Bonus (4410), M.DMG Bonus (4410)
        is_pct = not (sn_str in ["STR", "AGI", "VIT", "INT", "DEX", "LUK", "P.DMG Bonus", "M.DMG Bonus"])
        
        divinity_substats_pool[sn_str] = {
            "blue": float(val_blue) if val_blue is not None else 0.0,
            "purple": float(val_purple) if val_purple is not None else 0.0,
            "gold": float(val_gold) if val_gold is not None else 0.0,
            "is_pct": is_pct
        }

    divinity_catalog = {}
    for p_name in divinity_parts:
        m_info = divinity_main_stats.get(p_name, {"levels": {}, "stat_names": []})
        divinity_catalog[p_name] = {
            "name": p_name,
            "stat_names": m_info["stat_names"],
            "main_levels": m_info["levels"],
            "substats": divinity_substats_pool
        }

    # 7d. Debuff of MVPMINI
    ws_mvp = wb["Debuff of MVPMINI"]
    mvp_debuffs = []
    for r in range(3, 100):
        lvl = ws_mvp.cell(r, 2).value
        name = ws_mvp.cell(r, 3).value
        res = ws_mvp.cell(r, 4).value
        if name:
            mvp_debuffs.append({"level": int(lvl) if lvl else 0, "name": str(name).strip(), "debuff_res": float(res) if res else 0.0})

    # 7e. EquipSet bonuses (all 37 equip sets / 82+ variants across rows 3-156)
    ws_es = wb["EquipSet"]
    ws_es_f = wb_formulas["EquipSet"]
    equip_sets = []
    for r in range(3, 157):
        name_val = ws_es.cell(r, 1).value
        name_f = ws_es_f.cell(r, 1).value
        if not name_val and not name_f:
            continue
        name = str(name_val or name_f).strip()
        if name.startswith('="Tough Resilience'):
            name = "Tough Resilience Lv.1 - Sharp Stack"
        elif name.startswith('=IF(Input1!$B$2="Minstrel","Apricity Heart - Stack"'):
            name = "Soulmare Chains - Stack"
        elif name.startswith('=IF(Input1!$B$2="Minstrel","Apricity Heart I - Stack"'):
            name = "Soulmare Chains I - Stack"
        elif name.startswith('='):
            continue

        stat_name = ws_es.cell(r, 19).value
        stat_bonuses = []
        stats_dict = {}
        thresholds_dict = {}
        formulas_dict = {}
        min_threshold = 3

        for col_n, col_v in [(19, 20), (21, 22), (23, 24), (25, 26)]:
            sn = ws_es.cell(r, col_n).value
            sv = ws_es.cell(r, col_v).value
            sv_f = ws_es_f.cell(r, col_v).value
            if sn:
                sn_str = str(sn).strip()
                rate, thresh = parse_stat_formula(sv_f)
                stat_bonuses.append({
                    "stat": sn_str,
                    "value": rate,
                    "threshold": thresh,
                    "formula": str(sv_f or "")
                })
                stats_dict[sn_str] = rate
                thresholds_dict[sn_str] = thresh
                formulas_dict[sn_str] = str(sv_f or "")
                min_threshold = thresh

        acc_pieces = [str(ws_es.cell(r, c).value).strip() for c in range(6, 12) if ws_es.cell(r, c).value]
        tal_pieces = [str(ws_es.cell(r, c).value).strip() for c in range(12, 18) if ws_es.cell(r, c).value]

        set_entry = {
            "name": name,
            "stat": str(stat_name).strip() if stat_name else (stat_bonuses[0]["stat"] if stat_bonuses else ""),
            "threshold": min_threshold,
            "weapon": str(ws_es.cell(r, 2).value or "").strip(),
            "armor": str(ws_es.cell(r, 3).value or "").strip(),
            "cloak": str(ws_es.cell(r, 4).value or "").strip(),
            "shoes": str(ws_es.cell(r, 5).value or "").strip(),
            "acc1": str(ws_es.cell(r, 6).value or "").strip(),
            "acc2": str(ws_es.cell(r, 7).value or "").strip(),
            "acc3": str(ws_es.cell(r, 8).value or "").strip(),
            "acc4": str(ws_es.cell(r, 9).value or "").strip(),
            "acc5": str(ws_es.cell(r, 10).value or "").strip(),
            "acc6": str(ws_es.cell(r, 11).value or "").strip(),
            "talisman1": str(ws_es.cell(r, 12).value or "").strip(),
            "talisman2": str(ws_es.cell(r, 13).value or "").strip(),
            "talisman3": str(ws_es.cell(r, 14).value or "").strip(),
            "talisman4": str(ws_es.cell(r, 15).value or "").strip(),
            "talisman5": str(ws_es.cell(r, 16).value or "").strip(),
            "talisman6": str(ws_es.cell(r, 17).value or "").strip(),
            "talisman": str(ws_es.cell(r, 12).value or "").strip(),
            "accessories": acc_pieces,
            "talismans": tal_pieces,
            "stat_bonuses": stat_bonuses,
            "stats": stats_dict,
            "thresholds": thresholds_dict,
            "formulas": formulas_dict
        }
        equip_sets.append(set_entry)

    # 7f. CardSet combo rules (rows 38-45)
    ws_cs = wb["CardSet"]
    ws_cs_f = wb_formulas["CardSet"]
    card_sets = []
    for r in range(39, 46):
        cards = [str(ws_cs.cell(r, c).value).strip() for c in range(2, 12) if ws_cs.cell(r, c).value]
        if not cards:
            continue
        status_f = str(ws_cs_f.cell(r, 12).value or "")
        m_cnt = re.search(r'>=(\d+)', status_f)
        req_count = int(m_cnt.group(1)) if m_cnt else 1

        stat_rules = {}
        for c_stat in range(13, 23, 2):
            sn = ws_cs.cell(r, c_stat).value
            sv = ws_cs_f.cell(r, c_stat + 1).value or ws_cs.cell(r, c_stat + 1).value
            if sn:
                stat_rules[str(sn).strip()] = str(sv).strip() if sv else ""

        base_name = cards[0].split('[')[0].strip()
        card_sets.append({
            "name": f"{base_name} Combo",
            "base_card": base_name,
            "required_cards": cards,
            "req_count": req_count,
            "condition_formula": status_f,
            "stat_formulas": stat_rules
        })

    # 7g. Inscriptions catalog (Input3 B4:H37)
    ws_in3 = wb["Input3"]
    ws_in3_f = wb_formulas["Input3"]
    inscriptions_catalog = []
    current_cat = "Inscription"
    for r in range(4, 38):
        cat_val = ws_in3.cell(r, 2).value
        if cat_val and str(cat_val).strip() in ["Inscription", "Pioneer"]:
            current_cat = str(cat_val).strip()

        name_val = ws_in3.cell(r, 3).value
        name_f = ws_in3_f.cell(r, 3).value
        name = str(name_val or name_f or "").strip()

        stat1_name = str(ws_in3.cell(r, 5).value or ws_in3_f.cell(r, 5).value or "").strip()
        stat1_formula = str(ws_in3_f.cell(r, 6).value or ws_in3.cell(r, 6).value or "").strip()

        stat2_name = str(ws_in3.cell(r, 7).value or ws_in3_f.cell(r, 7).value or "").strip()
        stat2_formula = str(ws_in3_f.cell(r, 8).value or ws_in3.cell(r, 8).value or "").strip()

        if "IFERROR" in stat2_name:
            stat2_name = ""
        if "IFERROR" in stat2_formula:
            stat2_formula = ""

        inscriptions_catalog.append({
            "category": current_cat,
            "name": name,
            "max_level": 10,
            "stat1": stat1_name,
            "formula1": stat1_formula,
            "stat2": stat2_name,
            "formula2": stat2_formula
        })

    # 7h. Guild Blessing catalog (Input1 Q3:R18)
    ws_in1 = wb["Input1"]
    ws_in1_f = wb_formulas["Input1"]
    guild_blessings_catalog = []
    for r in range(3, 19):
        sn = ws_in1.cell(r, 17).value
        formula = ws_in1_f.cell(r, 18).value
        val = ws_in1.cell(r, 18).value
        if sn:
            guild_blessings_catalog.append({
                "stat_name": str(sn).strip(),
                "formula": str(formula).strip() if formula is not None else "",
                "default_value": float(val) if isinstance(val, (int, float)) else 0.0
            })

    # 7i. Card Awakening catalog (MasterData Q4:Q25)
    ws_md = wb["MasterData"]
    card_awakenings_catalog = []
    for r in range(4, 26):
        sn = ws_md.cell(r, 17).value
        if sn:
            card_awakenings_catalog.append({
                "stat_name": str(sn).strip(),
                "max_level": 100
            })

    # 7j. Wardrobe Shine Point milestones (Input1 T3:W52)
    wardrobe_milestones = []
    for r in range(3, 53, 2):
        pts_str = ws_in1.cell(r, 21).value
        if not pts_str:
            continue
        m_pts = re.search(r'(\d+)', str(pts_str))
        if not m_pts:
            continue
        pts = int(m_pts.group(1))

        stats = {}
        for row_offset in (0, 1):
            s_name = ws_in1.cell(r + row_offset, 22).value
            s_formula = ws_in1_f.cell(r + row_offset, 23).value
            if s_name and s_formula:
                m_val = re.search(r'=([0-9\.]+)\*', str(s_formula))
                val = float(m_val.group(1)) if m_val else 0.0
                stats[str(s_name).strip()] = val

        wardrobe_milestones.append({
            "point": pts,
            "level_or_point": pts,
            "identifier": f"{pts}_points",
            "stats": stats
        })

    # 8. Extract Equip Base & IDs from EquipData1
    ws_eq1 = wb["EquipData1"]
    equip_base = {}
    eq_slots = [
        ("Weapon", 2, 8, 9, 2),
        ("Shield", 11, 17, 18, 2),
        ("Clothes", 20, 26, 27, 2),
        ("Cloak", 29, 35, 36, 2),
        ("Shoes", 38, 44, 45, 2),
        ("Accessory", 47, 53, 54, 2),
        ("Talisman", 56, 62, 63, 2),
        ("CostumeHead", 65, None, None, 5),
        ("CostumeEyes", 78, None, None, 5),
        ("CostumeMouth", 91, None, None, 5),
        ("CostumeBack", 104, None, None, 5)
    ]
    for slot_name, s_col, up_col, ref_col, num_stats in eq_slots:
        equip_base[slot_name] = []
        for r in range(4, ws_eq1.max_row + 1):
            name_val = ws_eq1.cell(r, s_col + 1).value
            if not name_val or str(name_val).strip() == "":
                continue
            up_id = 0
            ref_id = 0
            if up_col is not None and ref_col is not None:
                u_val = ws_eq1.cell(r, up_col).value
                r_val = ws_eq1.cell(r, ref_col).value
                try:
                    up_id = int(u_val) if u_val is not None else 0
                except (ValueError, TypeError):
                    up_id = 0
                try:
                    ref_id = int(r_val) if r_val is not None else 0
                except (ValueError, TypeError):
                    ref_id = 0

            item_stats = {}
            for stat_idx in range(num_stats):
                sn = ws_eq1.cell(r, s_col + 2 + stat_idx * 2).value
                sv = ws_eq1.cell(r, s_col + 3 + stat_idx * 2).value
                if sn and sv is not None:
                    try:
                        item_stats[str(sn).strip()] = float(sv)
                    except ValueError:
                        item_stats[str(sn).strip()] = str(sv)
            equip_base[slot_name].append({
                "name": str(name_val).strip(),
                "up_id": up_id,
                "ref_id": ref_id,
                "stats": item_stats
            })

    # 9. Extract Upgrade tables from EquipData2 (compact lookup)
    ws_eq2 = wb["EquipData2"]
    upgrade_tables = {}
    for col_start in range(2, ws_eq2.max_column + 1, 7):
        for r in range(4, ws_eq2.max_row + 1):
            uid = ws_eq2.cell(r, col_start).value
            lvl = ws_eq2.cell(r, col_start + 1).value
            if uid is None or lvl is None:
                continue
            try:
                uid_str = str(int(uid))
                lvl_str = str(int(lvl))
            except (ValueError, TypeError):
                continue
            if uid_str not in upgrade_tables:
                upgrade_tables[uid_str] = {}
            s1_n = ws_eq2.cell(r, col_start + 2).value
            s1_v = ws_eq2.cell(r, col_start + 3).value
            s2_n = ws_eq2.cell(r, col_start + 4).value
            s2_v = ws_eq2.cell(r, col_start + 5).value
            stats = {}
            if s1_n and s1_v is not None:
                stats[str(s1_n).strip()] = float(s1_v)
            if s2_n and s2_v is not None:
                stats[str(s2_n).strip()] = float(s2_v)
            upgrade_tables[uid_str][lvl_str] = stats

    # 10. Extract Refine tables from EquipData3
    ws_eq3 = wb["EquipData3"]
    refine_tables = {}
    for col_start in range(2, ws_eq3.max_column + 1, 7):
        for r in range(4, ws_eq3.max_row + 1):
            rid = ws_eq3.cell(r, col_start).value
            lvl = ws_eq3.cell(r, col_start + 1).value
            if rid is None or lvl is None:
                continue
            try:
                rid_str = str(int(rid))
                lvl_str = str(int(lvl))
            except (ValueError, TypeError):
                continue
            if rid_str not in refine_tables:
                refine_tables[rid_str] = {}
            s1_n = ws_eq3.cell(r, col_start + 2).value
            s1_v = ws_eq3.cell(r, col_start + 3).value
            s2_n = ws_eq3.cell(r, col_start + 4).value
            s2_v = ws_eq3.cell(r, col_start + 5).value
            stats = {}
            if s1_n and s1_v is not None:
                stats[str(s1_n).strip()] = float(s1_v)
            if s2_n and s2_v is not None:
                stats[str(s2_n).strip()] = float(s2_v)
            refine_tables[rid_str][lvl_str] = stats

    static_data = {
        "version": "1.2.0",
        "element_matrix": element_matrix,
        "size_penalty": size_penalty,
        "shadow_hotfix": shadow_hotfix,
        "awakening_tiers": awakening_tiers,
        "enchant_cities": enchant_cities,
        "stat_list": stat_list,
        "cards_catalog": cards_catalog,
        "pets_catalog": pets_catalog,
        "sp_pets_catalog": sp_pets_catalog,
        "divinity_catalog": divinity_catalog,
        "mvp_debuffs": mvp_debuffs,
        "equip_sets": equip_sets,
        "card_sets": card_sets,
        "inscriptions_catalog": inscriptions_catalog,
        "guild_blessings_catalog": guild_blessings_catalog,
        "card_awakenings_catalog": card_awakenings_catalog,
        "wardrobe_milestones": wardrobe_milestones,
        "equip_base": equip_base,
        "upgrade_tables": upgrade_tables,
        "refine_tables": refine_tables
    }

    OUT_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(static_data, f, ensure_ascii=False, indent=None, separators=(',', ':'))

    data_size_kb = OUT_DATA_PATH.stat().st_size / 1024
    print(f"Exported static_game_data.json: {data_size_kb:.2f} KB")

    # 11. Compile Dragon Knight Manifest
    dragon_knight_manifest = {
        "class_id": "dragon_knight",
        "class_name": "Dragon Knight",
        "primary_stat": "STR",
        "primary_conversions": {
            "str_to_patk": "STR * 4 + (floor(STR/100)*100)^2 * 0.002 + (STR - floor(STR/100)*100) * (floor(STR/100) * 0.2) if STR < 3000 else STR * 10",
            "luk_to_patk": "LUK * 0.5 + (floor(LUK/100)*100)^2 * 0.000025 + (LUK - floor(LUK/100)*100) * (floor(LUK/100) * 0.025) if LUK < 3000 else LUK * 1.25",
            "dex_to_patk": "DEX * 0.2 + (floor(DEX/100)*100)^2 * 0.00001 + (DEX - floor(DEX/100)*100) * (floor(DEX/100) * 0.01) if DEX < 3000 else DEX * 0.5"
        },
        "skills": [
            {
                "id": "normal_attack",
                "name": "Normal Attack",
                "type": "Physical",
                "multiplier_formula": "PATK",
                "crit_formula": "PATK * CritDMGBonus",
                "cooldown": 0,
                "hits_per_sec": 6,
                "active_in_rotation": True
            },
            {
                "id": "double_blow",
                "name": "Double Blow",
                "type": "Physical",
                "multiplier_formula": "PATK * (0.5 + shadow_f54) * shadow_h54",
                "cooldown": 0,
                "hits_per_sec": 6,
                "active_in_rotation": True
            },
            {
                "id": "wind_cutter",
                "name": "Wind Cutter",
                "type": "Physical",
                "multiplier_formula": "PATK * (1 + shadow_h57)",
                "cooldown": 0,
                "hits_per_sec": 6,
                "active_in_rotation": True
            },
            {
                "id": "storm_slash",
                "name": "Storm Slash",
                "type": "Physical",
                "multiplier_formula": "PATK * (1.6 + shadow_f65)",
                "cooldown": 2.5,
                "hits_per_sec": 0.4,
                "active_in_rotation": True
            },
            {
                "id": "ignition_break",
                "name": "Ignition Break",
                "type": "Physical",
                "multiplier_formula": "PATK * (3 + min(15, STR / 800))",
                "cooldown": 0,
                "hits_per_sec": 0,
                "active_in_rotation": False
            },
            {
                "id": "dusk_claymore",
                "name": "Dusk Claymore",
                "type": "Physical",
                "multiplier_formula": "PATK * (3.51 + se_level * 3.51)",
                "cooldown": 5.0,
                "hits_per_sec": 0.2,
                "active_in_rotation": True
            },
            {
                "id": "demolition",
                "name": "Demolition",
                "type": "Physical",
                "multiplier_formula": "PATK * 2.38 * 10",
                "cooldown": 30.0,
                "hits_per_sec": 0.0333,
                "active_in_rotation": True
            },
            {
                "id": "phantom",
                "name": "Phantom",
                "type": "Physical",
                "multiplier_formula": "PATK * 17.4",
                "cooldown": 0,
                "hits_per_sec": 0,
                "active_in_rotation": False
            },
            {
                "id": "spooky_lamp",
                "name": "Spooky Lamp",
                "type": "Physical",
                "multiplier_formula": "PATK * 20 * 6",
                "cooldown": 30.0,
                "hits_per_sec": 0.0333,
                "active_in_rotation": True
            }
        ],
        "default_baseline": {
            "base_level": 87,
            "job_level": 17,
            "stats": {
                "str": 100,
                "agi": 60,
                "vit": 100,
                "int": 30,
                "dex": 39,
                "luk": 50
            },
            "job_stats": {
                "str": 42,
                "agi": 19,
                "vit": 34,
                "int": 15,
                "dex": 30,
                "luk": 16
            },
            "battle_achievement": {
                "str": 72,
                "vit": 72,
                "final_pdmg_bonus": 0.24,
                "fire_enhance": 0.30,
                "max_hp_pct": 0.24,
                "final_pdmg_red": 0.16
            },
            "loadout": {
                "weapon": {"name": "Teeth Bone Broadsword", "type": "2H Sword", "level": 1, "refine": 10, "upgrade": 60, "enchant_city": "Prontera", "enchant_lv": 6, "cards": ["Minorous Card", "Skeleton Worker Card"]},
                "clothes": {"name": "Vesper's Shield", "type": "Clothes", "level": 1, "refine": 6, "upgrade": 30, "enchant_city": "Prontera", "enchant_lv": 4, "cards": []},
                "cloak": {"name": "Vesper's Cloak", "type": "Cloak", "level": 1, "refine": 6, "upgrade": 30, "enchant_city": "Prontera", "enchant_lv": 4, "cards": []},
                "shoes": {"name": "Vesper's Shoes", "type": "Shoes", "level": 1, "refine": 6, "upgrade": 30, "enchant_city": "Prontera", "enchant_lv": 4, "cards": []},
                "accessory_1": {"name": "Autumn Earrings", "type": "Accessory", "level": 1, "refine": 6, "upgrade": 15, "enchant_city": "Prontera", "enchant_lv": 4, "cards": []},
                "accessory_2": {"name": "Autumn Earrings", "type": "Accessory", "level": 1, "refine": 6, "upgrade": 15, "enchant_city": "Prontera", "enchant_lv": 4, "cards": []},
                "talisman": {"name": "Autumn Amulet", "type": "Talisman", "level": 1, "refine": 6, "upgrade": 15, "enchant_city": "Prontera", "enchant_lv": 4, "cards": []},
                "costume_head": {"name": "Default Headgear", "type": "Head", "level": 1, "refine": 0, "upgrade": 0, "enchant_city": "", "enchant_lv": 0, "cards": []},
                "costume_eyes": {"name": "Default Face", "type": "Face", "level": 1, "refine": 0, "upgrade": 0, "enchant_city": "", "enchant_lv": 0, "cards": []},
                "costume_mouth": {"name": "Default Mouth", "type": "Mouth", "level": 1, "refine": 0, "upgrade": 0, "enchant_city": "", "enchant_lv": 0, "cards": []},
                "costume_back": {"name": "Default Back", "type": "Back", "level": 1, "refine": 0, "upgrade": 0, "enchant_city": "", "enchant_lv": 0, "cards": []}
            },
            "buffs": {
                "elemental_converter": "Fire",
                "spear_flash": True,
                "concentration": True,
                "spooky_lamp": True,
                "pet_active": True
            },
            "target": {
                "name": "Lord of the Dead Lv.150",
                "level": 150,
                "element": "Shadow",
                "race": "Formless",
                "size": "Large",
                "p_def": 1200,
                "p_def_pct": 0.40,
                "final_p_def": 0.15,
                "final_p_dmg_red": 0.20
            }
        }
    }

    with open(OUT_DK_PATH, "w", encoding="utf-8") as f:
        json.dump(dragon_knight_manifest, f, ensure_ascii=False, indent=2)

    dk_size_kb = OUT_DK_PATH.stat().st_size / 1024
    print(f"Exported dragon_knight_manifest.json: {dk_size_kb:.2f} KB")

if __name__ == "__main__":
    compile_all()
