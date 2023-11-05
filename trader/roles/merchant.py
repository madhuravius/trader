from dataclasses import dataclass
from typing import Any, List, Optional

import pandas as pd
from dataclass_wizard import JSONWizard
from loguru import logger

from trader.dao.markets import get_market_trade_goods_by_system
from trader.roles.common import Common

# do not spend more than X% of the current account on any purchase
MAXIMUM_PERCENT_OF_ACCOUNT_PURCHASE = 0.25


@dataclass
class ArbitrageOpportunity(JSONWizard):
    purchase_waypoint_symbol: str
    purchase_supply: str
    purchase_price: int
    sell_waypoint_symbol: str
    sell_supply: str
    sell_price: int
    trade_good_symbol: str
    purchase_system_symbol: Optional[str] = None
    sell_system_symbol: Optional[str] = None
    profit: Optional[int] = None
    percent_profit: Optional[float] = None


class Merchant(Common):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def seek_arbitrage_opportunities_in_system(self) -> List[ArbitrageOpportunity]:
        """
        Will look for maximum arbitrage opportunities in terms of percentage in the ship's
        current system.
        """
        logger.info(
            f"Ship {self.ship.symbol} seeking arbitrage opportunities to make sales"
        )
        self.reload_ship()
        market_trade_goods = get_market_trade_goods_by_system(
            engine=self.dao.engine, system_symbol=self.ship.nav.system_symbol
        )

        arbitrage_opportunities: List[ArbitrageOpportunity] = []
        pd_goods = pd.DataFrame([t.dict() for t in market_trade_goods])
        good_names = pd_goods["symbol"].unique()
        for good_name in good_names:
            good_rows: Any = pd_goods[pd_goods["symbol"] == good_name]
            lowest_purchase_price_loc = good_rows["purchase_price"].idxmin()
            highest_sale_price_loc = good_rows["sell_price"].idxmax()
            purchase_row = good_rows.loc[lowest_purchase_price_loc]
            sale_row = good_rows.loc[highest_sale_price_loc]
            arbitrage_opportunities.append(
                ArbitrageOpportunity(
                    purchase_waypoint_symbol=purchase_row.waypoint_symbol,
                    purchase_price=purchase_row.purchase_price,
                    purchase_supply=purchase_row.supply,
                    sell_waypoint_symbol=sale_row.waypoint_symbol,
                    sell_price=sale_row.sell_price,
                    sell_supply=sale_row.supply,
                    trade_good_symbol=good_name,
                )
            )

        # compute profit and ratio, and spit it out for determination
        arbitrage_data = pd.DataFrame([t.to_dict() for t in arbitrage_opportunities])
        arbitrage_data["profit"] = arbitrage_data["sellPrice"].astype(
            int
        ) - arbitrage_data["purchasePrice"].astype(int)
        arbitrage_data["percentProfit"] = arbitrage_data["profit"] / arbitrage_data[
            "purchasePrice"
        ].astype(int)
        most_profitable_trades = arbitrage_data.sort_values(
            "percentProfit", ascending=False
        )
        return [
            ArbitrageOpportunity.from_dict(trade.to_dict())
            for _, trade in most_profitable_trades.head(10).iterrows()
        ]

    def buy_cargo(self, waypoint_symbol: str, good_symbol: str, units: int):
        pass

    def sell_cargo(self):
        """
        Naively attempts to liquidate everything in cargo
        """
        logger.info(f"Ship {self.ship.symbol} starting to navigate to makes sales")
        goods_to_sell = [inventory.symbol for inventory in self.ship.cargo.inventory]
        closest_market_location = self.find_closest_market_location_with_goods(
            goods=goods_to_sell
        )

        self.refuel_and_navigate_to_waypoint(
            waypoint_symbol=closest_market_location.symbol,
            system_symbol=closest_market_location.system_symbol,
        )
        self.client.dock(call_sign=self.ship.symbol)
        self.reload_ship()
        self.refresh_market_data(
            system_symbol=closest_market_location.system_symbol,
            waypoint_symbol=closest_market_location.symbol,
        )

        for inventory in self.ship.cargo.inventory:
            logger.info(
                f"Ship {self.ship.symbol} selling {inventory.units} units of {inventory.symbol}"
            )
            sale_response = self.client.sell(
                call_sign=self.ship.symbol,
                symbol=inventory.symbol,
                units=inventory.units,
            )
            if sale_response.data:
                self.add_to_credits_earned(
                    credits=sale_response.data.transaction.total_price
                )
