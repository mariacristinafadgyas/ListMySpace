"""modified messages class

Revision ID: df211f46a369
Revises: f67a4e520438
Create Date: 2024-10-20 18:19:07.209133

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'df211f46a369'
down_revision = 'f67a4e520438'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.alter_column('customer_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.alter_column('owner_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.alter_column('owner_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('customer_id',
               existing_type=sa.INTEGER(),
               nullable=False)

    # ### end Alembic commands ###