from threading import Thread
from time import sleep
from typing import Any, Callable, Dict, Optional, Tuple

from loguru import logger

from trader.client.ship import Ship
from trader.queue.queue import Queue

MAXIMUM_RETRIES_PER_ACTION = 3
DEFAULT_QUEUE_POLLING_INTERVAL = 0.25

ActionQueueElement = Tuple[Callable, Dict[str, Any]]


class ActionQueue:
    """
    Utility class to ensure functions are execute in order for a given ship.
    This is used to break up possible work and more importantly, allow commands
    to be diverted on a given ship.

    WARNING - if this becomes a distributed application, make sure the Queue
    lives alongside this caller per client. Do not allow this to diverge or you
    will have a bad time as the functions are stored in memory.
    """

    ship: Ship
    queue: Queue
    queue_id: str

    def __init__(
        self, ship: Ship, queue_name: str, purge: Optional[bool] = False
    ) -> None:
        self.ship = ship
        self.queue_id = f"{self.ship.symbol}-{queue_name}"
        self.queue = Queue(queue_id=self.queue_id, queue_name=queue_name)
        if purge:
            self.queue.purge()
        thread = Thread(target=self.run_loop)
        thread.setDaemon(True)
        thread.start()

    def dequeue(self):
        (action, data) = self.queue.pop()
        if action:
            self.execute(action=action, data=data)
        else:
            logger.warning(f"Got an empty request to execute on {self.queue_id}")

    def enqueue(self, action: ActionQueueElement):
        func, data = action
        self.queue.append(function=func, data=data)

    def execute(self, action: Callable, data: Dict[str, Any]):
        attempt = 0
        while True:
            try:
                return action(**data)
            except:
                if attempt < MAXIMUM_RETRIES_PER_ACTION:
                    attempt += 1
                    sleep(3)
                    continue
                raise

    def len(self):
        return self.queue.len()

    def run_loop(self):
        while True:
            try:
                if self.len():
                    self.dequeue()
            except Exception as e:
                logger.exception(e)
            sleep(DEFAULT_QUEUE_POLLING_INTERVAL)
