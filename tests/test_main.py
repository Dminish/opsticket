"""
Basic smoke tests. Run against a live Neo4j instance (docker compose up first) and a real
OpenAI API key (OPENAI_API_KEY set) since this scaffold intentionally doesn't mock its
dependencies, being able to say "I have working tests against the real dependencies, not
just mocks" is a reasonable interview talking point too.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_read_ticket():
    create_response = client.post(
        "/tickets",
        json={
            "subject": "Printer offline",
            "description": "Office printer shows offline, can't print from any laptop",
        },
    )
    assert create_response.status_code == 201
    ticket = create_response.json()
    assert ticket["category"] == "hardware"
    assert ticket["resolver"] == "hardware-team"

    read_response = client.get(f"/tickets/{ticket['id']}")
    assert read_response.status_code == 200
    assert read_response.json()["subject"] == "Printer offline"


def test_ticket_not_found():
    response = client.get("/tickets/999999")
    assert response.status_code == 404
