# Rent Ledger App (Flask + Postgres + Docker + Render Blueprint)

Simple personal rent ledger app to track lease details, scheduled rent due, payments, and running balance.

## Stack
- Flask + SQLAlchemy + Flask-Migrate
- Postgres (Docker locally, Render Postgres in production)
- Docker / Docker Compose for local dev
- Render Blueprint (`render.yaml`) for deployment

## Local setup (Docker)
```bash
cp .env.example .env
docker compose up --build
# in a second terminal (first time only)
docker compose exec web flask db upgrade
```
Open http://localhost:5002

## Render deploy (Blueprint)
1. Push to GitHub.
2. Render → New + → Blueprint → connect repo.
3. After deploy, open shell and run:
```bash
flask db upgrade
```

## Notes
- Starter app is single-user and has no login.
- Add auth before broad/public use.
