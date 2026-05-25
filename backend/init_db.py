"""
Database initialization script for C2 Coordinator.

Creates all tables via SQLAlchemy Base.metadata.create_all() and seeds
default records (admin user, auto_push_config, traffic_obfuscation_config).
Safe to run repeatedly -- all operations are idempotent.

Usage:
    cd backend/
    python init_db.py
"""

import sys
import os

# Ensure the backend/ directory is first on sys.path so that
# "from app.xxx" imports resolve correctly regardless of CWD.
_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Also ensure the parent directory of backend/ is available if needed
_parent_dir = os.path.dirname(_backend_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# pydantic-settings reads .env relative to CWD by default.
os.chdir(_backend_dir)

from app.core.database import engine, Base, SessionLocal
from app.utils.password import hash_password

# Import every model so they are registered on Base.metadata before create_all
from app.models.user import User                      # noqa: F401
from app.models.task import AttackTask                # noqa: F401
from app.models.coordination import (                 # noqa: F401
    SessionMapping,
    AutoPushConfig,
)
from app.models.log import OperationLog               # noqa: F401
from app.models.advanced import (                     # noqa: F401
    IpPool,
    DomainDnsConfig,
    TrafficObfuscationConfig,
)


def create_tables():
    """Create all tables that do not yet exist (idempotent)."""
    print("[1/3] Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("      Tables ensured (8 tables registered).")


def create_default_user():
    """Insert the default admin user if none exists."""
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            print("[2/3] Default admin user already exists -- skipping.")
            return

        hashed = hash_password("admin123")
        admin = User(username="admin", password_hash=hashed)
        db.add(admin)
        db.commit()
        print("[2/3] Default admin user created (username: admin, password: admin123).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_default_configs():
    """Insert default configuration rows when their tables are empty."""
    db = SessionLocal()
    try:
        apc = db.query(AutoPushConfig).first()
        if apc is None:
            db.add(AutoPushConfig(enabled=False))
            db.commit()
            print("      auto_push_config default record inserted (enabled=false).")
        else:
            print("      auto_push_config record already exists -- skipping.")

        to_config = db.query(TrafficObfuscationConfig).first()
        if to_config is None:
            db.add(
                TrafficObfuscationConfig(
                    encryption="AES-256",
                    random_headers=True,
                    data_chunking=True,
                )
            )
            db.commit()
            print("      traffic_obfuscation_config default record inserted (encryption=AES-256).")
        else:
            print("      traffic_obfuscation_config record already exists -- skipping.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("  C2 Coordinator — Database Initialization")
    print("=" * 60)
    create_tables()
    create_default_user()
    print("[3/3] Seeding default configuration records...")
    create_default_configs()
    print("=" * 60)
    print("  Database initialization completed successfully.")
    print("=" * 60)
