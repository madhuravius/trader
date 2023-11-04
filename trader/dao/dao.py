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
    Waypoint,
    WaypointTrait,
]


class DAO(metaclass=Singleton):
    engine: Engine

    def __init__(self):
        self.ensure_db()

    def ensure_db(self):
        self.engine = create_engine("sqlite:///db.db", echo="SQL_DEBUG" in os.environ)
        SQLModel.metadata.create_all(self.engine)
