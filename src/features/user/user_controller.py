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
from src.domain.entity.lokasi import Lokasi
from src.domain.entity.user import User, UserRole
from src.features.user.usecase.get_all_users_usecase import GetAllUsersUsecase
from src.infrastructure.repositories.lokasi_repository import LokasiRepository
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
    lokasi_id: UUID | None
    lokasi: "LokasiResponseDto | None"
    email_verified_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None


class LokasiResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    latitude: float
    longitude: float


def _to_user_response_dto(user: User, lokasi: Lokasi | None) -> UserResponseDto:
    return UserResponseDto(
        id=user.id,
        email=user.email,
        role=user.role,
        nim=user.nim,
        fakultas=user.fakultas,
        departemen=user.departemen,
        nip=user.nip,
        lokasi_id=user.lokasi_id,
        lokasi=LokasiResponseDto.model_validate(lokasi) if lokasi is not None else None,
        email_verified_at=user.email_verified_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


# ── Endpoints ───────────────────────────────────────────────────────────────


@user_router.get("", response_model=HTTPDataResponse[list[UserResponseDto]])
async def get_all_users(
    _current_user: User = Depends(require_role(UserRole.STAFF)),
    db: AsyncSession = Depends(get_async_db_session),
) -> HTTPDataResponse[list[UserResponseDto]]:
    """Get all users. **Staff only.**"""
    usecase = GetAllUsersUsecase(user_repository=UserRepository(db))
    result = await usecase.execute()

    users = list(result.users)
    lokasi_ids = {user.lokasi_id for user in users if user.lokasi_id is not None}
    lokasi_by_id: dict[UUID, Lokasi] = {}

    if lokasi_ids:
        lokasi_repository = LokasiRepository(db)
        lokasi_by_id = {
            lokasi.id: lokasi
            for lokasi in await lokasi_repository.find_all_by_ids(lokasi_ids)
        }

    return HTTPDataResponse[list[UserResponseDto]](
        status="success",
        data=[
            _to_user_response_dto(user, lokasi_by_id.get(user.lokasi_id))
            for user in users
        ],
        message="Users fetched successfully",
    )
