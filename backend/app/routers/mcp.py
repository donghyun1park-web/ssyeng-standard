from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.mcp_gateway import McpGateway


router = APIRouter(tags=["mcp"])
gateway = McpGateway()


class McpToolCallRequest(BaseModel):
    tool_name: str = Field(..., min_length=3, max_length=120)
    arguments: dict[str, Any] = Field(default_factory=dict)


@router.get("/mcp/status")
def mcp_status():
    return gateway.status()


@router.get("/mcp/tools")
def mcp_tools():
    return {"ok": True, "tools": gateway.list_tools()}


@router.post("/mcp/call")
def mcp_call(payload: McpToolCallRequest):
    return gateway.call_tool(payload.tool_name, payload.arguments)
