r"""Simple controller for runs with GeoClaw

Includes support for multiple runs at the same time

"""
# ============================================================================
#      Copyright (C) 2013 Kyle Mandli <kyle@ices.utexas.edu>
#
#  Distributed under the terms of the Berkeley Software Distribution (BSD) 
#  license
#                     http://www.opensource.org/licenses/
# ============================================================================

import subprocess
import os
import time
import glob


class Test(object):
    r"""Base object for all tests 

    The ``type``, ``name``, and ``prefix`` attributes are used by the 
    :class:`TestController` to create the path to the output files along with 
    the name of the output directories and log file.  The pattern is 
    ``base_path/type/name/prefix*``.  See :class:`TestController` for more 
    information on how these are created.

    .. attribute:: type

        (string) - The top most directory that the test output will be 
        located in.  ``default = ""``.
    
    .. attribute:: name

        (string) - The second top most directory that the test output will
        be located in.  ``default = ""``.
    
    .. attribute:: prefix

        (string) - The prefix applied to the data directory, the output
        directory, and the log file.  ``default = None``.
    
    .. attribute:: executable

        (string) - Name of the binary executable.  ``default = "xclaw"``.
    
    .. attribute:: setplot

        (string) - Name of the module containing the `setplot` 
        function.  ``default = "setplot"``.
    
    .. attribute:: rundata

        (clawpack.clawutil.data.ClawRunData) - The data object 
        containing all data objects.  By default all data objects inside of this
        object will be written out.  This attribute must be instantiated by any
        subclass and if not will raise a ValueError exception when asked to 
        write out.

    :Initialization:

    Output:
     - (:class:`Test`) - Initialized Test object.
    """

    def __init__(self):
        r"""
        Initialize a TestController object
        
        See :class:`TestController` for full documentation
        """ 

        # Base test traits
        self.type = ""
        self.name = ""
        self.setplot = "setplot"
        self.prefix = None
        self.executable = 'xclaw'

        self.rundata = None
        

    def __str__(self):
        output = "Test %s: %s" % (self.name,self.prefix)
        output += "\n  Setplot: %s" % self.setplot
        return output
    
        
    def write_data_objects(self):
        r"""
        Write out data objects contained in *rundata*

        Raises ValueError if *rundata* has not been set.

        """

        if self.rundata is None:
            raise ValueError("Must set rundata to a ClawRunData object.")
        self.rundata.write()

  

class TestController(object):
    r"""
    Controller for Clawpack test runs

    Controller object that will run the set of tests provided with the
    parameters set in the object including plotting, path creation, and 
    simple process parallelism.

    .. attribute:: tests 

        (list) - List of :class:`Test` objects that will be run.

    .. attribute:: plot 

        (bool) - If True each test will be plotted after it has run.  
        ``default = True``

    .. attribute:: tar

        (bool) - If True will tar and gzip the plots directory.  
        ``default = False``

    .. attribute:: verbose

        (bool) - If True will print to stdout the remaining tests 
        waiting to be run and how many are in currently in the process queue.
        ``default = False``.

    .. attribute:: terminal_output

        (bool) - If ``paralllel`` is False, this controls where
        the output is sent.  If True then it will simply use stdout, if False
        then the usual log file will be used.  ``default = False``.

    .. attribute:: base_path

        (path) - The base path to put all output.  If the 
        environment variable ``DATA_PATH`` is set than the ``base_path`` will be
        set to that.  Otherwise the current working directory (returned by 
        ``os.getcwd()``) will be used.

    .. attribute:: parallel

        (bool) - If True, tests will be run in parallel.  This means
        that tests will be run concurrently with other tests up to a maximum at
        one time of ``max_processes``.  Once a process completes a new one is 
        started.  ``default = True``.

    .. attribute:: wait

        (bool) - If True, the method waits to return until the last test
        has completed.  If False then the method returns immediately once the 
        last test has been added to the process queue.  Default is `False`.

    .. attribute:: poll_interval

        (float) - Interval to poll for the status of each 
        processes.  Default is `5.0` seconds.

    .. attribute:: max_processes

        (int) - The maximum number of processes that can be run
        at one time.  If the environment variable `OMP_NUM_THREADS` is set then
        this defaults to that number.  Otherwise `4` is used.

    .. attribute:: runclaw_cmd

        (string) - The string that stores the base command for the
        run command.
        ``default = "python $CLAW/clawutil/src/python/clawutil/runclaw.py"``.

    .. attribute:: plotclaw_cmd

        (string) - The string that stores the base command for the
        plotting command. 
        ``default = "python $CLAW/visclaw/src/visclaw/plotclaw.py"``.


    :Initialization:

    Input:
     - *tests* - (list) List of :class:`Test` objects to be run.

    Output:
     - (:class:`TestController`) Initialized TestController object

    """

    def __init__(self, tests=[]):
        r"""
        Initialize a TestController object
        
        See :class:`TestController` for full documentation
        """ 

        super(TestController, self).__init__()

        # Establish controller default parameters
        # Execution controls
        self.plot = True
        self.tar = False
        self.verbose = False
        self.terminal_output = False

        # Path controls
        if os.environ.has_key('DATA_PATH'):
            self.base_path = os.environ['DATA_PATH']
        else:
            self.base_path = os.getcwd()
        self.base_path = os.path.expanduser(self.base_path)
    
        # Parallel run controls
        self.parallel = True
        self.wait = False
        self.poll_interval = 5.0
        if os.environ.has_key('OMP_NUM_THREADS'):
            self.max_processes = int(os.environ['OMP_NUM_THREADS'])
        else:
            self.max_processes = 4
        self._process_queue = []

        # Default commands for running and plotting
        self.runclaw_cmd = "python $CLAW/clawutil/src/python/clawutil/runclaw.py"
        self.plotclaw_cmd = "python $CLAW/visclaw/src/python/visclaw/plotclaw.py"

        # Add the initial tests to the tests list
        if not isinstance(tests, list) and not isinstance(tests, tuple):
            raise ValueError("Tests must be a list or tuple.")
        self.tests = []
        for test in tests:
            if isinstance(test, Test):
                self.tests.append(test)
            else:
                raise ValueError("Elements of tests must be a Test.")


    def __str__(self):
        output = ""
        for (i,test) in enumerate(self.tests):
            output += "====== Test #%s ============================\n" % (i)
            output += str(test) + "\n"
        return output


    def run(self):
        r"""Run tests from controllers *tests* list.

        For each Test object in *tests* create a set of paths, directory
        structures, and log files in preperation for running the commands
        constructed.  If *parallel* is True then tests are started and added
        to a queue with a maximum of *maximum_processes*.  If *parallel* is 
        False each test is run to completion before continuing.  The *wait*
        parameter controls whether the function waits for the last test to run
        before returning.

        Output:
         - *paths* - (list) List of dictionaries containing paths to the data
           constructed for each test. The dictionary has keys 'test', 'data', 
           'output', 'plots', and 'log' which respectively stores the base 
           directory of the test, the data, output, and plot directories, and
           the log file.
        """
        
        # Run tests
        paths = []
        for (i,test) in enumerate(self.tests):
            # Create output directory
            data_dirname = ''.join((test.prefix,'_data'))
            output_dirname = ''.join((test.prefix,"_output"))
            plots_dirname = ''.join((test.prefix,"_plots"))
            log_name = ''.join((test.prefix,"_log.txt"))
            
            if len(test.type) > 0:
                test_path = os.path.join(self.base_path,test.type,test.name)
            else:
                test_path = os.path.join(self.base_path,test.name)
            test_path = os.path.abspath(test_path)
            data_path = os.path.join(test_path,data_dirname)
            output_path = os.path.join(test_path,output_dirname)
            plots_path = os.path.join(test_path,plots_dirname)
            log_path = os.path.join(test_path,log_name)
            paths.append({'test':test_path, 'data':data_path,
                          'output':output_path, 'plots':plots_path,
                          'log':log_path})

            # Create test directory if not present
            if not os.path.exists(test_path):
                os.makedirs(test_path)

            # Clobber old data directory
            if os.path.exists(data_path):
                if not test.rundata.clawdata.restart:
                    data_files = glob.glob(os.path.join(data_path,'*.data'))
                    for data_file in data_files:
                        os.remove(data_file)
            else:
                os.mkdir(data_path)

            # Open and start log file
            log_file = open(log_path,'w')
            tm = time.localtime()
            year = str(tm[0]).zfill(4)
            month = str(tm[1]).zfill(2)
            day = str(tm[2]).zfill(2)
            hour = str(tm[3]).zfill(2)
            minute = str(tm[4]).zfill(2)
            second = str(tm[5]).zfill(2)
            date = 'Started %s/%s/%s-%s:%s.%s' % (year,month,day,hour,minute,second)
            log_file.write(date)
        
            # Write out data
            temp_path = os.getcwd()
            os.chdir(data_path)
            test.write_data_objects()
            os.chdir(temp_path)

            # Handle restart requests
            if test.rundata.clawdata.restart:
                restart = "T"
                overwrite = "F"
            else:
                restart = "F"
                overwrite = "T"
            
            # Construct string commands
            run_cmd = "%s %s %s %s %s %s True" % (self.runclaw_cmd, test.executable, output_path,
                                                      overwrite, restart, data_path)
            plot_cmd = "%s %s %s %s" % (self.plotclaw_cmd, output_path, plots_path, 
                                                                       test.setplot)
            tar_cmd = "tar -cvzf %s.tgz -C %s/.. %s" % (plots_path, plots_path, os.path.basename(plots_path))
            cmd = run_cmd
            if self.plot:
                cmd = ";".join((cmd,plot_cmd))
                if self.tar:
                    cmd = ";".join((cmd,tar_cmd))
            
            # Run test
            if self.parallel:
                while len(self._process_queue) == self.max_processes:
                    if self.verbose:
                        print "Number of processes currently:",len(self._process_queue)
                    for process in self._process_queue:
                        if process.poll() == 0:
                            self._process_queue.remove(process)
                    time.sleep(self.poll_interval)
                self._process_queue.append(subprocess.Popen(cmd,shell=True,
                        stdout=log_file,stderr=log_file))
                
            else:
                if self.terminal_output:
                    log_file.write("Outputting to terminal...")
                    subprocess.Popen(cmd,shell=True).wait()
                    log_file.write("Command completed.")
                else:
                    subprocess.Popen(cmd,shell=True,stdout=log_file,
                        stderr=log_file).wait()

        # -- All tests have been started --

        # Wait to exit while processes are still going
        if self.wait:
            while len(self._process_queue) > 0:
                time.sleep(self.poll_interval)
                for process in self._process_queue:
                    if process.poll() == 0:
                        self._process_queue.remove(process)
                print "Number of processes currently:",len(self._process_queue)
            
        return paths

