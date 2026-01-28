from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel

import enum


class Region(str, enum.Enum):
    kanto = "Kanto"
    johto = "Johto"

class PokemonBase(SQLModel):
    name: str
    number: int
    region: Region

class Pokemon(PokemonBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

