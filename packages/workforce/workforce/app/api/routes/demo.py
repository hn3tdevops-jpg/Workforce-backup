from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_session
from apps.api.app.cli.seed_demo import run_seed_return
from apps.api.app.cli.seed_demo_accounts import run_demo_seed

router = APIRouter(tags=["demo"])


@router.post("/demo/seed")
def seed_demo(db: Session = Depends(get_session)):
    """Seed demo data and return key IDs for the UI."""
    return run_seed_return(db)


@router.post("/demo/seed-accounts")
def seed_demo_accounts():
    """Seed demo user accounts (owner + worker) with permissions."""
    return run_demo_seed()
