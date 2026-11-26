import os
import shutil
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEST_DB_PATH = (BASE_DIR / "test_isolated_suite.db").resolve()
ORIG_DB_PATH = (BASE_DIR / "smart_shopping.db").resolve()
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH.as_posix()}"

# Set DATABASE_URL immediately at module load time so any early import uses the isolated DB
if ORIG_DB_PATH.exists():
    shutil.copyfile(ORIG_DB_PATH, TEST_DB_PATH)

os.environ["DATABASE_URL"] = TEST_DB_URL

def pytest_configure(config):
    if ORIG_DB_PATH.exists():
        shutil.copyfile(ORIG_DB_PATH, TEST_DB_PATH)
    os.environ["DATABASE_URL"] = TEST_DB_URL

    import app.core.config as app_config
    app_config.settings.DATABASE_URL = TEST_DB_URL

    import app.db.session as session_module
    test_engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    session_module.engine = test_engine
    session_module.SessionLocal = TestSessionLocal

    from app.main import app
    from app.db.session import get_db

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

def pytest_unconfigure(config):
    import app.db.session as session_module
    if hasattr(session_module, "engine") and session_module.engine:
        session_module.engine.dispose()
    
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass

@pytest.fixture(scope="session", autouse=True)
def isolate_database():
    yield
