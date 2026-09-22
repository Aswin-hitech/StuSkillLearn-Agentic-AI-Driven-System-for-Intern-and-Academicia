from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import AcademicianProfile, CompanyProfile, EmailActionToken, InstitutionProfile, RefreshSession, StudentProfile, User
from app.security import (
    constant_time_token_match,
    create_access_token,
    create_refresh_secret,
    hash_password,
    hash_refresh_secret,
    password_needs_rehash,
    verify_password,
)

from app.timeutils import ensure_utc, utc_now

ROLE_STUDENT = "STUDENT"
ROLE_COMPANY = "COMPANY"
ROLE_ACADEMICIAN = "ACADEMICIAN"
ROLE_INSTITUTION = "INSTITUTION"
ROLE_ADMIN = "ADMIN"
PUBLIC_ROLES = {ROLE_STUDENT, ROLE_COMPANY, ROLE_ACADEMICIAN, ROLE_INSTITUTION}
ALL_ROLES = PUBLIC_ROLES | {ROLE_ADMIN}


class AuthPayload(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            raise ValueError("Enter a valid email")
        return email

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if not any(ch.islower() for ch in value) or not any(ch.isupper() for ch in value) or not any(ch.isdigit() for ch in value):
            raise ValueError("Password must include uppercase, lowercase and a number")
        return value


class LoginPayload(BaseModel):
    email: str
    password: str


class EmailAddressPayload(BaseModel):
    email: str = Field(min_length=5, max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            raise ValueError("Enter a valid email")
        return email


class ActionTokenPayload(BaseModel):
    token: str = Field(min_length=20, max_length=512)


class PasswordResetPayload(ActionTokenPayload):
    password: str = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if not any(ch.islower() for ch in value) or not any(ch.isupper() for ch in value) or not any(ch.isdigit() for ch in value):
            raise ValueError("Password must include uppercase, lowercase and a number")
        return value


class UserResponse(BaseModel):
    public_id: str
    email: str
    role: str
    email_verified: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


def register_user(db: Session, email: str, password: str, role: str) -> User:
    role = role.upper()
    if role not in PUBLIC_ROLES:
        raise HTTPException(status_code=400, detail="Unsupported portal role")
    if len(password) < 12:
        raise HTTPException(status_code=422, detail="Password must be at least 12 characters")
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=email,
        password_hash=hash_password(password),
        role=role,
        email_verified=not settings.require_email_verification,
    )
    db.add(user)
    db.flush()
    if role == ROLE_STUDENT:
        db.add(StudentProfile(user_id=user.id, name=email.split("@", 1)[0].replace(".", " ").title()))
    elif role == ROLE_COMPANY:
        db.add(CompanyProfile(user_id=user.id, company_name="New Industry Partner", verified=False, verification_status="PENDING"))
    elif role == ROLE_ACADEMICIAN:
        db.add(AcademicianProfile(user_id=user.id, name=email.split("@", 1)[0].replace(".", " ").title()))
    elif role == ROLE_INSTITUTION:
        db.add(InstitutionProfile(user_id=user.id, institution_name="New Institution", verified=False, verification_status="PENDING"))
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    if not user or not verify_password(password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    user.last_login_at = utc_now()
    db.commit()
    db.refresh(user)
    return user


def _user_response(user: User) -> UserResponse:
    return UserResponse(public_id=user.public_id, email=user.email, role=user.role, email_verified=user.email_verified)


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    common = {
        "httponly": True,
        "secure": settings.secure_cookies,
        "samesite": settings.cookie_samesite,
        "domain": settings.cookie_domain,
        "path": "/",
    }
    response.set_cookie(settings.access_cookie_name, access_token, max_age=settings.jwt_expire_minutes * 60, **common)
    response.set_cookie(settings.refresh_cookie_name, refresh_token, max_age=settings.refresh_token_days * 86400, **common)


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(settings.access_cookie_name, domain=settings.cookie_domain, path="/")
    response.delete_cookie(settings.refresh_cookie_name, domain=settings.cookie_domain, path="/")


def issue_session(db: Session, user: User, request: Request, response: Response) -> TokenResponse:
    access = create_access_token(user.public_id, user.role)
    refresh_secret = create_refresh_secret()
    session = RefreshSession(
        user_id=user.id,
        token_hash=hash_refresh_secret(refresh_secret),
        expires_at=utc_now() + timedelta(days=settings.refresh_token_days),
        user_agent=request.headers.get("user-agent", "")[:500],
        ip_address=(request.client.host if request.client else "")[:64],
    )
    db.add(session)
    db.commit()
    # Prefix the opaque secret with the session public id so lookup remains O(1).
    refresh_token = f"{session.public_id}.{refresh_secret}"
    _set_auth_cookies(response, access, refresh_token)
    return TokenResponse(
        access_token=access,
        expires_in=settings.jwt_expire_minutes * 60,
        user=_user_response(user),
    )


def rotate_refresh_session(db: Session, raw_token: str, request: Request, response: Response) -> TokenResponse:
    try:
        session_public_id, secret = raw_token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh session") from exc
    # Lock the refresh-session row on databases that support it so the same
    # opaque refresh token cannot be rotated concurrently into multiple live sessions.
    session = db.scalar(
        select(RefreshSession)
        .where(RefreshSession.public_id == session_public_id)
        .with_for_update()
    )
    now = utc_now()
    if (
        not session
        or session.revoked_at is not None
        or ensure_utc(session.expires_at) <= now
        or not constant_time_token_match(secret, session.token_hash)
    ):
        raise HTTPException(status_code=401, detail="Refresh session expired or revoked")
    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Account unavailable")
    session.revoked_at = now
    db.flush()
    return issue_session(db, user, request, response)


def revoke_refresh_session(db: Session, raw_token: str | None) -> None:
    if not raw_token or "." not in raw_token:
        return
    session_public_id, secret = raw_token.split(".", 1)
    session = db.scalar(select(RefreshSession).where(RefreshSession.public_id == session_public_id))
    if session and session.revoked_at is None and constant_time_token_match(secret, session.token_hash):
        session.revoked_at = utc_now()
        db.commit()


def create_email_action_token(db: Session, user: User, purpose: str, minutes: int) -> str:
    now = utc_now()
    # Invalidate older unused tokens for the same purpose.
    previous = db.scalars(
        select(EmailActionToken).where(
            EmailActionToken.user_id == user.id,
            EmailActionToken.purpose == purpose,
            EmailActionToken.used_at.is_(None),
        )
    ).all()
    for item in previous:
        item.used_at = now
    raw = secrets.token_urlsafe(48)
    db.add(EmailActionToken(
        user_id=user.id,
        purpose=purpose,
        token_hash=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        expires_at=now + timedelta(minutes=minutes),
    ))
    db.commit()
    return raw


def consume_email_action_token(db: Session, raw_token: str, purpose: str) -> User:
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    item = db.scalar(select(EmailActionToken).where(EmailActionToken.token_hash == token_hash, EmailActionToken.purpose == purpose))
    now = utc_now()
    if not item or item.used_at is not None or ensure_utc(item.expires_at) <= now:
        raise HTTPException(status_code=400, detail="This link is invalid or has expired")
    user = db.get(User, item.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="This link is invalid or has expired")
    item.used_at = now
    db.flush()
    return user


def revoke_all_refresh_sessions(db: Session, user_id: int) -> None:
    now = utc_now()
    rows = db.scalars(select(RefreshSession).where(RefreshSession.user_id == user_id, RefreshSession.revoked_at.is_(None))).all()
    for row in rows:
        row.revoked_at = now


def get_current_user(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    access_cookie: Annotated[str | None, Cookie(alias=settings.access_cookie_name)] = None,
    db: Session = Depends(get_db),
) -> User:
    token: str | None = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    elif access_cookie:
        token = access_cookie
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    from app.security import decode_access_token
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    user = db.scalar(select(User).where(User.public_id == payload.get("sub")))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Authentication required")
    if settings.require_email_verification and not user.email_verified:
        raise HTTPException(status_code=403, detail="Email verification required")
    return user


def require_roles(*roles: str):
    allowed = set(roles)

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="This portal is not available to your role")
        return user

    return dependency
