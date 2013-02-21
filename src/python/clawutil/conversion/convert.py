"""
Conversion module for 2d amrclaw setrun.py file from 4.6 to 5.0 format.
"""
    

import os,sys

clawutil = os.environ['CLAWUTIL'] + '/src/python/clawutil'
template_amrclaw_2d = open(clawutil \
             + '/conversion/setrun_template_amrclaw_2d.py').read()

sys.path.insert(0,os.getcwd())
sys.path.append(os.getcwd() + '/pyclaw')

def convert_setrun(setrun_file='setrun.py', claw_pkg=None):

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

    if claw_pkg is None:
        raise ValueError("*** Could not determine claw_pkg from %s" \
                                % setrun_file)
        

    setrun_module = os.path.splitext(setrun_file)[0]
    exec('from %s import setrun' % setrun_module)

    rundata = setrun()
    c = rundata.clawdata

    limiter_map = {0:'none',1:'minmod',2:'superbee',3:'mc',4:'vanleer'}
    limiter = [limiter_map.get(i,i) for i in c.mthlim]


    bc_map = {0:'user', 1:'extrap', 2:'periodic', 3:'wall'}
    for b in ['xlower','xupper','ylower','yupper']:
        exec("s = bc_map.get(c.mthbc_%s, c.mthbc_%s)" % (b,b))
        if type(s) is str: 
            exec("""mthbc_%s = "'%s'" """ % (b,s))
        else:
            exec("mthbc_%s = '%s'" % (b,s))
            
    try:
        gauges = c.gauges
    except:
        gauges = []

    try:
        regions = c.regions
    except:
        regions = []


    # -------------------------------------------------
    # Mapping from old setrun variables to new ones:

    mapping = {
        'xlower': c.xlower,
        'xupper': c.xupper,
        'ylower': c.ylower,
        'yupper': c.yupper,
        'mx': c.mx,
        'my': c.my,
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
        'mthbc_ylower': mthbc_ylower,
        'mthbc_yupper': mthbc_yupper,
        'amr_levels_max': abs(c.mxnest),
        'refinement_ratios_x': str(c.inratx),
        'refinement_ratios_y': str(c.inraty),
        'refinement_ratios_t': str(c.inratt),
        'aux_type': str(c.auxtype),
        'flag_richardson': str(c.tol > 0.),
        'flag_richardson_tol': abs(c.tol),
        'flag2refine': str(c.tolsp > 0.),
        'flag2refine_tol': c.tolsp,
        'regrid_interval': c.kcheck,
        'regrid_buffer_width': c.ibuff,
        'clustering_cutoff': c.cutoff,
        'gauges': gauges,
        'regions': regions,
        }

    if claw_pkg == 'amrclaw':
        newtext = template_amrclaw_2d.format(**mapping)
    else:
        raise ValueError("*** convert not yet implemented for claw_pkg = %s" \
                    % claw_pkg)

    setrun_text = open(setrun_file).readlines()
    for line in setrun_text:
        if "new_UserData" in line:
            if line.strip()[0] != '#':
                print "*** Warning: call to new_UserData detected..."
                print line
                print "*** User data lines from %s have NOT been copied "\
                        % setrun_file


    os.system("mv %s original_%s" % (setrun_file,setrun_file))
    print 'Moved %s to original_%s ' % (setrun_file,setrun_file)
    open(setrun_file,'w').write(newtext)
    print 'Created ', setrun_file
    return claw_pkg


def copy_Makefile(claw_pkg):
    if claw_pkg == 'amrclaw':
        try:
            os.system("mv Makefile original_Makefile")
            os.system("cp %s/conversion/Makefile_amrclaw_2d Makefile" \
                    % clawutil)
        except:
            raise Exception("*** Error copying Makefile")
    else:
        raise ValueError("*** convert not yet implemented for claw_pkg = %s" \
                    % claw_pkg)

    print "Moved Makefile to original_Makefile"
    print "Created new Makefile template -- must be customized!"
    print "*** Edit Makefile based on original_Makefile, e.g. point to"
    print "*** any local files, correct Riemann solver, etc."
    print "*** You might have to make other modifications to local fortran"
    print "*** files -- in particular indices have been reordered!"


def convert_setplot(setplot_file='setplot.py'):

    setplot_text = open(setplot_file).read()
    setplot_text = setplot_text.replace('pyclaw.plotters','clawpack.visclaw')
    setplot_text = setplot_text.replace('2d_grid','2d_patch')
    setplot_text = setplot_text.replace('gridedges','patchedges')
    setplot_text = setplot_text.replace('gridlines','celledges')

    os.system("mv %s original_%s" % (setplot_file,setplot_file))
    print 'Moved %s to original_%s ' % (setplot_file,setplot_file)
    open(setplot_file,'w').write(setplot_text)
    print 'Created ', setplot_file


if __name__ == "__main__":
    claw_pkg = convert_setrun()
    copy_Makefile(claw_pkg)
    convert_setplot()
