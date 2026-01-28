"""
Unit tests for the Pokemon model.
"""
from datetime import datetime, timezone

import pytest
from sqlmodel import Session

from blazing.models.pokemon import Pokemon, Region


@pytest.mark.unit
class TestPokemonModel:
    """Test cases for the Pokemon model."""
    
    def test_pokemon_creation(self):
        """Test creating a Pokemon instance."""
        pokemon = Pokemon(
            name="Bulbasaur",
            number=1,
            region=Region.kanto
        )
        
        assert pokemon.name == "Bulbasaur"
        assert pokemon.number == 1
        assert pokemon.region == Region.kanto
        assert pokemon.id is None
    
    def test_pokemon_with_id(self):
        """Test creating a Pokemon with an explicit ID."""
        pokemon = Pokemon(
            id=1,
            name="Charmander",
            number=4,
            region=Region.kanto
        )
        
        assert pokemon.id == 1
        assert pokemon.name == "Charmander"
    
    def test_pokemon_created_at_auto_generated(self):
        """Test that created_at is automatically set."""
        before = datetime.now(timezone.utc)
        pokemon = Pokemon(
            name="Squirtle",
            number=7,
            region=Region.kanto
        )
        after = datetime.now(timezone.utc)
        
        assert pokemon.created_at is not None
        assert before <= pokemon.created_at <= after
    
    def test_pokemon_persistence(self, session: Session):
        """Test saving a Pokemon to the database."""
        pokemon = Pokemon(
            name="Pikachu",
            number=25,
            region=Region.kanto
        )
        
        session.add(pokemon)
        session.commit()
        session.refresh(pokemon)
        
        assert pokemon.id is not None
        assert pokemon.id > 0
    
    def test_pokemon_retrieval(self, session: Session):
        """Test retrieving a Pokemon from the database."""
        pokemon = Pokemon(
            name="Eevee",
            number=133,
            region=Region.kanto
        )
        
        session.add(pokemon)
        session.commit()
        session.refresh(pokemon)
        
        retrieved = session.get(Pokemon, pokemon.id)
        
        assert retrieved is not None
        assert retrieved.name == "Eevee"
        assert retrieved.number == 133
        assert retrieved.region == Region.kanto
    
    def test_pokemon_johto_region(self, session: Session):
        """Test creating a Pokemon from Johto region."""
        pokemon = Pokemon(
            name="Chikorita",
            number=152,
            region=Region.johto
        )
        
        session.add(pokemon)
        session.commit()
        session.refresh(pokemon)
        
        assert pokemon.region == Region.johto
        assert pokemon.region.value == "Johto"


@pytest.mark.unit
class TestRegionEnum:
    """Test cases for the Region enum."""
    
    def test_region_enum_values(self):
        """Test that Region enum has correct values."""
        assert Region.kanto.value == "Kanto"
        assert Region.johto.value == "Johto"
    
    def test_region_enum_members(self):
        """Test that Region enum has correct members."""
        regions = list(Region)
        assert len(regions) == 2
        assert Region.kanto in regions
        assert Region.johto in regions