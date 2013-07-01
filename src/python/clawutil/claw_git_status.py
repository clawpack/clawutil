"""
Print status of all clawpack git repositories.
"""

import os,sys, time


def make_git_status_file(outdir='.'):
    """
    Print status of all clawpack git repositories.
    Creates 2 files:
         outdir + '/claw_git_status.txt'
            contains list of last commits, what branch is checked out, and
            a short version of git status.
         outdir + '/claw_git_diffs.txt'
            contains all diffs between current working state and last commits.
        
    """

    try:
        CLAW = os.environ['CLAW']
    except:
        raise Exception("*** CLAW environment variable not set ***")

    topdir = CLAW

    outdir = os.path.abspath(outdir)
    fname = outdir + '/claw_git_status.txt' 
    print "Will save to ",fname

    diff_file = 'claw_git_diffs.txt'
    f = open(fname,'w')
    f.write("Clawpack Git Status \n")
    f.write("Diffs can be found in %s\n\n" % diff_file)
    f.close()

    diff_file = os.path.join(outdir, diff_file)
    f = open(diff_file,'w')
    f.write("Clawpack git diffs...")
    f.close()


    def fwrite(s,file=fname):
        f = open(file,'a')
        f.write(s + "\n")
        f.close()

    os.system("date >> %s\n\n" % fname)
    fwrite("$CLAW = %s \n" % CLAW)
    try:
        FC = os.environ['FC']
        fwrite("$FC = %s " % FC)
        os.system("%s --version | head -1 >> %s" % (FC,fname))
    except:
        fwrite("$FC not set")

    claw_repositories = \
        ['classic','amrclaw','clawutil','pyclaw','visclaw','riemann','geoclaw']

    os.chdir(topdir)

    for repos in claw_repositories:
        
        fwrite("\n\n===========\n%s\n===========" % repos)

        try:
            os.chdir(repos)
            os.system('pwd >> %s' % fname)
            if 0:
                fwrite("\n--- branches ---")
                os.system('git branch >> %s' % fname)
            fwrite("\n--- last commit ---")
            os.system('git log -1 --oneline >> %s' % fname)
            fwrite("\n--- branch and status ---")
            os.system('git status -b -s --untracked-files=no >> %s' % fname)

            fwrite("\n\n===========\n%s\n===========" % repos, diff_file)
            os.system('git diff --no-ext-diff >> %s' % diff_file)
            os.system('git diff --cached --no-ext-diff >> %s' % diff_file)

        except:
            fwrite("*** git repository not found ***")
        os.chdir(topdir)

if __name__=="__main__":
    import sys
    make_git_status_file(*sys.argv[1:])
