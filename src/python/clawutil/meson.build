package = 'clawpack.clawutil'
pkg_dir = join_paths(package.split('.'))

python_sources = [
  '__init__.py',
  'b4run.py',
  'chardiff.py',
  'clawcode2html.py',
  'claw_git_status.py',
  #'conversion/convert43to46.py',
  #'conversion/convert46to50.py',
  #'conversion/permute.py',
  'conversion/pyclaw/data.py',
  'conversion/pyclaw/__init__.py',
  #'conversion/setrun_template_amrclaw_2d.py',
  #'conversion/setrun_template_classic_1d.py',
  #'conversion/setrun_template_classic_2d.py',
  #'conversion/setrun_template_classic_3d.py',
  #'conversion/setrun_template_geoclaw_2d_shallow.py',
  'convert_readme.py',
  'data.py',
  'git.py',
  'imagediff.py',
  'make_all.py',
  'nbtools.py',
  'regression_tests.py',
  'runclaw.py',
  'setenv.py',
  'test.py',
  'whichclaw.py',
]

py.install_sources(
  python_sources,
  subdir: pkg_dir,
)
