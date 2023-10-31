import os

from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, create_engine

from trader.dao.agent_history import AgentHistory
from trader.dao.requests import CachedRequest
from trader.dao.ship_events import ShipEvent
from trader.dao.ships import Ship
from trader.util.singleton import Singleton

Tables = [AgentHistory, CachedRequest, Ship, ShipEvent]


class DAO(metaclass=Singleton):
    engine: Engine

    def __init__(self):
        self.ensure_db()

    def ensure_db(self):
        self.engine = create_engine("sqlite:///db.db", echo="DEBUG" in os.environ)
        SQLModel.metadata.create_all(self.engine)
