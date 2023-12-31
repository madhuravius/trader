"""Added market summary information to be supplied and set by scouts/explorers

Revision ID: 6b93295149a3
Revises: d0433f0c972e
Create Date: 2023-10-31 22:33:50.164811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '6b93295149a3'
down_revision: Union[str, None] = 'd0433f0c972e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('marketexchange',
    sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('symbol', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('waypoint_symbol', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('system_symbol', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_marketexchange_created_at'), 'marketexchange', ['created_at'], unique=False)
    op.create_index(op.f('ix_marketexchange_waypoint_symbol'), 'marketexchange', ['waypoint_symbol'], unique=False)
    op.create_table('marketexport',
    sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('symbol', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('waypoint_symbol', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('system_symbol', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_marketexport_created_at'), 'marketexport', ['created_at'], unique=False)
    op.create_index(op.f('ix_marketexport_waypoint_symbol'), 'marketexport', ['waypoint_symbol'], unique=False)
    op.create_table('marketimport',
    sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('symbol', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('waypoint_symbol', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('system_symbol', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_marketimport_created_at'), 'marketimport', ['created_at'], unique=False)
    op.create_index(op.f('ix_marketimport_waypoint_symbol'), 'marketimport', ['waypoint_symbol'], unique=False)
    op.create_table('markettradegood',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('symbol', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('trade_volume', sa.Integer(), nullable=False),
    sa.Column('supply', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('purchase_price', sa.Integer(), nullable=False),
    sa.Column('sell_price', sa.Integer(), nullable=False),
    sa.Column('waypoint_symbol', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('system_symbol', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_markettradegood_waypoint_symbol'), 'markettradegood', ['waypoint_symbol'], unique=False)
    op.create_table('markettransaction',
    sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('ship_symbol', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('trade_symbol', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('transaction_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('units', sa.Integer(), nullable=False),
    sa.Column('price_per_unit', sa.Integer(), nullable=False),
    sa.Column('total_price', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('waypoint_symbol', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('system_symbol', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_markettransaction_created_at'), 'markettransaction', ['created_at'], unique=False)
    op.create_index(op.f('ix_markettransaction_waypoint_symbol'), 'markettransaction', ['waypoint_symbol'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_markettransaction_waypoint_symbol'), table_name='markettransaction')
    op.drop_index(op.f('ix_markettransaction_created_at'), table_name='markettransaction')
    op.drop_table('markettransaction')
    op.drop_index(op.f('ix_markettradegood_waypoint_symbol'), table_name='markettradegood')
    op.drop_table('markettradegood')
    op.drop_index(op.f('ix_marketimport_waypoint_symbol'), table_name='marketimport')
    op.drop_index(op.f('ix_marketimport_created_at'), table_name='marketimport')
    op.drop_table('marketimport')
    op.drop_index(op.f('ix_marketexport_waypoint_symbol'), table_name='marketexport')
    op.drop_index(op.f('ix_marketexport_created_at'), table_name='marketexport')
    op.drop_table('marketexport')
    op.drop_index(op.f('ix_marketexchange_waypoint_symbol'), table_name='marketexchange')
    op.drop_index(op.f('ix_marketexchange_created_at'), table_name='marketexchange')
    op.drop_table('marketexchange')
    # ### end Alembic commands ###
