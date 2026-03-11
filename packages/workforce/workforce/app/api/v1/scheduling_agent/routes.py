"""
AI Scheduling Agent routes — tenant-scoped.
Manages scheduling rules and triggers schedule generation via local Ollama LLM.
"""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.core.auth_deps import CurrentUser, require_permission
from apps.api.app.core.db import get_db
from apps.api.app.models.identity import AgentRun, AgentRunStatus
from apps.api.app.models.schedule import ScheduleRule
from apps.api.app.services.scheduler_agent import generate_schedule, parse_rule

router = APIRouter(
    prefix="/api/v1/tenant/{business_id}/agent",
    tags=["scheduling-agent"],
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class RuleCreate(BaseModel):
    raw_text: str


class GenerateRequest(BaseModel):
    week_start: str  # ISO date string, e.g. "2026-02-23"
    model: str = "llama3"


# ── Rules ─────────────────────────────────────────────────────────────────────

@router.get("/rules", dependencies=[require_permission("schedule:read")])
def list_rules(business_id: str, db: Session = Depends(get_db)):
    rules = db.execute(
        select(ScheduleRule).where(ScheduleRule.business_id == business_id)
        .order_by(ScheduleRule.created_at.desc())
    ).scalars().all()
    return [
        {
            "id": r.id,
            "raw_text": r.raw_text,
            "rule_type": r.rule_type,
            "parsed_json": json.loads(r.parsed_json) if r.parsed_json else None,
            "is_active": r.is_active,
            "created_at": r.created_at,
        }
        for r in rules
    ]


@router.post("/rules", status_code=201, dependencies=[require_permission("schedule:write")])
def add_rule(
    business_id: str,
    payload: RuleCreate,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    raw = payload.raw_text.strip()
    if not raw:
        raise HTTPException(400, "Rule text cannot be empty")

    # Parse via Ollama (best-effort — saves rule even if parsing fails)
    try:
        parsed = parse_rule(raw)
    except RuntimeError:
        # Ollama unreachable — still save rule as constraint with no parsed JSON
        parsed = {"rule_type": "constraint", "parsed_json": None}

    rule = ScheduleRule(
        business_id=business_id,
        raw_text=raw,
        rule_type=parsed["rule_type"],
        parsed_json=parsed.get("parsed_json"),
        is_active=True,
        created_by_user_id=user.id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return {
        "id": rule.id,
        "raw_text": rule.raw_text,
        "rule_type": rule.rule_type,
        "parsed_json": json.loads(rule.parsed_json) if rule.parsed_json else None,
        "is_active": rule.is_active,
    }


@router.patch("/rules/{rule_id}", dependencies=[require_permission("schedule:write")])
def toggle_rule(
    business_id: str,
    rule_id: str,
    is_active: bool,
    db: Session = Depends(get_db),
):
    rule = db.execute(
        select(ScheduleRule).where(
            ScheduleRule.id == rule_id,
            ScheduleRule.business_id == business_id,
        )
    ).scalar_one_or_none()
    if not rule:
        raise HTTPException(404, "Rule not found")
    rule.is_active = is_active
    db.commit()
    return {"id": rule.id, "is_active": rule.is_active}


@router.delete("/rules/{rule_id}", status_code=204, dependencies=[require_permission("schedule:write")])
def delete_rule(
    business_id: str,
    rule_id: str,
    db: Session = Depends(get_db),
):
    rule = db.execute(
        select(ScheduleRule).where(
            ScheduleRule.id == rule_id,
            ScheduleRule.business_id == business_id,
        )
    ).scalar_one_or_none()
    if not rule:
        raise HTTPException(404, "Rule not found")
    db.delete(rule)
    db.commit()


# ── Generate ──────────────────────────────────────────────────────────────────

@router.post("/generate", dependencies=[require_permission("schedule:write")])
def trigger_generate(
    business_id: str,
    payload: GenerateRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    try:
        week_start = datetime.fromisoformat(payload.week_start).replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(400, f"Invalid week_start date: {payload.week_start!r}")

    # Record agent run
    run = AgentRun(
        agent_id=None,  # system-triggered (no API key agent)
        status=AgentRunStatus.running,
        started_at=datetime.now(timezone.utc),
    )
    # Use correlation_id to track business + week
    run.correlation_id = f"{business_id}:{payload.week_start}"
    db.add(run)
    db.flush()

    try:
        result = generate_schedule(
            business_id=business_id,
            week_start=week_start,
            db=db,
            model=payload.model,
        )
        run.status = AgentRunStatus.success
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        return {"run_id": run.id, **result}

    except RuntimeError as e:
        run.status = AgentRunStatus.failed
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(503, str(e))

    except Exception as e:
        run.status = AgentRunStatus.failed
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(500, f"Agent error: {e}")


# ── Run history ───────────────────────────────────────────────────────────────

@router.get("/runs", dependencies=[require_permission("schedule:read")])
def list_runs(business_id: str, db: Session = Depends(get_db)):
    runs = db.execute(
        select(AgentRun)
        .where(AgentRun.correlation_id.like(f"{business_id}:%"))
        .order_by(AgentRun.started_at.desc())
        .limit(50)
    ).scalars().all()
    return [
        {
            "id": r.id,
            "status": r.status,
            "week": r.correlation_id.split(":", 1)[1] if r.correlation_id else None,
            "started_at": r.started_at,
            "finished_at": r.finished_at,
        }
        for r in runs
    ]
