"""
Conversion module for 2d amrclaw setrun.py file from 4.6 to 5.0 format.
"""
    

import os,sys

clawutil = os.environ['CLAWUTIL'] + '/src/python/clawutil'
template = open(clawutil + '/conversion/setrun_template_amrclaw_2d.py').read()

sys.path.insert(0,os.getcwd())

def convert(setrun_file='setrun.py'):

    setrun_module = os.path.splitext(setrun_file)[0]
    exec('from %s import setrun' % setrun_module)

    rundata = setrun()
    c = rundata.clawdata

    limiter_map = {0:'none',1:'minmod',2:'superbee',3:'mc',4:'vanleer'}
    limiter = [limiter_map.get(i,i) for i in c.mthlim]
    print "limiter: ", c.mthlim, limiter


    bc_map = {0:'user', 1:'extrap', 2:'periodic', 3:'wall'}
    for b in ['xlower','xupper','ylower','yupper']:
        exec("s = bc_map.get(c.mthbc_%s, c.mthbc_%s)" % (b,b))
        if type(s) is str: 
            exec("""mthbc_%s = "'%s'" """ % (b,s))
        else:
            exec("mthbc_%s = '%s'" % (b,s))
            

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
        }

    newtext = template.format(**mapping)
    new_setrun_file = 'new_' + setrun_file

    setrun_text = open(setrun_file).readlines()
    for line in setrun_text:
        if "new_UserData" in line:
            if line.strip()[0] != '#':
                print "*** Warning: call to new_UserData detected..."
                print line
                print "*** User data lines from %s have NOT been copied to %s"\
                        % (setrun_file, new_setrun_file)


    open(new_setrun_file,'w').write(newtext)
    print 'Created ', new_setrun_file

if __name__ == "__main__":
    convert(*sys.argv[1:])
