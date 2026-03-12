"""Hospitable property ops tables: buildings, floors, sectors, room groups,
rooms, assets, supply pars, tasks, task events, maintenance issues,
room status events.

Revision ID: 0002_hospitable_property_ops
Revises: 0001_initial
Create Date: 2026-03-12
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_hospitable_property_ops"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def _is_sqlite() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "sqlite"


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # property_buildings
    # ------------------------------------------------------------------ #
    op.create_table(
        "property_buildings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "location_id",
            sa.String(36),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "location_id", "code", name="uq_property_building_location_code"
        ),
    )
    op.create_index(
        "ix_property_buildings_location_id", "property_buildings", ["location_id"]
    )

    # ------------------------------------------------------------------ #
    # property_floors
    # ------------------------------------------------------------------ #
    op.create_table(
        "property_floors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "building_id",
            sa.Integer(),
            sa.ForeignKey("property_buildings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("floor_number", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "building_id", "floor_number", name="uq_property_floor_building_number"
        ),
    )
    op.create_index(
        "ix_property_floors_building_id", "property_floors", ["building_id"]
    )

    # ------------------------------------------------------------------ #
    # property_sectors
    # ------------------------------------------------------------------ #
    op.create_table(
        "property_sectors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "floor_id",
            sa.Integer(),
            sa.ForeignKey("property_floors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "floor_id", "code", name="uq_property_sector_floor_code"
        ),
    )
    op.create_index(
        "ix_property_sectors_floor_id", "property_sectors", ["floor_id"]
    )

    # ------------------------------------------------------------------ #
    # hk_room_groups
    # ------------------------------------------------------------------ #
    op.create_table(
        "hk_room_groups",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "location_id",
            sa.String(36),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("color", sa.String(32), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_hk_room_groups_location_id", "hk_room_groups", ["location_id"]
    )

    # ------------------------------------------------------------------ #
    # hk_rooms
    # ------------------------------------------------------------------ #
    op.create_table(
        "hk_rooms",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "location_id",
            sa.String(36),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "building_id",
            sa.Integer(),
            sa.ForeignKey("property_buildings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "floor_id",
            sa.Integer(),
            sa.ForeignKey("property_floors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sector_id",
            sa.Integer(),
            sa.ForeignKey("property_sectors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "room_group_id",
            sa.Integer(),
            sa.ForeignKey("hk_room_groups.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("room_number", sa.String(16), nullable=False),
        sa.Column("room_label", sa.String(120), nullable=True),
        sa.Column("room_type", sa.String(64), nullable=True),
        sa.Column("bed_count", sa.Integer(), nullable=True),
        sa.Column("bed_type_summary", sa.String(120), nullable=True),
        sa.Column(
            "floor_surface",
            sa.String(16),
            nullable=False,
            server_default="carpet",
        ),
        sa.Column(
            "housekeeping_status",
            sa.String(16),
            nullable=False,
            server_default="dirty",
        ),
        sa.Column(
            "occupancy_status",
            sa.String(16),
            nullable=False,
            server_default="vacant",
        ),
        sa.Column(
            "inspection_status",
            sa.String(16),
            nullable=False,
            server_default="not_required",
        ),
        sa.Column(
            "maintenance_status",
            sa.String(16),
            nullable=False,
            server_default="ok",
        ),
        sa.Column("out_of_order_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("last_cleaned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_inspected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "location_id", "room_number", name="uq_hk_room_location_number"
        ),
    )
    op.create_index("ix_hk_rooms_location_id", "hk_rooms", ["location_id"])
    op.create_index(
        "ix_hk_rooms_housekeeping_status", "hk_rooms", ["housekeeping_status"]
    )

    # ------------------------------------------------------------------ #
    # hk_room_assets
    # ------------------------------------------------------------------ #
    op.create_table(
        "hk_room_assets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "room_id",
            sa.Integer(),
            sa.ForeignKey("hk_rooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("asset_type", sa.String(64), nullable=False),
        sa.Column("asset_name", sa.String(120), nullable=False),
        sa.Column("quantity_expected", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("quantity_present", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("condition_status", sa.String(32), nullable=True),
        sa.Column("maintenance_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_hk_room_assets_room_id", "hk_room_assets", ["room_id"])

    # ------------------------------------------------------------------ #
    # hk_room_supply_pars
    # ------------------------------------------------------------------ #
    op.create_table(
        "hk_room_supply_pars",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "room_id",
            sa.Integer(),
            sa.ForeignKey("hk_rooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_code", sa.String(64), nullable=False),
        sa.Column("item_name", sa.String(120), nullable=False),
        sa.Column("expected_qty", sa.Integer(), nullable=False),
        sa.Column("min_qty", sa.Integer(), nullable=False),
        sa.Column("unit", sa.String(32), nullable=False, server_default="ea"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_hk_room_supply_pars_room_id", "hk_room_supply_pars", ["room_id"]
    )

    # ------------------------------------------------------------------ #
    # hk_tasks
    # ------------------------------------------------------------------ #
    op.create_table(
        "hk_tasks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "location_id",
            sa.String(36),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "room_id",
            sa.Integer(),
            sa.ForeignKey("hk_rooms.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("task_type", sa.String(32), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(16), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("assigned_user_id", sa.String(36), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.String(36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_hk_tasks_location_id", "hk_tasks", ["location_id"])
    op.create_index("ix_hk_tasks_status", "hk_tasks", ["status"])

    # ------------------------------------------------------------------ #
    # hk_task_events
    # ------------------------------------------------------------------ #
    op.create_table(
        "hk_task_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "task_id",
            sa.Integer(),
            sa.ForeignKey("hk_tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("from_status", sa.String(64), nullable=True),
        sa.Column("to_status", sa.String(64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.String(36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_hk_task_events_task_id", "hk_task_events", ["task_id"])

    # ------------------------------------------------------------------ #
    # maintenance_issues
    # ------------------------------------------------------------------ #
    op.create_table(
        "maintenance_issues",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "location_id",
            sa.String(36),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "room_id",
            sa.Integer(),
            sa.ForeignKey("hk_rooms.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("issue_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(32), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("assigned_user_id", sa.String(36), nullable=True),
        sa.Column("reported_by_user_id", sa.String(36), nullable=True),
        sa.Column(
            "reported_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_maintenance_issues_location_id", "maintenance_issues", ["location_id"]
    )
    op.create_index("ix_maintenance_issues_status", "maintenance_issues", ["status"])

    # ------------------------------------------------------------------ #
    # hk_room_status_events
    # ------------------------------------------------------------------ #
    op.create_table(
        "hk_room_status_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "room_id",
            sa.Integer(),
            sa.ForeignKey("hk_rooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("old_value", sa.String(64), nullable=True),
        sa.Column("new_value", sa.String(64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.String(36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_hk_room_status_events_room_id", "hk_room_status_events", ["room_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_hk_room_status_events_room_id", table_name="hk_room_status_events")
    op.drop_table("hk_room_status_events")

    op.drop_index("ix_maintenance_issues_status", table_name="maintenance_issues")
    op.drop_index("ix_maintenance_issues_location_id", table_name="maintenance_issues")
    op.drop_table("maintenance_issues")

    op.drop_index("ix_hk_task_events_task_id", table_name="hk_task_events")
    op.drop_table("hk_task_events")

    op.drop_index("ix_hk_tasks_status", table_name="hk_tasks")
    op.drop_index("ix_hk_tasks_location_id", table_name="hk_tasks")
    op.drop_table("hk_tasks")

    op.drop_index("ix_hk_room_supply_pars_room_id", table_name="hk_room_supply_pars")
    op.drop_table("hk_room_supply_pars")

    op.drop_index("ix_hk_room_assets_room_id", table_name="hk_room_assets")
    op.drop_table("hk_room_assets")

    op.drop_index("ix_hk_rooms_housekeeping_status", table_name="hk_rooms")
    op.drop_index("ix_hk_rooms_location_id", table_name="hk_rooms")
    op.drop_table("hk_rooms")

    op.drop_index("ix_hk_room_groups_location_id", table_name="hk_room_groups")
    op.drop_table("hk_room_groups")

    op.drop_index("ix_property_sectors_floor_id", table_name="property_sectors")
    op.drop_table("property_sectors")

    op.drop_index("ix_property_floors_building_id", table_name="property_floors")
    op.drop_table("property_floors")

    op.drop_index("ix_property_buildings_location_id", table_name="property_buildings")
    op.drop_table("property_buildings")
