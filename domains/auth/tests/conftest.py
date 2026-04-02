"""
Conftest for auth domain tests.

Ensures the installed `mcp` package is loaded before pytest adds the local
domain directory to sys.path, preventing the local `mcp/` package from
shadowing the installed MCP SDK that fastmcp depends on.
"""

import importlib
import importlib.util
import sys

# The local mcp/ directory in the auth domain shadows the installed mcp
# package. We need to find the installed one specifically (by excluding the
# local path) and load it into sys.modules before anything else can trigger
# the collision.
if "mcp" not in sys.modules:
    # Build a path list that excludes the local mcp directory
    _clean_path = [p for p in sys.path if "LV_Presentation/domains/auth" not in p]

    # Find mcp using the clean path
    _mcp_spec = importlib.machinery.PathFinder.find_spec("mcp", _clean_path)
    if _mcp_spec is not None:
        _mcp_module = importlib.util.module_from_spec(_mcp_spec)
        sys.modules["mcp"] = _mcp_module
        _mcp_spec.loader.exec_module(_mcp_module)
