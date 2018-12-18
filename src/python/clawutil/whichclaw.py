"""
Print out 
  - settings of environment variables,
  - elements of sys.path that contain "clawpack"
  - lines of site-packages/easy-install.pth files that contain "clawpack"

Useful for figuring out how paths are set and which version of clawpack is being
used when more than one has been installed.

Notes: 
  - this should be run in the users' shell (which might not be bash)
  - this script has not been extensively tested, maybe it's missing something

"""


import sys, os
import site
import inspect

try:
    import clawpack
    claw_file = inspect.getfile(clawpack)
    claw_dir = os.path.split(claw_file)[0]
    print('\n`import clawpack` imports from:\n    %s' % claw_dir[:-9])
except:
    print('\n`import clawpack` gives an import error')
    

CLAW = os.environ.get('CLAW','')
if CLAW != '':
    print("\nThe CLAW environment variable is set to: \n    %s" % CLAW)
else:
    print("\nThe CLAW environment variable is not set")

PPATH = os.environ.get('PYTHONPATH','')
if PPATH != '':
    print("The PYTHONPATH environment variable is set to: \n    %s" % PPATH)
else:
    print("The PYTHONPATH environment variable is not set")

print("\nThe following directories on sys.path might contain clawpack,")
print("and are searched in this order:")
ppath = sys.path
for p in ppath:
    if 'clawpack' in p:
        if os.path.isdir(os.path.join(p,'clawpack')):
            print('    %s' % p)
        else:
            continue

print("\nThe following easy-install.pth files list clawpack:")
for p in ppath:
    if 'site-packages' in p:
        if os.path.isfile(os.path.join(p, 'easy-install.pth')):
            fname = os.path.join(p, 'easy-install.pth')
            f = open(fname).readlines()
            for line in f:
                if 'clawpack' in line:
                    print('    %s \n        (points to %s)' \
                          % (fname,line.strip()))
        else:
            continue




