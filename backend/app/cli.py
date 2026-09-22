from __future__ import annotations

import argparse
import getpass
import os
import re

from sqlalchemy import select

from app.db import SessionLocal
from app.models import User
from app.security import hash_password


def _normalize_email(value: str) -> str:
    email = value.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError("Enter a valid administrator email address")
    return email


def _validate_password(value: str) -> str:
    if len(value) < 12:
        raise ValueError("Administrator password must be at least 12 characters")
    if not any(ch.islower() for ch in value) or not any(ch.isupper() for ch in value) or not any(ch.isdigit() for ch in value):
        raise ValueError("Administrator password must include uppercase, lowercase, and a number")
    return value


def create_admin(email: str, password: str) -> User:
    email = _normalize_email(email)
    password = _validate_password(password)
    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.email == email))
        if existing:
            if existing.role != "ADMIN":
                raise RuntimeError("That email already belongs to a non-admin account")
            existing.password_hash = hash_password(password)
            existing.is_active = True
            existing.email_verified = True
            db.commit()
            db.refresh(existing)
            return existing
        user = User(
            email=email,
            password_hash=hash_password(password),
            role="ADMIN",
            is_active=True,
            email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def main() -> None:
    parser = argparse.ArgumentParser(description="StuSkillLink administrative maintenance CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create-admin", help="Create or reset a privileged administrator account")
    create.add_argument("--email", default=os.getenv("STUSKILLLINK_ADMIN_EMAIL"))
    create.add_argument("--password", default=os.getenv("STUSKILLLINK_ADMIN_PASSWORD"))
    args = parser.parse_args()

    if args.command == "create-admin":
        email = args.email or input("Admin email: ").strip()
        password = args.password or getpass.getpass("Admin password: ")
        user = create_admin(email, password)
        print(f"Admin account ready: {user.email} ({user.public_id})")


if __name__ == "__main__":
    main()
