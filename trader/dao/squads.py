from typing import List, Optional

from sqlmodel import Column, Field, ForeignKey, Relationship, SQLModel, String


class Squad(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    name: str
    squad_members: List["SquadMember"] = Relationship(
        sa_relationship_kwargs={
            "cascade": "all, delete",
        }
    )


class SquadMember(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    order: int
    ship_id: Optional[str] = Field(
        default=None,
        sa_column=Column(String, ForeignKey("ship.id", ondelete="CASCADE")),
    )
    squad_id: Optional[str] = Field(
        default=None,
        sa_column=Column(String, ForeignKey("squad.id", ondelete="CASCADE")),
    )

    squad: Optional[Squad] = Relationship(back_populates="squad_members")
