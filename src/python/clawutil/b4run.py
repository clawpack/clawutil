"""
Sample b4run.py file, defining a function b4run(rundir,outdir).  

If a file like this is in the rundir directory used by runclaw.py 
(e.g. the application directory from which you execute 'make .output'),
this will be executed after creating the outdir and before running 
the Clawpack code.

If no b4run.py file is found in the rundir then the environment variable B4RUN,
if set, is used to locate a file to be used more globally, e.g. you could
set this to point to $HOME/b4ruon.py for a default version to use if there
is no local version, or you can use this version globally by setting B4RUN to
$CLAW/clawutil/src/python/clawutil/b4run.py

Use this capability, for example, to copy any files you want to the outdir,
either because they are needed for the run or to archive them along
with the output.

This sample version copies the Makefile and any Python or Fortran codes.
Note that *.data files are automatically copied by runclaw.

It also creates (or appends to) a runlog.txt file containing information 
about this run: the rundir and the time/date the run started.

Adapt this file to your own needs.
"""


def b4run(rundir, outdir):

    import os,sys,glob,shutil,time

    # ---------------------------------------------------------------------
    # files to copy to outdir (in addition to *.data files always copied):
    to_copy = ['Makefile', '*.py', '*.f*']

    if rundir != outdir:
        for pattern in to_copy:
            files = glob.glob(pattern)  # files matching pattern
            for file in files:
                print('Copying %s to %s' % (file, outdir))
                shutil.copy(file, os.path.join(outdir,file))

    # ---------------------------------------------------------------------
    # also add to outdir/runlog.txt with info about when run was done
    # and from what directory:

    runlog = os.path.join(outdir, 'runlog.txt')

    tm = time.localtime()
    year = str(tm.tm_year).zfill(4)
    month = str(tm.tm_mon).zfill(2)
    day = str(tm.tm_mday).zfill(2)
    hour = str(tm.tm_hour).zfill(2)
    minute = str(tm.tm_min).zfill(2)
    tz = tm.tm_zone
    dt = '%s-%s-%s-%s:%s%s'  % (year,month,day,hour,minute,tz)

    with open(runlog,'a') as f:
        f.write('Run started at %s\n' % dt)
        f.write('from RUNDIR =\n   %s\n' % os.path.abspath(rundir))

