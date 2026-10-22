import json
from pathlib import Path
import pytest
from starlette.testclient import TestClient
from rox_wiki.server import app

ROOT_DIR = Path(__file__).resolve().parent.parent
INDEX_HTML_PATH = ROOT_DIR / "src" / "rox_wiki" / "templates" / "index.html"
GOLDEN_BUILDS_PATH = Path(__file__).resolve().parent / "golden_builds.json"

REQUIRED_SLOTS = [
    "weapon",
    "clothes",
    "cloak",
    "shoes",
    "accessory_1",
    "accessory_2",
    "talisman",
    "costume_head",
    "costume_eyes",
    "costume_mouth",
    "costume_back",
]


def test_golden_loadout_slot_coverage():
    with open(GOLDEN_BUILDS_PATH, "r", encoding="utf-8") as f:
        goldens = json.load(f)
    
    builds = [b for b in goldens.get("builds", []) if b.get("class_id") == "dragon_knight"]
    assert len(builds) > 0, "No dragon_knight build found in golden_builds.json"
    dk_build = builds[0]
    loadout = dk_build.get("input", {}).get("loadout", {})
    
    for slot in REQUIRED_SLOTS:
        assert slot in loadout, f"Slot {slot} missing from golden loadout"
        slot_data = loadout[slot]
        assert "refine" in slot_data
        assert "upgrade" in slot_data


def test_cockpit_view_markup_structure():
    assert INDEX_HTML_PATH.exists()
    content = INDEX_HTML_PATH.read_text(encoding="utf-8")
    
    assert "cockpit-layout" in content, "Missing .cockpit-layout in index.html"
    assert "cockpit-workspace" in content, "Missing .cockpit-workspace in index.html"
    assert "cockpit-hud" in content, "Missing .cockpit-hud in index.html"
    assert "paper-doll-container" in content, "Missing .paper-doll-container in index.html"
    
    for slot in REQUIRED_SLOTS:
        assert f'data-slot="{slot}"' in content or f'id="slot-{slot}"' in content or f'data-slot-key="{slot}"' in content, f"Slot {slot} missing in paper doll markup"


def test_equip_drawer_markup_exists():
    assert INDEX_HTML_PATH.exists()
    content = INDEX_HTML_PATH.read_text(encoding="utf-8")
    
    assert "sim-equip-drawer" in content, "Missing #sim-equip-drawer in index.html"
    assert "drawer-equip-body" in content, "Missing #drawer-equip-body in index.html"
    assert "btn-close-equip-drawer" in content, "Missing #btn-close-equip-drawer in index.html"
    assert "sim-drawer-backdrop" in content, "Missing #sim-drawer-backdrop in index.html"


def test_secondary_systems_accordions_markup():
    assert INDEX_HTML_PATH.exists()
    content = INDEX_HTML_PATH.read_text(encoding="utf-8")
    
    assert 'id="acc-base-stats"' in content, "Missing #acc-base-stats accordion"
    assert 'id="acc-progression"' in content, "Missing #acc-progression accordion"
    assert 'id="acc-buffs"' in content, "Missing #acc-buffs accordion"
    assert 'id="acc-pet"' in content, "Missing #acc-pet accordion"
    assert 'id="acc-divinity"' in content, "Missing #acc-divinity accordion"


def test_duplicate_enchant_stats_payload_valid():
    with open(GOLDEN_BUILDS_PATH, "r", encoding="utf-8") as f:
        goldens = json.load(f)
    build = goldens["builds"][0]["input"]
    build["class_id"] = "dragon_knight"
    
    # Configure 3 identical enchant lines in weapon slot (Payon P.ATK Level 6)
    weapon = build["loadout"]["weapon"]
    weapon["enchant_lines"] = [
        {"city": "Payon", "stat": "P.ATK", "level": 6},
        {"city": "Payon", "stat": "P.ATK", "level": 6},
        {"city": "Payon", "stat": "P.ATK", "level": 6},
    ]
    
    with TestClient(app) as client:
        res = client.post("/api/sim/calculate", json={"build": build})
        assert res.status_code == 200, f"Engine failed on duplicate enchants: {res.text}"
        data = res.json()
        assert "statBreakdown" in data
        assert "P.ATK" in data["statBreakdown"]
        # Breakdown should contain enchant_weapon source with non-zero bonus
        assert "enchant_weapon" in data["statBreakdown"]["P.ATK"]
        assert data["statBreakdown"]["P.ATK"]["enchant_weapon"] > 0
        assert data["dps"] > 0


def test_paper_doll_balanced_two_column_structure():
    assert INDEX_HTML_PATH.exists()
    content = INDEX_HTML_PATH.read_text(encoding="utf-8")
    assert "doll-col-left" in content, "Missing .doll-col-left in index.html"
    assert "doll-col-right" in content, "Missing .doll-col-right in index.html"
    assert "doll-center-preview" in content, "Missing .doll-center-preview in index.html"


def test_divinity_named_and_indexed_substats_tally():
    from rox_wiki.engine import tally_divinity_stats
    static_data = json.load(open(ROOT_DIR / "src" / "rox_wiki" / "static" / "data" / "static_game_data.json", encoding="utf-8"))
    
    # 1. Named part test with substats
    named_div = {
        "Spear of Eternity": {
            "quality": "gold",
            "level": 7,
            "selected_substats": ["STR", "P.ATK%"]
        }
    }
    tally1 = tally_divinity_stats(named_div, static_data)
    assert tally1.get("STR", 0) > 0, "Named divinity part failed to calculate STR substat"
    assert tally1.get("P.ATK%", 0) > 0, "Named divinity part failed to calculate P.ATK% substat"
    assert tally1.get("Max HP", 0) > 0, "Named divinity part failed to calculate Max HP main stat"

    # 2. Keyed part test (Part I)
    keyed_div = {
        "Part I": {
            "quality": "gold",
            "level": 7,
            "selected_substats": ["STR", "P.ATK%"]
        }
    }
    tally2 = tally_divinity_stats(keyed_div, static_data)
    assert tally2.get("STR", 0) == tally1.get("STR", 0), "Keyed Part I failed parity with named part"
    assert tally2.get("P.ATK%", 0) == tally1.get("P.ATK%", 0), "Keyed Part I failed parity with named part"


def test_favicon_served_and_linked():
    content = INDEX_HTML_PATH.read_text(encoding="utf-8")
    assert 'rel="icon"' in content, "Missing rel=icon in index.html"

    with TestClient(app) as client:
        res = client.get("/favicon.ico")
        assert res.status_code == 200, f"GET /favicon.ico returned {res.status_code}"
        assert len(res.content) > 0, "Favicon content was empty"
        assert "image/" in res.headers.get("content-type", "").lower()


def test_bento_grid_architecture_markup():
    content = INDEX_HTML_PATH.read_text(encoding="utf-8")
    assert 'bento-grid-container' in content, "Missing .bento-grid-container in index.html"
    assert 'id="bento-equip"' in content, "Missing #bento-equip Bento card"
    assert 'id="bento-systems"' in content, "Missing #bento-systems Bento card"
    assert 'id="bento-hud"' in content, "Missing #bento-hud Bento card"
    assert 'id="bento-calibrator"' in content, "Missing #bento-calibrator Bento card"


def test_detailed_stat_calibrator_markup():
    content = INDEX_HTML_PATH.read_text(encoding="utf-8")
    assert 'id="sim-stat-calibrator"' in content, "Missing #sim-stat-calibrator table wrapper"
    assert 'id="sim-stat-calibrator-table"' in content, "Missing #sim-stat-calibrator-table"
    assert 'id="btn-calibrator-reset"' in content, "Missing #btn-calibrator-reset button"
    assert 'STAT NAME' in content
    assert 'GEAR BASE' in content
    assert '[+/- OFFSET]' in content
    assert 'EFFECTIVE TOTAL' in content


def test_secondary_systems_summary_tiles_and_modals():
    content = INDEX_HTML_PATH.read_text(encoding="utf-8")
    assert 'id="tile-base-stats"' in content
    assert 'id="tile-divinity"' in content
    assert 'id="tile-companions"' in content
    assert 'id="tile-buffs"' in content

    # Center Modals
    assert 'id="modal-base-stats"' in content
    assert 'id="modal-buffs"' in content
    assert 'id="divinity-modal"' in content
    assert 'id="companion-modal"' in content


def test_monster_drawer_test_dps_bridge_cta():
    wiki_js_path = ROOT_DIR / "src" / "rox_wiki" / "static" / "wiki.js"
    assert wiki_js_path.exists()
    content = wiki_js_path.read_text(encoding="utf-8")
    assert 'btn-wiki-test-dps' in content, "Missing .btn-wiki-test-dps class in wiki.js"
    assert 'id="btn-wiki-test-dps"' in content, "Missing #btn-wiki-test-dps button in wiki.js"
    assert 'Test DPS on this Monster' in content, "Missing in-game English CTA text"


def test_overview_cards_and_drawer_popup_contract():
    content = INDEX_HTML_PATH.read_text(encoding="utf-8")
    assert 'id="card-overview-gear"' in content, "Missing #card-overview-gear in index.html"
    assert 'id="card-overview-costumes"' in content, "Missing #card-overview-costumes in index.html"
    assert 'data-subsystem="gear"' in content, "Missing data-subsystem=gear in index.html"
    assert 'data-subsystem="costumes"' in content, "Missing data-subsystem=costumes in index.html"
    assert 'id="sim-equip-drawer"' in content, "Missing #sim-equip-drawer in index.html"
    assert 'id="sim-drawer-backdrop"' in content, "Missing #sim-drawer-backdrop in index.html"


