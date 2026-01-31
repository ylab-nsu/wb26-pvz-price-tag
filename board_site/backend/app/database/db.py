from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import DATA_DIR

DB_PATH = DATA_DIR / "database.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from .models import BoardORM, UserORM, Base
    Base.metadata.create_all(bind=engine)
