
"""
Set up the plot figures, axes, and items to be done for each frame.

This module is imported by the plotting routines and then the
function setplot is called to set the plot parameters.

This setplot will be read in by clawmultip_tools.set_plotdata_params
and called with a different case dictionary of data for each case.

Note: this version has case as a parameter to setplot, a dictionary used to pass
in values that vary from case to case for doing a parameter sweep.
"""


#--------------------------
def setplot(plotdata=None, case={}):
#--------------------------

    """
    Specify what is to be plotted at each frame.
    Input:  plotdata, an instance of clawpack.visclaw.data.ClawPlotData.
    Output: a modified version of plotdata.

    """
    import os
    from clawpack.clawutil.data import ClawData

    # The values below are expected to be in case dictionary,
    # and may vary from case to case:

    outdir = case['outdir']  # required to read proper setprob.data
    case_name = case['case_name']  # used in plot title


    if plotdata is None:
        from clawpack.visclaw.data import ClawPlotData
        plotdata = ClawPlotData()

    plotdata.clearfigures()  # clear any old figures,axes,items data

    probdata = ClawData()
    setprob_file = os.path.join(outdir, 'setprob.data')
    print('Reading setprob data from %s' % setprob_file)
    probdata.read(setprob_file, force=True)
    print("Parameters: u = %g, beta = %g" % (probdata.u, probdata.beta))

    def qtrue(x,t):
        """
        The true solution, for comparison.
        Should be consistent with the initial data specified in qinit.f90.
        """
        from numpy import mod, exp, where, logical_and
        x0 = x - probdata.u*t
        x0 = mod(x0, 1.)   # because of periodic boundary conditions
        q = exp(-probdata.beta * (x0-0.75)**2)
        q = where(logical_and(x0 > 0.1, x0 < 0.4), q+1, q)
        return q

    # Figure for q[0]
    plotfigure = plotdata.new_plotfigure(name='Pressure and Velocity', figno=1)

    # Set up for axes in this figure:
    plotaxes = plotfigure.new_plotaxes()
    plotaxes.xlimits = 'auto'
    plotaxes.ylimits = [-.5,1.3]

    plotaxes.title = '%s\n q' % case_name  # Requires passing in case

    # Set up for item on these axes:
    plotitem = plotaxes.new_plotitem(plot_type='1d_plot')
    plotitem.plot_var = 0
    plotitem.plotstyle = '-o'
    plotitem.color = 'b'

    # Plot true solution for comparison:
    def plot_qtrue(current_data):
        from pylab import plot, legend
        x = current_data.x
        t = current_data.t
        q = qtrue(x,t)
        plot(x,q,'r',label='true solution')
        legend()

    plotaxes.afteraxes = plot_qtrue



    # Parameters used only when creating html and/or latex hardcopy
    # e.g., via clawpack.visclaw.frametools.printframes:

    plotdata.printfigs = True                # print figures
    plotdata.print_format = 'png'            # file format
    plotdata.print_framenos = 'all'          # list of frames to print
    plotdata.print_fignos = 'all'            # list of figures to print
    plotdata.html = True                     # create html files of plots?
    plotdata.html_homelink = '../README.html'
    plotdata.latex = True                    # create latex file of plots?
    plotdata.latex_figsperline = 2           # layout of plots
    plotdata.latex_framesperline = 1         # layout of plots
    plotdata.latex_makepdf = False           # also run pdflatex?
    plotdata.parallel = False                # make multiple frame png's at once

    return plotdata
