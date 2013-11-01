
from docutils.core import publish_string
import glob, os

html_string=publish_string(open('README.rst').read(),writer_name='html')

make_files = glob.glob("Makefile")
f_files = glob.glob("*.f") + glob.glob("*.f90")
py_files = glob.glob("*.py")
m_files = glob.glob("*.m")
out_dirs = glob.glob("_out*")
plot_dirs = glob.glob("_plot*")


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
        print "*** No _PlotIndex.html in ",f


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
<p>
%s
</ul>
</body>
</html>
""" % (make_text,f_text,py_text,m_text,out_text,plot_text)

html_string = html_string.replace("</body>\n</html>",new_text)

open('README.html','w').write(html_string)

