from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AcademicianProfile, CompanyProfile, InstitutionProfile, StudentProfile, User
from app.security import create_access_token, decode_access_token, hash_password, verify_password

ROLE_STUDENT = "STUDENT"
ROLE_COMPANY = "COMPANY"
ROLE_ACADEMICIAN = "ACADEMICIAN"
ROLE_INSTITUTION = "INSTITUTION"
PUBLIC_ROLES = {ROLE_STUDENT, ROLE_COMPANY, ROLE_ACADEMICIAN, ROLE_INSTITUTION}


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


class LoginPayload(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    public_id: str
    email: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


def register_user(db: Session, email: str, password: str, role: str) -> User:
    role = role.upper()
    if role not in PUBLIC_ROLES:
        raise HTTPException(status_code=400, detail="Unsupported portal role")
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=email, password_hash=hash_password(password), role=role)
    db.add(user)
    db.flush()
    if role == ROLE_STUDENT:
        db.add(StudentProfile(user_id=user.id, name=email.split("@", 1)[0].replace(".", " ").title()))
    elif role == ROLE_COMPANY:
        db.add(CompanyProfile(user_id=user.id, company_name="New Industry Partner", verified=False))
    elif role == ROLE_ACADEMICIAN:
        db.add(AcademicianProfile(user_id=user.id, name=email.split("@", 1)[0].replace(".", " ").title()))
    elif role == ROLE_INSTITUTION:
        db.add(InstitutionProfile(user_id=user.id, institution_name="New Institution"))
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    if not user or not verify_password(password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return user


def token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.public_id, user.role),
        user=UserResponse(public_id=user.public_id, email=user.email, role=user.role),
    )


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    user = db.scalar(select(User).where(User.public_id == payload.get("sub")))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_roles(*roles: str):
    allowed = set(roles)
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="This portal is not available to your role")
        return user
    return dependency
