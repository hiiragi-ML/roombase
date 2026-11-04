import pytest

from app.config import get_allowed_origins

def test_allowed_origins_in_development(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:8000"
    )

    origins = get_allowed_origins()

    assert sorted(origins) == ["http://localhost:5173", "http://localhost:8000"]

def test_reject_http_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv(
        "ALLOWED_ORIGINS",
        "http://example.com"
    )

    with pytest.raises(RuntimeError):
        get_allowed_origins()