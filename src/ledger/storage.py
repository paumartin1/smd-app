"""Reading and writing transactions: the CSV file and the database."""

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ledger.db import Account, TransactionRow
from ledger.models import Transaction


def read_csv(path: Path) -> list[Transaction]:
    """Reads a CSV file with the columns of a `Transaction`, one row per transaction."""
    with open(path, newline="") as f:
        return [
            Transaction(
                date=date.fromisoformat(row["date"]),
                account=row["account"],
                description=row["description"],
                category=row["category"],
                amount=Decimal(row["amount"]),
            )
            for row in csv.DictReader(f)
        ]


def find_account(session: Session, name: str) -> Account | None:
    """The account with this name, or None if there is none."""
    return session.scalars(select(Account).where(Account.name == name)).first()


def get_or_create_account(session: Session, name: str) -> Account:
    account = find_account(session, name)
    if account is None:
        account = Account(name=name)
        session.add(account)
    return account


def import_csv(session: Session, path: Path) -> int:
    """Adds the transactions of a CSV file to the database. Returns how many."""
    transactions = read_csv(path)
    for t in transactions:
        session.add(
            TransactionRow(
                date=t.date,
                account=get_or_create_account(session, t.account),
                description=t.description,
                category=t.category,
                amount=t.amount,
            )
        )
    session.commit()
    return len(transactions)


def to_transaction(row: TransactionRow) -> Transaction:
    """The Transaction stored in one row of the table `transactions`."""
    return Transaction(
        date=row.date,
        account=row.account.name,
        description=row.description,
        category=row.category,
        amount=row.amount,
        id=row.id,
    )


def load_transactions(
    session: Session, account: str | None = None, category: str | None = None
) -> list[Transaction]:
    """The transactions in the database, oldest first, of one account or category
    if they are given."""
    query = select(TransactionRow).order_by(TransactionRow.date, TransactionRow.id)
    if account is not None:
        query = query.join(Account).where(Account.name == account)
    if category is not None:
        query = query.where(TransactionRow.category == category)
    return [to_transaction(row) for row in session.scalars(query)]


def get_transaction(session: Session, transaction_id: int) -> Transaction | None:
    """The transaction with this id, or None if there is none."""
    row = session.get(TransactionRow, transaction_id)
    if row is None:
        return None
    return to_transaction(row)


def add_transaction(
    session: Session,
    account_name: str,
    amount: Decimal,
    category: str,
    description: str,
    day: date,
) -> Transaction:
    """Records one transaction in an existing account, and returns it with its id."""
    account = find_account(session, account_name)
    if account is None:
        raise ValueError(f"there is no account called {account_name!r}")
    if amount != round(amount, 2):
        raise ValueError(f"{amount} has more than two decimals")
    row = TransactionRow(
        date=day,
        account=account,
        description=description,
        category=category,
        amount=amount,
    )
    session.add(row)
    session.commit()
    return to_transaction(row)


def delete_transaction(session: Session, transaction_id: int) -> bool:
    """Deletes the transaction with this id. Returns False if there is none."""
    row = session.get(TransactionRow, transaction_id)
    if row is None:
        return False
    session.delete(row)
    session.commit()
    return True
