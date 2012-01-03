#
#       Makefile for the clawpack code:
#
#       For this help summary, type:              make help
#
#       To make all object files, type:           make .objs
#
#       To compile a single file.f:               make file.o
#
#       To make the executable, type:             make .exe
#
#       To make data files by running 
#       setrun.py:                                make .data
#
#       To make and run code putting results
#       in subdirectory named output:             make .output
#
#       To make and run code and then plot        
#       results from subdirectory output
#       into subdirectory named plots:            make .plots
#
#       To make a single program file from all
#       sources and library source files:         make .program
#
#       To create html files from the program
#       and data files using clawcode2html:       make .htmls
#
#       To clean up files created by make:        make clean
#       Deletes *.o, x*, .htmls
#
#       To clean up output and graphics files:    make clobber
#

# Fortran compiler:  FC may be set as an environment variable or in make
# file that 'includes' this one.
FC ?= gfortran
LINK ?= $(FC)

# Flags for compiling and linking:
FFLAGS ?=  
LFLAGS ?= $(FFLAGS)

# Path to version of python to use:  May need to use something other than
# the system default in order for plotting to work.  Can set PY as
# environment variable or in make file that 'includes' this one.
PY ?= python
PYTHON = $(PY)


# Targets that do not correspond to file names:
.PHONY: .objs .exe clean clobber new all output plots;

# Variables below should be set in Makefile that "includes" this one.
# Default values if not set:
CLAW_EXE ?= xclaw
CLAW_PKG ?= classic
CLAW_OUTDIR ?= _output
CLAW_PLOTDIR ?= _plots
CLAW_INCLUDE ?= 
CLAW_LIB ?= $(CURDIR)/
CLAW_OVERWRITE ?= True
CLAW_RESTART ?= False


#----------------------------------------------------------------------------

# how to make .o files from .f files:
.SUFFIXES:
.SUFFIXES: .f90 .f .mod .o
%.o : %.f90 $(CLAW_INCLUDE) ; $(FC) -c -I$(CLAW_LIB) $< -o $@ $(FFLAGS)
%.o : %.f $(CLAW_INCLUDE) ; $(FC) -c -I$(CLAW_LIB) $< -o $@ $(FFLAGS) 

# make list of .o files required from the sources above:
CLAW_OBJECTS = $(subst .f,.o, $(subst .f90,.o, $(CLAW_SOURCES)))
CLAW_LIBOBJECTS = $(subst .f,.o, $(subst .f90,.o, $(CLAW_LIBSOURCES)))

#----------------------------------------------------------------------------
# Executable:

.objs: $(CLAW_OBJECTS) $(CLAW_LIBOBJECTS) ;


$(CLAW_EXE): $(CLAW_LIBOBJECTS) $(CLAW_OBJECTS) $(MAKEFILE_LIST);
	$(LINK) $(LFLAGS) $(CLAW_OBJECTS) $(CLAW_LIBOBJECTS) -o $(CLAW_EXE)

.exe: $(CLAW_EXE) ;

#----------------------------------------------------------------------------

# Command to create *.html files from *.f etc:
CC2HTML = $(PYTHON) $(CLAW)/doc/clawcode2html.py --force 

# make list of html files to be created by 'make .htmls':
HTML = \
  $(subst .f,.f.html,$(wildcard *.f)) \
  $(subst .f95,.f95.html,$(wildcard *.f95)) \
  $(subst .f90,.f90.html,$(wildcard *.f90)) \
  $(subst .m,.m.html,$(wildcard *.m)) \
  $(subst .py,.py.html,$(wildcard *.py)) \
  $(subst .data,.data.html,$(wildcard *.data)) \
  $(subst .txt,.html,$(wildcard *.txt)) \
  $(subst .sh,.sh.html,$(wildcard *.sh)) \
  Makefile.html

# Rules to make html files:  
# e.g. qinit.f --> qinit.f.html
%.f.html : %.f ; $(CC2HTML) $<              
%.f95.html : %.f95 ; $(CC2HTML) $<
%.f90.html : %.f90 ; $(CC2HTML) $<
%.m.html : %.m ; $(CC2HTML) $<
%.py.html : %.py ; $(CC2HTML) $<
%.data.html : %.data ; $(CC2HTML) $<
%.sh.html : %.sh ; $(CC2HTML) $<
Makefile.html : Makefile ; $(CC2HTML) $<    
# drop .txt extension, e.g. README.txt --> README.html
%.html : %.txt ; $(CC2HTML) --dropext $<    

.htmls: $(HTML) ;

#----------------------------------------------------------------------------

# Make data files needed by Fortran code:
.data: $(CLAW_setrun_file) $(MAKEFILE_LIST) ;
	$(PYTHON) $(CLAW_setrun_file) $(CLAW_PKG)
	touch .data

#----------------------------------------------------------------------------
# Run the code and put fort.* files into subdirectory named output:
# runclaw will execute setrun.py to create data files and determine
# what executable to run, e.g. xclaw or xamr.
.output: $(CLAW_EXE) .data $(MAKEFILE_LIST);
	@echo $(CLAW_OUTDIR) > .output
	$(PYTHON) $(CLAW)/clawutil/src/python/runclaw.py  $(CLAW_EXE) $(CLAW_OUTDIR) $(CLAW_OVERWRITE) $(CLAW_RESTART)

#----------------------------------------------------------------------------
# Run the code without checking dependencies:
output: 
	$(PYTHON) $(CLAW)/clawutil/src/runclaw.py  $(CLAW_EXE) $(CLAW_OUTDIR) $(CLAW_OVERWRITE) $(CLAW_RESTART)

#----------------------------------------------------------------------------

# Python command to create plots:
# Environment variable COMSPEC is only defined on Windows -- 
#   in which case assume Cygwin is being used an use Windows version of
#   Python which should have matplotlib (e.g. via EPD)
ifdef COMSPEC   
  PLOTCMD := C:\Python25\python.exe C:\cygwin$(CLAW)\python\pyclaw\plotters\plotclaw.py
else
  PLOTCMD := $(PYTHON) $(CLAW)/python/pyclaw/plotters/plotclaw.py
endif

# Rule to make the plots into subdirectory specified by CLAW_PLOTDIR,
# using data in subdirectory specified by CLAW_OUTDIR and the plotting
# commands specified in CLAW_setplot_file.

.plots: .output $(CLAW_setplot_file) $(MAKEFILE_LIST) ;
	$(PLOTCMD) $(CLAW_OUTDIR) $(CLAW_PLOTDIR) $(CLAW_setplot_file)
	@echo $(CLAW_PLOTDIR) > .plots

# Make the plots without checking dependencies:
plots:
	$(PLOTCMD) $(CLAW_OUTDIR) $(CLAW_PLOTDIR) $(CLAW_setplot_file)

#----------------------------------------------------------------------------

# Rule to make full program by catenating all source files.
# Sometimes useful for debugging:

.program: $(CLAW_SOURCES) $(CLAW_LIBSOURCES) $(CLAW_INCLUDE) $(MAKEFILE_LIST);
	cat $(CLAW_SOURCES) $(CLAW_LIBSOURCES) $(CLAW_INCLUDE) > claw_program.f
	touch .program

#----------------------------------------------------------------------------

# Clean up options:

clean:
	-rm -f $(CLAW_OBJECTS) $(CLAW_EXE) $(HTML) 
	-rm -f .data .output .plots .htmls 

clobber:
	$(MAKE) clean
	-rm -f -r fort.*  *.pyc *.db pyclaw.log output *.so
	-rm -f -r _plots* _output* 

#----------------------------------------------------------------------------

# Do multiple things:

all:
	$(MAKE) .plots
	$(MAKE) .htmls

new: 
	-rm -f  $(CLAW_OBJECTS)
	-rm -f  $(CLAW_LIBOBJECTS)
	$(MAKE) .exe

regression_test: .output
	$(PYTHON) $(CLAW)/python/pyclaw/regression_test.py $(CLAW_OUTDIR)

#----------------------------------------------------------------------------

help: 
	@echo '   "make .objs"    to compile object files'
	@echo '   "make .exe"     to create executable'
	@echo '   "make .data"    to create data files using setrun.py'
	@echo '   "make .output"  to run code'
	@echo '   "make output"   to run code with no dependency checking'
	@echo '   "make .plots"   to produce plots'
	@echo '   "make plots"    to produce plots with no dependency checking'
	@echo '   "make .htmls"   to produce html versions of files'
	@echo '   "make .program" to produce single program file'
	@echo '   "make regression_test"     to compare against archived results'
	@echo '   "make new"      to remove all objs and then make .exe'
	@echo '   "make clean"    to clean up compilation and html files'
	@echo '   "make clobber"  to also clean up output and plot files'
	@echo '   "make all"      to make .htmls and make .plots'
	@echo '   "make help"     to print this message'

.help: help

