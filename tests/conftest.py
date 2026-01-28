"""
Shared pytest fixtures for unit and integration tests.
"""
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from blazing.main import app
from blazing.db import get_session
from blazing.models.pokemon import Pokemon


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    """
    Create an in-memory SQLite database for testing.
    This fixture is used for both unit and integration tests.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session
    
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with the test database session.
    This fixture overrides the database dependency for integration tests.
    """
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override
    
    client = TestClient(app)
    yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_pokemon_data() -> dict:
    """
    Sample Pokemon data for testing.
    """
    return {
        "name": "Pikachu",
        "number": 25,
        "region": "Kanto"
    }


@pytest.fixture
def sample_pokemon(session: Session, sample_pokemon_data: dict) -> Pokemon:
    """
    Create and persist a sample Pokemon in the test database.
    """
    from blazing.models.pokemon import Region
    
    pokemon = Pokemon(
        name=sample_pokemon_data["name"],
        number=sample_pokemon_data["number"],
        region=Region.kanto
    )
    session.add(pokemon)
    session.commit()
    session.refresh(pokemon)
    
    return pokemon