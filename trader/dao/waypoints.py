from typing import List, Optional

from sqlalchemy.engine import Engine
from sqlalchemy.orm import selectinload
from sqlmodel import (
    Column,
    Field,
    ForeignKey,
    Relationship,
    Session,
    SQLModel,
    String,
    select,
)

from trader.client.waypoint import Waypoint as WaypointClient


class Waypoint(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    waypoint_system_type: Optional[str] = Field(
        sa_column=Column("type", String, default=None)
    )
    system_symbol: str
    x: int
    y: int
    symbol: str
    traits: List["WaypointTrait"] = Relationship(
        sa_relationship_kwargs={
            "cascade": "all, delete",
        }
    )


class WaypointTrait(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str
    waypoint_id: Optional[str] = Field(
        default=None,
        sa_column=Column(String, ForeignKey("waypoint.id", ondelete="CASCADE")),
    )
    name: str
    description: str
    waypoint: Optional[Waypoint] = Relationship(back_populates="traits")


def save_client_waypoints(engine: Engine, waypoints: List[WaypointClient]):
    with Session(engine) as session:
        for waypoint in waypoints:
            upsert = session.exec(
                select(Waypoint).where(Waypoint.id == waypoint.symbol)
            ).one_or_none()
            if upsert:
                [setattr(upsert, key, attr) for key, attr in upsert.dict().items()]
                [session.delete(trait) for trait in upsert.traits]
                upsert.traits = [
                    WaypointTrait(
                        symbol=trait.symbol,
                        waypoint=upsert,
                        name=trait.name,
                        description=trait.description,
                    )
                    for trait in waypoint.traits
                ]
                session.add(upsert)
            else:
                waypoint_to_save = Waypoint(
                    id=waypoint.symbol,
                    waypoint_system_type=waypoint.waypoint_system_type,
                    system_symbol=waypoint.system_symbol,
                    x=waypoint.x,
                    y=waypoint.y,
                    symbol=waypoint.symbol,
                )
                waypoint_to_save.traits = [
                    WaypointTrait(
                        symbol=trait.symbol,
                        waypoint=waypoint_to_save,
                        name=trait.name,
                        description=trait.description,
                    )
                    for trait in waypoint.traits
                ]
                session.add(waypoint_to_save)

        session.commit()


def get_waypoints_by_system_symbol(
    engine: Engine, system_symbol: str
) -> List[Waypoint]:
    waypoints: List[Waypoint] = []
    with Session(engine) as session:
        expression = (
            select(Waypoint)
            .where(Waypoint.system_symbol == system_symbol)
            .options(selectinload(Waypoint.traits))
        )
        waypoints = session.exec(expression).all()

    return waypoints
