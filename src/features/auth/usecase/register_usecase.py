"""Usecase: Register a new Mahasiswa."""

from src.domain.entity.i_mahasiswa_repository import IMahasiswaRepository
from src.core.exceptions import BadRequestException, ConflictException
from src.domain.entity.user import ALLOWED_EMAIL_DOMAIN, Mahasiswa, User
from src.application.i_email_service import IEmailService
from src.application.i_password_service import IPasswordService
from src.application.i_token_service import ITokenService


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


class RegisterUsecase:
    """Registration use case"""

    def __init__(
        self,
        mhs_repository: IMahasiswaRepository,
        password_service: IPasswordService,
        token_service: ITokenService,
        email_service: IEmailService,
    ) -> None:
        self._mhs_repository = mhs_repository
        self._password_service = password_service
        self._token_service = token_service
        self._email_service = email_service

    async def execute(self, request: RegisterRequest) -> RegisterResult:
        """Execute the registration."""

        if not request.email.endswith(ALLOWED_EMAIL_DOMAIN):
            raise BadRequestException(
                f"Hanya {ALLOWED_EMAIL_DOMAIN} email yang diperbolehkan"
            )

        existing = await self._mhs_repository.find_by_email(request.email)
        if existing is not None:
            raise ConflictException(f"Email {request.email} sudah terdaftar")

        hashed_password = self._password_service.hash(request.password)

        newMahasiswa = Mahasiswa.New(
            email=request.email,
            hashed_password=hashed_password,
            nim=request.nim,
            fakultas=request.fakultas,
            departemen=request.departemen,
        )

        newMahasiswa = await self._mhs_repository.save(newMahasiswa)

        verify_token = self._token_service.generate_verification_token(
            newMahasiswa.email
        )
        await self._email_service.send_verification_email(
            newMahasiswa.email, verify_token
        )

        return RegisterResult(user=newMahasiswa)
