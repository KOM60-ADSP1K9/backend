# FastAPI VSA-DDD Template (WORK IN PROGRESS)

A FastAPI template implementing Vertical Slice Architecture (VSA) and Domain-Driven Design (DDD) approach with async PostgreSQL support. Purposely for System Analysis and Design courses (KOM1337) so it may need some changes for another use.

check out my other template : [Nest TS Starter Kit](https://github.com/AghnatHs/nest-core-kit)

!! Not fully implementing DDD

### Project Structure

```
├── src/
│   ├── app.py                 # FastAPI application entry point
│   ├── core/                  # Core infrastructure
│   │   ├── config.py          # Application configuration
│   │   └── db.py              # Database setup and session management
│   ├── domain/                # Domain models (business entities)
│   │   └── user.py            # User domain model
│   ├── features/              # Feature slices (VSA)
│   └── infrastructure/        # Infrastructure layer
│       └── tables/            # SQLAlchemy table mappings
│           ├── user_table.py  # User table ORM
│           └── __init__.py
├── alembic/                   # Database migrations
│   ├── env.py                 # Alembic environment config
│   └── versions/              # Migration scripts
├── main.py                    # Application entry point
├── pyproject.toml             # Project dependencies
├── requirements.txt           # Pip dependencies
└── alembic.ini               # Alembic configuration
```

## Features

- **Database Migrations**: Alembic integration for schema versioning
- **Domain Models**: Rich domain models with business logic
- **Vertical Slice**: Separate by business language / domain
- **Environment Config**: `.env` based configuration
- **Code Quality**: Pre-commit hooks with Black and Ruff
- **Type Safety**: Full type hints support

## 📋 Prerequisites

- Python 3.13.11+
- PostgreSQL 17+
- Docker 24+
- Docker Compose v2+
- Git

## 🛠️ Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd fastapi-vsa-ddd
   ```

2. **Venv and its dependencies**

   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv sync

   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your credentials

   cp .env.example .env.test
   # Edit .env.test with your for test environment credentials
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Configuration

Edit `.env` file with your settings:

```env
# App Configuration
APP_ENV=development
PORT=9000
BASE_URL=http://localhost:9000

# Database Configuration (PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# Authentication (JWT)
# Generate secret key using `openssl rand -hex 32`
JWT_SECRET_KEY=your_super_secret_key_here
JWT_EXPIRES_MINUTES=1440
VERIFICATION_SECRET_KEY=your_verification_secret_key_here
EMAIL_SALT=your_email_salt

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:9000/auth/google/callback

# Email Service (Mailtrap/SMTP)
SMTP_HOST=sandbox.smtp.mailtrap.io
SMTP_PORT=587
SMTP_USER=your_mailtrap_user
SMTP_PASSWORD=your_mailtrap_password
SMTP_FROM=noreply@apps.ipb.ac.id

```

Configuration is managed in [`src/core/config.py`](src/core/config.py).

## Database Setup

2. **Run migrations**

   ```bash
   alembic upgrade head
   ```

3. **Create new migration** (after model changes)
   ```bash
   alembic revision --autogenerate -m "description"
   alembic upgrade head
   ```

## Database Seeding (DEVELOPMENT ONLY)

Seeder utilities are available for three operations:

- `seed`: insert seed data without clearing existing rows
- `reseed`: truncate first, then insert fresh seed data
- `truncate`: remove all rows from the target table

for best practice, use `reseed` to ensure a clean state before seeding new data.

Use seeder

```bash
python seed.py seed
python seed.py reseed
python seed.py truncate
```

Docker seeder usage:

```bash
docker compose exec app python /app/seed.py seed
docker compose exec app python /app/seed.py reseed
docker compose exec app python /app/seed.py truncate
```

One-off seeding without starting the app service first:

```bash
docker compose run --rm app python /app/seed.py reseed
```

## Running the Application

### Development mode (auto reload)\*\*:

```bash
python main.py
```

### Production mode\*\*:

```bash
uvicorn src.app:app --host 0.0.0.0 --port 9000
```

### Docker Compose

#### 1. Prepare environment

```bash
cp .env.example .env
```

Set .env correctly

`docker-compose.yaml` will use these values for both app and PostgreSQL.

#### 2. Build and run

```bash
docker compose up -d --build
```

The app and database run in one network

- `http://localhost:${PORT}`

#### 3. Watch mode in development (live update)

```bash
docker compose up --watch --build
```

watch behavior:

- sync `./src` to `/app/src`
- rebuild on `pyproject.toml`, `uv.lock`, and `Dockerfile` changes

#### 4. Migrations in Docker

Migrations are automatically executed on app startup:

```bash
alembic upgrade head
```

or, run them manually:

```bash
docker compose exec app alembic upgrade head
```

The API will be available at `http://localhost:9000`

## Code Style

- **Black**: Code formatting
- **Ruff**: Fast Python linter
- **Pre-commit**: Automated code quality checks

Run manually:

```bash
black .
ruff check --fix
```

## Testing

```bash
pytest tests/ -v
```
