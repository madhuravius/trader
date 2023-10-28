from typing import Optional

from sqlmodel import Field, SQLModel


class CachedRequest(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    method: str
    url: str
    data: str
    params: str
    response: bytes
    expiration: float
