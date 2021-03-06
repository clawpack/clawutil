""" 
Module to set up run time parameters for Clawpack -- classic code.

The values set in the function setrun are then written out to data files
that will be read in by the Fortran code.
    
""" 

from __future__ import absolute_import
import os
import numpy as np

#------------------------------
def setrun(claw_pkg='classic'):
#------------------------------
    
    """ 
    Define the parameters used for running Clawpack.

    INPUT:
        claw_pkg expected to be "classic" for this setrun.

    OUTPUT:
        rundata - object of class ClawRunData 
    
    """ 
    
    from clawpack.clawutil import data 
    
    
    assert claw_pkg.lower() == 'classic',  "Expected claw_pkg = 'classic'"

    num_dim = 3
    rundata = data.ClawRunData(claw_pkg, num_dim)

    #------------------------------------------------------------------
    # Problem-specific parameters to be written to setprob.data:
    #------------------------------------------------------------------
    # Sample setup to write one line to setprob.data ...
    #probdata = rundata.new_UserData(name='probdata',fname='setprob.data')
    #probdata.add_param('u',     0.5,  'ubar advection velocity')
    
    #------------------------------------------------------------------
    # Standard Clawpack parameters to be written to claw.data:
    #------------------------------------------------------------------

    clawdata = rundata.clawdata  # initialized when rundata instantiated


    # ---------------
    # Spatial domain:
    # ---------------

    # Number of space dimensions:
    clawdata.num_dim = num_dim
    
    # Lower and upper edge of computational domain:
    clawdata.lower[0] = {xlower:e}          # xlower
    clawdata.upper[0] = {xupper:e}          # xupper
    clawdata.lower[1] = {ylower:e}          # ylower
    clawdata.upper[1] = {yupper:e}          # yupper
    clawdata.lower[2] = {zlower:e}          # zlower
    clawdata.upper[2] = {zupper:e}          # zupper
    
    # Number of grid cells:
    clawdata.num_cells[0] = {mx:d}      # mx
    clawdata.num_cells[1] = {my:d}      # my
    clawdata.num_cells[2] = {mz:d}      # mz
    

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

    clawdata.t0 = {t0:f}
    

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
        clawdata.tfinal = {tfinal:f}
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
    # if dt_variable==False: fixed time steps dt = dt_initial always used.
    clawdata.dt_variable = {dt_variable:s}
    
    # Initial time step for variable dt.  
    # (If dt_variable==0 then dt=dt_initial for all steps)
    clawdata.dt_initial = {dt_initial:e}
    
    # Max time step to be allowed if variable dt used:
    clawdata.dt_max = {dt_max:e}
    
    # Desired Courant number if variable dt used 
    clawdata.cfl_desired = {cfl_desired:f}
    # max Courant number to allow without retaking step with a smaller dt:
    clawdata.cfl_max = {cfl_max:f}
    
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
    #  0 ==> donor cell (only normal solver used)
    #  10 ==> transverse terms
    #  11 ==> double transverse terms too
    #  22 ==> 2nd order corrections too
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
    clawdata.limiter = {limiter:s}
    
    clawdata.use_fwaves = False    # True ==> use f-wave version of algorithms
    
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
    
    clawdata.bc_lower[0] = {mthbc_xlower:s}   # at xlower
    clawdata.bc_upper[0] = {mthbc_xupper:s}   # at xupper

    clawdata.bc_lower[1] = {mthbc_ylower:s}   # at ylower
    clawdata.bc_upper[1] = {mthbc_yupper:s}   # at yupper
                  
    clawdata.bc_lower[2] = {mthbc_ylower:s}   # at zlower
    clawdata.bc_upper[2] = {mthbc_yupper:s}   # at zupper
                  
    return rundata

    # end of function setrun
    # ----------------------


if __name__ == '__main__':
    # Set up run-time parameters and write all data files.
    import sys
    rundata = setrun(*sys.argv[1:])
    rundata.write()
    
