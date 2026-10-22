import pytest
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent / "src" / "rox_wiki"

def test_cyberpunk_hud_tokens():
    css_path = ROOT_DIR / "static" / "wiki.css"
    assert os.path.exists(css_path), "wiki.css must exist"
    with open(css_path, "r", encoding="utf-8") as file:
        content = file.read()
    assert "#090d16" in content.lower() or "#0a0a0f" in content.lower(), "Must include OLED void black token"
    assert "--border-focus" in content, "Must include border-focus token"

def test_master_gear_studio_markup():
    html_path = ROOT_DIR / "templates" / "index.html"
    assert os.path.exists(html_path), "index.html must exist"
    with open(html_path, "r", encoding="utf-8") as file:
        content = file.read()
    assert "master-gear-studio-dialog" in content, "Must contain master-gear-studio-dialog"
    assert "gear-modal-wing-left" in content, "Must contain left wing container"
    assert "gear-modal-wing-right" in content, "Must contain right wing container"
    assert "drawer-equip-body" in content, "Must contain center dynamic editor container"
