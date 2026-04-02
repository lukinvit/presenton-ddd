"""
Conftest for agent domain tests.

Ensures the installed `mcp` package is loaded before pytest adds the local
domain directory to sys.path, preventing the local `mcp/` package from
shadowing the installed MCP SDK that fastmcp depends on.
"""

import importlib
import importlib.machinery
import importlib.util
import os
import sys

if "mcp" not in sys.modules:
    _local_mcp_path = None
    for path_entry in sys.path:
        candidate = os.path.join(path_entry, "mcp")
        if os.path.isdir(candidate) and "LV_Presentation/domains/agent" in candidate:
            _local_mcp_path = candidate
            break

    _clean_path = [p for p in sys.path if "LV_Presentation/domains/agent" not in p]

    _mcp_spec = importlib.machinery.PathFinder.find_spec("mcp", _clean_path)
    if _mcp_spec is not None:
        _mcp_module = importlib.util.module_from_spec(_mcp_spec)
        sys.modules["mcp"] = _mcp_module
        _mcp_spec.loader.exec_module(_mcp_module)
