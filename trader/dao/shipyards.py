from typing import Optional, Sequence

from sqlalchemy.engine import Engine
from sqlmodel import Field, Session, SQLModel, select

from trader.client.shipyard import ShipTransaction as ShipTransactionClient
from trader.client.shipyard import Shipyard as ShipyardClient
from trader.client.shipyard import ShipyardShip as ShipyardShipClient


class ShipyardShip(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    ship_type: str
    name: str
    description: str
    supply: str
    activity: str
    purchase_price: int
    system_symbol: str
    waypoint_symbol: str


class ShipyardTransaction(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    ship_symbol: str
    price: int
    agent_symbol: str
    system_symbol: str
    waypoint_symbol: str


def upsert_shipyard_ship(
    session: Session,
    shipyard: ShipyardClient,
    shipyard_ship: ShipyardShipClient,
    system_symbol: str,
) -> None:
    shipyard_ship_id = f"{shipyard.symbol}-{shipyard_ship.ship_type}"
    upsert = session.exec(
        select(ShipyardShip).where(ShipyardShip.id == shipyard_ship_id)
    ).one_or_none()
    shipyard_ship_creation = ShipyardShip(
        id=shipyard_ship_id,
        name=shipyard_ship.name,
        ship_type=shipyard_ship.ship_type,
        supply=shipyard_ship.supply,
        activity=shipyard_ship.activity,
        purchase_price=shipyard_ship.purchase_price,
        description=shipyard_ship.description,
        waypoint_symbol=shipyard.symbol,
        system_symbol=system_symbol,
    )

    if upsert:
        [
            setattr(upsert, key, attr)
            for key, attr in shipyard_ship_creation.dict().items()
        ]
        session.add(upsert)
    else:
        session.add(shipyard_ship_creation)


def upsert_shipyard_transaction(
    session: Session,
    shipyard: ShipyardClient,
    shipyard_transaction: ShipTransactionClient,
    system_symbol: str,
) -> None:
    shipyard_transaction_id = f"{shipyard.symbol}-{shipyard_transaction.agent_symbol}-{shipyard_transaction.ship_symbol}-{shipyard_transaction.timestamp}"
    upsert = session.exec(
        select(ShipyardTransaction).where(
            ShipyardTransaction.id == shipyard_transaction_id
        )
    ).one_or_none()
    shipyard_transaction_creation = ShipyardTransaction(
        id=shipyard_transaction_id,
        price=shipyard_transaction.price,
        agent_symbol=shipyard_transaction.agent_symbol,
        ship_symbol=shipyard_transaction.ship_symbol,
        waypoint_symbol=shipyard.symbol,
        system_symbol=system_symbol,
    )

    if upsert:
        [
            setattr(upsert, key, attr)
            for key, attr in shipyard_transaction_creation.dict().items()
        ]
        session.add(upsert)
    else:
        session.add(shipyard_transaction_creation)


def save_client_shipyard(
    engine: Engine, shipyard: ShipyardClient, system_symbol: str
) -> None:
    with Session(engine) as session:
        if shipyard.ships:
            for shipyard_ship in shipyard.ships:
                upsert_shipyard_ship(
                    session=session,
                    shipyard=shipyard,
                    shipyard_ship=shipyard_ship,
                    system_symbol=system_symbol,
                )
        if shipyard.transactions:
            for shipyard_transaction in shipyard.transactions:
                upsert_shipyard_transaction(
                    session=session,
                    shipyard=shipyard,
                    shipyard_transaction=shipyard_transaction,
                    system_symbol=system_symbol,
                )
        session.commit()


def get_shipyard_ships_by_waypoint(
    engine: Engine, waypoint_symbol: str, system_symbol: str
) -> Sequence[ShipyardShip]:
    with Session(engine) as session:
        expression = (
            select(ShipyardShip)
            .where(ShipyardShip.system_symbol == system_symbol)
            .where(ShipyardShip.waypoint_symbol == waypoint_symbol)
        )
        return session.exec(expression).all()
