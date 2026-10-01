"""Compatibility shim exposing ``src/kern/workflows`` as top‑level ``workflows``.
Tests import ``workflows.xxx`` directly.
"""
import importlib.util
import sys
from pathlib import Path

_real_pkg_dir = Path(__file__).parent.parent / "src" / "kern" / "workflows"
_real_init = _real_pkg_dir / "__init__.py"

_spec = importlib.util.spec_from_file_location("_workflows_real", _real_init)
_real_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_real_mod)  # type: ignore[arg-type]

# Export public attributes.
for _name in dir(_real_mod):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_real_mod, _name)

__path__ = [_real_pkg_dir.as_posix()]
__file__ = _real_init.as_posix()

sys.modules[__name__] = sys.modules[__name__]
