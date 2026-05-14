from app.api.dependencies import (
    require_permission_with_location,
    resolve_location_from_query,
)

require_rooms_read = require_permission_with_location("hk.rooms.read", location_resolver=resolve_location_from_query)
require_tasks_manage = require_permission_with_location("hk.tasks.manage", location_resolver=resolve_location_from_query)
require_schedule_read = require_permission_with_location("schedule.read", location_resolver=resolve_location_from_query)
require_time_read = require_permission_with_location("time.read", location_resolver=resolve_location_from_query)