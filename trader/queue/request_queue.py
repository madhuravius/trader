from threading import Thread
from time import sleep
from typing import Any, Callable, Dict, Optional, Tuple
from uuid import uuid4

import httpx
from loguru import logger

from trader.client.request import ClientRequest
from trader.queue.queue import Queue
from trader.util.singleton import Singleton

MAXIMUM_REQUESTS_PER_SECOND = 1.5
MAXIMUM_RETRIES_PER_REQUEST = 10
REQUESTS_QUEUE_DATA_PREFIX = "requests"


class RequestQueue(metaclass=Singleton):
    """
    This class is a queue object with a priority queue. Its purpose is to
    organize requests into a priority (1-5), where the higher the number, the
    higher it is in priority. Items are popped off (LIFO) the queue based on
    priority.

    This is a singleton because there should only be one of these present per client
    after which there will be throttling per API key. WARNING: if this becomes a distributed
    application, you will want to move some of this logic into the data layer (namely around throttling)

    Doing things like system scans are much lower priority vs. operations that
    actively generate revenue (ex: harvesting/trading/navigation).
    """

    requests: Dict[int, Queue] = {}
    responses: Dict[str, httpx.Response] = {}
    request_queue_instance: str

    def __init__(self, client_id: str):
        self.request_queue_instance = client_id
        thread = Thread(target=self.run_loop)
        thread.setDaemon(True)
        thread.start()

    def get_request_debug_info(
        self, request_function: Callable, request_arguments: Dict[str, Any]
    ) -> str:
        name = request_function.__name__
        url = request_arguments.get("url")
        params = request_arguments.get("params")
        return f"{name} {url} {params}"

    def get_highest_priority_queue(
        self,
    ) -> Optional[Tuple[int, Queue]]:
        if not self.requests.keys():
            return None

        priority = sorted(self.requests.keys()).pop()
        return priority, self.requests[priority]

    def dequeue(self):
        priority_queue = self.get_highest_priority_queue()

        if priority_queue:
            (priority, queue) = priority_queue
            (request_function, (request_id, request_arguments)) = queue.pop()
            if queue.len() == 0:
                queue.delete()
                del self.requests[priority]

            if request_function:
                logger.debug(
                    f"Dequeuing (priority - {priority}) "
                    f"- {self.get_request_debug_info(request_function=request_function, request_arguments=request_arguments)}"
                )
                response = self.execute(
                    request_function=request_function,
                    request_arguments=request_arguments,
                )
                self.responses[request_id] = response
            else:
                logger.warning(
                    f"Dequeuing (priority - {priority}) with {request_id} had no actionable queued function!"
                )

    def run_loop(self):
        while True:
            try:
                self.dequeue()
            except Exception as e:
                logger.exception(e)
            sleep(1 / MAXIMUM_REQUESTS_PER_SECOND)

    def enqueue(self, priority: int, request: ClientRequest) -> str:
        if self.requests.get(priority) is None:
            self.requests[priority] = Queue(
                queue_id=f"{REQUESTS_QUEUE_DATA_PREFIX}-{priority}-{self.request_queue_instance}",
                queue_name=f"{REQUESTS_QUEUE_DATA_PREFIX}-{priority}-{self.request_queue_instance}",
            )
        request_id = str(uuid4())
        logger.debug(
            f"Enqueued (priority - {priority}) - "
            f"{self.get_request_debug_info(request_function=request.function, request_arguments=request.arguments)}"
        )
        self.requests[priority].append(
            function=request.function, data=(request_id, request.arguments)
        )
        return request_id

    def execute(
        self, request_function: Callable, request_arguments: Dict[str, Any]
    ) -> httpx.Response:
        logger.debug(
            "Executing - "
            f"{self.get_request_debug_info(request_function=request_function, request_arguments=request_arguments)}"
        )
        attempt = 0
        while True:
            try:
                return request_function(**request_arguments)
            except (httpx.ReadTimeout, httpx.ConnectError) as e:
                if attempt < MAXIMUM_RETRIES_PER_REQUEST:
                    attempt += 1
                    time_to_wait = 5 * (2**attempt)
                    sleep(time_to_wait)
                    logger.warning(
                        f"Error when conducting request and attempting retry "
                        f"{repr(e)}. Sleeping for {time_to_wait} seconds "
                        f"before retrying. Attempt #{attempt}."
                    )
                    continue
                raise

    def wait_for_response(self, request_id: str) -> httpx.Response:
        while True:
            if self.responses.get(request_id):
                return self.responses.pop(request_id)
            sleep(0.5)
