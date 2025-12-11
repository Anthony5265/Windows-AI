"""
SQLAlchemy ORM models for cloud sync database - for Alembic migrations only.
The actual application uses raw SQL in database.py for performance.
These models exist solely for Alembic autogenerate support.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Device(Base):
    """Device information table"""
    __tablename__ = "devices"

    device_id = Column(String, primary_key=True)
    device_name = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    os_version = Column(String, nullable=False)
    app_version = Column(String, nullable=False)
    last_seen = Column(String, nullable=False)
    is_active = Column(Integer, nullable=False, default=1)
    sync_priority = Column(Integer, nullable=False, default=100)
    created_at = Column(String, nullable=False, default=datetime.utcnow().isoformat())


class SyncState(Base):
    """Sync state tracking table"""
    __tablename__ = "sync_state"

    category = Column(String, primary_key=True)
    last_sync = Column(String, nullable=True)
    last_pull = Column(String, nullable=True)
    last_push = Column(String, nullable=True)
    pending_changes = Column(Integer, nullable=False, default=0)
    conflicts = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="idle")
    error_message = Column(String, nullable=True)
    sync_version = Column(Integer, nullable=False, default=1)
    updated_at = Column(String, nullable=False, default=datetime.utcnow().isoformat())


class SyncQueue(Base):
    """Queue for offline changes"""
    __tablename__ = "sync_queue"

    change_id = Column(String, primary_key=True)
    category = Column(String, nullable=False)
    operation = Column(String, nullable=False)
    item_id = Column(String, nullable=False)
    data = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    timestamp = Column(String, nullable=False)
    synced = Column(Integer, nullable=False, default=0)
    retry_count = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    created_at = Column(String, nullable=False, default=datetime.utcnow().isoformat())


class Conflict(Base):
    """Sync conflicts table"""
    __tablename__ = "conflicts"

    conflict_id = Column(String, primary_key=True)
    category = Column(String, nullable=False)
    item_id = Column(String, nullable=False)
    local_version = Column(Integer, nullable=False)
    remote_version = Column(Integer, nullable=False)
    local_data = Column(Text, nullable=True)
    remote_data = Column(Text, nullable=True)
    local_timestamp = Column(String, nullable=True)
    remote_timestamp = Column(String, nullable=True)
    resolution = Column(String, nullable=True)
    resolved = Column(Integer, nullable=False, default=0)
    created_at = Column(String, nullable=False)


class Conversation(Base):
    """Conversations table"""
    __tablename__ = "conversations"

    conversation_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    messages = Column(Text, nullable=False)
    model = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    # Note: 'metadata' is a reserved name in SQLAlchemy, so we use Column() with name override
    metadata_ = Column("metadata", Text, nullable=True)
    synced = Column(Integer, nullable=False, default=0)
    deleted = Column(Integer, nullable=False, default=0)


class Settings(Base):
    """Settings table"""
    __tablename__ = "settings"

    category = Column(String, primary_key=True)
    settings = Column(Text, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(String, nullable=False)
    synced = Column(Integer, nullable=False, default=0)


class Automation(Base):
    """Automations table"""
    __tablename__ = "automations"

    automation_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    config = Column(Text, nullable=False)
    enabled = Column(Integer, nullable=False, default=1)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    synced = Column(Integer, nullable=False, default=0)
    deleted = Column(Integer, nullable=False, default=0)
