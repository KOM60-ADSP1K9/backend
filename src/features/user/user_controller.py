"""User controller – user-management endpoints (Staff only).

GET  /users – Get all users (Staff only)

"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import require_role
from src.core.db import get_async_db_session
from src.core.http import HTTPDataResponse
from src.domain.entity.user import User, UserRole
from src.features.user.usecase.get_all_users_usecase import GetAllUsersUsecase
from src.infrastructure.repositories.user_repository import UserRepository

user_router = APIRouter(prefix="/users", tags=["users"])


# ── DTOs ────────────────────────────────────────────────────────────────────


class UserResponseDto(BaseModel):
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


# ── Endpoints ───────────────────────────────────────────────────────────────


@user_router.get("", response_model=HTTPDataResponse[list[UserResponseDto]])
async def get_all_users(
    _current_user: User = Depends(require_role(UserRole.STAFF)),
    db: AsyncSession = Depends(get_async_db_session),
) -> HTTPDataResponse[list[UserResponseDto]]:
    """Get all users. **Staff only.**"""
    usecase = GetAllUsersUsecase(user_repository=UserRepository(db))
    result = await usecase.execute()
    return HTTPDataResponse[list[UserResponseDto]](
        status="success",
        data=[UserResponseDto.model_validate(u) for u in result.users],
        message="Users fetched successfully",
    )
