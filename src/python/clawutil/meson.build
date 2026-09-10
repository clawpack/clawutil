package = 'clawpack.clawutil'
pkg_dir = join_paths(package.split('.'))

python_sources = [
  '__init__.py',
  'b4run.py',
  'chardiff.py',
  'clawcode2html.py',
  'claw_git_status.py',
  'clawmultip_tools.py',
  # convert_readme.py is deliberately not installed: its body runs at import
  # (it reads README.rst from the working directory, or calls sys.exit), so it
  # cannot be used as a module.  Makefile.common, apps/notebooks/Makefile and
  # doc's application_documentation.rst all invoke it by $CLAW path instead.
  'data.py',
  'git.py',
  'imagediff.py',
  'make_all.py',
  'multip_tools.py',
  'nbtools.py',
  'regression_tests.py',
  'runclaw.py',
  'run_examples.py',
  'setenv.py',
  'test.py',
  'util.py',
  'whichclaw.py',
]

py.install_sources(
  python_sources,
  subdir: pkg_dir,
)
