"""
Happy-path pytest suite for main_auth.py
Everything should succeed (2xx / 204); no 429s.

Run:
    pytest -q test_main_auth_success.py
"""

# ── 1) Environment setup *before* importing the app ──────────────────────────
import os, tempfile, pathlib, pytest
os.environ["EMPLOYEE_API_KEY"]     = "mysecretapikey"
os.environ["EMPLOYEE_RATE_LIMIT"]  = "10"   # ample for each individual test
os.environ["EMPLOYEE_RATE_PERIOD"] = "60"

# ── 2) Import the FastAPI app -------------------------------------------------
import main_auth                    # your existing file—unchanged
from fastapi.testclient import TestClient

# ── 3) One TestClient per session, pointing at a temp database ---------------
@pytest.fixture(scope="session")
def client():
    tmp_db = pathlib.Path(tempfile.gettempdir()) / "employees_success.db"
    if tmp_db.exists():
        tmp_db.unlink()             # start clean
    main_auth.DATABASE = str(tmp_db)
    main_auth.init_db()             # schema + seed rows

    with TestClient(main_auth.app) as c:
        yield c

    tmp_db.unlink(missing_ok=True)  # tidy up after all tests complete


API_HEADERS = {"X-API-Key": os.environ["EMPLOYEE_API_KEY"]}

# ── 4) NEW: reset the in-memory rate-limit log before *every* test ───────────
@pytest.fixture(autouse=True)
def _reset_rate_limit():
    """Ensure each test starts with an empty rate-limit history."""
    main_auth._request_log.clear()


# ── 5) Happy-path tests ──────────────────────────────────────────────────────
def test_get_employees_success(client):
    resp = client.get("/employees", headers=API_HEADERS)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_employee_success(client):
    payload = {"name": "Zara Patel", "country": "India", "salary": 65000}
    resp = client.post("/employees", json=payload, headers=API_HEADERS)
    assert resp.status_code == 201
    body = resp.json()
    assert all(k in body for k in ("id", "name", "country", "salary"))


def test_update_employee_success(client):
    # Create a row to update
    created_id = client.post(
        "/employees",
        json={"name": "Temp", "country": "IN", "salary": 1},
        headers=API_HEADERS,
    ).json()["id"]

    new_payload = {"name": "Temp Updated", "country": "IN", "salary": 70000}
    resp = client.put(f"/employees/{created_id}", json=new_payload, headers=API_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["salary"] == 70000


def test_delete_employee_success(client):
    # Add → delete → confirm gone
    eid = client.post(
        "/employees",
        json={"name": "DeleteMe", "country": "SG", "salary": 1},
        headers=API_HEADERS,
    ).json()["id"]

    del_resp = client.delete(f"/employees/{eid}", headers=API_HEADERS)
    assert del_resp.status_code == 204

    # Confirm it no longer exists
    all_rows = client.get("/employees", headers=API_HEADERS).json()
    assert eid not in [row["id"] for row in all_rows]


def test_rate_limit_never_exceeded(client):
    """Stay comfortably below the configured limit."""
    for _ in range(5):              # 5 < EMPLOYEE_RATE_LIMIT (10)
        r = client.get("/employees", headers=API_HEADERS)
        assert r.status_code == 200
