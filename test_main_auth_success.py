"""
Happy-path tests for main_auth.py.
All HTTP responses should be 2xx.
Run:  pytest -q test_main_auth_success.py
"""

# ── 1) Prepare environment BEFORE importing the app ──────────────────────────
import os, tempfile, pathlib, pytest

BASE = os.getenv("API_BASE", "http://localhost:8000")
API_HEADERS = {"X-API-Key": os.getenv("mysecretapikey")}
os.environ["EMPLOYEE_RATE_LIMIT"] = "10"     # generous → no 429s
os.environ["EMPLOYEE_RATE_PERIOD"] = "60"

# ── 2) Import the app and helpers ────────────────────────────────────────────
import main_auth
from fastapi.testclient import TestClient

# ── 3) Provide a fresh temp-file database for every test session ─────────────
@pytest.fixture(scope="session")
def client():
    tmp_db = pathlib.Path(tempfile.gettempdir()) / "employees_success.db"
    if tmp_db.exists():
        tmp_db.unlink()                      # start clean
    main_auth.DATABASE = str(tmp_db)         # point app at temp DB
    main_auth.init_db()                      # create schema + seed rows

    with TestClient(main_auth.app) as c:
        yield c                              # hand the client to tests

    tmp_db.unlink(missing_ok=True)           # tidy up


API_HEADERS = {"X-API-Key": os.environ["EMPLOYEE_API_KEY"]}


# ── 4) Happy-path tests ──────────────────────────────────────────────────────
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
    # Update the employee we just created (ID comes from previous test)
    new_payload = {"name": "Z. Patel", "country": "India", "salary": 70000}
    created_id = client.post(                  # create another row
        "/employees",
        json={"name": "Temp", "country": "IN", "salary": 1},
        headers=API_HEADERS,
    ).json()["id"]

    resp = client.put(
        f"/employees/{created_id}",
        json=new_payload,
        headers=API_HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["salary"] == 70000


def test_delete_employee_success(client):
    # Add → delete → confirm gone with GET list count drop
    eid = client.post(
        "/employees",
        json={"name": "DeleteMe", "country": "SG", "salary": 1},
        headers=API_HEADERS,
    ).json()["id"]

    del_resp = client.delete(f"/employees/{eid}", headers=API_HEADERS)
    assert del_resp.status_code == 204

    all_rows = client.get("/employees", headers=API_HEADERS).json()
    assert eid not in [row["id"] for row in all_rows]


def test_rate_limit_never_exceeded(client):
    """Stay comfortably below the configured rate limit."""
    for _ in range(5):                        # 5 < EMPLOYEE_RATE_LIMIT (10)
        r = client.get("/employees", headers=API_HEADERS)
        assert r.status_code == 200
