"""
Compare plots in all subdirectories to archived results.

Assumes the code has been freshly run in all subdirectories.  The script
make_all.py can be used for this.

Function test_subdirs returns True if all .png files agree in 
alls subdirectories the two directories test_dir and compare_dir.

Image differences can be viewed by opening a browser to 
    _image_diff/_ImageDiffIndex.html

If compare_dir is not specified, attempt to compare with plots in the latest
Clawpack gallery.  For this to work you need to first clone and/or
fetch a zip file of the latest gallery results from
     git://github.com/clawpack/clawpack.github.com
Put this in the top $CLAW directory so that there is a subdirectory
$CLAW/clawpack.github.com.  The archived plots can then be found in
$CLAW/clawpack.github.com/doc/_static.

"""

import os, subprocess
from clawpack.clawutil import imagediff


def test_subdirs(compare_dir=None,examples_dir='.',\
                 verbose=True,relocatable=False):

    from .make_all import list_examples

    if compare_dir is None:
        print("Attempting to find gallery for comparison...")
        try:
            CLAW = os.environ['CLAW']
        except:
            raise Exception("Need to set CLAW environment variable")
        examples_dir = os.path.abspath(examples_dir)

        iclaw = examples_dir.find(CLAW)
        if iclaw==-1:
            print("*** examples_dir is not under $CLAW, failed to find gallery")
            return False
              
        gallery_home = os.path.join(CLAW,'clawpack.github.com','doc','_static')
        package = os.path.split(os.path.split(examples_dir)[0])[1]
        compare_dir = os.path.join(gallery_home,package,'examples')
        if not os.path.isdir(compare_dir):
            print("*** Failed to find ",compare_dir)
            return False


    all_ok = True

    dir_list = list_examples(examples_dir)
    print("Found the following example subdirectories:")
    for d in dir_list:
        print("    ", d)
 
    print("Will run imagediff on _plots in the above subdirectories of ")
    print("    ", examples_dir)
    print("Will compare to _plots in corresponding subdirectories of: \n   %s" \
            % compare_dir)
    if 0:
        ans = input("Ok? ")
        if ans.lower() not in ['y','yes']:
            print("Aborting.")
            all_ok = False
            return all_ok

    top_dir = os.getcwd()
    for test_subdir in dir_list:
        print("\n=============================================================")
        print(test_subdir)
        print("=============================================================")
        #subdir = os.path.split(test_subdir)[1]
        subdir = test_subdir[len(examples_dir)+1:]
        compare_subdir = os.path.join(compare_dir, subdir)
        test_plots = os.path.join(test_subdir,'_plots')
        compare_plots = os.path.join(compare_subdir, '_plots')

        if not os.path.isdir(test_plots):
            print("*** Cannot find _plots directory ")
            print("*** Looking for ",test_plots)
            all_ok = False
            continue

        if not os.path.isdir(compare_plots):
            print("*** Cannot find _plots directory to compare against")
            print("*** Looking for ",compare_plots)
            all_ok = False
            continue
    
        os.chdir(subdir)
        try:
            regression_ok = imagediff.imagediff_dir(test_plots,compare_plots, \
                                    relocatable=relocatable,overwrite=True, \
                                    verbose=verbose)
            if not regression_ok:
                print("*** Regression files are not all identical in ")
                print("   ",test_subdir)
        except:
            print("*** Error running imagediff with directories \n  %s\n  %s\n" \
                        % (test_plots,compare_plots))
            regression_ok = False
        all_ok = all_ok and regression_ok
        os.chdir(top_dir)

    return all_ok
    
if __name__=="__main__":
    import sys
    all_ok = test_subdirs(*sys.argv[1:])
    print("==> all_ok = ",all_ok)


