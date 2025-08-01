"""
Simple pytest suite for main_auth.py
Run:  pytest -q
"""

# --- 1) Configure env *before* importing the app ----------------------------
import os, tempfile, pathlib, time, pytest
os.environ["EMPLOYEE_API_KEY"] = "testkey"   # test key
os.environ["EMPLOYEE_RATE_LIMIT"] = "3"      # lower limit → quicker test
os.environ["EMPLOYEE_RATE_PERIOD"] = "60"

# --- 2) Import the app -------------------------------------------------------
import main_auth
from fastapi.testclient import TestClient

# --- 3) Build a TestClient with an isolated temp DB --------------------------
@pytest.fixture(scope="session")
def client():
    """Fresh DB for the whole test session (keeps tests deterministic)."""
    tmp_db = pathlib.Path(tempfile.gettempdir()) / "employees_test.db"
    if tmp_db.exists():
        tmp_db.unlink()
    main_auth.DATABASE = str(tmp_db)   # point the app to the temp DB
    main_auth.init_db()                # create schema + seed data
    with TestClient(main_auth.app) as c:
        yield c            # provide the configured client to tests
    tmp_db.unlink(missing_ok=True)      # clean up after tests finish


API_HEADERS = {"X-API-Key": os.environ["EMPLOYEE_API_KEY"]}


# --- 4) Tests ----------------------------------------------------------------
def test_auth_required(client):
    r = client.get("/employees")                # NO key
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid or missing API Key"


def test_get_all_employees(client):
    r = client.get("/employees", headers=API_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    # seeded with 10 sample rows
    assert len(body) == 10


def test_create_employee(client):
    payload = {"name": "Zara Patel", "country": "India", "salary": 65000}
    r = client.post("/employees", json=payload, headers=API_HEADERS)
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == payload["name"]
    # new row should now exist
    r2 = client.get(f"/employees/{body['id']}", headers=API_HEADERS)
    assert r2.status_code == 200
    assert r2.json()["country"] == "India"


def test_update_employee(client):
    # pick existing ID 1 (from seed data)
    payload = {"name": "Alice J.", "country": "USA", "salary": 80000}
    r = client.put("/employees/1", json=payload, headers=API_HEADERS)
    assert r.status_code == 200
    r2 = client.get("/employees/1", headers=API_HEADERS)
    assert r2.json()["salary"] == 80000


def test_delete_employee(client):
    # create -> delete -> confirm gone
    r = client.post("/employees",
                    json={"name": "Temp", "country": "FR", "salary": 1},
                    headers=API_HEADERS)
    row_id = r.json()["id"]
    del_resp = client.delete(f"/employees/{row_id}", headers=API_HEADERS)
    assert del_resp.status_code == 204
    r2 = client.get(f"/employees/{row_id}", headers=API_HEADERS)
    assert r2.status_code == 404


def test_rate_limit(client):
    # EMPLOYEE_RATE_LIMIT is set to 3; 4th call within the
    # same period should trigger 429.
    for i in range(3):
        assert client.get("/employees", headers=API_HEADERS).status_code == 200
    r = client.get("/employees", headers=API_HEADERS)
    assert r.status_code == 429
    assert r.headers["Retry-After"] == "60"
