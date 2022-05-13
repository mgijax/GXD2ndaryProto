#!/bin/bash

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

# get IDs of the desired PREDTYPE
grep "|${PREDTYPE}|" Routings.txt | cut -d '|' -f 1 > ${IDFILE}

# get subset of samples
getSample.py --sampledatalib $SAMPLEDATALIB --header `cat ${IDFILE} ` < $SAMPLEFILE > $OUTPUTSAMPLEFILE

echo $PREDTYPE samples written to $OUTPUTSAMPLEFILE
grep "MGI:" $OUTPUTSAMPLEFILE | wc -l

python ${BASEDIR}/doRouting.py ${PREDTYPE}_ < ${OUTPUTSAMPLEFILE}
