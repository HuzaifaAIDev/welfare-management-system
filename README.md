# Welfare Management System

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED)
![License](https://img.shields.io/badge/License-MIT-yellow)

A **FastAPI-based Welfare Management System** designed to connect donors with people in need through a centralized platform. The system supports **blood donations**, **financial aid**, **food (rashan) donations**, and **counseling/problem reporting**, while providing administrators with powerful tools for managing requests, inventory, and announcements.

---

## Features

### Authentication & Security
- JWT-based authentication
- Separate admin authentication flow
- Password hashing using bcrypt
- Password complexity validation
- Forgot password functionality with email notifications
- Environment-based secret management

### Blood Donation Management
- Blood donation registration
- Blood request submission
- Blood inventory tracking
- Admin approval and fulfillment workflow

### Fund Donation Management
- Monetary donation submission
- Financial assistance requests
- Approval/rejection workflow
- Fund allocation tracking

### Food (Rashan) Management
- Food donation registration
- Food request submission
- Inventory management
- Partial and complete request fulfillment
- Category-wise stock tracking

### Problem/Counseling System
- Submit personal or social problems
- Admin counseling responses
- Status tracking

### Admin Dashboard APIs
- Unified search
- Inventory overview
- Request management
- Announcement management
- Approval/rejection operations
- Statistics and monitoring

### Additional Features
- Email notifications
- Docker support
- Environment-based configuration
- Automated admin account bootstrap
- API documentation with Swagger UI and ReDoc

---

## Tech Stack

| Category | Technology |
|----------|------------|
| Backend | FastAPI |
| Server | Uvicorn |
| Database ORM | SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| Authentication | JWT (python-jose) |
| Password Hashing | passlib + bcrypt |
| Configuration | pydantic-settings |
| Testing | Pytest |
| Containerization | Docker & Docker Compose |
| Frontend | HTML, CSS, JavaScript |

---

## Project Structure

```text
welfare-management-system/
│
├── app/
│   ├── api/                    # API routes/endpoints
│   │   ├── auth.py
│   │   ├── donor.py
│   │   ├── food.py
│   │   ├── fund.py
│   │   ├── problem.py
│   │   └── admin.py
│   │
│   ├── core/                   # Configuration & security
│   │   ├── config.py
│   │   ├── security.py
│   │   └── logging_config.py
│   │
│   ├── database/               # Database configuration
│   │   └── session.py
│   │
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic
│   ├── templates/              # Frontend templates
│   ├── static/                 # Static files
│   ├── utils/                  # Utility functions
│   └── main.py                 # Application entry point
│
├── tests/                      # Test suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── README.md
└── .env.example
```

---

## System Architecture

```text
Frontend (HTML/JS)
        │
        ▼
    FastAPI API
        │
        ▼
 Business Logic
    (Services)
        │
        ▼
 SQLAlchemy ORM
        │
        ▼
    Database
(SQLite/PostgreSQL)
```

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/HuzaifaAIDev/welfare-management-system.git
cd welfare-management-system
```

### 2. Create Virtual Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux/macOS

```bash
python -m venv venv
source venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

Create your environment file:

```bash
cp .env.example .env
```

Configure the following variables:

| Variable | Required | Description |
|----------|----------|-------------|
| SECRET_KEY | ✅ | Secret key used for JWT generation |
| ADMIN_EMAIL | ✅ | Initial admin account email |
| ADMIN_PASSWORD | ✅ | Initial admin account password |
| DATABASE_URL | ❌ | Database connection URL |
| CORS_ORIGINS | ❌ | Allowed origins |
| SMTP_SENDER_EMAIL | ❌ | Email sender account |
| SMTP_PASSWORD | ❌ | Email app password |

Example:

```env
SECRET_KEY=your-secret-key
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your-password
DATABASE_URL=sqlite:///./welfare.db
```

---

## Running the Application

Start the development server:

```bash
uvicorn app.main:app --reload
```

Application URLs:

| Service | URL |
|---------|-----|
| Home | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

---

## Docker Setup

Build and run with Docker Compose:

```bash
cp .env.example .env
docker compose up --build
```

Stop containers:

```bash
docker compose down
```

---

## Running Tests

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest
```

Run tests with verbose output:

```bash
pytest -v
```

---

## API Modules

| Module | Description |
|---------|-------------|
| `/auth` | Authentication and user management |
| `/donor` | Blood donation operations |
| `/fund` | Financial donation operations |
| `/food` | Food donation operations |
| `/problem` | Counseling/problem management |
| `/admin` | Administrative operations |

---

## Security Features

- Password hashing using **bcrypt**
- JWT authentication
- Environment-based secret management
- Password complexity enforcement
- Admin bootstrap through environment variables
- Secure password reset workflow
- Protection against plain-text password storage

---

## Database Support

Currently supported:

- SQLite (default)
- PostgreSQL

The application can be switched to PostgreSQL by changing the `DATABASE_URL` environment variable.

---

## Screenshots

> Add screenshots here after deployment.

### Home Page

```text
screenshots/home.png
```

### Swagger Documentation

```text
screenshots/swagger.png
```

### Admin Dashboard

```text
screenshots/admin-dashboard.png
```

---

## Future Improvements

- PostgreSQL migrations using Alembic
- Redis caching
- Role-Based Access Control (RBAC)
- API rate limiting
- Frontend dashboard using React
- Kubernetes deployment
- CI/CD pipeline using GitHub Actions
- Notification system
- Analytics dashboard

---

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/new-feature
```

3. Commit your changes

```bash
git commit -m "Add new feature"
```

4. Push your branch

```bash
git push origin feature/new-feature
```

5. Open a Pull Request

---

## License

This project is licensed under the MIT License.

See the [LICENSE](LICENSE) file for details.

---

## Author

**Muhammad Huzaifa**

- GitHub: https://github.com/HuzaifaAIDev

---

## Support

If you found this project useful, consider giving it a ⭐ on GitHub.