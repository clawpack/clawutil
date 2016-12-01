"""
Conversion module for 2d classic, amrclaw, or geoclaw setrun.py file 
from 4.6 to 5.0 format.
"""
    
from __future__ import absolute_import
from __future__ import print_function
import os,sys
from permute import permute_file

try:
    clawutil = os.path.join(os.environ['CLAW'], 'clawutil/src/python/clawutil')
except:
    raise Exception("*** Environment variable CLAW must be set")


sys.path.insert(0,os.getcwd())
sys.path.append(os.getcwd() + '/pyclaw')

def convert_setrun(setrun_file='setrun.py', claw_pkg=None, ndim=None):

    setrun_text = open(setrun_file).readlines()
    if claw_pkg is None:
        for line in setrun_text:
            if 'claw_pkg' in line:
                if 'classic' in line:
                    claw_pkg = 'classic'
                elif 'amrclaw' in line:
                    claw_pkg = 'amrclaw'
                elif 'geoclaw' in line:
                    claw_pkg = 'geoclaw'

    if ndim is None:
        for line in setrun_text:
            if 'ndim' in line:
                if '1' in line: ndim = 1
                elif '2' in line: ndim = 2
                elif '3' in line: ndim = 3

    if claw_pkg is None:
        raise ValueError("*** Could not determine claw_pkg from %s" \
                                % setrun_file)
    else:
        print("claw_pkg = ",claw_pkg)
        
    if ndim is None:
        raise ValueError("*** Could not determine ndim from %s" \
                                % setrun_file)
    else:
        print("ndim = ",ndim)
        

    setrun_module = os.path.splitext(setrun_file)[0]
    exec('from %s import setrun' % setrun_module)

    rundata = setrun()
    c = rundata.clawdata

    limiter_map = {0:'none',1:'minmod',2:'superbee',3:'vanleer',4:'mc'}
    limiter = [limiter_map.get(i,i) for i in c.mthlim]


    bc_map = {0:'user', 1:'extrap', 2:'periodic', 3:'wall'}
    bc_list = ['xlower','xupper']
    if ndim >= 2: bc_list = bc_list + ['ylower','yupper']
    if ndim == 3: bc_list = bc_list + ['zlower','zupper']
    for b in bc_list:
        exec("s = bc_map.get(c.mthbc_%s, c.mthbc_%s)" % (b,b))
        if type(s) is str: 
            exec("""mthbc_%s = "'%s'" """ % (b,s))
        else:
            exec("mthbc_%s = '%s'" % (b,s))
            
    try:
        gauges = c.gauges
    except:
        try:
            gauges = rundata.geodata.gauges
        except:
            gauges = []

    # AMRClaw didn't have regions before, only geoclaw...
    try:
        regions = rundata.geodata.regions
    except:
        regions = []


    # -------------------------------------------------
    # Mapping from old setrun variables to new ones:

    # all packages and dimensions have these parameters:

    mapping = {
        'xlower': c.xlower,
        'xupper': c.xupper,
        'mx': c.mx,
        'num_eqn': c.meqn,
        'num_aux': c.maux,
        'capa_index': c.mcapa,
        't0': c.t0,
        'num_output_times': c.nout,
        'tfinal': c.tfinal,
        'dt_variable': str(c.dt_variable==1),
        'dt_initial': c.dt_initial,
        'dt_max': c.dt_max,
        'cfl_desired': c.cfl_desired,
        'cfl_max': c.cfl_max,
        'steps_max': c.max_steps,
        'order': c.order,
        'transverse_waves': c.order_trans,
        'num_waves': c.mwaves,
        'limiter': str(limiter),
        'source_split': c.src_split,
        'num_ghost': c.mbc,
        'mthbc_xlower': mthbc_xlower,
        'mthbc_xupper': mthbc_xupper,
        'gauges' : gauges}

    # add more for various cases:

    if ndim >= 2:
        mapping['ylower'] = c.ylower
        mapping['yupper'] = c.yupper
        mapping['my'] = c.my
        mapping['mthbc_ylower'] = mthbc_ylower
        mapping['mthbc_yupper'] = mthbc_yupper

    if ndim == 3:
        mapping['zlower'] = c.zlower
        mapping['zupper'] = c.zupper
        mapping['mz'] = c.mz
        mapping['mthbc_zlower'] = mthbc_zlower
        mapping['mthbc_zupper'] = mthbc_zupper

    if claw_pkg in ['amrclaw', 'geoclaw']:
        mapping['amr_levels_max'] =  abs(c.mxnest)
        mapping['refinement_ratios_x'] =  str(c.inratx)
        mapping['refinement_ratios_y'] =  str(c.inraty)
        mapping['refinement_ratios_t'] =  str(c.inratt)
        mapping['aux_type'] =  str(c.auxtype)
        mapping['flag_richardson'] =  str(c.tol > 0.)
        mapping['flag_richardson_tol'] =  abs(c.tol)
        mapping['flag2refine'] =  str(c.tolsp > 0.)
        mapping['flag2refine_tol'] =  c.tolsp
        mapping['regrid_interval'] =  c.kcheck
        mapping['regrid_buffer_width'] =  c.ibuff
        mapping['clustering_cutoff'] =  c.cutoff
        mapping['regions'] =  regions

    if claw_pkg == 'geoclaw':
        try:
            g = rundata.geodata
        except:
            raise ValueError("*** rundata has no geodata attribute")
        mapping['gravity'] =  g.gravity
        mapping['coordinate_system'] =  g.icoordsys
        mapping['earth_radius'] =  g.Rearth
        mapping['coriolis_forcing'] =  (g.icoriolis == 1)
        mapping['sea_level'] =  g.sealevel
        mapping['dry_tolerance'] =  g.drytolerance
        mapping['friction_forcing'] =  (g.ifriction == 1)
        mapping['manning_coefficient'] =  g.coeffmanning
        mapping['friction_depth'] =  g.frictiondepth
        mapping['variable_dt_refinement_ratios'] = g.variable_dt_refinement_ratios
        mapping['wave_tolerance'] =  g.wavetolerance
        mapping['deep_depth'] =  g.depthdeep
        mapping['max_level_deep'] =  g.maxleveldeep
        mapping['topofiles'] =  g.topofiles
        mapping['dtopofiles'] =  g.dtopofiles
        mapping['qinit_type'] =  g.iqinit
        mapping['qinitfiles'] =  g.qinitfiles
        mapping['fixedgrids'] =  g.fixedgrids
        mapping['fgmax_files'] =  []

    if claw_pkg == 'amrclaw' and ndim == 3:
        mapping['refinement_ratios_z'] =  str(c.inratz)

    # Use mapping to convert setrun file:

    if claw_pkg == 'classic' and ndim==1:
        template = open(clawutil \
                 + '/conversion/setrun_template_classic_1d.py').read()
        newtext = template.format(**mapping)

    elif claw_pkg == 'classic' and ndim==2:
        template = open(clawutil \
                 + '/conversion/setrun_template_classic_2d.py').read()
        newtext = template.format(**mapping)

    elif claw_pkg == 'classic' and ndim==3:
        template = open(clawutil \
                 + '/conversion/setrun_template_classic_3d.py').read()
        newtext = template.format(**mapping)

    elif claw_pkg == 'geoclaw' and ndim==2:
        template = open(clawutil \
                 + '/conversion/setrun_template_geoclaw_2d_shallow.py').read()
        newtext = template.format(**mapping)

    elif claw_pkg == 'amrclaw' and ndim==2:
        template = open(clawutil \
                 + '/conversion/setrun_template_amrclaw_2d.py').read()
        newtext = template.format(**mapping)

    else:
        raise ValueError("*** convert not yet implemented " + \
                    "for claw_pkg = %s, ndim = %s" \
                    % (claw_pkg, ndim))

    setrun_text = open(setrun_file).readlines()
    for line in setrun_text:
        if "new_UserData" in line:
            if line.strip()[0] != '#':
                print("*** Warning: call to new_UserData detected...")
                print(line)
                print("*** User data lines from %s have NOT been copied "\
                        % setrun_file)


    os.system("mv %s %s_4.x" % (setrun_file,setrun_file))
    print('Moved %s to %s_4.x ' % (setrun_file,setrun_file))
    open(setrun_file,'w').write(newtext)
    print('===> Created ', setrun_file)
    return claw_pkg, ndim


def copy_Makefile(claw_pkg, ndim):
    if claw_pkg == 'classic' and ndim==1:
        try:
            os.system("mv Makefile Makefile_4.x")
            os.system("cp %s/conversion/Makefile_classic_1d Makefile" \
                    % clawutil)
        except:
            raise Exception("*** Error copying Makefile")
    elif claw_pkg == 'classic' and ndim==2:
        try:
            os.system("mv Makefile Makefile_4.x")
            os.system("cp %s/conversion/Makefile_classic_2d Makefile" \
                    % clawutil)
        except:
            raise Exception("*** Error copying Makefile")
    elif claw_pkg == 'classic' and ndim==3:
        try:
            os.system("mv Makefile Makefile_4.x")
            os.system("cp %s/conversion/Makefile_classic_3d Makefile" \
                    % clawutil)
        except:
            raise Exception("*** Error copying Makefile")
    elif claw_pkg == 'amrclaw' and ndim==2:
        try:
            os.system("mv Makefile Makefile_4.x")
            os.system("cp %s/conversion/Makefile_amrclaw_2d Makefile" \
                    % clawutil)
        except:
            raise Exception("*** Error copying Makefile")
    elif claw_pkg == 'geoclaw' and ndim==2:
        try:
            os.system("mv Makefile Makefile_4.x")
            os.system("cp %s/conversion/Makefile_geoclaw_2d_shallow Makefile" \
                    % clawutil)
        except:
            raise Exception("*** Error copying Makefile")
    else:
        raise ValueError("*** copy_Makefile not yet implemented " + \
                    "for claw_pkg = %s, ndim = %s" \
                    % (claw_pkg, ndim))

    print("Moved Makefile to Makefile_4.x")
    print("===> Created new Makefile template -- must be customized!")
    print("*** Edit Makefile based on Makefile_4.x, e.g. point to")
    print("*** any local files, correct Riemann solver, etc.\n")
    print("*** You might have to make other modifications to local fortran files")


def convert_setplot(setplot_file='setplot.py'):

    setplot_text = open(setplot_file).read()
    setplot_text = setplot_text.replace('pyclaw.plotters','clawpack.visclaw')
    setplot_text = setplot_text.replace('2d_grid','2d_patch')
    setplot_text = setplot_text.replace('gridedges','patchedges')
    setplot_text = setplot_text.replace('gridlines','celledges')
    setplot_text = setplot_text.replace('grid_bgcolor','patch_bgcolor')

    os.system("mv %s %s_4.x" % (setplot_file,setplot_file))
    print('Moved %s to %s_4.x ' % (setplot_file,setplot_file))
    open(setplot_file,'w').write(setplot_text)
    print('===> Created ', setplot_file)

def fix_fortran(claw_pkg, ndim):
    
    import glob
    if claw_pkg=='classic':
        os.system("mv driver.f driver.f_4.x")
        print("Moved driver.f to driver.f_4.x (no longer needed)")

    ffiles = glob.glob('*.f*')

    # Order to permute indices:
    if ndim==1:
        plist = [('q',     [2,1]), ('aux',   [2,1])]
    elif ndim==2:
        plist = [('q',     [3,1,2]), ('aux',   [3,1,2])]
    elif ndim==3:
        plist = [('q',     [4,1,2,3]), ('aux',   [4,1,2,3])]

    for f in ffiles:
        if f[:1] == 'rp':
            print("*** not reordering Riemann solver ",f)
            print("*** switch to library routine from $CLAW/riemann if possible")
        else:
            f4x = f + "_4.x"
            os.system("mv %s %s" % (f,f4x))
            permute_file(f4x, f, plist, write_header=False)
            print("===> Tried to reorder indices in ",f)
            print("Moved original to ",f4x)
    

if __name__ == "__main__":
    claw_pkg, ndim = convert_setrun()
    copy_Makefile(claw_pkg, ndim)
    convert_setplot()

    fix_fortran(claw_pkg, ndim)

    print("*** WARNING -- this only did a first pass at conversion")
    print("*** WARNING -- see hints above for what else needs to be done")
    print("*** WARNING -- and check all files for correctness")
