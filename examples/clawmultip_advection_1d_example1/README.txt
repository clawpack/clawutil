
Modified example from $CLAW/classic/examples/advection_1d_example1

The script run_cases_clawpack.py runs 6 different cases:
    3 resolutions mx = 50, 100, 200 points
    each with order = 1 and order = 2

First create the executable xclaw via:

    $ make .exe

Then run the script via:

    $ python run_cases_clawpack.py

run_cases_clawpack.py creates a caselist of dictionaries for the 
cases to be run and then does all the runs and creates corresponding plots.

Six _output and six _plots directories should be created.  To view all the
plots in 6 separate browser tabs, open _plots*/allframes_fig1.html

setrun_cases.py contains the setrun function, with an additional parameter case
so that a case dictionary can be passed in for use in setting up a single run.

Similarly, setplot_cases.py provides the setplot function, with an
additional parameter case so that the titles of the plots can be properly
formed for each particular case.


Code from $CLAW/clawutil/src/python/clawutil is used, see the
    README_clawmultip.txt
file in that directory for more information.

After running this code, case_summary.txt will list the case dictionary for
all the cases run.  (The file will be added to if more cases are later run.)

In addition, each _output directory will contain files
    case_info.txt
    case_info.pkl
with the dictionary entries for this case.  The case_info.txt file is
human-readable, while case_info.pkl is a pickled version that can be loaded
to recreate the case dictionary via:

    import pickle
    with open(outdir + '/case_info.pkl', 'rb') as f:
        case = pickle.load(f)
        
