"""Add squad members in preparation for fleet orchestration

Revision ID: da1e111fb73b
Revises: 85517e9af294
Create Date: 2023-11-04 14:18:09.426783

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'da1e111fb73b'
down_revision: Union[str, None] = '85517e9af294'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('squad',
    sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('squadmember',
    sa.Column('ship_id', sa.String(), nullable=True),
    sa.Column('squad_id', sa.String(), nullable=True),
    sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['ship_id'], ['ship.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['squad_id'], ['squad.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('squadmember')
    op.drop_table('squad')
    # ### end Alembic commands ###