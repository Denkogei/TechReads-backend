"""Add admin

Revision ID: 11bbf717fba6
Revises: fa6b6787b25a
Create Date: 2025-02-26 07:42:44.273216

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '11bbf717fba6'
down_revision = 'fa6b6787b25a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_admin', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_admin')

    # ### end Alembic commands ###
