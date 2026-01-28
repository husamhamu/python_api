"""
Integration tests for Pokemon API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from blazing.models.pokemon import Pokemon, Region


@pytest.mark.integration
class TestPokemonEndpoints:
    """Integration tests for /pokemon endpoints."""
    
    def test_add_pokemon(self, client: TestClient):
        """Test POST /pokemon/ endpoint."""
        response = client.post(
            "/pokemon/",
            json={
                "name": "Bulbasaur",
                "number": 1,
                "region": "Kanto"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Bulbasaur"
        assert data["number"] == 1
        assert data["region"] == "Kanto"
        assert "id" in data
        assert "created_at" in data
    
    def test_add_pokemon_johto_region(self, client: TestClient):
        """Test adding a Pokemon from Johto region."""
        response = client.post(
            "/pokemon/",
            json={
                "name": "Chikorita",
                "number": 152,
                "region": "Johto"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["region"] == "Johto"
    
    def test_get_pokemon_success(self, client: TestClient, sample_pokemon: Pokemon):
        """Test GET /pokemon/{id} endpoint with existing Pokemon."""
        response = client.get(f"/pokemon/{sample_pokemon.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_pokemon.id
        assert data["name"] == sample_pokemon.name
        assert data["number"] == sample_pokemon.number
    
    def test_get_pokemon_not_found(self, client: TestClient):
        """Test GET /pokemon/{id} endpoint with non-existent ID."""
        response = client.get("/pokemon/99999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Pokemon not found"
    
    def test_delete_pokemon_success(self, client: TestClient, sample_pokemon: Pokemon):
        """Test DELETE /pokemon/{id} endpoint with existing Pokemon."""
        pokemon_id = sample_pokemon.id
        
        response = client.delete(f"/pokemon/{pokemon_id}")
        
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        
        # Verify Pokemon is actually deleted
        get_response = client.get(f"/pokemon/{pokemon_id}")
        assert get_response.status_code == 404
    
    def test_delete_pokemon_not_found(self, client: TestClient):
        """Test DELETE /pokemon/{id} endpoint with non-existent ID."""
        response = client.delete("/pokemon/99999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Pokemon not found"
    
    def test_list_pokemon_empty(self, client: TestClient):
        """Test GET /pokemon/ endpoint with no Pokemon in database."""
        response = client.get("/pokemon/")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_pokemon_with_data(self, client: TestClient, session: Session):
        """Test GET /pokemon/ endpoint with multiple Pokemon."""
        # Add multiple Pokemon
        pokemon_list = [
            Pokemon(name="Bulbasaur", number=1, region=Region.kanto),
            Pokemon(name="Charmander", number=4, region=Region.kanto),
            Pokemon(name="Squirtle", number=7, region=Region.kanto),
            Pokemon(name="Chikorita", number=152, region=Region.johto),
        ]
        
        for pokemon in pokemon_list:
            session.add(pokemon)
        session.commit()
        
        response = client.get("/pokemon/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        assert all("name" in p for p in data)
        assert all("number" in p for p in data)
        assert all("region" in p for p in data)
    
    def test_list_pokemon_correct_order(self, client: TestClient, session: Session):
        """Test that list returns Pokemon in insertion order."""
        names = ["Pikachu", "Eevee", "Mewtwo"]
        for name in names:
            pokemon = Pokemon(name=name, number=25, region=Region.kanto)
            session.add(pokemon)
        session.commit()
        
        response = client.get("/pokemon/")
        data = response.json()
        
        returned_names = [p["name"] for p in data]
        assert returned_names == names


@pytest.mark.integration
class TestPokemonEndpointsValidation:
    """Integration tests for Pokemon API validation."""
    
    def test_add_pokemon_missing_fields(self, client: TestClient):
        """Test POST /pokemon/ with missing required fields."""
        response = client.post(
            "/pokemon/",
            json={"name": "Pikachu"}
        )
        
        assert response.status_code == 422
    
    def test_add_pokemon_invalid_region(self, client: TestClient):
        """Test POST /pokemon/ with invalid region."""
        response = client.post(
            "/pokemon/",
            json={
                "name": "Pikachu",
                "number": 25,
                "region": "InvalidRegion"
            }
        )
        
        assert response.status_code == 422
    
    def test_get_pokemon_invalid_id_type(self, client: TestClient):
        """Test GET /pokemon/{id} with non-integer ID."""
        response = client.get("/pokemon/not_a_number")
        
        assert response.status_code == 422


@pytest.mark.integration
class TestPokemonEndpointsEdgeCases:
    """Integration tests for edge cases."""
    
    def test_add_pokemon_duplicate_number(self, client: TestClient):
        """Test adding Pokemon with duplicate number (should be allowed)."""
        pokemon_data = {
            "name": "Pikachu",
            "number": 25,
            "region": "Kanto"
        }
        
        response1 = client.post("/pokemon/", json=pokemon_data)
        response2 = client.post("/pokemon/", json=pokemon_data)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json()["id"] != response2.json()["id"]
    
    def test_pokemon_roundtrip(self, client: TestClient):
        """Test complete CRUD cycle for a Pokemon."""
        # Create
        create_response = client.post(
            "/pokemon/",
            json={
                "name": "Mew",
                "number": 151,
                "region": "Kanto"
            }
        )
        assert create_response.status_code == 200
        pokemon_id = create_response.json()["id"]
        
        # Read
        read_response = client.get(f"/pokemon/{pokemon_id}")
        assert read_response.status_code == 200
        assert read_response.json()["name"] == "Mew"
        
        # List
        list_response = client.get("/pokemon/")
        assert list_response.status_code == 200
        assert any(p["id"] == pokemon_id for p in list_response.json())
        
        # Delete
        delete_response = client.delete(f"/pokemon/{pokemon_id}")
        assert delete_response.status_code == 200
        
        # Verify deletion
        verify_response = client.get(f"/pokemon/{pokemon_id}")
        assert verify_response.status_code == 404