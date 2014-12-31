"""
Useful tools for running Clawpack from an IPython notebook.
"""

from IPython.core.display import display
try:
    from IPython.display import FileLink
except:
    print "*** Ipython version does not support FileLink"


def make_htmls(outfile=None, verbose=False, readme_link=True):
    """Perform 'make .htmls' and display link."""
    import os,sys
    
    if outfile is None:
        outfile='htmls_output.txt'
    cmd = 'make .htmls &> %s' % outfile

    if verbose:
        print "Making html documentation files... %s" % cmd
        sys.stdout.flush()

    status = os.system(cmd)
    
    if verbose:
        local_file = FileLink(outfile)
        print "Done...  Check this file to see output:" 
        display(local_file)
    if readme_link:
        print "See the README.html file for links to input files..."
        display(FileLink('README.html'))
    
def make_data(verbose=True):
    """Perform 'make data' and display link."""
    import os,sys
    
    outfile='data_output.txt'
    cmd = 'make data &> %s' % outfile

    if verbose:
        print "Making Fortran data files... %s" % cmd
        sys.stdout.flush()

    status = os.system(cmd)
    
    if verbose:
        local_file = FileLink(outfile)
        print "Done...  Check this file to see output:" 
        display(local_file)

def make_exe(new=False, verbose=True):
    """
    Perform 'make .exe' and display link.
    If *new = True*, do 'make new' instead to force recompilation of everything.
    """
    import os,sys
    
    outfile='compile_output.txt'
    if new:
        cmd = 'make new &> %s' % outfile
    else:
        cmd = 'make .exe &> %s' % outfile

    if verbose:
        print "Compiling code... %s" % cmd
        sys.stdout.flush()

    status = os.system(cmd)
    
    if verbose:
        local_file = FileLink(outfile)
        print "Done...  Check this file to see output:" 
        display(local_file)
    
def make_output(label=None, verbose=True):
    """Perform 'make output' and display link."""
    import os,sys
    
    if label is None: 
        label = ''
    else:
        if label[0] != '_':
            label = '_' + label
    outdir = '_output%s' % str(label)
    outfile = 'run_output%s.txt' % str(label)

    cmd = 'make output OUTDIR=%s &> %s' % (outdir,outfile)

    if verbose:
        print "Running code... %s" % cmd
        sys.stdout.flush()
    status = os.system(cmd)
    
    if verbose:
        local_file = FileLink(outfile)
        print "Done... Check this file to see output:"
        display(local_file)

    return outdir
    
def make_plots(label=None, verbose=True):
    """Perform 'make plots' and display links"""
    import os, sys

    if label is None: 
        label = ''
    else:
        if label[0] != '_':
            label = '_' + label
    outdir = '_output%s' % str(label)
    plotdir = '_plots%s' % str(label)
    outfile = 'plot_output%s.txt' % str(label)

    cmd = 'make plots OUTDIR=%s PLOTDIR=%s  &> %s' % (outdir,plotdir,outfile)

    if verbose:
        print "Making plots... %s" % cmd
        sys.stdout.flush()

    status = os.system(cmd)
    
    if verbose:
        local_file = FileLink(outfile)
        print "Done... Check this file to see output:"
        display(local_file)
    
        index_file = FileLink('%s/_PlotIndex.html' % plotdir)
        print "View plots created at this link:"
        display(index_file)

    return plotdir
    

def make_output_and_plots(label=None, verbose=True):

    import sys
    if label is None: 
        label = ''
    else:
        if label[0] != '_':
            label = '_' + label

    outdir = make_output(label,verbose)
    plotdir = make_plots(label,verbose)
    return outdir,plotdir
