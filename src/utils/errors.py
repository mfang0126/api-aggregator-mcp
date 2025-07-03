"""Error handling utilities for the API Aggregator MCP Server."""

import logging
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Standard JSON-RPC error codes."""
    
    # JSON-RPC standard errors
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # Custom application errors
    API_KEY_MISSING = -32001
    API_KEY_INVALID = -32002
    EXTERNAL_API_ERROR = -32003
    RATE_LIMIT_EXCEEDED = -32004
    TOOL_NOT_AVAILABLE = -32005


class MCPError(BaseModel):
    """Structured error response for MCP protocol."""
    
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None


class APIError(Exception):
    """Custom exception for API-related errors."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        data: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.data = data
        self.original_error = original_error
    
    def to_mcp_error(self) -> MCPError:
        """Convert to MCP error format."""
        error_data = self.data or {}
        if self.original_error:
            error_data["original_error"] = str(self.original_error)
        
        return MCPError(
            code=self.code.value,
            message=self.message,
            data=error_data if error_data else None,
        )


def handle_external_api_error(
    error: Exception,
    api_name: str,
    operation: str,
) -> APIError:
    """Normalize external API errors into our error format."""
    logger.error(f"External API error in {api_name}.{operation}: {error}")
    
    # Common HTTP error handling
    if hasattr(error, 'response'):
        response = error.response
        if hasattr(response, 'status_code'):
            if response.status_code == 401:
                return APIError(
                    message=f"Invalid API key for {api_name}",
                    code=ErrorCode.API_KEY_INVALID,
                    data={"api": api_name, "operation": operation},
                    original_error=error,
                )
            elif response.status_code == 429:
                return APIError(
                    message=f"Rate limit exceeded for {api_name}",
                    code=ErrorCode.RATE_LIMIT_EXCEEDED,
                    data={"api": api_name, "operation": operation},
                    original_error=error,
                )
    
    # Generic external API error
    return APIError(
        message=f"External API error: {api_name} {operation} failed",
        code=ErrorCode.EXTERNAL_API_ERROR,
        data={"api": api_name, "operation": operation},
        original_error=error,
    )


def create_validation_error(field: str, value: Any, message: str) -> APIError:
    """Create a validation error for invalid parameters."""
    return APIError(
        message=f"Invalid parameter '{field}': {message}",
        code=ErrorCode.INVALID_PARAMS,
        data={"field": field, "value": value},
    )


def create_missing_api_key_error(api_name: str) -> APIError:
    """Create an error for missing API key."""
    return APIError(
        message=f"API key missing for {api_name}",
        code=ErrorCode.API_KEY_MISSING,
        data={"api": api_name},
    ) 