"""
Compare the results of run_regression_tests.py with archived results, if they
can be found using clawpack.clawutil.fetch_regression_data.
"""

from clawpack.clawutil.fetch_regression_data import fetch_regression_data
from clawpack.clawutil.chardiff import chardiff_dir
from clawpack.clawutil.imagediff import imagediff_dir
import os,sys,glob


def compare_regression_tests(regression_dir="_regression_tests"):

    try:
        archived_dir, tar_file = fetch_regression_data(regression_dir)
        archived_dir = os.path.abspath(archived_dir)
        os.system("rm %s" % tar_file)
    except:
        print "*** Error retrieving regression results"
        sys.exit()


    try:
        os.chdir(regression_dir)
    except:
        print "*** Cannot cd to ",regression_dir
        sys.exit()

    index_file = 'index.html'
    hfile = open(index_file,'w')
    index_file = os.path.abspath(index_file)

    hfile.write("""<html>
        <h1>Regression test results</h1>
        <h2>Comparison of output files:</h2>
        <ul>
        """)

    outdirs = glob.glob('_output*')

    if outdirs == []:
        print "*** No output directories found"
    else:
        if glob.glob('_chardiffs*') != []:
            ans = raw_input("Ok to clobber all _chardiffs directories? ")
            if ans=='y': 
                os.system("rm -rf _chardiffs*")

    for outdir in outdirs:
        outdir_archived = archived_dir + "/" + outdir
        if not os.path.exists(outdir_archived):
            print "*** Cannot find directory ",outdir_archived
            print "***        will not compare to ",outdir
        else:
            diffdir = "_chardiffs" + outdir
            chardiff_dir(outdir_archived, outdir, dir3=diffdir)
            hfile.write("""<li> <a href="%s/_DiffIndex.html">%s</a>""" % (diffdir,outdir))

    hfile.write("""</ul>
        <h2>Comparison of plot files:</h2>
        <ul>
        """)

    plotdirs = glob.glob('_plots*')
    if plotdirs == []:
        print "*** No plots directories found"
    else:
        if glob.glob('_imagediffs*') != []:
            ans = raw_input("Ok to clobber all _imagediffs directories? ")
            if ans=='y': 
                os.system("rm -rf _imagediffs*")

    for plotdir in plotdirs:
        plotdir_archived = archived_dir + "/" + plotdir
        if not os.path.exists(plotdir_archived):
            print "*** Cannot find directory ",plotdir_archived
            print "***        will not compare to ",plotdir
        else:
            diffdir = "_imagediffs" + plotdir
            imagediff_dir(plotdir_archived, plotdir, dir3=diffdir)
            hfile.write("""<li> <a href="%s/_ImageDiffIndex.html">%s</a>""" % (diffdir,plotdir))

    hfile.write("""</ul>
        </html>
        """)
    hfile.close()

    print "\nTo see resulting diffs, open \n   %s\n" % index_file

if __name__=="__main__":

    compare_regression_tests(*sys.argv[1:])
