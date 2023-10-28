import os

from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, create_engine

from trader.dao.models import CachedRequest
from trader.util.singleton import Singleton

Tables = CachedRequest


class DAO(metaclass=Singleton):
    engine: Engine

    def __init__(self):
        self.ensure_db()

    def ensure_db(self):
        self.engine = create_engine("sqlite:///db.db", echo="DEBUG" in os.environ)
        SQLModel.metadata.create_all(self.engine)
