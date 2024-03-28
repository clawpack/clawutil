"""
Run all examples in subdirectories of the directory from which this script
is invoked, by doing `make all` in each.
Also run any Jupyter notebooks to make .html versions.

Two files
    make_all_output.txt
    make_all_errors.txt
will be created that contain the output normally sent to the screen and any
error messages from running the examples.
"""

from clawpack.clawutil import make_all
import os

# run examples with the user's current environment by default:
env = os.environ

# Explicitly set some environment variables, if desired, e.g.:
#env['GIT_STATUS'] = 'True'
#env['FFLAGS'] = '-O2 -fopenmp'
#env['OMP_NUM_THREADS'] = '6'

make_all.make_all(make_clean_first=True, env=env)

run_notebooks = True  # run any *.ipynb files and create html versions?

if run_notebooks:
    make_all.make_notebook_htmls(env=env)


