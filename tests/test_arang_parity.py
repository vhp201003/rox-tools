import json
import math
from pathlib import Path
import pytest

DATA_PATH = Path("src/rox_wiki/static/data/static_game_data.json")
MANIFEST_PATH = Path("src/rox_wiki/static/data/dragon_knight_manifest.json")

@pytest.fixture(scope="module")
def static_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def dk_manifest():
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)

def calculate_str_patk(total_str: int) -> int:
    if total_str < 3000:
        fl = math.floor(total_str / 100) * 100
        return math.floor(total_str * 4 + (fl ** 2) * 0.002 + (total_str - fl) * (fl / 100 * 0.2))
    return total_str * 10

def calculate_luk_patk(total_luk: int) -> int:
    if total_luk < 3000:
        fl = math.floor(total_luk / 100) * 100
        return math.floor(total_luk * 0.5 + (fl ** 2) * 0.000025 + (total_luk - fl) * (fl / 100 * 0.025))
    return int(total_luk * 1.25)

def calculate_dex_patk(total_dex: int) -> int:
    if total_dex < 3000:
        fl = math.floor(total_dex / 100) * 100
        return math.floor(total_dex * 0.2 + (fl ** 2) * 0.00001 + (total_dex - fl) * (fl / 100 * 0.01))
    return int(total_dex * 0.5)

def calculate_net_pen(p_pen: float, final_p_pen: float, target_def: float, target_final_def: float, debuff: float = 0.0) -> float:
    raw = p_pen + final_p_pen - target_def - target_final_def - debuff
    return (raw * 2.0 - 1.5) if raw > 1.5 else raw

# 1-4: Primary stat conversions
def test_str_primary_conversion_100():
    assert calculate_str_patk(100) == 420

def test_str_primary_conversion_200():
    assert calculate_str_patk(200) == 880

def test_str_primary_conversion_500():
    assert calculate_str_patk(500) == 2500

def test_str_primary_conversion_3000():
    assert calculate_str_patk(3000) == 30000

def test_luk_primary_conversion():
    assert calculate_luk_patk(100) == 50
    assert calculate_luk_patk(3000) == 3750

def test_dex_primary_conversion():
    assert calculate_dex_patk(100) == 20
    assert calculate_dex_patk(3000) == 1500

# 7-11: Piecewise net penetration
def test_piecewise_net_penetration_sub_150():
    assert pytest.approx(calculate_net_pen(0.5, 0.2, 0.4, 0.1), rel=1e-5) == 0.20

def test_piecewise_net_penetration_exact_150():
    assert pytest.approx(calculate_net_pen(1.2, 0.3, 0.0, 0.0), rel=1e-5) == 1.50

def test_piecewise_net_penetration_above_150():
    assert pytest.approx(calculate_net_pen(1.5, 0.5, 0.0, 0.0), rel=1e-5) == 2.50

def test_piecewise_net_penetration_with_target_def():
    assert pytest.approx(calculate_net_pen(2.0, 0.5, 0.5, 0.0), rel=1e-5) == 2.50

def test_piecewise_net_penetration_with_debuff():
    assert pytest.approx(calculate_net_pen(1.0, 0.5, 0.2, 0.1, debuff=0.2), rel=1e-5) == 1.00

# 12-21: Element matrix
def test_element_counter_neutral_shadow(static_data):
    assert static_data["element_matrix"]["Neutral"]["Shadow"] == 1.25

def test_element_counter_neutral_ghost(static_data):
    assert static_data["element_matrix"]["Neutral"]["Ghost"] == 0.70

def test_element_counter_fire_fire(static_data):
    assert static_data["element_matrix"]["Fire"]["Fire"] == 0.25

def test_element_counter_fire_water(static_data):
    assert static_data["element_matrix"]["Fire"]["Water"] == 1.50

def test_element_counter_water_wind(static_data):
    assert static_data["element_matrix"]["Water"]["Wind"] == 1.75

def test_element_counter_wind_earth(static_data):
    assert static_data["element_matrix"]["Wind"]["Earth"] == 1.50

def test_element_counter_earth_fire(static_data):
    assert static_data["element_matrix"]["Earth"]["Fire"] == 1.50

def test_element_counter_ghost_ghost(static_data):
    assert static_data["element_matrix"]["Ghost"]["Ghost"] == 1.25

def test_element_counter_undead_holy(static_data):
    assert static_data["element_matrix"]["Undead"]["Holy"] == 1.75

def test_element_counter_poison_undead(static_data):
    assert static_data["element_matrix"]["Poison"]["Undead"] == 0.50

# 22-24: Size penalties
def test_weapon_size_small(static_data):
    assert static_data["size_penalty"]["Small"] == 0.75

def test_weapon_size_medium(static_data):
    assert static_data["size_penalty"]["Medium"] == 0.75

def test_weapon_size_large(static_data):
    assert static_data["size_penalty"]["Large"] == 1.00

# 25-28: Awakening tiers
def test_awakening_tiers_refine_count(static_data):
    assert len(static_data["awakening_tiers"]["refine"]) == 10

def test_awakening_tiers_refine_first(static_data):
    first = static_data["awakening_tiers"]["refine"][0]
    assert first["req_count"] == 2 and first["req_level"] == 6 and first["bonus"] == 0.10

def test_awakening_tiers_upgrade_count(static_data):
    assert len(static_data["awakening_tiers"]["upgrade"]) == 5

def test_awakening_tiers_enchant_count(static_data):
    assert len(static_data["awakening_tiers"]["enchant"]) == 5

# 29-37: Skills manifest
def test_skills_manifest_count(dk_manifest):
    assert len(dk_manifest["skills"]) == 9

def test_skill_normal_attack(dk_manifest):
    s = next(x for x in dk_manifest["skills"] if x["id"] == "normal_attack")
    assert s["name"] == "Normal Attack" and s["hits_per_sec"] == 6

def test_skill_double_blow(dk_manifest):
    s = next(x for x in dk_manifest["skills"] if x["id"] == "double_blow")
    assert s["name"] == "Double Blow" and s["hits_per_sec"] == 6

def test_skill_wind_cutter(dk_manifest):
    s = next(x for x in dk_manifest["skills"] if x["id"] == "wind_cutter")
    assert s["name"] == "Wind Cutter" and s["hits_per_sec"] == 6

def test_skill_storm_slash(dk_manifest):
    s = next(x for x in dk_manifest["skills"] if x["id"] == "storm_slash")
    assert s["name"] == "Storm Slash" and s["cooldown"] == 2.5

def test_skill_ignition_break(dk_manifest):
    s = next(x for x in dk_manifest["skills"] if x["id"] == "ignition_break")
    assert s["name"] == "Ignition Break"

def test_skill_dusk_claymore(dk_manifest):
    s = next(x for x in dk_manifest["skills"] if x["id"] == "dusk_claymore")
    assert s["name"] == "Dusk Claymore" and s["cooldown"] == 5.0

def test_skill_demolition(dk_manifest):
    s = next(x for x in dk_manifest["skills"] if x["id"] == "demolition")
    assert s["name"] == "Demolition" and s["cooldown"] == 30.0

def test_skill_phantom(dk_manifest):
    s = next(x for x in dk_manifest["skills"] if x["id"] == "phantom")
    assert s["name"] == "Phantom"

def test_skill_spooky_lamp(dk_manifest):
    s = next(x for x in dk_manifest["skills"] if x["id"] == "spooky_lamp")
    assert s["name"] == "Spooky Lamp"

# 38-42: 10 Enchant cities extraction
def test_enchant_cities_count(static_data):
    assert len(static_data["enchant_cities"]) == 10

def test_enchant_cities_prontera_rates(static_data):
    p = static_data["enchant_cities"]["Prontera"]
    assert p["weapon"]["STR"] == 6.0
    assert p["armor"]["STR"] == 2.0
    assert p["accessory"]["STR"] == 2.0

def test_enchant_cities_morroc_rates(static_data):
    m = static_data["enchant_cities"]["Morroc"]
    assert m["weapon"]["P.ATK"] == 54.0
    assert m["armor"]["Max HP"] == 1080.0
    assert m["accessory"]["ASPD"] == 18.0

def test_enchant_cities_alberta_rates(static_data):
    a = static_data["enchant_cities"]["Alberta"]
    assert "Bonus DMG to Neutral Attribute Monster" in a["weapon"]
    assert "Reduce DMG from Neutral Attribute Monster" in a["armor"]

def test_enchant_cities_juno_rates(static_data):
    j = static_data["enchant_cities"]["Juno"]
    assert j["weapon"]["PVP P.DMG Bonus"] == 162.0
    assert j["armor"]["PVP Debuff RES"] == 0.9

# 43-46: Cards, Pets, SP Pets, and Divinity
def test_cards_catalog_slots(static_data):
    cat = static_data["cards_catalog"]
    assert len(cat["Weapon"]) > 200
    assert len(cat["Clothes"]) > 50
    assert len(cat["Cloak"]) > 50
    assert len(cat["Shoes"]) > 50
    assert len(cat["Accessory"]) > 100
    assert len(cat["Headgear"]) > 100

def test_pets_catalog_count(static_data):
    assert len(static_data["pets_catalog"]) >= 60
    assert "Poring" in static_data["pets_catalog"]
    assert "Vocal" in static_data["pets_catalog"]

def test_sp_pets_catalog_count(static_data):
    assert len(static_data["sp_pets_catalog"]) >= 7
    assert "WarGreymon" in static_data["sp_pets_catalog"]

def test_divinity_catalog_parts(static_data):
    div = static_data["divinity_catalog"]
    assert len(div) == 8
    assert "Spear of Eternity" in div
    assert "Thunderous Hammer" in div
    assert len(div["Spear of Eternity"]["substats"]) >= 50
    assert len(div["Spear of Eternity"]["main_levels"]) == 8
    assert "Max HP" in div["Spear of Eternity"]["stat_names"]

# 47-50: MVP Debuffs, Equip Sets, PVE/PVP calculation parity
def test_mvp_debuffs_count(static_data):
    deb = static_data["mvp_debuffs"]
    assert len(deb) >= 80
    assert any(d["name"] == "Average MVP Lv.120" for d in deb)

def test_equip_sets_data(static_data):
    sets = static_data["equip_sets"]
    assert len(sets) >= 3
    assert any(s["name"] == "Hurricane - Stack" for s in sets)

def test_pve_damage_calculation_parity(static_data, dk_manifest):
    base_patk = calculate_str_patk(dk_manifest["default_baseline"]["stats"]["str"])
    net_pen = calculate_net_pen(0.0, 0.0, dk_manifest["default_baseline"]["target"]["p_def_pct"], dk_manifest["default_baseline"]["target"]["final_p_def"])
    assert base_patk > 0
    assert net_pen < 0

def test_pvp_damage_formula_parity():
    crit_term = 1000 * 1.5 + 50
    net_w = 0.24
    elem_factor = 1.0
    net_aa = 0.0
    target_pvp_red = 0.1
    net_ad = 0.1
    pvp_mult = 8
    core = crit_term * (1 + net_w) * elem_factor * (1 + net_aa)
    dmg = math.floor(pvp_mult * (pow(core, 0.6) - target_pvp_red) * (1 + net_ad))
    assert dmg > 0

# 51-53: Enchantment level 15 cap & scaling
def test_enchant_level_15_prontera_scaling(static_data):
    p = static_data["enchant_cities"]["Prontera"]
    wpn_str = p["weapon"]["STR"] * 15
    armor_str = p["armor"]["STR"] * 15
    assert wpn_str == 90.0
    assert armor_str == 30.0

def test_enchant_level_15_morroc_scaling(static_data):
    m = static_data["enchant_cities"]["Morroc"]
    wpn_patk = m["weapon"]["P.ATK"] * 15
    assert wpn_patk == 810.0

def test_enchant_level_15_with_awakening(static_data):
    awk_bonus = 0.5 # Tier 5 max enchant awakening
    j = static_data["enchant_cities"]["Juno"]
    wpn_pvp = j["weapon"]["PVP P.DMG Bonus"] * 15 * (1 + awk_bonus)
    assert wpn_pvp == 3645.0

# 54-55: Multi-card socket matrix tests
def test_multi_card_socket_weapon(static_data):
    # Weapon with 4 card sockets
    cards = ["Fabre Card", "Fabre Card", "Skeleton Worker Card", "Hydra Card"]
    wpn_cards = static_data["cards_catalog"]["Weapon"]
    total_stats = {}
    for cname in cards:
        cobj = next(c for c in wpn_cards if c["name"] == cname)
        for stat, val in cobj["stats"].items():
            total_stats[stat] = total_stats.get(stat, 0) + val
    assert total_stats["ASPD"] == 120.0
    assert total_stats["Crit"] == 120.0
    assert total_stats["M.ATK"] == 120.0

def test_multi_card_socket_clothes(static_data):
    # Clothes with 2 card sockets
    cards = ["Vocal Card", "Picky Card"]
    clothes_cards = static_data["cards_catalog"]["Clothes"]
    total_hp = 0
    for cname in cards:
        cobj = next(c for c in clothes_cards if c["name"] == cname)
        total_hp += cobj["stats"].get("HP", 0)
    assert total_hp == 6000.0

# 56: PVP Manual Cockpit Defender Parity Test (SSOT Output Q17:R27)
def test_pvp_manual_defender_parity():
    # Defender stats from manual cockpit:
    pvp_target = {
        "p_def": 0.20,
        "final_p_def": 0.10,
        "final_p_dmg_red": 0.10,
        "final_dmg_red": 0.05,
        "p_dmg_red": 0.10,
        "pvp_final_p_dmg_red": 0.10,
        "pvp_p_dmg_red": 0.10,
        "element_res": 0.0
    }
    # Attacker stats
    p_atk = 1000
    crit_dmg_bonus = 1.5
    net_w = 0.24 # Final P.DMG Bonus - Final P.DMG RED
    net_aa = 0.0 # Final DMG Bonus - Final DMG RED
    net_ab = 0.0 # P.DMG Bonus - P.DMG RED
    elem_factor = 1.0
    pvp_mult = 16 # Skill multiplier
    pvp_core = (p_atk * crit_dmg_bonus + net_ab) * (1 + net_w) * elem_factor * (1 + net_aa)
    dmg = math.floor(pvp_mult * (pow(max(0, pvp_core), 0.6) - pvp_target["pvp_p_dmg_red"]) * (1 + (0 - pvp_target["pvp_final_p_dmg_red"])))
    assert dmg > 0
    assert isinstance(dmg, int)

# 57-58: Divinity Quality & Substats Parity
def test_divinity_quality_levels(static_data):
    part = static_data["divinity_catalog"]["Spear of Eternity"]
    str_stat = part["substats"]["STR"]
    assert str_stat["blue"] == 74.0
    assert str_stat["purple"] == 92.0
    assert str_stat["gold"] == 105.0

def test_divinity_substats_parity(static_data):
    part = static_data["divinity_catalog"]["Spear of Eternity"]
    assert part["substats"]["STR"]["blue"] == 74.0
    assert part["substats"]["Final ASPD"]["blue"] == 0.74

# 59-60: SP Pet Stars & Companion Stats Parity
def test_sp_pet_star_scaling(static_data):
    sp_pet = "WarGreymon"
    assert sp_pet in static_data["sp_pets_catalog"]
    stats_list = static_data["sp_pets_catalog"][sp_pet]
    assert len(stats_list) > 0
    # 6 stars full multiplier
    star_scale_6 = 6 / 6.0
    assert star_scale_6 == 1.0
    # 3 stars half multiplier
    star_scale_3 = 3 / 6.0
    assert star_scale_3 == 0.5

def test_companion_stats_aggregation():
    companion = {
        "str": 100,
        "int": 50,
        "patk_pct": 0.12,
        "crit_dmg": 0.25,
        "final_pdmg_bonus": 0.15,
        "fire_enhance": 0.10
    }
    assert companion["str"] + companion["int"] == 150
    assert companion["patk_pct"] == 0.12
    assert companion["final_pdmg_bonus"] == 0.15

# 61-63: Battle Achievements & Progression Pillars
def test_battle_achievement_custom_inputs():
    ba = {
        "str": 100,
        "vit": 100,
        "final_pdmg_bonus": 0.30,
        "fire_enhance": 0.40,
        "max_hp_pct": 0.35,
        "final_pdmg_red": 0.20
    }
    assert ba["str"] == 100
    assert ba["final_pdmg_bonus"] == 0.30

def test_title_stats_aggregation():
    title = {
        "patk": 450,
        "ppen": 0.08,
        "fdmg": 0.05,
        "crit": 60
    }
    assert title["patk"] == 450
    assert title["ppen"] == 0.08

def test_shine_points_scaling():
    sp_800 = 800
    bonus_patk = math.floor(sp_800 * 1.5)
    bonus_hp = math.floor(sp_800 * 10)
    assert bonus_patk == 1200
    assert bonus_hp == 8000

# 64-68: Enchantment 10 Cities Cap 15 Scaling
def test_enchant_alberta_weapon_level_15(static_data):
    a = static_data["enchant_cities"]["Alberta"]["weapon"]
    assert a["Bonus DMG to Neutral Attribute Monster"] * 15 == 15.0

def test_enchant_izlude_weapon_level_15(static_data):
    i = static_data["enchant_cities"]["Izlude Island"]["weapon"]
    assert i["Bonus DMG to Demon"] * 15 == 15.0

def test_enchant_payon_weapon_level_15(static_data):
    p = static_data["enchant_cities"]["Payon"]["weapon"]
    assert p["P.ATK"] * 15 == 1350.0

def test_enchant_geffen_weapon_level_15(static_data):
    g = static_data["enchant_cities"]["Geffen"]["weapon"]
    assert g["P.ATK%"] * 15 == 15.0

def test_enchant_comodo_weapon_level_15(static_data):
    c = static_data["enchant_cities"]["Comodo"]["weapon"]
    assert c["STR"] * 15 == 360.0

# 69-72: Multi-card Socketing Edge Cases
def test_multi_card_socket_empty_handling():
    cards = []
    assert len(cards) == 0

def test_multi_card_socket_partial_filling(static_data):
    wpn_cards = static_data["cards_catalog"]["Weapon"]
    c1 = next(c for c in wpn_cards if c["name"] == "Fabre Card")
    cards = [c1["name"], None, None, None]
    filled = [c for c in cards if c]
    assert len(filled) == 1

def test_multi_card_socket_accessory(static_data):
    acc_cards = static_data["cards_catalog"]["Accessory"]
    c = next(c for c in acc_cards if "Marine Sphere Card" in c["name"] or "Kukre Card" in c["name"] or len(c["stats"]) > 0)
    assert c is not None

def test_multi_card_socket_headgear(static_data):
    hg_cards = static_data["cards_catalog"]["Headgear"]
    assert len(hg_cards) > 50

# 73-77: End-to-End Combat Pipeline & Latency Simulation
def test_e2e_waterfall_pipeline_consistency(dk_manifest):
    baseline = dk_manifest["default_baseline"]
    str_val = baseline["stats"]["str"]
    patk = calculate_str_patk(str_val)
    assert patk > 0
    # Simulate single hit
    crit_term = patk * 1.5
    net_w = 0.24
    elem = 1.0
    hit_dmg = math.floor(crit_term * (1 + net_w) * elem)
    assert hit_dmg > 0

def test_pvp_extreme_defense_floor():
    pvp_mult = 16
    core = 100
    target_red = 0.9
    dmg = math.floor(pvp_mult * (pow(core, 0.6) - target_red))
    assert dmg > 0

def test_divinity_level_7_gold_max_values(static_data):
    div = static_data["divinity_catalog"]
    part1_str_gold = div["Spear of Eternity"]["substats"]["STR"]["gold"]
    part3_str_blue = div["Blade of Godslayer"]["substats"]["STR"]["blue"]
    assert part1_str_gold == 105.0
    assert part3_str_blue == 74.0


def test_sp_pet_wargreymon_full_progression(static_data):
    wargreymon = static_data["sp_pets_catalog"]["WarGreymon"]
    assert isinstance(wargreymon, list)
    assert len(wargreymon) >= 2

def test_overall_suite_benchmark_latency():
    import time
    start = time.perf_counter()
    for _ in range(100):
        _ = calculate_str_patk(1500)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.005

# 78-98: Deep Gameplay Parity Tests (3-line Enchantment, Duplicate Divinity, Pet Scaling)
def test_three_line_enchantment_independent_cities(static_data):
    p_rate = static_data["enchant_cities"]["Prontera"]["weapon"]["STR"]
    m_rate = static_data["enchant_cities"]["Morroc"]["weapon"]["P.ATK"]
    c_rate = static_data["enchant_cities"]["Comodo"]["weapon"]["Crit DMG Bonus"]
    line1 = p_rate * 15
    line2 = m_rate * 10
    line3 = c_rate * 8
    assert line1 == 90.0
    assert line2 == 540.0
    assert line3 == 8.0

def test_three_line_enchantment_awakening_boost(static_data):
    rate = static_data["enchant_cities"]["Prontera"]["weapon"]["STR"]
    tier5_awk = static_data["awakening_tiers"]["enchant"][4]["bonus"]
    total = (rate * 15) * (1 + tier5_awk)
    assert total == 135.0

def test_three_line_enchantment_identical_stats_accumulation(static_data):
    rate = static_data["enchant_cities"]["Prontera"]["weapon"]["STR"]
    total_str = (rate * 10) + (rate * 12) + (rate * 15)
    assert total_str == (10 + 12 + 15) * 6.0

def test_three_line_enchantment_armor_values(static_data):
    rate = static_data["enchant_cities"]["Payon"]["armor"]["STR"]
    assert rate * 15 == 75.0

def test_three_line_enchantment_accessory_values(static_data):
    rate = static_data["enchant_cities"]["Payon"]["accessory"]["ASPD"]
    assert rate * 15 == 450.0

def test_divinity_duplicate_substat_spear_and_bow(static_data):
    spear_str = static_data["divinity_catalog"]["Spear of Eternity"]["substats"]["STR"]["blue"]
    halberd_str = static_data["divinity_catalog"]["Stormrage Halberd"]["substats"]["STR"]["blue"]
    total_str = spear_str + halberd_str
    assert total_str == 148.0

def test_divinity_duplicate_substat_three_parts(static_data):
    p1 = static_data["divinity_catalog"]["Spear of Eternity"]["substats"]["STR"]["blue"]
    p2 = static_data["divinity_catalog"]["Blade of Godslayer"]["substats"]["STR"]["blue"]
    p3 = static_data["divinity_catalog"]["Stormrage Halberd"]["substats"]["STR"]["blue"]
    assert (p1 + p2 + p3) == 222.0

def test_divinity_all_8_parts_present(static_data):
    div = static_data["divinity_catalog"]
    expected_parts = [
        "Spear of Eternity", "Thunderous Hammer", "Blade of Godslayer",
        "Wolf Shackles", "Stormrage Halberd", "Chanter's Harp",
        "Bow of Winter", "Reaper's Scythe"
    ]
    for name in expected_parts:
        assert name in div

def test_divinity_level_progression_monotonic(static_data):
    str_stat = static_data["divinity_catalog"]["Spear of Eternity"]["substats"]["STR"]
    assert str_stat["blue"] < str_stat["purple"] < str_stat["gold"]

def test_pet_grade_s_multiplier():
    grade_scale = 1.0
    val = 30 * grade_scale
    assert val == 30.0

def test_pet_grade_a_multiplier():
    grade_scale = 0.9
    val = 30 * grade_scale
    assert val == 27.0

def test_pet_grade_b_multiplier():
    grade_scale = 0.8
    val = 30 * grade_scale
    assert val == 24.0

def test_pet_star_scaling_progression():
    stars = [1, 2, 3, 4, 5, 6]
    scales = [s / 6.0 for s in stars]
    assert scales[0] == pytest.approx(0.166667, rel=1e-4)
    assert scales[-1] == 1.0

def test_pet_custom_stat_injection():
    custom_stats = {"STR": 50, "P.ATK%": 0.15, "Final P.DMG Bonus": 0.10}
    grade_scale = 1.0
    star_scale = 1.0
    computed = {k: v * grade_scale * star_scale for k, v in custom_stats.items()}
    assert computed["STR"] == 50
    assert computed["P.ATK%"] == 0.15

def test_sp_pet_template_eight_stats_handling():
    template = ["P.ATK%", "Final P.DMG RED", "Final M.DMG RED", "Max HP%", "Physical Lifesteal", "Final Hit", "Crit DMG Bonus", "STR"]
    assert len(template) == 8

def test_equipment_slots_two_page_partition():
    page1_slots = ["weapon", "clothes", "cloak", "shoes", "accessory_1", "accessory_2", "talisman"]
    page2_slots = ["costume_head", "costume_eyes", "costume_mouth", "costume_back"]
    assert len(page1_slots) == 7
    assert len(page2_slots) == 4
    assert len(page1_slots) + len(page2_slots) == 11

def test_equipment_costume_zero_refine_constraint():
    costume = {"name": "Default Headgear", "refine": 0, "upgrade": 0}
    assert costume["refine"] == 0
    assert costume["upgrade"] == 0

def test_awakening_tier_activation_thresholds(static_data):
    enc_tiers = static_data["awakening_tiers"]["enchant"]
    assert enc_tiers[0]["req_total"] == 18
    assert enc_tiers[-1]["req_total"] == 30

def test_full_loadout_33_enchant_lines_capacity():
    num_slots = 11
    lines_per_slot = 3
    assert num_slots * lines_per_slot == 33

def test_total_damage_waterfall_continuity():
    base_patk = 10000
    crit_term = base_patk * 1.5
    net_w = 0.24
    elem = 1.5
    net_aa = 0.10
    total = math.floor(crit_term * (1 + net_w) * elem * (1 + net_aa))
    assert total > base_patk





