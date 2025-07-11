"""Add DemoRequest model

Revision ID: 3fa2cc2a4b06
Revises: 00697a24add6
Create Date: 2025-06-26 20:08:27.718271

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3fa2cc2a4b06'
down_revision = '00697a24add6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('demo_requests',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('company_name', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('team_size', sa.String(length=100), nullable=True),
    sa.Column('ai_usage', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('demo_requests')
    # ### end Alembic commands ###
