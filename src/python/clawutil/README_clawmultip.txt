
README_clawmultip.txt
------------------------

The module multip_tools.py provides a function 

    run_many_cases_pool(caselist, nprocs, run_one_case, abort_time=5)

that takes a list caselist of dictionaries specifiying parameters needed for
each case, and a function run_one_case that takes a single case dictionary
as input and runs that case.  The Python mulitprocessing.Pool function
is then used to split up the case between nprocs processors.

This module also contains a sample function
    run_one_case_sample(case)
that simply prints out the case number set in case['num'] and 
    make_all_cases_sample()
that creates the caselist of dictionaries for each case.

------------------------

The module clawmultip_tools.py provides a function that can be used along with 
multip_tools.py to easily do a parameter sweep in Clawpack:

    run_one_case_clawpack(case)

Some specific entries of the case dictionary must be specified in order
to control the Clawpack run and/or plotting done for each case.

See the docstrings for more details.  

Example usage is found in 
    $CLAW/clawutil/examples/clawmultip_advection_1d_example1
See the README.txt file in that directory for more information.

