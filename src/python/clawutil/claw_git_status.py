
import os,sys, time


def make_git_status_file(outdir='.'):

    try:
        CLAW = os.environ['CLAW']
    except:
        raise Exception("*** CLAW environment variable not set ***")

    topdir = CLAW

    outdir = os.path.abspath(outdir)
    fname = outdir + '/claw_git_status.txt' 
    print "Will save to ",fname

    f = open(fname,'w')
    f.write("Clawpack Git Status \n\n")
    f.close()

    def fwrite(s):
        f = open(fname,'a')
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
        ['classic','amrclaw','clawutil','visclaw','riemann','geoclaw']

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
        except:
            fwrite("*** git repository not found ***")
        os.chdir(topdir)

if __name__=="__main__":
    import sys
    make_git_status_file(*sys.argv[1:])
