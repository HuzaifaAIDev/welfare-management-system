# CHANGELOG

All notable changes made while refactoring the original `Welfare_Project`
into the production-quality `welfare-management-system` project.

## [2.0.0] — Full Refactor

### 🏗️ Project Structure
- Converted the flat single-folder layout (`Welfare_Project/*.py`) into a
  professional `app/` package with clear layers:
  `api/`, `core/`, `database/`, `models/`, `schemas/`, `services/`, `utils/`,
  `templates/`, `static/`.
- Split each `route_*.py` into `app/api/*.py` (HTTP layer only).
- Split each `model_*.py` into `app/models/*.py` (ORM only — business logic
  extracted into services).
- Split each `schema_*.py` into `app/schemas/*.py`.
- Renamed `email_controll.py` → `app/services/email_service.py`.
- Extracted inventory business logic (`add_stock`, `remove_stock`,
  `get_or_create`, `snapshot`, `classify_food`) out of `model_inventory.py`
  into `app/services/inventory_service.py`; the model file now contains only
  the `Inventory` ORM class and category constants.
- Extracted admin-bootstrap logic out of `route_admin.py` into
  `app/services/admin_service.py`.
- Added `app/api/deps.py` for shared FastAPI dependencies
  (`get_current_user`, `require_role`), removing duplication across routers.
- Added `app/utils/identifiers.py` for the `DON-0001` / `NEE-0001`-style ID
  formatting that was previously duplicated as inline f-strings in 5+ places.
- Added a `tests/` package with pytest smoke tests and CI-friendly fixtures.

### 🔐 Security
- **Removed all hardcoded secrets.** `SECRET_KEY` (JWT signing key),
  `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and SMTP credentials are no longer
  hardcoded anywhere in source — they are loaded exclusively from
  environment variables via `app/core/config.py` (pydantic-settings) and
  documented in `.env.example`.
- **Removed the hardcoded admin email/password** (`admin@welfare.bahadurabad`
  / `123admin123`) that lived in `route_admin.py`. The admin account is now
  bootstrapped once from `ADMIN_EMAIL` / `ADMIN_PASSWORD` env vars and its
  password is stored as a bcrypt hash, exactly like any other user.
- **`/admin/login` now verifies the bcrypt hash** stored in the database
  instead of comparing the submitted password to a plain-text constant.
- **Removed the `password_plain` column** from the `User` model. The
  original app stored every user's password in plain text so "forgot
  password" could email it back — this is a serious security anti-pattern.
  The forgot-password flow now generates a strong random temporary
  password, stores only its bcrypt hash, and emails the temporary password
  to the user (who is expected to log in and, going forward, change it).
  No plain-text password is ever persisted.
- **Removed the hardcoded Gmail sender address and the `app_password.txt`
  file mechanism** from the email module. SMTP host/port/sender/password
  are now configured entirely via environment variables
  (`SMTP_HOST`, `SMTP_PORT`, `SMTP_SENDER_EMAIL`, `SMTP_PASSWORD`).
- Replaced the dynamic `getattr(__import__(mod), cls)` pattern in
  `reject_request` (a code-smell / minor injection-adjacent pattern) with an
  explicit, statically-imported model map.
- JWT token creation now uses timezone-aware UTC timestamps
  (`datetime.now(timezone.utc)`) instead of naive `datetime.utcnow()`.

### 🐛 Bug Fixes
- Fixed a variable-shadowing bug present in every `update_*_status` route
  (`route_donor.py`, `route_food.py`, `route_fund.py`): the query parameter
  was named `status`, which shadowed the imported `fastapi.status` module
  inside the same function, making `status.HTTP_404_NOT_FOUND` reference the
  parameter instead of the module (a latent `AttributeError` waiting to
  happen). The parameter is now `new_status` with a `status` query alias, so
  the public API contract (`?status=...`) is unchanged.
- `get_all_donations` / `get_all_requests` previously used
  `getattr(d, 'is_fulfilled', False)` on `BloodDonation` / `BloodRequest`
  models that never defined an `is_fulfilled` column — this always silently
  evaluated to `False`. Replaced with a correct, explicit
  `status in (...)` check.
- Removed a dead/no-op existence check in `add_fund_donation`
  (`existing = ... if hasattr(FundDonation, 'status') else None`, whose
  result was never used).

### 🧹 Code Quality / Cleanup
- Removed unused imports (e.g. `Optional` in the admin schema, duplicate
  `BloodGroup`/`StatusEnum` boilerplate consolidated per-module).
- Added type hints to all route handlers, service functions, and schemas.
- Added docstrings and section comments throughout.
- Replaced deprecated Pydantic v1-style `@validator` with Pydantic v2
  `@field_validator`, and `class Config: from_attributes = True` with
  `model_config = ConfigDict(from_attributes=True)`.
- Replaced the deprecated SQLAlchemy `declarative_base()` factory with the
  modern `class Base(DeclarativeBase)` pattern (SQLAlchemy 2.0 style).
- Added structured logging (`app/core/logging_config.py`) replacing scattered
  `print()` statements in `email_controll.py` / `main.py`.
- Consistent naming: `route_donor.py` → `app/api/donor.py`, local variable
  names disambiguated (e.g. `req` → `blood_request`/`food_request`/
  `fund_request`) to avoid confusion with the `Request` concept.
- Converted the app-startup admin bootstrap + table creation from the
  deprecated `@app.on_event("startup")` decorator to FastAPI's recommended
  `lifespan` context manager.

### 📦 Dependencies
- Pinned `bcrypt==4.0.1` (down from the project's implicit resolution of
  bcrypt 4.1.x) to avoid the well-known `passlib==1.7.4` +
  `bcrypt>=4.1` incompatibility (`AttributeError: module 'bcrypt' has no
  attribute '__about__'`).
- Added `pydantic-settings` for environment-driven configuration.
- Added `email-validator` (required by Pydantic's `EmailStr`).
- Added `requirements-dev.txt` with `pytest`, `httpx`, and `ruff` for local
  development / CI.

### 🚀 New / Added
- `.env.example` — full list of supported environment variables with
  descriptions.
- `Dockerfile` — multi-stage-ready, non-root user, healthcheck.
- `docker-compose.yml` — single-service compose file with a persisted
  SQLite volume.
- `.github/workflows/ci.yml` — GitHub Actions pipeline that lints (`ruff`),
  runs the test suite (`pytest`), and verifies the app imports cleanly.
- `README.md`, `LICENSE` (MIT), this `CHANGELOG.md`.
- `pyproject.toml` with `ruff` configuration.
- `tests/` — smoke tests covering health check, registration, login,
  password-strength validation, and admin login/auth.
- `/health` endpoint now also reports the app version.

### ✅ Preserved Functionality
Every existing feature from the original project continues to work,
unchanged from the frontend's perspective (all route prefixes, request/
response shapes, and status codes were kept identical unless explicitly
called out above):
- User registration/login/profile (`/auth/*`)
- Admin login & bootstrap (`/admin/login`)
- Blood donation & requests (`/blood/*`)
- Fund donation & requests (`/fund/*`)
- Food/rashan donation & requests (`/food/*`)
- Problem/counseling submissions (`/problem/*`)
- Admin announcements, unified search, inventory, and fulfillment/rejection
  workflows (`/admin/*`)
- Forgot-password email notifications (now via a secure temporary-password
  flow instead of storing plain-text passwords)
- The existing HTML/JS frontend (`templates/index.html`) is served as-is
  and requires **no changes**, since all API paths and payloads are
  unchanged.
