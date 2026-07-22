"""Auto-discovers Strategy implementations from src/strategies/.

Convention for any new strategy file dropped into strategies/:
- One class per file, following the pattern of ma_crossover.py / rsi_reversion.py.
- The class needs a `name: str` class attribute and an `on_tick` method (the
  Strategy Protocol from strategy.py).
- The class MUST be constructible with zero arguments — every constructor
  parameter needs a sensible default. This is what lets this registry (and the
  backtest UI) instantiate any strategy generically without knowing its specific
  constructor signature.
- Files/modules starting with an underscore (e.g. _template.py) are skipped —
  use that prefix for templates or shared helpers that aren't themselves strategies.

Drop a new file in strategies/ following this convention and it appears in the
backtest UI and CLI scripts automatically on the next run — no other file needs
to change. Note: this only picks up NEW files automatically each rerun; if you
EDIT an already-imported strategy file, restart the process (or Streamlit) to
pick up the change, since Python caches imported modules.
"""

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import cast

import strategies
from strategy import Strategy


def discover_strategies() -> dict[str, type[Strategy]]:
    """Returns {strategy_name: StrategyClass} for every strategy found in strategies/."""
    found: dict[str, type[Strategy]] = {}
    package_path = Path(strategies.__file__).parent

    for module_info in pkgutil.iter_modules([str(package_path)]):
        if module_info.name.startswith("_"):
            continue

        module = importlib.import_module(f"strategies.{module_info.name}")

        for _, raw_obj in inspect.getmembers(module, inspect.isclass):
            if raw_obj.__module__ != module.__name__:
                continue  # skip imported classes (e.g. the Strategy protocol itself)
            if not (hasattr(raw_obj, "name") and hasattr(raw_obj, "on_tick")):
                continue

            # inspect.getmembers types classes as `type[object]`; hasattr checks above
            # are the real runtime guarantee that this satisfies the Strategy Protocol,
            # but mypy can't narrow on hasattr alone, hence the explicit cast here.
            obj = cast(type[Strategy], raw_obj)

            try:
                instance = obj()
            except TypeError as e:
                raise TypeError(
                    f"Strategy class '{obj.__name__}' in strategies/{module_info.name}.py "
                    f"could not be constructed with zero arguments. Every strategy needs "
                    f"defaults for all constructor parameters to be auto-discovered. "
                    f"Original error: {e}"
                ) from e

            found[instance.name] = obj

    return found