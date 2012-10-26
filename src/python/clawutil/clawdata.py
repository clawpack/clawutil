r"""
Data Module

Contains the general class definition and the subclasses of the Clawpack data
objects.

Rewritten for 5.0:
 Stripped down version of Data object, no longer keeps track of "owners".
 data classes are now subclasses of ClawData, which checks if attributes
   already exist before setting.

"""

import os
import logging

import numpy as np


# ========================
class Data(object):
# ========================
    """
    Unrestricted object, can assign to new attributes.
    """
    
    def __init__(self, attributes=None):
        
        # Initialize from attribute list provided
        if attributes:
            for attr in attributes:
                self.__setattr__(attr,None)

    def add_attribute(self, name, value=None, add_to_list=True):
        setattr(self,name,value)

# ========================
class ClawData(object):
# ========================
    r"""
    Class to be subclassed when defining data objects that should have
    a limited set of allowed attributes.  Useful to guard against
    typos or misrembering the names of expected attributes.

    Resetting values of existing attributes is allowed as usual,
    but new attributes can only be added using the method add_attribute.

    Trying to set a nonexistent attribute will raise an AttributeError
    exception, except for those starting with '_'.   
    """


    def __init__(self, attributes=None):
        
        # Attribute to store a list of the allowed attributes, 
        # appended to when add_attribute is used: 
        object.__setattr__(self,'_attributes',[])

        # Initialize from attribute list provided
        if attributes:
            for attr in attributes:
                self.add_attribute(attr,None)

    def __setattr__(self,name,value):
        r"""
        Check that attribute exists before setting it.
        If not, raise an AttributeError.
        Exception: attributes starting with '_' are ok to set.
        """

        if (not name in self._attributes) and (name[0] != '_'):
            print "*** Unrecognized attribute: ",name
            print "*** Perhaps a typo?"
            print "*** Add new attributes using add_attribute method"
            raise AttributeError("Unrecognized attribute: %s" % name)
        
        # attribute exists, ok to set:
        object.__setattr__(self,name,value)

    def add_attribute(self, name, value=None, add_to_list=True):
        r"""
        Adds an attribute called name to the data object

        If an attribute needs to be added to the object, this routine must be
        called or the attribute will not be written out.

        :Input:
         - *name* - (string) Name of the data attribute
         - *value* - (id) Value to set *name* to, defaults to None
        """
        if (name not in self._attributes) and add_to_list:
            self._attributes.append(name)
        object.__setattr__(self,name,value)

    def add_attributes(self, arg_list, value=None):
        r"""
        Add a list of attributes, each initialized to *value*.
        """
        for name in arg_list:
            self.add_attribute(name, value)

    def remove_attributes(self, arg_list):
        r"""
        Remove the listed attributes.
        """

        # Convert to list if args is not already a list
        if not isinstance(arg_list,list):
            arg_list = [arg_list]

        for arg in arg_list:
            self._attributes.remove(arg)
            delattr(self,arg)

    #def attributes():
    #    def fget(self): return self._attributes
    #    return locals()
    #attributes = property(**attributes())

    def has_attribute(self,name):
        r"""
        Check if this data object has the given attributes

        :Input:
         - *name* - (string) Name of attribute

        :Output:
         - (bool) - True if data object contains a data attribute name
        """
        return name in self._attributes
        
    def iteritems(self):
        r"""
        Returns an iterator of attributes and values from this object

        :Output:
         - (Iterator) Iterator over attributes and values
        """
        return [(k,getattr(self,k)) for k in self._attributes]



# ========== Parse Value Utility Function ====================================

def _parse_value(value):
    r"""
    Attempt to make sense of a value string from a config file.  If the
    value is not obviously an integer, float, or boolean, it is returned as
    a string stripped of leading and trailing whitespace.

    :Input:
        - *value* - (string) Value string to be parsed

    :Output:
        - (id) - Appropriate object based on *value*
    """
    value = value.strip()
    if not value:
        return None

    # assume that values containing spaces are lists of values
    if len(value.split()) > 1:
        return [_parse_value(vv) for vv in value.split()]

    try:
        # see if it's an integer
        value = int(value)
    except ValueError:
        try:
            # see if it's a float
            value = float(value)
        except ValueError:
            # see if it's a bool
            if value[0] == 'T':
                value = True
            elif value[0] == 'F':
                value = False

    return value


#-----------------------------------------------------------------------

# New classes and functions for dealing with data in setrun function.

class ClawInputData(ClawData):
    r"""
    Object that will be written out to claw.data.
    """
    def __init__(self, num_dim):
        super(ClawInputData,self).__init__()

        # Set default values:
        self.add_attribute('num_dim',num_dim)
        self.add_attribute('num_eqn',1)
        self.add_attribute('num_waves',1)
        self.add_attribute('num_aux',0)
        self.add_attribute('output_style',1)
        self.add_attribute('output_times',[])
        self.add_attribute('num_output_times',None)
        self.add_attribute('output_t0',True)
        self.add_attribute('output_step_interval',None)
        self.add_attribute('total_steps',None)
        self.add_attribute('tfinal',None)
        self.add_attribute('output_format',1)
        self.add_attribute('output_q_components','all')
        self.add_attribute('output_aux_components',[])
        self.add_attribute('output_aux_onlyonce',True)
        
        self.add_attribute('dt_initial',1.e-5)
        self.add_attribute('dt_max',1.e99)
        self.add_attribute('dt_variable',1)
        self.add_attribute('cfl_desired',0.9)
        self.add_attribute('cfl_max',1.0)
        self.add_attribute('steps_max',50000)
        self.add_attribute('order',2)
        self.add_attribute('transverse_waves',2)
        self.add_attribute('dimensional_split',0)
        self.add_attribute('verbosity',0)
        self.add_attribute('verbosity_regrid',0)
        self.add_attribute('source_split',0)
        self.add_attribute('capa_index',0)
        self.add_attribute('limiter',[4])
        self.add_attribute('t0',0.)
        self.add_attribute('num_ghost',2)
        self.add_attribute('fwave',False)
        self.add_attribute('restart',False)
        self.add_attribute('restart_file','')
        self.add_attribute('regions',[])
        self.add_attribute('gauges',[])

        if num_dim == 1:
            self.add_attribute('lower',[0.])
            self.add_attribute('upper',[1.])
            self.add_attribute('num_cells',[100])
            self.add_attribute('bc_lower',[0])
            self.add_attribute('bc_upper',[0])
        elif num_dim == 2:
            self.add_attribute('lower',[0.,0.])
            self.add_attribute('upper',[1.,1.])
            self.add_attribute('num_cells',[100,100])
            self.add_attribute('bc_lower',[0,0])
            self.add_attribute('bc_upper',[0,0])
        elif num_dim == 3:
            self.add_attribute('lower',[0.,0.,0.])
            self.add_attribute('upper',[1.,1.,1.])
            self.add_attribute('num_cells',[100,100,100])
            self.add_attribute('bc_lower',[0,0,0])
            self.add_attribute('bc_upper',[0,0,0])
        else:
            raise ValueError("Only num_dim=1, 2, or 3 supported ")

    def write(self):
        print 'Creating data file claw.data for use with xclaw'
        make_clawdatafile(self)


class AmrclawInputData(ClawInputData):
    r"""
    Object that will be written out to amrclaw.data.
    """
    def __init__(self, num_dim):

        # Set default values:
        
        # Some defaults are inherited from ClawInputData:
        super(AmrclawInputData,self).__init__(num_dim)
        
        self.add_attribute('amr_levels_max',1)
        self.add_attribute('refinement_ratios_x',[1])
        self.add_attribute('refinement_ratios_y',[1])
        if num_dim == 3:
            self.add_attribute('refinement_ratios_z',[1])
        if num_dim == 1:
            raise Exception("*** 1d AMR not yet supported")
        self.add_attribute('variable_dt_refinement_ratios',False)

        self.add_attribute('refinement_ratios_t',[1])
        self.add_attribute('aux_type',[])

        self.add_attribute('checkpt_style',1)
        self.add_attribute('checkpt_interval',1000)
        self.add_attribute('checkpt_time_interval',1000.)
        self.add_attribute('checkpt_times',[1000.])
        
        self.add_attribute('flag_richardson',False)
        self.add_attribute('flag_richardson_tol',1.0)
        self.add_attribute('flag2refine',True)
        self.add_attribute('flag2refine_tol',0.05)
        self.add_attribute('regrid_interval',2)
        self.add_attribute('regrid_buffer_width',3)
        self.add_attribute('clustering_cutoff',0.7)

        
        # debugging flags:
        self.add_attribute('dprint',False)
        self.add_attribute('eprint',False)
        self.add_attribute('edebug',False)
        self.add_attribute('gprint',False)
        self.add_attribute('nprint',False)
        self.add_attribute('pprint',False)
        self.add_attribute('rprint',False)
        self.add_attribute('sprint',False)
        self.add_attribute('tprint',False)
        self.add_attribute('uprint',False)

        
        if num_dim == 1:
            
            # attributes needed only because 1d AMR is done using 2d amrclaw:
            self.add_attribute('my',1)
            self.add_attribute('ylower',0.)
            self.add_attribute('yupper',1.)
            self.add_attribute('bc_ylower',1)
            self.add_attribute('bc_yupper',1)
            self.add_attribute('refinement_ratios_y',[1,1,1,1,1,1])


    def write(self):
        print 'Creating data file amrclaw.data for use with xamr'
        make_amrclawdatafile(self)
        make_setgauges_datafile(self)
        if len(self.regions) > 0:
            print "*** Warning: regions not yet implemented!"



def open_datafile(name, datasource='setrun.py'):
    """
    Open a data file and write a warning header.
    Warning header starts with '#' character.  These lines are skipped if
    data file is opened using the library routine opendatafile.

    :Input:
     - *name* - (string) Name of data file
     - *datasource* - (string) Source for the data

    :Output:
     - (file) - file object
    """

    import string

    source = string.ljust(datasource,25)
    file = open(name, 'w')
    file.write('########################################################\n')
    file.write('### DO NOT EDIT THIS FILE:  GENERATED AUTOMATICALLY ####\n')
    file.write('### To modify data, edit  %s ####\n' % source)
    file.write('###    and then "make .data"                        ####\n')
    file.write('########################################################\n\n')

    return file


def data_write_old(file, dataobj, name=None, descr=''):
    r"""
    Write out value to data file, in the form ::

       value =: name  descr

    Remove brackets and commas from lists, and replace booleans by T/F.

    :Input:
     - *name* - (string) normally a string defining the variable,
       ``if name==None``, write a blank line.
     - *descr* - (string) A short description to appear on the line
    """

    import string
    if name is None:
        file.write('\n')
    else:
        try:
            value = getattr(dataobj, name)
        except:
            print "Variable missing: ",name
            print "  from dataobj = ", dataobj
            raise
        # Convert value to an appropriate string repr
        if isinstance(value,tuple) | isinstance(value,list):
            # Remove [], (), and ','
            string_value = repr(value)[1:-1]
            string_value = string_value.replace(',','')
        elif isinstance(value,bool):
            if value:
                string_value = 'T'
            else:
                string_value = 'F'
        else:
            string_value = repr(value)
        padded_value = string.ljust(string_value, 25)
        padded_name = string.ljust(name, 12)
        file.write('%s =: %s %s\n' % (padded_value, padded_name, descr))

def data_write(file, value, name=None, description=''):
    r"""
    Write out value to data file, in the form ::

       value    # name  [description]

    Remove brackets and commas from lists, and replace booleans by T/F.

    :Input:
     - *name* - (string) normally a string defining the variable,
       ``if name==None``, write a blank line.
     - *description* - (string) optional description
    """

    import string
    from numpy import ndarray
    if name is None:
        file.write('\n')
    else:
        # Convert value to an appropriate string repr
        if isinstance(value,ndarray):
            value = list(value)
        if isinstance(value,tuple) | isinstance(value,list):
            # Remove [], (), and ','
            string_value = repr(value)[1:-1]
            string_value = string_value.replace(',','')
        elif isinstance(value,bool):
            if value:
                string_value = 'T'
            else:
                string_value = 'F'
        else:
            string_value = repr(value)
        padded_value = string.ljust(string_value, 40)
        #padded_name = string.ljust(name, 12)
        file.write('%s # %s  %s\n' % (padded_value, name, description))


def make_clawdatafile(clawdata):
    r"""
    Take the data specified in clawdata and write it to claw.data in the
    form required by the Fortran code classic/src/Nd/??.
    """


    # open file and write a warning header:
    file = open_datafile('claw.data')

    write_clawdata_noamr(clawdata, file)
    file.close()


def write_clawdata_noamr(clawdata, file):
    r"""
    Write out the Clawpack parameters that are used both for Classic and AMR.
    """
    
    #import pdb; pdb.set_trace()
    num_dim = clawdata.num_dim
    data_write(file, clawdata.num_dim, 'num_dim')
    data_write(file, clawdata.lower, 'lower')
    data_write(file, clawdata.upper, 'upper')
    data_write(file, clawdata.num_cells, 'num_cells')
    data_write(file, clawdata, None)  # writes blank line
    data_write(file, clawdata.num_eqn, 'num_eqn')
    data_write(file, clawdata.num_waves, 'num_waves')
    data_write(file, clawdata.num_aux, 'num_aux')
    data_write(file, clawdata, None)  # writes blank line

    data_write(file, clawdata.t0, 't0')
    data_write(file, clawdata, None)
    data_write(file, clawdata.output_style, 'output_style')

    if clawdata.output_style==1:
        data_write(file, clawdata.num_output_times, 'num_output_times')
        data_write(file, clawdata.tfinal, 'tfinal')
        data_write(file, clawdata.output_t0, 'output_t0')
    elif clawdata.output_style==2:
        if len(clawdata.output_times) == 0:
            raise AttributeError("*** output_style==2 requires nonempty list" \
                    + " of output times")
        clawdata.num_output_times = len(clawdata.output_times)
        data_write(file, clawdata.num_output_times, 'num_output_times')
        data_write(file, clawdata.output_times, 'output_times')
    elif clawdata.output_style==3:
        data_write(file, clawdata.output_step_interval, 'output_step_interval')
        data_write(file, clawdata.total_steps, 'total_steps')
        data_write(file, clawdata.output_t0, 'output_t0')
    else:
        raise AttributeError("*** Unrecognized output_style: %s"\
              % clawdata.output_style)
        

    data_write(file, clawdata, None)
    if clawdata.output_format in [1,'ascii']:
        clawdata.output_format = 1
    elif clawdata.output_format in [2,'netcdf']:
        clawdata.output_format = 2
    else:
        raise ValueError("*** Error in data parameter: " + \
              "output_format unrecognized: ",clawdata.output_format)
        
    data_write(file, clawdata.output_format, 'output_format')

    if clawdata.output_q_components == 'all':
        iout_q = clawdata.num_eqn * [1]
    elif clawdata.output_q_components == 'none':
        iout_q = clawdata.num_eqn * [0]
    else:
        iout_q = np.where(clawdata.output_q_components, 1, 0)

    data_write(file, iout_q, 'iout_q')

    if clawdata.num_aux > 0:
        if clawdata.output_aux_components == 'all':
            iout_aux = clawdata.num_aux * [1]
        elif clawdata.output_aux_components == 'none':
            iout_aux = clawdata.num_aux * [0]
        else:
            iout_aux = np.where(clawdata.output_aux_components, 1, 0)
        data_write(file, iout_aux, 'iout_aux')
        data_write(file, clawdata.output_aux_onlyonce, 'output_aux_onlyonce')

    data_write(file, clawdata, None)
    data_write(file, clawdata.dt_initial, 'dt_initial')
    data_write(file, clawdata.dt_max, 'dt_max')
    data_write(file, clawdata.cfl_max, 'cfl_max')
    data_write(file, clawdata.cfl_desired, 'cfl_desired')
    data_write(file, clawdata.steps_max, 'steps_max')
    data_write(file, clawdata, None)
    data_write(file, clawdata.dt_variable, 'dt_variable')
    data_write(file, clawdata.order, 'order')
    if num_dim == 1:
        pass
    else:
        if clawdata.transverse_waves in [0,'none']:  
            clawdata.transverse_waves = 0
        elif clawdata.transverse_waves in [1,'increment']:  
            clawdata.transverse_waves = 1
        elif clawdata.transverse_waves in [2,'all']:  
            clawdata.transverse_waves = 2
        else:
            raise AttributeError("Unrecognized transverse_waves: %s" \
                  % clawdata.transverse_waves)
        data_write(file, clawdata.transverse_waves, 'transverse_waves')

        if clawdata.dimensional_split in [0,'unsplit']:  
            clawdata.dimensional_split = 0
        elif clawdata.dimensional_split in [1,'godunov']:  
            clawdata.dimensional_split = 1
        elif clawdata.dimensional_split in [2,'strang']:  
            clawdata.dimensional_split = 2
        else:
            raise AttributeError("Unrecognized dimensional_split: %s" \
                  % clawdata.dimensional_split)
        data_write(file, clawdata.dimensional_split, 'dimensional_split')
        
    data_write(file, clawdata.verbosity, 'verbosity')

    if clawdata.source_split in [0,'none']:  
        clawdata.source_split = 0
    elif clawdata.source_split in [1,'godunov']:  
        clawdata.source_split = 1
    elif clawdata.source_split in [2,'strang']:  
        clawdata.source_split = 2
    else:
        raise AttributeError("Unrecognized source_split: %s" \
              % clawdata.source_split)
    data_write(file, clawdata.source_split, 'source_split')

    data_write(file, clawdata.capa_index, 'capa_index')
    if clawdata.num_aux > 0:
        data_write(file, clawdata.aux_type, 'aux_type')
    data_write(file, clawdata.fwave, 'fwave')
    data_write(file, clawdata, None)

    for i in range(len(clawdata.limiter)):
        if clawdata.limiter[i] in [0,'none']:        clawdata.limiter[i] = 0
        elif clawdata.limiter[i] in [1,'minmod']:    clawdata.limiter[i] = 1
        elif clawdata.limiter[i] in [2,'superbee']:  clawdata.limiter[i] = 2
        elif clawdata.limiter[i] in [3,'mc']:        clawdata.limiter[i] = 3
        elif clawdata.limiter[i] in [4,'vanleer']:   clawdata.limiter[i] = 4
        else:
            raise AttributeError("Unrecognized limiter: %s" \
                  % clawdata.limiter[i])
    data_write(file, clawdata.limiter, 'limiter')

    data_write(file, clawdata, None)


    data_write(file, clawdata.num_ghost, 'num_ghost')
    for i in range(num_dim):
        if clawdata.bc_lower[i] in [0,'user']:       clawdata.bc_lower[i] = 0
        elif clawdata.bc_lower[i] in [1,'extrap']:   clawdata.bc_lower[i] = 1
        elif clawdata.bc_lower[i] in [2,'periodic']: clawdata.bc_lower[i] = 2
        elif clawdata.bc_lower[i] in [3,'wall']:     clawdata.bc_lower[i] = 3
        else:
            raise AttributeError("Unrecognized bc_lower: %s" \
                  % clawdata.bc_lower[i])
    data_write(file, clawdata.bc_lower, 'bc_lower')

    for i in range(num_dim):
        if clawdata.bc_upper[i] in [0,'user']:       clawdata.bc_upper[i] = 0
        elif clawdata.bc_upper[i] in [1,'extrap']:   clawdata.bc_upper[i] = 1
        elif clawdata.bc_upper[i] in [2,'periodic']: clawdata.bc_upper[i] = 2
        elif clawdata.bc_upper[i] in [3,'wall']:     clawdata.bc_upper[i] = 3
        else:
            raise AttributeError("Unrecognized bc_upper: %s" \
                  % clawdata.bc_upper[i])
    data_write(file, clawdata.bc_upper, 'bc_upper')

    data_write(file, clawdata, None)
    data_write(file, clawdata.restart, 'restart')
    data_write(file, clawdata.restart_file, 'restart_file')
    data_write(file, clawdata.checkpt_style, 'checkpt_style')
    if clawdata.checkpt_style==2:
        num_checkpt_times = len(clawdata.checkpt_times)
        data_write(file, num_checkpt_times, 'num_checkpt_times')
        data_write(file, clawdata.checkpt_times, 'checkpt_times')
    elif clawdata.checkpt_style==3:
        data_write(file, clawdata.checkpt_interval, 'checkpt_interval')
    elif clawdata.checkpt_style not in [0,1]:
        raise AttributeError("*** Unrecognized checkpt_style: %s"\
              % clawdata.checkpt_style)

    data_write(file, clawdata, None)


def make_amrclawdatafile(clawdata):
    r"""
    Take the data specified in clawdata and write it to claw.data in the
    form required by the Fortran code lib/main.f95.
    """


    # open file and write a warning header:
    file = open_datafile('amrclaw.data')

    write_clawdata_noamr(clawdata, file)
    write_clawdata_amr(clawdata, file)
    file.close()


def write_clawdata_amr(clawdata, file):
    r"""
    Write the input parameters only used by AMRClaw.
    """

    num_dim = clawdata.num_dim
    data_write(file, clawdata.amr_levels_max, 'amr_levels_max')

    num_ratios = max(abs(clawdata.amr_levels_max)-1, 1)
    if len(clawdata.refinement_ratios_x) < num_ratios:
        raise ValueError("*** Error in data parameter: " + \
              "require len(refinement_ratios_x) >= %s " % num_ratios)
    if len(clawdata.refinement_ratios_y) < num_ratios:
        raise ValueError("*** Error in data parameter: " + \
              "require len(refinement_ratios_y) >= %s " % num_ratios)
    data_write(file, clawdata.refinement_ratios_x, 'refinement_ratios_x')
    data_write(file, clawdata.refinement_ratios_y, 'refinement_ratios_y')
    if num_dim == 3:
        if len(clawdata.refinement_ratios_z) < num_ratios:
                raise ValueError("*** Error in data parameter: " + \
                  "require len(refinement_ratios_z) >= %s " % num_ratios)
        data_write(file, clawdata.refinement_ratios_z, 'refinement_ratios_z')
    if len(clawdata.refinement_ratios_t) < num_ratios:
        raise ValueError("*** Error in data parameter: " + \
              "require len(refinement_ratios_t) >= %s " % num_ratios)
    data_write(file, clawdata.refinement_ratios_t, 'refinement_ratios_t')

    data_write(file, clawdata, None)  # writes blank line

        
    data_write(file, clawdata.flag_richardson, 'flag_richardson')
    data_write(file, clawdata.flag_richardson_tol, 'flag_richardson_tol')
    data_write(file, clawdata.flag2refine, 'flag2refine')
    data_write(file, clawdata.flag2refine_tol, 'flag2refine_tol')
    data_write(file, clawdata.regrid_interval, 'regrid_interval')
    data_write(file, clawdata.regrid_buffer_width, 'regrid_buffer_width')
    data_write(file, clawdata.clustering_cutoff, 'clustering_cutoff')
    data_write(file, clawdata.verbosity_regrid, 'verbosity_regrid')
    data_write(file, clawdata, None)

    data_write(file, clawdata, None)

    data_write(file, clawdata.dprint, 'dprint')
    data_write(file, clawdata.eprint, 'eprint')
    data_write(file, clawdata.edebug, 'edebug')
    data_write(file, clawdata.gprint, 'gprint')
    data_write(file, clawdata.nprint, 'nprint')
    data_write(file, clawdata.pprint, 'pprint')
    data_write(file, clawdata.rprint, 'rprint')
    data_write(file, clawdata.sprint, 'sprint')
    data_write(file, clawdata.tprint, 'tprint')
    data_write(file, clawdata.uprint, 'uprint')
    data_write(file, clawdata, None)

def regions_and_gauges():
    r"""
    Placeholder... where to put these?
    """
    clawdata.add_attribute('nregions', len(clawdata.regions))
    data_write(file, clawdata.nregions, 'nregions')
    for regions in clawdata.regions:
        file.write(8*"   %g" % tuple(regions) +"\n")

    clawdata.add_attribute('ngauges', len(clawdata.gauges))
    data_write(file, clawdata.ngauges, 'ngauges')
    gaugeno_used = []
    for gauge in clawdata.gauges:
        gaugeno = gauge[0]
        if gaugeno in gaugeno_used:
            print "*** Gauge number %s used more than once! " % gaugeno
            raise Exception("Repeated gauge number")
        else:
            gaugeno_used.append(gauge[0])
        #file.write("%4i %19.10e  %17.10e  %13.6e  %13.6e\n" % tuple(gauge))
        file.write(5*"   %g" % tuple(gauge) +"\n")


def make_userdatafile(userdata):
    r"""
    Create the data file using the parameters in userdata.
    The parameters will be written to this file in the same order they were
    specified using userdata.add_attribute.
    Presumably the user will read these in using a Fortran routine, such as
    setprob.f95, and the order is important.
    """

    # open file and write a warning header:
    file = open_datafile(userdata.__fname__)

    # write all the parameters:
    for param in userdata._attributes:
        descr = userdata.__descr__.get(param, '')
        data_write(file, getattr(userdata,param), param, descr)

    file.close()

def make_setgauges_datafile(clawdata):
    """
    Create setgauges.data using gauges attribute of clawdata.
    """
    gauges = getattr(clawdata,'gauges',[])
    ngauges = len(gauges)

    print 'Creating data file setgauges.data'
    # open file and write a warning header:
    file = open_datafile('setgauges.data')
    file.write("%4i   =: ngauges\n" % ngauges)
    gaugeno_used = []
    for gauge in gauges:
        gaugeno = gauge[0]
        if gaugeno in gaugeno_used:
            print "*** Gauge number %s used more than once! " % gaugeno
            raise Exception("Repeated gauge number")
        else:
            gaugeno_used.append(gauge[0])
        file.write("%4i %19.10e  %17.10e  %13.6e  %13.6e\n" % tuple(gauge))
        # or use this variant with =:
        #gauge.append(gaugeno)
        #file.write("%4i %19.10e  %17.10e  %13.6e  %13.6e  =: gauge%s\n" % tuple(gauge))
    file.close()


#-----------------------------------------------------
# New version 6/30/09

class ClawRunData(ClawData):
    r"""
    Object that will be written out to claw.data.
    """
    def __init__(self, pkg, num_dim):
        super(ClawRunData,self).__init__()
        self.add_attribute('pkg',pkg)
        self.add_attribute('num_dim',num_dim)
        self.add_attribute('datalist',[])


        if pkg.lower() in ['classic', 'classicclaw']:
            self.add_attribute('xclawcmd', 'xclaw')

            # Required data set for basic run parameters:
            clawdata = ClawInputData(num_dim)
            self.add_attribute('clawdata', clawdata)
            self.datalist.append(clawdata)

        elif pkg.lower() in ['amrclaw', 'amr']:
            self.add_attribute('xclawcmd', 'xamr')

            # Required data set for basic run parameters:
            clawdata = AmrclawInputData(num_dim)
            self.add_attribute('clawdata', clawdata)
            self.datalist.append(clawdata)

        elif pkg.lower() in ['geoclaw']:
            self.add_attribute('xclawcmd', 'xgeoclaw')

            # Required data set for basic run parameters:
            clawdata = AmrclawInputData(num_dim)
            self.add_attribute('clawdata', clawdata)
            self.datalist.append(clawdata)
            geodata = GeoclawInputData(num_dim)
            self.add_attribute('geodata', geodata)
            self.datalist.append(geodata)

        else:
            raise AttributeError("Unrecognized Clawpack pkg = %s" % pkg)

    def new_UserData(self,name,fname):
        r"""
        Create a new attribute called name
        for application specific data to be written
        to the data file fname.
        """
        userdata = UserData(fname)
        self.datalist.append(userdata)
        self.add_attribute(name,userdata)
        exec('self.%s = userdata' % name)
        return userdata

    def add_GaugeData(self):
        r"""
        Create a gaugedata attribute for writing to gauges.data.
        """
        gaugedata = GaugeData(self.num_dim)
        self.datalist.append(gaugedata)
        self.gaugedata = gaugedata
        return gaugedata

    def write(self):
        for d in self.datalist:
            d.write()

class UserData(ClawData):
    r"""
    Object that will be written out to user file such as setprob.data, as
    determined by the fname attribute.
    """

    def __init__(self, fname):

        super(UserData,self).__init__()

        # Create attributes without adding to attributes list:

        # file to be read by Fortran for this data:
        object.__setattr__(self,'__fname__',fname)

        # dictionary to hold descriptions:
        object.__setattr__(self,'__descr__',{})

    def add_param(self,name,value,descr=''):
         self.add_attribute(name,value)
         descr_dict = self.__descr__
         descr_dict[name] = descr

    def write(self):
         print 'Creating data file %s' % self.__fname__
         make_userdatafile(self)


class GeoclawInputData(Data):
    r"""
    Object that will be written out to the various GeoClaw data files.
    """
    def __init__(self, num_dim):
        super(GeoclawInputData,self).__init__()

        # Set default values:
        self.add_attribute('igravity',1)
        self.add_attribute('iqinit',0)
        self.add_attribute('icoriolis',1)
        self.add_attribute('Rearth',6367500.0)
        # NEED TO CONTINUE!

    def write(self):

        print 'Creating data file setgeo.data'
        # open file and write a warning header:
        file = open_datafile('setgeo.data')
        data_write(file, self, 'igravity')
        data_write(file, self, 'gravity')
        data_write(file, self, 'icoordsys')
        data_write(file, self, 'icoriolis')
        data_write(file, self, 'Rearth')
        file.close()

        print 'Creating data file settsunami.data'
        # open file and write a warning header:
        file = open_datafile('settsunami.data')
        data_write(file, self, 'sealevel')
        data_write(file, self, 'drytolerance')
        data_write(file, self, 'wavetolerance')
        data_write(file, self, 'depthdeep')
        data_write(file, self, 'maxleveldeep')
        data_write(file, self, 'ifriction')
        data_write(file, self, 'coeffmanning')
        data_write(file, self, 'frictiondepth')
        file.close()

        print 'Creating data file settopo.data'
        # open file and write a warning header:
        file = open_datafile('settopo.data')
        self.ntopofiles = len(self.topofiles)
        data_write(file, self, 'ntopofiles')
        for tfile in self.topofiles:
            try:
                fname = os.path.abspath(tfile[-1])
            except:
                print "*** Error: file not found: ",tfile[-1]
                raise MissingFile("file not found")
            file.write("\n'%s' \n " % fname)
            file.write("%3i %3i %3i %20.10e %20.10e \n" % tuple(tfile[:-1]))
        file.close()

        print 'Creating data file setdtopo.data'
        # open file and write a warning header:
        file = open_datafile('setdtopo.data')
        self.mdtopofiles = len(self.dtopofiles)
        data_write(file, self, 'mdtopofiles')
        data_write(file, self, None)
        for tfile in self.dtopofiles:
            try:
                fname = "'%s'" % os.path.abspath(tfile[-1])
            except:
                print "*** Error: file not found: ",tfile[-1]
                raise MissingFile("file not found")
            file.write("\n%s \n" % fname)
            file.write("%3i %3i %3i\n" % tuple(tfile[:-1]))
        file.close()

        print 'Creating data file setqinit.data'
        # open file and write a warning header:
        file = open_datafile('setqinit.data')
        # self.iqinit tells which component of q is perturbed!
        data_write(file, self, 'iqinit')
        data_write(file, self, None)
        for tfile in self.qinitfiles:
            try:
                fname = "'%s'" % os.path.abspath(tfile[-1])
            except:
                print "*** Error: file not found: ",tfile[-1]
                raise MissingFile("file not found")
            file.write("\n%s  \n" % fname)
            file.write("%3i %3i \n" % tuple(tfile[:-1]))
        file.close()

        make_setgauges_datafile(self)


        print 'Creating data file setfixedgrids.data'
        # open file and write a warning header:
        file = open_datafile('setfixedgrids.data')
        self.nfixedgrids = len(self.fixedgrids)
        data_write(file, self, 'nfixedgrids')
        data_write(file, self, None)
        for fixedgrid in self.fixedgrids:
            file.write(11*"%g  " % tuple(fixedgrid) +"\n")
        file.close()


        print 'Creating data file setregions.data'
        # open file and write a warning header:
        file = open_datafile('setregions.data')
        self.nregions = len(self.regions)
        data_write(file, self, 'nregions')
        data_write(file, self, None)
        for regions in self.regions:
            file.write(8*"%g  " % tuple(regions) +"\n")
        file.close()

