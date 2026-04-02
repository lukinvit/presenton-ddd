"""
Root conftest for web_access domain tests.

Fixes two import shadows that arise because pytest adds the domain directory
and the project root to sys.path (via the pythonpath config):

1. The local `mcp/` directory shadows the installed mcp SDK used by fastmcp.
2. The `shared/` directory at the project root creates a Python namespace package
   that shadows the proper `presenton-shared` editable install.

Both are resolved by pre-loading the correct modules before any test files import.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys


def _fix_mcp_shadow() -> None:
    """Load the installed mcp package, bypassing local mcp/ shadow."""
    if "mcp" in sys.modules:
        # Already loaded — check it's the real one
        pkg = sys.modules["mcp"]
        if getattr(pkg, "__file__", None) is None or "web_access" in str(
            getattr(pkg, "__file__", "")
        ):
            del sys.modules["mcp"]
        else:
            return

    _clean_path = [p for p in sys.path if p != "" and "LV_Presentation/domains/web_access" not in p]
    _mcp_spec = importlib.machinery.PathFinder.find_spec("mcp", _clean_path)
    if _mcp_spec is not None:
        _mcp_module = importlib.util.module_from_spec(_mcp_spec)
        sys.modules["mcp"] = _mcp_module
        _mcp_spec.loader.exec_module(_mcp_module)


def _fix_shared_shadow() -> None:
    """
    Load the proper `shared` package from the editable install, bypassing
    any namespace-package created from the `shared/` directory at project root.
    """
    pkg = sys.modules.get("shared")
    # If already loaded properly (has an __init__.py), nothing to do
    if pkg is not None and getattr(pkg, "__file__", None) is not None:
        return

    # If broken (namespace package with __file__=None), evict it
    if pkg is not None:
        # Remove shared and all sub-modules so they can be re-imported cleanly
        to_remove = [k for k in sys.modules if k == "shared" or k.startswith("shared.")]
        for key in to_remove:
            del sys.modules[key]

    # Find the real shared package: it lives in <project_root>/shared/shared/
    # The .pth file added that path to sys.path so it should be discoverable
    # when we exclude the project-root path that causes the namespace collision.
    import os

    # project root is two levels up from the domain dir (domains/web_access -> .)
    _domain_dir = os.path.dirname(os.path.abspath(__file__))
    _project_root = os.path.normpath(os.path.join(_domain_dir, "..", ".."))
    _shared_src = os.path.join(_project_root, "shared")  # .../LV_Presentation/shared

    # Build a clean search path: use real filesystem paths (no empty string, no
    # project-root dir that contains the colliding `shared/` directory), but DO
    # include the shared-package source directory.
    _clean_path = [
        p
        for p in sys.path
        if p != "" and os.path.normpath(p) != _project_root  # excludes the ../.. entry
    ]
    if _shared_src not in _clean_path:
        _clean_path.append(_shared_src)

    _shared_spec = importlib.machinery.PathFinder.find_spec("shared", _clean_path)
    if _shared_spec is not None and _shared_spec.origin is not None:
        _shared_module = importlib.util.module_from_spec(_shared_spec)
        sys.modules["shared"] = _shared_module
        _shared_spec.loader.exec_module(_shared_module)


_fix_mcp_shadow()
_fix_shared_shadow()
