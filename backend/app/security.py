from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets

try:
    import bcrypt
except ImportError:  # Local review environments may not have optional wheels preinstalled.
    bcrypt = None
import jwt

from app.config import settings

LEGACY_PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
LEGACY_PASSWORD_HASH_ITERATIONS = 390_000


def _legacy_hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), LEGACY_PASSWORD_HASH_ITERATIONS).hex()
    return f"{LEGACY_PASSWORD_HASH_ALGORITHM}${LEGACY_PASSWORD_HASH_ITERATIONS}${salt}${derived}"


def hash_password(password: str) -> str:
    if bcrypt is None:
        if settings.is_production:
            raise RuntimeError("bcrypt is required in production")
        return _legacy_hash_password(password)
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _verify_legacy_pbkdf2(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt, expected = password_hash.split("$", 3)
        iterations = int(iterations_text)
    except ValueError:
        return False
    if algorithm != LEGACY_PASSWORD_HASH_ALGORITHM:
        return False
    actual = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    ).hex()
    return hmac.compare_digest(actual, expected)


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith(f"{LEGACY_PASSWORD_HASH_ALGORITHM}$"):
        return _verify_legacy_pbkdf2(password, password_hash)
    if bcrypt is None:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return password_hash.startswith(f"{LEGACY_PASSWORD_HASH_ALGORITHM}$")


def create_access_token(public_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": public_id,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expire_minutes)).timestamp()),
        "jti": secrets.token_hex(12),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            raise ValueError("Invalid authentication token")
        return payload
    except jwt.PyJWTError as exc:
        raise ValueError("Invalid authentication token") from exc


def create_refresh_secret() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def constant_time_token_match(secret: str, expected_hash: str) -> bool:
    return hmac.compare_digest(hash_refresh_secret(secret), expected_hash)
