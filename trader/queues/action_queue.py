from threading import Thread
from time import sleep
from typing import Callable, Dict, Optional, Tuple

from loguru import logger

from trader.client.ship import Ship
from trader.queues.base_queue import Queue

MAXIMUM_RETRIES_PER_ACTION = 3
DEFAULT_QUEUE_POLLING_INTERVAL = 0.25

ActionQueueParameters = Dict[str, int | float | str | None]
ActionCallable = Callable[..., ActionQueueParameters | None]
ActionQueueElement = Tuple[ActionCallable, ActionQueueParameters]


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
    outputs: ActionQueueParameters = {}

    def __init__(
        self,
        ship: Ship,
        queue_name: str,
        purge: Optional[bool] = False,
        disable_background_processes: bool = False,
    ) -> None:
        self.ship = ship
        self.queue_id = f"{self.ship.symbol}-{queue_name}"
        self.queue = Queue(queue_id=self.queue_id, queue_name=queue_name)
        if purge:
            self.queue.purge()
        if not disable_background_processes:
            thread = Thread(target=self.run_loop)
            thread.daemon = True
            thread.start()

    def dequeue(self):
        (action, data) = self.queue.pop()
        if action:
            output = self.execute(action=action, data=data)
            if output:
                self.outputs = {**self.outputs, **output}
        else:
            logger.warning(f"Got an empty request to execute on {self.queue_id}")

    def enqueue(self, action: ActionQueueElement):
        func, data = action
        self.queue.append(function=func, data=data)

    def execute(self, action: ActionCallable, data: ActionQueueParameters):
        attempt = 0
        while True:
            try:
                return action(**{**self.outputs, **data})
            except:
                if attempt < MAXIMUM_RETRIES_PER_ACTION:
                    attempt += 1
                    sleep(3)
                    continue
                # TODO: When more stable, should probably purge the queue and start over
                raise

    def len(self):
        return self.queue.len()

    def reset_outputs(self, **_):
        self.outputs = {}

    def run_loop(self):
        while True:
            try:
                if self.len():
                    self.dequeue()
            except Exception as e:
                logger.exception(e)
            sleep(DEFAULT_QUEUE_POLLING_INTERVAL)
