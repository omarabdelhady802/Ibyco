"""
Standalone SQLAlchemy session for the agent (FastAPI).
The Flask dashboard uses db.session from models.models instead.
"""
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

DB_PATH = Path(__file__).parent.parent / "instance" / "Ibyco.db"

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)

Session = scoped_session(sessionmaker(bind=engine))
