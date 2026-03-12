"""Usecase: Verify user email via token link."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import AuthenticationException, BadRequestException
from src.domain.entity.user import User
from src.infrastructure.repositories.user_repository import UserRepository
from src.infrastructure.services.jwt_token_service import JWTTokenService


class VerifyEmailResult:
    def __init__(self, user: User) -> None:
        self.user = user


async def verify_email_usecase(
    token: str,
    db: AsyncSession,
) -> VerifyEmailResult:
    """Execute the email verification flow."""

    token_service = JWTTokenService()
    email = token_service.verify_email_token(token)

    repo = UserRepository(db)

    user = await repo.find_by_email(email)
    if user is None:
        raise AuthenticationException(
            "Verifikasi token tidak valid: pengguna tidak ditemukan"
        )

    if user.is_email_verified:
        raise BadRequestException("Email sudah diverifikasi")

    user.verify_email()
    user = await repo.update(user)

    return VerifyEmailResult(user=user)
