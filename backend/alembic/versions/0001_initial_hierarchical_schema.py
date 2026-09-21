"""initial_hierarchical_schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-09-20 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('roles', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. Nodes table (Polymorphic Hierarchical Tree)
    op.create_table(
        'nodes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('node_type', sa.Enum('ORGANIZATION', 'FOLDER', 'PROJECT', 'RESOURCE', name='node_type_enum'), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('path', sa.String(length=1024), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('visibility_settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['nodes.id'], name=op.f('fk_nodes_parent_id_nodes'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_nodes')),
    )
    op.create_index(op.f('ix_nodes_tenant_id'), 'nodes', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_nodes_node_type'), 'nodes', ['node_type'], unique=False)
    op.create_index(op.f('ix_nodes_parent_id'), 'nodes', ['parent_id'], unique=False)
    op.create_index(op.f('ix_nodes_path'), 'nodes', ['path'], unique=False)
    op.create_index('ix_nodes_tenant_type', 'nodes', ['tenant_id', 'node_type'], unique=False)
    op.create_index('ix_nodes_path_pattern', 'nodes', ['path'], unique=False)

    # 3. NodeUserMappings (Identity vs Capacity Separation)
    op.create_table(
        'node_user_mappings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('node_id', sa.UUID(), nullable=False),
        sa.Column('capacity_title', sa.String(length=255), nullable=False),
        sa.Column('allocation_percentage', sa.Float(), nullable=False, server_default=sa.text('100.0')),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], name=op.f('fk_node_user_mappings_node_id_nodes'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_node_user_mappings_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_node_user_mappings')),
    )
    op.create_index(op.f('ix_node_user_mappings_user_id'), 'node_user_mappings', ['user_id'], unique=False)
    op.create_index(op.f('ix_node_user_mappings_node_id'), 'node_user_mappings', ['node_id'], unique=False)
    op.create_index('ix_user_node_unique', 'node_user_mappings', ['user_id', 'node_id'], unique=True)

    # 4. NodeAvailabilities
    op.create_table(
        'node_availabilities',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('node_id', sa.UUID(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=True),
        sa.Column('specific_date', sa.Date(), nullable=True),
        sa.Column('start_time', sa.String(length=5), nullable=False),
        sa.Column('end_time', sa.String(length=5), nullable=False),
        sa.Column('slot_duration_minutes', sa.Integer(), nullable=False, server_default=sa.text('30')),
        sa.Column('buffer_minutes', sa.Integer(), nullable=False, server_default=sa.text('10')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], name=op.f('fk_node_availabilities_node_id_nodes'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_node_availabilities')),
    )
    op.create_index(op.f('ix_node_availabilities_node_id'), 'node_availabilities', ['node_id'], unique=False)
    op.create_index('ix_avail_node_day', 'node_availabilities', ['node_id', 'day_of_week'], unique=False)
    op.create_index('ix_avail_node_date', 'node_availabilities', ['node_id', 'specific_date'], unique=False)

    # 5. BookingIntents (Intent Pipeline & Screening Triage)
    op.create_table(
        'booking_intents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('target_node_id', sa.UUID(), nullable=False),
        sa.Column('triage_project_id', sa.UUID(), nullable=True),
        sa.Column('escalated_node_id', sa.UUID(), nullable=True),
        sa.Column('booker_name', sa.String(length=255), nullable=False),
        sa.Column('booker_email', sa.String(length=255), nullable=False),
        sa.Column('requested_start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('requested_end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.Enum('PENDING_REVIEW', 'APPROVED', 'REJECTED', 'RESCHEDULED', 'COMPLETED', name='intent_status_enum'), nullable=False),
        sa.Column('intake_responses', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('triage_notes', sa.Text(), nullable=True),
        sa.Column('escalation_token', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['target_node_id'], ['nodes.id'], name=op.f('fk_booking_intents_target_node_id_nodes'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['triage_project_id'], ['nodes.id'], name=op.f('fk_booking_intents_triage_project_id_nodes'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['escalated_node_id'], ['nodes.id'], name=op.f('fk_booking_intents_escalated_node_id_nodes'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_booking_intents')),
    )
    op.create_index(op.f('ix_booking_intents_tenant_id'), 'booking_intents', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_booking_intents_target_node_id'), 'booking_intents', ['target_node_id'], unique=False)
    op.create_index(op.f('ix_booking_intents_triage_project_id'), 'booking_intents', ['triage_project_id'], unique=False)
    op.create_index(op.f('ix_booking_intents_status'), 'booking_intents', ['status'], unique=False)

    # 6. Appointments
    op.create_table(
        'appointments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('resource_node_id', sa.UUID(), nullable=False),
        sa.Column('booker_user_id', sa.UUID(), nullable=True),
        sa.Column('booker_name', sa.String(length=255), nullable=False),
        sa.Column('booker_email', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.Enum('CONFIRMED', 'CANCELLED', 'COMPLETED', name='appointment_status_enum'), nullable=False),
        sa.Column('payment_status', sa.String(length=50), nullable=False, server_default='free'),
        sa.Column('payment_amount_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('payment_reference', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['booker_user_id'], ['users.id'], name=op.f('fk_appointments_booker_user_id_users'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resource_node_id'], ['nodes.id'], name=op.f('fk_appointments_resource_node_id_nodes'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_appointments')),
    )
    op.create_index(op.f('ix_appointments_tenant_id'), 'appointments', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_appointments_resource_node_id'), 'appointments', ['resource_node_id'], unique=False)
    op.create_index(op.f('ix_appointments_status'), 'appointments', ['status'], unique=False)
    op.create_index('ix_appointments_conflict_lookup', 'appointments', ['resource_node_id', 'status', 'start_time', 'end_time'], unique=False)

    # 7. CalendarIntegrations
    op.create_table(
        'calendar_integrations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('resource_node_id', sa.UUID(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('account_email', sa.String(length=255), nullable=False),
        sa.Column('sync_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('access_token_enc', sa.Text(), nullable=True),
        sa.Column('refresh_token_enc', sa.Text(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_status_message', sa.String(length=255), nullable=False, server_default='Connected and Healthy'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['resource_node_id'], ['nodes.id'], name=op.f('fk_calendar_integrations_resource_node_id_nodes'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_calendar_integrations')),
    )
    op.create_index(op.f('ix_calendar_integrations_resource_node_id'), 'calendar_integrations', ['resource_node_id'], unique=False)

    # 8. PaymentEscrowConfigs
    op.create_table(
        'payment_escrow_configs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('node_id', sa.UUID(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('amount_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('escrow_policy', sa.String(length=100), nullable=False, server_default='escrow_hold_until_session'),
        sa.Column('account_connected_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], name=op.f('fk_payment_escrow_configs_node_id_nodes'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_payment_escrow_configs')),
    )
    op.create_index(op.f('ix_payment_escrow_configs_node_id'), 'payment_escrow_configs', ['node_id'], unique=True)

    # 9. IntakeFormSchemas
    op.create_table(
        'intake_form_schemas',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('node_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('fields_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], name=op.f('fk_intake_form_schemas_node_id_nodes'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_intake_form_schemas')),
    )
    op.create_index(op.f('ix_intake_form_schemas_node_id'), 'intake_form_schemas', ['node_id'], unique=True)


def downgrade() -> None:
    op.drop_table('intake_form_schemas')
    op.drop_table('payment_escrow_configs')
    op.drop_table('calendar_integrations')
    op.drop_table('appointments')
    op.drop_table('booking_intents')
    op.drop_table('node_availabilities')
    op.drop_table('node_user_mappings')
    op.drop_table('nodes')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS appointment_status_enum')
    op.execute('DROP TYPE IF EXISTS intent_status_enum')
    op.execute('DROP TYPE IF EXISTS node_type_enum')
