"""reproai_core — the engine's import name through 0.7; renamed reproai_prep in 0.8.

Kept for one release so code written against 0.7 still imports: every module of
reproai_prep is also reachable as reproai_core.<name>, as the same module object.
"""

import importlib
import pkgutil
import sys
import warnings

import reproai_prep

warnings.warn("reproai_core is now reproai_prep; the old name is removed after 0.8",
              DeprecationWarning, stacklevel=2)

for _info in pkgutil.iter_modules(reproai_prep.__path__):
    _module = importlib.import_module(f"reproai_prep.{_info.name}")
    sys.modules[f"{__name__}.{_info.name}"] = _module
    globals()[_info.name] = _module

from reproai_prep import GENERATED_BY, __version__  # noqa: E402,F401
