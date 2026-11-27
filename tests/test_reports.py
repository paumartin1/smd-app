"""Tests of the calculations: transactions in, totals out."""

from datetime import date
from decimal import Decimal

import pytest

from ledger import reports
from ledger.models import Transaction


def make(day: str, account: str, category: str, amount: str) -> Transaction:
    """A transaction with the fields the reports use."""
    return Transaction(
        date=date.fromisoformat(day),
        account=account,
        description="test",
        category=category,
        amount=Decimal(amount),
    )


@pytest.fixture
def transactions() -> list[Transaction]:
    """Two months of a small ledger, with a transfer between the two accounts."""
    return [
        make("2026-01-01", "checking", "salary", "2000.00"),
        make("2026-01-02", "checking", "groceries", "-65.15"),
        make("2026-01-15", "checking", "transfer", "-300.00"),
        make("2026-01-15", "savings", "transfer", "300.00"),
        make("2026-02-03", "checking", "groceries", "-40.00"),
        make("2026-02-10", "checking", "restaurants", "-25.50"),
    ]


def test_balances(transactions):
    result = reports.balances(transactions)

    assert result == {"checking": Decimal("1569.35"), "savings": Decimal("300.00")}


def test_balances_of_no_transactions():
    assert reports.balances([]) == {}


def test_a_transfer_is_not_spending():
    transfer = make("2026-01-15", "checking", "transfer", "-300.00")

    assert not reports.is_spending(transfer)


def test_spending_by_category(transactions):
    result = reports.spending_by_category(transactions)

    assert result == {
        "groceries": Decimal("105.15"),
        "restaurants": Decimal("25.50"),
    }
    assert list(result) == ["groceries", "restaurants"]


def test_net_by_month(transactions):
    result = reports.net_by_month(transactions)

    assert result == {"2026-01": Decimal("1934.85"), "2026-02": Decimal("-65.50")}
