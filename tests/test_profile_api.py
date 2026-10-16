import json
import uuid
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from rox_wiki.server import app

client = TestClient(app)

DK_MANIFEST_PATH = Path("src/rox_wiki/static/data/dragon_knight_manifest.json")

@pytest.fixture(scope="module")
def sample_build():
    with open(DK_MANIFEST_PATH, encoding="utf-8") as f:
        dk = json.load(f)
    b = dk["default_baseline"]
    b["class_id"] = "dragon_knight"
    return b


def test_profile_crud_lifecycle(sample_build):
    with TestClient(app) as client:
        profile_id = str(uuid.uuid4())

        # 1. GET non-existent -> 404
        res = client.get(f"/api/sim/profiles/{profile_id}")
        assert res.status_code == 404

        # 2. POST create/commit
        payload = {"build": sample_build}
        res = client.post(f"/api/sim/profiles/{profile_id}", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == profile_id
        assert data["class_id"] == "dragon_knight"
        assert data["computed_dps"] == 94413
        assert data["computed_results"]["dps"] == 94413
        assert data["computed_results"]["talliedStats"]["P.ATK"] == 738.0

        # 3. GET profile
        res = client.get(f"/api/sim/profiles/{profile_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == profile_id
        assert data["computed_dps"] == 94413

        # 4. PUT update profile (e.g. change STR)
        modified_build = json.loads(json.dumps(sample_build))
        modified_build["stats"]["str"] = 150
        res = client.put(f"/api/sim/profiles/{profile_id}", json={"build": modified_build})
        assert res.status_code == 200
        data = res.json()
        assert data["computed_dps"] > 94413

        # 5. Invalid UUID format validation check
        res = client.get("/api/sim/profiles/not-a-valid-uuid")
        assert res.status_code == 422

        # 6. DELETE profile
        res = client.delete(f"/api/sim/profiles/{profile_id}")
        assert res.status_code == 200
        assert res.json()["status"] == "deleted"

        # 7. GET after delete -> 404
        res = client.get(f"/api/sim/profiles/{profile_id}")
        assert res.status_code == 404
