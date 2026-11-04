from getpass import getpass

from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import engine
from .models import User
from .security import hash_password

def create_admin():
    name = input("User name: ").strip()
    email = input("Email: ").strip().lower()
    password_verified = False
    while password_verified == False:
        password = getpass("Password: ")
        if len(password) < 8:
            print("パスワードは8文字以上にしてください。")
            continue
        confirm = getpass("Confirm password: ")
        if password != confirm:
            print("パスワードが一致しません。")
            continue
        else:
            password_verified = True

    with Session(engine) as session:
        existing_user = session.scalar(
            select(User).where(User.email == email)
        )
        if existing_user is None:
            admin = User(
                email=email,
                name=name,
                password_hash=hash_password(password),
                role="admin",
            )

            session.add(admin)
            session.commit()
        else:
            print("ユーザーがすでに存在しています。")

if __name__ == '__main__':
    create_admin()