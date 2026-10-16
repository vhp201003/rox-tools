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
