# Expense Tracker — Interactive Portfolio Demo

[Try the live demo](https://expense-tracker-portfolio-demo.vercel.app) · [My portfolio](https://github.com/jesusprz2492)

An English/Spanish expense management app built with Python, FastAPI, Jinja2, and JavaScript. This showcase demonstrates an Excel-to-web migration using entirely fictional data.

## Explore

- Dashboard: income, spending, budgets, and balance.
- Create, edit, and delete temporary transactions; adjust monthly budgets.
- Browse six months of transactions and reports.
- English by default, with an EN/ES switch at the top.
- No sign-in or password required.

Each browser tab has its own temporary changes. Changes reset on reload, leaving/closing the page, or after 60 minutes. Catalogs are viewable but cannot be edited.

## Architecture and scope

FastAPI renders Jinja2 templates from generated fixtures: 72 transactions across six months, categories, accounts, payment methods, and contacts. JavaScript keeps visitor operations in memory. A stateless render endpoint validates those operations and rebuilds the response without persistence.

The original private application uses PostgreSQL and an idempotent Excel importer. This repository contains only the isolated demo: no original workbooks, production database connection, credentials, or real financial records. The importer and database implementation are not included.

## Run locally

Requires Python 3.10 or newer. No environment variables or database are needed.

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8765
```

Open http://127.0.0.1:8765.

## Verify

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests
node tests/test_demo_lifecycle.cjs
```

Tests cover rendered routes, months, EN/ES output, totals, input validation, blocked persistence routes, and isolated changes. The JavaScript lifecycle check uses a simulated clock to verify the hourly reset and page lifecycle behavior.

## Deployment

The included Vercel configuration targets FastAPI. Deploy to a separate project with no production database configuration.

## Author

Jesus Perez — full-stack development, Python automation, and applied AI systems. [LinkedIn](https://www.linkedin.com/in/jesus-perez-22a09b103/)
