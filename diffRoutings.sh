#!/bin/bash

function Usage() {
    cat - <<ENDTEXT

$0 TP|FP|TN|FN RoutingFile1 RoutingFile2

Compare two routing files to report a specific predType (TP, FP, TN, FN)
    in one file and not the other

Example:   $0 FN R1 R2
                reports FN's that are in R1 and not in R2
ENDTEXT
    exit 5
}

while [ $# -gt 0 ]; do
    case "$1" in
    -h|--help) Usage ;;
    -*|--*) echo "invalid option $1"; Usage ;;
    *) break; ;;
    esac
done
if [ $# -ne 3 ]; then
    Usage
fi

PREDTYPE="$1"
R1="$2"
R2="$3"
R1_short="tmp.$$.r1.short"
R2_short="tmp.$$.r2.short"

# get files with truncated routings, so the counts don't cause diffs
# -f 1-4:    ID, knownClassName, routing, predType
cut -d "|" -f 1-4 $R1 | grep $PREDTYPE> $R1_short
cut -d "|" -f 1-4 $R2 | grep $PREDTYPE> $R2_short
diff $R1_short $R2_short | egrep "[<>]"

rm -f $R1_short $R2_short
