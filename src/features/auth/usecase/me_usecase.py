"""Usecase: Get current authenticated user profile."""

from src.domain.entity.user import User


class MeResult:
    def __init__(self, user: User) -> None:
        self.user = user


class MeUsecase:
    """Current-user profile use case (no external dependencies)."""

    def execute(self, user: User) -> MeResult:
        """Return the current user."""
        return MeResult(user=user)
