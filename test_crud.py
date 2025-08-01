"""
End-to-end CRUD tests for the Employee API.

• Assumes the FastAPI app is running at http://127.0.0.1:8000
• Uses the default API key 'mysecretapikey' unless overridden via env var.

Run:
    pytest -q test_crud.py
"""

import os
import random
import requests
from pprint import pprint    # standard-library pretty-printer
import pytest

# --------------------------------------------------------------------------- #
#  Configuration – override via environment variables if you wish            #
# --------------------------------------------------------------------------- #
BASE_URL = os.getenv("API_BASE", "http://127.0.0.1:8000")
API_KEY  = os.getenv("EMPLOYEE_API_KEY", "mysecretapikey")
HEADERS  = {"X-API-Key": API_KEY}

# Fail fast if the app isn’t reachable
@pytest.fixture(scope="session", autouse=True)
def _check_server_alive():
    try:
        requests.get(f"{BASE_URL}/docs", timeout=3)
    except requests.exceptions.RequestException as exc:
        pytest.skip(f"FastAPI server not reachable at {BASE_URL}: {exc}")

# --------------------------------------------------------------------------- #
#  Single happy-path test: Create → Read → Update → Delete → 404             #
# --------------------------------------------------------------------------- #
def test_crud_flow():
    # ---------- 1) CREATE --------------------------------------------------- #
    payload = {
        "name":    f"User{random.randint(1000, 9999)}",
        "country": "IN",
        "salary":  50000,
    }
    r = requests.post(f"{BASE_URL}/employees", json=payload, headers=HEADERS)
    assert r.status_code == 201
    emp = r.json()
    emp_id = emp["id"]
    pprint({"created": emp})

    # ---------- 2) READ ----------------------------------------------------- #
    r = requests.get(f"{BASE_URL}/employees/{emp_id}", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["country"] == "IN"

    # ---------- 3) UPDATE --------------------------------------------------- #
    updated = {**payload, "salary": 60000}
    r = requests.put(f"{BASE_URL}/employees/{emp_id}", json=updated, headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["salary"] == 60000

    # ---------- 4) DELETE --------------------------------------------------- #
    r = requests.delete(f"{BASE_URL}/employees/{emp_id}", headers=HEADERS)
    assert r.status_code == 204

    # ---------- 5) CONFIRM 404 --------------------------------------------- #
    r = requests.get(f"{BASE_URL}/employees/{emp_id}", headers=HEADERS)
    assert r.status_code == 404
