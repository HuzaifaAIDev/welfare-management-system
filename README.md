# Welfare Management System

A FastAPI-based platform that connects donors with people in need — blood
donations, cash/fund donations, food (rashan) donations, and a counseling
/ problem-reporting channel — with an admin dashboard for managing
inventory, requests, and announcements.

## Features

- **Authentication** — JWT-based auth for regular users (donor / needy) and
  a separately-bootstrapped admin account, with bcrypt password hashing.
- **Blood donation & requests** — donors offer blood, needy users request it;
  admin fulfills requests against tracked inventory.
- **Fund donations & requests** — cash donations and requests with admin
  approval workflow.
- **Food (rashan) donations & requests** — itemized by kg (rice, flour, oil,
  sugar, pulses), with inventory tracking and partial fulfillment.
- **Problem / counseling submissions** — users submit issues; admin responds.
- **Admin dashboard APIs** — unified search, inventory snapshot, announcements,
  and fulfillment/rejection endpoints.
- **Email notifications** — password-reset emails sent via SMTP.

## Tech Stack

- **FastAPI** + **Uvicorn**
- **SQLAlchemy 2.0** (SQLite by default; swappable to PostgreSQL)
- **Pydantic v2** + **pydantic-settings**
- **passlib[bcrypt]** for password hashing
- **python-jose** for JWT
- Vanilla HTML/JS frontend (served from `app/templates/index.html`)

## Project Structure

```
app/
├── main.py                # FastAPI app factory & startup
├── core/
│   ├── config.py          # Environment-driven settings
│   ├── security.py        # Password hashing & JWT helpers
│   └── logging_config.py  # Logging setup
├── database/
│   └── session.py         # Engine, session factory, Base
├── models/                # SQLAlchemy ORM models
├── schemas/                # Pydantic request/response schemas
├── services/               # Business logic (email, inventory, admin bootstrap)
├── api/                    # FastAPI routers (auth, donor, food, fund, problem, admin)
├── utils/                  # Small shared helpers
├── templates/index.html    # Frontend (served at "/")
└── static/                 # Static assets (if any)
tests/                       # Pytest test suite
```

## Getting Started

### 1. Clone & set up a virtual environment

```bash
git clone <your-repo-url>
cd welfare-management-system
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set, at minimum:

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | Random secret used to sign JWTs. Generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ADMIN_EMAIL` | ✅ | Email for the auto-bootstrapped admin account |
| `ADMIN_PASSWORD` | ✅ | Password for the auto-bootstrapped admin account |
| `DATABASE_URL` | – | Defaults to local SQLite; set to a PostgreSQL URL in production |
| `CORS_ORIGINS` | – | Comma-separated allowed origins, or `*` |
| `SMTP_SENDER_EMAIL` / `SMTP_PASSWORD` | – | Required only for the "forgot password" email feature (Gmail App Password recommended) |

See `.env.example` for the full list.

### 4. Run the app

```bash
uvicorn app.main:app --reload
```

The API and frontend will be available at `http://localhost:8000`.
Interactive API docs: `http://localhost:8000/docs`.

On first startup, the app automatically creates the admin account (if it
doesn't already exist) using `ADMIN_EMAIL` / `ADMIN_PASSWORD` from your
environment — the password is stored as a bcrypt hash, never in plain text.

### 5. Run tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Docker

```bash
cp .env.example .env   # fill in real values first
docker compose up --build
```

This builds the image, runs migrations implicitly via `create_tables()` on
startup, and persists the SQLite database in a named volume.

## API Overview

| Prefix | Purpose |
|---|---|
| `/auth` | Register, login, current user, forgot password |
| `/blood` | Blood donations & requests |
| `/fund` | Fund donations & requests |
| `/food` | Rashan donations & requests |
| `/problem` | Counseling / problem submissions |
| `/admin` | Admin login, announcements, search, inventory, fulfillment |

Full interactive documentation is available at `/docs` (Swagger UI) and
`/redoc` once the app is running.

## Security Notes

- Passwords are **always** hashed with bcrypt (via passlib) — never stored
  or compared in plain text.
- The admin account is bootstrapped from environment variables, not
  hardcoded in source.
- JWT signing key, SMTP credentials, and all other secrets are loaded
  exclusively from environment variables (`.env`, which is git-ignored).
- "Forgot password" issues a freshly generated temporary password and
  emails it to the user — the plain-text password is never persisted.

## License

MIT — see [LICENSE](LICENSE).
