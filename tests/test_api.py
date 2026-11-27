"""Tests of the web API, through HTTP requests, on a database in memory."""

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from ledger import api, storage
from ledger.db import Account

LUNCH = {
    "date": "2026-03-31",
    "account": "checking",
    "description": "Lunch with a client",
    "category": "restaurants",
    "amount": "-12.50",
}


@pytest.fixture
def client(session):
    """A client of the API, on the database of the fixture session, with two
    accounts and one transaction in each."""
    session.add_all([Account(name="checking"), Account(name="savings")])
    session.commit()
    day = date(2026, 1, 10)
    storage.add_transaction(session, "checking", Decimal("-39.90"), "sport", "Gym", day)
    storage.add_transaction(session, "savings", Decimal("1.60"), "interest", "Pay", day)

    api.app.dependency_overrides[api.get_session] = lambda: session
    yield TestClient(api.app)
    api.app.dependency_overrides.clear()


def test_list_accounts(client):
    response = client.get("/api/accounts")

    assert response.status_code == 200
    assert response.json() == [
        {"name": "checking", "balance": "-39.90"},
        {"name": "savings", "balance": "1.60"},
    ]


def test_get_a_transaction(client):
    response = client.get("/api/transactions/1")

    assert response.status_code == 200
    assert response.json()["description"] == "Gym"
    assert response.json()["amount"] == "-39.90"


def test_a_missing_transaction_is_404(client):
    response = client.get("/api/transactions/999")

    assert response.status_code == 404


def test_filter_by_category(client):
    response = client.get("/api/transactions", params={"category": "interest"})

    assert response.status_code == 200
    assert [t["id"] for t in response.json()] == [2]


def test_create_a_transaction(client):
    response = client.post("/api/transactions", json=LUNCH)

    assert response.status_code == 201
    assert response.json() == LUNCH | {"id": 3}


def test_an_unknown_account_is_400(client):
    response = client.post("/api/transactions", json=LUNCH | {"account": "credit"})

    assert response.status_code == 400
    assert response.json() == {"detail": "there is no account called 'credit'"}


def test_a_date_that_is_not_a_date_is_422(client):
    response = client.post("/api/transactions", json=LUNCH | {"date": "31/03/2026"})

    assert response.status_code == 422


def test_delete_a_transaction(client):
    response = client.delete("/api/transactions/1")

    assert response.status_code == 204

    response = client.get("/api/transactions/1")
    assert response.status_code == 404
