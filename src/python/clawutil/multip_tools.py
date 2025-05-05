"""
Code to run several similar cases over mulitple processors using the
Python multiprocess module.  This code is not specific to Clawpack, but
is used in clawmultip_tools.py, which provides tools to simplify doing
parameter sweeps in Clawpack.

The main function provided is
    run_many_cases_pool(caselist, nprocs, run_one_case)
which takes a list of cases to run, the number of processors to use, and
a function that runs a single case as input.

*caselist* is a list of dictionaries.
Each dictionary should define whatever parameters are needed for one case.

Example:

This module contains templates run_one_case_sample and make_all_cases_sample.
If you execute:
    python multip_tools.py 3
at the command line, for example, these will be used to do a quick example
with nprocs=3, where:

    run_one_case_sample simply prints out a case number and then
        sleeps for 2 seconds.

    make_all_cases_sample makes 7 such cases.

NOTE:

Because uses multiprocessing.Pool, you can only call run_many_cases_pool
from a main program, i.e. following
    if __name__ == '__main__':
in your Python code, not elsewhere in a module and not from an interactive
shell.  See:
 https://docs.python.org/3/library/multiprocessing.html#using-a-pool-of-workers

"""

from numpy import *
import os, time, shutil, sys
from multiprocessing import Process, current_process


setplot_file = os.path.abspath('setplot.py')


def run_many_cases_pool(caselist, nprocs, run_one_case, abort_time=5):
    """
    Split up cases in *caselist* between the *nprocs* processors.
    Each case is a dictionary of parameters for that case.
    Uses multiprocessing.Pool to assign cases to processes.

    *run_one_case* should be a function with a single input *case*
    that runs a single case.

    Prints out what will be done and then waits abort_time seconds
    before continuing, so user can abort if necessary.
    """

    from multiprocessing import Pool, TimeoutError

    print("\n%s cases will be run on %s processors" % (len(caselist),nprocs))
    print("You have %s seconds to abort..." % abort_time)

    time.sleep(abort_time) # give time to abort

    with Pool(processes=nprocs) as pool:
        pool.map(run_one_case, caselist)



def make_all_cases_sample():
    """
    Output: *caselist*, a list of cases to be run.
    Each case should be dictionary of any parameters needed to set up an
    individual case.  These will be used by run_one_case.

    This is a sample where each case has a single parameter 'num'.
    Specialize this code to the problem at hand.
    """

    # Create a list of the cases to be run:
    caselist = []
    num_cases = 7

    for num in range(num_cases):
        case = {'num': num}
        caselist.append(case)

    return caselist


def run_one_case_sample(case):
    """
    Generic code, must be specialized to the problem at hand.
    Input *case* should be a dictionary with any parameters needed to set up
    and run a specific case.
    """

    p = current_process()

    # For this sample, case['num'] is just an identifying number.
    print('Sample job... process %i now running case %i' \
            % (p.pid,case['num']))

    # This part shows how to redirect stdout so output from any
    # print statements go to a unique file...
    import sys
    import datetime


    message = ""
    stdout_fname = 'case%s_out.txt' % case['num']
    try:
        stdout_file = open(stdout_fname, 'w')
        message = message +  "Python output from this case will go to %s\n" \
                            % stdout_fname
    except:
        raise Exception("Cannot open file %s" % stdout_fname)

    sys_stdout = sys.stdout
    sys.stdout = stdout_file
    # send any errors to the same file:
    sys_stderr = sys.stderr
    sys.stderr = stdout_file


    timenow = datetime.datetime.today().strftime('%Y-%m-%d at %H:%M:%S')
    print('Working on case %s, started at %s' % (case['num'],timenow))

    print('Process %i is running this case ' % p.pid)

    # replace this with something useful:
    sleep_time = 2
    print("Will sleep for %s seconds..." % sleep_time)
    time.sleep(sleep_time)

    if 0:
        # throw an error to check that output:
        time.no_such_function()

    timenow = datetime.datetime.today().strftime('%Y-%m-%d at %H:%M:%S')
    print('Done with case %s at %s' % (case['num'],timenow))

    # Reset stdout and stdout:
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr


if __name__ == "__main__":

    # Sample code...

    if len(sys.argv) > 1:
        nprocs = int(sys.argv[1])
    else:
        nprocs = 1

    caselist = make_all_cases_sample()
    run_many_cases_pool(caselist, nprocs, run_one_case=run_one_case_sample)
    print("Done... See files caseN_out.txt for python output from each case")
