import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app as fastapi_app
from app.database import Base, get_db
import app.database as app_db
import app.services.job_processor as app_job_processor
import app.config as app_cfg


@pytest.fixture(scope="session")
def test_temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test DB and certificate PDFs."""
    temp_dir = Path(tempfile.mkdtemp(prefix="cert_test_"))
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def test_engine(test_temp_dir: Path):
    """Create an isolated SQLite database engine for testing."""
    test_db_file = test_temp_dir / "test_certificates.db"
    engine = create_engine(
        f"sqlite:///{test_db_file}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def TestingSessionLocal(test_engine):
    """Sessionmaker bound to the test database."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_test_environment(test_temp_dir: Path, TestingSessionLocal, monkeypatch):
    """
    Automatically configure test isolation for every test:
    - Route BackgroundTasks to the test database session.
    - Route PDF generation output to temporary directory.
    - Provide dependency overrides for FastAPI endpoints.
    """
    test_gen_dir = test_temp_dir / "generated"
    test_gen_dir.mkdir(parents=True, exist_ok=True)

    # Monkeypatch settings and SessionLocal references
    monkeypatch.setattr(app_cfg.settings, "GENERATED_DIR", test_gen_dir)
    monkeypatch.setattr(app_db, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(app_job_processor, "SessionLocal", TestingSessionLocal)

    def _override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    yield
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """TestClient fixture with lifespan execution."""
    with TestClient(fastapi_app) as test_client:
        yield test_client


@pytest.fixture
def db(TestingSessionLocal) -> Generator[Session, None, None]:
    """Direct database session fixture for inspecting or manipulating DB in tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
