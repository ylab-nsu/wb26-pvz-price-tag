from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from database.db import get_db
from database.models import BoardORM, UserORM
from database.utils import hash_password, verify_password

router = APIRouter()


class LoginRequest(BaseModel):
    login: str
    password: str


class Board(BaseModel):
    id: str
    product: str
    base_price: float
    discount: float
    installed_at: str
    synced: Optional[bool] = True

    class Config:
        orm_mode = True


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserORM).filter(UserORM.login == data.login).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"ok": True, "username": user.login}


@router.get("/boards", response_model=List[Board])
def get_boards(db: Session = Depends(get_db)):
    boards = db.query(BoardORM).all()
    return boards


@router.post("/update_board", response_model=Board)
def update_board(board: Board, db: Session = Depends(get_db)):
    errors = {}
    if not board.product.strip():
        errors["product"] = "Product name cannot be empty"
    if board.base_price <= 0:
        errors["base_price"] = "Base price must be greater than 0"
    if board.discount < 0 or board.discount >= 100:
        errors["discount"] = "Discount must be between 0 and 100"

    if errors:
        raise HTTPException(status_code=400, detail=errors)

    if board.id:
        db_board = db.query(BoardORM).filter(BoardORM.id == board.id).first()
        if not db_board:
            raise HTTPException(status_code=404, detail="Board not found")
        db_board.product = board.product
        db_board.base_price = board.base_price
        db_board.discount = board.discount
        db_board.installed_at = board.installed_at
        db_board.synced = False
    else:
        raise HTTPException(status_code=404, detail="No board id")


    db.commit()
    db.refresh(db_board)
    return db_board
