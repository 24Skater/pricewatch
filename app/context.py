"""Shared context variables for the application.

This module provides context variables that can be accessed throughout
the request lifecycle, across different modules without circular imports.
"""

import contextvars

# Request ID context variable - set by middleware, accessible in logging
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", 
    default=""
)


def get_request_id() -> str:
    """Get the current request ID from context.
    
    Returns:
        str: The current request ID, or empty string if not in a request context
    """
    return request_id_ctx.get()


def set_request_id(request_id: str) -> None:
    """Set the current request ID in context.
    
    Args:
        request_id: The request ID to set
    """
    request_id_ctx.set(request_id)

