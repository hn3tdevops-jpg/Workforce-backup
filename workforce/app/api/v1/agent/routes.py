"""
Agent plane routes — AI agents / integrations.
Authentication: X-API-Key (Bearer token = agent API key).
All routes enforce scope checking.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_deps import CurrentAgent, agent_require_scope
from app.core.db import get_db
from app.models.identity import AgentRun, AgentRunStatus
from app.models.scheduling import Shift

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


# ── Health / ping ─────────────────────────────────────────────────────────────

@router.get("/ping", dependencies=[agent_require_scope("ping")])
def agent_ping(agent: CurrentAgent):
    return {"status": "ok", "agent_id": agent.id, "agent_name": agent.name}


# ── Shifts (read access for scheduling agents) ────────────────────────────────

@router.get(
    "/businesses/{business_id}/shifts",
    dependencies=[agent_require_scope("schedule:read")],
)
def agent_list_shifts(
    business_id: str,
    agent: CurrentAgent,
    db: Session = Depends(get_db),
):
    # Enforce: agent must belong to this business or be global (no business_id)
    if agent.business_id and agent.business_id != business_id:
        from fastapi import HTTPException
        raise HTTPException(403, "Agent not authorized for this business")

    rows = db.execute(select(Shift)).scalars().all()
    return [
        {
            "id": s.id,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "status": s.status,
        }
        for s in rows
    ]


# ── Agent run tracking ────────────────────────────────────────────────────────

@router.post("/runs", status_code=201, dependencies=[agent_require_scope("runs:write")])
def start_run(agent: CurrentAgent, db: Session = Depends(get_db)):
    run = AgentRun(
        agent_id=agent.id,
        status=AgentRunStatus.running,
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return {"run_id": run.id, "status": run.status}


@router.patch("/runs/{run_id}", dependencies=[agent_require_scope("runs:write")])
def complete_run(
    run_id: str,
    status: str,
    agent: CurrentAgent,
    db: Session = Depends(get_db),
):
    run = db.get(AgentRun, run_id)
    if not run or run.agent_id != agent.id:
        from fastapi import HTTPException
        raise HTTPException(404, "Run not found")
    try:
        run.status = AgentRunStatus(status)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(400, f"Invalid status: {status}")
    run.finished_at = datetime.now(timezone.utc)
    db.commit()
    return {"run_id": run.id, "status": run.status}


@router.get("/runs", dependencies=[agent_require_scope("runs:read")])
def list_runs(agent: CurrentAgent, db: Session = Depends(get_db)):
    rows = db.execute(
        select(AgentRun).where(AgentRun.agent_id == agent.id).order_by(AgentRun.started_at.desc()).limit(50)
    ).scalars().all()
    return [
        {"id": r.id, "status": r.status, "started_at": r.started_at, "finished_at": r.finished_at}
        for r in rows
    ]
