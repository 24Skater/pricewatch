from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool, QueuePool
from .config import settings
from .logging_config import get_logger

logger = get_logger(__name__)

# Determine if using SQLite
is_sqlite = "sqlite" in settings.database_url

# Configure engine with appropriate pooling
if is_sqlite:
    # SQLite uses StaticPool for development
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        pool_pre_ping=True,
        echo=settings.debug,
    )
else:
    # PostgreSQL/MySQL use QueuePool with configurable settings
    engine = create_engine(
        settings.database_url,
        poolclass=QueuePool,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_pre_ping=True,  # Verify connections before use
        echo=settings.debug,  # Log SQL queries in debug mode
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Database dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
