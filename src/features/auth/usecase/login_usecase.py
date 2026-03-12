"""Usecase: Login (email + password) for both Mahasiswa and Staff."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import AuthenticationException
from src.infrastructure.repositories.user_repository import UserRepository
from src.infrastructure.services.bcrypt_password_service import BcryptPasswordService
from src.infrastructure.services.jwt_token_service import JWTTokenService


class LoginRequest:
    def __init__(self, email: str, password: str) -> None:
        self.email = email
        self.password = password


class LoginResult:
    def __init__(self, access_token: str) -> None:
        self.access_token = access_token


async def login_usecase(
    request: LoginRequest,
    db: AsyncSession,
) -> LoginResult:
    """Execute the login."""

    repo = UserRepository(db)

    user = await repo.find_by_email(request.email)
    if user is None:
        raise AuthenticationException("Email atau password salah")

    password_service = BcryptPasswordService()
    if not password_service.verify(request.password, user.hashed_password):
        raise AuthenticationException("Email atau password salah")

    if not user.is_email_verified:
        raise AuthenticationException("Silahkan verifikasi email Anda sebelum login")

    token_service = JWTTokenService()
    access_token = token_service.create_access_token(user)

    return LoginResult(access_token=access_token)
