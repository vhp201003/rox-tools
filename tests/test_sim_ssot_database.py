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

