#!/bin/bash

# diff two AgeMatch files
#
function Usage() {
    cat - <<ENDTEXT

$0 [--id] oldMatchfile newMatchfile
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

if [ "$includeIDs" == "0" ]; then
    # -f 4,6:    matchtype, matching text
    # include counts of changes
    cut  -f 4,6 $OLDFILE | sort |uniq -c > $OLDFILE_short
    cut  -f 4,6 $NEWFILE | sort |uniq -c > $NEWFILE_short
    diff $OLDFILE_short $NEWFILE_short 
else
    # -f 4,6:    matchtype, matching text
    cut  -f 4,6 $OLDFILE >tmp.$$.OLD1
    cut  -f 4,6 $NEWFILE >tmp.$$.NEW1
    cut  -f 1 $OLDFILE >tmp.$$.OLD2
    cut  -f 1 $NEWFILE >tmp.$$.NEW2
    paste tmp.$$.OLD1 tmp.$$.OLD2 | sort -u > $OLDFILE_short
    paste tmp.$$.NEW1 tmp.$$.NEW2 | sort -u > $NEWFILE_short
    diff $OLDFILE_short $NEWFILE_short 
fi

rm -f tmp.$$.*
