import argparse
import subprocess
import sys

from apps.api.app.cli.seed_demo import run_seed
from apps.api.app.cli.seed_hk_demo import run_hk_seed
from apps.api.app.cli.seed_roles import run_seed_roles


def cmd_init_db(_args):
    print("Running: alembic upgrade head")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=False,
    )
    sys.exit(result.returncode)


def cmd_seed_demo(_args):
    run_seed()


def cmd_match(args):
    from apps.api.app.core.db import db_session
    from apps.api.app.services.matching import find_candidates_for_shift

    with db_session() as db:
        try:
            candidates = find_candidates_for_shift(db, args.shift_id)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    if not candidates:
        print("No candidates found.")
        return

    print(f"{'Name':<30} {'Email':<35} {'Proficiency':>11} {'Availability':<12}")
    print("-" * 90)
    for c in candidates:
        name = f"{c['first_name']} {c['last_name']}"
        email = c["email"] or ""
        print(f"{name:<30} {email:<35} {c['proficiency']:>11} {c['availability_status'].value:<12}")


def cmd_purge(_args):
    """Purge expired messages and stale refresh tokens."""
    from datetime import datetime, timezone
    from sqlalchemy import delete
    from apps.api.app.core.db import db_session
    from apps.api.app.models.messaging import Message
    from apps.api.app.models.identity import RefreshToken

    now = datetime.now(timezone.utc)

    with db_session() as db:
        msg_result = db.execute(
            delete(Message).where(Message.expires_at < now)
        )
        print(f"Purged {msg_result.rowcount} expired messages.")

    with db_session() as db:
        token_result = db.execute(
            delete(RefreshToken).where(
                (RefreshToken.revoked == True) |  # noqa: E712
                (RefreshToken.expires_at < now)
            )
        )
        print(f"Purged {token_result.rowcount} stale refresh tokens.")


def main():
    parser = argparse.ArgumentParser(description="Workforce CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init-db", help="Run alembic upgrade head")
    sub.add_parser("seed-demo", help="Seed demo dataset")
    sub.add_parser("seed-hk-demo", help="Seed HKops demo rooms and tasks")
    sub.add_parser("purge", help="Purge expired messages and stale refresh tokens")
    sub.add_parser("seed-roles", help="Seed default RBAC roles and permissions")

    match_parser = sub.add_parser("match", help="Find candidates for a shift")
    match_parser.add_argument("--shift-id", required=True, help="Shift UUID")

    args = parser.parse_args()

    if args.command == "init-db":
        cmd_init_db(args)
    elif args.command == "seed-demo":
        cmd_seed_demo(args)
    elif args.command == "seed-hk-demo":
        run_hk_seed()
    elif args.command == "seed-roles":
        run_seed_roles()
    elif args.command == "match":
        cmd_match(args)
    elif args.command == "purge":
        cmd_purge(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
