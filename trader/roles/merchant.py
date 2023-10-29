from loguru import logger

from trader.roles.common import Common


class Merchant(Common):
    def sell_cargo(self):
        self.refuel_ship()

        logger.info(f"Ship {self.ship.symbol} starting to navigate to makes sales")
        goods_to_sell = [inventory.symbol for inventory in self.ship.cargo.inventory]
        closest_market_location = self.find_closest_market_location_with_goods(
            goods=goods_to_sell
        )
        self.navigate_to_waypoint(waypoint_symbol=closest_market_location.symbol)
        self.client.dock(call_sign=self.ship.symbol)

        for inventory in self.ship.cargo.inventory:
            logger.info(
                f"Ship {self.ship.symbol} selling {inventory.units} units of {inventory.symbol}"
            )
            self.client.sell(
                call_sign=self.ship.symbol,
                symbol=inventory.symbol,
                units=inventory.units,
            )
