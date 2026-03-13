"""
Shared test helpers – reusable seed functions and constants.
"""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity.user import User, UserRole
from src.infrastructure.repositories.user_repository import UserRepository
from src.infrastructure.services.bcrypt_password_service import BcryptPasswordService
from src.infrastructure.services.jwt_token_service import JWTTokenService

# ── Constants ────────────────────────────────────────────────────────

VALID_EMAIL = "testuser@apps.ipb.ac.id"
VALID_PASSWORD = "SecureP@ss123"
VALID_NIM = "G6401211001"
VALID_FAKULTAS = "FMIPA"
VALID_DEPARTEMEN = "Ilmu Komputer"

STAFF_EMAIL = "staff@apps.ipb.ac.id"
STAFF_PASSWORD = "StaffP@ss123"
STAFF_NIP = "197001011990011001"

# Pre-hashed password (computed once to keep tests fast)
_pwd_svc = BcryptPasswordService()
_HASHED_PASSWORD = _pwd_svc.hash(VALID_PASSWORD)
_HASHED_STAFF_PASSWORD = _pwd_svc.hash(STAFF_PASSWORD)


async def seed_verified_mahasiswa(db: AsyncSession) -> User:
    """Insert a verified MAHASISWA and return the domain entity."""
    user = User.register(
        email=VALID_EMAIL,
        hashed_password=_HASHED_PASSWORD,
        role=UserRole.MAHASISWA,
        nim=VALID_NIM,
        fakultas=VALID_FAKULTAS,
        departemen=VALID_DEPARTEMEN,
    )
    user.verify_email()
    return await UserRepository(db).save(user)


async def seed_unverified_mahasiswa(db: AsyncSession) -> User:
    """Insert an unverified MAHASISWA and return the domain entity."""
    user = User.register(
        email=VALID_EMAIL,
        hashed_password=_HASHED_PASSWORD,
        role=UserRole.MAHASISWA,
        nim=VALID_NIM,
        fakultas=VALID_FAKULTAS,
        departemen=VALID_DEPARTEMEN,
    )
    return await UserRepository(db).save(user)


async def seed_verified_staff(db: AsyncSession) -> User:
    """Insert a verified STAFF user and return the domain entity."""
    user = User.register(
        email=STAFF_EMAIL,
        hashed_password=_HASHED_STAFF_PASSWORD,
        role=UserRole.STAFF,
        nip=STAFF_NIP,
    )
    user.verify_email()
    return await UserRepository(db).save(user)


def get_auth_header(user: User) -> dict[str, str]:
    """Generate a valid Authorization header for the given user."""
    token_svc = JWTTokenService()
    token = token_svc.create_access_token(user)
    return {"Authorization": f"Bearer {token}"}


async def login_and_get_token(client: AsyncClient, email: str, password: str) -> str:
    """Login via the API and return the access token string."""
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["data"]["access_token"]
