import pytest
from starlette.testclient import TestClient
from rox_wiki import database as db
from rox_wiki import level_scaler as scaler
from rox_wiki.server import app

client = TestClient(app)

def test_load_growth_curves():
    curves = scaler.load_growth_curves()
    assert len(curves) == 200
    assert 1 in curves
    assert 50 in curves
    assert 132 in curves
    assert 200 in curves
    assert curves[132]["hp"] > curves[50]["hp"]
    assert curves[132]["def"] > curves[50]["def"]

def test_scale_monster_same_level():
    m = db.get_monster_by_id(10001)
    res = scaler.scale_monster(m, 1)
    assert res["is_scaled"] is False
    assert res["level"] == 1
    assert res["max_hp"] == m["max_hp"]

def test_scale_monster_higher_level():
    m = db.get_monster_by_id(10001)
    res = scaler.scale_monster(m, 50)
    assert res["is_scaled"] is True
    assert res["level"] == 50
    assert res["max_hp"] > m["max_hp"]
    assert res["p_def"] >= m["p_def"]
    assert res["hit"] == m["hit"] + 3 * (50 - 1)
    assert res["flee"] == m["flee"] + 3 * (50 - 1)
    assert res["base_exp"] > m["base_exp"]

def test_scale_boss_to_level_132():
    strouf = db.get_monster_by_id(30005)
    res = scaler.scale_monster(strouf, 132)
    assert res["is_scaled"] is True
    assert res["level"] == 132
    assert res["max_hp"] > strouf["max_hp"]
    assert res["p_def"] > strouf["p_def"]
    assert res["scale_ratio"] > 1.0

def test_scale_api_endpoint():
    res = client.get("/api/db/monsters/10001/scale?level=80")
    assert res.status_code == 200
    data = res.json()
    assert data["level"] == 80
    assert data["is_scaled"] is True
    assert data["name"] == "Poring"

def test_scale_api_invalid_monster():
    res = client.get("/api/db/monsters/9999999/scale?level=50")
    assert res.status_code == 404

def test_canonical_monsters_default_filtering():
    res = client.get("/api/db/monsters?limit=100")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    for item in data["items"]:
        assert item["is_canonical"] == 1

def test_all_variants_explicit_filtering():
    res = client.get("/api/db/monsters?canonical=false&limit=20")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 3000
