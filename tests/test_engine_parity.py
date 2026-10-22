import json
import pytest
from pathlib import Path
from rox_wiki.engine import (
    calculate_primary_conversions,
    calculate_awakening_bonuses,
    tally_player_stats,
    calculate_net_pen,
    calculate_skill_damage,
    simulate_combat_timeline
)
from rox_wiki.class_adapters import get_adapter, RangerAdapter

STATIC_DATA_PATH = Path("src/rox_wiki/static/data/static_game_data.json")
DK_MANIFEST_PATH = Path("src/rox_wiki/static/data/dragon_knight_manifest.json")
GOLDEN_PATH = Path("tests/golden_builds.json")

@pytest.fixture(scope="module")
def static_data():
    with open(STATIC_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def manifests():
    with open(DK_MANIFEST_PATH, encoding="utf-8") as f:
        dk = json.load(f)
    return {"dragon_knight": dk}

@pytest.fixture(scope="module")
def golden_builds():
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        return json.load(f)["builds"]


def test_golden_builds_count(golden_builds):
    assert len(golden_builds) >= 10


def test_engine_parity_across_all_golden_builds(golden_builds, static_data, manifests):
    for b in golden_builds:
        name = b["name"]
        class_id = b["class_id"]
        is_pvp = b.get("is_pvp", False)
        inp = b["input"]
        exp = b["expected"]

        adapter = get_adapter(class_id, manifests)
        tally = tally_player_stats(inp, static_data, adapter.get_primary_conversion_fn())

        for stat_name, exp_val in exp["stats"].items():
            act_val = tally["stats"].get(stat_name, 0.0)
            assert act_val == pytest.approx(exp_val, abs=1e-5), f"[{name}] Stat mismatch for {stat_name}: expected {exp_val}, got {act_val}"

        target = inp.get("target") or {}
        buffs = inp.get("buffs") or {}
        debuffs = inp.get("debuffs") or {}
        skills = adapter.get_skills()

        sim = simulate_combat_timeline(
            skills,
            tally["stats"],
            target,
            buffs,
            static_data,
            debuffs,
            is_pvp
        )

        assert sim["dps"] == exp["dps"], f"[{name}] DPS mismatch: expected {exp['dps']}, got {sim['dps']}"
        assert sim["totalDmg60s"] == exp["totalDmg60s"], f"[{name}] totalDmg60s mismatch: expected {exp['totalDmg60s']}, got {sim['totalDmg60s']}"

        for i, sk_exp in enumerate(exp["skills"]):
            sk_act = sim["hitsBreakdown"][i]
            assert sk_act["skillId"] == sk_exp["skillId"]
            assert sk_act["damagePerHit"] == sk_exp["damagePerHit"], f"[{name}] Skill {sk_act['skillId']} damagePerHit mismatch: expected {sk_exp['damagePerHit']}, got {sk_act['damagePerHit']}"
            assert sk_act["hitsIn60s"] == sk_exp["hitsIn60s"]
            assert sk_act["totalSkillDmg"] == sk_exp["totalSkillDmg"]


def test_ranger_dex_primary_conversion():
    adapter = RangerAdapter()
    conv_fn = adapter.get_primary_conversion_fn()
    res = conv_fn({"dex": 100, "str": 50, "luk": 50}, {"dex": 20})
    assert res["totalStats"]["dex"] == 120
    assert res["totalStats"]["str"] == 50
    assert res["convertedPatk"] == 504


def test_build_payload_parity_fields_validation():
    from rox_wiki.schemas import BuildPayload
    payload = BuildPayload(
        inscriptions={"Strength I": 10.0, "Physical Attack I": 10.0},
        card_awakening={"STR": 50.0, "P.ATK": 100.0},
        guild_blessing={"P.ATK": 200.0, "Max HP": 1000.0},
        active_equip_sets=["Hurricane - Stack", "Fierce Gail - Stack"],
        skip_class_passives=True
    )
    d = payload.model_dump()
    assert d["inscriptions"]["Strength I"] == 10.0
    assert d["card_awakening"]["STR"] == 50.0
    assert d["guild_blessing"]["P.ATK"] == 200.0
    assert "Hurricane - Stack" in d["active_equip_sets"]
    assert d["skip_class_passives"] is True


def test_stream_1_title_card_awakening_guild_blessing_wardrobe(static_data):
    build = {
        "progression": {
            "title": {
                "STR": 10,
                "AGI": 10,
                "VIT": 10,
                "INT": 10,
                "DEX": 10,
                "LUK": 10,
                "P.ATK": 50,
                "M.ATK": 50,
                "P.PEN": 30,
                "M.PEN": 30,
                "ASPD": 40,
                "Haste": 40,
                "Hit": 20,
                "Crit": 20,
                "P.DEF": 25,
                "M.DEF": 25,
                "Flee": 15,
                "Anti-Crit": 15,
                "Max HP": 500,
                "Max SP": 100,
                "HP Regen": 5,
                "SP Regen": 5,
                "Bonus DMG to Plant": 0.05,
                "Bonus DMG to Brute": 0.05,
                "Bonus DMG to Demi-Human": 0.05,
                "Final DMG Bonus": 0.08,
            },
            "shine_points": 200
        },
        "card_awakening": {
            "STR": 20.0,
            "P.ATK": 150.0
        },
        "guild_blessing": {
            "P.ATK": 100.0,
            "Max HP": 2000.0
        }
    }
    tally = tally_player_stats(build, static_data)
    bd = tally["breakdown"]

    # 26 Title stats
    assert bd["STR"]["title"] == 10.0
    assert bd["P.ATK"]["title"] == 50.0
    assert bd["P.PEN"]["title"] == 30.0
    assert bd["Final DMG Bonus"]["title"] == 0.08
    assert bd["Bonus DMG to Plant"]["title"] == 0.05
    assert bd["Bonus DMG to Demi-Human"]["title"] == 0.05

    # Card Awakening & Guild Blessing
    assert bd["STR"]["card_awakening"] == 20.0
    assert bd["P.ATK"]["card_awakening"] == 150.0
    assert bd["P.ATK"]["guild_blessing"] == 100.0
    assert bd["Max HP"]["guild_blessing"] == 2000.0

    # Wardrobe milestones table lookup at 200 points
    assert bd["P.DEF"]["wardrobe_milestone"] == 60.0
    assert bd["M.DEF"]["wardrobe_milestone"] == 60.0
    assert bd["Max HP"]["wardrobe_milestone"] == 3000.0
    assert bd["Max SP"]["wardrobe_milestone"] == 600.0
    assert bd["P.ATK"]["wardrobe_milestone"] == 60.0
    assert bd["M.ATK"]["wardrobe_milestone"] == 60.0
    assert bd["Hit"]["wardrobe_milestone"] == 60.0
    assert bd["Flee"]["wardrobe_milestone"] == 60.0
    assert bd["Crit"]["wardrobe_milestone"] == 60.0
    assert bd["Anti-Crit"]["wardrobe_milestone"] == 60.0


def test_stream_7_shadow_hotfix_and_inscriptions(static_data):
    from rox_wiki.engine import calculate_inscription_stat

    # Inscription bracket calculation helper
    assert calculate_inscription_stat(0, 1.0) == 0.0
    assert calculate_inscription_stat(5, 1.0) == 5.0
    assert calculate_inscription_stat(10, 1.0) == 10.0
    assert calculate_inscription_stat(10, 12.0) == 120.0

    # Build with shadow level and 2H Sword inscriptions
    build_2h = {
        "progression": {"shadow_level": 10},
        "loadout": {
            "weapon": {"name": "Teeth Bone Broadsword", "type": "2H Sword"}
        },
        "inscriptions": {
            "Strength I": 10,
            "Luck I": 10,
            "Crit I": 10,
            "Physical Damage Reduction IV": 10,
            "Water/Wind Resist": 10
        }
    }
    tally = tally_player_stats(build_2h, static_data)
    bd = tally["breakdown"]

    # Shadow hotfix: level 10 -> 120 P.DMG Bonus
    assert bd["P.DMG Bonus"]["shadow_hotfix"] == 120.0

    # Inscriptions: 2H sword selects Luck I and Crit I
    assert bd["STR"]["inscriptions"] == 10.0
    assert bd["LUK"]["inscriptions"] == 10.0
    assert bd["Crit"]["inscriptions"] == 120.0
    assert bd["PVP Final P.DMG RED"]["inscriptions"] == pytest.approx(0.05)
    assert bd["Water Attribute RES"]["inscriptions"] == pytest.approx(0.20)
    assert bd["Wind Attribute RES"]["inscriptions"] == pytest.approx(0.20)

    # Build with 1H Sword selects Dexterity I and Physical Penetration I
    build_1h = {
        "loadout": {
            "weapon": {"name": "Knight Sword", "type": "1H Sword"}
        },
        "inscriptions": {
            1: 10,
            2: 10,
        }
    }
    tally_1h = tally_player_stats(build_1h, static_data)
    bd_1h = tally_1h["breakdown"]
    assert bd_1h["DEX"]["inscriptions"] == 10.0
    assert bd_1h["P.PEN"]["inscriptions"] == 120.0


def test_stream_8_dragon_knight_passives_and_normalized_buffs(static_data):
    # Test individual passives
    build_str = {
        "class_id": "dragon_knight",
        "stats": {"str": 100, "vit": 100}
    }
    tally = tally_player_stats(build_str, static_data)
    bd = tally["breakdown"]

    # Sword Mastery: 80.0 + (tot_str / 2.0) = 80 + 50 = 130
    assert bd["P.ATK"]["skill_sword_mastery"] == 130.0
    # Cavalry Mastery: 80.0 + (0.50 * tot_str) = 80 + 50 = 130
    assert bd["P.ATK"]["skill_cavalry_mastery"] == 130.0
    # Call of Justice: 2.0 * tot_vit = 2 * 100 = 200
    assert bd["P.ATK"]["skill_call_of_justice"] == 200.0
    # Lord's Aura: 0.10 P.ATK%
    assert bd["P.ATK%"]["skill_lords_aura"] == 0.10
    # Head Crush: 0.20 P.ATK%, 0.50 Crit DMG Bonus
    assert bd["P.ATK%"]["skill_head_crush"] == 0.20
    assert bd["Crit DMG Bonus"]["skill_head_crush"] == 0.50
    # Aura Blade: 0.20 + (100 / 50) / 100 = 0.22 Crit DMG Bonus, 0.20 Final Crit
    assert bd["Crit DMG Bonus"]["skill_aura_blade"] == pytest.approx(0.22)
    assert bd["Final Crit"]["skill_aura_blade"] == 0.20

    # Normalized buffs: Concentration and Spooky Lamp produce Damage Increase
    build_buffs = {
        "buffs": {
            "concentration": True,
            "spooky_lamp": True,
            "spear_flash": True
        }
    }
    tally_buffs = tally_player_stats(build_buffs, static_data)
    bd_buffs = tally_buffs["breakdown"]
    assert bd_buffs["Damage Increase"]["buff_concentration"] == 0.20
    assert bd_buffs["Damage Increase"]["buff_spooky_lamp"] == 0.24
    assert bd_buffs["Final P.DMG Bonus"]["buff_spear_flash"] == 0.20

    # Test skip_class_passives gating
    build_skip = {
        "class_id": "dragon_knight",
        "stats": {"str": 100},
        "skip_class_passives": True
    }
    tally_skip = tally_player_stats(build_skip, static_data)
    assert "skill_sword_mastery" not in tally_skip["breakdown"].get("P.ATK", {})


def test_stream_13_equip_sets_and_card_sets(static_data):
    # Equip set via active_equip_sets list
    build_eq = {
        "active_equip_sets": ["Hurricane - Stack"]
    }
    tally_eq = tally_player_stats(build_eq, static_data)
    assert tally_eq["breakdown"]["PVP Final P.DMG Bonus"]["equip_set"] == 0.025
    assert tally_eq["breakdown"]["PVP Final M.DMG Bonus"]["equip_set"] == 0.025

    # Card combos via slotted cards: Drake Card gives Bonus DMG to Small and Large
    build_card = {
        "loadout": {
            "weapon": {
                "name": "Teeth Bone Broadsword",
                "type": "2H Sword",
                "cards": ["Drake Card [Day]"]
            }
        }
    }
    tally_card = tally_player_stats(build_card, static_data)
    assert tally_card["breakdown"]["Bonus DMG to Small"]["card_set"] == 0.25
    assert tally_card["breakdown"]["Bonus DMG to Large"]["card_set"] == 0.25
