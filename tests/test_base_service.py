"""Test base service class functionality."""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.exc import SQLAlchemyError
from app.services.base import BaseService
from app.models import Tracker
from app.exceptions import DatabaseError


class TestBaseService:
    """Test BaseService common functionality."""
    
    def test_commit_success(self, db_session):
        """Test successful commit."""
        service = BaseService[Tracker](db_session)
        
        # Create a tracker to commit
        tracker = Tracker(
            url="https://example.com/test",
            alert_method="email",
            contact="test@example.com"
        )
        db_session.add(tracker)
        
        # Should not raise
        service._commit()
        assert tracker.id is not None
    
    def test_commit_failure_rolls_back(self, db_session):
        """Test commit failure triggers rollback."""
        service = BaseService[Tracker](db_session)
        
        # Create invalid tracker that will fail on commit
        tracker = Tracker(
            url="https://example.com/test",
            alert_method="email",
            contact="test@example.com"
        )
        db_session.add(tracker)
        
        # Mock commit to raise exception
        with patch.object(db_session, 'commit', side_effect=SQLAlchemyError("Commit failed")):
            with pytest.raises(DatabaseError):
                service._commit()
    
    def test_rollback_success(self, db_session):
        """Test successful rollback."""
        service = BaseService[Tracker](db_session)
        
        tracker = Tracker(
            url="https://example.com/test",
            alert_method="email",
            contact="test@example.com"
        )
        db_session.add(tracker)
        
        # Should not raise
        service._rollback()
    
    def test_rollback_failure_logs(self, db_session):
        """Test rollback failure is logged but doesn't raise."""
        service = BaseService[Tracker](db_session)
        
        # Mock rollback to raise exception
        with patch.object(db_session, 'rollback', side_effect=SQLAlchemyError("Rollback failed")):
            # Should not raise, just log
            service._rollback()
    
    def test_add(self, db_session):
        """Test adding instance to session."""
        service = BaseService[Tracker](db_session)
        
        tracker = Tracker(
            url="https://example.com/test",
            alert_method="email",
            contact="test@example.com"
        )
        
        service._add(tracker)
        assert tracker in db_session.new
    
    def test_delete(self, db_session):
        """Test deleting instance from session."""
        service = BaseService[Tracker](db_session)
        
        tracker = Tracker(
            url="https://example.com/test",
            alert_method="email",
            contact="test@example.com"
        )
        db_session.add(tracker)
        db_session.commit()
        
        service._delete(tracker)
        assert tracker in db_session.deleted
    
    def test_refresh(self, db_session):
        """Test refreshing instance from database."""
        service = BaseService[Tracker](db_session)
        
        tracker = Tracker(
            url="https://example.com/test",
            alert_method="email",
            contact="test@example.com"
        )
        db_session.add(tracker)
        db_session.commit()
        
        # Modify in another session to test refresh
        tracker.name = "Updated Name"
        
        service._refresh(tracker)
        # After refresh, should have latest from DB
    
    def test_save_success(self, db_session):
        """Test successful save operation."""
        service = BaseService[Tracker](db_session)
        
        tracker = Tracker(
            url="https://example.com/test",
            alert_method="email",
            contact="test@example.com"
        )
        
        result = service._save(tracker)
        assert result.id is not None
        assert result == tracker
    
    def test_save_commit_failure(self, db_session):
        """Test save operation when commit fails."""
        service = BaseService[Tracker](db_session)
        
        tracker = Tracker(
            url="https://example.com/test",
            alert_method="email",
            contact="test@example.com"
        )
        
        # Mock commit to raise DatabaseError
        with patch.object(service, '_commit', side_effect=DatabaseError("Commit failed")):
            with pytest.raises(DatabaseError):
                service._save(tracker)
    
    def test_save_other_exception(self, db_session):
        """Test save operation when other exception occurs."""
        service = BaseService[Tracker](db_session)
        
        tracker = Tracker(
            url="https://example.com/test",
            alert_method="email",
            contact="test@example.com"
        )
        
        # Mock refresh to raise exception
        with patch.object(db_session, 'refresh', side_effect=Exception("Refresh failed")):
            with pytest.raises(DatabaseError):
                service._save(tracker)

