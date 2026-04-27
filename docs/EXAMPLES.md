Examples: registration, login, invite, admin-create, and SQL seeding

1) Public registration (account only)

Request:
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"Secret123!","first_name":"Alice","last_name":"Example"}'

Typical response (201):
{
  "access_token": "<token>",
  "token_type": "bearer",
  "user": {"id":"<user-id>", "email":"alice@example.com"}
}

Note: /api/v1/auth/register creates a user account but does NOT create any Business or Membership.

2) Login when user has no active membership (expected failure)

Request:
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"alice@example.com","password":"Secret123!"}'

Typical response (403):
{
  "detail": "User has no active memberships."
}

3) Seed a Business + active Membership (manual SQL example)

-- Create a tenant, business, and active membership for an existing user
INSERT INTO tenants (id, name, slug) VALUES ('11111111-1111-1111-1111-111111111111','T1','tenant-t1');
INSERT INTO businesses (id, tenant_id, name) VALUES ('22222222-2222-2222-2222-222222222222','11111111-1111-1111-1111-111111111111','Biz A');
-- membership: link user -> business as active and optionally is_owner
INSERT INTO memberships (id, user_id, business_id, status, is_owner) VALUES ('33333333-3333-3333-3333-333333333333','<user-id>','22222222-2222-2222-2222-222222222222','active', true);

After creating the membership, /auth/login will succeed for that user.

4) Login after membership exists (success)

Request: same as step 2
Response (200):
{
  "access_token": "<token>",
  "token_type": "bearer",
  "user": {"id":"<user-id>", "email":"alice@example.com"}
}

5) GET /api/v1/auth/me (example)

Request:
curl -H "Authorization: Bearer <access_token>" http://localhost:8000/api/v1/auth/me

Response (200):
{
  "id": "<user-id>",
  "email": "alice@example.com",
  "memberships": [
    { "business_id": "22222222-2222-2222-2222-222222222222", "status": "active", "is_owner": true }
  ]
}

6) Admin: invite user to a business (creates invited user + invited membership)

Request:
curl -X POST "http://localhost:8000/api/v1/users/invite?business_id=22222222-2222-2222-2222-222222222222" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin-token>" \
  -d '{"email":"newhire@example.com","role_ids": []}'

Response (201):
{
  "membership_id": "<membership-id>",
  "user_id": "<user-id>",
  "email": "newhire@example.com"
}

Behavior notes:
- Invite creates a User with is_active=false (stub) and a Membership with status='invited'.
- Invite does not make the membership active until the invited user accepts or an admin activates it.

7) Admin: create a new user and seed an active membership & owner role

Request:
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin-token>" \
  -d '{"email":"manager@example.com","business_id":"22222222-2222-2222-2222-222222222222","is_owner": true}'

Response (201):
{
  "id":"<user-id>",
  "email":"manager@example.com",
  "memberships":[{"business_id":"22222222-2222-2222-2222-222222222222","status":"active","is_owner":true}]
}

Implementation constraints and policy reminders
- Login must NOT create memberships as a side-effect.
- Do NOT weaken RBAC, tenant scoping, or location scoping.
- Keep system User accounts separate from Employee records; employee-to-user linkage is explicit and business-controlled.

JWT payload example

When the API issues access tokens, the JWT typically includes claims like:
{
  "sub": "<user-id>",
  "iat": 1610000000,
  "exp": 1610003600,
  "type": "access",
  "superadmin": false,
  "business_id": "<business-id>"  # optional: set when token scoped to a business
}

Sample staging URLs

- Staging app: https://staging.workforce.example.com
- Staging API base: https://staging-api.workforce.example.com/api/v1
- Use the same endpoints as examples above, replacing http://localhost:8000 with the staging API base and include an Authorization header when required.

Acceptance test script (step-by-step)

1) Register a public user (expect account created but no workspace)

curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"acceptance+alice@example.com","password":"Secret123!"}'

Expect: 201, response includes access_token. Note: user has no memberships.

2) Attempt login (should fail because no active membership)

curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"acceptance+alice@example.com","password":"Secret123!"}'

Expect: 403 {"detail":"User has no active memberships."}

3) As admin, create a tenant/business and seed an active membership for the user (use admin-create or SQL)

Admin route (preferred):
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin-token>" \
  -d '{"email":"acceptance+alice@example.com","business_id":"22222222-2222-2222-2222-222222222222","is_owner":true}'

Or manual SQL seed (if automating test DB):
INSERT INTO tenants (id, name, slug) VALUES ('11111111-1111-1111-1111-111111111111','T1','tenant-t1');
INSERT INTO businesses (id, tenant_id, name) VALUES ('22222222-2222-2222-2222-222222222222','11111111-1111-1111-1111-111111111111','Biz A');
INSERT INTO memberships (id, user_id, business_id, status, is_owner) VALUES ('33333333-3333-3333-3333-333333333333','<user-id>','22222222-2222-2222-2222-222222222222','active', true);

Expect: 201 (admin-create) or SQL applied successfully.

4) Attempt login again for the user

curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"acceptance+alice@example.com","password":"Secret123!"}'

Expect: 200 with access_token.

5) Verify /auth/me returns membership context

curl -H "Authorization: Bearer <access_token>" http://localhost:8000/api/v1/auth/me

Expect: 200 and JSON containing memberships array with the seeded business and status 'active'.

6) Cleanup (optional): remove test tenant/business/membership rows if using a shared DB.

References
- See docs/CHANGELOG.md (2026-04-27) and PR #18 for implementation details and tests.