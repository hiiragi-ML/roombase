from app.config import cookie_secure

def test_cookie_secure_in_development(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")

    assert cookie_secure() == False

def test_cookie_secure_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")

    assert cookie_secure() == True