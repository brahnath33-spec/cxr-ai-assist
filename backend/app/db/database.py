"""SQLite database for storing CXRAI prediction reports."""

from datetime import datetime
from pathlib import Path

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DB_DIR = Path("C:/Users/brahn/cxr-ai-assist/backend/data")
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "cxrai.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    model_version = Column(String)
    predictions = Column(JSON)
    confidence = Column(Float)
    flagged = Column(JSON)
    inference_time_ms = Column(Float)
    image_dimensions = Column(JSON)
    image_data_url = Column(Text, nullable=True)
    heatmap_data_url = Column(Text, nullable=True)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()