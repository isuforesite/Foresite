# ----------------------------------------------------------------------
# Create Fill Algorithm Comparison
# Author: T. Taggart
# ----------------------------------------------------------------------

import os, sys, subprocess, time



# function definitions
def runCommand_logged (cmd, logstd, logerr):
    p = subprocess.call(cmd, stdout=logstd, stderr=logerr)
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# environmental variables/paths
if (os.name == "posix"):
    os.environ["PATH"] += os.pathsep + "/usr/local/bin"
else:
    os.environ["PATH"] += os.pathsep + "C:\program files (x86)\SAGA-GIS"
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# global variables

WORKDIR    = "D:\TomTaggart\DepressionFillingTest\Ran_DEMs"

# This directory is the toplevel directoru (i.e. DEM_8)
INPUTDIR   = "D:\TomTaggart\DepressionFillingTest\Ran_DEMs"

STDLOG     = WORKDIR + os.sep + "processing.log"
ERRLOG     = WORKDIR + os.sep + "processing.error.log"
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# open logfiles (append in case files are already existing)
logstd = open(STDLOG, "a")
logerr = open(ERRLOG, "a")
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# initialize
t0      = time.time()
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# loop over files, import them and calculate TWI

# this for loops walks through and identifies all the folder, sub folders, and so on.....and all the files, in the directory
# location that is passed to it - in this case the INPUTDIR
for dirname, dirnames, filenames in os.walk(INPUTDIR):
    # print path to all subdirectories first.
    #for subdirname in dirnames:
        #print os.path.join(dirname, subdirname)

    # print path to all filenames.
    for filename in filenames:
        #print os.path.join(dirname, filename)
        filename_front, fileext = os.path.splitext(filename)
        #print filename
        if filename_front == "w001001":
        #if fileext == ".adf":


            # Resetting the working directory to the current directory
            os.chdir(dirname)

            # Outputting the working directory
            print "\n\nCurrently in Directory: " + os.getcwd()

            # Creating new Outputs directory
            os.mkdir("Outputs")

            # Checks
            #print dirname + os.sep + filename_front
            #print dirname + os.sep + "Outputs" + os.sep + ".sgrd"

            # IMPORTING Files
            # --------------------------------------------------------------
            cmd = ['saga_cmd', '-f=q', 'io_gdal', 'GDAL: Import Raster',
                   '-FILES', filename,
                   '-GRIDS', dirname + os.sep + "Outputs" + os.sep + filename_front + ".sgrd",
                   #'-SELECT', '1',
                   '-TRANSFORM',
                   '-INTERPOL', '1'
                  ]

            print "Beginning to Import Files"

            try:
                runCommand_logged(cmd, logstd, logerr)

            except Exception, e:
                logerr.write("Exception thrown while processing file: " + filename + "\n")
                logerr.write("ERROR: %s\n" % e)

            print "Finished importing Files"

            # --------------------------------------------------------------


            # Resetting the working directory to the ouputs directory
            os.chdir(dirname + os.sep + "Outputs")



            # Depression Filling - Wang & Liu
            # --------------------------------------------------------------
            cmd = ['saga_cmd', '-f=q', 'ta_preprocessor', 'Fill Sinks (Wang & Liu)',
                   '-ELEV', filename_front + ".sgrd",
                   '-FILLED',  filename_front + "_WL_filled.sgrd",  # output - NOT optional grid
                   '-FDIR', filename_front + "_WL_filled_Dir.sgrd",  # output - NOT optional grid
                   '-WSHED', filename_front + "_WL_filled_Wshed.sgrd",  # output - NOT optional grid
                   '-MINSLOPE', '0.0100000', 
                               ]

            print "Beginning Depression Filling - Wang & Liu"

            try:
                runCommand_logged(cmd, logstd, logerr)

            except Exception, e:
                logerr.write("Exception thrown while processing file: " + filename + "\n")
                logerr.write("ERROR: %s\n" % e)

            print "Done Depression Filling - Wang & Liu"


            # Depression Filling - Planchon & Darboux
            # --------------------------------------------------------------
            cmd = ['saga_cmd', '-f=q', 'ta_preprocessor', 'Fill Sinks (Planchon/Darboux, 2001)',
                   '-DEM', filename_front + ".sgrd",
                   '-RESULT',  filename_front + "_PD_filled.sgrd",  # output - NOT optional grid
                   '-MINSLOPE', '0.0100000',
                               ]

            print "Beginning Depression Filling - Planchon & Darboux"

            try:
                runCommand_logged(cmd, logstd, logerr)

            except Exception, e:
                logerr.write("Exception thrown while processing file: " + filename + "\n")
                logerr.write("ERROR: %s\n" % e)

            print "Done Depression Filling - Planchon & Darboux"

            # Raster Calculator - DIff between Planchon & Darboux and Wang & Liu
            # --------------------------------------------------------------
            cmd = ['saga_cmd', '-f=q', 'grid_calculus', 'Grid Calculator',
                   '-GRIDS', filename_front + "_PD_filled.sgrd",
                   '-XGRIDS', filename_front + "_WL_filled.sgrd",
                   '-RESULT',  filename_front + "_DepFillDiff.sgrd",      # output - NOT optional grid
                   '-FORMULA', "(((g1-h1)/g1)*100)",
                   '-NAME', 'Calculation',
                   '-FNAME',
                   '-TYPE', '8',
                               ]

            print "Depression Filling - Diff Calc"

            try:
                runCommand_logged(cmd, logstd, logerr)

            except Exception, e:
                logerr.write("Exception thrown while processing file: " + filename + "\n")
                logerr.write("ERROR: %s\n" % e)

            print "Done Depression Filling - Diff Calc"