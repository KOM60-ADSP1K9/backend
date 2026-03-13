"""Usecase: Login (email + password) for both Mahasiswa and Staff."""

from src.core.exceptions import AuthenticationException
from src.application.i_password_service import IPasswordService
from src.application.i_token_service import ITokenService
from src.domain.entity.i_user_repository import IUserRepository


class LoginRequest:
    def __init__(self, email: str, password: str) -> None:
        self.email = email
        self.password = password


class LoginResult:
    def __init__(self, access_token: str) -> None:
        self.access_token = access_token


class LoginUsecase:
    """Login use case"""

    def __init__(
        self,
        user_repository: IUserRepository,
        password_service: IPasswordService,
        token_service: ITokenService,
    ) -> None:
        self._user_repository = user_repository
        self._password_service = password_service
        self._token_service = token_service

    async def execute(self, request: LoginRequest) -> LoginResult:
        """Execute the login."""

        user = await self._user_repository.find_by_email(request.email)
        if user is None:
            raise AuthenticationException("Email atau password salah")

        if not self._password_service.verify(request.password, user.hashed_password):
            raise AuthenticationException("Email atau password salah")

        if not user.is_email_verified:
            raise AuthenticationException(
                "Silahkan verifikasi email Anda sebelum login"
            )

        access_token = self._token_service.create_access_token(user)

        return LoginResult(access_token=access_token)
