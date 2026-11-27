"""The web API: reads HTTP requests, calls storage and reports, returns JSON."""

import datetime
from collections.abc import Iterator
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ledger import db, reports, storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.create_tables()
    yield


app = FastAPI(title="ledger", lifespan=lifespan)


def get_session() -> Iterator[Session]:
    """One database session per request, closed when the response is sent."""
    with db.get_session() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


class NewTransaction(BaseModel):
    """What the client sends to record a transaction."""

    date: datetime.date
    account: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=50)
    amount: Decimal


class TransactionOut(NewTransaction):
    """What the API returns: a stored transaction, with its id."""

    id: int


class AccountOut(BaseModel):
    name: str
    balance: Decimal


@app.get("/api/accounts")
def list_accounts(session: SessionDep) -> list[AccountOut]:
    balances = reports.balances(storage.load_transactions(session))
    return [AccountOut(name=name, balance=total) for name, total in balances.items()]


@app.get("/api/transactions")
def list_transactions(
    session: SessionDep, account: str | None = None, category: str | None = None
) -> list[TransactionOut]:
    return storage.load_transactions(session, account=account, category=category)


@app.get("/api/transactions/{transaction_id}")
def get_transaction(transaction_id: int, session: SessionDep) -> TransactionOut:
    transaction = storage.get_transaction(session, transaction_id)
    if transaction is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"there is no transaction {transaction_id}"
        )
    return transaction


@app.post("/api/transactions", status_code=status.HTTP_201_CREATED)
def create_transaction(new: NewTransaction, session: SessionDep) -> TransactionOut:
    try:
        return storage.add_transaction(
            session, new.account, new.amount, new.category, new.description, new.date
        )
    except ValueError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from None


@app.delete(
    "/api/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_transaction(transaction_id: int, session: SessionDep) -> None:
    if not storage.delete_transaction(session, transaction_id):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"there is no transaction {transaction_id}"
        )


@app.get("/api/reports/spending")
def spending(session: SessionDep) -> dict[str, Decimal]:
    return reports.spending_by_category(storage.load_transactions(session))


@app.get("/api/reports/months")
def months(session: SessionDep) -> dict[str, Decimal]:
    return reports.net_by_month(storage.load_transactions(session))
