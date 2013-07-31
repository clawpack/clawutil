#!/usr/bin/env python
# encoding: utf-8
"""
Generic code for running the fortran version of Clawpack and sending the
results to subdirectory output of the directory from which this is executed.
Execute via
    $ python $CLAW/clawutil/src/python/clawutil/runclaw.py
from a directory that contains a claw.data file and a Clawpack executable.
"""

import os
import sys
import glob
import shutil
from claw_git_status import make_git_status_file

def runclaw(xclawcmd=None, outdir=None, overwrite=True, restart=False, 
            rundir=None, print_git_status=False):
    """
    Run the Fortran version of Clawpack using executable xclawcmd, which is
    typically set to 'xclaw', 'xamr', etc.

    If it is not set by the call, get it from the environment variable
    CLAW_EXE.  Default to 'xclaw' if that's not set.
    
    If rundir is None, all *.data is copied from current directory, if a path 
    is given, data files are copied from there instead.
    """
    
    import os,glob,shutil,time
    verbose = True
    xclawout = None
    xclawerr = None

    if type(overwrite) is str:
        # convert to boolean
        overwrite = (overwrite.lower() in ['true','t'])
    
    if type(restart) is str:
        # convert to boolean
        restart = (restart.lower() in ['true','t'])
    

    if xclawcmd is None:
        # Determine what executable to use from environment variable CLAW_EXE
        # Default to 'xclaw' if it's not set:
        xclawcmd = os.environ.get('CLAW_EXE', 'xclaw')
    

    if outdir is None:
        outdir = '.'
        
    if rundir is None:
        rundir = os.getcwd()
    rundir = os.path.abspath(rundir)
    print "==> runclaw: Will take data from ", rundir

    # directory for fort.* files:
    outdir = os.path.abspath(outdir)
    print '==> runclaw: Will write output to ',outdir
    
    
    #returncode = clawjob.runxclaw()

    if 1:
        startdir = os.getcwd()
        xdir = os.path.abspath(startdir)
        outdir = os.path.abspath(outdir)
        rundir = os.path.abspath(rundir)
        xclawcmd = os.path.join(xdir,xclawcmd)
        
        try:
            os.chdir(xdir)
        except:
            raise Exception( "==> runclaw: Cannot change to directory xdir = %s" %xdir)
            return 
    
    
        if os.path.isfile(outdir):
            print "==> runclaw: Error: outdir specified is a file"
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
                print "==> runclaw: Directory already exists: ",os.path.split(outdir)[1]
                if restart:
                    print "==> runclaw: Copying directory to:      ",os.path.split(outdir_backup)[1]
                else:
                    print "==> runclaw: Moving directory to:      ",os.path.split(outdir_backup)[1]
                time.sleep(1)
            
            try:
                shutil.move(outdir,outdir_backup)
                if restart:
                    shutil.copytree(outdir_backup,outdir)
            except:
                print "==> runclaw: Could not move directory... copy already exists?"
            
            
        if (not os.path.isdir(outdir)):
            try:
                os.mkdir(outdir)
            except:
                print "Cannot make directory ",outdir
                return
    
        try:
            os.chdir(outdir)
        except:
            print '==> runclaw: *** Error in runxclaw: cannot move to outdir = ',\
                  outdir
            raise
            return
    
        if print_git_status not in [False,'False']:
            make_git_status_file()

        fortfiles = glob.glob(os.path.join(outdir,'fort.*'))
        if (overwrite and (not restart)):
            # remove any old versions:
            if verbose:
                print "==> runclaw: Removing all old fort files in ", outdir
            for file in fortfiles:
                os.remove(file)
        elif restart:
            if verbose:
                print "==> runclaw: Restart: leaving original fort files in ", outdir
        else:
            if len(fortfiles) > 1:
                print "==> runclaw: *** Remove fort.* and try again,"
                print "  or use overwrite=True in call to runxclaw"
                print "  e.g., by setting CLAW_OVERWRITE = True in Makefile"
                return
            
        
        try:
            os.chdir(rundir)
        except:
            raise Exception("Cannot change to directory %s" % rundir)
            return 
    
        datafiles = glob.glob('*.data')
        if datafiles == ():
            print "==> runclaw: Warning: no data files found in directory ",rundir
        else:
            if rundir != outdir:
                for file in datafiles:
                    shutil.copy(file,os.path.join(outdir,file))
    
        if xclawout:
            xclawout = open(xclawout,'wb')
        if xclawerr:
            xclawerr = open(xclawerr,'wb')
    
        os.chdir(outdir)
    
        #print "\nIn directory outdir = ",outdir,"\n"
    
        # execute command to run fortran program:
    
        try:
            #print "\nExecuting ",xclawcmd, "  ...  "
            #pclaw = subprocess.Popen(xclawcmd,stdout=xclawout,stderr=xclawerr)
            #print '+++ pclaw started'
                #pclaw.wait()   # wait for code to run
            #returncode = pclaw.returncode
            #print '+++ pclaw done'
            
            returncode = os.system(xclawcmd)
    
            if returncode == 0:
                print "\n==> runclaw: Finished executing\n"
            else:
                print "\n ==> runclaw: *** Runtime error: return code = %s\n " % returncode
        except:
            raise Exception("Could not execute command %s" % xclawcmd)
    
        os.chdir(startdir)

    if returncode != 0:
        print '==> runclaw: *** fortran returncode = ', returncode, '   aborting'
    print '==> runclaw: Done executing %s via clawutil.runclaw.py' % xclawcmd
    print '==> runclaw: Output is in ', outdir
    

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
    
    if kargs.has_key('outdir'):
        outdir = kargs['outdir']
    else:
        base_path = os.environ.get('DATA_PATH',os.getcwd())
        outdir = os.path.join(base_path,name,"%s_output" % prefix)
    if kargs.has_key('plotdir'):
        plotdir = kargs['plotdir']
    else:
        base_path = os.environ.get('DATA_PATH',os.getcwd())
        plotdir = os.path.join(base_path,name,"%s_plots" % prefix)
    if kargs.has_key('logfile'):
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
