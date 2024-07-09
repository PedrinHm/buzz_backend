import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.config.database import Base, get_db
from app.models.user_type import UserType, UserTypeNames

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency override for testing
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def test_app():
    Base.metadata.create_all(bind=engine)
    # Criando tipos de usuário
    session = TestingSessionLocal()
    session.add_all([
        UserType(description=UserTypeNames.STUDENT),
        UserType(description=UserTypeNames.DRIVER),
        UserType(description=UserTypeNames.ADMIN),
    ])
    session.commit()
    session.close()
    
    client = TestClient(app)
    yield client
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
