
from __future__ import absolute_import
from __future__ import print_function
import glob, os, sys

try:
    from docutils.core import publish_string
except:
    print('*** Install docutils to convert README.rst')
    sys.exit(0)

if not os.path.isfile('README.rst'):
    print('*** README.rst file not found in %s' % os.getcwd())
    sys.exit()

if (sys.version_info > (3,0)):
    html_string=publish_string(open('README.rst').read(),writer_name='html',
                settings_overrides={'output_encoding': 'unicode'})
else:
    html_string=publish_string(open('README.rst').read(),writer_name='html')

make_files = glob.glob("Makefile")
f_files = glob.glob("*.f") + glob.glob("*.f90")
py_files = glob.glob("*.py")
m_files = glob.glob("*.m")
out_dirs = glob.glob("_out*")   # not currently listed on html page
plot_dirs = glob.glob("_plots") # for gallery -- want only main _plots
#plot_dirs = glob.glob("_plot*")   # might want to list other plot directories


make_text = "\n"
for f in make_files:
    flink = f + '.html'
    if not os.path.isfile(flink): flink = f
    make_text = make_text + '<li><a href="%s">%s</a>\n' % (flink,f)

f_text = "\n"
for f in f_files:
    flink = f + '.html'
    if not os.path.isfile(flink): flink = f
    f_text = f_text + '<li><a href="%s">%s</a>\n' % (flink,f)

py_text = "\n"
for f in py_files:
    flink = f + '.html'
    if not os.path.isfile(flink): flink = f
    py_text = py_text + '<li><a href="%s">%s</a>\n' % (flink,f)

m_text = "\n"
for f in m_files:
    flink = f + '.html'
    if not os.path.isfile(flink): flink = f
    m_text = m_text + '<li><a href="%s">%s</a>\n' % (flink,f)

out_text = "\n"
for f in out_dirs:
    out_text = out_text + '<li><a href="%s">%s</a>\n' % (f,f)

plot_text = "\n"
for f in plot_dirs:
    if os.path.isfile("%s/_PlotIndex.html" % f):
        plot_text = plot_text + '<li><a href="%s/_PlotIndex.html">%s</a>\n' % (f,f)
    else:
        print("*** No _PlotIndex.html in ",f)


new_text = """
<h2>Files</h2>
<ul>
%s
<p>
%s
<p>
%s
<p>
%s
<p>
%s
</ul>
<p>
""" % (make_text,f_text,py_text,m_text,plot_text)

# If README.rst contains a section labelled "Version", insert the list of
# files before this section.  Otherwise put list of files at end...

version_loc = html_string.find(r"<h1>Version</h1>")
end_body = html_string.find(r"</body>\n</html>")

if version_loc > -1:
    html_string = html_string[:version_loc] + new_text + html_string[version_loc:]
else:
    html_string = html_string[:end_body] + new_text + html_string[end_body:]

# Adjust size of section heading:
html_string = html_string.replace(r'<h1>Version</h1>','<h2>Version</h2>')

# Fix head for Clawpack style:
head_text = """
<link rel="icon" href="http://www.clawpack.org/clawicon.ico" />
</head>
<body BGCOLOR="#FFFFE8" LINK="#7F0000" VLINK="#7F0000">
<font FACE="TREBUCHET MS,HELVETICA,ARIAL">
<a href="http://www.clawpack.org">
<IMG SRC="http://www.clawpack.org/clawlogo.jpg" WIDTH="200" HEIGHT="70" 
VSPACE="0" HSPACE="0" ALT="CLAWPACK" BORDER="0" LOOP="0"> </a>
"""

i1 = html_string.find(r'</head>')
i2 = i1+15

html_string = html_string[:i1] + head_text + html_string[i2:]

open('README.html','w').write(html_string)

