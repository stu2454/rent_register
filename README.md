# Rent Ledger App (Flask + Postgres + Docker + Render Blueprint)

Simple personal rent ledger app to track lease details, scheduled rent due, payments, and running balance.

## Stack
- Flask + SQLAlchemy + Flask-Migrate + Flask-Login
- Postgres (Docker locally, Render Postgres in production)
- Docker / Docker Compose for local dev
- Render Blueprint (`render.yaml`) for deployment

## Local setup (Docker)
```bash
cp .env.example .env
# Add ADMIN_USERNAME and ADMIN_PASSWORD to .env
docker compose up --build
```
Open http://localhost:5002 — migrations and admin user creation run automatically on startup.

## Render deploy (Blueprint)
1. Push to GitHub.
2. Render → New + → Blueprint → connect repo.
3. When prompted, set `ADMIN_USERNAME` and `ADMIN_PASSWORD` — these become your login credentials.

Migrations run automatically on startup. The admin user is created on first boot if it doesn't exist yet.

## Adding more users
```bash
# Local
docker compose exec web flask create-user <username> <password>

# Render — set ADMIN_USERNAME/ADMIN_PASSWORD for the first user;
# additional users require shell access or a future admin UI.
```

## Notes
- No public registration — users must be created via CLI.
- Add HTTPS (Render provides it automatically) before sharing publicly.
