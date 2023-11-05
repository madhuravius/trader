import os

from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, create_engine

from trader.dao.agent_histories import AgentHistory
from trader.dao.markets import (
    MarketExchange,
    MarketExport,
    MarketImport,
    MarketTransaction,
)
from trader.dao.queues import Queue, QueueEntry
from trader.dao.requests import CachedRequest
from trader.dao.ship_events import ShipEvent
from trader.dao.ships import Ship
from trader.dao.shipyards import ShipyardShip, ShipyardTransaction
from trader.dao.squads import Squad, SquadMember
from trader.dao.waypoints import Waypoint, WaypointTrait
from trader.util.singleton import Singleton

Tables = [
    AgentHistory,
    CachedRequest,
    MarketExchange,
    MarketExport,
    MarketImport,
    MarketTransaction,
    Queue,
    QueueEntry,
    Ship,
    ShipEvent,
    ShipyardShip,
    ShipyardTransaction,
    Squad,
    SquadMember,
    Waypoint,
    WaypointTrait,
]

DB_URL = os.environ.get("DB_URL", "sqlite:///db.db")


class DAO(metaclass=Singleton):
    db_url: str
    engine: Engine

    def __init__(self):
        self.db_url = DB_URL
        self.ensure_db()

    def ensure_db(self):
        self.engine = create_engine(self.db_url, echo="SQL_DEBUG" in os.environ)
        SQLModel.metadata.create_all(self.engine)
