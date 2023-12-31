"""Added general write to disk queues

Revision ID: a61333bd0558
Revises: 6b93295149a3
Create Date: 2023-11-02 17:12:59.482710

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a61333bd0558'
down_revision: Union[str, None] = '6b93295149a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('queue',
    sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('queueentry',
    sa.Column('queue_id', sa.String(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('data', sa.LargeBinary(), nullable=False),
    sa.ForeignKeyConstraint(['queue_id'], ['queue.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('queueentry')
    op.drop_table('queue')
    # ### end Alembic commands ###
