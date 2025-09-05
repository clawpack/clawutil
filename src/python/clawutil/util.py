r"""
clawutil.util Module  `$CLAW/clawutil/src/python/clawutil/util.py`

Provides general utility functions.

:Functions:

 - fullpath_import: import a module using its full path

"""

def fullpath_import(fullpath, verbose=True):
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
    """

    import os, sys, importlib
    fname = os.path.split(fullpath)[1]
    modname = os.path.splitext(fname)[0]
    spec = importlib.util.spec_from_file_location(modname, fullpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[modname] = module
    if verbose:
        print('loaded module from file: ',module.__file__)
    return module


