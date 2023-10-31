from threading import Thread
from time import sleep
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

import httpx
from loguru import logger

from trader.client.request import ClientRequest
from trader.util.singleton import Singleton

MAXIMUM_REQUESTS_PER_SECOND = 1.75


class Queue(metaclass=Singleton):
    """
    This class is a queue object with a priority queue. Its purpose is to
    organize requests into a priority (1-5), where the higher the number, the
    higher it is in priority. Items are popped off (LIFO) the queue based on
    priority.

    Doing things like system scans are much lower priority vs. operations that
    actively generate revenue (ex: harvesting/trading/navigation).
    """

    requests: Dict[int, List[Tuple[str, ClientRequest]]] = {}
    responses: Dict[str, httpx.Response] = {}

    def __init__(self):
        thread = Thread(target=self.run_loop)
        thread.setDaemon(True)
        thread.start()

    def get_request_debug_info(self, request: ClientRequest) -> str:
        name = request.function.__name__
        url = request.arguments.get("url")
        params = request.arguments.get("params")
        return f"{name} {url} {params}"

    def get_highest_priority_queue(
        self,
    ) -> Optional[Tuple[int, List[Tuple[str, ClientRequest]]]]:
        if not self.requests.keys():
            return None

        priority = sorted(self.requests.keys()).pop()
        return priority, self.requests[priority]

    def dequeue(self):
        priority_queue = self.get_highest_priority_queue()

        if priority_queue:
            (priority, queue) = priority_queue
            (request_id, request_to_handle) = queue.pop()
            if len(queue) == 0:
                del self.requests[priority]

            logger.debug(
                f"Dequeuing - {self.get_request_debug_info(request_to_handle)}"
            )
            response = self.execute(request_to_handle)
            self.responses[request_id] = response

    def run_loop(self):
        while True:
            try:
                self.dequeue()
            except Exception as e:
                logger.exception(e)
            sleep(1 / MAXIMUM_REQUESTS_PER_SECOND)

    def enqueue(self, priority: int, request: ClientRequest) -> str:
        if self.requests.get(priority) is None:
            self.requests[priority] = []
        request_id = str(uuid4())
        logger.debug(f"Enqueued - {self.get_request_debug_info(request)}")
        self.requests[priority].append((request_id, request))
        return request_id

    def execute(self, request: ClientRequest) -> httpx.Response:
        logger.debug(f"Executing - {self.get_request_debug_info(request)}")
        return request.function(**request.arguments)

    def wait_for_response(self, request_id: str) -> httpx.Response:
        while True:
            if self.responses.get(request_id):
                return self.responses.pop(request_id)
            sleep(0.5)
