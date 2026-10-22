import pytest
from rox_wiki import database as db


def test_ssot_class_registry():
    dk = db.get_sim_class_registry("dragon_knight")
    assert dk is not None
    assert dk["primary_stat"] == "STR"
    assert dk["hp_per_vit"] == 320.0


def test_ssot_enchant_rules_independent_lines():
    # User can fetch all rules for a city and slot category
    payon_weapon_rules = db.get_sim_enchant_rules(city_name="Payon", slot_category="weapon")
    assert len(payon_weapon_rules) > 0
    stat_names = [r["stat_name"] for r in payon_weapon_rules]
    assert "P.ATK" in stat_names
    assert "STR" in stat_names

    # Finding specific rate
    patk_rule = next(r for r in payon_weapon_rules if r["stat_name"] == "P.ATK")
    assert patk_rule["rate_per_level"] == 90.0


def test_ssot_equipment_catalog_and_scales():
    # Test getting equipment
    item = db.get_sim_equipment_item("Teeth Bone Broadsword")
    assert item is not None
    assert item["slot_type"] == "Weapon"
    assert item["up_id"] is not None
    assert item["ref_id"] is not None

    # Test scaling
    up_scale = db.get_sim_equipment_scale("upgrade", item["up_id"], 10)
    assert up_scale is not None
    assert "P.ATK" in up_scale

    ref_scale = db.get_sim_equipment_scale("refine", item["ref_id"], 5)
    assert ref_scale is not None


def test_ssot_combat_rules_element_matrix():
    rules = db.get_sim_combat_rules("element_matrix")
    assert len(rules) >= 50
    fire_vs_earth = next((r for r in rules if r["key_1"] == "Fire" and r["key_2"] == "Earth"), None)
    assert fire_vs_earth is not None
    assert fire_vs_earth["value"] == 0.9

    fire_vs_water = next((r for r in rules if r["key_1"] == "Fire" and r["key_2"] == "Water"), None)
    assert fire_vs_water is not None
    assert fire_vs_water["value"] == 1.5


def test_ssot_inscriptions():
    all_inc = db.get_sim_inscriptions()
    assert len(all_inc) == 34

    inscriptions = db.get_sim_inscriptions("Inscription")
    assert len(inscriptions) == 17
    assert any(i["name"] == "Strength I" for i in inscriptions)

    pioneers = db.get_sim_inscriptions("Pioneer")
    assert len(pioneers) == 17
    assert any(p["name"] == "Physical Attack I" for p in pioneers)

    first = inscriptions[0]
    assert "stats_per_level" in first
    assert "stat1" in first["stats_per_level"]


def test_ssot_passive_milestones_and_wardrobe():
    guild_blessings = db.get_sim_passive_milestones("guild_blessing")
    assert len(guild_blessings) == 16
    assert any(gb["identifier"] == "P.ATK" for gb in guild_blessings)

    card_awakenings = db.get_sim_passive_milestones("card_awakening")
    assert len(card_awakenings) == 22
    assert any(ca["identifier"] == "STR" for ca in card_awakenings)

    all_wardrobe = db.get_sim_wardrobe_milestones()
    assert len(all_wardrobe) == 25

    wardrobe_100 = db.get_sim_wardrobe_milestones(max_points=100)
    assert len(wardrobe_100) == 5
    assert [m["level_or_point"] for m in wardrobe_100] == [20, 40, 60, 80, 100]


def test_ssot_equip_sets_and_card_sets():
    equip_sets = db.get_sim_equip_sets()
    assert len(equip_sets) >= 37
    assert any(es["key_1"] == "Hurricane - Stack" for es in equip_sets)
    assert any("Ferocity" in es["key_1"] for es in equip_sets)

    first_set = next(es for es in equip_sets if es["key_1"] == "Hurricane - Stack")
    assert "extra" in first_set
    assert first_set["extra"]["stat"] == "PVP Final P.DMG Bonus"

    card_sets = db.get_sim_card_sets()
    assert len(card_sets) == 4
    card_set_names = [cs["key_1"] for cs in card_sets]
    assert any("Drake" in n for n in card_set_names)
    assert any("Arc Angeling" in n for n in card_set_names)
    assert any("Thanatos" in n for n in card_set_names)
    assert any("Skeggiold" in n for n in card_set_names)

