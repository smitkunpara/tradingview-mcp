from fastmcp import FastMCP
from typing import Annotated
from pydantic import Field
import asyncio

# Initialize FastMCP server
mcp = FastMCP(
    name="My MCP Server",
    instructions="A sample MCP server with basic functionality"
)

# Sample tool with proper parameter documentation
@mcp.tool()
def greet_user(
    name: Annotated[str, Field(
        description="Name of the person to greet",
        min_length=1,
        max_length=100
    )],
    greeting_type: Annotated[str, Field(
        description="Type of greeting (formal/casual)",
        pattern="^(formal|casual)$"
    )] = "casual"
) -> str:
    """Greet a user with a personalized message.
    
    This tool creates customized greetings based on the user's name
    and preferred greeting style.
    """
    if greeting_type == "formal":
        return f"Good day, {name}. It's a pleasure to meet you."
    else:
        return f"Hey {name}! Nice to meet you!"

# Sample resource
@mcp.resource("config://server/info")
def server_info() -> dict:
    """Provide information about this MCP server."""
    return {
        "name": "My MCP Server",
        "version": "1.0.0",
        "description": "A sample FastMCP server implementation",
        "capabilities": ["greeting", "basic_info"]
    }

# Entry point for the server
if __name__ == "__main__":
    mcp.run()
