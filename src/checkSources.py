#quick script to consolidate common and custom sources
#If a custom file has the same name as a common file, the common one is excluded.
#Exclusions can also be manually set for replacement files with different names

import sys
import os


#extract just the file name
def get_name(filedir):
	return str(filedir).split('/')[-1]


#first, make arrays for sources
sources=[]
s_names=[]

all_sources=list(sys.argv)
all_sources.pop(0)
mode=0
for arg in all_sources:
	if(arg==";"):
		mode+=1
		continue
	
	#common file
	if mode==0:
		sources.append(arg)
		s_names.append(get_name(arg))
	
	#overwritten file
	else:
		exname=get_name(arg)
		#check if there is a file to replace
		if exname in s_names:
			ind=s_names.index(exname)
			sources.pop(ind)
			s_names.pop(ind)
		
		#custom file
		if mode==2:
			sources.append(arg)
			s_names.append(get_name(arg))

#return the consolidated source list
out=""
for source in sources:
	out+=" "+source
print out
