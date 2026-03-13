"""Usecase: Get all users (Staff only)."""

from collections.abc import Iterable
from src.domain.entity.user import User
from src.domain.entity.i_user_repository import IUserRepository


class GetAllUsersResult:
    def __init__(self, users: Iterable[User]) -> None:
        self.users = users


class GetAllUsersUsecase:
    """Get-all-users use case with injected repository."""

    def __init__(self, user_repository: IUserRepository) -> None:
        self._user_repository = user_repository

    async def execute(self) -> GetAllUsersResult:
        """Return every user in the system."""
        users = await self._user_repository.findAll()
        return GetAllUsersResult(users=users)
