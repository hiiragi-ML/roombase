import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import engine
from .models import User, InviteCode

def create_invite():
    email = input("Admin email: ").strip().lower()

    with Session(engine) as session:
        admin = session.scalar(
            select(User).where(User.email == email)
        )
        if admin is None or admin.role != "admin":
            print("管理者権限がありません")
            return
        code = secrets.token_urlsafe(32)
        code_hash = hashlib.sha256(
            code.encode("utf-8")
        ).hexdigest()

        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        inviteCode = InviteCode(
            code_hash=code_hash,
            created_by=admin.id,
            expires_at=expires_at,
            revoked_at=None,
        )

        session.add(inviteCode)
        session.commit()

        print("招待コード: ", code)

if __name__ == '__main__':
    create_invite()