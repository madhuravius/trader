from typing import List, Optional

from loguru import logger

from trader.dao.markets import (
    get_market_trade_good_by_waypoint,
    get_market_trade_goods_by_system,
)
from trader.dao.waypoints import get_waypoints_by_system_symbol
from trader.exceptions import TraderException
from trader.roles.common import Common
from trader.roles.merchant.finder import (
    ArbitrageOpportunity,
    generate_arbitrage_opportunities,
)

# do not spend more than X% of the current account on any purchase
MAXIMUM_PERCENT_OF_ACCOUNT_PURCHASE = 0.25


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
        waypoints = get_waypoints_by_system_symbol(
            engine=self.dao.engine, system_symbol=self.ship.nav.system_symbol
        )
        return generate_arbitrage_opportunities(market_trade_goods, waypoints=waypoints)

    def buy_cargo(
        self,
        waypoint_symbol: str,
        system_symbol: str,
        good_symbol: str,
        units: Optional[int] = None,
    ):
        """
        Simple utility function to jump to a specific location and buy cargo
        """
        logger.info(
            f"Ship {self.ship.symbol} starting to navigate to makes purchases of {good_symbol} ({units} units)"
        )
        self.refuel_and_navigate_to_waypoint(
            waypoint_symbol=waypoint_symbol,
            system_symbol=system_symbol,
        )
        self.client.dock(call_sign=self.ship.symbol)
        self.reload_ship()
        self.refresh_market_data(
            waypoint_symbol=waypoint_symbol,
            system_symbol=system_symbol,
        )
        trade_good_at_location = get_market_trade_good_by_waypoint(
            engine=self.dao.engine,
            waypoint_symbol=waypoint_symbol,
            good_symbol=good_symbol,
        )
        cargo_space_left = self.ship.cargo.capacity - self.ship.cargo.units
        if units is None:
            maximum_amount_to_buy = (
                MAXIMUM_PERCENT_OF_ACCOUNT_PURCHASE * self.agent.credits
            )
            cost_per_good: int = get_market_trade_good_by_waypoint(
                engine=self.dao.engine,
                waypoint_symbol=waypoint_symbol,
                good_symbol=good_symbol,
            ).purchase_price
            units = min(
                [
                    int(maximum_amount_to_buy / cost_per_good),
                    cargo_space_left,
                ]
            )

        # TODO - persist units bought into map, so we know how much to sell
        good_maximum_volume = trade_good_at_location.trade_volume
        purchased = 0

        while purchased < units:
            number_to_buy = good_maximum_volume
            if good_maximum_volume > cargo_space_left:
                # ex, 5 to buy due ot space constraint, but trade volume is 10, we must buy 5
                number_to_buy = cargo_space_left

            logger.info(
                f"Ship {self.ship.symbol} buying {good_maximum_volume} ({purchased} of {units}) units of {good_symbol}"
            )
            buy_response = self.client.buy(
                call_sign=self.ship.symbol,
                symbol=good_symbol,
                units=number_to_buy,
            )
            if buy_response.data:
                self.add_to_credits_spent(
                    credits=buy_response.data.transaction.total_price
                )
            purchased += number_to_buy

    def sell_cargo(
        self,
        waypoint_symbol: Optional[str] = None,
        system_symbol: Optional[str] = None,
        liquidate_inventory: Optional[bool] = True,
        good_symbol: Optional[str] = None,
        units: Optional[int] = None,
    ):
        """
        Naively attempts to liquidate everything in cargo. If liquidate_inventory is set to False, you
        must provide a good symbol and unit to proceed or errors will raise!

        If preferred location is specified, it will try to honor that request.
        """
        if not liquidate_inventory and not good_symbol and not units:
            raise TraderException(
                "Error - requested sale that avoided liquidating inventory, but also "
                "failed to provide which good to sell and the number of units"
            )

        if liquidate_inventory and not self.ship.cargo.units:
            # nothing to do, just returning
            logger.warning(
                f"Ship {self.ship.symbol} has no cargo to sell! Empty inventory"
            )
            return

        logger.info(f"Ship {self.ship.symbol} starting to navigate to makes sales")
        # TODO - try to sell as much as possible and construct a group route in case one
        #        location does not accept all goods

        goods_to_sell = [inventory.symbol for inventory in self.ship.cargo.inventory]

        if waypoint_symbol is None or system_symbol is None:
            closest_market_location = self.find_closest_market_location_with_goods(
                goods=goods_to_sell
            )
            waypoint_symbol = closest_market_location.symbol
            system_symbol = closest_market_location.system_symbol

        self.refuel_and_navigate_to_waypoint(
            system_symbol=system_symbol,
            waypoint_symbol=waypoint_symbol,
        )
        self.client.dock(call_sign=self.ship.symbol)
        self.reload_ship()
        self.refresh_market_data(
            system_symbol=system_symbol,
            waypoint_symbol=waypoint_symbol,
        )

        if liquidate_inventory:
            for inventory in self.ship.cargo.inventory:
                trade_good_at_location = get_market_trade_good_by_waypoint(
                    engine=self.dao.engine,
                    waypoint_symbol=waypoint_symbol,
                    good_symbol=inventory.symbol,
                )
                current_units = inventory.units
                while current_units > 0:
                    units = min(
                        [
                            inventory.units,
                            trade_good_at_location.trade_volume,
                        ]
                    )
                    logger.info(
                        f"Ship {self.ship.symbol} selling {units} units ({inventory.units - current_units} of {current_units})"
                    )
                    sale_response = self.client.sell(
                        call_sign=self.ship.symbol,
                        symbol=inventory.symbol,
                        units=units,
                    )
                    current_units -= units
                    if sale_response.data:
                        self.add_to_credits_earned(
                            credits=sale_response.data.transaction.total_price
                        )