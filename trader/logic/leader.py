import os
from typing import Callable

from loguru import logger

from trader.logic.common import Common
from trader.logic.simple_miner import SimpleMiner
from trader.logic.simple_trader import SimpleTrader
from trader.queues.action_queue import ActionQueue
from trader.roles.harvester import Harvester
from trader.roles.merchant.merchant import Merchant


class Leader(Common):
    """
    Common catch-all set of behavior for miners that will mine, then go to market and trade.
    It will trade if trading is better, and it will mine and trade if that is better with current
    market prices.

    This effectively behaves as SimpleMiner and SimpleTrader, doing which ever is more profitable
    at the present time.

    Intended to purge queue on start and will begin from its current location.
    """

    base_priority: int = 2
    harvester: Harvester
    merchant: Merchant

    def __init__(self, api_key: str, call_sign: str, repeat: bool = False):
        super().__init__()
        self.harvester = Harvester(
            api_key=api_key, call_sign=call_sign, base_priority=self.base_priority
        )
        self.merchant = Merchant(
            api_key=api_key, call_sign=call_sign, base_priority=self.base_priority
        )
        self.roles = [self.harvester, self.merchant]
        self.repeat = repeat
        self.ship = self.harvester.ship
        self.action_queue = ActionQueue(
            ship=self.ship,
            queue_name="leader",
            purge=True,  # purge on start to avoid functional orphans
        )
        # leader is a superset of other roles and will do the the most immediately needed activity
        # it will either trade, or mine
        self.simple_miner = SimpleMiner(api_key=api_key, call_sign=call_sign, repeat=False)
        self.simple_trader = SimpleTrader(api_key=api_key, call_sign=call_sign, repeat=False)

    def empty_extra_goods(self):
        # if having goods already, should empty first if needed
        self.merchant.reload_ship()
        if self.ship.cargo.units > 0:
            logger.info(
                f"Found extra cargo on {self.ship.symbol}, emptying before starting loop"
            )
            self.merchant.sell_cargo()

    def determine_ideal_activity(self) -> Callable:
        return self.simple_trader.run_loop

    def run_loop(self):
        self.running_loop = True
        iteration = 1
        if self.repeat:
            logger.info(
                "Repeat option enabled, repeating the run loop upon completion!"
            )
        while self.running_loop:
            try:
                if self.repeat:
                    logger.info(
                        f"Starting leader iteration {iteration} of loop for ship {self.ship.symbol}"
                    )
                activity = self.determine_ideal_activity()
                activity()
            except KeyboardInterrupt:
                os._exit(1)
            except Exception as e:
                # just log the exception and loop, avoid the crash
                logger.exception(e)
            if not self.repeat:
                break
            iteration += 1
