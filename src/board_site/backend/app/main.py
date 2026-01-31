from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from core import init_users
from database import db

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
load_dotenv()

db.init_db()
init_users.init_admin_user()


def init_routers():
    from routers.api import router as api_router
    from routers.board_host import router as brd_router

    app.include_router(api_router, prefix="/api")
    app.include_router(brd_router, prefix="/board_host")

    app.mount("/", StaticFiles(directory="front", html=True), name="frontend")
    
init_routers()
