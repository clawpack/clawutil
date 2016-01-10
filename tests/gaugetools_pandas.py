
"""
Gauge tools using Pandas
"""

def split_fort_gauge(outdir='_output', verbose=True):
    """
    Read fort.gauge file from outdir and split up into separate fort.g files 
    for each each.  For backward compatibility.
    """

    import numpy
    import os

    fname = os.path.join(outdir, 'fort.gauge')
    try:
        data = numpy.loadtxt(fname)
    except:
        if verbose:
            print "*** No gauge data found in %s" % fname
        return None

    gauge_numbers = numpy.array(data[:, 0], dtype=int) 
    gaugenos = list(set(gauge_numbers))   # list of unique numbers

    # Create a new file for each gauge:

    for gaugeno in gaugenos:
        gauge_indices = numpy.nonzero(gauge_numbers == gaugeno)[0]
        gdata = data[gauge_indices,:]  # only the rows for this gaugeno
        gdata = gdata[:,1:]  # omit first column, the gauge number
        ncols = gdata.shape[1]
        gfile = os.path.join(outdir, 'fort.g%s' % str(gaugeno).zfill(5))
        with open(gfile, 'w') as outfile:
            format = (ncols-1) * "  %17.10e"
            format = "%4i" + format + "\n"
            for k in range(gdata.shape[0]):
                outfile.write(format % tuple(gdata[k,:]))
            
        if verbose:
            print "Created ",gfile

def read_gauge(gaugeno, outdir='_output', column_names=None, 
               datetime_origin = None, verbose=True):

    import pandas as pd
    import datetime
    import os

    gfile = os.path.join(outdir, 'fort.g%s' % str(gaugeno).zfill(5))

    if column_names == 'geoclaw':
        column_names = ['level', 'time', 'h', 'hu', 'hv', 'eta']

    try:
        gdata = pd.read_csv(gfile, delim_whitespace=True, names=column_names,
                            header=None)
    except:
        raise IOError("*** problem reading %s" % gfile)

    if column_names is None:
        ncols = gdata.shape[1]
        column_names = ['level', 'time']
        for ivar in range(ncols-2):
            column_names.append('q%s' % str(ivar).zfill(2))
        gdata.columns = column_names

    if datetime_origin is not None:
        time_since_origin = [datetime_origin + \
            datetime.timedelta(seconds=s) for s in gdata['time']]
        gdata['datetime'] = time_since_origin

    return gdata

        

    
