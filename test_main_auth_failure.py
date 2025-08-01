"""
Negative-path tests for main_auth.py

* test_rate_limit_triggers_429  – go past the limit → expect 429
* test_get_employees_no_auth    – no X-API-Key → expect 401
"""

# ── 1) Environment: tiny rate-limit so we hit it fast ────────────────────────
import os, tempfile, pathlib, pytest
os.environ["EMPLOYEE_API_KEY"]     = "negtestkey" # gave wrong key
os.environ["EMPLOYEE_RATE_LIMIT"]  = "3"     # only 3 requests allowed
os.environ["EMPLOYEE_RATE_PERIOD"] = "60"

# ── 2) Import the app & utilities ────────────────────────────────────────────
import main_auth
from fastapi.testclient import TestClient

# ── 3) Shared TestClient and fresh temp DB for this file ---------------------
@pytest.fixture(scope="session")
def client():
    tmp_db = pathlib.Path(tempfile.gettempdir()) / "employees_failure.db"
    if tmp_db.exists():
        tmp_db.unlink()
    main_auth.DATABASE = str(tmp_db)
    main_auth.init_db()

    with TestClient(main_auth.app) as c:
        yield c

    tmp_db.unlink(missing_ok=True)


API_HEADERS = {"X-API-Key": os.environ["EMPLOYEE_API_KEY"]}

# Make sure each test has its own clean rate-limit log
@pytest.fixture(autouse=True)
def _reset_rate_limit():
    main_auth._request_log.clear()


# ── 4) Failing scenarios ─────────────────────────────────────────────────────
def test_rate_limit_triggers_429(client):
    """Fourth request within the window should be rejected."""
    # First three succeed
    for _ in range(3):
        assert client.get("/employees", headers=API_HEADERS).status_code == 200
    # Fourth exceeds limit
    r = client.get("/employees", headers=API_HEADERS)
    assert r.status_code == 429
    assert r.json()["detail"] == "Too Many Requests"


def test_get_employees_no_auth(client):
    """Missing X-API-Key header results in 401."""
    r = client.get("/employees")          # no headers
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid or missing API Key"
