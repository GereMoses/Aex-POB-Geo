from fastapi import Depends, HTTPException, status, Request, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Optional

from .database import get_db
from .security import verify_token
from .config import settings
# Temporarily bypass User model due to import issues
# from ..models.user import User
from sqlalchemy import text

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode and inspect claims
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Reject refresh tokens — they must not be used as access tokens
        if payload.get("type") == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh tokens cannot be used for API access",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Block mfa_pending tokens from accessing any endpoint except /mfa/verify
        if payload.get("mfa_pending"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MFA verification required — complete TOTP verification before accessing this endpoint",
            )

        # Allowlist: only genuine access tokens may authenticate API calls.
        # This rejects password-reset tokens (type=password_reset) — which are
        # emailed and would otherwise double as un-revokable bearer credentials.
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type for API access",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check token blacklist (covers logout and explicit revocation)
        jti = payload.get("jti", "")
        if jti:
            from .security import _is_blacklisted
            if _is_blacklisted(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except HTTPException:
        raise
    except JWTError:
        raise credentials_exception
    except Exception:
        raise credentials_exception
    
    # Look up user — check auth_user (BioTime primary) first, then users table
    user_data = None
    source = None

    # Try auth_user first (primary user store)
    result = db.execute(text("""
        SELECT id, username, email, NULL AS full_name, NULL AS phone, is_active, is_superuser,
               TRUE AS is_verified, COALESCE(is_global_admin, FALSE) AS is_global_admin
        FROM auth_user
        WHERE LOWER(email) = LOWER(:email) OR LOWER(username) = LOWER(:email)
    """), {"email": email}).fetchone()

    if result:
        user_data = result
        source = "auth_user"
    else:
        # Fallback: users table
        result = db.execute(text("""
            SELECT id, username, email, full_name, phone, is_active, is_superuser, is_verified,
                   COALESCE(is_global_admin, FALSE) AS is_global_admin
            FROM users
            WHERE email = :email OR username = :email
        """), {"email": email}).fetchone()
        if result:
            user_data = result
            source = "users"

    if user_data is None:
        raise credentials_exception

    if not user_data.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id, username, email, full_name, phone, is_active, is_superuser, is_verified, is_global_admin = (
        user_data.id, user_data.username, user_data.email,
        user_data.full_name if hasattr(user_data, 'full_name') else None,
        user_data.phone if hasattr(user_data, 'phone') else None,
        user_data.is_active, user_data.is_superuser, user_data.is_verified,
        user_data.is_global_admin
    )

    class SimpleUser:
        def __init__(self):
            self.id = user_id
            self.username = username
            self.email = email
            self.full_name = full_name
            self.phone = phone
            self.is_active = is_active
            self.is_superuser = is_superuser
            self.is_verified = is_verified
            self.is_global_admin = is_global_admin
            # Add personnel_id for role permission checks
            self.personnel_id = user_id  # For admin, personnel_id equals user_id
    
    return SimpleUser()


async def get_current_user_sse(
    request: Request,
    token: Optional[str] = Query(default=None),
    ticket: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Auth dependency for SSE/EventSource endpoints.

    Preference order (most secure → least secure):
    1. ?ticket=  — short-lived single-use ticket from POST /auth/sse-ticket (preferred)
    2. Authorization: Bearer header
    3. ?token=   — legacy fallback; kept for backwards compat; tokens appear in server logs
    """
    # 1. Short-lived ticket (best option — token never touches URL logs)
    if ticket:
        try:
            from .redis_client import get_redis_client
            r = get_redis_client()
            user_id_bytes = r.getdel(f"sse_ticket:{ticket}")
            if user_id_bytes:
                user_id = int(user_id_bytes)
                # Build a minimal user object from DB
                from .database import SessionLocal
                from sqlalchemy import text as _text
                _db = SessionLocal()
                try:
                    row = _db.execute(_text(
                        "SELECT id, username, email, is_active, is_superuser, "
                        "COALESCE(is_global_admin, FALSE) AS is_global_admin "
                        "FROM auth_user WHERE id = :uid AND is_active = TRUE"
                    ), {"uid": user_id}).fetchone()
                    if row:
                        return await _resolve_user_row(row)
                finally:
                    _db.close()
        except Exception:
            pass
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired ticket")

    # 2. Bearer header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return await _resolve_user(auth_header[7:], db)

    # 3. Token in query param (legacy — logs warning)
    if token:
        import logging as _logging
        _logging.getLogger(__name__).debug(
            "SSE auth via ?token= (URL) for %s — use ?ticket= instead", request.url.path
        )
        return await _resolve_user(token, db)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


async def _resolve_user_row(row):
    """Build a SimpleUser from a pre-fetched auth_user row (used by SSE ticket path)."""
    class SimpleUser:
        def __init__(self):
            self.id = row.id; self.username = row.username; self.email = row.email
            self.full_name = getattr(row, "full_name", None)
            self.phone = getattr(row, "phone", None)
            self.is_active = row.is_active; self.is_superuser = row.is_superuser
            self.is_verified = getattr(row, "is_verified", True)
            self.is_global_admin = getattr(row, "is_global_admin", False)
            self.personnel_id = row.id
    return SimpleUser()


async def _resolve_user(token: str, db: Session):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Single decode via verify_token — enforces signature, expiry, type, and blacklist.
        # verify_token returns the sub claim (email/username) or None.
        email = verify_token(token)
        if email is None:
            raise credentials_exception

        # verify_token does not check mfa_pending; do that here.
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("mfa_pending"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MFA verification required",
            )
    except HTTPException:
        raise
    except JWTError:
        raise credentials_exception

    result = db.execute(text("""
        SELECT id, username, email, NULL AS full_name, NULL AS phone, is_active, is_superuser,
               TRUE AS is_verified, COALESCE(is_global_admin, FALSE) AS is_global_admin
        FROM auth_user WHERE email = :email OR username = :email
    """), {"email": email}).fetchone()

    if not result:
        result = db.execute(text("""
            SELECT id, username, email, full_name, phone, is_active, is_superuser, is_verified,
                   COALESCE(is_global_admin, FALSE) AS is_global_admin
            FROM users WHERE email = :email OR username = :email
        """), {"email": email}).fetchone()

    if not result:
        raise credentials_exception

    if not result.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    class SimpleUser:
        def __init__(self):
            self.id = result.id; self.username = result.username; self.email = result.email
            self.full_name = getattr(result, 'full_name', None)
            self.phone = getattr(result, 'phone', None)
            self.is_active = result.is_active; self.is_superuser = result.is_superuser
            self.is_verified = getattr(result, 'is_verified', True)
            self.is_global_admin = result.is_global_admin
            self.personnel_id = result.id

    return SimpleUser()


async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
    current_user = Depends(get_current_active_user)
):
    """Get current superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
