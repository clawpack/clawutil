#!/usr/bin/env python
# encoding: utf-8
"""
Generic code for running the fortran version of Clawpack and sending the
results to subdirectory output of the directory from which this is executed.
Execute via
    $ python $CLAW/clawutil/src/python/clawutil/runclaw.py
from a directory that contains a claw.data file and a Clawpack executable.
"""

from __future__ import absolute_import
from __future__ import print_function
import six

import os
import sys
import glob
import shutil
import shlex
import subprocess
import time

from clawpack.clawutil.data import ClawData
from clawpack.clawutil.claw_git_status import make_git_status_file

# define an execution error class that returns a
# message as well as the rest of the subprocess exceptions
class ClawExeError(subprocess.CalledProcessError):
    def __init__(self, msg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg = msg
        
    def __str__(self):
        return self.msg

def runclaw(xclawcmd=None, outdir=None, overwrite=True, restart=None, 
            rundir=None, print_git_status=False, nohup=False, nice=None,
            xclawout=None, xclawerr=None, verbose=True):
    """
    Run the Fortran version of Clawpack using executable xclawcmd, which is
    typically set to 'xclaw', 'xamr', etc.

    If it is not set by the call, get it from the environment variable
    CLAW_EXE.  Default to 'xclaw' if that's not set.

    If overwrite is True, it's ok to zap current contents of the outdir.
    If overwrite is False, move the outdir (or copy in the case of a restart)
    to a backup directory with a unique name based on time executed.

    If restart is None, determine whether this is a restart from claw.data
    (as set in setrun.py).  Can remove setting RESTART in Makefiles.
    
    If rundir is None, all *.data is copied from current directory, if a path 
    is given, data files are copied from there instead.

    If print_git_status is True, print a summary of the git status of all
    clawpack repositories in the file claw_git_status.txt in outdir.

    If nohup is True, run the xclawcmd in nohup mode:  runs in background and
    output goes into nohup.out file in the directory specified by outdir,
    rather than all output going to the screen.  The job keeps running if user 
    logs off.  Useful for scripts starting long jobs in batch mode.

    If type(nice) is int, runs the code using "nice -n "
    with this nice value so it doesn't hog computer resources.
    
    xclawout and xclawerr define the locations of stdout and stderr for the 
    execution of CLAW_EXE. They should be strings to filepaths or open file
    objects or ``subprocess.PIPE`` or ``subprocess.STDOUT``. To pass both
    to the same file, specify ``xclawout`` as the filepath and 
    ``xclawerr=subprocess.STDOUT``.

    """
    
    if nice is not None:
        try:
            nice = int(nice)
        except:
            nice = None

    # convert strings passed in from Makefile to boolean:
    if type(overwrite) is str:
        overwrite = (overwrite.lower() in ['true','t'])
    if type(restart) is str:
        if restart == 'None':
            restart = None
        else:
            restart = (restart.lower() in ['true','t'])
    if type(print_git_status) is str:
        print_git_status = (print_git_status.lower() in ['true','t'])
    if type(nohup) is str:
        nohup = (nohup.lower() in ['true','t'])
    

    if xclawcmd is None:
        # Determine what executable to use from environment variable CLAW_EXE
        # Default to 'xclaw' if it's not set:
        xclawcmd = os.environ.get('CLAW_EXE', 'xclaw')
    

    if outdir is None:
        outdir = '.'

    if rundir is None:
        rundir = os.getcwd()
    rundir = os.path.abspath(rundir)
    print("==> runclaw: Will take data from ", rundir)

    # directory for fort.* files:
    outdir = os.path.abspath(outdir)
    print('==> runclaw: Will write output to ',outdir)
    
    if restart is None:
        # Added option to determine restart from claw.data (i.e. setrun.py)
        clawdata = ClawData()
        clawdata.read(os.path.join(rundir,'claw.data'), force=True) 
        restart = clawdata.restart
        
    xclawcmd = os.path.abspath(xclawcmd)

    if os.path.isfile(outdir):
        print("==> runclaw: Error: outdir specified is a file")
        return

    if (os.path.isdir(outdir) & (not overwrite)):
        # copy the old outdir before possibly overwriting
        tm = time.localtime(os.path.getmtime(outdir))
        year = str(tm[0]).zfill(4)
        month = str(tm[1]).zfill(2)
        day = str(tm[2]).zfill(2)
        hour = str(tm[3]).zfill(2)
        minute = str(tm[4]).zfill(2)
        second = str(tm[5]).zfill(2)
        outdir_backup = outdir + '_%s-%s-%s-%s%s%s' \
              % (year,month,day,hour,minute,second)
        if verbose:
            print("==> runclaw: Directory already exists: ",os.path.split(outdir)[1])
            if restart:
                print("==> runclaw: Copying directory to:      ",os.path.split(outdir_backup)[1])
            else:
                print("==> runclaw: Moving directory to:      ",os.path.split(outdir_backup)[1])
            time.sleep(1)

        try:
            shutil.move(outdir,outdir_backup)
            if restart:
                shutil.copytree(outdir_backup,outdir)
        except:
            print("==> runclaw: Could not move directory... copy already exists?")

    if six.PY2:
        if (not os.path.isdir(outdir)):
            try:
                os.mkdir(outdir)
            except:
                print("Cannot make directory ",outdir)
                return
    else:
        os.makedirs(outdir, exist_ok=True)

    if print_git_status not in [False,'False']:
        # create files claw_git_status.txt and claw_git_diffs.txt in
        # outdir:
        make_git_status_file(outdir=outdir)

    # old fort.* files to be removed for new run?
    fortfiles = glob.glob(os.path.join(outdir,'fort.*'))
    # also need to remove gauge*.txt output files now that the gauge
    # output is no longer in fort.gauge  (but don't remove new gauges.data)
    gaugefiles = glob.glob(os.path.join(outdir,'gauge*.txt'))

    if (overwrite and (not restart)):
        # remove any old versions:
        if verbose:
            print("==> runclaw: Removing all old fort/gauge files in ", outdir)
        for file in fortfiles + gaugefiles:
            os.remove(file)
    elif restart:
        if verbose:
            print("==> runclaw: Restart: leaving original fort/gauge files in ", outdir)
    else:
        # this should never be reached: 
        # if overwrite==False then outdir has already been moved
        if len(fortfiles+gaugefiles) > 1:
            print("==> runclaw: *** Remove fort.* and gauge*.txt")
            print("  from output directory %s and try again," % outdir)
            print("  or use overwrite=True in call to runclaw")
            print("  e.g., by setting OVERWRITE = True in Makefile")
            return

    datafiles = glob.glob(os.path.join(rundir,'*.data'))
    if datafiles == ():
        print("==> runclaw: Warning: no data files found in directory ",rundir)
    else:
        if rundir != outdir:
            for file in datafiles:
                shutil.copy(file, os.path.join(outdir,os.path.basename(file)))

    # execute command to run fortran program:
    if nohup:
        # run in nohup mode:
        print("\n==> Running in nohup mode, output will be sent to:")
        print("      %s/nohup.out" % outdir)
        if type(nice) is int:
            cmd = "nohup time nice -n %s %s " % (nice,xclawcmd)
        else:
            cmd = "nohup time %s " % xclawcmd
        print("\n==> Running with command:\n   ", cmd)
    else:
        if type(nice) is int:
            cmd = "nice -n %s %s " % (nice,xclawcmd)
        else:
            cmd = xclawcmd
        print("\n==> Running with command:\n   ", cmd)

    cmd_split = shlex.split(cmd)
    if isinstance(xclawout, str):
        xclawout = open(xclawout,'w', encoding='utf-8',
                        buffering=1)
    if isinstance(xclawerr, str):
        xclawerr = open(xclawerr,'w', encoding='utf-8',
                        buffering=1)
    try:
        proc = subprocess.check_call(cmd_split,
                                     cwd=outdir,
                                     stdout=xclawout,
                                     stderr=xclawerr)

    except subprocess.CalledProcessError as cpe:
        exe_error_str = "\n\n*** FORTRAN EXE FAILED ***\n"
        raise ClawExeError(exe_error_str, cpe.returncode, cpe.cmd,
                           output=cpe.output, 
                           stderr=cpe.stderr)
    
    print('==> runclaw: Done executing %s via clawutil.runclaw.py' %\
                xclawcmd)
    print('==> runclaw: Output is in ', outdir)

    return proc
    

#----------------------------------------------------------

def create_path(path,overwrite=False):
    r"""Create a path and over write it if requested"""
    
    if not os.path.exists(path):
        os.makedirs(path)
    elif overwrite:
        data_files = glob.glob(path,"*")
        for data_file in data_files:
            os.remove(data_file)

def create_output_paths(name,prefix,**kargs):
    r"""Create an output, plotting, and data path with the given prefix."""
    
    if 'outdir' in kargs:
        outdir = kargs['outdir']
    else:
        base_path = os.environ.get('DATA_PATH',os.getcwd())
        outdir = os.path.join(base_path,name,"%s_output" % prefix)
    if 'plotdir' in kargs:
        plotdir = kargs['plotdir']
    else:
        base_path = os.environ.get('DATA_PATH',os.getcwd())
        plotdir = os.path.join(base_path,name,"%s_plots" % prefix)
    if 'logfile' in kargs:
        log_path = kargs['logfile']
    else:
        base_path = os.environ.get('DATA_PATH',os.getcwd())
        log_path = os.path.join(base_path,name,"%s_log.txt" % prefix)
        
    create_path(outdir,overwrite=kargs.get('overwrite',False))
    create_path(plotdir,overwrite=kargs.get('overwrite',False))
    create_path(os.path.dirname(log_path),overwrite=False)
    
    return outdir,plotdir,log_path


def replace_stream_handlers(logger_name,log_path,log_file_append=True):
    r"""Replace the stream handlers in the logger logger_name
        
        This routine replaces all stream handlers in logger logger_name with a 
        file handler which outputs to the log file at log_path. If 
        log_file_append is True then the log files is opened for appending, 
        otherwise it is written over.
        
        TODO: This seems to only be working in certain instances, need to debug
    """
    import logging
    
    logger = logging.getLogger(logger_name)
    handler_list = [handler for handler in logger.handlers if isinstance(handler,logging.StreamHandler)]
    for handler in handler_list:
        # Create new handler
        if log_file_append:
            new_handler = logging.FileHandler(log_path,'a')
        else:
            new_handler = logging.FileHandler(log_path,'w')
            log_file_append = True
        new_handler.setLevel(handler.level)
        # new_handler.name = handler.name
        new_handler.setFormatter(handler.formatter)
            
        # Remove old handler
        if isinstance(handler,logging.FileHandler):
            handler.close()
            if os.path.exists(handler.baseFilename):
                os.remove(handler.baseFilename)
        logger.removeHandler(handler)
          
        # Add new handler  
        logger.addHandler(new_handler)


if __name__=='__main__':
    """
    If executed at command line prompt, simply call the function, with
    any argument used as setplot:
    """
    import sys
    args = sys.argv[1:]   # any command line arguments
    runclaw(*args)
