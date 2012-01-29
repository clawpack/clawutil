import sys,os

def chardiff_file(fname1, fname2, print_all_lines=True, hfile1='', \
                  hfile2='', verbose=True):

    # html files to create:
    if hfile1 == "": hfile1 = "diff_all_lines.html"
    if hfile2 == "": hfile2 = "diff_changed_lines.html"

    f1 = open(fname1,'r').readlines()
    f2 = open(fname2,'r').readlines()

    if (len(f1) != len(f2)) and verbose:
        print "*** files have different number of lines"
    flen = min(len(f1), len(f2))
    
    table1 = []
    table2 = []
    linenos = []
    changed = []
    
    for i in range(flen):
        line1 = f1[i].replace("\n","")
        line2 = f2[i].replace("\n","")
        badline = False
        if line1==line2:
            line_changed = False
        else:
            line_changed = True
            len_line = max(len(line1),len(line2))
            if (len(line1)<len_line):
                badline = True  # signal break after this line
                line1 = line1.ljust(len_line)  # pad the line
            if (len(line2)<len_line):
                badline = True  # signal break after this line
                line2 = line2.ljust(len_line)  # pad the line

            toggle = []   # keep track of where switch between 
                          # matching and not matching sections
            same = True
            for j in range(len_line):
                if (same and (line1[j] != line2[j])) or \
                      ((not same) and (line1[j] == line2[j])):
                    same = not same
                    toggle.append(j)

            if len(toggle)==0:
                print "*** Error: toggle should be nonempty"
                print "*** Aborting"
                raise Exception()
    
        if print_all_lines and (not line_changed):
            changed.append(False)
            table1.append(line1)
            table2.append(line2)
            linenos.append(i)
        elif line_changed:
            changed.append(True)
            table1line = ""
            table2line = ""
            badline = False
            same = True
            for k in range(len(toggle)+1):
                if k==0:
                    j1 = 0
                    j2 = toggle[0]
                else:
                    j1 = toggle[k-1]
                    if k<len(toggle):
                        j2 = toggle[k]
                    else:
                        j2 = len_line+1
                if same:
                    table1line = table1line + line1[j1:j2]
                    table2line = table2line + line2[j1:j2]
                else:
                    table1line = table1line + \
                           "<span class=yellow>%s</span>" % line1[j1:j2]
                    table2line = table2line + \
                           "<span class=yellow>%s</span>" % line2[j1:j2]
                same = (not same)
            table1.append(table1line)
            table2.append(table2line)
            linenos.append(i)

            # Maybe better not break, might want remainder of file too...
            #if badline: break

    numchanges = sum(changed)

    html = open(hfile1,"w")
    if verbose:
        print "Point your browser to: "
        print "  all %s lines with diffs: %s" % (flen, hfile1)
    hf2 = os.path.split(hfile2)[1]
    html.write("""
        <html>
        <style>
        span.yellow { background-color: yellow; }
        span.red { background-color: #ff8888; }
        span.green { background-color: #88ff88; }
        </style>
        <h2>All %s lines of files with highlighted diffs on %s lines</h2>
        <h3>
        See also: <a href="%s">Only changed lines</a>
        </h3>
        <table style="border-collapse: collapse; padding: 50px;">
        <col span="3" style="padding: 50px; background-color: #FFFFFF;
        border: 2px solid #000000;" />\n""" % (flen,numchanges,hf2))
    html.write("<td></td><td><b>%s&nbsp;&nbsp;</b></td><td><b>%s&nbsp;&nbsp;</b></td></tr>\n" \
                % (os.path.abspath(fname1),os.path.abspath(fname2))) 
    html.write("<tr><td></td><td>__________________</td><td>__________________</td></tr>\n") 

    for i in range(len(table1)):
        if changed[i]:
            html.write("<tr><td><span class=red>Line %s</span></td>" \
                 % (linenos[i]+1))
        else:
            html.write("<tr><td><span class=green>Line %s</span></td>" \
                 % (linenos[i]+1))
        html.write("<td>%s</td><td>%s</td></tr>\n" % (table1[i],table2[i]))

    html.write("</table>\n")
    #if badline:
        #html.write("<h2>Files disagree after this point --- truncated</h2>\n")
    html.write("</html>\n""")
    html.close()
       
    # Only changed lines:
    
    html = open(hfile2,"w")
    if verbose:
        print "  only %s lines with changes: %s" % (numchanges, hfile2)
    hf1 = os.path.split(hfile1)[1]
    html.write("""
        <html>
        <style>
        span.yellow { background-color: yellow; }
        span.red { background-color: #ff8888; }
        span.green { background-color: #88ff88; }
        </style>
        <h2>Displaying only changed lines of files (%s out of %s lines)</h2>
        <h3>
        See also: <a href="%s">All lines with diffs highlighted </a>
        </h3>
        <table style="border-collapse: collapse; padding: 50px;">
        <col span="3" style="padding: 50px; background-color: #FFFFFF;
        border: 2px solid #000000;" />\n""" % (numchanges,flen,hf1))
    html.write("<td></td><td><b>%s&nbsp;&nbsp;</b></td><td><b>%s&nbsp;&nbsp;</b></td></tr>\n" \
                % (os.path.abspath(fname1),os.path.abspath(fname2))) 
    html.write("<tr><td></td><td>__________________</td><td>__________________</td></tr>\n") 

    for i in range(len(table1)):
        if changed[i]:
            html.write("<tr><td><span class=red>Line %s</span></td>" \
                 % (linenos[i]+1))
            html.write("<td>%s</td><td>%s</td></tr>\n" % (table1[i],table2[i]))

    html.write("</table>\n")
    #if badline:
        #html.write("<h2>Files disagree after this point --- truncated</h2>\n")
    html.write("</html>\n""")
    html.close()
    return numchanges
    
    

def chardiff_dir(dir1, dir2, file_pattern='all', dir3="diff_dir", overwrite=False, print_all_lines=True):
    """
    Run chardiff_file on all common files between dir1 and dir2 that match the patterns in the
    list files.
    """
    import filecmp, glob
    
    # Construct sorted list of files matching in either or both directories:
    if file_pattern=='all':
        files_both = os.listdir(dir1) + os.listdir(dir2)
    else:
        file_pattern = list(file_pattern)  # in case it was a single pattern
        files1 = []
        files2 = []
        for pattern in file_pattern:
            files1p = glob.glob("%s/%s" % (dir1,pattern))
            files1p = [f.replace(dir1+'/','') for f in files1p]
            files2p = glob.glob("%s/%s" % (dir2,pattern))
            files2p = [f.replace(dir2+'/','') for f in files2p]
            files1 = files1 + files1p
            files2 = files2 + files2p
        files_both = files1 + files2
    files = []
    for f in files_both:
        if f not in files: files.append(f)
    files.sort()
    

    print "Comparing files in the  directory: ", dir1
    print "               with the directory: ", dir2
    
    if os.path.isdir(dir3):
        if (len(os.listdir(dir3)) > 0)  and (not overwrite):
            ans = raw_input("Ok to overwrite files in %s ?  " % dir3)
            if ans.lower() not in ['y','yes']:
                print "*** Aborting"
                return
    else:
        os.system('mkdir -p %s' % dir3)
            
    hfile = open(dir3+'/diff.html','w')
    hfile.write("""<html>
            <h1>Directory comparison</h1>
            Comparing files in the directory: &nbsp; dir1 = %s<br>
            with the directory: &nbsp; dir2 = %s<p>
            Matching the pattern: %s<p>
            &nbsp;<p>
            <h2>Files:</h2>
            <ul>
            """ % (dir1,dir2,file_pattern))
                    
    f_equal, f_diff, f_other = filecmp.cmpfiles(dir1,dir2,files,False)
    
    for f in files:
        hfile.write("<li> <b>%s:</b> &nbsp; " % f)
        if f not in files2:
            hfile.write("Only appears in dir1\n")
        elif f not in files1:
            hfile.write("Only appears in dir2\n")
        elif f in f_equal:
            hfile.write("Are identical in dir1 and dir2\n")
        else:
            hfile1 = "%s_diff_all_lines.html" % f
            hfile2 = "%s_diff_changed_lines.html" % f
            
            numchanges = chardiff_file(os.path.join(dir1,f), \
                    os.path.join(dir2,f), \
                    hfile1=os.path.join(dir3,hfile1), \
                    hfile2=os.path.join(dir3,hfile2), verbose=False)
                          
            hfile.write("""Differ on %s lines, 
                    view <a href="%s">these lines</a> or
                    <a href="%s">all lines</a>\n""" \
                    % (numchanges, hfile2,hfile1))

    hfile.write("</ul>\n</html>\n")
        
        
        
    print "To view diffs, open the file ",dir3+'/diffs.html'
    
       
if __name__=="__main__":
    args = sys.argv[1:]
    highlight_diffs_html(*args)
            
            
