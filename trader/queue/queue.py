from typing import Any, Callable, Dict, Tuple, cast

import dill as pickle
from loguru import logger
from sqlalchemy import delete
from sqlmodel import Session, col, func, select

from trader.dao.dao import DAO
from trader.dao.queues import Queue as QueueDAO
from trader.dao.queues import QueueEntry


class Queue:
    """
    This class is a queue construct that will hydrate queues to a database.
    This is useful because if the application is stopped and restarted, the
    queue mechanics will work again as they were initially intended.

    WARNING: In most cases, we will just want to purge these queues on init, but on
    known start and stop. This is because the application is still very unstable
    and parameters are very likely to change.
    """

    dao: DAO
    queue_id: str
    queue_name: str
    functions: Dict[int, Callable | None]

    def __init__(self, queue_id: str, queue_name: str):
        self.queue_id = queue_id
        self.queue_name = queue_name
        self.dao = DAO()
        self.functions = {}
        self._ensure_queue_record()

    def _ensure_queue_record(self):
        with Session(self.dao.engine) as session:
            if not session.exec(
                select(QueueDAO).where(QueueDAO.id == self.queue_id)
            ).one_or_none():
                session.add(QueueDAO(id=self.queue_id, name=self.queue_name))
                session.commit()

    def len(self) -> int:
        count = 0
        with Session(self.dao.engine) as session:
            count_data = session.exec(
                select([func.count(QueueEntry.id)]).where(
                    QueueEntry.queue_id == self.queue_id
                )
            ).one_or_none()
            if count_data:
                count = cast(int, count_data)
        return count

    def delete(self):
        with Session(self.dao.engine) as session:
            # deletion of the queue object should cascade and delete associated children
            queue = session.exec(
                select(QueueDAO).where(QueueDAO.id == self.queue_id)
            ).one()
            session.delete(queue)
            session.commit()

    def pop(self) -> Tuple[Callable | None, Any]:
        # get all records ordered by size
        # pop by removing from queue and ideally removing values and then reordering the rest
        with Session(self.dao.engine) as session:
            expression = (
                select(QueueEntry)
                .where(QueueEntry.queue_id == self.queue_id)
                .order_by(col(QueueEntry.order).desc())
            )
            queue_entry = session.exec(expression.limit(1)).one()
            functional_return = None
            if queue_entry.id:
                functional_return = self.functions.get(queue_entry.id)
                del self.functions[queue_entry.id]
            logger.debug(
                f"Deleting key from queue entry id: {queue_entry.id} on queue: {self.queue_id}"
            )
            data = pickle.loads(queue_entry.data)
            session.delete(queue_entry)
            session.commit()
            return functional_return, data

    def purge(self) -> None:
        """
        Use with care. Meant to fully empty a queue.
        """

        with Session(self.dao.engine) as session:
            expression = delete(QueueEntry).where(QueueEntry.queue_id == self.queue_id)
            session.exec(expression)  # type: ignore
            session.commit()

    def append(self, function: Callable, data: Any):
        # when appending or updating, will need to acquire locks because of the lack of guards
        # on locking concurrent records
        with Session(self.dao.engine) as session:
            queue_entry = QueueEntry(
                queue_id=self.queue_id,
                order=self.len() + 1,
                data=pickle.dumps(data),
            )
            session.add(queue_entry)
            session.commit()
            if queue_entry.id:
                self.functions[queue_entry.id] = function
            logger.debug(
                f"Appending key from queue: {queue_entry.id} on queue: {self.queue_id}"
            )
