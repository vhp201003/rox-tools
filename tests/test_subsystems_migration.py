import json
import uuid
import pytest
from pathlib import Path
from pydantic import ValidationError

from rox_wiki import database as db
from rox_wiki.engine import tally_player_stats, simulate_combat_timeline
from rox_wiki.class_adapters import get_adapter
from rox_wiki.schemas import (
    EquipSlotPayload,
    CompanionLinePayload,
    CompanionSlotPayload,
    DivinityPartPayload,
    BuildPayload,
)

STATIC_DATA_PATH = Path("src/rox_wiki/static/data/static_game_data.json")
DK_MANIFEST_PATH = Path("src/rox_wiki/static/data/dragon_knight_manifest.json")


@pytest.fixture(scope="module")
def static_data():
    with open(STATIC_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def dk_manifest():
    with open(DK_MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_2h_weapon_five_cards_and_shield_disabled(static_data, dk_manifest):
    build = {
        "class_id": "dragon_knight",
        "stats": {"str": 100},
        "loadout": {
            "weapon": {
                "name": "Teeth Bone Broadsword",
                "type": "2H Sword",
                "cards": [
                    "Fabre Card",
                    "Fabre Card",
                    "Fabre Card",
                    "Fabre Card",
                    "Fabre Card"
                ]
            },
            "shield": {
                "name": "Vesper's Shield",
                "type": "Shield",
                "refine": 10,
                "upgrade": 50,
                "cards": ["Fabre Card", "Fabre Card"],
                "is_disabled": False
            }
        }
    }

    adapter = get_adapter("dragon_knight", {"dragon_knight": dk_manifest})
    tally = tally_player_stats(build, static_data, adapter.get_primary_conversion_fn())

    assert build["loadout"]["shield"]["is_disabled"] is True
    # Fabre Card gives 60 ASPD each. 5 on weapon = 300 ASPD. Shield cards must not add ASPD.
    assert tally["stats"].get("ASPD") == 300.0
    assert "card_shield" not in tally["breakdown"].get("ASPD", {})
    assert "equip_refine_shield" not in tally["breakdown"].get("P.DEF", {})


def test_1h_weapon_with_active_shield(static_data, dk_manifest):
    build = {
        "class_id": "dragon_knight",
        "stats": {"str": 100},
        "loadout": {
            "weapon": {
                "name": "Knight Sword",
                "type": "1H Sword",
                "cards": [
                    "Fabre Card",
                    "Fabre Card",
                    "Fabre Card"
                ]
            },
            "shield": {
                "name": "Knight Shield",
                "type": "Shield",
                "cards": [
                    "Fabre Card",
                    "Fabre Card"
                ],
                "is_disabled": False
            }
        }
    }

    adapter = get_adapter("dragon_knight", {"dragon_knight": dk_manifest})
    tally = tally_player_stats(build, static_data, adapter.get_primary_conversion_fn())

    assert build["loadout"]["shield"]["is_disabled"] is False
    # 3 weapon cards + 2 shield cards = 5 Fabre Cards = 300 ASPD
    assert tally["stats"].get("ASPD") == 300.0
    assert tally["breakdown"]["ASPD"]["card_weapon"] == 180.0
    assert tally["breakdown"]["ASPD"]["card_shield"] == 120.0


def test_slot_card_limits_pydantic_validation():
    # 2H weapon allows up to 5 cards
    slot_2h = EquipSlotPayload(
        type="2H Sword",
        cards=["C1", "C2", "C3", "C4", "C5"]
    )
    assert len(slot_2h.cards) == 5

    # 2H weapon rejects 6 cards
    with pytest.raises(ValidationError):
        EquipSlotPayload(
            type="2H Sword",
            cards=["C1", "C2", "C3", "C4", "C5", "C6"]
        )

    # 1H weapon allows up to 3 cards
    slot_1h = EquipSlotPayload(
        type="1H Sword",
        cards=["C1", "C2", "C3"]
    )
    assert len(slot_1h.cards) == 3

    # 1H weapon rejects 4 cards
    with pytest.raises(ValidationError):
        EquipSlotPayload(
            type="1H Sword",
            cards=["C1", "C2", "C3", "C4"]
        )

    # Shield allows up to 2 cards, rejects 3
    with pytest.raises(ValidationError):
        EquipSlotPayload(
            type="Shield",
            cards=["C1", "C2", "C3"]
        )

    # Costume allows up to 2 cards, rejects 3
    with pytest.raises(ValidationError):
        EquipSlotPayload(
            type="CostumeHead",
            tab_type="costume",
            cards=["C1", "C2", "C3"]
        )


def test_costume_slots_only_contribute_cards(static_data, dk_manifest):
    build = {
        "class_id": "dragon_knight",
        "stats": {"str": 100},
        "loadout": {
            "costume_head": {
                "name": "Angel Wing",
                "type": "CostumeHead",
                "tab_type": "costume",
                "upgrade": 50,
                "refine": 10,
                "enchant_city": "Prontera",
                "enchant_lv": 5,
                "cards": ["Fabre Card", "Fabre Card"]
            },
            "costume_back": {
                "name": "Fallen Angel Wing",
                "type": "CostumeBack",
                "tab_type": "costume",
                "cards": ["Fabre Card"]
            }
        }
    }

    adapter = get_adapter("dragon_knight", {"dragon_knight": dk_manifest})
    tally = tally_player_stats(build, static_data, adapter.get_primary_conversion_fn())

    # 2 Fabre Cards on head + 1 on back = 3 * 60 = 180 ASPD
    assert tally["stats"].get("ASPD") == 180.0
    # No upgrade or refine stats allowed from costumes
    assert "equip_upgrade_costume_head" not in tally["breakdown"].get("P.DEF", {})
    assert "equip_refine_costume_head" not in tally["breakdown"].get("P.DEF", {})
    assert "enchant_costume_head" not in tally["breakdown"].get("P.ATK", {})


def test_four_companions_24_lines_aggregation_without_is_pct(static_data, dk_manifest):
    build = {
        "class_id": "dragon_knight",
        "stats": {"str": 100},
        "companion": [
            {
                "slot_index": 1,
                "name": "Spark",
                "offensive": [
                    {"stat_name": "P.ATK", "value": 150.0},
                    {"stat_name": "Final P.PEN", "value": 0.05},
                    {"stat_name": "Final Crit", "value": 0.04}
                ],
                "defensive": [
                    {"stat_name": "Max HP", "value": 1200.0},
                    {"stat_name": "Final P.DEF", "value": 0.06},
                    {"stat_name": "Final P.DMG RED", "value": 0.05}
                ]
            },
            {
                "slot_index": 2,
                "name": "Wraith",
                "offensive": [
                    {"stat_name": "P.ATK", "value": 200.0},
                    {"stat_name": "Final P.PEN", "value": 0.05},
                    {"stat_name": "Final Crit", "value": 0.03}
                ],
                "defensive": [
                    {"stat_name": "Max HP", "value": 800.0},
                    {"stat_name": "Final P.DEF", "value": 0.04},
                    {"stat_name": "Final P.DMG RED", "value": 0.05}
                ]
            },
            {
                "slot_index": 3,
                "name": "Cloudsong",
                "offensive": [
                    {"stat_name": "P.ATK", "value": 100.0},
                    {"stat_name": "P.ATK%", "value": 0.05},
                    {"stat_name": "Crit DMG Bonus", "value": 0.10}
                ],
                "defensive": [
                    {"stat_name": "Final Anti-Crit", "value": 0.05},
                    {"stat_name": "Crit DMG RED", "value": 0.10},
                    {"stat_name": "Final Flee", "value": 0.04}
                ]
            },
            {
                "slot_index": 4,
                "name": "Bubbles",
                "offensive": [
                    {"stat_name": "Final P.DMG Bonus", "value": 0.08},
                    {"stat_name": "Final ASPD", "value": 0.15},
                    {"stat_name": "Final Haste", "value": 0.05}
                ],
                "defensive": [
                    {"stat_name": "Max HP%", "value": 0.08},
                    {"stat_name": "Final M.DEF", "value": 0.06},
                    {"stat_name": "Final M.DMG RED", "value": 0.05}
                ]
            }
        ]
    }

    adapter = get_adapter("dragon_knight", {"dragon_knight": dk_manifest})
    tally = tally_player_stats(build, static_data, adapter.get_primary_conversion_fn())

    # Raw P.ATK: 150 + 200 + 100 = 450 from companion
    # Plus base STR 100 converted = 400. Total base = 850.
    # Plus P.ATK% 0.05 = floor(850 * 1.05) = 892
    assert tally["stats"]["Final P.PEN"] == pytest.approx(0.10)
    assert tally["stats"]["Final Crit"] == pytest.approx(0.07)
    assert tally["stats"]["Final P.DMG Bonus"] == pytest.approx(0.08)
    assert tally["stats"]["Final P.DMG RED"] == pytest.approx(0.10)


def test_divinity_gold_lv7_flash_sustained_dps_increase_mvp_mini(static_data, dk_manifest):
    mvp_target = {
        "name": "Lord of the Dead Lv.150",
        "race": "Undead",
        "size": "Large",
        "element": "Shadow",
        "is_mvp": True,
        "dummy_type": "mvp"
    }

    base_build = {
        "class_id": "dragon_knight",
        "stats": {"str": 1000},
        "target": mvp_target,
        "divinity": [
            {
                "part_index": 1,
                "name": "Spear of Eternity",
                "rarity": "gold",
                "level": 7,
                "has_flash": False
            }
        ]
    }

    flash_build = {
        "class_id": "dragon_knight",
        "stats": {"str": 1000},
        "target": mvp_target,
        "divinity": [
            {
                "part_index": 1,
                "name": "Spear of Eternity",
                "rarity": "gold",
                "level": 7,
                "has_flash": True
            }
        ]
    }

    adapter = get_adapter("dragon_knight", {"dragon_knight": dk_manifest})
    skills = adapter.get_skills()

    tally_base = tally_player_stats(base_build, static_data, adapter.get_primary_conversion_fn())
    sim_base = simulate_combat_timeline(skills, tally_base["stats"], mvp_target, {}, static_data)

    tally_flash = tally_player_stats(flash_build, static_data, adapter.get_primary_conversion_fn())
    sim_flash = simulate_combat_timeline(skills, tally_flash["stats"], mvp_target, {}, static_data)

    # Flash adds 0.42 to final_dmg_bonus_mvp_mini, increasing sustained damage by exactly ~42%
    ratio = sim_flash["dps"] / sim_base["dps"]
    assert ratio == pytest.approx(1.42, rel=0.01)


def test_database_profile_storage_14_slots_4_companions_8_divinity():
    profile_id = str(uuid.uuid4())
    class_id = "dragon_knight"
    build_data = {
        "class_id": class_id,
        "loadout": {
            f"slot_{i}": {"name": f"Item {i}", "cards": ["Card A"]}
            for i in range(14)
        },
        "companion": [
            {
                "slot_index": i,
                "name": f"Companion {i}",
                "offensive": [{"stat_name": "P.ATK", "value": 100.0}],
                "defensive": [{"stat_name": "Max HP", "value": 500.0}]
            }
            for i in range(1, 5)
        ],
        "divinity": [
            {
                "part_index": i,
                "name": f"Part {i}",
                "level": 7,
                "rarity": "gold",
                "has_flash": (i == 1)
            }
            for i in range(1, 9)
        ]
    }

    saved = db.upsert_profile(profile_id, class_id, build_data, computed_dps=1234567)
    assert saved["id"] == profile_id
    assert saved["computed_dps"] == 1234567

    loaded = db.get_profile(profile_id)
    assert loaded is not None
    assert len(loaded["build_data"]["loadout"]) == 14
    assert len(loaded["build_data"]["companion"]) == 4
    assert len(loaded["build_data"]["divinity"]) == 8
    assert loaded["build_data"]["divinity"][0]["has_flash"] is True


def test_dict_format_companion_and_divinity_with_flash(static_data, dk_manifest):
    mvp_target = {
        "name": "Lord of the Dead Lv.150",
        "race": "Undead",
        "size": "Large",
        "element": "Shadow",
        "is_mvp": True,
        "dummy_type": "mvp"
    }
    build = {
        "class_id": "dragon_knight",
        "stats": {"str": 100},
        "target": mvp_target,
        "companion": {
            "companions": {
                "Spark": {
                    "offensive": [{"stat": "P.ATK", "value": 100.0}],
                    "defensive": [{"stat": "Max HP", "value": 500.0}]
                },
                "Wraith": {
                    "offense": [{"stat_name": "P.ATK", "value": 50.0}],
                    "defense": [{"stat_name": "Max HP", "value": 300.0}]
                }
            }
        },
        "divinity": {
            "Part I": {
                "quality": "gold",
                "level": 7,
                "has_flash": True
            }
        }
    }
    adapter = get_adapter("dragon_knight", {"dragon_knight": dk_manifest})
    tally = tally_player_stats(build, static_data, adapter.get_primary_conversion_fn())
    assert tally["stats"]["final_dmg_bonus_mvp_mini"] == pytest.approx(0.42)
    assert "pet_companion" in tally["breakdown"]["Max HP"]
    assert tally["breakdown"]["Max HP"]["pet_companion"] == 800.0
