from datetime import UTC, datetime
from typing import Optional, Sequence

from sqlalchemy.engine import Engine
from sqlmodel import Field, Session, SQLModel, col, select


class AgentHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_symbol: str
    created_at: datetime = Field(index=True, default=datetime.now(UTC))
    ship_count: int
    in_system_count: int
    credits: int


def get_agent_histories(engine: Engine, limit: int = 20) -> Sequence[AgentHistory]:
    agent_histories: Sequence[AgentHistory] = []
    with Session(engine) as session:
        agent_history_statement = (
            select(AgentHistory)
            .order_by(col(AgentHistory.created_at).desc())
            .limit(limit)
        )
        agent_histories = session.exec(agent_history_statement).all()
    return agent_histories


def get_agent_histories_by_date_cutoff(
    engine: Engine, cutoff: datetime
) -> Sequence[AgentHistory]:
    agent_histories: Sequence[AgentHistory] = []
    with Session(engine) as session:
        agent_history_statement = (
            select(AgentHistory).where(AgentHistory.created_at >= cutoff).limit(1)
        )
        agent_histories = session.exec(agent_history_statement).all()
    return agent_histories


def save_agent_history(
    engine: Engine,
    agent_symbol: str,
    credits: int,
    ship_count: int,
    in_system_count: int,
):
    with Session(engine) as session:
        session.add(
            AgentHistory(
                agent_symbol=agent_symbol,
                credits=credits,
                created_at=datetime.now(UTC),
                ship_count=ship_count,
                in_system_count=in_system_count,
            )
        )
        session.commit()
