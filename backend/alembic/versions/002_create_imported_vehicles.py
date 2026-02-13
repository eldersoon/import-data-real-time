"""create imported_vehicles table

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'imported_vehicles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('modelo', sa.String(), nullable=False),
        sa.Column('placa', sa.String(7), nullable=False),
        sa.Column('ano', sa.Integer(), nullable=False),
        sa.Column('valor_fipe', sa.Numeric(12, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['job_id'], ['import_jobs.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "ano >= 1900 AND ano <= EXTRACT(YEAR FROM CURRENT_DATE) + 1",
            name='check_ano'
        ),
        sa.CheckConstraint(
            "valor_fipe > 0",
            name='check_valor_fipe'
        ),
        sa.UniqueConstraint('placa', name='uq_imported_vehicles_placa'),
    )
    op.create_index('ix_imported_vehicles_job_id', 'imported_vehicles', ['job_id'])
    op.create_index('ix_imported_vehicles_placa', 'imported_vehicles', ['placa'])
    op.create_index('ix_imported_vehicles_ano', 'imported_vehicles', ['ano'])


def downgrade() -> None:
    op.drop_index('ix_imported_vehicles_ano', table_name='imported_vehicles')
    op.drop_index('ix_imported_vehicles_placa', table_name='imported_vehicles')
    op.drop_index('ix_imported_vehicles_job_id', table_name='imported_vehicles')
    op.drop_table('imported_vehicles')
