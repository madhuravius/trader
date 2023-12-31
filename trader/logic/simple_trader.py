import os
from time import sleep
from typing import List, cast

from loguru import logger

from trader.dao.markets import get_market_trade_goods_by_system
from trader.dao.waypoints import get_waypoints_by_system_symbol
from trader.exceptions import TraderException
from trader.logic.common import DEFAULT_INTERNAL_LOOP_INTERVAL, Common
from trader.queues.action_queue import (
    ActionQueue,
    ActionQueueElement,
    ActionQueueParameters,
)
from trader.roles.merchant.finder import find_most_profitable_trade_in_system
from trader.roles.merchant.merchant import MAXIMUM_PERCENT_OF_ACCOUNT_PURCHASE, Merchant


class SimpleTrader(Common):
    """
    Simple trading behavior for ships with cargo holds to try their best to
    buy low and sell high.

    Intended to purge queue on start and will begin from its current location.
    """

    base_priority: int = 2

    def __init__(self, api_key: str, call_sign: str, repeat: bool = False):
        super().__init__()
        self.merchant = Merchant(
            api_key=api_key, call_sign=call_sign, base_priority=self.base_priority
        )
        self.roles = [self.merchant]
        self.repeat = repeat
        self.ship = self.merchant.ship
        self.action_queue = ActionQueue(
            ship=self.ship,
            queue_name="simple-trader",
            purge=True,  # purge on start to avoid functional orphans
        )

    def empty_extra_goods(self):
        # if having goods already, should empty first if needed
        self.merchant.reload_ship()
        if self.ship.cargo.units > 0:
            logger.info(
                f"Found extra cargo on {self.ship.symbol}, emptying before starting loop"
            )
            self.merchant.sell_cargo()

    def begin_trading_cycle(self) -> ActionQueueParameters:
        trading_cycle_data: ActionQueueParameters = {}
        waypoints = get_waypoints_by_system_symbol(
            engine=self.merchant.dao.engine,
            system_symbol=self.merchant.ship.nav.system_symbol,
        )
        trade_goods = get_market_trade_goods_by_system(
            engine=self.merchant.dao.engine,
            system_symbol=self.merchant.ship.nav.system_symbol,
        )
        most_profitable_trade = find_most_profitable_trade_in_system(
            maximum_purchase_price=MAXIMUM_PERCENT_OF_ACCOUNT_PURCHASE
            * self.merchant.agent.credits,
            trade_goods=trade_goods,
            waypoints=waypoints,
            prefer_within_cluster=True,
        )
        if most_profitable_trade:
            trading_cycle_data[
                "buy_waypoint_symbol"
            ] = most_profitable_trade.purchase_waypoint.symbol
            trading_cycle_data[
                "buy_system_symbol"
            ] = most_profitable_trade.purchase_waypoint.system_symbol
            trading_cycle_data[
                "sell_waypoint_symbol"
            ] = most_profitable_trade.sell_waypoint.symbol
            trading_cycle_data[
                "sell_system_symbol"
            ] = most_profitable_trade.sell_waypoint.system_symbol
            trading_cycle_data["good_symbol"] = most_profitable_trade.trade_good_symbol
        else:
            raise TraderException("Unable to find profitable trade to continue")

        return trading_cycle_data

    def translate_trading_cycle_to_buy(
        self, **trading_cycle_data: ActionQueueParameters
    ):
        params = {
            "waypoint_symbol": cast(str, trading_cycle_data["buy_waypoint_symbol"]),
            "system_symbol": cast(str, trading_cycle_data["buy_system_symbol"]),
            "good_symbol": cast(str, trading_cycle_data["good_symbol"]),
            "units": None,
        }
        self.merchant.buy_cargo(**params)

    def translate_trading_cycle_to_sell(
        self, **trading_cycle_data: ActionQueueParameters
    ):
        params = {
            "waypoint_symbol": cast(str, trading_cycle_data["sell_waypoint_symbol"]),
            "system_symbol": cast(str, trading_cycle_data["sell_system_symbol"]),
            "liquidate_inventory": True,
        }
        self.merchant.sell_cargo(**params)

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
                        f"Starting iteration {iteration} of loop for ship {self.ship.symbol}"
                    )

                actions: List[ActionQueueElement] = [
                    (
                        self.persist_audit_performance,
                        {"event_name": "simple-trader-loop.begin"},
                    ),
                    (self.empty_extra_goods, {}),
                    (
                        self.begin_trading_cycle,
                        {},
                    ),
                    (
                        self.persist_audit_performance,
                        {"event_name": "simple-trader-loop.buy"},
                    ),
                    (
                        self.translate_trading_cycle_to_buy,
                        {},
                    ),
                    (
                        self.persist_audit_performance,
                        {"event_name": "simple-trader-loop.sell"},
                    ),
                    (
                        self.translate_trading_cycle_to_sell,
                        {},
                    ),
                    (self.log_audit_performance, {}),
                    (
                        self.persist_audit_performance,
                        {"event_name": "simple-trader-loop.finish"},
                    ),
                    (self.reset_audit_performance, {}),
                    (self.action_queue.reset_outputs, {}),
                ]
                [self.action_queue.enqueue(action) for action in actions]

                while self.action_queue.len():
                    # wait for internal queue to be empty before trying again
                    sleep(DEFAULT_INTERNAL_LOOP_INTERVAL)
            except KeyboardInterrupt:
                os._exit(1)
            except Exception as e:
                # just log the exception and loop, avoid the crash
                logger.exception(e)
            if not self.repeat:
                break
            iteration += 1
