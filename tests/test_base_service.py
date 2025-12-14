"""Test base service class functionality."""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.exc import SQLAlchemyError
from app.services.base import BaseService
from app.models import Tracker
from app.exceptions import DatabaseError


class TestBaseService:
    """Test BaseService functionality."""
    
    def test_init(self, db_session):
        """Test service initialization."""
        service = BaseService(db_session)
        assert service.db == db_session
        assert service.logger is not None
    
    def test_commit_success(self, db_session):
        """Test successful commit."""
        service = BaseService(db_session)
        # Should not raise
        service._commit()
    
    def test_commit_failure(self, db_session):
        """Test commit failure handling."""
        service = BaseService(db_session)
        
        # Mock commit to raise exception
        with patch.object(db_session, 'commit', side_effect=SQLAlchemyError("Commit failed")):
            with pytest.raises(DatabaseError):
                service._commit()
    
    def test_rollback_success(self, db_session):
        """Test successful rollback."""
        service = BaseService(db_session)
        # Should not raise
        service._rollback()
    
    def test_rollback_failure(self, db_session):
        """Test rollback failure handling."""
        service = BaseService(db_session)
        
        # Mock rollback to raise exception
        with patch.object(db_session, 'rollback', side_effect=SQLAlchemyError("Rollback failed")):
            # Should not raise, just log
            service._rollback()
    
    def test_add(self, db_session):
        """Test adding instance to session."""
        service = BaseService(db_session)
        tracker = Tracker(
            url="https://example.com",
            alert_method="email",
            contact="test@example.com"
        )
        service._add(tracker)
        assert tracker in db_session.new
    
    def test_delete(self, db_session):
        """Test deleting instance from session."""
        service = BaseService(db_session)
        tracker = Tracker(
            url="https://example.com",
            alert_method="email",
            contact="test@example.com"
        )
        db_session.add(tracker)
        db_session.commit()
        
        service._delete(tracker)
        assert tracker in db_session.deleted
    
    def test_refresh(self, db_session):
        """Test refreshing instance from database."""
        service = BaseService(db_session)
        tracker = Tracker(
            url="https://example.com",
            alert_method="email",
            contact="test@example.com"
        )
        db_session.add(tracker)
        db_session.commit()
        
        # Modify in memory
        tracker.name = "Modified"
        # Refresh from DB
        service._refresh(tracker)
        # Name should be reset to None (original value)
        assert tracker.name is None
    
    def test_save_success(self, db_session):
        """Test successful save operation."""
        service = BaseService(db_session)
        tracker = Tracker(
            url="https://example.com",
            alert_method="email",
            contact="test@example.com"
        )
        
        result = service._save(tracker)
        assert result.id is not None
        assert result == tracker
    
    def test_save_commit_failure(self, db_session):
        """Test save with commit failure."""
        service = BaseService(db_session)
        tracker = Tracker(
            url="https://example.com",
            alert_method="email",
            contact="test@example.com"
        )
        
        with patch.object(service, '_commit', side_effect=DatabaseError("Commit failed")):
            with pytest.raises(DatabaseError):
                service._save(tracker)
    
    def test_save_other_exception(self, db_session):
        """Test save with other exception."""
        service = BaseService(db_session)
        tracker = Tracker(
            url="https://example.com",
            alert_method="email",
            contact="test@example.com"
        )
        
        with patch.object(service, '_refresh', side_effect=ValueError("Refresh failed")):
            with pytest.raises(DatabaseError):
                service._save(tracker)
