"""
Pokemon routes with comprehensive logging.
"""
from fastapi import APIRouter, HTTPException, Request
from sqlmodel import select

from blazing.db import SessionType
from blazing.models.pokemon import Pokemon, PokemonBase
from blazing.logging.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/pokemon",
    tags=["pokemon"],
)


@router.post("/", response_model=Pokemon)
def add_pokemon(pokemon_data: PokemonBase, session: SessionType, request: Request) -> Pokemon:
    """
    Create a new Pokemon.
    
    Args:
        pokemon_data: Pokemon data to create
        session: Database session
        request: HTTP request object
    
    Returns:
        Created Pokemon
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.info(
        f"Creating new Pokemon: {pokemon_data.name}",
        extra={
            "request_id": request_id,
            "pokemon_name": pokemon_data.name,
            "pokemon_number": pokemon_data.number,
            "region": pokemon_data.region.value,
        }
    )
    
    try:
        pokemon = Pokemon.model_validate(pokemon_data)
        session.add(pokemon)
        session.commit()
        session.refresh(pokemon)
        
        logger.info(
            f"Pokemon created successfully: {pokemon.name} (ID: {pokemon.id})",
            extra={
                "request_id": request_id,
                "pokemon_id": pokemon.id,
                "pokemon_name": pokemon.name,
            }
        )
        
        return pokemon
    
    except Exception as e:
        logger.error(
            f"Failed to create Pokemon: {str(e)}",
            extra={
                "request_id": request_id,
                "pokemon_name": pokemon_data.name,
            },
            exc_info=True
        )
        session.rollback()
        raise


@router.get("/{pokemon_id}", response_model=Pokemon)
def get_pokemon(pokemon_id: int, session: SessionType, request: Request) -> Pokemon:
    """
    Get a Pokemon by ID.
    
    Args:
        pokemon_id: ID of the Pokemon to retrieve
        session: Database session
        request: HTTP request object
    
    Returns:
        Pokemon with the given ID
    
    Raises:
        HTTPException: If Pokemon not found
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.debug(
        f"Fetching Pokemon with ID: {pokemon_id}",
        extra={"request_id": request_id, "pokemon_id": pokemon_id}
    )
    
    pokemon = session.get(Pokemon, pokemon_id)
    
    if not pokemon:
        logger.warning(
            f"Pokemon not found: ID {pokemon_id}",
            extra={"request_id": request_id, "pokemon_id": pokemon_id}
        )
        raise HTTPException(status_code=404, detail="Pokemon not found")
    
    logger.debug(
        f"Pokemon found: {pokemon.name} (ID: {pokemon.id})",
        extra={
            "request_id": request_id,
            "pokemon_id": pokemon.id,
            "pokemon_name": pokemon.name,
        }
    )
    
    return pokemon


@router.delete("/{pokemon_id}")
def delete_pokemon(pokemon_id: int, session: SessionType, request: Request):
    """
    Delete a Pokemon by ID.
    
    Args:
        pokemon_id: ID of the Pokemon to delete
        session: Database session
        request: HTTP request object
    
    Returns:
        Success message
    
    Raises:
        HTTPException: If Pokemon not found
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.info(
        f"Attempting to delete Pokemon with ID: {pokemon_id}",
        extra={"request_id": request_id, "pokemon_id": pokemon_id}
    )
    
    try:
        pokemon = get_pokemon(pokemon_id, session, request)
    except HTTPException:
        logger.warning(
            f"Cannot delete - Pokemon not found: ID {pokemon_id}",
            extra={"request_id": request_id, "pokemon_id": pokemon_id}
        )
        raise
    
    pokemon_name = pokemon.name
    
    try:
        session.delete(pokemon)
        session.commit()
        
        logger.info(
            f"Pokemon deleted successfully: {pokemon_name} (ID: {pokemon_id})",
            extra={
                "request_id": request_id,
                "pokemon_id": pokemon_id,
                "pokemon_name": pokemon_name,
            }
        )
        
        return {"ok": True}
    
    except Exception as e:
        logger.error(
            f"Failed to delete Pokemon: {str(e)}",
            extra={
                "request_id": request_id,
                "pokemon_id": pokemon_id,
            },
            exc_info=True
        )
        session.rollback()
        raise


@router.get("/", response_model=list[Pokemon])
def list_pokemon(session: SessionType, request: Request) -> list[Pokemon]:
    """
    List all Pokemon.
    
    Args:
        session: Database session
        request: HTTP request object
    
    Returns:
        List of all Pokemon
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.debug(
        "Fetching all Pokemon",
        extra={"request_id": request_id}
    )
    
    try:
        pokemon_list = list(session.exec(select(Pokemon)).all())
        
        logger.info(
            f"Retrieved {len(pokemon_list)} Pokemon",
            extra={
                "request_id": request_id,
                "count": len(pokemon_list),
            }
        )
        
        return pokemon_list
    
    except Exception as e:
        logger.error(
            f"Failed to list Pokemon: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise


def get_integer() -> int:
    """
    Helper function for testing.
    
    Returns:
        The integer 42
    """
    logger.debug("get_integer called")
    return 42