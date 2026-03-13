"""Usecase: Verify user email via token link."""

from src.core.exceptions import AuthenticationException, BadRequestException
from src.domain.entity.user import User
from src.application.i_token_service import ITokenService
from src.domain.entity.i_user_repository import IUserRepository


class VerifyEmailResult:
    def __init__(self, user: User) -> None:
        self.user = user


class VerifyEmailUsecase:
    """Email verification use case"""

    def __init__(
        self,
        user_repository: IUserRepository,
        token_service: ITokenService,
    ) -> None:
        self._user_repository = user_repository
        self._token_service = token_service

    async def execute(self, token: str) -> VerifyEmailResult:
        """Execute the email verification flow."""

        email = self._token_service.verify_email_token(token)

        user = await self._user_repository.find_by_email(email)
        if user is None:
            raise AuthenticationException(
                "Verifikasi token tidak valid: pengguna tidak ditemukan"
            )

        if user.is_email_verified:
            raise BadRequestException("Email sudah diverifikasi")

        user.verify_email()
        user = await self._user_repository.update(user)

        return VerifyEmailResult(user=user)
