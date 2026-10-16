import pytest
from fastapi.testclient import TestClient
from rox_wiki.server import app

client = TestClient(app)


def test_stateless_calculation_with_breakdown():
    with TestClient(app) as client:
        payload = {
            "build": {
                "class_id": "dragon_knight",
                "is_pvp": False,
                "stats": {"str": 100, "vit": 50, "dex": 30},
                "job_stats": {"str": 40, "vit": 20, "dex": 10},
                "battle_achievement": {
                    "str": 72,
                    "vit": 72,
                    "final_pdmg_bonus": 0.24,
                    "fire_enhance": 0.3
                },
                "loadout": {
                    "weapon": {
                        "name": "Teeth Bone Broadsword",
                        "type": "2H Sword",
                        "upgrade": 10,
                        "refine": 5,
                        "enchant_lines": [
                            {"line_index": 1, "city": "Payon", "stat": "P.ATK", "level": 10},
                            {"line_index": 2, "city": "Payon", "stat": "P.ATK", "level": 10},
                            {"line_index": 3, "city": "Payon", "stat": "P.ATK", "level": 5}
                        ],
                        "cards": ["Minorous Card"]
                    }
                },
                "buffs": {
                    "elemental_converter": "Fire",
                    "spear_flash": True
                },
                "target": {
                    "name": "Lord of the Dead Lv.150",
                    "race": "Formless",
                    "size": "Large",
                    "element": "Shadow",
                    "p_def_pct": 0.5,
                    "final_p_def": 0.0
                }
            }
        }

        res = client.post("/api/sim/calculate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "dps" in data
        assert data["dps"] > 0
        assert "talliedStats" in data
        assert "statBreakdown" in data

        # Verify 100% Traceability in breakdown
        breakdown = data["statBreakdown"]
        assert "STR" in breakdown
        assert "base_and_job" in breakdown["STR"]
        assert "battle_achievement" in breakdown["STR"]

        assert "P.ATK" in breakdown
        assert "enchant_weapon" in breakdown["P.ATK"]


def test_ssot_reference_endpoints():
    with TestClient(app) as client:
        # 1. Class
        res = client.get("/api/sim/reference/class/dragon_knight")
        assert res.status_code == 200
        assert res.json()["primary_stat"] == "STR"

        # 2. Enchant Rules (3 independent lines can query Payon weapon)
        res = client.get("/api/sim/reference/enchant-rules?city=Payon&slot_category=weapon")
        assert res.status_code == 200
        stats = [r["stat_name"] for r in res.json()]
        assert "P.ATK" in stats

        # 3. Combat Rules
        res = client.get("/api/sim/reference/combat-rules/element_matrix")
        assert res.status_code == 200
        assert len(res.json()) >= 50

