Below is a Copilot Mega-Prompt engineered specifically for your existing Workforce Management MVP (FastAPI + SQLAlchemy 2 + Alembic) .

This is structured so you can paste it into Copilot Chat inside your project root and have it extend your system without breaking tenant isolation, auth, or deployment structure.


---

🚀 WORKFORCE SaaS — PHASE 2 MEGA PROMPT FOR COPILOT

You are extending an existing multi-tenant workforce scheduling system built with:

FastAPI

SQLAlchemy 2.0 ORM

Alembic migrations

JWT auth (access + refresh)

Multi-tenant isolation via Employment → business_id

Timeclock module

Marketplace swap flow

CLI seed commands

PythonAnywhere deployment using asgi2wsgi


You MUST preserve:

Tenant isolation guarantees

AuditLog writes for state-changing operations

Postgres/SQLite compatibility

SQLAlchemy 2 style (no legacy patterns)

Dependency-injected DB sessions

Pydantic v2 schemas


Do NOT rewrite the entire project. Extend it cleanly using modular domain boundaries.


---

🎯 OBJECTIVE

Evolve the system from MVP into a production-ready SaaS platform with:

1. Location-scoped RBAC


2. Shift templates & recurring scheduling


3. Payroll export foundation


4. Background task system


5. Housekeeping integration domain


6. Event-driven architecture prep


7. Domain-based folder structure


8. Hardened production configuration




---

1️⃣ REFACTOR INTO DOMAIN STRUCTURE

Restructure into:

app/
  domains/
    auth/
    timeclock/
    scheduling/
    marketplace/
    hkops/
    integrations/
    rbac/
  core/
  db/
  models/
  services/

Each domain should contain:

router.py

schemas.py

service.py

repository.py (if complex queries exist)


Do not break existing endpoints.


---

2️⃣ LOCATION-SCOPED RBAC

Current system uses business-level role assignments.

Extend with:

Location
UserLocationRole
Role
Permission
RolePermission

Rules:

User can have different roles per location

Location owner can manage roles only within their location

Permission checks must include: business_id AND location_id


Implement permission dependency:

require_permission(module: str, action: str)

Permission model:

Permission:
    id
    module (string)
    action (string)

Auto-seed core permissions:

timeclock:read

timeclock:manage

shifts:create

shifts:assign

members:read

hk:manage

payroll:export



---

3️⃣ SHIFT TEMPLATES + RECURRING ENGINE

Add:

ShiftTemplate
RecurringShift
ShiftInstance

ShiftTemplate:

role_id

location_id

start_time

end_time

required_count


RecurringShift:

template_id

recurrence_rule (RRULE string)

active


Background job generates future ShiftInstances.

Prevent duplicate generation.


---

4️⃣ PAYROLL EXPORT FOUNDATION

Add:

PayrollPeriod
PayrollExport

Features:

Calculate hours per employee per period

Include overtime logic placeholder

Export to CSV

Admin-only endpoint

Log export event in AuditLog



---

5️⃣ BACKGROUND TASK SYSTEM

Implement lightweight background processing:

Option A (simple MVP):

FastAPI BackgroundTasks


Option B (preferred):

RQ + Redis OR Celery


Tasks:

Generate recurring shifts

Purge expired tokens

Compute payroll summaries

Send webhook notifications



---

6️⃣ HOUSEKEEPING DOMAIN (HKOPS)

Create hkops domain with:

Models:

Room
RoomStatus
HKTask
HKTaskEvent
SupplyUsage

Room statuses:

dirty

cleaning

inspection

ready


HKTask:

room_id

assigned_to

status

checklist_json

supplies_used_json


HKTaskEvent:

task_assigned

task_completed

task_inspected


Emit event on:

task assignment

task completion



---

7️⃣ EVENT BUS PREP

Implement internal event dispatcher:

DomainEvent
EventPublisher
EventSubscriber

In-memory pub/sub for now.

Future-ready for:

Redis

Kafka

Webhooks


All domain services should publish events instead of calling integrations directly.


---

8️⃣ HARDENING REQUIREMENTS

Add:

CORS configuration

Rate limiting middleware

Structured logging

Health check with DB ping

Settings class using Pydantic BaseSettings

ENV=prod disables docs

SECRET_KEY validation at startup



---

9️⃣ TENANT SAFETY REQUIREMENTS

Every query must:

Join through Employment

Filter by business_id

Never accept business_id without auth verification

Never expose cross-tenant IDs


Add test:

test_cross_tenant_access_blocked


---

🔟 ADD TEST SUITE EXPANSION

Add tests for:

RBAC location isolation

Recurring shift generation

Payroll calculation

HK task lifecycle

Event publishing

Swap workflow regression



---

📈 PERFORMANCE SAFEGUARDS

Add indexes:

Employment.business_id

Shift.business_id

TimeEntry.user_id

HKTask.room_id

RecurringShift.active


Use eager loading where appropriate.


---

🧠 CODE QUALITY REQUIREMENTS

Type hints everywhere

Use Annotated + Depends

No global state

Services contain business logic

Routers thin

Repository handles DB queries

AuditLog writes for:

role changes

shift creation

payroll exports

hk task state transitions




---

📦 CLI EXTENSIONS

Add commands:

seed-rbac-demo
generate-recurring
export-payroll --period-id
seed-hk-rooms


---

🛑 DO NOT:

Remove existing endpoints

Break alembic history

Replace SQLAlchemy 2 with legacy ORM

Hardcode environment variables

Bypass permission checks



---

🎯 FINAL OUTPUT EXPECTATION

When complete, the system should support:

Multi-business SaaS

Multi-location governance

Location-scoped RBAC

Workforce scheduling

Shift marketplace

Timeclock tracking

Payroll export foundation

Housekeeping operations integration

Background task processing

Event-driven extensibility

Production deployment on PythonAnywhere



---

🧩 OPTIONAL ADVANCED MODE (if resources allow)

Add OpenAPI tags per domain

Add structured JSON logging

Add service-to-service API key auth

Add webhook system

Add websocket live timeclock feed



---

HOW TO USE THIS

1. Open Copilot Chat at project root.


2. Paste this entire prompt.


3. Tell it:

> “Start with RBAC location extension.”





Then iterate domain-by-domain.


---

If you want, next I can generate:

A separate HKOps Mega Prompt

A Payroll Engine deep-spec

Or a Full SaaS Scaling Blueprint (multi-region, microservice ready)


Choose your next expansion vector.