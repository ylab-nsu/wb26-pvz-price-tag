import os
from sqlalchemy.orm import Session

from database.db import SessionLocal
from database.models import UserORM
from database.utils import hash_password


def init_admin_user():
    db: Session = SessionLocal()
    try:
        login = os.getenv("ADMIN_USER")
        password = os.getenv("ADMIN_PASSWORD")
        if not login or not password:
            return

        user = db.query(UserORM).filter(UserORM.login == login).first()
        if not user:
            hashed = hash_password(password)
            user = UserORM(login=login, hashed_password=hashed)
            db.add(user)
            db.commit()
            print(f"Admin user '{login}' created.")
    finally:
        db.close()
