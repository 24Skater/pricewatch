"""Base service class with common database operations."""

from typing import TypeVar, Generic, Optional, Type
from sqlalchemy.orm import Session
from app.database import Base
from app.logging_config import get_logger
from app.exceptions import DatabaseError

# Generic type variable for model classes
T = TypeVar("T", bound=Base)


class BaseService(Generic[T]):
    """Base service class with common database operations.
    
    Provides standardized database session handling, commit/rollback helpers,
    and logging configuration that all services can inherit.
    
    Attributes:
        db: SQLAlchemy database session
        logger: Logger instance for the service
    """
    
    def __init__(self, db: Session):
        """Initialize the service with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.logger = get_logger(self.__class__.__module__)
    
    def _commit(self) -> None:
        """Commit the current transaction.
        
        Raises:
            DatabaseError: If commit fails
        """
        try:
            self.db.commit()
        except Exception as e:
            self._rollback()
            self.logger.error(f"Database commit failed: {e}")
            raise DatabaseError(f"Database commit failed: {e}")
    
    def _rollback(self) -> None:
        """Rollback the current transaction."""
        try:
            self.db.rollback()
        except Exception as e:
            self.logger.error(f"Database rollback failed: {e}")
    
    def _add(self, instance: T) -> None:
        """Add an instance to the session.
        
        Args:
            instance: Model instance to add
        """
        self.db.add(instance)
    
    def _delete(self, instance: T) -> None:
        """Delete an instance from the session.
        
        Args:
            instance: Model instance to delete
        """
        self.db.delete(instance)
    
    def _refresh(self, instance: T) -> None:
        """Refresh an instance from the database.
        
        Args:
            instance: Model instance to refresh
        """
        self.db.refresh(instance)
    
    def _save(self, instance: T) -> T:
        """Add, commit, and refresh an instance.
        
        This is a convenience method that combines add, commit, and refresh
        into a single operation with proper error handling.
        
        Args:
            instance: Model instance to save
            
        Returns:
            The saved and refreshed instance
            
        Raises:
            DatabaseError: If save operation fails
        """
        try:
            self._add(instance)
            self._commit()
            self._refresh(instance)
            return instance
        except DatabaseError:
            raise
        except Exception as e:
            self._rollback()
            self.logger.error(f"Failed to save instance: {e}")
            raise DatabaseError(f"Failed to save: {e}")

