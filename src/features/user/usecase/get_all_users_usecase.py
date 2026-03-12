"""Usecase: Get all users (Staff only)."""

from collections.abc import Iterable
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entity.user import User
from src.infrastructure.repositories.user_repository import UserRepository


class GetAllUsersResult:
    def __init__(self, users: Iterable[User]) -> None:
        self.users = users


async def get_all_users_usecase(db: AsyncSession) -> GetAllUsersResult:
    """Return every user in the system."""
    repo = UserRepository(db)
    users = await repo.findAll()
    return GetAllUsersResult(users=users)
