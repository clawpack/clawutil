""" 
Module to set up run time parameters for Clawpack -- AMRClaw code.

The values set in the function setrun are then written out to data files
that will be read in by the Fortran code.
    
""" 

from __future__ import absolute_import
from __future__ import print_function
import os
import numpy as np

#------------------------------
def setrun(claw_pkg='geoclaw'):
#------------------------------
    
    """ 
    Define the parameters used for running Clawpack.

    INPUT:
        claw_pkg expected to be "geoclaw" for this setrun.

    OUTPUT:
        rundata - object of class ClawRunData 
    
    """ 
    
    from clawpack.clawutil import data 
    
    
    assert claw_pkg.lower() == 'geoclaw',  "Expected claw_pkg = 'geoclaw'"

    num_dim = 2
    rundata = data.ClawRunData(claw_pkg, num_dim)

    #------------------------------------------------------------------
    # Problem-specific parameters to be written to setprob.data:
    #------------------------------------------------------------------
    #probdata = rundata.new_UserData(name='probdata',fname='setprob.data')


    #------------------------------------------------------------------
    # GeoClaw specific parameters:
    #------------------------------------------------------------------
    rundata = setgeo(rundata)
    
    #------------------------------------------------------------------
    # Standard Clawpack parameters to be written to claw.data:
    #------------------------------------------------------------------

    clawdata = rundata.clawdata  # initialized when rundata instantiated


    # Set single grid parameters first.
    # See below for AMR parameters.


    # ---------------
    # Spatial domain:
    # ---------------

    # Number of space dimensions:
    clawdata.num_dim = num_dim
    
    # Lower and upper edge of computational domain:
    clawdata.lower[0] = {xlower}          # xlower
    clawdata.upper[0] = {xupper}          # xupper
    clawdata.lower[1] = {ylower}          # ylower
    clawdata.upper[1] = {yupper}          # yupper
    
    # Number of grid cells:
    clawdata.num_cells[0] = {mx:d}      # mx
    clawdata.num_cells[1] = {my:d}      # my
    

    # ---------------
    # Size of system:
    # ---------------

    # Number of equations in the system:
    clawdata.num_eqn = {num_eqn:d}

    # Number of auxiliary variables in the aux array (initialized in setaux)
    clawdata.num_aux = {num_aux:d}
    
    # Index of aux array corresponding to capacity function, if there is one:
    clawdata.capa_index = {capa_index:d}
    
    
    # -------------
    # Initial time:
    # -------------

    clawdata.t0 = {t0}
    

    # Restart from checkpoint file of a previous run?
    # Note: If restarting, you must also change the Makefile to set:
    #    RESTART = True
    # If restarting, t0 above should be from original run, and the
    # restart_file 'fort.chkNNNNN' specified below should be in 
    # the OUTDIR indicated in Makefile.

    clawdata.restart = False               # True to restart from prior results
    clawdata.restart_file = 'fort.chk00006'  # File to use for restart data
    
    
    # -------------
    # Output times:
    #--------------

    # Specify at what times the results should be written to fort.q files.
    # Note that the time integration stops after the final output time.
 
    clawdata.output_style = 1
 
    if clawdata.output_style==1:
        # Output ntimes frames at equally spaced times up to tfinal:
        # Can specify num_output_times = 0 for no output
        clawdata.num_output_times = {num_output_times:d}
        clawdata.tfinal = {tfinal}
        clawdata.output_t0 = True  # output at initial (or restart) time?
        
    elif clawdata.output_style == 2:
        # Specify a list or numpy array of output times:
        # Include t0 if you want output at the initial time.
        clawdata.output_times =  [0., 0.1]
 
    elif clawdata.output_style == 3:
        # Output every step_interval timesteps over total_steps timesteps:
        clawdata.output_step_interval = 2
        clawdata.total_steps = 4
        clawdata.output_t0 = True  # output at initial (or restart) time?
        

    clawdata.output_format = 'ascii'      # 'ascii', 'binary', 'netcdf'

    clawdata.output_q_components = 'all'   # could be list such as [True,True]
    clawdata.output_aux_components = 'none'  # could be list
    clawdata.output_aux_onlyonce = True    # output aux arrays only at t0
    

    # ---------------------------------------------------
    # Verbosity of messages to screen during integration:  
    # ---------------------------------------------------

    # The current t, dt, and cfl will be printed every time step
    # at AMR levels <= verbosity.  Set verbosity = 0 for no printing.
    #   (E.g. verbosity == 2 means print only on levels 1 and 2.)
    clawdata.verbosity = 0
    
    

    # --------------
    # Time stepping:
    # --------------

    # if dt_variable==True:  variable time steps used based on cfl_desired,
    # if dt_variable==Falseixed time steps dt = dt_initial always used.
    clawdata.dt_variable = {dt_variable}
    
    # Initial time step for variable dt.  
    # (If dt_variable==0 then dt=dt_initial for all steps)
    clawdata.dt_initial = {dt_initial}
    
    # Max time step to be allowed if variable dt used:
    clawdata.dt_max = {dt_max}
    
    # Desired Courant number if variable dt used 
    clawdata.cfl_desired = {cfl_desired}
    # max Courant number to allow without retaking step with a smaller dt:
    clawdata.cfl_max = {cfl_max}
    
    # Maximum number of time steps to allow between output times:
    clawdata.steps_max = {steps_max:d}


    # ------------------
    # Method to be used:
    # ------------------

    # Order of accuracy:  1 => Godunov,  2 => Lax-Wendroff plus limiters
    clawdata.order = {order:d}
    
    # Use dimensional splitting? (not yet available for AMR)
    clawdata.dimensional_split = 'unsplit'
    
    # For unsplit method, transverse_waves can be 
    #  0 or 'none'      ==> donor cell (only normal solver used)
    #  1 or 'increment' ==> corner transport of waves
    #  2 or 'all'       ==> corner transport of 2nd order corrections too
    clawdata.transverse_waves = {transverse_waves:d}
    
    
    # Number of waves in the Riemann solution:
    clawdata.num_waves = {num_waves:d}
    
    # List of limiters to use for each wave family:  
    # Required:  len(limiter) == num_waves
    # Some options:
    #   0 or 'none'     ==> no limiter (Lax-Wendroff)
    #   1 or 'minmod'   ==> minmod
    #   2 or 'superbee' ==> superbee
    #   3 or 'vanleer'  ==> van Leer
    #   4 or 'mc'       ==> MC limiter
    clawdata.limiter = {limiter}
    
    clawdata.use_fwaves = True    # True ==> use f-wave version of algorithms
    
    # Source terms splitting:
    #   src_split == 0 or 'none'    ==> no source term (src routine never called)
    #   src_split == 1 or 'godunov' ==> Godunov (1st order) splitting used, 
    #   src_split == 2 or 'strang'  ==> Strang (2nd order) splitting used,  not recommended.
    clawdata.source_split = {source_split:d}
    
    
    # --------------------
    # Boundary conditions:
    # --------------------

    # Number of ghost cells (usually 2)
    clawdata.num_ghost = {num_ghost:d}
    
    # Choice of BCs at xlower and xupper:
    #   0 or 'user'     => user specified (must modify bcNamr.f to use this option)
    #   1 or 'extrap'   => extrapolation (non-reflecting outflow)
    #   2 or 'periodic' => periodic (must specify this at both boundaries)
    #   3 or 'wall'     => solid wall for systems where q(2) is normal velocity
    
    clawdata.bc_lower[0] = {mthbc_xlower}   # at xlower
    clawdata.bc_upper[0] = {mthbc_xupper}   # at xupper

    clawdata.bc_lower[1] = {mthbc_ylower}   # at ylower
    clawdata.bc_upper[1] = {mthbc_yupper}   # at yupper
                  
       
    # ---------------
    # Gauges:
    # ---------------
    rundata.gaugedata.gauges = {gauges}
    # for gauges append lines of the form  [gaugeno, x, y, t1, t2]

                  
    # --------------
    # Checkpointing:
    # --------------

    # Specify when checkpoint files should be created that can be
    # used to restart a computation.

    clawdata.checkpt_style = 0

    if clawdata.checkpt_style == 0:
      # Do not checkpoint at all
      pass

    elif clawdata.checkpt_style == 1:
      # Checkpoint only at tfinal.
      pass

    elif clawdata.checkpt_style == 2:
      # Specify a list of checkpoint times.  
      clawdata.checkpt_times = [0.1,0.15]

    elif clawdata.checkpt_style == 3:
      # Checkpoint every checkpt_interval timesteps (on Level 1)
      # and at the final time.
      clawdata.checkpt_interval = 5

    

    # ---------------
    # AMR parameters:   (written to amr.data)
    # ---------------
    amrdata = rundata.amrdata

    # max number of refinement levels:
    amrdata.amr_levels_max = {amr_levels_max:d}

    # List of refinement ratios at each level (length at least amr_level_max-1)
    amrdata.refinement_ratios_x = {refinement_ratios_x}
    amrdata.refinement_ratios_y = {refinement_ratios_y}
    amrdata.refinement_ratios_t = {refinement_ratios_t}


    # Specify type of each aux variable in amrdata.auxtype.
    # This must be a list of length num_aux, each element of which is one of:
    #   'center',  'capacity', 'xleft', or 'yleft'  (see documentation).
    amrdata.aux_type = {aux_type}


    # Flag for refinement based on Richardson error estimater:
    amrdata.flag_richardson = {flag_richardson}    # use Richardson?
    amrdata.flag_richardson_tol = {flag_richardson_tol}  # Richardson tolerance
    
    # Flag for refinement using routine flag2refine:
    amrdata.flag2refine = {flag2refine}      # use this?
    amrdata.flag2refine_tol = {flag2refine_tol}  # tolerance used in this routine
    # Note: in geoclaw the refinement tolerance is set as wave_tolerance below 
    # and flag2refine_tol is unused!

    # steps to take on each level L between regriddings of level L+1:
    amrdata.regrid_interval = {regrid_interval:d}       

    # width of buffer zone around flagged points:
    # (typically the same as regrid_interval so waves don't escape):
    amrdata.regrid_buffer_width  = {regrid_buffer_width:d}

    # clustering alg. cutoff for (# flagged pts) / (total # of cells refined)
    # (closer to 1.0 => more small grids may be needed to cover flagged cells)
    amrdata.clustering_cutoff = {clustering_cutoff}

    # print info about each regridding up to this level:
    amrdata.verbosity_regrid = 0      


    # ---------------
    # Regions:
    # ---------------
    rundata.regiondata.regions = {regions}
    # to specify regions of refinement append lines of the form
    #  [minlevel,maxlevel,t1,t2,x1,x2,y1,y2]


    #  ----- For developers ----- 
    # Toggle debugging print statements:
    amrdata.dprint = False      # print domain flags
    amrdata.eprint = False      # print err est flags
    amrdata.edebug = False      # even more err est flags
    amrdata.gprint = False      # grid bisection/clustering
    amrdata.nprint = False      # proper nesting output
    amrdata.pprint = False      # proj. of tagged points
    amrdata.rprint = False      # print regridding summary
    amrdata.sprint = False      # space/memory output
    amrdata.tprint = False      # time step reporting each level
    amrdata.uprint = False      # update/upbnd reporting
    
    return rundata

    # end of function setrun
    # ----------------------


#-------------------
def setgeo(rundata):
#-------------------
    """
    Set GeoClaw specific runtime parameters.
    """

    try:
        geo_data = rundata.geo_data
    except:
        print("*** Error, this rundata has no geo_data attribute")
        raise AttributeError("Missing geo_data attribute")

    # == Physics ==
    geo_data.gravity = {gravity}
    geo_data.coordinate_system = {coordinate_system: d}
    geo_data.earth_radius = {earth_radius}

    # == Forcing Options
    geo_data.coriolis_forcing = {coriolis_forcing}

    # == Algorithm and Initial Conditions ==
    geo_data.sea_level = {sea_level}
    geo_data.dry_tolerance = {dry_tolerance}
    geo_data.friction_forcing = {friction_forcing}
    geo_data.manning_coefficient = {manning_coefficient}
    geo_data.friction_depth = {friction_depth}

    # Refinement settings
    refinement_data = rundata.refinement_data
    refinement_data.variable_dt_refinement_ratios = {variable_dt_refinement_ratios}
    refinement_data.wave_tolerance = {wave_tolerance}
    refinement_data.deep_depth = {deep_depth}
    refinement_data.max_level_deep = {max_level_deep}

    # == settopo.data values ==
    rundata.topo_data.topofiles = {topofiles}
    topofiles = rundata.topo_data.topofiles
    # for topography, append lines of the form
    #    [topotype, minlevel, maxlevel, t1, t2, fname]

    # == setdtopo.data values ==
    rundata.dtopo_data.dtopofiles = {dtopofiles}
    dtopofiles = rundata.dtopo_data.dtopofiles
    # for moving topography, append lines of the form :  
    #   [topotype, minlevel,maxlevel,fname]


    # == setqinit.data values ==
    rundata.qinit_data.qinit_type = {qinit_type: d}
    rundata.qinit_data.qinitfiles = {qinitfiles}
    qinitfiles = rundata.qinit_data.qinitfiles 
    # for qinit perturbations, append lines of the form: (<= 1 allowed for now!)
    #   [minlev, maxlev, fname]

    # == fixedgrids.data values ==
    rundata.fixed_grid_data.fixedgrids = {fixedgrids}
    fixedgrids = rundata.fixed_grid_data.fixedgrids
    # for fixed grids append lines of the form
    # [t1,t2,noutput,x1,x2,y1,y2,xpoints,ypoints,\
    #  ioutarrivaltimes,ioutsurfacemax]

    # == fgmax.data values ==
    fgmax_files = rundata.fgmax_data.fgmax_files
    # for fixed grids append to this list names of any fgmax input files


    return rundata
    # end of function setgeo
    # ----------------------

if __name__ == '__main__':
    # Set up run-time parameters and write all data files.
    import sys
    rundata = setrun(*sys.argv[1:])
    rundata.write()
    
