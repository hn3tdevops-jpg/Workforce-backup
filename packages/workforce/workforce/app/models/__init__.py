# Local model registry: import all model classes so Base.metadata is populated
from packages.workforce.workforce.app.models.base import Base  # noqa: F401
from packages.workforce.workforce.app.models.business import Business, Location  # noqa: F401
from packages.workforce.workforce.app.models.employee import Employee, Employment, EmployeeRole, Role  # noqa: F401
from packages.workforce.workforce.app.models.scheduling import AvailabilityBlock, Shift, ShiftAssignment  # noqa: F401
from packages.workforce.workforce.app.models.training import EmployeeTraining, TrainingModule  # noqa: F401
from packages.workforce.workforce.app.models.audit import AuditLog  # noqa: F401
from packages.workforce.workforce.app.models.identity import AuditEvent  # noqa: F401
from packages.workforce.workforce.app.models.identity import (
    User, RefreshToken, Membership, WorkerProfile,
    BizRole, Permission, BizRolePermission, MembershipRole, MembershipLocationRole,
    Agent, AgentCredential, AgentRun,
)  # noqa: F401
from packages.workforce.workforce.app.models.auth import Role as AuthRole, user_roles  # noqa: F401
from packages.workforce.workforce.app.models.timeclock import TimeEntry, TimeEntryStatus  # noqa: F401
from packages.workforce.workforce.app.models.marketplace import (
    JobPosting, ShiftRequest, TrainingRequest, ShiftSwapRequest, SwapPermissionRule,
    PostingStatus, RequestStatus, SwapStatus, SwapRuleEffect,
)  # noqa: F401
from packages.workforce.workforce.app.models.schedule import ScheduleShift, ScheduleAssignment, ShiftStatus, AssignmentStatus  # noqa: F401
from packages.workforce.workforce.app.models.dashboard import WidgetDefinition, DashboardTemplate, UserDashboard, WidgetType  # noqa: F401
from packages.workforce.workforce.app.models.messaging import Channel, ChannelMember, Message, MessagingApiKey  # noqa: F401
from packages.workforce.workforce.app.models.hkops import (
    HKRoom, HKTaskType, HKTask, HKInspection,
    RoomStatus, TaskStatus, TaskPriority, InspectionResult,
)  # noqa: F401
