from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import os

from database.db import get_db
from database.models import BoardORM

router = APIRouter()

GATEWAY_TOKEN = os.getenv("GATEWAY_TOKEN")


class PriceValue(BaseModel):
    rubs: int
    kopecks: int = 99


class DiscountInfo(BaseModel):
    base_price: Optional[PriceValue]
    discount: Optional[float]


class ProductInfo(BaseModel):
    name: str
    res_price: PriceValue
    discount: Optional[DiscountInfo]


class BoardData(BaseModel):
    board_id: Optional[str]
    product: ProductInfo


class ConfirmBoardRequest(BaseModel):
    board_id: str


@router.get("/unsync_board", response_model=Optional[BoardData])
def get_first_unsynced_board(
        authorization: str = Header(...),
        db: Session = Depends(get_db)):
    board = (
        db.query(BoardORM)
        .filter(BoardORM.synced == False)
        .order_by(BoardORM.id)
        .first()
    )
    if authorization != f"Bearer {GATEWAY_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not board or board.base_price is None or board.product is None:
        return None

    res_price = board.base_price
    discount_block = None
    if board.discount is not None:
        res_price = board.base_price * (1 - board.discount / 100)
        discount_block = DiscountInfo(
            base_price=PriceValue(rubs=int(board.base_price)),
            discount=board.discount
        )
        
    return BoardData(
        board_id=board.id,
        product=ProductInfo(
            name=board.product,
            res_price=PriceValue(rubs=int(res_price)),
            discount=discount_block
        )
    )


@router.post("/confirm_board")
def confirm_board(
    data: ConfirmBoardRequest,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    if authorization != f"Bearer {GATEWAY_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    board = db.query(BoardORM).filter(BoardORM.id == data.board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    board.synced = True
    db.commit()

    return {"ok": True, "board_id": board.id}
