"""
Geothermal Leases MCP Tools

This module provides tools for interacting with the Geothermal Leases API,
allowing searches, summaries, and analysis of geothermal leases information.
"""

from . import (
    get_lease_details,
)


def register_tools(mcp):
    """Register all tools with the MCP server."""
    get_lease_details.register(mcp)
    