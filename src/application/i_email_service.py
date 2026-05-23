"""Abstract interface for email sending."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entity.inquiry import InquiryType


class IEmailService(ABC):
    """Port for sending transactional emails."""

    @abstractmethod
    async def send_verification_email(self, to_email: str, token: str) -> None:
        """Send a verification email to *to_email* containing *token*."""

    @abstractmethod
    async def send_inquiry_notification(
        self,
        to_email: str,
        inquiry_type: InquiryType,
        laporan_id: UUID,
    ) -> None:
        """Notify a laporan owner that a new inquiry has been submitted."""
