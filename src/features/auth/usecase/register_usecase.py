"""Usecase: Register a new Mahasiswa."""

from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import BadRequestException, ConflictException
from src.domain.entity.user import ALLOWED_EMAIL_DOMAIN, User, UserRole
from src.infrastructure.repositories.user_repository import UserRepository
from src.infrastructure.services.bcrypt_password_service import BcryptPasswordService
from src.infrastructure.services.jwt_token_service import JWTTokenService
from src.infrastructure.services.smtp_email_service import SmtpEmailService


class RegisterRequest:
    def __init__(
        self,
        email: str,
        password: str,
        nim: str,
        fakultas: str,
        departemen: str,
    ) -> None:
        self.email = email
        self.password = password
        self.nim = nim
        self.fakultas = fakultas
        self.departemen = departemen


class RegisterResult:
    def __init__(self, user: User) -> None:
        self.user = user


async def register_usecase(
    request: RegisterRequest,
    db: AsyncSession,
) -> RegisterResult:
    """Execute the registration."""

    if not request.email.endswith(ALLOWED_EMAIL_DOMAIN):
        raise BadRequestException(
            f"Hanya {ALLOWED_EMAIL_DOMAIN} email yang diperbolehkan"
        )

    repo = UserRepository(db)

    existing = await repo.find_by_email(request.email)
    if existing is not None:
        raise ConflictException("Email sudah terdaftar")

    password_service = BcryptPasswordService()
    hashed_password = password_service.hash(request.password)

    user = User.register(
        email=request.email,
        hashed_password=hashed_password,
        role=UserRole.MAHASISWA,
        nim=request.nim,
        fakultas=request.fakultas,
        departemen=request.departemen,
    )

    user = await repo.save(user)

    token_service = JWTTokenService()
    verify_token = token_service.generate_verification_token(user.email)

    email_service = SmtpEmailService()
    await email_service.send_verification_email(user.email, verify_token)

    return RegisterResult(user=user)
