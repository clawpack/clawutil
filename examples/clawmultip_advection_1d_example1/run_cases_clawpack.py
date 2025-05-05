from pylab import *
from clawpack.clawutil import runclaw

import os,sys,shutil,pickle

from clawpack.clawutil import multip_tools, clawmultip_tools


def make_cases():

    """
    Create a list of the cases to be run, varying a couple rundata parameters
    after setting common parameters from setrun_cases.py.

    The parameters set for each case (as dictionary keys) are determined by
    the fact that we will use clawmultip_tools.run_one_case_clawpack()
    to run a single case.  See that code for more documentation.
    """

    caselist = []

    for mx in [50,100,200]:
        for order in [1,2]:
            case = {}
            case_name = 'order%s_mx%s' % (order, str(mx).zfill(4))
            case['case_name'] = case_name

            case['outdir'] = '_output_%s' % case_name

            #case['xclawcmd'] = None  # if None, will not run code
            case['xclawcmd'] = 'xclaw'  # executable created by 'make .exe'

            # setrun parameters:
            case['setrun_file'] = 'setrun_cases.py'

            # setrun_cases.py should contain a setrun function with case
            # as a keyword argument so we can pass in the following values:

            case['order'] = order
            case['mx'] = mx

            #case['plotdir'] = None  # if None, will not make plots
            case['plotdir'] = '_plots_%s' % case_name

            case['setplot_file'] = 'setplot_cases.py'

            # setplot_cases.py should contain a setplot function with case
            # as a keyword argument so we can pass in the parameters,
            # so that outdir and case_name can be used in the title of figures

            caselist.append(case)

    return caselist


if __name__ == '__main__':

    # number of Clawpack jobs to run simultaneously:
    nprocs = 4

    caselist = make_cases()

    # run all cases using nprocs processors:
    run_one_case = clawmultip_tools.run_one_case_clawpack
    multip_tools.run_many_cases_pool(caselist, nprocs, run_one_case)
