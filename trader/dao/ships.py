from typing import List, Optional

from sqlalchemy.engine import Engine
from sqlmodel import Field, Session, SQLModel, select

from trader.client.ship import Ship as ShipClient


class Ship(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    call_sign: str
    faction: str
    frame_name: str
    system_symbol: str
    waypoint_symbol: str


def save_client_ships(engine: Engine, ships: List[ShipClient]) -> None:
    with Session(engine) as session:
        for ship in ships:
            upsert = session.exec(
                select(Ship).where(Ship.id == ship.symbol)
            ).one_or_none()
            if upsert:
                [
                    setattr(upsert, key, attr)
                    for key, attr in (
                        {
                            "system_symbol": ship.nav.system_symbol,
                            "waypoint_symbol": ship.nav.waypoint_symbol,
                        }
                    ).items()
                ]
                session.add(upsert)
            else:
                session.add(
                    Ship(
                        id=ship.symbol,
                        call_sign=ship.symbol,
                        faction=ship.registration.faction_symbol,
                        frame_name=ship.frame.name,
                        system_symbol=ship.nav.system_symbol,
                        waypoint_symbol=ship.nav.waypoint_symbol,
                    )
                )
        session.commit()
