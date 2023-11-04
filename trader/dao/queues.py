from typing import List, Optional

from sqlmodel import Column, Field, ForeignKey, Relationship, SQLModel, String


class QueueEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    queue_id: Optional[str] = Field(
        default=None,
        sa_column=Column(String, ForeignKey("queue.id", ondelete="CASCADE")),
    )
    order: int
    data: bytes


class Queue(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    name: str
    entries: List[QueueEntry] = Relationship(
        sa_relationship_kwargs={
            "cascade": "all, delete",
        }
    )
