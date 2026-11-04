import os
from dotenv import load_dotenv

load_dotenv()

def cookie_secure() -> bool:
    env = os.getenv("APP_ENV", "development").lower()

    if env not in ("development", "production"):
        raise RuntimeError("APP_ENVの設定が不正です")

    return env == "production"

def get_allowed_origins() -> list[str]:
    env = os.getenv("APP_ENV", "development").lower()

    if env not in ("development", "production"):
        raise RuntimeError("APP_ENVの設定が不正です")

    raw = os.getenv("ALLOWED_ORIGINS", "").strip()

    if not raw:
        if env == "production":
            raise RuntimeError(
                "本番環境ではALLOWED_ORIGINSが必要です"
            )
        return [
            "http://localhost:5173",
            "http://localhost:8000"
        ]

    origins = [
        origin.strip()
        for origin in raw.split(",")
        if origin.strip()
    ]

    if any(
        origin == "*"
        or not origin.startswith(("http://", "https://"))
        or origin.endswith("/")
        for origin in origins
    ):
        raise RuntimeError("ALLOWED_ORIGINSの形式が不正です")

    if env == "production" and any(
        not origin.startswith("https://")
        for origin in origins
    ):
        raise RuntimeError(
            "本番環境ではHTTPSのOriginのみ許可します"
        )
    return origins