"""
Auth routes — public interface under /api/v1/auth.

This module re-exports the router defined in app.api.v1.auth.routes so that
it can be included from app.main or other entry points without duplication.

Endpoints (all prefixed /api/v1/auth):
  POST /token     — issue access + refresh tokens (OAuth2-style login)
  POST /login     — alias for /token
  POST /refresh   — rotate refresh token, issue new access token
  POST /logout    — revoke refresh token
  POST /register  — create new user account
  GET  /me        — return current authenticated user's profile
"""
from app.api.v1.auth.routes import router  # noqa: F401 — re-export
