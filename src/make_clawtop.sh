
# Go into top level of clawpack (above amrclaw, clawutil, etc)
#   source clawutil/src/make_clawtop.sh

CLAWTOP=python
GITDIR=`pwd`
mkdir -p $CLAWTOP/clawpack
cd $CLAWTOP/clawpack
echo " " > __init__.py
ln -sf $GITDIR/pyclaw/src/pyclaw pyclaw
ln -sf $GITDIR/visclaw/src/python/visclaw visclaw
ln -sf $GITDIR/riemann/src/python/riemann riemann
ln -sf $GITDIR/clawutil/src/python/clawutil clawutil
ln -sf $GITDIR/amrclaw/src/python/amrclaw amrclaw
ln -sf $GITDIR/geoclaw/src/python/geoclaw geoclaw
cd $GITDIR
