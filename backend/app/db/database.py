from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.app.config import settings

# Engine configuration - SQLite or PostgreSQL
db_url = settings.DATABASE_URL
engine_kwargs = {}
if db_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(db_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db(max_retries: int = 5, retry_interval: float = 2.0):
    import time
    import logging
    logger = logging.getLogger(__name__)
    from backend.app.db import models  # noqa
    for attempt in range(1, max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"Failed to initialize database after {max_retries} attempts: {e}")
                raise
            logger.warning(f"Database connection attempt {attempt}/{max_retries} failed ({e}). Retrying in {retry_interval}s...")
            time.sleep(retry_interval)
