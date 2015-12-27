
def test():
    try:
        import pandas as pd
    except:
        print "*** could not import pandas"

    gdata = pd.read_csv('data/fort.gauge',delim_whitespace=True,header=None)
    assert gdata.shape == (1365,7), '*** gdata.shape = %s' % str(gdata.shape)

