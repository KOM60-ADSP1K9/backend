"""Dependency providers for auth repositories, services, and use cases."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.repositories.mahasiswa_repository import MahasiswaRepository
from src.core.db import get_async_db_session
from src.features.auth.usecase.login_usecase import LoginUsecase
from src.features.auth.usecase.me_usecase import MeUsecase
from src.features.auth.usecase.register_usecase import RegisterUsecase
from src.features.auth.usecase.verify_email_usecase import VerifyEmailUsecase
from src.infrastructure.repositories.user_repository import UserRepository
from src.infrastructure.services.bcrypt_password_service import BcryptPasswordService
from src.infrastructure.services.jwt_token_service import JWTTokenService
from src.infrastructure.services.mailtrap_email_service import MailtrapEmailService


def get_user_repository(
    db: AsyncSession = Depends(get_async_db_session),
) -> UserRepository:
    return UserRepository(db)


def get_mhs_repository(
    db: AsyncSession = Depends(get_async_db_session),
) -> UserRepository:
    return MahasiswaRepository(db)


def get_password_service() -> BcryptPasswordService:
    return BcryptPasswordService()


def get_token_service() -> JWTTokenService:
    return JWTTokenService()


def get_email_service() -> MailtrapEmailService:
    return MailtrapEmailService()


def get_register_usecase(
    mhs_repository: MahasiswaRepository = Depends(get_mhs_repository),
    password_service: BcryptPasswordService = Depends(get_password_service),
    token_service: JWTTokenService = Depends(get_token_service),
    email_service: MailtrapEmailService = Depends(get_email_service),
) -> RegisterUsecase:
    return RegisterUsecase(
        mhs_repository=mhs_repository,
        password_service=password_service,
        token_service=token_service,
        email_service=email_service,
    )


def get_login_usecase(
    user_repository: UserRepository = Depends(get_user_repository),
    password_service: BcryptPasswordService = Depends(get_password_service),
    token_service: JWTTokenService = Depends(get_token_service),
) -> LoginUsecase:
    return LoginUsecase(
        user_repository=user_repository,
        password_service=password_service,
        token_service=token_service,
    )


def get_verify_email_usecase(
    user_repository: UserRepository = Depends(get_user_repository),
    token_service: JWTTokenService = Depends(get_token_service),
) -> VerifyEmailUsecase:
    return VerifyEmailUsecase(
        user_repository=user_repository,
        token_service=token_service,
    )


def get_me_usecase() -> MeUsecase:
    return MeUsecase()
