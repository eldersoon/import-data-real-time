"""create job_logs table

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:00:02.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'job_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('level', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['job_id'], ['import_jobs.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "level IN ('info', 'warning', 'error')",
            name='check_level'
        ),
    )
    op.create_index('ix_job_logs_job_id', 'job_logs', ['job_id'])
    op.create_index('ix_job_logs_level', 'job_logs', ['level'])
    op.create_index('ix_job_logs_created_at', 'job_logs', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_job_logs_created_at', table_name='job_logs')
    op.drop_index('ix_job_logs_level', table_name='job_logs')
    op.drop_index('ix_job_logs_job_id', table_name='job_logs')
    op.drop_table('job_logs')
