
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
    #fname = os.path.abspath(fname)
    os.system("date >> %s" % fname)

    claw_repositories = \
        ['classic','amrclaw','clawutil','visclaw','riemann','geoclaw']

    os.chdir(topdir)

    for repos in claw_repositories:
        
        f = open(fname,'a')
        f.write("\n\n===========\n%s\n===========\n" % repos)
        f.close()

        try:
            os.chdir(repos)
            os.system('pwd >> %s' % fname)
            if 0:
                f = open(fname,'a')
                f.write("\n--- branches ---\n")
                f.close()
                os.system('git branch >> %s' % fname)
            f = open(fname,'a')
            f.write("\n--- last commit ---\n")
            f.close()
            os.system('git log -1 --oneline >> %s' % fname)
            f = open(fname,'a')
            f.write("\n--- branch and status ---\n")
            f.close()
            os.system('git status -b -s --untracked-files=no >> %s' % fname)
        except:
            f = open(fname,'a')
            f.write("*** git repository not found ***")
            f.close()
        os.chdir(topdir)

if __name__=="__main__":
    import sys
    make_git_status_file(*sys.argv[1:])
