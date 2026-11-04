import secrets
import hashlib

from datetime import datetime, timezone, timedelta

from pathlib import Path

from fastapi import FastAPI, HTTPException, Response, Request, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse

from sqlalchemy import text, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .models import Room, User, InviteCode, AuthSession, Reservation
from .schemas import RegisterRequest, LoginRequest, ReservationRequest
from .reservation_rules import JST, get_slot_id
from .security import hash_password, verify_password
from .database import engine, get_db
from .auth import get_current_user, get_current_admin
from .config import cookie_secure, get_allowed_origins
from .rate_limit import limiter


app = FastAPI(title="ROOMBASE API", docs_url=None, redoc_url=None)
app.state.limiter = limiter

ALLOWED_ORIGINS = set(get_allowed_origins())

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"]
)
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

@app.middleware("http")
async def check_origin(request: Request, call_next):
    unsafe_methods = {"POST", "PUT", "PATCH", "DELETE"}

    if(
        request.method in unsafe_methods
        and request.url.path.startswith("/api/")
    ):
        origin = request.headers.get("origin")

        if origin not in ALLOWED_ORIGINS:
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "許可されていない送信元です"
                }
            )

    return await call_next(request)

@app.get("/docs", include_in_schema=False)
def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="ROOMBASE API - Swagger UI",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
        swagger_favicon_url="/static/favicon.png"
    )

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/rooms")
def room_info():
    with Session(engine) as session:
        rooms = session.scalars(select(Room)).all()
        data = [
            {
                "id": room.id,
                "name": room.name,
                "description": room.description,
                "capacity": room.capacity,
                "color": room.color,
                "amenities": room.amenities
            } for room in rooms
        ]

    return {"rooms": data}

@app.get("/api/db-check")
def db_check():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT current_database()"))
        database_name = result.scalar_one()

    return {
        "status":"ok",
        "database": database_name,
    }

@app.get("/api/auth/me")
def get_me(user: User = Depends(get_current_user)):
        return {
            "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": user.role
            }
        }

@app.get("/api/dev/admin-check")
def admin_check(
    admin: User = Depends(get_current_admin)
):
    return {
        "message": "管理者として認証されました",
        "user_id": str(admin.id)
    }

@app.get("/api/reservations")
def get_reservations(
    from_: datetime = Query(alias="from"),
    to_: datetime = Query(alias="to"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if from_.utcoffset() is None or to_.utcoffset() is None:
        raise HTTPException(
            status_code=422,
            detail="タイムゾーン情報が確認できません"
        )
    if from_ >= to_:
        raise HTTPException(
            status_code=400,
            detail="開始時間と終了時間が不正です"
        )

    stmt = (
        select(Reservation, User.name)
        .join(User, Reservation.user_id == User.id)
        .where(Reservation.start_at < to_, Reservation.end_at > from_).order_by(Reservation.start_at)
    )

    rows = db.execute(stmt).all()

    data = [
        {
            "id": str(reservation.id),
            "room_id": reservation.room_id,
            "user_id": str(reservation.user_id),
            "user_name": user_name,
            "title": reservation.title,
            "note": reservation.note,
            "start_at": reservation.start_at.isoformat(),
            "end_at": reservation.end_at.isoformat(),
            "created_at": reservation.created_at.isoformat()
        } for reservation, user_name in rows
    ]

    return {"reservations": data}

@app.post('/api/auth/register', status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    name = data.name.strip()
    email = data.email.strip().lower()
    code_hash = hashlib.sha256(
        data.invite_code.encode("utf-8")
    ).hexdigest()

    invite = db.scalar(
        select(InviteCode).where(
            InviteCode.code_hash == code_hash
        )
    )

    if invite is None or invite.revoked_at is not None or invite.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="招待コードが無効です"
        )

    existing_user = db.scalar(
        select(User).where(User.email == email)
        )
    
    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail="このメールアドレスは登録済みです"
        )

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(data.password),
        role="member"
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="このメールアドレスは登録済みです"
        )

    db.refresh(user)

    return {
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
        }
    }

@app.post("/api/auth/login")
@limiter.limit("10/minute")
def login(request: Request, data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    email = data.email.strip().lower()
    user = db.scalar(
        select(User).where(
            User.email == email
        )
    )
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="メールアドレスまたはパスワードが正しくありません"
        )
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="メールアドレスまたはパスワードが正しくありません"
        )

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    auth_session = AuthSession(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        revoked_at=None
    )

    db.add(auth_session)
    db.commit()

    response.set_cookie(
        key="roombase_session",
        value=token,
        httponly=True,
        secure=cookie_secure(),
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        path="/"
    )

    return {
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
        }
    }

@app.post("/api/auth/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("roombase_session")
    if token is not None:
        token_hash = hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

        auth_session = db.scalar(
            select(AuthSession).where(
                AuthSession.token_hash == token_hash
            )
        )

        if auth_session is not None and auth_session.revoked_at is None:
            auth_session.revoked_at = datetime.now(timezone.utc)
            db.commit()

    response.delete_cookie(
        key="roombase_session",
        path="/",
        secure=cookie_secure(),
        httponly=True,
        samesite="lax"
    )

@app.post("/api/reservations", status_code=201)
def create_reservation(
    data: ReservationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.room_id != "main":
        raise HTTPException(
            status_code=400,
            detail="存在しない部室IDです"
        )

    title = data.title.strip()
    if title == "":
        raise HTTPException(
            status_code=400,
            detail="利用目的を入力してください"
        )

    if data.start_at.utcoffset() is None or data.end_at.utcoffset() is None:
        raise HTTPException(
            status_code=422,
            detail="タイムゾーン情報が必要です"
        )

    if data.start_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="過去の予約はできません"
        )

    start_jst = data.start_at.astimezone(JST)
    end_jst = data.end_at.astimezone(JST)

    if start_jst.date() != end_jst.date():
        raise HTTPException(
            status_code=400,
            detail="同じ日程で予約してください"
        )

    slot_id = get_slot_id(
        start_jst.time(),
        end_jst.time()
    )

    if slot_id == None:
        raise HTTPException(
            status_code=400,
            detail="予約枠が存在しません"
        )

    reservation = Reservation(
        room_id="main",
        user_id=user.id,
        reservation_date=start_jst.date(),
        slot_id=slot_id,
        title=title,
        note=data.note,
        start_at=data.start_at.astimezone(timezone.utc),
        end_at=data.end_at.astimezone(timezone.utc)
    )

    db.add(reservation)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()

        constraint_name = getattr(
            getattr(exc.orig, "diag", None),
            "constraint_name",
            None
        )

        if constraint_name == "uq_reservation_room_date_slot":
            raise HTTPException(
                status_code=409,
                detail="この予約枠はすでに予約されています"
            ) from exc
        raise

    db.refresh(reservation)

    return {
        "reservation": {
            "id": str(reservation.id),
            "room_id": reservation.room_id,
            "user_id": str(reservation.user_id),
            "user_name": user.name,
            "title": reservation.title,
            "note": reservation.note,
            "start_at": reservation.start_at.isoformat(),
            "end_at": reservation.end_at.isoformat(),
            "created_at": reservation.created_at.isoformat()
        }
    }

@app.delete("/api/reservations/{reservation_id}", status_code=204)
def cancel_reservation(
    reservation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reservation = db.get(Reservation, reservation_id)

    if reservation is None:
        raise HTTPException(
            status_code=404,
            detail="その予約はまだありません"
        )

    if reservation.user_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="キャンセル権限がありません"
        )

    if reservation.start_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=409,
            detail="利用開始後の予約はキャンセルできません"
        )

    db.delete(reservation)
    db.commit()


FRONTEND_DIR = (
    Path(__file__).resolve().parent.parent / "frontend"
)

app.mount(
    "/",
    StaticFiles(
        directory=str(FRONTEND_DIR),
        html=True
    ),
    name="frontend"
)