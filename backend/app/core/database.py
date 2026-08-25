import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def normalize_database_url(url: str) -> str:
    """
    Normalizes database URL string.
    Render passes PostgreSQL URLs starting with 'postgres://', which SQLAlchemy 1.4+
    requires to be 'postgresql://' or 'postgresql+psycopg2://'.
    """
    if not url:
        return "sqlite:///./pathwise.db"
    url = url.strip()
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def get_engine_kwargs(url: str) -> dict:
    """Returns dialect-specific engine configuration options."""
    kwargs = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    elif url.startswith("postgresql"):
        kwargs["pool_pre_ping"] = True
        # Optional pooling tuning from environment variables if present
        pool_size = os.getenv("DB_POOL_SIZE")
        if pool_size:
            try:
                kwargs["pool_size"] = int(pool_size)
            except ValueError:
                pass
        max_overflow = os.getenv("DB_MAX_OVERFLOW")
        if max_overflow:
            try:
                kwargs["max_overflow"] = int(max_overflow)
            except ValueError:
                pass
    else:
        kwargs["pool_pre_ping"] = True
    return kwargs


DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", "sqlite:///./pathwise.db"))

engine = create_engine(DATABASE_URL, **get_engine_kwargs(DATABASE_URL))

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_sqlite_columns_safely(engine_instance):
    """Safely adds newly added columns to existing SQLite tables if they do not already exist."""
    try:
        with engine_instance.connect() as conn:
            # Notifications table migration
            result = conn.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='notifications'")
            if result.fetchone():
                info = conn.exec_driver_sql("PRAGMA table_info(notifications)").fetchall()
                existing_cols = {row[1].lower() for row in info}
                needed_notif_cols = [
                    ("risk_snapshot_id", "INTEGER"),
                    ("notification_type", "VARCHAR(50)"),
                    ("severity", "VARCHAR(20)"),
                    ("title", "VARCHAR(255)"),
                    ("message", "TEXT"),
                    ("is_read", "BOOLEAN DEFAULT 0"),
                    ("created_at", "DATETIME"),
                    ("read_at", "DATETIME"),
                ]
                for col_name, col_type in needed_notif_cols:
                    if col_name.lower() not in existing_cols:
                        conn.exec_driver_sql(f"ALTER TABLE notifications ADD COLUMN {col_name} {col_type}")

            # Interventions table migration
            result = conn.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='interventions'")
            if result.fetchone():
                info = conn.exec_driver_sql("PRAGMA table_info(interventions)").fetchall()
                existing_cols = {row[1].lower() for row in info}
                needed_interv_cols = [
                    ("intervention_type", "VARCHAR(50) DEFAULT 'COUNSELLING'"),
                    ("title", "VARCHAR(255) DEFAULT 'Support Action'"),
                    ("follow_up_date", "DATE"),
                    ("completed_at", "DATETIME"),
                    ("updated_at", "DATETIME"),
                ]
                for col_name, col_type in needed_interv_cols:
                    if col_name.lower() not in existing_cols:
                        conn.exec_driver_sql(f"ALTER TABLE interventions ADD COLUMN {col_name} {col_type}")
    except Exception:
        pass  # Non-SQLite or in-memory DB will have fresh tables created via create_all


def init_db(engine_instance=None):
    """Initializes all database tables registered with Base and migrates SQLite columns safely."""
    target_engine = engine_instance or engine
    Base.metadata.create_all(bind=target_engine)
    if str(target_engine.url).startswith("sqlite"):
        _migrate_sqlite_columns_safely(target_engine)
