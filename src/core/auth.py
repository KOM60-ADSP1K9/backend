from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_async_db_session
from src.core.exceptions import AuthenticationException, AuthorizationException
from src.domain.entity.user import User, UserRole
from src.infrastructure.repositories.user_repository import UserRepository
from src.infrastructure.services.jwt_token_service import JWTTokenService

_bearer_scheme = HTTPBearer()
_token_service = JWTTokenService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_async_db_session),
) -> User:
    payload = _token_service.verify_token(credentials.credentials)

    user = await UserRepository(db).findById(payload.user_id)
    if user is None:
        raise AuthenticationException("User tidak ditemukan")

    return user


def require_role(*roles: UserRole) -> Callable:
    async def _guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise AuthorizationException(
                "Kamu tidak memiliki izin untuk mengakses resource ini",
            )
        return user

    return _guard
