"""Core MCP Server implementation."""

import logging
from typing import Any, Dict, List, Optional, Callable, Awaitable
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
import structlog

from .utils.config import get_settings, Settings
from .utils.errors import APIError, MCPError, ErrorCode


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class ToolSchema(BaseModel):
    """Schema for tool definition."""
    
    name: str
    description: str
    input_schema: Dict[str, Any]


class ToolRequest(BaseModel):
    """Request model for tool invocation."""
    
    tool_name: str
    parameters: Dict[str, Any]


class ToolResponse(BaseModel):
    """Response model for tool execution."""
    
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[MCPError] = None


class MCPServerRequest(BaseModel):
    """MCP protocol request wrapper."""
    
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[str] = None


class MCPServerResponse(BaseModel):
    """MCP protocol response wrapper."""
    
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[MCPError] = None
    id: Optional[str] = None


ToolHandler = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]


class MCPServer:
    """Model Context Protocol Server for API Aggregation."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.app = FastAPI(
            title="API Aggregator MCP Server",
            description="MCP Server providing unified access to multiple APIs",
            version="1.0.0",
            debug=settings.debug,
        )
        
        # Tool registry
        self._tools: Dict[str, ToolSchema] = {}
        self._handlers: Dict[str, ToolHandler] = {}
        
        # Setup middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self) -> None:
        """Setup FastAPI routes."""
        
        @self.app.get("/")
        async def root():
            """Health check endpoint."""
            return {"status": "healthy", "server": "API Aggregator MCP"}
        
        @self.app.get("/tools")
        async def list_tools() -> List[ToolSchema]:
            """List all available tools."""
            return list(self._tools.values())
        
        @self.app.post("/tools/{tool_name}")
        async def invoke_tool(
            tool_name: str,
            request: Dict[str, Any],
            settings: Settings = Depends(get_settings),
        ) -> ToolResponse:
            """Invoke a specific tool."""
            try:
                if tool_name not in self._tools:
                    raise APIError(
                        message=f"Tool '{tool_name}' not found",
                        code=ErrorCode.METHOD_NOT_FOUND,
                    )
                
                # Execute tool handler
                handler = self._handlers[tool_name]
                result = await handler(request)
                
                return ToolResponse(success=True, data=result)
                
            except APIError as e:
                logger.error("Tool execution failed", tool=tool_name, error=str(e))
                return ToolResponse(success=False, error=e.to_mcp_error())
            except Exception as e:
                logger.error("Unexpected error", tool=tool_name, error=str(e))
                error = APIError(
                    message="Internal server error",
                    code=ErrorCode.INTERNAL_ERROR,
                    original_error=e,
                )
                return ToolResponse(success=False, error=error.to_mcp_error())
        
        @self.app.post("/mcp")
        async def mcp_endpoint(
            request: MCPServerRequest,
            settings: Settings = Depends(get_settings),
        ) -> MCPServerResponse:
            """Main MCP protocol endpoint."""
            try:
                if request.method == "tools/list":
                    return MCPServerResponse(
                        result={"tools": list(self._tools.values())},
                        id=request.id,
                    )
                elif request.method == "tools/call":
                    params = request.params or {}
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    if not tool_name:
                        raise APIError(
                            message="Tool name is required",
                            code=ErrorCode.INVALID_PARAMS,
                        )
                    
                    if tool_name not in self._tools:
                        raise APIError(
                            message=f"Tool '{tool_name}' not found",
                            code=ErrorCode.METHOD_NOT_FOUND,
                        )
                    
                    handler = self._handlers[tool_name]
                    result = await handler(arguments)
                    
                    return MCPServerResponse(
                        result={"content": [{"type": "text", "text": str(result)}]},
                        id=request.id,
                    )
                else:
                    raise APIError(
                        message=f"Unknown method: {request.method}",
                        code=ErrorCode.METHOD_NOT_FOUND,
                    )
                    
            except APIError as e:
                logger.error("MCP request failed", method=request.method, error=str(e))
                return MCPServerResponse(
                    error=e.to_mcp_error(),
                    id=request.id,
                )
            except Exception as e:
                logger.error("Unexpected MCP error", method=request.method, error=str(e))
                error = APIError(
                    message="Internal server error",
                    code=ErrorCode.INTERNAL_ERROR,
                    original_error=e,
                )
                return MCPServerResponse(
                    error=error.to_mcp_error(),
                    id=request.id,
                )
    
    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: ToolHandler,
    ) -> None:
        """Register a tool with the server."""
        tool_schema = ToolSchema(
            name=name,
            description=description,
            input_schema=input_schema,
        )
        
        self._tools[name] = tool_schema
        self._handlers[name] = handler
        
        logger.info("Tool registered", tool=name, description=description)
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        return self.app 