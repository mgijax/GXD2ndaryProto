#!/bin/bash

function Usage() {
    cat - <<ENDTEXT

$0 [-s] [-TP|-FP|-TN|-FN] RoutingFile1 RoutingFile2

Diff two routing files to report routing differences. Default: all differences.
   -s   short diff output:  < lines in the 1st file, > lines in the 2nd
   -TP  only report true positives in one file and not the other
   -FP  etc.
   -TN  etc.
   -FN  etc.

Example:   $0 -FN R1 R2
           reports FN's that are in R1 and not in R2, and vice versa
ENDTEXT
    exit 5
}

PREDTYPE=""     # no specific predtype
SHORTOUTPUT='0'
while [ $# -gt 0 ]; do
    case "$1" in
    -h|--help) Usage ;;
    -s)       SHORTOUTPUT=1; shift;;
    -TP|--TP) PREDTYPE=TP; shift ;;
    -TN|--TN) PREDTYPE=TN; shift ;;
    -FP|--FP) PREDTYPE=FP; shift ;;
    -FN|--FN) PREDTYPE=FN; shift ;;
    -*|--*) echo "invalid option $1"; Usage ;;
    *) break; ;;
    esac
done
if [ $# -ne 2 ]; then
    Usage
fi

R1="$1"
R2="$2"
R1_nocounts="tmp.$$.r1.nocounts"
R2_nocounts="tmp.$$.r2.nocounts"

# get files with truncated routings, so the counts don't cause diffs
# -f 1-4:    ID, knownClassName, routing, predType
cut -d "|" -f 1-4 $R1 | grep "$PREDTYPE" > $R1_nocounts
cut -d "|" -f 1-4 $R2 | grep "$PREDTYPE" > $R2_nocounts

if [ "$SHORTOUTPUT" -eq "1" ]; then
    diff $R1_nocounts $R2_nocounts | egrep "[<>]"
else
    diff $R1_nocounts $R2_nocounts
fi

rm -f $R1_nocounts $R2_nocounts
