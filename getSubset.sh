#!/bin/bash

# THIS IS OUT OF DATE.
# This was an attempt to automate part of analysis workflow where I'd
#  1. Pull out references from a routing file of a particular type (e.g., FN)
#  2. Create a new testSet file of just those references
#  3. Run the routing algorithm to get match files for those refs.
# Now that match files contain info about the reference and the routing, this 
#  is not needed.

# create a file of samples from a given prediction type (as specified in the
#  Routings.txt file
#
# usage:  getSubset.sh FN|FP samplefile

PREDTYPE="$1"
IDFILE=${PREDTYPE}_ids.txt
BASEDIR=~/work/GXD2ndaryProto
SAMPLEDATALIB=${BASEDIR}/GXDrefSample.py
SAMPLEFILE="$2"
OUTPUTSAMPLEFILE=${PREDTYPE}_samples.txt
OUTPUTSAMPLEFILE2=${PREDTYPE}_samples.noagemap.txt

PYTHONPATH=${BASEDIR}:$PYTHONPATH
export PYTHONPATH

# get IDs of the desired PREDTYPE
grep "|${PREDTYPE}|" Routings.txt | cut -d '|' -f 1 > ${IDFILE}

# get subset of samples
getSample.py --sampledatalib $SAMPLEDATALIB --header `cat ${IDFILE} ` < $SAMPLEFILE > $OUTPUTSAMPLEFILE

# output count for sanity sake
echo $PREDTYPE samples written to $OUTPUTSAMPLEFILE
grep "MGI:" $OUTPUTSAMPLEFILE | wc -l

# run routing on the subset to get reports
python ${BASEDIR}/doRouting.py ${PREDTYPE}_ < ${OUTPUTSAMPLEFILE}

# now go back to the raw sample files (w/o age mapping)
getSample.py --sampledatalib $SAMPLEDATALIB --header `cat ${IDFILE} ` < $BASEDIR/testSet3.figtext.txt > $OUTPUTSAMPLEFILE2

# run the age mappings on those so we can get the context report
# NOTE output, foo, below should be identical to $OUTPUTSAMPLEFILE
# BUT it is not because getSample.py inserts \n at the end of every record
# and preprocessSample.py does something different (and getSample.py does not
# output a #meta line).
# Need to do some work on getSample.py as it wasn't originally designed to
#  output subset sample files.
preprocessSamples.py --sampledatalib $SAMPLEDATALIB --sampletype ClassifiedRefSample --report ${PREDTYPE}_age4.context.txt -p textTransform_age ${OUTPUTSAMPLEFILE2}  > foo
