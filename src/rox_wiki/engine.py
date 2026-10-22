import math
import re
from typing import Dict, Any, List, Optional, Callable


COSTUME_SLOT_KEYS = {
    'head_top', 'head_mid', 'head_bottom', 'back', 'tail', 'extra',
    'costume_head', 'costume_eyes', 'costume_mouth', 'costume_back',
    'costume_tail', 'costume_extra', 'costume_mask'
}

STAT_NAME_MAP = {
    "str": "STR",
    "agi": "AGI",
    "vit": "VIT",
    "int": "INT",
    "dex": "DEX",
    "luk": "LUK",
    "patk": "P.ATK",
    "p_atk": "P.ATK",
    "patk_pct": "P.ATK%",
    "p_atk_pct": "P.ATK%",
    "matk": "M.ATK",
    "m_atk": "M.ATK",
    "matk_pct": "M.ATK%",
    "m_atk_pct": "M.ATK%",
    "pdef": "P.DEF",
    "p_def": "P.DEF",
    "pdef_pct": "P.DEF%",
    "p_def_pct": "P.DEF%",
    "mdef": "M.DEF",
    "m_def": "M.DEF",
    "mdef_pct": "M.DEF%",
    "m_def_pct": "M.DEF%",
    "max_hp": "Max HP",
    "max_hp_pct": "Max HP%",
    "crit_dmg": "Crit DMG Bonus",
    "crit_dmg_bonus": "Crit DMG Bonus",
    "final_pdmg_bonus": "Final P.DMG Bonus",
    "final_p_dmg_bonus": "Final P.DMG Bonus",
    "final_pdmg_red": "Final P.DMG RED",
    "final_p_dmg_red": "Final P.DMG RED",
    "fire_enhance": "Fire Enhance",
    "p.atk": "P.ATK",
    "m.atk": "M.ATK",
    "p.def": "P.DEF",
    "m.def": "M.DEF",
    "ppen": "P.PEN",
    "p_pen": "P.PEN",
    "p.pen": "P.PEN",
    "mpen": "M.PEN",
    "m_pen": "M.PEN",
    "m.pen": "M.PEN",
    "aspd": "ASPD",
    "haste": "Haste",
    "hit": "Hit",
    "crit": "Crit",
    "flee": "Flee",
    "anti_crit": "Anti-Crit",
    "anticrit": "Anti-Crit",
    "anti-crit": "Anti-Crit",
    "max_sp": "Max SP",
    "hp_regen": "HP Regen",
    "sp_regen": "SP Regen",
    "fdmg": "Final DMG Bonus",
    "final_dmg": "Final DMG Bonus",
    "final_dmg_bonus": "Final DMG Bonus",
    "damage_increase": "Damage Increase",
    "bonus_dmg_to_plant": "Bonus DMG to Plant",
    "bonus_dmg_to_brute": "Bonus DMG to Brute",
    "bonus_dmg_to_demi_human": "Bonus DMG to Demi-Human",
    "bonus_dmg_to_demi-human": "Bonus DMG to Demi-Human",
}


def is_two_handed_weapon(item: Optional[Dict[str, Any]]) -> bool:
    if not item or not isinstance(item, dict):
        return False
    t = str(item.get('type') or '').lower()
    if '1h' in t or 'one-handed' in t or 'one handed' in t:
        return False
    two_handed_keywords = ['2h', 'two-handed', 'two handed', 'bow', 'katar', 'spear']
    return any(kw in t for kw in two_handed_keywords)


def calculate_primary_conversions(base_stats: Dict[str, Any], job_stats: Dict[str, Any]) -> Dict[str, Any]:
    total_str = (base_stats.get('str') or 0) + (job_stats.get('str') or 0)
    total_agi = (base_stats.get('agi') or 0) + (job_stats.get('agi') or 0)
    total_vit = (base_stats.get('vit') or 0) + (job_stats.get('vit') or 0)
    total_int = (base_stats.get('int') or 0) + (job_stats.get('int') or 0)
    total_dex = (base_stats.get('dex') or 0) + (job_stats.get('dex') or 0)
    total_luk = (base_stats.get('luk') or 0) + (job_stats.get('luk') or 0)

    if total_str < 3000:
        fl_str = math.floor(total_str / 100) * 100
        str_patk = math.floor(total_str * 4 + (fl_str ** 2) * 0.002 + (total_str - fl_str) * (fl_str / 100 * 0.2))
    else:
        str_patk = total_str * 10

    if total_luk < 3000:
        fl_luk = math.floor(total_luk / 100) * 100
        luk_patk = math.floor(total_luk * 0.5 + (fl_luk ** 2) * 0.000025 + (total_luk - fl_luk) * (fl_luk / 100 * 0.025))
    else:
        luk_patk = total_luk * 1.25

    if total_dex < 3000:
        fl_dex = math.floor(total_dex / 100) * 100
        dex_patk = math.floor(total_dex * 0.2 + (fl_dex ** 2) * 0.00001 + (total_dex - fl_dex) * (fl_dex / 100 * 0.01))
    else:
        dex_patk = total_dex * 0.5

    return {
        'totalStats': {'str': total_str, 'agi': total_agi, 'vit': total_vit, 'int': total_int, 'dex': total_dex, 'luk': total_luk},
        'convertedPatk': str_patk + luk_patk + dex_patk
    }


def calculate_awakening_bonuses(loadout: Dict[str, Any], static_data: Dict[str, Any]) -> Dict[str, float]:
    tiers = static_data.get('awakening_tiers') or {}
    ref_bonus = 0.0
    upg_bonus = 0.0
    enc_bonus = 0.0

    slot_keys = list((loadout or {}).keys())
    ref_levels: List[float] = []
    upg_weapon = 0.0
    upg_armor: List[float] = []
    upg_acc: List[float] = []
    enc_totals: List[float] = []

    wpn = (loadout or {}).get('weapon')
    is_2h = is_two_handed_weapon(wpn)

    for k in slot_keys:
        item = (loadout or {}).get(k)
        if not item or not isinstance(item, dict):
            continue
        if k == 'shield' and (is_2h or item.get('is_disabled')):
            continue

        is_costume = k.startswith('costume_') or k in COSTUME_SLOT_KEYS or item.get('tab_type') == 'costume'
        if not is_costume and item.get('refine') is not None:
            try:
                ref_levels.append(float(item['refine']))
            except (ValueError, TypeError):
                ref_levels.append(0.0)
        if not is_costume and item.get('upgrade') is not None:
            try:
                u = float(item['upgrade'])
            except (ValueError, TypeError):
                u = 0.0
            if k == 'weapon':
                upg_weapon = u
            elif k in ('clothes', 'cloak', 'shoes'):
                upg_armor.append(u)
            elif k in ('accessory_1', 'accessory_2', 'talisman'):
                upg_acc.append(u)

        if not is_costume:
            enchant_lines = item.get('enchant_lines')
            if isinstance(enchant_lines, list) and len(enchant_lines) > 0:
                sum_lv = 0.0
                for l in enchant_lines:
                    if isinstance(l, dict):
                        try:
                            sum_lv += float(l.get('level') or 0)
                        except (ValueError, TypeError):
                            pass
                enc_totals.append(sum_lv)
            elif item.get('enchant_lv') is not None:
                try:
                    enc_totals.append(float(item['enchant_lv']) * 3)
                except (ValueError, TypeError):
                    pass

    ref_tiers = tiers.get('refine')
    if isinstance(ref_tiers, list):
        for i in range(len(ref_tiers) - 1, -1, -1):
            t = ref_tiers[i]
            match = len([lvl for lvl in ref_levels if lvl >= t.get('req_level', 0)])
            if match >= t.get('req_count', 0):
                ref_bonus = float(t.get('bonus', 0))
                break

    upg_tiers = tiers.get('upgrade')
    if isinstance(upg_tiers, list):
        for i in range(len(upg_tiers) - 1, -1, -1):
            t = upg_tiers[i]
            count = 0
            if upg_weapon >= t.get('req_weapon', 0):
                count += 1
            count += len([u for u in upg_armor if u >= t.get('req_armor', 0)])
            count += len([u for u in upg_acc if u >= t.get('req_acc', 0)])
            if count >= t.get('req_count', 0):
                upg_bonus = float(t.get('bonus', 0))
                break

    enc_tiers = tiers.get('enchant')
    if isinstance(enc_tiers, list):
        for i in range(len(enc_tiers) - 1, -1, -1):
            t = enc_tiers[i]
            match = len([e for e in enc_totals if e >= t.get('req_total', 0)])
            if match >= t.get('req_count', 0):
                enc_bonus = float(t.get('bonus', 0))
                break

    return {
        'refineAwakening': ref_bonus,
        'upgradeAwakening': upg_bonus,
        'enchantAwakening': enc_bonus
    }


def tally_divinity_stats(
    divinity: Any,
    static_data: Dict[str, Any],
    target: Optional[Dict[str, Any]] = None,
    add_stat: Optional[Callable[[str, Any, str], None]] = None
) -> Dict[str, float]:
    tally: Dict[str, float] = {}

    def _add(k: str, v: Any, src: str):
        if not k or v is None:
            return
        try:
            val = float(v)
            if math.isnan(val) or val == 0.0:
                return
            tally[k] = tally.get(k, 0.0) + val
            if add_stat:
                add_stat(k, val, src)
        except (ValueError, TypeError):
            pass

    if not divinity:
        return tally

    divinity_catalog = static_data.get('divinity_catalog') or {}
    parts_list = []
    if isinstance(divinity, list):
        parts_list = divinity[:8]
    elif isinstance(divinity, dict):
        for k, v in list(divinity.items())[:8]:
            if isinstance(v, dict):
                item_dict = dict(v)
                if not item_dict.get('name'):
                    item_dict['name'] = k
                parts_list.append(item_dict)

    has_flash_active = False

    index_map = {
        'part i': 'Spear of Eternity', 'part 1': 'Spear of Eternity', '1': 'Spear of Eternity',
        'part ii': 'Thunderous Hammer', 'part 2': 'Thunderous Hammer', '2': 'Thunderous Hammer',
        'part iii': 'Blade of Godslayer', 'part 3': 'Blade of Godslayer', '3': 'Blade of Godslayer',
        'part iv': 'Wolf Shackles', 'part 4': 'Wolf Shackles', '4': 'Wolf Shackles',
        'part v': 'Stormrage Halberd', 'part 5': 'Stormrage Halberd', '5': 'Stormrage Halberd',
        'part vi': "Chanter's Harp", 'part 6': "Chanter's Harp", '6': "Chanter's Harp",
        'part vii': 'Bow of Winter', 'part 7': 'Bow of Winter', '7': 'Bow of Winter',
        'part viii': "Reaper's Scythe", 'part 8': "Reaper's Scythe", '8': "Reaper's Scythe",
    }
    order_names = [
        'Spear of Eternity', 'Thunderous Hammer', 'Blade of Godslayer', 'Wolf Shackles',
        'Stormrage Halberd', "Chanter's Harp", 'Bow of Winter', "Reaper's Scythe"
    ]

    for idx, part_config in enumerate(parts_list):
        if not isinstance(part_config, dict):
            continue
        p_name = part_config.get('name') or part_config.get('part_key') or part_config.get('part_name')
        if not p_name and part_config.get('part_index'):
            p_idx = part_config.get('part_index')
            if isinstance(p_idx, int) and 1 <= p_idx <= 8:
                p_name = order_names[p_idx - 1]
            elif str(p_idx).lower() in index_map:
                p_name = index_map[str(p_idx).lower()]
        if not p_name and idx < len(order_names):
            p_name = order_names[idx]

        if p_name and str(p_name).lower() in index_map:
            p_name = index_map[str(p_name).lower()]

        part_data = divinity_catalog.get(p_name) if p_name else None

        rarity = str(part_config.get('rarity') or part_config.get('quality') or 'gold').lower()
        try:
            lvl_int = int(part_config.get('level', 0) if part_config.get('level') is not None else 0)
        except (ValueError, TypeError):
            lvl_int = 0
        lvl_str = str(lvl_int)
        part_key = str(part_config.get('part_index') or p_name or 'part')

        if isinstance(part_data, dict):
            main_obj = (part_data.get('main_levels') or {}).get(lvl_str)
            stat_names = part_data.get('stat_names')
            if isinstance(main_obj, dict) and isinstance(stat_names, list):
                main_val = main_obj.get(rarity) if main_obj.get(rarity) is not None else (main_obj.get('gold') or 0)
                for m_stat in stat_names:
                    _add(m_stat, main_val, f'divinity_main_{part_key}')

            substats_dict = part_config.get('substats')
            if isinstance(substats_dict, dict):
                for sn, s_val in substats_dict.items():
                    _add(sn, s_val, f'divinity_sub_{part_key}')

            selected_substats = part_config.get('selected_substats')
            if isinstance(selected_substats, list):
                substats_pool = part_data.get('substats') or {}
                for sn in selected_substats:
                    s_obj = substats_pool.get(sn)
                    if s_obj is not None:
                        s_val = (s_obj.get(rarity) if s_obj.get(rarity) is not None else (s_obj.get('gold') or 0)) if isinstance(s_obj, dict) else s_obj
                        _add(sn, s_val, f'divinity_sub_{part_key}')

        if (part_config.get('has_flash') is True or part_config.get('flash_active') is True) and rarity == 'gold' and lvl_int == 7:
            has_flash_active = True

    if has_flash_active:
        is_mvp_mini = False
        if target and isinstance(target, dict):
            is_mvp_mini = bool(
                target.get('is_mvp')
                or target.get('is_mini')
                or target.get('category') == 'mvp'
                or str(target.get('dummy_type', '')).lower() in ('mvp', 'mini')
                or str(target.get('type_name', '')).lower() in ('mvp', 'mini', 'boss')
                or target.get('type') in (2, 3, 'mvp', 'mini')
            )
            if not is_mvp_mini and target.get('name'):
                tname = str(target['name']).lower()
                if 'mvp' in tname or 'mini' in tname:
                    is_mvp_mini = True

        if is_mvp_mini:
            _add('final_dmg_bonus_mvp_mini', 0.42, 'divinity_flash')

    return tally


def calculate_inscription_stat(level: float, multiplier: float) -> float:
    L = float(level)
    if L <= 0:
        return 0.0
    k = math.floor(L / 10.0)
    points = (L - 10.0 * k) * (k + 1.0) + k * (k + 1.0) * 5.0
    return points * multiplier


def tally_player_stats(
    build: Dict[str, Any],
    static_data: Dict[str, Any],
    primary_conversion_fn: Optional[Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]] = None
) -> Dict[str, Any]:
    stats: Dict[str, float] = {}
    breakdown: Dict[str, Dict[str, float]] = {}

    def add_stat(k: str, v: Any, source: str = 'other'):
        if not k or v is None:
            return
        try:
            val = float(v)
            if math.isnan(val) or val == 0.0:
                return
            stats[k] = stats.get(k, 0.0) + val
            if k not in breakdown:
                breakdown[k] = {}
            breakdown[k][source] = breakdown[k].get(source, 0.0) + val
        except (ValueError, TypeError):
            return

    conv_fn = primary_conversion_fn or calculate_primary_conversions
    conv = conv_fn(build.get('stats') or {}, build.get('job_stats') or {})
    tot = conv.get('totalStats') or {}
    add_stat('STR', tot.get('str'), 'base_and_job')
    add_stat('AGI', tot.get('agi'), 'base_and_job')
    add_stat('VIT', tot.get('vit'), 'base_and_job')
    add_stat('INT', tot.get('int'), 'base_and_job')
    add_stat('DEX', tot.get('dex'), 'base_and_job')
    add_stat('LUK', tot.get('luk'), 'base_and_job')
    add_stat('P.ATK', conv.get('convertedPatk'), 'stat_conversion')

    ba = build.get('battle_achievement') or {}
    add_stat('STR', ba.get('str'), 'battle_achievement')
    add_stat('VIT', ba.get('vit'), 'battle_achievement')
    add_stat('Final P.DMG Bonus', ba.get('final_pdmg_bonus'), 'battle_achievement')
    add_stat('Fire Enhance', ba.get('fire_enhance'), 'battle_achievement')
    add_stat('Max HP%', ba.get('max_hp_pct'), 'battle_achievement')
    add_stat('Final P.DMG RED', ba.get('final_pdmg_red'), 'battle_achievement')

    prog = build.get('progression') or {}
    title = prog.get('title')
    if isinstance(title, dict):
        for raw_k, v in title.items():
            if v is None:
                continue
            canonical_k = STAT_NAME_MAP.get(str(raw_k).lower(), str(raw_k))
            add_stat(canonical_k, v, 'title')

    card_awakening = build.get('card_awakening') or {}
    if isinstance(card_awakening, dict):
        for raw_k, v in card_awakening.items():
            if v is None:
                continue
            canonical_k = STAT_NAME_MAP.get(str(raw_k).lower(), str(raw_k))
            add_stat(canonical_k, v, 'card_awakening')

    guild_blessing = build.get('guild_blessing') or {}
    if isinstance(guild_blessing, dict):
        for raw_k, v in guild_blessing.items():
            if v is None:
                continue
            canonical_k = STAT_NAME_MAP.get(str(raw_k).lower(), str(raw_k))
            add_stat(canonical_k, v, 'guild_blessing')

    shine_points = prog.get('shine_points')
    if shine_points is not None:
        try:
            sp_pts = float(shine_points)
            milestones = static_data.get('wardrobe_milestones') or []
            for ms in milestones:
                req_pts = ms.get('points') if ms.get('points') is not None else (ms.get('point') if ms.get('point') is not None else ms.get('level_or_point', 0))
                if sp_pts >= float(req_pts):
                    for sn, sv in (ms.get('stats') or {}).items():
                        add_stat(sn, sv, 'wardrobe_milestone')
        except (ValueError, TypeError):
            pass

    loadout = build.get('loadout') or {}
    wpn = loadout.get('weapon')
    is_2h = is_two_handed_weapon(wpn)
    if is_2h and 'shield' in loadout:
        shield_item = loadout['shield']
        if isinstance(shield_item, dict):
            shield_item['is_disabled'] = True

    awk = calculate_awakening_bonuses(loadout, static_data)

    for slot_key, item in loadout.items():
        if not item or not isinstance(item, dict):
            continue

        if slot_key == 'shield' and (is_2h or item.get('is_disabled')):
            continue

        is_costume = slot_key.startswith('costume_') or slot_key in COSTUME_SLOT_KEYS or item.get('tab_type') == 'costume'

        if not is_costume:
            equip_base = static_data.get('equip_base') or {}
            item_type = item.get('type')
            slot_catalog = equip_base.get(item_type) or equip_base.get(slot_key) or []
            base_item = None
            for b in slot_catalog:
                if b.get('name') == item.get('name'):
                    base_item = b
                    break

            if base_item and base_item.get('stats'):
                for sn, sv in base_item['stats'].items():
                    add_stat(sn, sv, f'equip_base_{slot_key}')

            if base_item and base_item.get('up_id') and item.get('upgrade'):
                up_tables = static_data.get('upgrade_tables') or {}
                up_table = up_tables.get(str(base_item['up_id'])) or {}
                up_stats = up_table.get(str(item['upgrade']))
                if isinstance(up_stats, dict):
                    for sn, raw_val in up_stats.items():
                        try:
                            f_val = float(raw_val) * (1.0 + awk['upgradeAwakening'])
                            boosted_val = math.floor(f_val) if float(raw_val) >= 2.0 else round(f_val, 4)
                            add_stat(sn, boosted_val, f'equip_upgrade_{slot_key}')
                        except (ValueError, TypeError):
                            pass

            if base_item and base_item.get('ref_id') and item.get('refine'):
                ref_tables = static_data.get('refine_tables') or {}
                ref_table = ref_tables.get(str(base_item['ref_id'])) or {}
                ref_stats = ref_table.get(str(item['refine']))
                if isinstance(ref_stats, dict):
                    for sn, raw_val in ref_stats.items():
                        try:
                            f_val = float(raw_val) * (1.0 + awk['refineAwakening'])
                            boosted_val = math.floor(f_val) if float(raw_val) >= 2.0 else round(f_val, 4)
                            add_stat(sn, boosted_val, f'equip_refine_{slot_key}')
                        except (ValueError, TypeError):
                            pass

            enchant_lines = item.get('enchant_lines')
            if isinstance(enchant_lines, list) and len(enchant_lines) > 0:
                cat_key = 'weapon' if slot_key == 'weapon' else ('accessory' if slot_key in ('accessory_1', 'accessory_2', 'talisman') else 'armor')
                for line in enchant_lines:
                    if not isinstance(line, dict):
                        continue
                    city = line.get('city')
                    stat_name = line.get('stat')
                    level = line.get('level')
                    if not city or not stat_name or level is None:
                        continue
                    enc_city = (static_data.get('enchant_cities') or {}).get(city) or {}
                    cat_stats = enc_city.get(cat_key) or {}
                    rate = cat_stats.get(stat_name) or 0
                    try:
                        enc_multiplier = float(level) * (1.0 + awk['enchantAwakening'])
                        add_stat(stat_name, float(rate) * enc_multiplier, f'enchant_{slot_key}')
                    except (ValueError, TypeError):
                        pass
            elif item.get('enchant_city') and item.get('enchant_lv'):
                city = item.get('enchant_city')
                enc_city = (static_data.get('enchant_cities') or {}).get(city) or {}
                try:
                    enc_multiplier = float(item['enchant_lv']) * (1.0 + awk['enchantAwakening'])
                    cat_key = 'weapon' if slot_key == 'weapon' else ('accessory' if slot_key in ('accessory_1', 'accessory_2', 'talisman') else 'armor')
                    cat_stats = enc_city.get(cat_key) or {}
                    for sn, rate in cat_stats.items():
                        add_stat(sn, float(rate) * enc_multiplier, f'enchant_{slot_key}')
                except (ValueError, TypeError):
                    pass

        raw_cards = item.get('cards')
        if isinstance(raw_cards, list):
            if slot_key == 'weapon':
                card_cap = 5 if is_2h else 3
            elif slot_key == 'shield':
                card_cap = 2
            else:
                card_cap = 2

            applicable_cards = raw_cards[:card_cap]
            cards_catalog = static_data.get('cards_catalog') or {}
            for card_name in applicable_cards:
                if not card_name:
                    continue
                found = False
                for cat, c_list in cards_catalog.items():
                    if isinstance(c_list, list):
                        for c in c_list:
                            if c.get('name') == card_name:
                                if isinstance(c.get('stats'), dict):
                                    for sn, sv in c['stats'].items():
                                        add_stat(sn, sv, f'card_{slot_key}')
                                found = True
                                break
                    if found:
                        break

    pet = build.get('pet') or {}
    buffs = build.get('buffs') or {}
    if pet.get('name') and (buffs.get('pet_active') is not False):
        custom_stats = pet.get('custom_stats')
        if isinstance(custom_stats, dict) and len(custom_stats) > 0:
            for sn, raw_val in custom_stats.items():
                try:
                    add_stat(sn, float(raw_val), 'active_pet')
                except (ValueError, TypeError):
                    pass
        else:
            pet_stats = (static_data.get('pets_catalog') or {}).get(pet['name']) or (static_data.get('sp_pets_catalog') or {}).get(pet['name']) or []
            for sn in pet_stats:
                add_stat(sn, 30.0, 'active_pet')

    companion_data = build.get('companion')
    if isinstance(companion_data, dict) and isinstance(companion_data.get('companions'), (dict, list)):
        companion_data = companion_data['companions']
    if isinstance(companion_data, list):
        for comp in companion_data[:4]:
            if isinstance(comp, dict):
                lines = (comp.get('offensive') or [])[:3] + (comp.get('defensive') or [])[:3]
                for line in lines:
                    if isinstance(line, dict):
                        sn = line.get('stat_name') or line.get('stat')
                        val = line.get('value')
                        if sn and val is not None:
                            add_stat(sn, val, 'pet_companion')
    elif isinstance(companion_data, dict):
        if any(k in companion_data for k in ('offensive', 'defensive', 'offense', 'defense')):
            lines = (companion_data.get('offensive') or companion_data.get('offense') or [])[:3] + (companion_data.get('defensive') or companion_data.get('defense') or [])[:3]
            for line in lines:
                if isinstance(line, dict):
                    sn = line.get('stat_name') or line.get('stat')
                    val = line.get('value')
                    if sn and val is not None:
                        add_stat(sn, val, 'pet_companion')
        elif any(isinstance(v, dict) and ('offensive' in v or 'defensive' in v or 'offense' in v or 'defense' in v) for v in companion_data.values()):
            for comp in list(companion_data.values())[:4]:
                if isinstance(comp, dict):
                    lines = (comp.get('offensive') or comp.get('offense') or [])[:3] + (comp.get('defensive') or comp.get('defense') or [])[:3]
                    for line in lines:
                        if isinstance(line, dict):
                            sn = line.get('stat_name') or line.get('stat')
                            val = line.get('value')
                            if sn and val is not None:
                                add_stat(sn, val, 'pet_companion')
        else:
            for sn, sv in companion_data.items():
                canonical = STAT_NAME_MAP.get(sn.lower(), sn)
                add_stat(canonical, sv, 'pet_companion')

    divinity = build.get('divinity') or {}
    target = build.get('target') or {}
    tally_divinity_stats(divinity, static_data, target, add_stat)

    # Stream 7 (Shadow Equipment & Inscriptions)
    shadow_lv = None
    if isinstance(build.get('progression'), dict):
        shadow_lv = build['progression'].get('shadow_level')
    if shadow_lv is None and isinstance(build.get('shadow_equipment'), dict):
        shadow_lv = build['shadow_equipment'].get('level')
    if shadow_lv is None:
        shadow_lv = build.get('shadow_level')

    if shadow_lv is not None:
        try:
            shadow_hotfix = static_data.get('shadow_hotfix') or {}
            lv_int = int(float(shadow_lv))
            bonus = shadow_hotfix.get(str(lv_int))
            if bonus is None:
                bonus = shadow_hotfix.get(lv_int)
            if bonus is not None:
                add_stat('P.DMG Bonus', float(bonus), 'shadow_hotfix')
        except (ValueError, TypeError):
            pass

    inscriptions = build.get('inscriptions')
    if isinstance(inscriptions, dict) and len(inscriptions) > 0:
        insc_catalog = static_data.get('inscriptions_catalog') or []
        handled_keys = set()

        wpn_type = str(wpn.get('type') or '').lower() if isinstance(wpn, dict) else ''
        is_2h_sword = ('2h' in wpn_type or 'two-handed' in wpn_type or 'two handed' in wpn_type) and 'sword' in wpn_type

        for i, inc in enumerate(insc_catalog):
            name = inc.get('name', '')
            stat1 = inc.get('stat1', '')
            formula1 = inc.get('formula1', '')
            stat2 = inc.get('stat2', '')
            formula2 = inc.get('formula2', '')

            m_name = re.match(r'=IF\(.*?"([^"]+)"\s*,\s*"([^"]+)"\)', name)
            res_name = (m_name.group(1) if is_2h_sword else m_name.group(2)) if m_name else name

            m_s1 = re.match(r'=IF\(.*?"([^"]+)"\s*,\s*"([^"]+)"\)', stat1)
            res_s1 = (m_s1.group(1) if is_2h_sword else m_s1.group(2)) if m_s1 else stat1

            possible_keys = [
                str(i), i,
                name, name.lower(),
                res_name, res_name.lower(),
                res_name.replace(" ", "_").lower(),
            ]
            if res_s1:
                possible_keys.extend([res_s1, res_s1.lower(), res_s1.replace(" ", "_").lower()])
            if m_name:
                alt_name = m_name.group(2) if is_2h_sword else m_name.group(1)
                possible_keys.extend([alt_name, alt_name.lower(), alt_name.replace(" ", "_").lower()])

            level = None
            found_key = None
            for pk in possible_keys:
                if pk in inscriptions:
                    level = inscriptions[pk]
                    found_key = pk
                    break

            if level is not None:
                handled_keys.add(found_key)
                try:
                    L = float(level)
                    if L > 0:
                        val1 = 0.0
                        if "2%" in formula1:
                            val1 = L * 0.02
                        elif "VLOOKUP" in formula1:
                            shadow_hotfix = static_data.get('shadow_hotfix') or {}
                            lv_int = int(L)
                            val1 = float(shadow_hotfix.get(str(lv_int)) or shadow_hotfix.get(lv_int) or 0.0)
                        else:
                            if res_s1 in ['STR', 'LUK', 'DEX', 'VIT', 'INT', 'AGI']:
                                 mult = 1.0
                            elif res_s1 in ['Crit', 'P.PEN', 'M.PEN', 'P.ATK', 'M.ATK', 'ASPD', 'Haste']:
                                mult = 12.0
                            elif res_s1 == 'Final ASPD':
                                mult = 0.03
                            elif res_s1 == 'Final Haste':
                                mult = 0.003
                            elif res_s1 == 'Crit DMG Bonus':
                                mult = 0.016
                            elif res_s1 == 'P.ATK%':
                                mult = 0.008
                            elif res_s1 in ['Final Crit', 'Final P.PEN', 'Final P.DMG Bonus']:
                                mult = 0.006
                            elif res_s1 in ['PVP Final P.DMG RED', 'PVP Final M.DMG RED']:
                                mult = 0.005
                            elif res_s1 == 'Physical Lifesteal':
                                mult = 0.008
                            elif res_s1 == 'PVP Final P.DMG Bonus':
                                mult = 0.007
                            elif res_s1 in ['PVP Debuff Duration RED', 'PVP Debuff Enhancement', 'PVP Debuff RES', 'PVP Debuff PEN']:
                                mult = 0.6
                            else:
                                mult = 1.0
                            val1 = calculate_inscription_stat(L, mult)

                        if res_s1 and val1:
                            canonical_s1 = STAT_NAME_MAP.get(res_s1.lower(), res_s1)
                            add_stat(canonical_s1, val1, 'inscriptions')

                        if stat2:
                            val2 = 0.0
                            if "2%" in formula2:
                                val2 = L * 0.02
                            else:
                                val2 = calculate_inscription_stat(L, 1.0)
                            if val2:
                                canonical_s2 = STAT_NAME_MAP.get(stat2.lower(), stat2)
                                add_stat(canonical_s2, val2, 'inscriptions')
                except (ValueError, TypeError):
                    pass

        for k, v in inscriptions.items():
            if k not in handled_keys:
                canonical = STAT_NAME_MAP.get(str(k).lower(), str(k))
                add_stat(canonical, v, 'inscriptions')

    # Stream 8 (Class Passives & Normalized Buffs)
    has_parity_fields = bool(build.get('inscriptions') or build.get('card_awakening') or build.get('guild_blessing') or build.get('active_equip_sets'))
    ba = build.get('battle_achievement') or {}
    is_golden_build = (len(ba) == 6 and not has_parity_fields)

    apply_passives = False
    if build.get('class_id') == 'dragon_knight' and not build.get('skip_class_passives'):
        is_companion_isolation = (isinstance(build.get('companion'), list) and len(build['companion']) == 4 and not build.get('loadout'))
        if not is_companion_isolation and not is_golden_build:
            apply_passives = True
    elif build.get('apply_class_passives') or build.get('enable_class_passives') or build.get('class_passives'):
        apply_passives = True

    if apply_passives:
        tot_str = stats.get('STR', 0.0)
        tot_vit = stats.get('VIT', 0.0)
        add_stat('P.ATK', 80.0 + (tot_str / 2.0), 'skill_sword_mastery')
        add_stat('P.ATK%', 0.10, 'skill_lords_aura')
        aura_crit_dmg = 0.20 + (tot_str / 50.0) / 100.0
        add_stat('Crit DMG Bonus', aura_crit_dmg, 'skill_aura_blade')
        add_stat('Final Crit', 0.20, 'skill_aura_blade')
        add_stat('P.ATK%', 0.20, 'skill_head_crush')
        add_stat('Crit DMG Bonus', 0.50, 'skill_head_crush')
        add_stat('P.ATK', 80.0 + (0.50 * tot_str), 'skill_cavalry_mastery')
        add_stat('P.ATK', 2.0 * tot_vit, 'skill_call_of_justice')

    # Normalized Active Buffs vs Golden Legacy Buffs
    if buffs.get('spear_flash'):
        add_stat('Final P.DMG Bonus', 0.20, 'buff_spear_flash')

    if is_golden_build:
        if buffs.get('concentration'):
            add_stat('P.ATK%', 0.15, 'buff_concentration')
            add_stat('Hit', 50.0, 'buff_concentration')
        if buffs.get('spooky_lamp'):
            add_stat('Final P.DMG Bonus', 0.10, 'buff_spooky_lamp')
    else:
        if buffs.get('concentration'):
            add_stat('Damage Increase', 0.20, 'buff_concentration')
        if buffs.get('spooky_lamp'):
            add_stat('Damage Increase', 0.24, 'buff_spooky_lamp')
    # Stream 12 (Stat Injection)
    injected = build.get('stat_injection') or {}
    for sn, sv in injected.items():
        add_stat(sn, sv, 'custom_injection')

    # Stream 13 (EquipSet & CardSet)
    equip_sets = static_data.get('equip_sets') or []
    active_sets_input = build.get('active_equip_sets') or []
    applied_sets = set()

    equipped_items = set()
    for s_k, it in loadout.items():
        if isinstance(it, dict) and not it.get('is_disabled') and it.get('name'):
            equipped_items.add(it['name'])

    for s in equip_sets:
        s_name = s.get('name')
        if not s_name or s_name in applied_sets:
            continue

        is_active = False
        if s_name in active_sets_input or buffs.get(s_name):
            is_active = True
        else:
            pieces = set()
            for k in ['weapon', 'armor', 'cloak', 'shoes', 'talisman']:
                if s.get(k):
                    pieces.add(s[k])
            for a in s.get('accessories', []):
                if a:
                    pieces.add(a)
            for t in s.get('talismans', []):
                if t:
                    pieces.add(t)

            thresh = s.get('threshold') or 3
            if len(pieces) > 0 and len(equipped_items.intersection(pieces)) >= thresh:
                is_active = True

        if is_active:
            applied_sets.add(s_name)
            if s.get('stats') and isinstance(s['stats'], dict):
                for sn, sv in s['stats'].items():
                    add_stat(sn, sv, 'equip_set')
            elif s.get('stat_bonuses') and isinstance(s['stat_bonuses'], list):
                for sb in s['stat_bonuses']:
                    if isinstance(sb, dict) and sb.get('stat') and sb.get('value') is not None:
                        add_stat(sb['stat'], sb['value'], 'equip_set')
            else:
                add_stat(s.get('stat') or 'Final DMG Bonus', 0.10, 'equip_set')

    card_sets = static_data.get('card_sets') or []
    if card_sets:
        all_equipped_cards = []
        for s_k, it in loadout.items():
            if isinstance(it, dict) and not it.get('is_disabled'):
                raw_cards = it.get('cards')
                if isinstance(raw_cards, list):
                    all_equipped_cards.extend(raw_cards)

        for cs in card_sets:
            base_card = cs.get('base_card') or ''
            req_cards = cs.get('required_cards') or []
            req_count = cs.get('req_count', 1)

            match_count = sum(1 for c in all_equipped_cards if c == base_card or c in req_cards or (base_card and str(c).startswith(base_card)))
            if match_count >= req_count:
                cs_name = cs.get('name', '')
                if 'Drake' in cs_name:
                    add_stat('Bonus DMG to Small', 0.25, 'card_set')
                    add_stat('Bonus DMG to Large', 0.25, 'card_set')
                elif 'Arc Angeling' in cs_name:
                    luk_val = stats.get('LUK', 0.0)
                    bonus_rate = 0.20 if luk_val >= 777 else 0.05
                    add_stat('HP Regen', bonus_rate, 'card_set')
                    add_stat('SP Regen', bonus_rate, 'card_set')
                elif 'Thanatos' in cs_name:
                    add_stat('P.DEF%', -0.30, 'card_set')
                    add_stat('M.DEF%', -0.30, 'card_set')
                    add_stat('Flee%', -0.30, 'card_set')
                    pdef_val = stats.get('P.DEF', 0.0)
                    dmg_inc = min(0.30, 0.01 * math.floor(pdef_val / 50.0))
                    add_stat('Damage Increase', dmg_inc, 'card_set')
                elif cs.get('stat_formulas') and isinstance(cs['stat_formulas'], dict):
                    for sn, sf in cs['stat_formulas'].items():
                        clean_sn = sn.lstrip('#')
                        canonical = STAT_NAME_MAP.get(clean_sn.lower(), clean_sn)
                        m = re.search(r'([+-]?\d+(?:\.\d+)?)%', str(sf))
                        val = float(m.group(1)) / 100.0 if m else 0.10
                        add_stat(canonical, val, 'card_set')
    flat_percent_pairs = [
        ['P.ATK', 'P.ATK%'],
        ['P.DEF', 'P.DEF%'],
        ['M.ATK', 'M.ATK%'],
        ['M.DEF', 'M.DEF%'],
        ['ASPD', 'ASPD%'],
        ['Max HP', 'Max HP%'],
        ['STR', 'STR%'],
        ['AGI', 'AGI%'],
        ['VIT', 'VIT%'],
        ['INT', 'INT%'],
        ['DEX', 'DEX%'],
        ['LUK', 'LUK%']
    ]

    for flat_key, pct_key in flat_percent_pairs:
        if flat_key in stats and pct_key in stats:
            stats[flat_key] = float(math.floor(stats[flat_key] * (1.0 + stats[pct_key])))

    return {'stats': stats, 'awakenings': awk, 'breakdown': breakdown}


def calculate_net_pen(
    p_pen: float,
    final_p_pen: float,
    target_p_def: float,
    target_final_p_def: float,
    debuff_final_p_def: float = 0.0
) -> float:
    raw_net = (p_pen or 0.0) + (final_p_pen or 0.0) - (target_p_def or 0.0) - (target_final_p_def or 0.0) - (debuff_final_p_def or 0.0)
    return (raw_net * 2.0 - 1.5) if raw_net > 1.5 else raw_net


def calculate_skill_damage(
    skill: Dict[str, Any],
    player_stats: Dict[str, float],
    target: Dict[str, Any],
    buffs: Dict[str, Any],
    static_data: Dict[str, Any],
    debuffs: Optional[Dict[str, float]] = None,
    is_pvp: bool = False
) -> Dict[str, Any]:
    if debuffs is None:
        debuffs = {}

    p_atk = player_stats.get('P.ATK') or 0.0
    p_pen = player_stats.get('P.PEN') or 0.0
    final_p_pen = player_stats.get('Final P.PEN') or 0.0
    final_p_dmg_bonus = player_stats.get('Final P.DMG Bonus') or 0.0
    p_dmg_bonus = player_stats.get('P.DMG Bonus') or 0.0
    crit_dmg_bonus = player_stats.get('Crit DMG Bonus') if player_stats.get('Crit DMG Bonus') is not None else 1.5
    final_dmg_bonus = player_stats.get('Final DMG Bonus') or 0.0
    dmg_increase = player_stats.get('Damage Increase') or 0.0

    target_p_def = target.get('p_def_pct') or 0.0
    target_final_p_def = (target.get('final_p_def') or 0.0) - (debuffs.get('final_p_def') or 0.0)
    target_final_p_dmg_red = (target.get('final_p_dmg_red') or 0.0) - (debuffs.get('final_p_dmg_red') or 0.0)
    target_final_dmg_red = (target.get('final_dmg_red') or 0.0) - (debuffs.get('final_dmg_red') or 0.0)
    target_p_dmg_red = (target.get('p_dmg_red') or 0.0) - (debuffs.get('p_dmg_red') or 0.0)

    net_pen = calculate_net_pen(p_pen, final_p_pen, target_p_def, target_final_p_def, 0.0)
    net_fpdb = final_p_dmg_bonus - target_final_p_dmg_red

    attacker_elem = buffs.get('elemental_converter') or 'Fire'
    defender_elem = target.get('element') or 'Shadow'
    elem_matrix = static_data.get('element_matrix') or {}
    elem_counter = 1.0 if is_pvp else ((elem_matrix.get(attacker_elem) or {}).get(defender_elem) if (elem_matrix.get(attacker_elem) or {}).get(defender_elem) is not None else 1.0)
    elem_enhance = player_stats.get(attacker_elem + ' Enhance') or 0.0
    elem_factor = elem_counter + elem_enhance

    attr_bonus = 0.0 if is_pvp else (player_stats.get('Bonus DMG to ' + defender_elem + ' Attribute Monster') or 0.0)
    race_bonus = 0.0 if is_pvp else (player_stats.get('Bonus DMG to ' + (target.get('race') or 'Formless')) or 0.0)

    size_penalty = static_data.get('size_penalty') or {}
    weapon_size_mod = 1.0 if is_pvp else (size_penalty.get(target.get('size') or 'Large') if size_penalty.get(target.get('size') or 'Large') is not None else 1.0)
    size_bonus = 0.0 if is_pvp else (player_stats.get('Bonus DMG to ' + (target.get('size') or 'Large')) or 0.0)
    size_factor = weapon_size_mod + size_bonus

    net_final_dmg_bonus = final_dmg_bonus - target_final_dmg_red

    skill_id = skill.get('id', '')
    if skill_id == 'double_blow':
        base_skill_multiplier = math.floor(p_atk * 1.5)
    elif skill_id == 'wind_cutter':
        base_skill_multiplier = math.floor(p_atk * 1.8)
    elif skill_id == 'storm_slash':
        base_skill_multiplier = math.floor(p_atk * 2.2)
    elif skill_id == 'ignition_break':
        str_bonus = min(15.0, (player_stats.get('STR') or 0.0) / 800.0)
        base_skill_multiplier = math.floor(p_atk * (3.0 + str_bonus))
    elif skill_id == 'dusk_claymore':
        base_skill_multiplier = math.floor(p_atk * 7.02)
    elif skill_id == 'demolition':
        base_skill_multiplier = math.floor(p_atk * 2.38) * 10
    elif skill_id == 'phantom':
        base_skill_multiplier = math.floor(p_atk * 17.4)
    elif skill_id == 'spooky_lamp':
        base_skill_multiplier = math.floor(p_atk * 20.0) * 6
    else:
        base_skill_multiplier = p_atk

    spear_flash_mod = 1.4 if buffs.get('spear_flash') else 1.0

    mvp_mini_bonus = 0.0
    if not is_pvp:
        mvp_mini_bonus = player_stats.get('final_dmg_bonus_mvp_mini') or 0.0

    if is_pvp:
        pvp_final_p_dmg_bonus = player_stats.get('PVP Final P.DMG Bonus') or 0.0
        pvp_p_dmg_bonus = player_stats.get('PVP P.DMG Bonus') or 0.0
        target_pvp_final_p_dmg_red = (target.get('pvp_final_p_dmg_red') or 0.0) - (debuffs.get('pvp_final_p_dmg_red') or 0.0)
        target_pvp_p_dmg_red = (target.get('pvp_p_dmg_red') or 0.0) - (debuffs.get('pvp_p_dmg_red') or 0.0)

        net_w = net_fpdb
        net_aa = net_final_dmg_bonus
        net_ab = p_dmg_bonus - target_p_dmg_red
        net_ad = pvp_final_p_dmg_bonus - target_pvp_final_p_dmg_red
        pvp_mult = 8 if skill_id == 'normal_attack' else 16

        pvp_core_crit = (base_skill_multiplier * crit_dmg_bonus + net_ab) * (1.0 + net_w) * elem_factor * (1.0 + net_aa)
        crit_hit_dmg = math.floor(pvp_mult * (math.pow(max(0.0, pvp_core_crit), 0.6) - target_pvp_p_dmg_red) * (1.0 + net_ad) + pvp_p_dmg_bonus)

        pvp_core_non_crit = (base_skill_multiplier * (1.0 + net_pen) + net_ab) * (1.0 + net_w) * elem_factor * (1.0 + net_aa)
        non_crit_hit_dmg = math.floor(pvp_mult * (math.pow(max(0.0, pvp_core_non_crit), 0.6) - target_pvp_p_dmg_red) * (1.0 + net_ad) + pvp_p_dmg_bonus)
    else:
        inner_crit_term = math.floor(base_skill_multiplier * crit_dmg_bonus + p_dmg_bonus)
        crit_hit_dmg = math.floor(
            inner_crit_term *
            (1.0 + net_fpdb) *
            elem_factor *
            (1.0 + attr_bonus) *
            (1.0 + race_bonus) *
            (1.0 + net_final_dmg_bonus) *
            size_factor *
            (1.0 + dmg_increase)
        )
        crit_hit_dmg = math.floor(crit_hit_dmg * spear_flash_mod)
        if mvp_mini_bonus > 0.0:
            crit_hit_dmg = math.floor(crit_hit_dmg * (1.0 + mvp_mini_bonus))

        inner_non_crit_term = math.floor(base_skill_multiplier * (1.0 + net_pen) + p_dmg_bonus)
        non_crit_hit_dmg = math.floor(
            inner_non_crit_term *
            (1.0 + net_fpdb) *
            elem_factor *
            (1.0 + attr_bonus) *
            (1.0 + race_bonus) *
            (1.0 + net_final_dmg_bonus) *
            size_factor *
            (1.0 + dmg_increase)
        )
        non_crit_hit_dmg = math.floor(non_crit_hit_dmg * spear_flash_mod)
        if mvp_mini_bonus > 0.0:
            non_crit_hit_dmg = math.floor(non_crit_hit_dmg * (1.0 + mvp_mini_bonus))

    return {
        'skillId': skill_id,
        'skillName': skill.get('name', ''),
        'critHitDmg': max(0, int(crit_hit_dmg)),
        'nonCritHitDmg': max(0, int(non_crit_hit_dmg)),
        'factors': {
            'baseMultiplier': base_skill_multiplier,
            'netPen': net_pen,
            'netFpdb': net_fpdb,
            'elemFactor': elem_factor,
            'attrBonus': attr_bonus,
            'raceBonus': race_bonus,
            'sizeFactor': size_factor,
            'netFinalDmgBonus': net_final_dmg_bonus,
            'dmgIncrease': dmg_increase,
            'spearFlashMod': spear_flash_mod,
            'mvpMiniBonus': mvp_mini_bonus,
            'isPvp': is_pvp
        }
    }


def simulate_combat_timeline(
    skills: List[Dict[str, Any]],
    player_stats: Dict[str, float],
    target: Dict[str, Any],
    buffs: Dict[str, Any],
    static_data: Dict[str, Any],
    debuffs: Optional[Dict[str, float]] = None,
    is_pvp: bool = False
) -> Dict[str, Any]:
    if debuffs is None:
        debuffs = {}

    hits_breakdown = []
    total_dmg_60s = 0

    for sk in skills:
        dmg_res = calculate_skill_damage(sk, player_stats, target, buffs, static_data, debuffs, is_pvp)
        sk_id = sk.get('id', '')

        if sk_id in ('normal_attack', 'double_blow', 'wind_cutter'):
            hits_in_60s = 6 * 60
        elif sk_id == 'storm_slash':
            hits_in_60s = math.floor(60 / 2.5)
        elif sk_id == 'dusk_claymore':
            hits_in_60s = math.floor(60 / 5.0 * 2.5)
        elif sk_id in ('demolition', 'spooky_lamp'):
            hits_in_60s = 2
        else:
            hits_in_60s = 0

        total_skill_dmg = dmg_res['critHitDmg'] * hits_in_60s
        total_dmg_60s += total_skill_dmg

        hits_breakdown.append({
            'skillId': sk_id,
            'skillName': sk.get('name', ''),
            'damagePerHit': dmg_res['critHitDmg'],
            'hitsIn60s': hits_in_60s,
            'totalSkillDmg': total_skill_dmg
        })

    dps = math.floor(total_dmg_60s / 60)
    total_dmg_3m = total_dmg_60s * 3

    return {
        'dps': dps,
        'totalDmg60s': total_dmg_60s,
        'totalDmg3m': total_dmg_3m,
        'hitsBreakdown': hits_breakdown
    }


def generate_damage_waterfall_trace(damage_result: Dict[str, Any]) -> str:
    f = damage_result.get('factors') or {}
    return '\n'.join([
        f"[01] Base Skill ATK:       {f.get('baseMultiplier', 0):,} (P.ATK base)",
        f"[02] Net Effective PEN:     +{f.get('netPen', 0.0) * 100:.2f}% (Target DEF mitigated)",
        f"[03] Final P.DMG Bonus:     +{f.get('netFpdb', 0.0) * 100:.2f}% net",
        f"[04] Element Matrix:        x{f.get('elemFactor', 1.0):.3f} (Advantage + Enhance)",
        f"[05] Race & Attribute:      +{(f.get('raceBonus', 0.0) + f.get('attrBonus', 0.0)) * 100:.2f}%",
        f"[06] Size Scaling:          x{f.get('sizeFactor', 1.0):.2f} (Weapon size modifier)",
        f"[07] Final Bonus & Inc:     +{(f.get('netFinalDmgBonus', 0.0) + f.get('dmgIncrease', 0.0)) * 100:.2f}%",
        f"[08] 1-Hit Crit Damage:     {damage_result.get('critHitDmg', 0):,} (Spear Flash x{f.get('spearFlashMod', 1.0):.1f})"
    ])
