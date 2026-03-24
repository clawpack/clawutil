r"""
Utilities for regression testing Clawpack examples.

This module currently contains two testing interfaces:

1. ``ClawpackTestRunner``
   A lightweight pytest-oriented runner for new regression tests.  This is
   the preferred interface for new example tests.  It is designed to work
   naturally with pytest fixtures such as ``tmp_path`` and optional command
   line flags such as ``--save`` defined in ``conftest.py``.

2. ``ClawpackRegressionTest``
   The older unittest-based regression framework.  This remains available
   for compatibility with existing tests, but new tests should prefer
   ``ClawpackTestRunner``.

The intended workflow for new tests is:

- create a runner for a temporary output directory,
- load or modify ``rundata`` from a local ``setrun.py``,
- write data files into the temporary directory,
- build the example executable using the example ``Makefile``,
- run the code in the temporary directory,
- compare selected frames or gauges against saved regression data.

By default, regression data is stored in a ``regression_data/`` directory
next to the test file or example directory.

Notes
-----
- ``ClawpackTestRunner`` is designed for example-based regression tests,
  not as a general-purpose unit test framework for arbitrary solver
  internals.
- The runner intentionally exercises the normal example build workflow
  through ``make`` rather than bypassing it using the `make new` target.
- Temporary simulation output should be written to pytest-managed temporary
  directories such as ``tmp_path``.
"""

from pathlib import Path
import os
import sys
import subprocess
import importlib
import shutil
import inspect
import random
import string
from collections.abc import Iterable
from typing import Optional

import numpy as np

import clawpack.clawutil.runclaw as runclaw
import clawpack.clawutil.claw_git_status as claw_git_status
import clawpack.pyclaw.solution as solution
import clawpack.pyclaw.gauges as gauges


# Support for ClawpackRegressionTest
import tempfile
import unittest
import time
import glob

# TODO: Update documentation
class ClawpackTestRunner:
    r"""
    Helper for pytest-based Clawpack regression tests.

    Parameters
    ----------
    path : pathlib.Path
        Temporary directory used for generated data files, build products,
        executable placement, and simulation output.  In pytest-based tests
        this is typically the ``tmp_path`` fixture or a subdirectory of it.
    test_path : pathlib.Path, optional
        Directory containing the example under test.  This directory is used
        to locate the local ``Makefile``, the default ``setrun.py``, and the
        default ``regression_data/`` directory.  If not provided, the runner
        attempts to infer it from the calling test file.

    Attributes
    ----------
    temp_path : pathlib.Path
        Temporary working directory used by the test run.
    test_path : pathlib.Path
        Example or test directory containing the build and regression inputs.
    executable_name : str
        Name of the executable produced by the example ``Makefile``.
        Defaults to ``"xclaw"``.
    rundata : object
        Run-time data object returned by ``setrun.setrun()`` after
        :meth:`set_data` is called.

    Notes
    -----
    The runner is intentionally small.  It orchestrates the existing Clawpack
    example workflow rather than replacing it.  A typical test sequence is::

        runner = ClawpackTestRunner(tmp_path, test_path=Path(__file__).parent)
        runner.set_data()
        runner.write_data()
        runner.build_executable()
        runner.run_code()
        runner.check_frame(1)

    For new tests, prefer explicit setup in the test itself so that the test
    remains easy to read and modify.
    """

    def __init__(self, path: Path, test_path: Optional[Path]=None):
        r"""
        Initialize a regression test runner for a single example run.

        Parameters
        ----------
        path : pathlib.Path
            Temporary working directory for this test.
        test_path : pathlib.Path, optional
            Directory containing the example under test.  If omitted, the runner
            infers this from the calling test file.
        """

        self.temp_path = path
        # This works if the originating caller is in the right spot in the stack
        # If this is not the case, we provide a way to set it manually
        if test_path:
            self.test_path = test_path
        else:
            self.test_path = Path(Path(inspect.stack()[2].filename).absolute()
                                                                    ).parent
        self.executable_name = 'xclaw'

        # Do we want to set this?
        self.verbose = False


    def set_data(self, setrun_path: Optional[Path]=None):
        r"""
        Load ``rundata`` from a ``setrun.py`` file.

        Parameters
        ----------
        setrun_path : pathlib.Path, optional
            Path to the ``setrun.py`` file to import.  If omitted, the runner
            uses ``test_path / "setrun.py"``.

        Notes
        -----
        The ``setrun`` module is imported under a unique temporary module name
        so that multiple tests can load different ``setrun.py`` files in the
        same Python session without clashing in ``sys.modules``.

        After this method completes, the resulting run-time data object is
        available as ``self.rundata`` and may be modified by the test before
        calling :meth:`write_data`.
        """

        if not setrun_path:
            setrun_path = Path(self.test_path) / "setrun.py"

        mod_name = '_'.join(("setrun",
                             "".join(random.choices(string.ascii_letters
                                                    + string.digits, k=32))))
        spec = importlib.util.spec_from_file_location(mod_name, setrun_path)
        setrun_module = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = setrun_module
        spec.loader.exec_module(setrun_module)
        self.rundata = setrun_module.setrun()


    def write_data(self, path: Optional[Path]=None):
        r"""
        Write the current ``rundata`` object to disk.

        Parameters
        ----------
        path : pathlib.Path, optional
            Output directory for generated data files.  If omitted, data files
            are written to ``self.temp_path``.

        Notes
        -----
        This method expects :meth:`set_data` to have been called already.  Tests
        commonly modify values in ``self.rundata`` before calling this method in
        order to reduce run time or adjust output times for regression checks.
        """
        
        if not path:
            path = self.temp_path
        self.rundata.write(out_dir=path)


    def build_executable(self, make_level: str='new', 
                               FFLAGS: Optional[str]=None, 
                               LFLAGS: Optional[str]=None,
                               verbose: bool=False,
                               make_vars: Optional[dict[str, str]]=None):
        r"""
        Build the example executable using the local ``Makefile``.

        Parameters
        ----------
        make_level : {"new", "default", "exe"}, default "new"
            Build target to request from ``make``.

            - ``"new"``: request a fresh rebuild via ``make new``.
            - ``"default"``: remove local ``*.o`` and ``*.mod`` files in the
            example directory, then run ``make .exe``.
            - ``"exe"``: run ``make .exe`` directly.

            For regression tests, ``"new"`` is generally preferred because it
            makes build freshness explicit.
        FFLAGS : str, optional
            Fortran compiler flags to pass to ``make``.  If omitted, the runner
            uses the ``FFLAGS`` environment variable if it is set, and otherwise
            does not pass an explicit ``FFLAGS=...`` override.  This allows
            example-specific Makefiles to define or append their own defaults.
        LFLAGS : str, optional
            Linker flags to pass to ``make``.  If omitted, the runner uses the
            ``LFLAGS`` environment variable if it is set, and otherwise does not
            pass an explicit ``LFLAGS=...`` override.  This avoids clobbering
            Makefile-defined link settings such as LAPACK/BLAS additions.
        verbose : bool, default False
            If True, print the shell command before executing it.
        make_vars : dict of str to str, optional
            Additional variables to pass to the ``make`` command.

        Notes
        -----
        The build is performed in ``self.test_path`` using the example's own
        ``Makefile`` so that tests exercise the same build path used by normal
        example runs.

        When explicit ``FFLAGS`` or ``LFLAGS`` overrides are not supplied, the
        runner prefers to let the example ``Makefile`` control compiler and
        linker settings.  This is important for examples that add specialized
        libraries or append local build flags.

        After a successful build, the produced executable is moved from
        ``self.test_path`` into ``self.temp_path`` so that subsequent simulation
        output remains isolated from the source tree.

        Raises
        ------
        ValueError
            If ``make_level`` is not recognized.
        subprocess.CalledProcessError
            If the ``make`` command fails.
        """

        # Respect explicit arguments first, then environment variables, and
        # otherwise let the local Makefile provide its own defaults.
        if FFLAGS is None:
            FFLAGS = os.environ.get("FFLAGS")
        if LFLAGS is None:
            LFLAGS = os.environ.get("LFLAGS")

        if make_level.lower() == "new":
            make_target = "new"
        elif make_level.lower() == "default":
            # clean up *.o and *.mod files in test path only
            for path in self.test_path.glob("*.o"):
                path.unlink()
            for path in self.test_path.glob("*.mod"):
                path.unlink()
            make_target = ".exe"
        elif make_level.lower() == "exe":
            make_target = ".exe"
        else:
            raise ValueError(f"Invalid make_level={make_level} given.")

        cmd = ["make", make_target]
        if FFLAGS is not None:
            cmd.append(f"FFLAGS={FFLAGS}")
        if LFLAGS is not None:
            cmd.append(f"LFLAGS={LFLAGS}")

        if make_vars:
            for key, value in make_vars.items():
                cmd.append(f"{key}={value}")

        try:
            if verbose:
                print("Build command:", " ".join(str(part) for part in cmd))
                print("Build cwd:", self.test_path)
            subprocess.run(cmd, cwd=self.test_path, check=True)
        except subprocess.CalledProcessError as e:
            self.clean()
            raise e

        shutil.move(self.test_path / self.executable_name, self.temp_path)


    def run_code(self):
        r"""
        Run the compiled example in the temporary working directory.

        Notes
        -----
        This method uses :func:`clawpack.clawutil.runclaw.runclaw` to execute the
        compiled solver with:

        - ``xclawcmd`` set to the executable in ``self.temp_path``,
        - ``rundir`` set to ``self.temp_path``,
        - ``outdir`` set to ``self.temp_path``.

        As a result, both input data files and simulation output are kept in the
        temporary test directory rather than the source tree.

        This method expects :meth:`write_data` and :meth:`build_executable` to
        have been called already.
        """
        runclaw.runclaw(xclawcmd=self.temp_path / self.executable_name,
                        rundir=self.temp_path,
                        outdir=self.temp_path,
                        overwrite=True,
                        restart=False)

    def clean(self):
        r"""
        Clean up after a failed build or test run.

        Notes
        -----
        This method is currently a no-op and exists as an extension point for
        repository-specific runners.  Subclasses may override it to remove
        temporary files, preserve debugging artifacts, or perform other cleanup.
        """
        pass


    def check_frame(self, frame: int, indices: Iterable=(0,), 
                                      regression_path: Optional[Path]=None, 
                                      save: bool=False, **kwargs):        
        r"""
        Compare a computed solution frame against saved regression data.

        Parameters
        ----------
        frame : int
            Frame number to load from the simulation output in ``self.temp_path``.
        indices : iterable of int, default (0,)
            Indices of the ``q`` components to compare.  For each selected
            component, this method compares the sum of that component over the
            loaded frame.
        regression_path : pathlib.Path, optional
            Directory containing saved regression files.  If omitted, the default
            location is ``self.test_path / "regression_data"``.
        save : bool, default False
            If True, write the current frame summary to the regression file before
            comparing.  This is intended for intentional baseline creation or
            updates.
        **kwargs
            Additional keyword arguments passed to
            ``numpy.testing.assert_allclose``.  By default, ``rtol=1e-14`` and
            ``atol=1e-8``.

        Notes
        -----
        Regression data is stored in files named ``frameNNNN.txt`` where ``NNNN``
        is the zero-padded frame number.

        The current comparison metric is deliberately lightweight: it compares
        sums of selected solution components rather than the full solution array.
        This keeps regression files small and reviewable, while still detecting
        many unintended numerical changes.

        If ``save`` is True, the regression directory is created if necessary and
        a git-status metadata file is also written via
        ``claw_git_status.make_git_status_file``.
        """

        if not regression_path:
            regression_path = self.test_path / "regression_data"

        # Load test output data
        sol = solution.Solution(frame, path=self.temp_path)
        sol_sums = [sol.q[i, ...].sum() for i in indices]

        # Load regression data
        regression_data = regression_path / f"frame{str(frame).zfill(4)}.txt"
        if save:
            if not regression_data.parent.exists():
                regression_data.parent.mkdir(parents=True)
            np.savetxt(regression_data, sol_sums)
            claw_git_status.make_git_status_file(outdir=regression_path)
        regression_sum = np.loadtxt(regression_data)

        # Compare data
        kwargs.setdefault('rtol', 1e-14)
        kwargs.setdefault('atol', 1e-8)
        np.testing.assert_allclose(sol_sums, regression_sum, **kwargs)


    def check_gauge(self, gauge_id: int, 
                          indices: Iterable=(0,), 
                          regression_path: Optional[Path]=None, 
                          save: bool=False, **kwargs):
        r"""
        Compare a computed gauge record against saved regression data.

        Parameters
        ----------
        gauge_id : int
            Gauge number to load from the simulation output in ``self.temp_path``.
        indices : iterable of int, default (0,)
            Indices of the gauge solution components to compare.
        regression_path : pathlib.Path, optional
            Directory containing saved regression gauge files.  If omitted, the
            default location is ``self.test_path / "regression_data"``.
        save : bool, default False
            If True, copy the generated gauge file into ``regression_path`` before
            comparing.  This is intended for intentional baseline creation or
            updates.
        **kwargs
            Additional keyword arguments passed to
            ``numpy.testing.assert_allclose``.  By default, ``rtol=1e-14`` and
            ``atol=1e-8``.

        Notes
        -----
        This method compares the full time series for each selected gauge field,
        not just an aggregate summary.

        The generated gauge file is expected to have the standard Clawpack name
        ``gaugeNNNNN.txt`` where ``NNNNN`` is the zero-padded gauge number.

        Raises
        ------
        AssertionError
            If the computed gauge is empty, if the computed and regression gauges
            have different shapes, or if any selected component differs beyond the
            requested tolerances.
        """

        if not(isinstance(indices, tuple) or isinstance(indices, list)):
            indices = tuple(indices)

        if not regression_path:
            regression_path = self.test_path / "regression_data"

        # Load test output data
        gauge = gauges.GaugeSolution(gauge_id, path=self.temp_path)
        if gauge.q.shape[1] == 0:
            raise AssertionError(f"Empty gauge {gauge_id}.")

        # Load regression data
        if save:
            if not regression_path.exists():
                regression_path.mkdir(parents=True)
            shutil.copy(self.temp_path / f"gauge{str(gauge_id).zfill(5)}.txt",
                        regression_path)
            claw_git_status.make_git_status_file(outdir=regression_path)
        regression_gauge = gauges.GaugeSolution(gauge_id, path=regression_path)

        if gauge.q.shape[1] != regression_gauge.q.shape[1]:
            raise AssertionError( "Gauges have different sizes, regression" + 
                                 f" gauge = {regression_gauge.q.shape}, " +
                                 f"test gauge = {gauge.q.shape}")

        # Compare data
        kwargs.setdefault('rtol', 1e-14)
        kwargs.setdefault('atol', 1e-8)
        try:
            for n in indices:
                np.testing.assert_allclose(gauge.q[n, :],
                                              regression_gauge.q[n, :],
                                              **kwargs)
        except AssertionError as e:
            err_msg = "\n".join((e.args[0],
                                "Gauge Match Failed for gauge = %s" % gauge_id))
            err_msg = "\n".join((err_msg, "  failures in fields:"))
            failure_indices = []
            for n in indices:
                if not np.allclose(gauge.q[n, :], regression_gauge.q[n, :],
                                **kwargs):
                    failure_indices.append(str(n))
            index_str = ", ".join(failure_indices)
            raise AssertionError(" ".join((err_msg, index_str)))


# NOTE: The following class is the old unittest-based regression test framework.
# It is still available for compatibility with existing tests, but new tests
# should prefer the ClawpackTestRunner
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
            np.savetxt(regression_data_file, data_sum)
            claw_git_status.make_git_status_file(
                         outdir=os.path.join(self.test_path, "regression_data"))

        regression_sum = np.loadtxt(regression_data_file)

        assert np.allclose(data_sum, regression_sum, rtol=rtol, atol=atol), \
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
                np.testing.assert_allclose(gauge.q[n, :],
                                              regression_gauge.q[n, :],
                                              rtol=rtol, atol=atol,
                                              verbose=False)
        except AssertionError as e:
            err_msg = "\n".join((e.args[0],
                                "Gauge Match Failed for gauge = %s" % gauge_id))
            err_msg = "\n".join((err_msg, "  failures in fields:"))
            failure_indices = []
            for n in indices:
                if not np.allclose(gauge.q[n, :], regression_gauge.q[n, :],
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
