r"""
Execute nosetests in all subdirectories, to run a series of quick
regression tests.

Sends output and result/errors to separate files to simplify checking
results and looking for errors.
"""

from __future__ import print_function

from __future__ import absolute_import
import os
import sys
import tempfile
import subprocess
import unittest
import shutil
import inspect
import time
import glob

import numpy

import clawpack.geoclaw.util
import clawpack.pyclaw.gauges as gauges
import clawpack.pyclaw.solution as solution
import clawpack.clawutil.claw_git_status as claw_git_status
from clawpack.clawutil import runclaw

# Support for WIP decorator
from functools import wraps
from nose.plugins.attrib import attr
from nose.plugins.skip import SkipTest

# Work in progress test decorator
def fail(message):
    raise SkipTest(message)
 
# Work in progress decorator - will test but skips the test on failure
def wip(f):
    @wraps(f)
    def run_test(*args, **kwargs):
        try:
            # Set to success so we don't save out the output when we know things
            # are awry
            args[0].success = True
            f(*args, **kwargs)
        except Exception as e:
            raise SkipTest("WIP test failed: " + str(e))
        fail("test passed but marked as work in progress")
    
    return attr('wip')(run_test)


class ClawpackRegressionTest(unittest.TestCase):

    r"""Base Clawpcak regression test setup

    All regression tests for Clawpack are derived from this base class.  The
    class conforms to the *unittest* modules standards including *setUp*, 
    *runTest* and *tearDown* methods which implement various parts of the 
    regression test.  Generally these methods are responsible for the following:

     - *setUp*: Creates the temprorary directory that will house test output and
       data.   Also instantiates catching of output to both *stdout* and 
       *stderr*.  Finally, this method also calls *build_executable* which will
       call the local Makefile's build process via *make .exe*.
     - *runTest*: Actually runs the test calling the following functions by
       default:
        - *load_rundata(): Creates the *rundata* objects via the local 
          *setrun.py* file.  The resulting *rundata* object is stored in the 
          class attribute *rundata*.
        - *write_rundata_objects*: Writes out all the data objects found in the
          *rundata* class attribute.
        - *run_code*: Runs the simulation based on the *runclaw.py* script 
          (what *make output* usually calls) in a subprocess to preserve 
          parallelism.  Note that all output is redirected to the class 
          attributes *stderr* and *stdout*.
        - *check_gauges*: Default test check provided by this class.  Simply 
          checks the gauges recorded from the simulation that they are equal in
          sum to the default test data.
     - *tearDown*:  Closes output redirection and tests for success via the
       class attribute of a similar name.  If the tests were not successful the
       temporary directory contents is copied to the local directory.  The 
       temporary directory is removed at this point.


    """

    def __init__(self, methodName="runTest"):

        super(ClawpackRegressionTest, self).__init__(methodName=methodName)

        self.stdout = None
        self.stderr = None
        self.success = False
        self.remote_files = []
        self.temp_path = None
        self.test_path = os.path.dirname(inspect.getfile(self.__class__))
        if len(self.test_path) == 0:
             self.test_path = "./"
        self.rundata = None
        self.executable_name = None


    def get_remote_file(self, url, **kwargs):
        r"""Fetch file located at *url* and store in object's *temp_path*.

        Will check downloaded file's suffix to see if the file needs to be
        un-archived.

        """

        if self.temp_path is None:
            raise ValueError("Temporary data directory has not been ",
                             "set yet.  Try calling super before attempting ",
                             "to get remote files.")

        output_path = clawpack.clawutil.data.get_remote_file(url, 
                                                      output_dir=self.temp_path, 
                                                      **kwargs)
        self.remote_files.append(output_path)
        return output_path


    def setUp(self):
        r"""Create temp dir for data and setup log files.

        """
        
        self.temp_path = tempfile.mkdtemp()

        self.stdout = open(os.path.join(self.temp_path, "run_output.txt"), "w")
        self.stdout.write("Output from Test %s\n" % self.__class__.__name__)
        # TODO - Should change this to use the time module's formatting 
        # apparatus
        tm = time.localtime()
        year = str(tm[0]).zfill(4)
        month = str(tm[1]).zfill(2)
        day = str(tm[2]).zfill(2)
        hour = str(tm[3]).zfill(2)
        minute = str(tm[4]).zfill(2)
        second = str(tm[5]).zfill(2)
        date = 'Started %s/%s/%s-%s:%s.%s\n' % (year,month,day,hour,minute,second)
        self.stdout.write(date)
        self.stdout.write(("="*80 + "\n"))

        self.stderr = open(os.path.join(self.temp_path, "error_output.txt"), "w")
        self.stderr.write("Errors from Test %s\n" % self.__class__.__name__)
        self.stderr.write(date)
        self.stderr.write(("="*80 + "\n"))

        self.stdout.flush()
        self.stderr.flush()

        self.stdout.write("Paths:")
        self.stdout.write("  %s" % self.temp_path)
        self.stdout.write("  %s" % self.test_path)
        self.stdout.flush()
        # clean up *.o and *.mod files in test path
        for path in glob.glob(os.path.join(self.test_path,"*.o")):
            os.remove(path)
        for path in glob.glob(os.path.join(self.test_path,"*.mod")):
            os.remove(path)
        self.build_executable()


    def build_executable(self, executable_name="xclaw"):
        r"""Build executable by running `make .exe` in test directory.

        Moves the resulting executable to the temporary directory.


        """

        try:
            self.stdout.write("Test path and class info:\n")
            self.stdout.write("  class: %s\n" % str(self.__class__))
            self.stdout.write("  class file: %s\n" % str(inspect.getfile(self.__class__)))
            self.stdout.write("  test path: %s\n" % str(self.test_path))
            self.stdout.write("  temp path: %s\n" % str(self.temp_path))
            subprocess.check_call("cd %s ; make .exe" % self.test_path, 
                                                        stdout=self.stdout,
                                                        stderr=self.stderr,
                                                        shell=True)
        except subprocess.CalledProcessError as e:
            self.tearDown()
            raise e

        self.executable_name = executable_name
        shutil.move(os.path.join(self.test_path, self.executable_name),  
                    self.temp_path)


    def load_rundata(self):
        r"""(Re)load setrun module and create *rundata* object


        """

        if 'setrun' in sys.modules:
            del(sys.modules['setrun'])
        sys.path.insert(0, self.test_path)
        import setrun
        self.rundata = setrun.setrun()
        sys.path.pop(0)


    def write_rundata_objects(self, path=None):
        r"""Write out data in the *rundata* object to *path*

        Defaults to the temporary directory path *temp_path*.

        """

        if path is None:
            path = self.temp_path
        self.rundata.write(out_dir=path)


    def run_code(self):
        r"""Run test code given an already compiled executable"""

        runclaw.runclaw(xclawcmd=os.path.join(self.temp_path,self.executable_name),
                        rundir=self.temp_path,
                        outdir=self.temp_path,
                        overwrite=True,
                        restart=False,
                        xclawout=self.stdout,
                        xclawerr=self.stderr)
        
        self.stdout.flush()
        self.stderr.flush()


    def runTest(self, save=False, indices=(2, 3)):
        r"""Basic run test functionality

        Note that this stub really only runs the code and performs no tests.

        :Input:
         - *save* (bool) - If *True* will save the output from this test to 
           the file *regresion_data.txt*.  Passed to *check_gauges*.  Default is
           *False*.
         - *indices* (tuple) - Contains indices to compare in the gague 
           comparison and passed to *check_gauges*.  Defaults to *(2, 3)*.

        """

        # Write out data files
        self.load_rundata()
        self.write_rundata_objects()

        # Run code
        self.run_code()
        
        # Perform tests
        # Override this class to perform data checks, as is this class will
        # simply check that a test runs to completion

        # If we have gotten here then we do not need to copy the run results
        self.success = True

    
    def check_frame(self, save=False, indices=[0], frame_num=1,
                          file_name="regression_data.txt",
                          rtol=1e-14, atol=1e-08, tolerance=None):
        r"""Compare choosen frame to the comparison data

        :Input:
         - *save* (bool) - If *True* will save the output from this test to 
           the file *regresion_data.txt*.  Default is *False*.
         - *indices* (tuple) - Contains indices to compare in the gague 
           comparison.  Defaults to *(0)*.
         - *frame_num* (int) - Frame number to load from the run data.  Defaults
           to *1*. 
         - *regression_data_path* (path) - Path to the regression test data.
           Defaults to 'regression_data.txt'.
         - *rtol* (float) - Relative tolerance used in the comparison, default 
           is *1e-14*.  Note that the old *tolerance* input is now synonymous 
           with this parameter.
         - *atol* (float) - Absolute tolerance used in the comparison, default
           is *1e-08*.
        """

        if isinstance(tolerance, float):
            rtol = tolerance

        # Load test data
        data = solution.Solution(frame_num, path=self.temp_path)
        data_sum = []
        for index in indices:
            data_sum.append(data.q[index, ...].sum())
        
        # Get (and save) regression comparison data
        regression_data_file = os.path.join(self.test_path, "regression_data",
                                            file_name)
        if save:
            numpy.savetxt(regression_data_file, data_sum)
            claw_git_status.make_git_status_file(
                         outdir=os.path.join(self.test_path, "regression_data"))

        regression_sum = numpy.loadtxt(regression_data_file)

        assert numpy.allclose(data_sum, regression_sum, rtol=rtol, atol=atol), \
            "\n  new_data: %s, \n  expected: %s"  % (data_sum, regression_sum)


    def check_gauges(self, save=False, gauge_id=1, indices=[0],
                           rtol=1e-14, atol=1e-8, tolerance=None):
        r"""Basic test to assert gauge equality

        :Input:
         - *save* (bool) - If *True* will save the output from this test to 
           the file *regresion_data.txt*.  Default is *False*.
         - *indices* (tuple) - Contains indices to compare in the gague 
           comparison.  Defaults to *(0)*.
         - *rtol* (float) - Relative tolerance used in the comparison, default 
           is *1e-14*.  Note that the old *tolerance* input is now synonymous 
           with this parameter.
         - *atol* (float) - Absolute tolerance used in the comparison, default
           is *1e-08*.
        """

        if isinstance(tolerance, float):
            rtol = tolerance

        if not(isinstance(indices, tuple) or isinstance(indices, list)):
            indices = tuple(indices)

        # Get gauge data
        gauge = gauges.GaugeSolution(gauge_id, path=self.temp_path)

        # Get regression comparison data
        regression_data_path = os.path.join(self.test_path, "regression_data")
        if save:
            gauge_file_name = "gauge%s.txt" % str(gauge_id).zfill(5)
            shutil.copy(os.path.join(self.temp_path, gauge_file_name), 
                                                           regression_data_path)
            claw_git_status.make_git_status_file(outdir=regression_data_path)

        regression_gauge = gauges.GaugeSolution(gauge_id,
                                                path=regression_data_path)

        # Compare data
        try:
            for n in indices:
                numpy.testing.assert_allclose(gauge.q[n, :],
                                              regression_gauge.q[n, :], 
                                              rtol=rtol, atol=atol, 
                                              verbose=False)
        except AssertionError as e:
            err_msg = "\n".join((e.args[0], 
                                "Gauge Match Failed for gauge = %s" % gauge_id))
            err_msg = "\n".join((err_msg, "  failures in fields:"))
            failure_indices = []
            for n in indices:
                if ~numpy.allclose(gauge.q[n, :], regression_gauge.q[n, :], 
                                                          rtol=rtol, atol=atol):
                    failure_indices.append(str(n))
            index_str = ", ".join(failure_indices)
            raise AssertionError(" ".join((err_msg, index_str)))


    def tearDown(self):
        r"""Tear down test infrastructure.

        Closes *stdout* and *stderr*, removes the temporary directoy and if 
        *success* is *False*, copies the contents of the tempory directory to
        the current working directory.

        """
        self.stdout.close()
        self.stderr.close()

        if not self.success:
            output_dir = os.path.join(os.getcwd(),
                                         "%s_output" % self.__class__.__name__)

            # Remove directory if it exists already
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)

            # Copy out output files to local directory
            shutil.copytree(self.temp_path, output_dir)

        shutil.rmtree(self.temp_path)
        self.temp_path = None
