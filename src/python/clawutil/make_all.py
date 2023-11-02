"""
Performs 'make all' in each subdirectory to create sample results for the
gallery or to perform regression tests against results in the gallery,
or elsewhere.

Sends output and errors to separate files to simplify looking for errors.
"""

import os

# Determine directory:
try:
    CLAW = os.environ['CLAW']
except:
    raise Exception("Need to set CLAW environment variable")


def list_examples(examples_dir):
    """
    Searches all subdirectories of examples_dir for examples and prints out a list.
    """
    import os

    current_dir = os.getcwd()
    os.chdir(examples_dir)
    
    dirlist = []
    applist = []

    # Traverse directories depth-first (topdown=False) to insure e.g. that code in
    #    amrclaw/examples/acoustics_2d_radial/1drad 
    # is run before code in
    #    amrclaw/examples/acoustics_2d_radial

    for (dirpath, subdirs, files) in os.walk('.',topdown=False):

        if '_output' not in dirpath:
            # By convention we assume that a setrun.py file indicates this is an
            # example directory.
            files = os.listdir(os.path.abspath(dirpath))
            if 'setrun.py' in files:
                dirlist.append(os.path.abspath(dirpath))

    os.chdir(current_dir)

    return dirlist
        

def make_all(examples_dir = '.',make_clean_first=False, env=None):
    import os,sys

    if env is None:
        my_env = os.environ
    else:
        my_env = env

    examples_dir = os.path.abspath(examples_dir)
    if not os.path.isdir(examples_dir):
        raise Exception("Directory not found: %s" % examples_dir)

    current_dir = os.getcwd()

    dir_list = list_examples(examples_dir)
    print("Found the following example subdirectories:")
    for d in dir_list:
        print("    ", d)
 
    print("Will run code and make plots in the above subdirectories of ")
    print("    ", examples_dir)
    ans = input("Ok? ")
    if ans.lower() not in ['y','yes']:
        print("Aborting.")
        sys.exit()
    
    fname_output = 'make_all_output.txt'
    fout = open(fname_output, 'w')
    fout.write("ALL OUTPUT FROM RUNNING EXAMPLES\n\n")

    fname_errors = 'make_all_errors.txt'
    ferr = open(fname_errors, 'w')
    ferr.write("ALL ERRORS FROM RUNNING EXAMPLES\n\n")

    os.chdir(examples_dir)

    goodlist_run = []
    badlist_run = []
    
    import subprocess
    for directory in dir_list:

        fout.write("\n=============================================\n")
        fout.write(directory)
        fout.write("\n=============================================\n")
        ferr.write("\n=============================================\n")
        ferr.write(directory)
        ferr.write("\n=============================================\n")

        os.chdir(directory)
        print(directory)

        # flush I/O buffers:
        fout.flush()
        ferr.flush()

        if make_clean_first:
            # Run 'make clean':
            job = subprocess.Popen(['make','clean'], \
                      stdout=fout,stderr=ferr)
            return_code = job.wait()
                
        # Run 'make all':
        job = subprocess.Popen(['make','all'], \
                  stdout=fout,stderr=ferr,env=my_env)
        return_code = job.wait()
                
        if return_code == 0:
            print("Successful run\n")
            goodlist_run.append(directory)
        else:
            print("*** Run errors encountered: see %s\n" % fname_errors)
            badlist_run.append(directory)


    print('------------------------------------------------------------- ')
    print(' ')
    print('Ran "make all" and created output and plots in directories:')
    if len(goodlist_run) == 0:
        print('   None')
    else:
        for d in goodlist_run:
            print('   ',d)
    print(' ')
    
    print('Errors encountered in the following directories:')
    if len(badlist_run) == 0:
        print('   None')
    else:
        for d in badlist_run:
            print('   ',d)
    print(' ')
    
    fout.close()
    ferr.close()
    print('For all output see ', fname_output)
    print('For all errors see ', fname_errors)

    os.chdir(current_dir)


def make_notebook_htmls(examples_dir = '.',make_clean_first=False, env=None):
    import os,sys,glob

    if env is None:
        my_env = os.environ
    else:
        my_env = env

    examples_dir = os.path.abspath(examples_dir)
    if not os.path.isdir(examples_dir):
        raise Exception("Directory not found: %s" % examples_dir)

    current_dir = os.getcwd()

    dir_list = list_examples(examples_dir)
    print("Found the following Jupyter notebooks:")
    nb_dir_list = []
    for d in dir_list:
        notebooks = glob.glob(d + '/*.ipynb')
        if len(notebooks) != 0:
            nb_dir_list.append(d)
        for nbfile in notebooks:
            print(nbfile)
            
    if len(nb_dir_list) == 0:
        print("  none")
        sys.exit()
 
    print("Will run notebooks and make htmls in these subdirectories:")
    for nbdir in nb_dir_list:
        print("   ",nbdir)

    ans = input("Ok? ")
    if ans.lower() not in ['y','yes']:
        print("Aborting.")
        sys.exit()
    
    fname_output = 'make_nb_output.txt'
    fout = open(fname_output, 'w')
    fout.write("ALL OUTPUT FROM RUNNING NOTEBOOKS\n\n")

    fname_errors = 'make_nb_errors.txt'
    ferr = open(fname_errors, 'w')
    ferr.write("ALL ERRORS FROM RUNNING NOTEBOOKS\n\n")

    os.chdir(examples_dir)

    goodlist_run = []
    badlist_run = []
    
    import subprocess
    for directory in nb_dir_list:

        fout.write("\n=============================================\n")
        fout.write(directory)
        fout.write("\n=============================================\n")
        ferr.write("\n=============================================\n")
        ferr.write(directory)
        ferr.write("\n=============================================\n")

        os.chdir(directory)

        # flush I/O buffers:
        fout.flush()
        ferr.flush()

        if make_clean_first:
            # Run 'make clean':
            job = subprocess.Popen(['make','clean'], \
                      stdout=fout,stderr=ferr)
            return_code = job.wait()
                
        # Run 'make notebook_htmls':
        job = subprocess.Popen(['make','notebook_htmls'], \
                  stdout=fout,stderr=ferr,env=my_env)
        return_code = job.wait()
                
        if return_code == 0:
            print("Successful run\n")
            goodlist_run.append(directory)
        else:
            print("*** Run errors encountered: see %s\n" % fname_errors)
            badlist_run.append(directory)

        job = subprocess.Popen(['make','README.html'], \
                  stdout=fout,stderr=ferr,env=my_env)
        return_code = job.wait()
        
        if return_code != 0:
            print("*** problems making README.html in %s" % directory)

    print('------------------------------------------------------------- ')
    print(' ')
    print('Ran "make notebook_htmls" in directories:')
    if len(goodlist_run) == 0:
        print('   None')
    else:
        for d in goodlist_run:
            print('   ',d)
    print(' ')
    
    print('Errors encountered in the following directories:')
    if len(badlist_run) == 0:
        print('   None')
    else:
        for d in badlist_run:
            print('   ',d)
    print(' ')
    
    fout.close()
    ferr.close()
    print('For all output see ', fname_output)
    print('For all errors see ', fname_errors)

    os.chdir(current_dir)

if __name__=='__main__':
    import sys
    make_all(*sys.argv[1:])
