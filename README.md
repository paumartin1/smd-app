# smd-app

Personal finance ledger for the command line: balances, spending and monthly reports using a SQLite database.

## Run it

Import transactions from the CSV file:

```
uv run ledger import
```

View the reports:

```
uv run ledger balance
uv run ledger spending
uv run ledger months
```

Add a transaction:

```
uv run ledger add checking -12.50 restaurants "Lunch with a client" --date 2026-03-31
```

## Roadmap

- Monthly report of income and spending (completed)
- A database instead of a CSV file (completed)
- A web API and a dashboard

## Author

paumartin1
