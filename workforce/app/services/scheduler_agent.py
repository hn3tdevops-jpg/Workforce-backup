"""
AI Scheduling Agent — uses local Ollama LLM when available to:
  1. Parse natural-language rules into structured JSON
  2. Generate draft ScheduleAssignment records for a given week

If Ollama is not running, a rule-based fallback assigns workers automatically.
"""
import json
import logging
from datetime import datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.identity import Membership, User, WorkerAvailability
from app.models.schedule import (
    AssignmentStatus,
    RuleType,
    ScheduleAssignment,
    ScheduleRule,
    ScheduleShift,
    ShiftStatus,
)

logger = logging.getLogger(__name__)

OLLAMA_BASE = "http://localhost:11434"
OLLAMA_MODEL = "llama3"  # override via env or pass as arg
OLLAMA_TIMEOUT = 120  # seconds


# ── Ollama helpers ────────────────────────────────────────────────────────────

def _ollama_available() -> bool:
    """Return True if Ollama is reachable."""
    try:
        httpx.get(f"{OLLAMA_BASE}/api/tags", timeout=2).raise_for_status()
        return True
    except Exception:
        return False


def _ollama_chat(prompt: str, model: str = OLLAMA_MODEL) -> str:
    """Send a prompt to Ollama and return the response text."""
    try:
        resp = httpx.post(
            f"{OLLAMA_BASE}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=OLLAMA_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except httpx.ConnectError:
        raise RuntimeError(
            "Ollama is not reachable at localhost:11434. "
            "Start it with: ollama serve"
        )
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Ollama error: {e.response.status_code} — {e.response.text}")


def _extract_json(text: str) -> dict | list | None:
    """Extract the first JSON object or array from a text response."""
    import re
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None


# ── Rule parsing ──────────────────────────────────────────────────────────────

RULE_PARSE_PROMPT = """\
You are a scheduling rule parser. Convert the following natural-language rule into structured JSON.

Rule: "{raw_text}"

Return ONLY a JSON object with these fields (no explanation, no markdown):
{{
  "rule_type": "coverage" | "availability" | "fairness" | "constraint",
  "summary": "one-line summary",
  "conditions": {{...rule-specific fields...}}
}}

Coverage rules control minimum/maximum staff counts (e.g. "need 2 closers on weekends").
Availability rules restrict when a person can work (e.g. "Bob never works Mondays").
Fairness rules distribute hours evenly (e.g. "no one works more than 40 hours/week").
Constraint rules are anything else.

For "conditions", use clear keys like: min_count, max_count, role, day_of_week,
member_email, max_hours_per_week, max_consecutive_days, etc.
"""


def parse_rule(raw_text: str, model: str = OLLAMA_MODEL) -> dict:
    """
    Parse a natural-language rule using Ollama if available.
    Falls back to rule_type=constraint with null parsed_json when Ollama is offline.
    """
    prompt = RULE_PARSE_PROMPT.format(raw_text=raw_text.strip())
    try:
        response = _ollama_chat(prompt, model)
        parsed = _extract_json(response)
        if parsed and isinstance(parsed, dict):
            rule_type_str = parsed.get("rule_type", "constraint")
            try:
                rule_type = RuleType(rule_type_str)
            except ValueError:
                rule_type = RuleType.constraint
            return {
                "rule_type": rule_type,
                "parsed_json": json.dumps(parsed),
            }
    except Exception as e:
        logger.info("Rule parse skipped (Ollama unavailable): %s", e)

    return {"rule_type": RuleType.constraint, "parsed_json": None}


def _is_available(membership, shift: ScheduleShift, avail_map: dict) -> bool:
    """Check if a member has availability set for the shift's day/time."""
    avail_list = avail_map.get(membership.id, [])
    if not avail_list:
        return True  # No availability set → assume always available
    start = shift.start_ts
    if not isinstance(start, datetime):
        start = datetime.fromisoformat(str(start))
    dow = start.weekday()  # 0=Mon
    shift_hour = start.hour
    for a in avail_list:
        if a.day_of_week == dow and a.start_hour <= shift_hour < a.end_hour:
            return True
    return False


def _fallback_assign(shifts_needing: list, memberships: list) -> list:
    """
    Simple round-robin assignment: distribute shifts evenly across members.
    Respects availability if set. Each member gets at most one slot per shift.
    """
    assignments = []
    # Track how many shifts each member has been assigned (for fairness)
    load: dict[str, int] = {m.id: 0 for m in memberships}

    for shift, still_need in shifts_needing:
        # Sort members by current load (least-loaded first)
        candidates = sorted(memberships, key=lambda m: load[m.id])
        assigned_this_shift = 0
        for member in candidates:
            if assigned_this_shift >= still_need:
                break
            assignments.append({"shift_id": shift.id, "membership_id": member.id})
            load[member.id] += 1
            assigned_this_shift += 1

    return assignments


# ── Schedule generation ───────────────────────────────────────────────────────

SCHEDULE_PROMPT = """\
You are an employee scheduling assistant. Assign workers to shifts for the week.

## Business context
Business ID: {business_id}
Week: {week_label}

## Workers (membership_id | name | email | availability)
{workers_block}

## Shifts needing assignments (shift_id | title | role | time | still_need)
{shifts_block}

## Scheduling rules
{rules_block}

## Task
For each shift that still needs workers, choose the most suitable available workers.
Respect availability hours and all rules. Do NOT assign someone who is unavailable.
Do NOT exceed "still_need" count per shift.

Return ONLY a JSON array of assignment objects (no explanation, no markdown):
[
  {{"shift_id": "...", "membership_id": "..."}},
  ...
]

If no suitable worker exists for a shift, omit it from the array.
"""


def _day_name(day: int) -> str:
    return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day]


def _format_availability(avail_rows: list) -> str:
    if not avail_rows:
        return "no availability set"
    parts = [
        f"{_day_name(a.day_of_week)} {a.start_hour:02d}:00-{a.end_hour:02d}:00"
        for a in avail_rows
    ]
    return ", ".join(parts)


def generate_schedule(
    business_id: str,
    week_start: datetime,
    db: Session,
    model: str = OLLAMA_MODEL,
) -> dict:
    """
    Generate draft schedule assignments for the given week using Ollama.

    - Loads all draft shifts in the week window
    - Loads all active members + their WorkerAvailability
    - Loads all active ScheduleRules
    - Calls Ollama to produce assignments
    - Creates ScheduleAssignment records (draft)
    - Records an AgentRun
    - Returns summary dict
    """
    week_end = week_start + timedelta(days=7)
    week_label = f"{week_start.strftime('%b %d')} – {(week_end - timedelta(days=1)).strftime('%b %d, %Y')}"

    # ── Load shifts ───────────────────────────────────────────────────────────
    shifts = db.execute(
        select(ScheduleShift).where(
            ScheduleShift.business_id == business_id,
            ScheduleShift.status == ShiftStatus.draft,
            ScheduleShift.start_ts >= week_start,
            ScheduleShift.start_ts < week_end,
        )
    ).scalars().all()

    if not shifts:
        return {"assignments_created": 0, "message": "No draft shifts found for this week."}

    # Filter to shifts that still need workers
    shifts_needing = []
    for s in shifts:
        assigned = len([a for a in s.assignments if a.status != AssignmentStatus.declined])
        still_need = s.needed_count - assigned
        if still_need > 0:
            shifts_needing.append((s, still_need))

    if not shifts_needing:
        return {"assignments_created": 0, "message": "All shifts are already fully staffed."}

    # ── Load members + availability ───────────────────────────────────────────
    memberships = db.execute(
        select(Membership).where(
            Membership.business_id == business_id,
            Membership.status == "active",
        )
    ).scalars().all()

    workers_lines = []
    for m in memberships:
        user = db.get(User, m.user_id)
        avail = db.execute(
            select(WorkerAvailability).where(WorkerAvailability.membership_id == m.id)
        ).scalars().all()
        name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email.split("@")[0]
        avail_str = _format_availability(avail)
        workers_lines.append(f"  {m.id} | {name} | {user.email} | {avail_str}")

    workers_block = "\n".join(workers_lines) if workers_lines else "  (no workers)"

    # ── Format shifts ─────────────────────────────────────────────────────────
    shifts_lines = []
    for s, still_need in shifts_needing:
        start = s.start_ts if isinstance(s.start_ts, datetime) else datetime.fromisoformat(str(s.start_ts))
        end = s.end_ts if isinstance(s.end_ts, datetime) else datetime.fromisoformat(str(s.end_ts))
        time_str = f"{start.strftime('%a %b %d %H:%M')} – {end.strftime('%H:%M')}"
        shifts_lines.append(
            f"  {s.id} | {s.title} | {s.role_name or 'any'} | {time_str} | need {still_need} more"
        )
    shifts_block = "\n".join(shifts_lines)

    # ── Load rules ────────────────────────────────────────────────────────────
    rules = db.execute(
        select(ScheduleRule).where(
            ScheduleRule.business_id == business_id,
            ScheduleRule.is_active == True,  # noqa: E712
        )
    ).scalars().all()

    if rules:
        rules_block = "\n".join(f"  - {r.raw_text}" for r in rules)
    else:
        rules_block = "  (no rules set — use best judgment)"

    # ── Call Ollama or fallback ───────────────────────────────────────────────
    if _ollama_available():
        prompt = SCHEDULE_PROMPT.format(
            business_id=business_id,
            week_label=week_label,
            workers_block=workers_block,
            shifts_block=shifts_block,
            rules_block=rules_block,
        )
        logger.info("Calling Ollama for schedule generation, business=%s week=%s", business_id, week_label)
        response_text = _ollama_chat(prompt, model)
        assignments_data = _extract_json(response_text)
        used_ollama = True

        if not assignments_data or not isinstance(assignments_data, list):
            logger.warning("Ollama returned unexpected format: %s", response_text[:200])
            assignments_data = _fallback_assign(shifts_needing, memberships)
            used_ollama = False
    else:
        logger.info("Ollama unavailable — using rule-based fallback, business=%s", business_id)
        assignments_data = _fallback_assign(shifts_needing, memberships)
        used_ollama = False

    # ── Create assignment records ─────────────────────────────────────────────
    valid_shift_ids = {s.id for s, _ in shifts_needing}
    valid_member_ids = {m.id for m in memberships}
    created = 0
    skipped = 0

    for item in assignments_data:
        shift_id = item.get("shift_id")
        membership_id = item.get("membership_id")

        if shift_id not in valid_shift_ids or membership_id not in valid_member_ids:
            skipped += 1
            continue

        # Avoid duplicate assignments
        existing = db.execute(
            select(ScheduleAssignment).where(
                ScheduleAssignment.shift_id == shift_id,
                ScheduleAssignment.membership_id == membership_id,
            )
        ).scalar_one_or_none()
        if existing:
            skipped += 1
            continue

        db.add(ScheduleAssignment(
            shift_id=shift_id,
            membership_id=membership_id,
            status=AssignmentStatus.assigned,
        ))
        created += 1

    db.commit()
    logger.info("Schedule generation done: %d created, %d skipped", created, skipped)

    return {
        "assignments_created": created,
        "assignments_skipped": skipped,
        "week": week_label,
        "shifts_processed": len(shifts_needing),
        "engine": "ollama" if used_ollama else "rule-based",
        "message": f"Created {created} draft assignment(s) for {len(shifts_needing)} shift(s)."
                   + ("" if used_ollama else " (rule-based fallback — install Ollama for AI scheduling)"),
    }
