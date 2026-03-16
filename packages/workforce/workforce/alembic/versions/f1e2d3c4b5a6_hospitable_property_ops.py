"""hospitable_property_ops

Revision ID: f1e2d3c4b5a6
Revises: 432688e91336
Create Date: 2026-03-12 19:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1e2d3c4b5a6'
down_revision: Union[str, None] = '432688e91336'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Property hierarchy
    op.create_table(
        'property_buildings',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('location_id', sa.String(length=36), sa.ForeignKey('locations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.UniqueConstraint('location_id', 'code', name='uq_property_building_location_code')
    )
    op.create_index('ix_property_buildings_location_id', 'property_buildings', ['location_id'])

    op.create_table(
        'property_floors',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('building_id', sa.Integer(), sa.ForeignKey('property_buildings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('floor_number', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(length=120), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.UniqueConstraint('building_id', 'floor_number', name='uq_property_floor_building_number')
    )
    op.create_index('ix_property_floors_building_id', 'property_floors', ['building_id'])

    op.create_table(
        'property_sectors',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('floor_id', sa.Integer(), sa.ForeignKey('property_floors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.UniqueConstraint('floor_id', 'code', name='uq_property_sector_floor_code')
    )
    op.create_index('ix_property_sectors_floor_id', 'property_sectors', ['floor_id'])

    # Room groups
    op.create_table(
        'hk_room_groups',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('location_id', sa.String(length=36), sa.ForeignKey('locations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('color', sa.String(length=32), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    )
    op.create_index('ix_hk_room_groups_location_id', 'hk_room_groups', ['location_id'])

    # Rooms
    roomstatus_enum = sa.Enum('dirty','assigned','cleaning','clean','inspect','inspected','blocked', name='housestatus')
    floor_surface_enum = sa.Enum('carpet','hardwood','mixed','tile', name='floorsurface')
    occupancy_enum = sa.Enum('vacant','occupied','checkout','stayover','ooo', name='occupancystatus')
    inspection_enum = sa.Enum('not_required','pending','passed','failed', name='inspectionstatus')
    maintenance_enum = sa.Enum('ok','issue','in_progress','resolved', name='maintenancestatus')

    roomstatus_enum.create(op.get_bind(), checkfirst=True)
    floor_surface_enum.create(op.get_bind(), checkfirst=True)
    occupancy_enum.create(op.get_bind(), checkfirst=True)
    inspection_enum.create(op.get_bind(), checkfirst=True)
    maintenance_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'hk_rooms',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('location_id', sa.String(length=36), sa.ForeignKey('locations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('building_id', sa.Integer(), sa.ForeignKey('property_buildings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('floor_id', sa.Integer(), sa.ForeignKey('property_floors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sector_id', sa.Integer(), sa.ForeignKey('property_sectors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('room_group_id', sa.Integer(), sa.ForeignKey('hk_room_groups.id', ondelete='SET NULL'), nullable=True),
        sa.Column('room_number', sa.String(length=16), nullable=False),
        sa.Column('room_label', sa.String(length=120), nullable=True),
        sa.Column('room_type', sa.String(length=64), nullable=True),
        sa.Column('bed_count', sa.Integer(), nullable=True),
        sa.Column('bed_type_summary', sa.String(length=120), nullable=True),
        sa.Column('floor_surface', floor_surface_enum, nullable=False, server_default='carpet'),
        sa.Column('housekeeping_status', roomstatus_enum, nullable=False, server_default='dirty'),
        sa.Column('occupancy_status', occupancy_enum, nullable=False, server_default='vacant'),
        sa.Column('inspection_status', inspection_enum, nullable=False, server_default='not_required'),
        sa.Column('maintenance_status', maintenance_enum, nullable=False, server_default='ok'),
        sa.Column('out_of_order_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('last_cleaned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_inspected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.UniqueConstraint('location_id', 'room_number', name='uq_hk_room_location_number')
    )
    op.create_index('ix_hk_rooms_location_id', 'hk_rooms', ['location_id'])
    op.create_index('ix_hk_rooms_housekeeping_status', 'hk_rooms', ['housekeeping_status'])

    # Assets
    op.create_table(
        'hk_room_assets',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('room_id', sa.Integer(), sa.ForeignKey('hk_rooms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('asset_type', sa.String(length=64), nullable=False),
        sa.Column('asset_name', sa.String(length=120), nullable=False),
        sa.Column('quantity_expected', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('quantity_present', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('condition_status', sa.String(length=32), nullable=True),
        sa.Column('maintenance_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    )
    op.create_index('ix_hk_room_assets_room_id', 'hk_room_assets', ['room_id'])

    # Supply pars
    op.create_table(
        'hk_room_supply_pars',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('room_id', sa.Integer(), sa.ForeignKey('hk_rooms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('item_code', sa.String(length=64), nullable=False),
        sa.Column('item_name', sa.String(length=120), nullable=False),
        sa.Column('expected_qty', sa.Integer(), nullable=False),
        sa.Column('min_qty', sa.Integer(), nullable=False),
        sa.Column('unit', sa.String(length=32), nullable=False, server_default='ea'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    )
    op.create_index('ix_hk_room_supply_pars_room_id', 'hk_room_supply_pars', ['room_id'])

    # Tasks and events
    task_type_enum = sa.Enum('clean_checkout','clean_stayover','inspection','restock','maintenance_followup', name='tasktype')
    task_priority_enum = sa.Enum('low','normal','high','urgent', name='taskpriority')
    task_status_enum = sa.Enum('open','assigned','in_progress','done','cancelled', name='taskstatus')

    task_type_enum.create(op.get_bind(), checkfirst=True)
    task_priority_enum.create(op.get_bind(), checkfirst=True)
    task_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'hk_tasks',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('location_id', sa.String(length=36), sa.ForeignKey('locations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('room_id', sa.Integer(), sa.ForeignKey('hk_rooms.id', ondelete='SET NULL'), nullable=True),
        sa.Column('task_type', task_type_enum, nullable=False),
        sa.Column('title', sa.String(length=160), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', task_priority_enum, nullable=False, server_default='normal'),
        sa.Column('status', task_status_enum, nullable=False, server_default='open'),
        sa.Column('assigned_user_id', sa.String(length=36), nullable=True),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    )
    op.create_index('ix_hk_tasks_location_id', 'hk_tasks', ['location_id'])
    op.create_index('ix_hk_tasks_status', 'hk_tasks', ['status'])

    op.create_table(
        'hk_task_events',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('hk_tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('from_status', sa.String(length=64), nullable=True),
        sa.Column('to_status', sa.String(length=64), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    )
    op.create_index('ix_hk_task_events_task_id', 'hk_task_events', ['task_id'])

    # Maintenance issues
    maint_status_enum = sa.Enum('open','triaged','in_progress','resolved','closed', name='maintissue_status')
    maint_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'maintenance_issues',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('location_id', sa.String(length=36), sa.ForeignKey('locations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('room_id', sa.Integer(), sa.ForeignKey('hk_rooms.id', ondelete='SET NULL'), nullable=True),
        sa.Column('issue_type', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=160), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(length=32), nullable=False, server_default='normal'),
        sa.Column('status', maint_status_enum, nullable=False, server_default='open'),
        sa.Column('assigned_user_id', sa.String(length=36), nullable=True),
        sa.Column('reported_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('reported_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    )
    op.create_index('ix_maintenance_issues_location_id', 'maintenance_issues', ['location_id'])
    op.create_index('ix_maintenance_issues_status', 'maintenance_issues', ['status'])

    # Room status events
    op.create_table(
        'hk_room_status_events',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('room_id', sa.Integer(), sa.ForeignKey('hk_rooms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('old_value', sa.String(length=64), nullable=True),
        sa.Column('new_value', sa.String(length=64), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    )
    op.create_index('ix_hk_room_status_events_room_id', 'hk_room_status_events', ['room_id'])


def downgrade() -> None:
    op.drop_index('ix_hk_room_status_events_room_id', table_name='hk_room_status_events')
    op.drop_table('hk_room_status_events')

    op.drop_index('ix_maintenance_issues_status', table_name='maintenance_issues')
    op.drop_index('ix_maintenance_issues_location_id', table_name='maintenance_issues')
    op.drop_table('maintenance_issues')

    op.drop_index('ix_hk_task_events_task_id', table_name='hk_task_events')
    op.drop_table('hk_task_events')

    op.drop_index('ix_hk_tasks_status', table_name='hk_tasks')
    op.drop_index('ix_hk_tasks_location_id', table_name='hk_tasks')
    op.drop_table('hk_tasks')

    op.drop_index('ix_hk_room_supply_pars_room_id', table_name='hk_room_supply_pars')
    op.drop_table('hk_room_supply_pars')

    op.drop_index('ix_hk_room_assets_room_id', table_name='hk_room_assets')
    op.drop_table('hk_room_assets')

    op.drop_index('ix_hk_rooms_housekeeping_status', table_name='hk_rooms')
    op.drop_index('ix_hk_rooms_location_id', table_name='hk_rooms')
    op.drop_table('hk_rooms')

    op.drop_index('ix_hk_room_groups_location_id', table_name='hk_room_groups')
    op.drop_table('hk_room_groups')

    op.drop_index('ix_property_sectors_floor_id', table_name='property_sectors')
    op.drop_table('property_sectors')

    op.drop_index('ix_property_floors_building_id', table_name='property_floors')
    op.drop_table('property_floors')

    op.drop_index('ix_property_buildings_location_id', table_name='property_buildings')
    op.drop_table('property_buildings')

    # Drop enums (if created)
    sa.Enum(name='maintissue_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='taskstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='taskpriority').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='tasktype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='maintenancestatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='inspectionstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='occupancystatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='floorsurface').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='housestatus').drop(op.get_bind(), checkfirst=True)
