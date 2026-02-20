"""create dynamic_entities table

Revision ID: 005
Revises: 004
Create Date: 2024-01-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'dynamic_entities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('table_name', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('is_visible', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by_job_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_unique_constraint('uq_dynamic_entities_table_name', 'dynamic_entities', ['table_name'])
    op.create_index('ix_dynamic_entities_table_name', 'dynamic_entities', ['table_name'])
    op.create_index('ix_dynamic_entities_is_visible', 'dynamic_entities', ['is_visible'])
    op.create_index('ix_dynamic_entities_created_at', 'dynamic_entities', ['created_at'])
    op.create_foreign_key(
        'fk_dynamic_entities_created_by_job_id',
        'dynamic_entities',
        'import_jobs',
        ['created_by_job_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_dynamic_entities_created_by_job_id', 'dynamic_entities', type_='foreignkey')
    op.drop_index('ix_dynamic_entities_created_at', table_name='dynamic_entities')
    op.drop_index('ix_dynamic_entities_is_visible', table_name='dynamic_entities')
    op.drop_index('ix_dynamic_entities_table_name', table_name='dynamic_entities')
    op.drop_constraint('uq_dynamic_entities_table_name', 'dynamic_entities', type_='unique')
    op.drop_table('dynamic_entities')
