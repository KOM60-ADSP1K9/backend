"""Abstract interface for the Inquiry repository."""

from abc import abstractmethod
from collections.abc import Iterable
from uuid import UUID

from src.domain.entity.inquiry import Inquiry
from src.infrastructure.repositories.repository import IRepository


class IInquiryRepository(IRepository[Inquiry, UUID]):
    """Port for inquiry persistence."""

    @abstractmethod
    async def update(self, entity: Inquiry) -> Inquiry:
        """Persist changes to an existing inquiry."""

    @abstractmethod
    async def findByLaporanId(self, laporan_id: UUID) -> Iterable[Inquiry]:
        """Return all inquiries for a given laporan."""

    @abstractmethod
    async def findBySenderUserId(self, sender_user_id: UUID) -> Iterable[Inquiry]:
        """Return all inquiries sent by a given user."""
