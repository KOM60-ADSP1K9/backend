# Sistem Lost & Found IPB — Backend

REST API untuk sistem pelaporan kehilangan dan penemuan barang di lingkungan IPB University, dibangun dengan **FastAPI** menggunakan pendekatan **Vertical Slice Architecture (VSA)** dan **Domain-Driven Design (DDD)**.

---

**Mata Kuliah:** KOM 1337 Analisis dan Desain Sistem

**Kelompok 9 - P1**

| No | Nama | NIM |
|----|------|-----|
| 1 | Faqih Firman Pratama | G6401231063 |
| 2 | Aghnat Hasya Sayyidina | G6401231074 |
| 3 | Anargya Isadhi Maheswara | G6401231118 |

---

## Tech Stack

- **Framework:** FastAPI
- **Language:** Python 3.13+
- **Database:** PostgreSQL 17+ (async via SQLAlchemy + asyncpg)
- **Migrations:** Alembic
- **Auth:** JWT + email verification (itsdangerous)
- **Email:** SMTP via fastapi-mail
- **Storage:** Cloudflare R2 (aioboto3) / stub mode
- **Rate Limiting:** pyrate-limiter
- **Code Quality:** Ruff, Black, pre-commit
- **Testing:** pytest + pytest-asyncio
- **Containerization:** Docker + Docker Compose

## Arsitektur

Proyek ini menggunakan **Vertical Slice Architecture** di mana setiap fitur memiliki folder tersendiri yang mencakup controller, dependencies, dan usecase-nya masing-masing, dikombinasikan dengan prinsip **Domain-Driven Design** pada layer domain.

```
src/
├── app.py                          # FastAPI app entry point
├── core/                           # Infrastruktur inti
│   ├── auth.py                     # JWT auth dependency
│   ├── config.py                   # Konfigurasi env
│   ├── db.py                       # Database session
│   ├── db_seeder.py                # Seeder utility
│   ├── error_handler.py            # Global error handler
│   ├── exceptions.py               # Custom HTTP exceptions
│   ├── http.py                     # Response wrapper
│   └── rate_limiter.py             # Rate limit helper
├── application/                    # Interface/port layer
│   ├── i_email_service.py
│   ├── i_password_service.py
│   ├── i_storage_service.py
│   └── i_token_service.py
├── domain/                         # Domain entities & repository interfaces
│   └── entity/
│       ├── user.py                 # User, Mahasiswa, Staff
│       ├── laporan.py              # LaporanHilang, LaporanTemuan, status lifecycle
│       ├── inquiry.py              # ClaimInquiry, FoundInquiry
│       ├── barang.py               # Barang
│       ├── notification.py         # Notification
│       ├── lokasi.py               # Lokasi
│       ├── kategori_barang.py      # KategoriBarang
│       └── fakultas.py             # Daftar Fakultas & Departemen IPB
├── features/                       # Vertical slices per fitur
│   ├── auth/                       # Registrasi, login, verifikasi email, profil
│   ├── lost_report/                # Buat laporan kehilangan
│   ├── found_report/               # Buat laporan penemuan
│   ├── report/                     # Detail, edit, hapus, update status laporan
│   ├── inquiry/                    # Klaim & temuan inquiry
│   ├── homepage/                   # Daftar semua laporan & laporan milik user
│   ├── notification/               # Notifikasi user
│   ├── user/                       # Daftar user (staff only)
│   ├── lokasi/                     # Daftar lokasi
│   └── kategori_barang/            # Daftar kategori barang
└── infrastructure/                 # Implementasi konkret
    ├── repositories/               # SQLAlchemy repository implementations
    ├── services/                   # Email, JWT, bcrypt, storage
    └── tables/                     # SQLAlchemy ORM table mappings
```

## API Endpoints

| Method | Path | Deskripsi | Auth |
|--------|------|-----------|------|
| `POST` | `/auth/register` | Registrasi mahasiswa baru | — |
| `POST` | `/auth/login` | Login (email + password) | — |
| `GET` | `/auth/verify-email?token=` | Verifikasi email, redirect ke frontend | — |
| `GET` | `/auth/me` | Profil user yang sedang login | JWT |
| `GET` | `/auth/fakultas` | Daftar fakultas | — |
| `GET` | `/auth/fakultas/departemen?fakultas=` | Daftar departemen | — |
| `POST` | `/lost-reports` | Buat laporan kehilangan | JWT |
| `POST` | `/found-reports` | Buat laporan penemuan | JWT |
| `GET` | `/reports` | Daftar semua laporan | JWT |
| `GET` | `/reports/my` | Laporan milik user sendiri | JWT |
| `GET` | `/reports/:id` | Detail laporan | JWT |
| `PUT` | `/reports/:id` | Edit detail laporan | JWT |
| `PATCH` | `/reports/:id/status` | Update status laporan | JWT |
| `DELETE` | `/reports/:id` | Hapus laporan | JWT |
| `POST` | `/reports/:id/inquiries/claim` | Ajukan klaim | JWT |
| `POST` | `/reports/:id/inquiries/found` | Ajukan temuan | JWT |
| `PATCH` | `/inquiries/:id/status` | Update status inquiry | JWT |
| `GET` | `/notifications` | Daftar notifikasi | JWT |
| `PATCH` | `/notifications/:id/read` | Tandai notifikasi sebagai dibaca | JWT |
| `GET` | `/users` | Daftar semua user (staff) | JWT |
| `GET` | `/lokasi` | Daftar lokasi | JWT |
| `GET` | `/kategori-barang` | Daftar kategori barang | JWT |

## Prerequisites

- Python 3.13+
- PostgreSQL 17+
- Docker 24+ & Docker Compose v2+ (opsional)
- Git

## Instalasi

1. **Clone repository**

   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Setup virtual environment dan dependensi**

   ```bash
   uv venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   uv sync
   ```

   Atau dengan pip:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Setup environment variables**

   ```bash
   cp .env.example .env
   # Edit .env sesuai konfigurasi lokal

   cp .env.example .env.test
   # Edit .env.test untuk environment testing
   ```

4. **Install pre-commit hooks**

   ```bash
   pre-commit install
   ```

## Konfigurasi

Edit file `.env`:

```env
# App
APP_ENV=development
PORT=9000
BASE_URL=http://localhost:9000
FRONTEND_BASE_URL=http://localhost:5173

# Database (PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# JWT
# Generate: openssl rand -hex 32
JWT_SECRET_KEY=your_super_secret_key_here
JWT_EXPIRES_MINUTES=1440
VERIFICATION_SECRET_KEY=your_verification_secret_key_here
EMAIL_SALT=your_email_salt

# Email (SMTP / Mailtrap untuk development)
SMTP_HOST=sandbox.smtp.mailtrap.io
SMTP_PORT=587
SMTP_USER=your_mailtrap_user
SMTP_PASSWORD=your_mailtrap_password
SMTP_FROM=noreply@apps.ipb.ac.id

# Cloudflare R2 (file storage)
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET=
R2_PUBLIC_URL=

# stub = tidak upload file sungguhan (development)
FACTORY_STORAGE_TYPE=stub
```

## Database

**Jalankan migrasi:**

```bash
alembic upgrade head
```

**Buat migrasi baru** (setelah perubahan model):

```bash
alembic revision --autogenerate -m "deskripsi perubahan"
alembic upgrade head
```

## Database Seeding (Development)

```bash
python seed.py seed       # Insert data tanpa menghapus data lama
python seed.py reseed     # Truncate lalu insert ulang (direkomendasikan)
python seed.py truncate   # Hapus semua data
```

Via Docker:

```bash
docker compose exec app python /app/seed.py reseed
```

## Menjalankan Aplikasi

**Development (auto-reload):**

```bash
python main.py
```

**Production:**

```bash
uvicorn src.app:app --host 0.0.0.0 --port 9000
```

## Docker

**Build dan jalankan:**

```bash
docker compose up -d --build
```

**Development watch mode (live reload):**

```bash
docker compose up --watch --build
```

Migrasi dijalankan otomatis saat startup. Untuk menjalankan manual:

```bash
docker compose exec app alembic upgrade head
```

Aplikasi tersedia di `http://localhost:9000`

## Testing

```bash
pytest tests/ -v
```

## Code Quality

```bash
ruff check --fix .
black .
```
