import hashlib

from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import User, AuthSession

def get_current_user(
        request: Request,
        db: Session = Depends(get_db)
) -> User:
    token = request.cookies.get("roombase_session")
    if token is None:
        raise HTTPException(
            status_code=401,
            detail="ログインが必要です"
        )
    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    auth_session = db.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == token_hash
        )
    )

    if auth_session is None or auth_session.revoked_at is not None or auth_session.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=401,
            detail="ログインが必要です"
        )

    user = db.get(User, auth_session.user_id)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="ユーザーが存在しません"
        )
    return user

def get_current_admin(
        user: User = Depends(get_current_user)
) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="管理者権限がありません"
        )
    return user