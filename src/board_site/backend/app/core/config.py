import os
from pathlib import Path

PRJ_DIR = Path(__file__).parent.parent
DATA_DIR = PRJ_DIR / "data"

if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)