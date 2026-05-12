"""
Root test configuration.

Loads .env.test BEFORE any application code is imported, creates the
test database schema once per session, and provides per-test isolation
by truncating all tables after each test.
"""

import os
import asyncio
import pytest_asyncio

from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ── 1. Force .env.test BEFORE anything else touches `settings` ────────

load_dotenv(
    os.path.join(os.path.dirname(__file__), "..", ".env.test"),
    override=True,
)


# ── 2. Now it's safe to import application code ──────────────────────
def _load_app_modules():
    from src.core.config import Settings
    from src.core.db import Base, get_async_db_session
    from src.infrastructure.tables import (
        BarangTable,
        LaporanHilangTable,
        LaporanTable,
        LaporanTemuanTable,
        KategoriBarangTable,
        LokasiTable,
        UserTable,
    )

    # Ensure model modules are imported so metadata is fully registered.
    _ = (
        BarangTable,
        LaporanTable,
        LaporanHilangTable,
        LaporanTemuanTable,
        KategoriBarangTable,
        LokasiTable,
        UserTable,
    )

    return Settings, Base, get_async_db_session


Settings, Base, get_async_db_session = _load_app_modules()

# Build a fresh Settings from the test env vars
_test_settings = Settings()


# ── 3. Schema bootstrap (runs once, sync, before any async test) ─────
def _bootstrap_schema() -> list[str]:
    """
    Create all tables synchronously (before the async event loop
    used by the tests exists) and return the list of table names
    in reverse-dependency order (for truncation).
    """
    engine = create_async_engine(_test_settings.database_url, echo=False)
    loop = asyncio.new_event_loop()

    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    loop.run_until_complete(_setup())
    loop.close()

    return [t.name for t in reversed(Base.metadata.sorted_tables)]


_TABLE_NAMES = _bootstrap_schema()


# ── 4. Per-test session with auto-cleanup via truncation ─────────────
@pytest_asyncio.fixture
async def db_session():
    """
    Yield a fresh ``AsyncSession`` for each test.

    A **new engine** is created per-test to avoid the asyncpg
    "Future attached to a different loop" issue that occurs when
    engines created on one event loop are reused on another.

    After the test finishes, all tables are truncated so the next
    test starts with a clean slate.
    """
    engine = create_async_engine(_test_settings.database_url, echo=False)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        yield session

    # Truncate every table after the test (CASCADE for FKs)
    if _TABLE_NAMES:
        async with engine.begin() as conn:
            for name in _TABLE_NAMES:
                await conn.execute(text(f'TRUNCATE TABLE "{name}" CASCADE'))

    await engine.dispose()


# ── 5. Async HTTP client wired to the FastAPI app ────────────────────
@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """
    An ``httpx.AsyncClient`` that speaks to the FastAPI app in-process.
    The app's ``get_async_db_session`` dependency is overridden so
    every request inside a single test shares the same session—and
    therefore the same data scope. All ``get_storage_service``
    providers are pinned to ``StubStorageService`` so tests never
    hit real object storage even if the production wiring changes.
    """
    from src.app import app
    from src.application.i_storage_service import IStorageService
    from src.features.found_report.found_report_dependencies import (
        get_storage_service as get_found_report_storage_service,
    )
    from src.features.lost_report.lost_report_dependencies import (
        get_storage_service as get_lost_report_storage_service,
    )
    from src.features.report.report_dependencies import (
        get_storage_service as get_report_storage_service,
    )
    from src.infrastructure.services.stub_storage_service import StubStorageService

    async def _override_db():
        yield db_session

    def _override_storage() -> IStorageService:
        return StubStorageService()

    app.dependency_overrides[get_async_db_session] = _override_db
    app.dependency_overrides[get_found_report_storage_service] = _override_storage
    app.dependency_overrides[get_lost_report_storage_service] = _override_storage
    app.dependency_overrides[get_report_storage_service] = _override_storage

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
