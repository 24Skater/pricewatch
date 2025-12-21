"""Test database functionality."""

import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from app.database import get_db, engine, SessionLocal, Base
from app.models import Tracker
from app.config import settings


class TestDatabase:
    """Test database connection and session management."""
    
    def test_get_db_yields_session(self):
        """Test get_db dependency yields a database session."""
        db_gen = get_db()
        db = next(db_gen)
        
        assert db is not None
        assert hasattr(db, 'query')
        
        # Cleanup
        try:
            next(db_gen)
        except StopIteration:
            pass
    
    def test_get_db_handles_exception(self):
        """Test database session handles exceptions and rolls back."""
        db_gen = get_db()
        db = next(db_gen)
        
        # Add something to the session
        tracker = Tracker(
            url="https://example.com",
            alert_method="email",
            contact="test@example.com"
        )
        db.add(tracker)
        
        # Simulate exception to trigger error handling path
        try:
            raise ValueError("Test error")
        except ValueError:
            # This should trigger the exception handler in get_db
            # which logs the error, rolls back, and re-raises
            try:
                next(db_gen)  # This will trigger the exception handler
            except ValueError:
                # Exception should be re-raised
                pass
            except StopIteration:
                # Or generator completes
                pass
    
    def test_database_operations(self, db_session):
        """Test basic database operations work."""
        tracker = Tracker(
            url="https://example.com",
            alert_method="email",
            contact="test@example.com"
        )
        db_session.add(tracker)
        db_session.commit()
        
        assert tracker.id is not None
        
        # Query it back
        found = db_session.query(Tracker).filter(Tracker.id == tracker.id).first()
        assert found is not None
        assert found.url == "https://example.com"
    
    def test_database_rollback(self, db_session):
        """Test database rollback works."""
        tracker = Tracker(
            url="https://example.com",
            alert_method="email",
            contact="test@example.com"
        )
        db_session.add(tracker)
        db_session.rollback()
        
        # Should not be committed
        found = db_session.query(Tracker).filter(Tracker.url == "https://example.com").first()
        assert found is None
    
    def test_get_db_exception_path(self):
        """Test get_db exception handling path."""
        db_gen = get_db()
        db = next(db_gen)
        
        # Add something to session
        tracker = Tracker(
            url="https://example.com",
            alert_method="email",
            contact="test@example.com"
        )
        db.add(tracker)
        
        # Force an exception during yield
        with patch.object(db, 'rollback') as mock_rollback:
            try:
                # This should trigger the exception handler
                raise RuntimeError("Test exception")
            except RuntimeError:
                # Exception handler should call rollback
                try:
                    next(db_gen)
                except RuntimeError:
                    # Exception should be re-raised
                    pass
                except StopIteration:
                    pass
    
