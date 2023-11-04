from loguru import logger

from trader.roles.common import Common


class Merchant(Common):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def sell_cargo(self):
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
