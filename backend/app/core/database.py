import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pathwise.db")

# Configure connection args for SQLite
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)

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
