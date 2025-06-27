"""
The function run_one_case_clawpack defined in this module can be used when
calling mulitp_tools.run_many_cases_pool, along with a list of cases,
in order to perform a parameter sweep using Clawpack.

The function make_cases_template is a template for how to make a caselist
of case dictionaries with some values required by run_one_case_clawpack.

For sample code that uses this, see
    $CLAW/clawutil/examples/clawmultip_advection_1d_example
and the README.txt file in that directory.
"""


def run_one_case_clawpack(case):
    """
    Code to run a specific case and/or plot the results using Clawpack.
    This function can be pased in to multip_tools.run_many_cases_pool
    along with a list of cases to perform a parameter sweep based on the cases.

    Input `case` should be a dictionary with any parameters needed to set up
    and run a specific case and/or plot the results.

    It is assumed that values specified by the setrun function provided
    will be used for every run, with the exception of the parameters
    set for each case, and similarly for setplot.

    In order to pass the case into setrun and/or setplot so that the desired
    parameters can be modified, you can provide functions that include
    an additional parameter `case`.

    This function assumes that, in addition to any parameters you want to
    modify for your parameter sweep, the case dictionary includes the following:

        case['xclawcmd'] = path to the Clawpack executable to perform each run
                           or None if you do not want to run Clawpack
                              (in order to only make a new set of plots based
                              on existing output).

        case['outdir'] = path to _output directory for this run

        case['plotdir'] = path to _plots directory for this run,
                          or None if you do not want to make plots.

        case['setrun_file'] = path to a file that contains a function
                                 setrun(claw_pkg, case)
                              so that `case` can be passed in.
                              (Only needed if case['xclawcmd'] is not None)

        case['setplot_file'] = path to a file that contains a function 
                                 setplot(plotdata, case)
                              so that `case` can be passed in (if desired, or
                              a standard setplot(plotdata) can be used if it
                              is independent of the case).
                              (Only needed if case['plotdir'] is not None)

    The following are optional to set:

        case['overwrite'] = True/False.  (Default is True)
                            Aborts if this is False and case['outdir'] exists.
        case['runexe'] = Any string that must preceed xclawcmd to run the code
                         (Default is None)
        case['nohup'] = True to run with nohup. (Default is False)
        case['redirect_python'] = True/False. Redirect stdout to a file
                                  case['outdir'] + '/python_output.txt'
                                  (Default is True)

        In addition, add any other parameters to the case dictionary that
        you want to have available in setrun and/or setplot.

    For sample code that sets up a list of cases with modified setrun and
    setplot functions, see
        $CLAW/clawutil/examples/clawmultip_advection_1d_example
    and the README.txt file in that directory.

    This code also produces (or appends to) a file case_summary.txt
    listing the case dictionary entries for all the cases run.

    In addition, each _output directory will contain files
        case_info.txt
        case_info.pkl
    with the dictionary entries for this case.  The case_info.txt file is 
    human-readable, while case_info.pkl is a pickled version that can be loaded 
    to recreate the case dictionary via:
        import pickle
        with open(outdir + '/case_info.pkl', 'rb') as f:
            case = pickle.load(f)
    """

    import os,sys,shutil,pickle
    import inspect
    import datetime
    import importlib
    from multiprocessing import current_process
    from clawpack.clawutil.runclaw import runclaw
    from clawpack.clawutil import multip_tools
    from clawpack.visclaw.plotclaw import plotclaw

    p = current_process()

    # unpack the dictionary case to get parameters for this case:

    xclawcmd = case.get('xclawcmd', None)
    run_clawpack = xclawcmd is not None

    plotdir = case.get('plotdir', None)
    make_plots = plotdir is not None

    case_name = case['case_name']
    outdir = case['outdir']
    setrun_file = case.get('setrun_file', 'setrun.py')
    setplot_file = case.get('setplot_file', 'setplot.py')

    # clawpack.clawutil.runclaw parameters that might be specified:
    overwrite = case.get('overwrite', True) # if False, abort if outdir exists
    runexe = case.get('runexe', None)  # string that must preceed xclawcmd
    nohup = case.get('nohup', False)  # run with nohup

    redirect_python = case.get('redirect_python', True) # sent stdout to file


    if os.path.isdir(outdir):
        print('overwrite = %s and outdir already exists: %s' \
                % (overwrite,outdir))
        # note that runclaw will use overwrite parameter to see if allowed
    else:
        try:
            os.mkdir(outdir)
            print('Created %s' % outdir)
        except:
            raise Exception("Could not create directory: %s" % outdir)


    #timenow = datetime.datetime.today().strftime('%Y-%m-%d at %H:%M:%S')
    timenow = datetime.datetime.utcnow().strftime('%Y-%m-%d at %H:%M:%S') \
                + ' UTC'
    message = "Process %i started   case %s at %s\n" \
                % (p.pid, case_name, timenow)
    print(message)


    if redirect_python:
        stdout_fname = outdir + '/python_output.txt'
        try:
            stdout_file = open(stdout_fname, 'w')
            message = "Python output from this run will go to\n   %s\n" \
                                % stdout_fname
        except:
            print(message)
            raise Exception("Cannot open file %s" % stdout_fname)


        # Redirect stdout,stderr so any print statements go to a unique file...
        import sys
        sys_stdout = sys.stdout
        sys.stdout = stdout_file
        sys_stderr = sys.stderr
        sys.stderr = stdout_file
        print(message)

    # write out all case parameters:
    fname = os.path.join(outdir, 'case_info.txt')
    with open(fname,'w') as f:
        f.write('----------------\n%s\n' % timenow)
        f.write('case %s\n' % case['case_name'])
        for k in case.keys():
            f.write('%s:  %s\n' % (k.ljust(20), case[k]))
    print('Created %s' % fname)

    # pickle case dictionary for reloading later:
    fname = os.path.join(outdir, 'case_info.pkl')
    with open(fname, 'wb') as f:
        pickle.dump(case, f)
    print('Created %s' % fname)

    # global summary file:
    fname = 'case_summary.txt'
    with open(fname,'a') as f:
        f.write('=========\n%s\n\ncase_name: %s\n' % (timenow,case['case_name']))
        for k in case.keys():
            if k != 'case_name':
                f.write('%s:  %s\n' % (k.ljust(20), case[k]))


    if run_clawpack:

        # initialize rundata using specified setrun file:
        spec = importlib.util.spec_from_file_location('setrun',setrun_file)
        setrun = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(setrun)

        # The setrun function may have been modified to accept an argument
        # `case` so that the dictionary of parameters can be passed in:

        if 'case' in inspect.signature(setrun.setrun).parameters.keys():
            rundata = setrun.setrun(case=case)
        else:
            print('*** Warning: setrun does not support case parameter: ', \
                    '    setrun_file = %s' % setrun_file)
            rundata = setrun.setrun()

        # write .data files in outdir:
        rundata.write(outdir)

        # Run the clawpack executable
        if not os.path.isfile(xclawcmd):
            raise Exception('Executable %s not found' % xclawcmd)

        # redirect output and error messages:
        outfile = os.path.join(outdir, 'fortran_output.txt')
        print('Fortran output will be redirected to\n    ', outfile)

        # Use data from rundir=outdir, which was just written above...
        runclaw(xclawcmd=xclawcmd, outdir=outdir, overwrite=overwrite,
                rundir=outdir, nohup=nohup, runexe=runexe,
                xclawout=outfile, xclawerr=outfile)

    if make_plots:

        # initialize plotdata using specified setplot file:
        spec = importlib.util.spec_from_file_location('setplot',setplot_file)
        setplot = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(setplot)

        # The setplot function may have been modified to accept an argument
        # `case` so that the dictionary of parameters can be passed in:

        if 'case' in inspect.signature(setplot.setplot).parameters.keys():
            plotdata = setplot.setplot(plotdata=None,case=case)
        else:
            print('*** Warning: setplot does not support case parameter: ', \
                    '    setplot_file = %s' % setplot_file)
            plotdata = setplot.setplot(plotdata=None)


        # note that setplot can also be modified to return None if the
        # user does not want to make frame plots (setplot can explicitly
        # make other plots or do other post-processing)

        if plotdata is not None:
            # user wants to make time frame plots using plotclaw:
            plotdata.outdir = outdir
            plotdata.plotdir = plotdir

            # modified plotclaw is needed in order to pass plotdata here:
            plotclaw(outdir, plotdir, setplot, plotdata=plotdata)
        else:
            # assume setplot already made any plots desired by user,
            # e.g. fgmax, fgout, or specialized gauge plots.
            print('plotdata is None, so not making frame plots')

    #timenow = datetime.datetime.today().strftime('%Y-%m-%d at %H:%M:%S')
    timenow = datetime.datetime.utcnow().strftime('%Y-%m-%d at %H:%M:%S') \
                + ' UTC'
    message = "Process %i completed case %s at %s\n" \
                % (p.pid, case_name, timenow)
    print(message)

    if redirect_python:
        stdout_file.close()
        # Fix stdout again
        sys.stdout = sys_stdout
        sys.stderr = sys_stderr
        print(message) # to screen


def make_cases_template():

    """
    Create a list of the cases to be run, varying some setrun and/or setplot
    parameters for each case.
    """

    caselist = []

    num_cases = 2
    for j in range(num_cases):
        case = {}
        case_name = 'case_%s' % str(j).zfill(2)  # e.g. case_01, case_02
        case['case_name'] = case_name

        case['outdir'] = '_output_%s' % case_name

        #case['xclawcmd'] = None  # if None, will not run code
        case['xclawcmd'] = 'xclaw'  # executable created by 'make .exe'

        # setrun parameters:
        case['setrun_file'] = 'setrun_cases.py'
        # setrun_case.py should contain a setrun function with case
        # as a keyword argument so we can pass in parameters

        #case['plotdir'] = None  # if None, will not make plots
        case['plotdir'] = '_plots_%s' % case_name

        case['setplot_file'] = 'setplot_cases.py'
        # setplot_case.py might contain a setplot function with case
        # as a keyword argument so we can pass in parameters

        # ADD CASE ENTRIES for any setrun or setplot parameters that
        # are case-dependent, and then use these in setrun / setplot, via:
        # case[key] = value   # for each parameter

        caselist.append(case)

    return caselist
