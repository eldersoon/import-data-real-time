"""create import_jobs table

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'import_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('total_rows', sa.Integer(), nullable=True),
        sa.Column('processed_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name='check_status'
        ),
    )
    op.create_index('ix_import_jobs_status', 'import_jobs', ['status'])
    op.create_index('ix_import_jobs_created_at', 'import_jobs', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_import_jobs_created_at', table_name='import_jobs')
    op.drop_index('ix_import_jobs_status', table_name='import_jobs')
    op.drop_table('import_jobs')
