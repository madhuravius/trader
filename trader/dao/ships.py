from typing import List, Optional, Sequence, Tuple

from sqlalchemy.engine import Engine
from sqlmodel import Field, Session, SQLModel, col, select

from trader.client.ship import Ship as ShipClient
from trader.dao.ship_events import ShipEvent


class Ship(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    call_sign: str
    faction: str
    frame_name: str
    registration_role: str
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
                        registration_role=ship.registration.role,
                        system_symbol=ship.nav.system_symbol,
                        waypoint_symbol=ship.nav.waypoint_symbol,
                    )
                )
        session.commit()


def get_ship(engine: Engine, call_sign: str) -> Optional[Ship]:
    with Session(engine) as session:
        ship_statement = select(Ship).where(Ship.call_sign == call_sign)
        ship = session.exec(ship_statement).one_or_none()
    return ship


def get_ships(engine: Engine) -> Sequence[Ship]:
    with Session(engine) as session:
        ships_statement = select(Ship)
        ships = session.exec(ships_statement).all()
    return ships


def get_ship_events(
    engine: Engine, limit: int, call_sign: Optional[str] = None
) -> Sequence[Tuple[Ship, ShipEvent]]:
    ship_events: Sequence[Tuple[Ship, ShipEvent]] = []
    with Session(engine) as session:
        ship_statement = select(Ship)
        if call_sign:
            ship_statement = ship_statement.where(Ship.call_sign == call_sign)

        for ship in session.exec(ship_statement):
            ship_event_statement = (
                select(Ship, ShipEvent)
                .join(ShipEvent)
                .where(ship.id == ShipEvent.ship_id)
                .order_by(col(ShipEvent.created_at).desc())
                .limit(limit)
            )
            ship_events.append(*session.exec(ship_event_statement).all())
    return ship_events
