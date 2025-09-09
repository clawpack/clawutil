r"""
clawutil.util Module  `$CLAW/clawutil/src/python/clawutil/util.py`

Provides general utility functions.

:Functions:

 - fullpath_import: import a module using its full path

"""

import os, sys, importlib
from pathlib import Path


def fullpath_import(fullpath, verbose=False):
    """
    Return a module imported from a full path name, e.g. if you have
    a personal enhanced version of the geoclaw topotools module at
    /full/path/to/topotools.py then instead of:

        from clawpack.geoclaw import topotools

    use:

        from clawpack.clawutil.util import fullpath_import
        topotools = fullpath_import('/full/path/to/topotools.py')

    Relative imports also work, e.g.

        topotools = fullpath_import('../topotools.py')

    To reload the module if you make changes to it, use this function again
    (rather than using importlib.reload).

    Input `fullpath` can also be a `pathlib.Path` object instead of a string.

    If `fullpath` is a string that starts with `$`, then the path is assumed
    to start with an environment variable and this is resolved, if possible,
    from `os.environ`.  For example, this works:

        setrun_file = '$CLAW/amrclaw/examples/advection_2d_swirl/setrun.py'
        setrun = util.fullpath_import(setrun_file)

    It also expands `~` and `~user` constructs and resolves symlinks.
    """

    # expand any environment variables:
    fullpath = os.path.expandvars(fullpath)

    # convert to a Path object if necessary, expand user prefix `~`,
    # and convert to absolute path, resolving any symlinks:
    fullPath = Path(fullpath).expanduser().resolve()

    assert fullPath.suffix == '.py', '*** Expecting path to .py file'

    fname = fullPath.name     # should be modname.py
    modname = fullPath.stem   # without extension

    spec = importlib.util.spec_from_file_location(modname, fullPath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[modname] = module
    if verbose:
        print('loaded module from file: ',module.__file__)
    return module
