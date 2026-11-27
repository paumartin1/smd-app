"""Tests of storage, on a database in memory."""

from datetime import date
from decimal import Decimal

import pytest

from ledger import storage
from ledger.db import Account

DAY = date(2026, 3, 31)


@pytest.fixture
def db(session):
    """The empty database of the fixture session, plus one account, checking."""
    session.add(Account(name="checking"))
    session.commit()
    return session


def test_add_and_load_a_transaction(db):
    storage.add_transaction(db, "checking", Decimal("-12.50"), "food", "Lunch", DAY)

    [loaded] = storage.load_transactions(db)

    assert loaded.date == DAY
    assert loaded.account == "checking"
    assert loaded.category == "food"
    assert loaded.amount == Decimal("-12.50")


def test_import_csv(session, tmp_path):
    csv_file = tmp_path / "transactions.csv"
    csv_file.write_text(
        "date,account,description,category,amount\n"
        "2026-01-01,checking,Salary,salary,2000.00\n"
        "2026-01-02,checking,Carrefour,groceries,-65.15\n"
        "2026-01-15,savings,Transfer from checking,transfer,300.00\n"
    )

    count = storage.import_csv(session, csv_file)

    assert count == 3
    amounts = [t.amount for t in storage.load_transactions(session)]
    assert amounts == [Decimal("2000.00"), Decimal("-65.15"), Decimal("300.00")]


def test_an_unknown_account_is_refused(db):
    with pytest.raises(ValueError, match="no account called 'credit'"):
        storage.add_transaction(db, "credit", Decimal("-5"), "food", "Coffee", DAY)

    assert storage.load_transactions(db) == []


def test_a_fraction_of_a_cent_is_refused(db):
    with pytest.raises(ValueError, match="has more than two decimals"):
        storage.add_transaction(
            db, "checking", Decimal("-1.005"), "food", "Coffee", DAY
        )

    assert storage.load_transactions(db) == []
