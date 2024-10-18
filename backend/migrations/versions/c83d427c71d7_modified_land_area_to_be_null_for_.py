"""modified land_area to be null for apartments

Revision ID: c83d427c71d7
Revises: 
Create Date: 2024-10-16 15:08:30.219030

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c83d427c71d7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('residences', schema=None) as batch_op:
        batch_op.alter_column('land_area',
               existing_type=sa.FLOAT(),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('residences', schema=None) as batch_op:
        batch_op.alter_column('land_area',
               existing_type=sa.FLOAT(),
               nullable=False)

    # ### end Alembic commands ###