import requests
import json

BASE_URL = "http://localhost:5000"

def print_response(label, response):
    print(f"\n=== {label} ===")
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print(response.text)
    print()

def test_health():
    print("Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print_response("Health", response)

def test_schedule_no_conflict():
    """Test /schedule with a slot available (no conflict)"""
    data = {
        "Request_id": "test-noconflict-1",
        "Datetime": "2025-07-13T10:00:00",
        "Location": "Test Room",
        "From": "alice@example.com",
        "Attendees": [
            {"email": "bob@example.com"},
            {"email": "charlie@example.com"}
        ],
        "Subject": "No Conflict Meeting",
        "EmailContent": "Let's meet for a test meeting."
    }
    response = requests.post(f"{BASE_URL}/schedule", json=data)
    print_response("/schedule No Conflict", response)

def test_schedule_conflict():
    """Test /schedule with no slot available (conflict, triggers LLM)"""
    # All attendees are busy at the same time
    data = {
        "Request_id": "test-conflict-1",
        "Datetime": "2025-07-13T09:00:00",
        "Location": "Test Room",
        "From": "alice@example.com",
        "Attendees": [
            {"email": "bob@example.com"},
            {"email": "charlie@example.com"}
        ],
        "Subject": "Conflict Meeting",
        "EmailContent": "Let's meet when everyone is busy."
    }
    response = requests.post(f"{BASE_URL}/schedule", json=data)
    print_response("/schedule Conflict", response)

def test_available_slots():
    print("Testing /available-slots endpoint...")
    data = {
        "attendees": ["alice@example.com", "bob@example.com", "charlie@example.com"],
        "duration": 60
    }
    response = requests.post(f"{BASE_URL}/available-slots", json=data)
    print_response("/available-slots", response)

def test_calendar():
    print("Testing /calendar/alice@example.com endpoint...")
    response = requests.get(f"{BASE_URL}/calendar/alice@example.com")
    print_response("/calendar/alice@example.com", response)

if __name__ == "__main__":
    print("=== AMD AI Sprint - API Testing ===\n")
    test_health()
    test_schedule_no_conflict()
    test_schedule_conflict()
    test_available_slots()
    test_calendar()
    print("=== Testing Complete ===") 