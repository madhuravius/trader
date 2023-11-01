from datetime import datetime
from typing import Optional

from sqlalchemy.engine import Engine
from sqlmodel import Field, Session, SQLModel

from trader.client.market import Market as MarketClient


class MarketImport(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str
    name: str
    description: str
    created_at: datetime = Field(index=True, default=datetime.utcnow())
    waypoint_symbol: str = Field(index=True)
    system_symbol: str


class MarketExport(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str
    name: str
    description: str
    created_at: datetime = Field(index=True, default=datetime.utcnow())
    waypoint_symbol: str = Field(index=True)
    system_symbol: str


class MarketExchange(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str
    name: str
    description: str
    created_at: datetime = Field(index=True, default=datetime.utcnow())
    waypoint_symbol: str = Field(index=True)
    system_symbol: str


class MarketTransaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ship_symbol: str
    trade_symbol: str
    transaction_type: str
    units: int
    price_per_unit: int
    total_price: int
    created_at: datetime = Field(index=True, default=datetime.utcnow())
    waypoint_symbol: str = Field(index=True)
    system_symbol: str


def save_client_market(
    engine: Engine, market: MarketClient, system_symbol: str
) -> None:
    with Session(engine) as session:
        for market_import in market.imports:
            session.add(
                MarketImport(
                    name=market_import.name,
                    symbol=market_import.symbol,
                    description=market_import.description,
                    created_at=datetime.utcnow(),
                    waypoint_symbol=market.symbol,
                    system_symbol=system_symbol,
                )
            )
        for market_export in market.exports:
            session.add(
                MarketExport(
                    name=market_export.name,
                    symbol=market_export.symbol,
                    description=market_export.description,
                    created_at=datetime.utcnow(),
                    waypoint_symbol=market.symbol,
                    system_symbol=system_symbol,
                )
            )
        for market_exchange in market.exchange:
            session.add(
                MarketExport(
                    name=market_exchange.name,
                    symbol=market_exchange.symbol,
                    description=market_exchange.description,
                    created_at=datetime.utcnow(),
                    waypoint_symbol=market.symbol,
                    system_symbol=system_symbol,
                )
            )
        if market.transactions:
            for market_transaction in market.transactions:
                MarketTransaction(
                    ship_symbol=market_transaction.ship_symbol,
                    waypoint_symbol=market_transaction.waypoint_symbol,
                    units=market_transaction.units,
                    price_per_unit=market_transaction.price_per_unit,
                    total_price=market_transaction.total_price,
                    transaction_type=market_transaction.transaction_type,
                    trade_symbol=market_transaction.trade_symbol,
                    system_symbol=system_symbol,
                )
        session.commit()
