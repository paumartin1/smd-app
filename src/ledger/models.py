"""The data: what a transaction is."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Transaction:
    """One movement of money in one account. Negative amounts are money going out.

    `id` is the number the database gave it, or None if it is not stored yet.
    """

    date: date
    account: str
    description: str
    category: str
    amount: Decimal
    id: int | None = None
