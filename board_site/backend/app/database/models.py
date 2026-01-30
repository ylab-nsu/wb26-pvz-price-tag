from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class BoardORM(Base):
    __tablename__ = "boards"

    id = Column(String, primary_key=True, index=True)
    product = Column(String)
    base_price = Column(Float)
    discount = Column(Float)
    installed_at = Column(String, nullable=False)
    synced = Column(Boolean, default=True)


class UserORM(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
