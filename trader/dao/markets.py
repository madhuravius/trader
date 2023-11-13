from datetime import UTC, datetime
from typing import List, Optional

from sqlalchemy.engine import Engine
from sqlmodel import Field, Session, SQLModel, select

from trader.client.market import Exchange, Export, Import
from trader.client.market import Market as MarketClient
from trader.client.market import Transaction


class MarketImport(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    symbol: str
    name: str
    description: str
    created_at: datetime = Field(index=True, default=datetime.now(UTC))
    waypoint_symbol: str = Field(index=True)
    system_symbol: str


class MarketExport(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    symbol: str
    name: str
    description: str
    created_at: datetime = Field(index=True, default=datetime.now(UTC))
    waypoint_symbol: str = Field(index=True)
    system_symbol: str


class MarketExchange(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    symbol: str
    name: str
    description: str
    created_at: datetime = Field(index=True, default=datetime.now(UTC))
    waypoint_symbol: str = Field(index=True)
    system_symbol: str


class MarketTransaction(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    ship_symbol: str
    trade_symbol: str
    transaction_type: str
    units: int
    price_per_unit: int
    total_price: int
    created_at: datetime = Field(index=True, default=datetime.now(UTC))
    waypoint_symbol: str = Field(index=True)
    system_symbol: str


class MarketTradeGood(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str
    trade_volume: int
    supply: str
    purchase_price: int
    sell_price: int
    waypoint_symbol: str = Field(index=True)
    system_symbol: str


def upsert_market_import(
    session: Session, market: MarketClient, market_import: Import, system_symbol: str
):
    market_import_id = f"{market_import.symbol}-{market.symbol}"
    upsert = session.exec(
        select(MarketImport).where(MarketImport.id == market_import_id)
    ).one_or_none()
    market_import_creation = MarketImport(
        id=market_import_id,
        name=market_import.name,
        symbol=market_import.symbol,
        description=market_import.description,
        waypoint_symbol=market.symbol,
        system_symbol=system_symbol,
    )

    if upsert:
        [
            setattr(upsert, key, attr)
            for key, attr in market_import_creation.dict().items()
        ]
        session.add(upsert)
    else:
        session.add(market_import_creation)


def upsert_market_export(
    session: Session, market: MarketClient, market_export: Export, system_symbol: str
):
    market_export_id = f"{market_export.symbol}-{market.symbol}"
    upsert = session.exec(
        select(MarketExport).where(MarketExport.id == market_export_id)
    ).one_or_none()
    market_export_creation = MarketExport(
        id=market_export_id,
        name=market_export.name,
        symbol=market_export.symbol,
        description=market_export.description,
        waypoint_symbol=market.symbol,
        system_symbol=system_symbol,
    )

    if upsert:
        [
            setattr(upsert, key, attr)
            for key, attr in market_export_creation.dict().items()
        ]
        session.add(upsert)
    else:
        session.add(market_export_creation)


def upsert_market_exchange(
    session: Session,
    market: MarketClient,
    market_exchange: Exchange,
    system_symbol: str,
):
    market_exchange_id = f"{market_exchange.symbol}-{market.symbol}"
    upsert = session.exec(
        select(MarketExchange).where(MarketExchange.id == market_exchange_id)
    ).one_or_none()
    market_exchange_creation = MarketExchange(
        id=market_exchange_id,
        name=market_exchange.name,
        symbol=market_exchange.symbol,
        description=market_exchange.description,
        waypoint_symbol=market.symbol,
        system_symbol=system_symbol,
    )
    if upsert:
        [
            setattr(upsert, key, attr)
            for key, attr in market_exchange_creation.dict().items()
        ]
        session.add(upsert)
    else:
        session.add(market_exchange_creation)


def upsert_market_transaction(
    session: Session,
    market_transaction: Transaction,
    system_symbol: str,
):
    market_transaction_id = f"{system_symbol}-{market_transaction.trade_symbol}-{market_transaction.ship_symbol}-{market_transaction.timestamp}"
    upsert = session.exec(
        select(MarketTransaction).where(MarketTransaction.id == market_transaction_id)
    ).one_or_none()
    market_transaction_creation = MarketTransaction(
        id=f"{system_symbol}-{market_transaction.trade_symbol}-{market_transaction.ship_symbol}-{market_transaction.timestamp}",
        ship_symbol=market_transaction.ship_symbol,
        waypoint_symbol=market_transaction.waypoint_symbol,
        units=market_transaction.units,
        price_per_unit=market_transaction.price_per_unit,
        total_price=market_transaction.total_price,
        transaction_type=market_transaction.transaction_type,
        trade_symbol=market_transaction.trade_symbol,
        system_symbol=system_symbol,
    )
    if upsert:
        [
            setattr(upsert, key, attr)
            for key, attr in market_transaction_creation.dict().items()
        ]
        session.add(upsert)
    else:
        session.add(market_transaction_creation)


def save_client_market(
    engine: Engine, market: MarketClient, system_symbol: str
) -> None:
    with Session(engine) as session:
        for market_import in market.imports:
            upsert_market_import(
                session=session,
                market=market,
                market_import=market_import,
                system_symbol=system_symbol,
            )
        for market_export in market.exports:
            upsert_market_export(
                session=session,
                market=market,
                market_export=market_export,
                system_symbol=system_symbol,
            )
        for market_exchange in market.exchange:
            upsert_market_exchange(
                session=session,
                market=market,
                market_exchange=market_exchange,
                system_symbol=system_symbol,
            )
        if market.transactions:
            for market_transaction in market.transactions:
                upsert_market_transaction(
                    session=session,
                    market_transaction=market_transaction,
                    system_symbol=system_symbol,
                )
        if market.trade_goods:
            existing_goods = session.exec(
                select(MarketTradeGood).where(
                    MarketTradeGood.waypoint_symbol == market.symbol
                )
            ).all()
            for existing_good in existing_goods:
                session.delete(existing_good)
            session.commit()

            for market_trade_good in market.trade_goods:
                session.add(
                    MarketTradeGood(
                        system_symbol=system_symbol,
                        waypoint_symbol=market.symbol,
                        symbol=market_trade_good.symbol,
                        trade_volume=market_trade_good.trade_volume,
                        supply=market_trade_good.supply,
                        purchase_price=market_trade_good.purchase_price,
                        sell_price=market_trade_good.sell_price,
                    )
                )
        session.commit()


def get_market_trade_goods_by_system(
    engine: Engine, system_symbol: str
) -> List[MarketTradeGood]:
    with Session(engine) as session:
        expression = select(MarketTradeGood).where(
            MarketTradeGood.system_symbol == system_symbol
        )
        return session.exec(expression).all()


def get_market_trade_good_by_waypoint(
    engine: Engine, waypoint_symbol: str, good_symbol: str
) -> MarketTradeGood:
    with Session(engine) as session:
        expression = (
            select(MarketTradeGood)
            .where(MarketTradeGood.waypoint_symbol == waypoint_symbol)
            .where(MarketTradeGood.symbol == good_symbol)
        )
        return session.exec(expression).one()
