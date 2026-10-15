import pytest
from rox_wiki import database as db



def test_get_database_summary():
    summary = db.get_database_summary()
    assert summary["status"] == "ready"
    assert summary["monsters"] > 3000
    assert summary["cards"] > 800
    assert summary["dummies"] > 0


def test_search_monsters_drake():
    res = db.search_monsters(query="Drake", limit=10)
    assert res["total"] > 0
    names = [m["name"] for m in res["items"]]
    assert any("Drake" in n for n in names)
    drake = res["items"][0]
    assert "race_name" in drake
    assert "element_name" in drake
    assert "size_name" in drake


def test_search_monsters_by_filters():
    res = db.search_monsters(is_mvp=True, limit=5)
    assert res["total"] >= 0
    for m in res["items"]:
        assert m["is_mvp"] == 1


def test_get_monster_by_id():
    poring = db.get_monster_by_id(10001)
    assert poring is not None
    assert poring["name"] == "Poring"
    assert poring["level"] == 1
    assert poring["race_name"] == "Plant"
    assert poring["element_name"] == "Water"
    assert poring["size_name"] == "Medium"
    assert "hit" in poring
    assert "flee" in poring
    assert "crit" in poring
    assert "anti_crit" in poring
    assert "p_pen" in poring
    assert "m_pen" in poring
    assert "icon_url" in poring
    assert poring["icon_url"] == "/static/monsters/10001.png"
    assert poring["is_canonical"] == 1
    assert poring["card_id"] == 10102001
    assert poring["card"] is not None
    assert poring["card"]["name"] == "Poring Card"
    assert poring["card"]["slot_name"] == "Headgear"


def test_search_cards_and_get_detail():
    res = db.search_cards(query="Minorous", limit=5)
    assert res["total"] > 0
    card = res["items"][0]
    assert "Minorous" in card["name"]
    assert "slot_name" in card
    assert card["slot_name"] == "Weapon"

    detail = db.get_card_by_id(card["id"])
    assert detail is not None
    assert detail["id"] == card["id"]
    assert detail["slot_name"] == "Weapon"
    assert "attr_desc" in detail


def test_get_dps_dummies():
    dummies = db.get_dps_dummies()
    assert len(dummies) > 0
    assert "name" in dummies[0]
    assert "monster_id" in dummies[0]


def test_fastapi_db_endpoints():
    from starlette.testclient import TestClient
    from rox_wiki.server import app


    client = TestClient(app)

    r = client.get("/api/db/overview")
    assert r.status_code == 200
    assert r.json()["monsters"] > 3000

    r = client.get("/api/db/monsters?query=Poring&limit=5")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] > 0
    assert any(m["name"] == "Poring" for m in data["items"])

    r = client.get("/api/db/monsters/10001")
    assert r.status_code == 200
    assert r.json()["name"] == "Poring"

    r = client.get("/api/db/monsters/9999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Monster not found"

    r = client.get("/api/db/cards?query=Minorous&limit=5")
    assert r.status_code == 200
    assert r.json()["total"] > 0

    card_id = r.json()["items"][0]["id"]
    r = client.get(f"/api/db/cards/{card_id}")
    assert r.status_code == 200
    assert r.json()["id"] == card_id

    r = client.get("/api/db/cards/9999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Card not found"

    r = client.get("/api/db/dummies")
    assert r.status_code == 200
    assert len(r.json()) > 0

    r = client.get("/static/items/10001.png")
    assert r.status_code == 200
    assert r.headers["content-type"] in ["image/png", "application/octet-stream"]
    assert len(r.content) > 100

    r = client.get("/api/db/meta")
    assert r.status_code == 200
    meta = r.json()
    assert len(meta["elements"]) > 0
    assert len(meta["races"]) > 0
    assert len(meta["types"]) > 0

    r = client.get("/")
    assert r.status_code == 200
    assert "ROX WIKI" in r.text

    r = client.get("/ui/wiki.css")
    assert r.status_code == 200
    assert "--bg-canvas" in r.text

    r = client.get("/ui/wiki.js")
    assert r.status_code == 200
    assert "data-theme" in r.text

    r = client.get("/api/db/pets?limit=5")
    assert r.status_code == 200
    assert r.json()["total"] > 0

    r = client.get("/api/db/shadow-weapons?limit=5")
    assert r.status_code == 200
    assert r.json()["total"] > 0


def test_get_database_metadata_direct():
    meta = db.get_database_metadata()
    assert isinstance(meta, dict)
    assert "Fire" in meta["elements"]
    assert "Dragon" in meta["races"]
    assert "Large" in meta["sizes"]


def test_get_pet_and_shadow_weapon_direct():
    pets = db.search_pets(limit=3)
    assert pets["total"] > 0
    pet_id = pets["items"][0]["id"]
    p = db.get_pet_by_id(pet_id)
    assert p is not None
    assert p["id"] == pet_id

    sws = db.search_shadow_weapons(limit=3)
    assert sws["total"] > 0
    sw_id = sws["items"][0]["id"]
    sw = db.get_shadow_weapon_by_id(sw_id)
    assert sw is not None
    assert sw["id"] == sw_id


def test_numeric_id_search():
    m = db.search_monsters(query="10001", limit=1)
    assert m["total"] == 1
    assert m["items"][0]["name"] == "Poring"

    c = db.search_cards(query="10101043", limit=5)
    assert c["total"] >= 1
    assert any(card["id"] == 10101043 for card in c["items"])

    p = db.search_pets(query="85039", limit=1)
    assert p["total"] == 1
    assert p["items"][0]["name"] == "WarGreymon"

    sw = db.search_shadow_weapons(query="101001", limit=1)
    assert sw["total"] == 1
    assert "Devourer" in sw["items"][0]["name"]


def test_monster_sorting_and_level_filtering():
    res = db.search_monsters(is_mvp=True, sort_by="level_desc", limit=5)
    assert res["total"] > 0
    levels = [m["level"] for m in res["items"]]
    assert levels == sorted(levels, reverse=True)
    assert levels[0] >= 100

    filtered = db.search_monsters(is_mvp=True, min_level=80, max_level=100, limit=20)
    assert filtered["total"] > 0
    for m in filtered["items"]:
        assert 80 <= m["level"] <= 100


def test_monster_variants_and_endpoint():
    from starlette.testclient import TestClient
    from rox_wiki.server import app

    variants = db.get_monster_variants("Drake")
    assert len(variants) >= 5
    levels = [v["level"] for v in variants]
    assert 40 in levels
    assert 100 in levels

    poring = db.get_monster_by_id(10001)
    assert "variants" in poring
    assert len(poring["variants"]) >= 1

    client = TestClient(app)
    r = client.get("/api/db/monsters?is_mvp=true&sort_by=level_desc&limit=5")
    assert r.status_code == 200
    assert r.json()["items"][0]["level"] >= 100

    r = client.get("/api/db/monsters/34004/variants")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 5
    assert any(x["level"] == 100 for x in data)


def test_card_slot_mapping_and_api():
    from starlette.testclient import TestClient
    from rox_wiki.server import app

    client = TestClient(app)

    # Test metadata includes card_slots
    meta_r = client.get("/api/db/meta")
    assert meta_r.status_code == 200
    meta = meta_r.json()
    assert "card_slots" in meta
    assert len(meta["card_slots"]) == 8
    slot_names = [s["name"] for s in meta["card_slots"]]
    assert "Weapon" in slot_names
    assert "Armor" in slot_names
    assert "Headgear" in slot_names
    assert "Accessory" in slot_names

    # Test filtering cards by slot (card_type=1 -> Weapon)
    weapon_r = client.get("/api/db/cards?card_type=1&limit=10")
    assert weapon_r.status_code == 200
    weapons = weapon_r.json()["items"]
    assert len(weapons) > 0
    for w in weapons:
        assert w["card_type"] == 1
        assert w["slot_name"] == "Weapon"

    # Test monster detail includes hydrated card
    poring_r = client.get("/api/db/monsters/10001")
    assert poring_r.status_code == 200
    poring = poring_r.json()
    assert poring["card"] is not None
    assert poring["card"]["slot_name"] == "Headgear"
    assert poring["card"]["id"] == poring["card_id"]


def test_combat_stats_and_agav_benchmark():
    agav = db.get_monster_by_id(10298)
    assert agav is not None
    assert agav["name"] == "Agav"
    assert agav["level"] == 150
    assert agav["race_name"] == "Demi-Human"
    assert agav["element_name"] == "Neutral"
    assert agav["max_hp"] == 38464399

    assert round(agav["total_def"], 2) == 130.08
    assert round(agav["def_base"], 2) == 77.08
    assert round(agav["def_ext"], 2) == 53.00

    assert round(agav["total_mdef"], 2) == 216.83
    assert round(agav["mdef_base"], 2) == 110.83
    assert round(agav["mdef_ext"], 2) == 106.00

    assert round(agav["total_crit_res"], 2) == 150.43
    assert round(agav["crit_res_base"], 2) == 66.43
    assert round(agav["crit_res_ext"], 2) == 84.00

    assert round(agav["total_flee"], 2) == 77.30
    assert round(agav["flee_base"], 2) == 37.30
    assert round(agav["flee_ext"], 2) == 40.00


def test_weather_cards_multi_drop():
    # Angeling (30001)
    angeling = db.get_monster_by_id(30001)
    assert angeling is not None
    assert "cards" in angeling
    assert len(angeling["cards"]) == 3
    phases = {c["weather_phase"]: c for c in angeling["cards"]}
    assert "Day" in phases
    assert "Night" in phases
    assert "Void" in phases
    assert phases["Day"]["slot_name"] == "Armor"
    assert phases["Night"]["slot_name"] == "Weapon"
    assert phases["Void"]["slot_name"] == "Accessory"

    # Armored Titan (30092)
    titan = db.get_monster_by_id(30092)
    assert titan is not None
    assert "cards" in titan
    assert len(titan["cards"]) == 3
    t_phases = {c["weather_phase"]: c for c in titan["cards"]}
    assert "Day" in t_phases
    assert "Night" in t_phases
    assert "Void" in t_phases
    assert t_phases["Day"]["slot_name"] == "Armor"
    assert t_phases["Night"]["slot_name"] == "Cloak"
    assert t_phases["Void"]["slot_name"] == "Shoes"


def test_categories_filtering():
    monsters_res = db.search_monsters(category="monster", limit=50)
    assert monsters_res["total"] > 0
    for m in monsters_res["items"]:
        assert m["is_mvp"] == 0
        assert m["is_mini"] == 0

    mvp_res = db.search_monsters(category="mvp", limit=50)
    assert mvp_res["total"] > 0
    for m in mvp_res["items"]:
        assert m["is_mvp"] == 1 or m["is_mini"] == 1


def test_card_attribute_enrichment_coverage():
    conn = db.get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM cards")
    total_cards = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM cards WHERE attr_desc IS NOT NULL AND trim(attr_desc) != ''")
    cards_with_attr = cur.fetchone()[0]

    coverage_pct = cards_with_attr / total_cards * 100
    assert coverage_pct >= 97.0

    cur.execute("SELECT id, name, attr_desc FROM cards WHERE name = 'Shellfish Card'")
    shellfish = cur.fetchone()
    assert shellfish is not None
    assert "Earth Enhance" in shellfish[2] or "Fire Enhance" in shellfish[2]

    cur.execute("SELECT id, name, attr_desc FROM cards WHERE name LIKE '%Necromancer Card [Day]%'")
    necromancer = cur.fetchone()
    assert necromancer is not None
    assert "crit dmg" in necromancer[2].lower()

    cur.execute("SELECT id, name, attr_desc FROM cards WHERE name LIKE '%Arc Angeling Card [Night]%'")
    arc_angeling = cur.fetchone()
    assert arc_angeling is not None
    assert "pvp final m.dmg red" in arc_angeling[2].lower()

    cur.execute("SELECT id, name, attr_desc FROM cards WHERE id = 10101057")
    baphomet = cur.fetchone()
    assert baphomet is not None
    assert "splash" in baphomet[2].lower()

    cur.execute("SELECT id, name, attr_desc FROM cards WHERE id = 10102062")
    porcellio = cur.fetchone()
    assert porcellio is not None
    assert "max hp" in porcellio[2].lower()

