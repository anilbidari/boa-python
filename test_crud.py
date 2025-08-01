# tests/test_crud.py

import pytest  # for parametrize and marks

def test_read_employees_initial(client):
    # Call GET /employees
    resp = client.get("/employees", headers={"X-API-Key": "mysecretapikey"})
    # Expect HTTP 200 OK
    assert resp.status_code == 200
    data = resp.json()            # parse JSON body
    # We seeded 10 employees, so we should get 10 back
    assert isinstance(data, list)  
    assert len(data) == 10        

@pytest.mark.parametrize("new_emp", [
    {"name": "Test A", "country": "Nowhere",   "salary": 123.0},
    {"name": "Test B", "country": "Somewhere", "salary": 456.0},
])
def test_create_and_read(client, new_emp):
    # CREATE: POST /employees
    resp = client.post(
        "/employees", 
        json=new_emp, 
        headers={"X-API-Key": "mysecretapikey"}
    )
    assert resp.status_code == 201         # should be "Created"
    body = resp.json()                     # response JSON
    assert body["name"] == new_emp["name"] # verify name matches
    emp_id = body["id"]                    # grab new record’s ID

    # READ: GET /employees/{id}
    resp2 = client.get(f"/employees/{emp_id}",
                       headers={"X-API-Key": "mysecretapikey"})
    assert resp2.status_code == 200
    # the `country` should match what we just created
    assert resp2.json()["country"] == new_emp["country"]

def test_update_and_delete(client):
    # First, CREATE a fresh employee
    payload = {"name": "Upd", "country": "X", "salary": 1.1}
    r = client.post("/employees", json=payload,
                    headers={"X-API-Key": "mysecretapikey"})
    emp_id = r.json()["id"]

    # UPDATE: PUT /employees/{id}
    updated = {"name": "Upd2", "country": "Y", "salary": 2.2}
    ru = client.put(f"/employees/{emp_id}", json=updated,
                    headers={"X-API-Key": "mysecretapikey"})
    assert ru.status_code == 200           # OK
    assert ru.json()["salary"] == 2.2      # confirm salary changed

    # DELETE: DELETE /employees/{id}
    rd = client.delete(f"/employees/{emp_id}",
                       headers={"X-API-Key": "mysecretapikey"})
    assert rd.status_code == 204           # No Content

    # Finally, GET again should 404
    rg = client.get(f"/employees/{emp_id}",
                    headers={"X-API-Key": "mysecretapikey"})
    assert rg.status_code == 404           # Not Found
assert: simple yes/no check
@pytest.mark.parametrize: run one test with different inputs
