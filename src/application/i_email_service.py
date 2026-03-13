"""Abstract interface for email sending."""

from abc import ABC, abstractmethod


class IEmailService(ABC):
    """Port for sending transactional emails."""

    @abstractmethod
    async def send_verification_email(self, to_email: str, token: str) -> None:
        """Send a verification email to *to_email* containing *token*."""
