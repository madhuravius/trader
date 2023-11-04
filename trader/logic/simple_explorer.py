import os
from time import sleep
from typing import List

from loguru import logger

from trader.logic.common import DEFAULT_INTERNAL_LOOP_INTERVAL, ActionQueue, Common
from trader.queue.action_queue import ActionQueueElement
from trader.roles.explorer import Explorer


class SimpleExplorer(Common):
    """
    Common catch-all set of behavior for probes that will explore and track market data.

    Intended to purge queue on start and will begin from its current location.
    """

    base_priority: int = 1
    explorer: Explorer
    repeat: bool

    def __init__(self, api_key: str, call_sign: str, repeat: bool = False):
        super().__init__()
        self.explorer = Explorer(
            api_key=api_key, call_sign=call_sign, base_priority=self.base_priority
        )
        self.roles = [self.explorer]
        self.repeat = repeat
        self.ship = self.explorer.ship
        self.action_queue = ActionQueue(
            ship=self.ship, queue_name="simple-explorer", purge=True
        )

    def find_optimal_path_and_traverse(self):
        waypoints = self.explorer.find_optimal_path_to_explore()
        self.explorer.traverse_all_waypoints_and_check_markets_and_shipyards(
            waypoints=waypoints
        )

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
                        {"event_name": "simple-explorer-loop.begin"},
                    ),
                    (self.find_optimal_path_and_traverse, {}),
                    (self.log_audit_performance, {}),
                    (
                        self.persist_audit_performance,
                        {"event_name": "simple-explorer-loop.finish"},
                    ),
                    (self.reset_audit_performance, {}),
                ]
                [self.action_queue.enqueue(action) for action in actions]

                while self.action_queue.len():
                    # wait for internal queue to be empty before trying again
                    sleep(DEFAULT_INTERNAL_LOOP_INTERVAL)
            except KeyboardInterrupt:
                os._exit(1)
            except:
                # just log the exception and loop, avoid the crash
                logger.exception

            if not self.repeat:
                break
            iteration += 1
