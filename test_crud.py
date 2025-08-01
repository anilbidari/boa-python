import requests
from pprint import pprint

BASE = "http://127.0.0.1:8000"
HEAD = {"X-API-Key": "mysecretapikey"}

# Create
r = requests.post(f"{BASE}/employees", headers=HEAD, json={
    "name": "Zara Patel",
    "country": "India",
    "salary": 65000
})
emp = r.json(); pprint.pp(emp)

emp_id = emp["id"]

# Read
pprint(requests.get(f"{BASE}/employees/{emp_id}", headers=HEAD).json())

# Update
requests.put(f"{BASE}/employees/{emp_id}", headers=HEAD, json={
    "name": "Z. Patel",
    "country": "India",
    "salary": 70000
})

# Delete
requests.delete(f"{BASE}/employees/{emp_id}", headers=HEAD)
