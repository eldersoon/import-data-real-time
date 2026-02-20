"""add dynamic import support

Revision ID: 004
Revises: 003
Create Date: 2024-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create import_templates table
    op.create_table(
        'import_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('target_table', sa.String(), nullable=False),
        sa.Column('create_table', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('mapping_config', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_import_templates_name', 'import_templates', ['name'])
    op.create_index('ix_import_templates_target_table', 'import_templates', ['target_table'])
    op.create_index('ix_import_templates_created_at', 'import_templates', ['created_at'])

    # Add template_id and mapping_config to import_jobs
    op.add_column('import_jobs', sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('import_jobs', sa.Column('mapping_config', postgresql.JSONB(), nullable=True))
    op.create_foreign_key(
        'fk_import_jobs_template_id',
        'import_jobs',
        'import_templates',
        ['template_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_import_jobs_template_id', 'import_jobs', ['template_id'])


def downgrade() -> None:
    op.drop_index('ix_import_jobs_template_id', table_name='import_jobs')
    op.drop_constraint('fk_import_jobs_template_id', 'import_jobs', type_='foreignkey')
    op.drop_column('import_jobs', 'mapping_config')
    op.drop_column('import_jobs', 'template_id')
    op.drop_index('ix_import_templates_created_at', table_name='import_templates')
    op.drop_index('ix_import_templates_target_table', table_name='import_templates')
    op.drop_index('ix_import_templates_name', table_name='import_templates')
    op.drop_table('import_templates')
