r"""
Utility helpers for ``clawutil``.

Functions
---------
fullpath_import
    Import a Python module from an explicit filesystem path.
"""

from __future__ import annotations

import importlib.util
import random
import string
import sys
import os
from pathlib import Path
from typing import Optional


__all__ = ["fullpath_import"]


def _unique_module_name(path: Path) -> str:
    """Return a collision-resistant temporary module name for ``path``."""
    suffix = "".join(random.choices(string.ascii_letters + string.digits, k=32))
    return f"{path.stem}_{suffix}"


def fullpath_import(fullpath,
                    module_name: Optional[str] = None,
                    unique_name: bool = True,
                    verbose: bool = False):
    """
    Import and return a module from a filesystem path.

    This is useful for example-local helper files such as ``setrun.py`` or
    ``maketopo.py`` that should be imported without relying on the package
    import path.

    Examples
    --------
    Instead of::

        from clawpack.geoclaw import topotools

    you can import a local file directly::

        from clawpack.clawutil.util import fullpath_import
        topotools = fullpath_import('/full/path/to/topotools.py')

    Relative paths also work::

        setrun = fullpath_import('../setrun.py')

    Environment variables and ``~`` are expanded, so this also works::

        setrun = fullpath_import('$CLAW/amrclaw/examples/advection_2d_swirl/setrun.py')

    Parameters
    ----------
    fullpath : str or pathlib.Path
        Path to a Python source file.
    module_name : str, optional
        Explicit module name to register in ``sys.modules``.  If provided, this
        takes precedence over ``unique_name``.
    unique_name : bool, default True
        If True and ``module_name`` is not supplied, generate a collision-
        resistant temporary module name instead of using the file stem.  This is
        the safer default for test suites that may import many different files
        named ``setrun.py`` or ``maketopo.py`` in the same Python session.
    verbose : bool, default False
        If True, print the loaded module path and module name.

    Returns
    -------
    module
        Imported Python module object.

    Notes
    -----
    Calling this function again re-imports the module from disk.  This is often
    more convenient for local helper files than using ``importlib.reload``.

    Returns the imported module after registering it in ``sys.modules``.

    Raises
    ------
    FileNotFoundError
        If ``fullpath`` does not exist.
    ValueError
        If ``fullpath`` does not point to a ``.py`` file.
    ImportError
        If an import specification cannot be created for the file.
    """
    # Expand environment variables after string conversion so both strings and
    # Path-like inputs are handled consistently, then expand ``~`` and resolve
    # symlinks.
    full_path = Path(os.path.expandvars(str(fullpath))).expanduser().resolve()

    if not full_path.exists():
        raise FileNotFoundError(f"Module file not found: {full_path}")
    if full_path.suffix != ".py":
        raise ValueError(f"Expected path to a .py file, got: {full_path}")

    if module_name is None:
        module_name = _unique_module_name(full_path) if unique_name else full_path.stem

    spec = importlib.util.spec_from_file_location(module_name, full_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to create import spec for {full_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module

    if verbose:
        print(f"loaded module '{module_name}' from file: {module.__file__}")

    return module
