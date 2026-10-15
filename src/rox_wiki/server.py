"""ROX Wiki API server."""

import sys
from pathlib import Path
from typing import Optional

SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from rox_wiki import database as db
from rox_wiki import level_scaler as scaler

STATIC_DIR = SRC_DIR.parent / "data" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

UI_DIR = Path(__file__).resolve().parent / "static"
UI_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
INDEX_FILE = TEMPLATES_DIR / "index.html"

app = FastAPI(title="ROX Wiki")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/ui", StaticFiles(directory=str(UI_DIR)), name="ui")


@app.get("/")
def index():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return HTMLResponse(content="<!DOCTYPE html><html><head><title>ROX WIKI</title></head><body><h1>ROX WIKI [v2.0]</h1></body></html>")


@app.get("/api/db/overview")
def get_db_overview():
    return db.get_database_summary()


@app.get("/api/db/meta")
def get_db_metadata():
    return db.get_database_metadata()


@app.get("/api/db/monsters")
def search_monsters_endpoint(
    query: Optional[str] = None,
    category: Optional[str] = None,
    type_name: Optional[str] = None,
    element: Optional[str] = None,
    race: Optional[str] = None,
    is_mvp: Optional[bool] = None,
    min_level: Optional[int] = None,
    max_level: Optional[int] = None,
    sort_by: Optional[str] = None,
    canonical: Optional[bool] = None,
    page: int = 1,
    limit: int = 20,
):
    return db.search_monsters(
        query=query, category=category, type_name=type_name, element=element,
        race=race, is_mvp=is_mvp, min_level=min_level,
        max_level=max_level, sort_by=sort_by, canonical_only=canonical,
        page=page, limit=limit,
    )


@app.get("/api/db/monsters/{monster_id}")
def get_monster_detail_endpoint(monster_id: int):
    m = db.get_monster_by_id(monster_id)
    if not m:
        raise HTTPException(status_code=404, detail="Monster not found")
    return m


@app.get("/api/db/monsters/{monster_id}/scale")
def scale_monster_endpoint(monster_id: int, level: int = 1):
    m = db.get_monster_by_id(monster_id)
    if not m:
        raise HTTPException(status_code=404, detail="Monster not found")
    return scaler.scale_monster(m, level)


@app.get("/api/db/monsters/{monster_id}/variants")
def get_monster_variants_endpoint(monster_id: int):
    m = db.get_monster_by_id(monster_id)
    if not m:
        raise HTTPException(status_code=404, detail="Monster not found")
    return db.get_monster_variants(m["name"])


@app.get("/api/db/cards")
def search_cards_endpoint(
    query: Optional[str] = None,
    quality: Optional[int] = None,
    card_type: Optional[int] = None,
    is_mvp: Optional[bool] = None,
    page: int = 1,
    limit: int = 20,
):
    return db.search_cards(
        query=query, quality=quality, card_type=card_type, is_mvp=is_mvp, page=page, limit=limit
    )


@app.get("/api/db/cards/{card_id}")
def get_card_detail_endpoint(card_id: int):
    c = db.get_card_by_id(card_id)
    if not c:
        raise HTTPException(status_code=404, detail="Card not found")
    return c


@app.get("/api/db/dummies")
def get_dps_dummies_endpoint():
    return db.get_dps_dummies()


@app.get("/api/db/pets")
def search_pets_endpoint(
    query: Optional[str] = None,
    quality: Optional[int] = None,
    page: int = 1,
    limit: int = 20,
):
    return db.search_pets(query=query, quality=quality, page=page, limit=limit)


@app.get("/api/db/pets/{pet_id}")
def get_pet_detail_endpoint(pet_id: int):
    p = db.get_pet_by_id(pet_id)
    if not p:
        raise HTTPException(status_code=404, detail="Pet not found")
    return p


@app.get("/api/db/shadow-weapons")
def search_shadow_weapons_endpoint(
    query: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
):
    return db.search_shadow_weapons(query=query, page=page, limit=limit)


@app.get("/api/db/shadow-weapons/{sw_id}")
def get_shadow_weapon_detail_endpoint(sw_id: int):
    sw = db.get_shadow_weapon_by_id(sw_id)
    if not sw:
        raise HTTPException(status_code=404, detail="Shadow Weapon not found")
    return sw


def run():
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=False)


if __name__ == "__main__":
    run()
