"""
V1 API router — aggregates all planes.
"""
from fastapi import APIRouter

from app.api.v1.auth.routes import router as auth_router
from app.api.v1.control.routes import router as control_router
from app.api.v1.tenant.routes import router as tenant_router
from app.api.v1.worker.routes import router as worker_router
from app.api.v1.agent.routes import router as agent_router
from app.api.v1.timeclock.routes import worker_router as tc_worker_router, tenant_router as tc_tenant_router
from app.api.v1.marketplace.routes import (
    public_router as mkt_public,
    worker_router as mkt_worker,
    tenant_router as mkt_tenant,
)
from app.api.v1.schedule.routes import router as schedule_router
from app.api.v1.dashboard.routes import (
    control_router as dash_control_router,
    tenant_router as dash_tenant_router,
    worker_router as dash_worker_router,
)

from app.api.v1.messaging.routes import (
    worker_router as msg_worker_router,
    tenant_router as msg_tenant_router,
    external_router as msg_external_router,
)
from app.api.v1.hkops.routes import (
    worker_router as hk_worker_router,
    tenant_router as hk_tenant_router,
    control_router as hk_control_router,
)

v1_router = APIRouter()
v1_router.include_router(auth_router)
v1_router.include_router(control_router)
v1_router.include_router(tenant_router)
v1_router.include_router(worker_router)
v1_router.include_router(agent_router)
v1_router.include_router(tc_worker_router)
v1_router.include_router(tc_tenant_router)
v1_router.include_router(mkt_public)
v1_router.include_router(mkt_worker)
v1_router.include_router(mkt_tenant)
v1_router.include_router(schedule_router)

v1_router.include_router(dash_control_router)
v1_router.include_router(dash_tenant_router)
v1_router.include_router(dash_worker_router)
v1_router.include_router(msg_worker_router)
v1_router.include_router(msg_tenant_router)
v1_router.include_router(msg_external_router)

v1_router.include_router(hk_worker_router)
v1_router.include_router(hk_tenant_router)
v1_router.include_router(hk_control_router)

