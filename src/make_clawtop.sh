
# Go into top level of clawpack (above amrclaw, clawutil, etc)
#   source clawutil/src/make_clawtop.sh

CLAWTOP=python
GITDIR=`pwd`
mkdir -p $CLAWTOP/clawpack
cd $CLAWTOP/clawpack
echo " " > __init__.py
ln -s $GITDIR/pyclaw/src/pyclaw pyclaw
ln -s $GITDIR/visclaw/src/python/visclaw visclaw
ln -s $GITDIR/riemann/src/python/riemann riemann
ln -s $GITDIR/clawutil/src/python/clawutil clawutil
ln -s $GITDIR/amrclaw/src/python/amrclaw amrclaw
ln -s $GITDIR/geoclaw/src/python/geoclaw geoclaw
cd $GITDIR

echo Created python/clawpack directory with symbolic links to python dirctories
echo Modify your PYTHONPATH to include $CLAW/python 
echo        so you can import clawpack modules
