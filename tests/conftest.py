import os

os.environ["FINANCE_API_TEST"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.core.security import hash_password


@pytest.fixture()
def test_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestSession()
    admin = User(
        email="admin@test.com",
        hashed_password=hash_password("password12345"),
        full_name="Admin",
        role=UserRole.admin,
    )
    viewer = User(
        email="viewer@test.com",
        hashed_password=hash_password("password12345"),
        full_name="Viewer",
        role=UserRole.viewer,
    )
    analyst = User(
        email="analyst@test.com",
        hashed_password=hash_password("password12345"),
        full_name="Analyst",
        role=UserRole.analyst,
    )
    db.add_all([admin, viewer, analyst])
    db.commit()
    db.close()
    yield engine, TestSession
    engine.dispose()


@pytest.fixture()
def client(test_db):
    engine, TestSession = test_db

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
