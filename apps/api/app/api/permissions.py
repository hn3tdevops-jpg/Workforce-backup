from app.api.dependencies import require_permission

require_rooms_read = require_permission("hk.rooms.read")
require_tasks_manage = require_permission("hk.tasks.manage")
require_schedule_read = require_permission("schedule.read")
require_time_read = require_permission("time.read")