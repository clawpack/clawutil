r"""
Data Module

Contains the general class definition and the subclasses of the Clawpack data
objects.

Changes in 5.0:
 Stripped down version of Data object, no longer keeps track of "owners".
 Data classes are now subclasses of ClawData, which checks if attributes
   already exist before setting.

"""

from __future__ import absolute_import
from __future__ import print_function
import os
try:
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

import tarfile
import zipfile
import string

import numpy as np
import six
from six.moves import range
from six.moves import input

# ======================
#  Remote file handling
# ======================
def strip_archive_extensions(path, 
                             extensions=["tar", "tgz", "bz2", "gz", "zip"]):
    r"""
    Strip off archive extensions defined in *extensions* list.

    Return stripped path calling this function recursively until all splitext
    does not provide an extension in the *extensions* list.  Note that zip
    files store the names of the contained files in the archive and the 
    returned path will more than likely not have the appropriate file suffix.

    """

    if os.path.splitext(path)[-1][1:] in extensions:
        return strip_archive_extensions(os.path.splitext(path)[0])
    else:
        return path


def get_remote_file(url, output_dir=None, file_name=None, force=False,  
                         verbose=False, ask_user=False, unpack=True):
    r"""Fetch file located at *url* and store at *output_dir*.

    :Input:
    
     - *url* (path) - URL to file to be downloaded.
     - *output_dir* (path) - Directory that the remote file will be downloaded
       to.  Defaults to the GeoClaw sratch directory defined by 
       *os.path.join(os.environ['CLAW'], 'geoclaw', 'scratch')*.
     - *file_name* (string) - Name of local file.  This defaults to the name of
       the remote file.
     - *force* (bool) - Force downloading of remote file regardless of whether
       it exists locally or not.  Default is *False*
     - *verbose* (bool) - Print out status information.  Default is *False*
     - *ask_user* (bool) - Whether to ask the user if it is ok to download the
       file before proceeding.  Default is *False*

    :Raises:
     
    Exceptions are raised from the *urllib* module having to do with errors
    fetching the remote file.  Please see its documentation for more details of
    the exceptions that can be raised.

    :Notes:

    If fetching the file fails *urllib* does not always warn you so if errors
    occur it may be wise to check to make sure the downloaded file actually has
    content in it.

    returns *unarchived_output_path*
    """

    if output_dir is None:
        output_dir = os.path.join(os.environ['CLAW'], 'geoclaw', 'scratch')

    if file_name is None:
        file_name = os.path.basename(url)
        
    output_path = os.path.join(output_dir, file_name)
    unarchived_output_path = strip_archive_extensions(output_path)

    if not os.path.exists(unarchived_output_path) or force:

        if ask_user:
            ans = input("  Ok to download topo file and save as %s?  \n"
                            % unarchived_output_path,
                            "     Type y[es], n[o].")
            if ans.lower() in ['y', 'yes']:
                if verbose:
                    print("*** Aborting download.")
                return None
            
        # if not os.path.exists(output_path):
        # Fetch remote file, will raise a variety of exceptions depending on
        # the retrieval problem if it happens
        if verbose:
            print("Downloading %s to %s..." % (url, output_path))
        with open(output_path, "wb") as output_file:
            remote_file = urlopen(url)
            output_file.write(remote_file.read())
        if verbose:
            print("Done downloading.")
        # elif verbose:
        #     print("File already exists, not downloading")

        if tarfile.is_tarfile(output_path) and unpack:
            if verbose:
                print("Un-archiving %s to %s..." % (output_path, 
                                                    unarchived_output_path))
            with tarfile.open(output_path, mode="r:*") as tar_file:
                tar_file.extractall(path=output_dir)
            if verbose:
                print("Done un-archiving.")
        elif zipfile.is_zipfile(output_path) and unpack:
            if verbose:
                print("Un-archiving %s to %s..." % (output_path, 
                                                    unarchived_output_path))
            with zipfile.ZipFile(output_path, mode="r") as zip_file:
                zip_file.extractall(path=output_dir)
                # Add file suffix
                extension = os.path.splitext(zip_file.namelist()[0])[-1]
                unarchived_output_path = "".join((unarchived_output_path,
                                                  extension))
            if verbose:
                print("Done un-archiving.")

    else:
        if verbose:
            print("Skipping %s " % url)
            print("  because file already exists: %s" % output_path)

    if unpack:
        return unarchived_output_path
    else:
        return output_path



# ==============================================================================
#  Base data class for Clawpack data objects
class ClawData(object):
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

        # Output file handle
        object.__setattr__(self,'_out_file',None)

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
            print("*** Unrecognized attribute: ",name)
            print("*** Perhaps a typo?")
            print("*** Add new attributes using add_attribute method")
            raise AttributeError("Unrecognized attribute: %s" % name)
        
        # attribute exists, ok to set:
        object.__setattr__(self,name,value)


    def __str__(self):
        r"""Returns string representation of this object"""
        output = "%s%s\n" % ("Name".ljust(25),"Value".ljust(12))
        for (k,v) in six.iteritems(self):
            output += "%s%s\n" % (str(k).ljust(25),str(v).ljust(12))
        return output


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


    def attributes(self):
        r"""Returns tuple of attribute names"""
        return tuple(self._attributes)


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


    def open_data_file(self, name, datasource='setrun.py'):
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

        source = datasource.ljust(25)
        self._out_file = open(name, 'w')
        self._out_file.write('########################################################\n')
        self._out_file.write('### DO NOT EDIT THIS FILE:  GENERATED AUTOMATICALLY ####\n')
        self._out_file.write('### To modify data, edit  %s ####\n' % source)
        self._out_file.write('###    and then "make .data"                        ####\n')
        self._out_file.write('########################################################\n\n')


    def close_data_file(self):
        r"""Close output data file"""
        self._out_file.close()
        self._out_file = None


    def write(self,out_file,data_source='setrun.py'):
        r"""Write out all data files in this ClawData object"""

        # Open data file
        self.open_data_file(out_file,data_source)

        # Write out list of attributes
        for (name,value) in self.iteritems():
            self.data_write(name)


    def data_write(self, name=None, value=None, alt_name=None, description=''):
        r"""
        Write out value to data file, in the form ::

           value =: name   # [description]

        Remove brackets and commas from lists, and replace booleans by T/F.

        :Input:
         - *name* - (string) normally a string defining the variable,
           ``if name==None``, write a blank line.
         - *description* - (string) optional description
        """
        if self._out_file is None:
            raise Exception("No file currently open for output.")

        # Defaults to the name of the variable requested
        if alt_name is None:
            alt_name = name

        if name is None and value is None:
            # Write out a blank line
            self._out_file.write('\n')
        else:
            # Use the value passed in instead of fetching from the data object
            if value is None:
                value = self.__getattribute__(name)

            # Convert value to an appropriate string repr
            if isinstance(value,np.ndarray):
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
            padded_value = string_value.ljust(20)
            padded_name = alt_name.ljust(20)
            if description != '':
                self._out_file.write('%s =: %s # %s \n' % 
                                        (padded_value, padded_name, description))
            else:
                self._out_file.write('%s =: %s\n' % 
                                    (padded_value, padded_name))
  

    def read(self,path,force=False):
        r"""Read and fill applicable data attributes.

        Note that if the data attribute is not found an exception will be
        raised unless the force argument is set to True in which case a new
        attribute will be added.
        """

        data_file = open(os.path.abspath(path),'r')

        for lineno,line in enumerate(data_file):
            if "=:" not in line:
                continue

            value, tail = line.split("=:")
            varname = tail.split()[0]

            # Set this parameter
            if self.has_attribute(varname) or force:
                value = self._parse_value(value)
                if not self.has_attribute(varname):
                    self.add_attribute(varname,value)
                else:
                    setattr(self,varname,value)
    

    def _parse_value(self,value):
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
            return [self._parse_value(vv) for vv in value.split()]

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

#  Base data class for Clawpack data objects
# ==============================================================================


# ==============================================================================
# Clawpack input data classes
class ClawRunData(ClawData):
    r"""
    Object that contains all data objects that need to written out.

    Depending on the package type, this object contains the necessary data
    objects that need to eventually be written out to files.
    """

    def __init__(self, pkg, num_dim):
        super(ClawRunData,self).__init__()
        self.add_attribute('pkg',pkg)
        self.add_attribute('num_dim',num_dim)
        self.add_attribute('data_list',[])
        self.add_attribute('xclawcmd',None)

        # Always need the basic clawpack data object
        self.add_data(ClawInputData(num_dim),'clawdata')

        # Add package specific data objects
        if pkg.lower() in ['classic', 'classicclaw']:
            self.xclawcmd = 'xclaw'

        elif pkg.lower() in ['amrclaw', 'amr']:

            import clawpack.amrclaw.data as amrclaw

            self.xclawcmd = 'xamr'
            self.add_data(ClawInputData(num_dim),'clawdata')
            self.add_data(amrclaw.AmrclawInputData(self.clawdata),'amrdata')
            self.add_data(amrclaw.RegionData(num_dim=num_dim),'regiondata')
            self.add_data(amrclaw.GaugeData(num_dim=num_dim),'gaugedata')
            try:
                self.add_data(amrclaw.AdjointData(num_dim=num_dim),'adjointdata')
            except:
                pass # for backward compatibility

        elif pkg.lower() in ['geoclaw']:

            import clawpack.amrclaw.data as amrclaw
            import clawpack.geoclaw.data as geoclaw

            self.xclawcmd = 'xgeoclaw'

            # Required data set for basic run parameters:
            self.add_data(amrclaw.AmrclawInputData(self.clawdata),'amrdata')
            self.add_data(amrclaw.RegionData(num_dim=num_dim),'regiondata')
            self.add_data(amrclaw.GaugeData(num_dim=num_dim),'gaugedata')
            self.add_data(geoclaw.GeoClawData(),('geo_data'))
            self.add_data(geoclaw.TopographyData(),'topo_data')
            self.add_data(geoclaw.DTopoData(),'dtopo_data')
            self.add_data(geoclaw.RefinementData(),'refinement_data')
            self.add_data(geoclaw.FixedGridData(),'fixed_grid_data')
            self.add_data(geoclaw.QinitData(),'qinit_data')
            self.add_data(geoclaw.FGmaxData(),'fgmax_data')
            self.add_data(geoclaw.SurgeData(),'surge_data')
            self.add_data(geoclaw.FrictionData(),'friction_data')
            self.add_data(geoclaw.MultilayerData(), 'multilayer_data')

        else:
            raise AttributeError("Unrecognized Clawpack pkg = %s" % pkg)


    def add_data(self,data,name,file_name=None):
        r"""Add data object named *name* and written to *file_name*."""
        self.add_attribute(name,data)
        self.data_list.append(data)


    def replace_data(self, name, new_object):
        r"""
        Replace data objected named *name* with *new_object*
        """
        self.data_list.remove(getattr(self, name))
        setattr(self, name, new_object)
        self.data_list.append(getattr(self, name))


    def new_UserData(self,name,fname):
        r"""
        Create a new attribute called name
        for application specific data to be written
        to the data file fname.
        """
        data = UserData(fname)
        self.add_data(data,name,fname)
        return data


    def write(self):
        r"""Write out each data objects in datalist """
        
        import clawpack.amrclaw.data as amrclaw

        for data_object in self.data_list:
            if isinstance(data_object, amrclaw.GaugeData):
                data_object.write(self.clawdata.num_eqn, self.clawdata.num_aux)
            else:
                data_object.write()



class ClawInputData(ClawData):
    r"""
    Object containing basic Clawpack input data, usually written to 'claw.data'.


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
        self.add_attribute('output_aux_components','none')
        self.add_attribute('output_aux_onlyonce',True)
        
        self.add_attribute('dt_initial',1.e-5)
        self.add_attribute('dt_max',1.e99)
        self.add_attribute('dt_variable',True)
        self.add_attribute('cfl_desired',0.9)
        self.add_attribute('cfl_max',1.0)
        self.add_attribute('steps_max',50000)
        self.add_attribute('order',2)
        self.add_attribute('dimensional_split',0)
        self.add_attribute('verbosity',0)
        self.add_attribute('verbosity_regrid',0)
        self.add_attribute('source_split',0)
        self.add_attribute('capa_index',0)
        self.add_attribute('limiter',[4])
        self.add_attribute('t0',0.)
        self.add_attribute('num_ghost',2)
        self.add_attribute('use_fwaves',False)
        
        if num_dim == 1:
            self.add_attribute('lower',[0.])
            self.add_attribute('upper',[1.])
            self.add_attribute('num_cells',[100])
            self.add_attribute('bc_lower',[0])
            self.add_attribute('bc_upper',[0])
            self.add_attribute('transverse_waves',0)
        elif num_dim == 2:
            self.add_attribute('lower',[0.,0.])
            self.add_attribute('upper',[1.,1.])
            self.add_attribute('num_cells',[100,100])
            self.add_attribute('bc_lower',[0,0])
            self.add_attribute('bc_upper',[0,0])
            self.add_attribute('transverse_waves',2)
        elif num_dim == 3:
            self.add_attribute('lower',[0.,0.,0.])
            self.add_attribute('upper',[1.,1.,1.])
            self.add_attribute('num_cells',[100,100,100])
            self.add_attribute('bc_lower',[0,0,0])
            self.add_attribute('bc_upper',[0,0,0])
            self.add_attribute('transverse_waves',22)
        else:
            raise ValueError("Only num_dim=1, 2, or 3 supported ")

        # Restart capability, not all Clawpack packages handles this yet.
        self.add_attribute('restart',False)
        self.add_attribute('restart_file','')
        self.add_attribute('checkpt_style',0)
        self.add_attribute('checkpt_interval',1000)
        self.add_attribute('checkpt_time_interval',1000.)
        self.add_attribute('checkpt_times',[1000.])


    def write(self, out_file='claw.data', data_source='setrun.py'):
        r"""Write input data to a file"""
        self.open_data_file(out_file,data_source)

        self.data_write('num_dim')
        self.data_write('lower')
        self.data_write('upper')
        self.data_write('num_cells')
        self.data_write()  # writes blank line
        self.data_write('num_eqn')
        self.data_write('num_waves')
        self.data_write('num_aux')
        self.data_write()  # writes blank line

        self.data_write('t0')
        self.data_write()
        self.data_write('output_style')

        if self.output_style == 1:
            self.data_write('num_output_times')
            self.data_write('tfinal')
            self.data_write('output_t0')
        elif self.output_style == 2:
            if len(self.output_times) == 0:
                raise AttributeError("*** output_style==2 requires nonempty list" \
                        + " of output times")
            self.num_output_times = len(self.output_times)
            self.data_write('num_output_times')
            self.data_write('output_times')
        elif self.output_style==3:
            self.data_write('output_step_interval')
            self.data_write('total_steps')
            self.data_write('output_t0')
        else:
            raise AttributeError("*** Unrecognized output_style: %s"\
                  % self.output_style)

        self.data_write()
        if self.output_format in [1,'ascii']:
            self.output_format = 1
        elif self.output_format in [2,'netcdf']:
            self.output_format = 2
        elif self.output_format in [3,'binary']:
            self.output_format = 3
        else:
            raise ValueError("*** Error in data parameter: " + \
                  "output_format unrecognized: ",self.output_format)
            
        self.data_write('output_format')

        if self.output_q_components == 'all':
            iout_q = self.num_eqn * [1]
        elif self.output_q_components == 'none':
            iout_q = self.num_eqn * [0]
        else:
            #iout_q = np.where(self.output_q_components, 1, 0)
            print("*** WARNING: Selective output_q_components not implemented")
            print("***          Will output all components of q")
            iout_q = self.num_eqn * [1]
    

        # Write out local value of iout_q rather than a data member
        self.data_write('', value=iout_q, alt_name='iout_q')

        if self.num_aux > 0:
            if isinstance(self.output_aux_components,six.string_types):
                if self.output_aux_components.lower() == 'all':
                    iout_aux = self.num_aux * [1]
                elif self.output_aux_components.lower() == 'none':
                    iout_aux = self.num_aux * [0]
                else:
                    raise ValueError("Invalid aux array component option.")
            else:
                iout_aux = np.where(self.output_aux_components, 1, 0)
                print("*** WARNING: Selective output_aux_components not implemented")
                print("***          Will output all components of aux")
                iout_aux = self.num_aux * [1]
            self.data_write(name='', value=iout_aux, alt_name='iout_aux')
            self.data_write('output_aux_onlyonce')

        self.data_write()
        self.data_write('dt_initial')
        self.data_write('dt_max')
        self.data_write('cfl_max')
        self.data_write('cfl_desired')
        self.data_write('steps_max')
        self.data_write()
        self.dt_variable = bool(self.dt_variable) # in case 0 or 1
        self.data_write('dt_variable')
        self.data_write('order')

        if self.num_dim == 1:
            pass
        else:
            # Transverse options different in 2D and 3D
            if self.num_dim == 2:
                if self.transverse_waves in [0,'none']:  
                    self.transverse_waves = 0
                elif self.transverse_waves in [1,'increment']:  
                    self.transverse_waves = 1
                elif self.transverse_waves in [2,'all']:  
                    self.transverse_waves = 2
                else:
                    raise AttributeError("Unrecognized transverse_waves: %s" \
                                             % self.transverse_waves)
            else:    # 3D
                if self.transverse_waves in [0,'none']:  
                    self.transverse_waves = 0
                elif self.transverse_waves in [1,'increment']:  
                    self.transverse_waves = 11
                elif self.transverse_waves in [2,'all']:  
                    self.transverse_waves = 22
                if not (self.transverse_waves in [0, 10, 11, 20, 21, 22]):
                    raise AttributeError("Unrecognized transverse_waves: %s" \
                                             % self.transverse_waves)
            self.data_write(None, self.transverse_waves, 'transverse_waves')

            if self.dimensional_split in [0,'unsplit']:  
                self.dimensional_split = 0
            elif self.dimensional_split in [1,'godunov']:  
                self.dimensional_split = 1
            elif self.dimensional_split in [2,'strang']:  
                if self.num_dim == 3:
                    raise AttributeError("Strang dimensional splitting not supported in 3D")
                else:
                    self.dimensional_split = 2
            else:
                raise AttributeError("Unrecognized dimensional_split: %s" \
                      % self.dimensional_split)
            self.data_write('dimensional_split')
            
        self.data_write('verbosity')

        if self.source_split in [0,'none']:  
            self.source_split = 0
        elif self.source_split in [1,'godunov']:  
            self.source_split = 1
        elif self.source_split in [2,'strang']:  
            self.source_split = 2
        else:
            raise AttributeError("Unrecognized source_split: %s" \
                  % self.source_split)
        self.data_write('source_split')

        self.data_write('capa_index')
        self.data_write('use_fwaves')
        self.data_write()

        for i in range(len(self.limiter)):
            if self.limiter[i] in [0,'none']:        self.limiter[i] = 0
            elif self.limiter[i] in [1,'minmod']:    self.limiter[i] = 1
            elif self.limiter[i] in [2,'superbee']:  self.limiter[i] = 2
            elif self.limiter[i] in [3,'vanleer']:   self.limiter[i] = 3
            elif self.limiter[i] in [4,'mc']:        self.limiter[i] = 4
            else:
                raise AttributeError("Unrecognized limiter: %s" \
                      % self.limiter[i])
        self.data_write('limiter')

        self.data_write()

        self.data_write('num_ghost')
        if not isinstance(self.bc_lower, list):
            self.bc_lower = [self.bc_lower]    # Allow bare number in 1D
        if len(self.bc_lower) != self.num_dim:
            raise AttributeError("Incorrect number of lower BC codes (expected %d, got %d)" \
                                     %(self.num_dim, len(self.bc_lower)))
        for i in range(self.num_dim):
            if self.bc_lower[i] in [0,'user']:       self.bc_lower[i] = 0
            elif self.bc_lower[i] in [1,'extrap']:   self.bc_lower[i] = 1
            elif self.bc_lower[i] in [2,'periodic']: self.bc_lower[i] = 2
            elif self.bc_lower[i] in [3,'wall']:     self.bc_lower[i] = 3
            else:
                raise AttributeError("Unrecognized bc_lower: %s" \
                      % self.bc_lower[i])
        self.data_write('bc_lower')

        if not isinstance(self.bc_upper, list):
            self.bc_upper = [self.bc_upper]    # Allow bare number in 1D
        if len(self.bc_upper) != self.num_dim:
            raise AttributeError("Incorrect number of upper BC codes (expected %d, got %d)" \
                                     %(self.num_dim, len(self.bc_upper)))
        for i in range(self.num_dim):
            if self.bc_upper[i] in [0,'user']:       self.bc_upper[i] = 0
            elif self.bc_upper[i] in [1,'extrap']:   self.bc_upper[i] = 1
            elif self.bc_upper[i] in [2,'periodic']: self.bc_upper[i] = 2
            elif self.bc_upper[i] in [3,'wall']:     self.bc_upper[i] = 3
            else:
                raise AttributeError("Unrecognized bc_upper: %s" \
                      % self.bc_upper[i])
        self.data_write('bc_upper')

        self.data_write()
        self.data_write('restart')
        self.data_write('restart_file')
        self.data_write('checkpt_style')

        if self.checkpt_style in [-2,2]:
            num_checkpt_times = len(self.checkpt_times)
            self.data_write(name='', value=num_checkpt_times, alt_name='num_checkpt_times')
            self.data_write('checkpt_times')
        elif self.checkpt_style in [-3,3]:
            self.data_write('checkpt_interval')
        elif self.checkpt_style not in [0,1,-1]:
            raise AttributeError("*** Unrecognized checkpt_style: %s"\
                  % self.checkpt_style)

        self.data_write()
        self.close_data_file()


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

    def write(self,data_source='setrun.py'):
        super(UserData,self).write(self.__fname__, data_source)
        self.close_data_file()
