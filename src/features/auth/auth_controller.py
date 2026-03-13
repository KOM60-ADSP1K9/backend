"""
Auth controller – all authentication-related endpoints.

POST /auth/register     – Mahasiswa registration
POST /auth/login        – Login (email + password)
GET  /auth/verify-email – Verify email from link
GET  /auth/me           – Current user profile (protected)
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi_limiter.depends import RateLimiter
from pydantic import BaseModel, ConfigDict, EmailStr
from pyrate_limiter import Duration, Limiter, Rate
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.rate_limiter import rate_limit_dependency
from src.core.auth import get_current_user
from src.core.config import settings
from src.core.db import get_async_db_session
from src.core.http import HTTPDataResponse, HTTPMessageResponse
from src.domain.entity.user import User, UserRole
from src.features.auth.usecase.login_usecase import LoginRequest, LoginUsecase
from src.features.auth.usecase.me_usecase import MeUsecase
from src.features.auth.usecase.register_usecase import RegisterRequest, RegisterUsecase
from src.features.auth.usecase.verify_email_usecase import VerifyEmailUsecase
from src.infrastructure.repositories.user_repository import UserRepository
from src.infrastructure.services.bcrypt_password_service import BcryptPasswordService
from src.infrastructure.services.jwt_token_service import JWTTokenService
from src.infrastructure.services.smtp_email_service import SmtpEmailService

auth_router = APIRouter(prefix="/auth", tags=["auth"])

# ── DTOs ──


class RegisterBody(BaseModel):
    email: EmailStr
    password: str
    nim: str
    fakultas: str
    departemen: str


class RegisterResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    role: UserRole
    nim: str | None
    fakultas: str | None
    departemen: str | None


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class LoginResponseDto(BaseModel):
    access_token: str


class MeResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    role: UserRole
    nim: str | None
    fakultas: str | None
    departemen: str | None
    nip: str | None
    email_verified_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None


# ── Endpoints ──


@auth_router.post(
    "/register",
    response_model=HTTPDataResponse[RegisterResponseDto],
    status_code=201,
    dependencies=rate_limit_dependency(5, Duration.MINUTE * 10),
)
async def register(
    body: RegisterBody,
    db: AsyncSession = Depends(get_async_db_session),
) -> HTTPDataResponse[RegisterResponseDto]:
    """Register a new Mahasiswa. A verification email will be sent."""
    usecase = RegisterUsecase(
        user_repository=UserRepository(db),
        password_service=BcryptPasswordService(),
        token_service=JWTTokenService(),
        email_service=SmtpEmailService(),
    )
    result = await usecase.execute(
        RegisterRequest(
            email=body.email,
            password=body.password,
            nim=body.nim,
            fakultas=body.fakultas,
            departemen=body.departemen,
        ),
    )
    return HTTPDataResponse[RegisterResponseDto](
        status="success",
        data=RegisterResponseDto.model_validate(result.user),
        message="Registrasi Berhasil, Silahkan cek email Anda untuk memverifikasi akun.",
    )


@auth_router.post(
    "/login",
    response_model=HTTPDataResponse[LoginResponseDto],
    dependencies=rate_limit_dependency(5, Duration.MINUTE * 1),
)
async def login(
    body: LoginBody,
    db: AsyncSession = Depends(get_async_db_session),
) -> HTTPDataResponse[LoginResponseDto]:
    """Login with email and password (Mahasiswa & Staff)."""
    usecase = LoginUsecase(
        user_repository=UserRepository(db),
        password_service=BcryptPasswordService(),
        token_service=JWTTokenService(),
    )
    result = await usecase.execute(
        LoginRequest(email=body.email, password=body.password),
    )
    return HTTPDataResponse[LoginResponseDto](
        status="success",
        data=LoginResponseDto(
            access_token=result.access_token,
        ),
        message="Login berhasil",
    )


@auth_router.get(
    "/verify-email",
    response_model=HTTPMessageResponse,
    dependencies=rate_limit_dependency(5, Duration.MINUTE * 1),
)
async def verify_email(
    token: str = Query(..., description="Email verification token"),
    db: AsyncSession = Depends(get_async_db_session),
) -> HTTPMessageResponse:
    """Verify a user's email address via the token sent in the email."""
    usecase = VerifyEmailUsecase(
        user_repository=UserRepository(db),
        token_service=JWTTokenService(),
    )
    await usecase.execute(token)
    return HTTPMessageResponse(
        status="success",
        message="Verifikasi email berhasil",
    )


@auth_router.get(
    "/me",
    response_model=HTTPDataResponse[MeResponseDto],
    dependencies=rate_limit_dependency(40, Duration.MINUTE),
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> HTTPDataResponse[MeResponseDto]:
    """Get the currently authenticated user's profile."""
    usecase = MeUsecase()
    result = usecase.execute(current_user)
    return HTTPDataResponse[MeResponseDto](
        status="success",
        data=MeResponseDto.model_validate(result.user),
        message="Profile pengguna berhasil diambil",
    )
