"""
Conftest for identity domain tests.

Ensures the installed `mcp` package is loaded before pytest adds the local
domain directory to sys.path, preventing the local `mcp/` package from
shadowing the installed MCP SDK that fastmcp depends on.
"""
import sys
import importlib
import importlib.util

# The local mcp/ directory in the identity domain shadows the installed mcp
# package. We need to find the installed one specifically (by excluding the
# local path) and load it into sys.modules before anything else can trigger
# the collision.
if "mcp" not in sys.modules:
    _local_mcp_path = None
    for path_entry in sys.path:
        import os
        candidate = os.path.join(path_entry, "mcp")
        if os.path.isdir(candidate) and "LV_Presentation/domains/identity" in candidate:
            _local_mcp_path = candidate
            break

    # Build a path list that excludes the local mcp directory
    _clean_path = [p for p in sys.path if "LV_Presentation/domains/identity" not in p]

    # Find mcp using the clean path
    _finder = importlib.machinery.PathFinder()
    _mcp_spec = importlib.machinery.PathFinder.find_spec("mcp", _clean_path)
    if _mcp_spec is not None:
        _mcp_module = importlib.util.module_from_spec(_mcp_spec)
        sys.modules["mcp"] = _mcp_module
        _mcp_spec.loader.exec_module(_mcp_module)
