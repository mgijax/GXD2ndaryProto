#!/bin/bash

# diff two AgeMatch files
#
function Usage() {
    cat - <<ENDTEXT

$0 [--id] Matchfile1 Matchfile2

Compare two match files, omit routing details from the diff so only the
    different matches are reported.

    --id  include the reference IDs in the diff
            (if --id is not specified, output includes a count of the times
             the matchingText matched in each Matchfile)

ENDTEXT
    exit 5
}

# set defaults
includeIDs=0
while [ $# -gt 0 ]; do
    case "$1" in
    -h|--help) Usage ;;
    --id) includeIDs=1; shift ;;
    -*|--*) echo "invalid option $1"; Usage ;;
    *) break; ;;
    esac
done
if [ $# -ne 2 ]; then
    Usage
fi

OLDFILE="$1"
NEWFILE="$2"
OLDFILE_short="tmp.$$.old.short"
NEWFILE_short="tmp.$$.new.short"

if [ "$includeIDs" == "0" ]; then # No IDs, compare counts of matching text
    # -f 8,10:    matchtype, matching text
    # include counts of changes
    cut  -f 8,10 $OLDFILE | sort |uniq -c > $OLDFILE_short
    cut  -f 8,10 $NEWFILE | sort |uniq -c > $NEWFILE_short
    diff $OLDFILE_short $NEWFILE_short 
else    # include IDs in the diff. This lets you see which refs were affected
    cut  -f 8,10 $OLDFILE >tmp.$$.OLD1
    cut  -f 8,10 $NEWFILE >tmp.$$.NEW1
    cut  -f 1 $OLDFILE >tmp.$$.OLD2     # -f 1 ID field
    cut  -f 1 $NEWFILE >tmp.$$.NEW2
    paste tmp.$$.OLD1 tmp.$$.OLD2 | sort -u > $OLDFILE_short
    paste tmp.$$.NEW1 tmp.$$.NEW2 | sort -u > $NEWFILE_short
    diff $OLDFILE_short $NEWFILE_short 
fi

rm -f tmp.$$.*
