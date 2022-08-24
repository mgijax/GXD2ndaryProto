#!/bin/bash

# diff two AgeMatch files
#
function Usage() {
    cat - <<ENDTEXT

$0 [--id] Matchfile1 Matchfile2

Compare two match files, omit routing details from the diff so only the
    different types & matcheText are reported.

    --id  include the reference IDs in the diff
          This outputs differences in counts of matches within references.
          (so aggregated within references)
          W/o --id, output is difference in counts of matches across all refs.
          (so aggregated across all references)
ENDTEXT
    exit 5
}

# Process args
includeIDs=0
while [ $# -gt 0 ]; do
    case "$1" in
    -h|--help) Usage ;;
    --id|--ids) includeIDs=1; shift ;;
    -*|--*) echo "invalid option $1"; Usage ;;
    *) break; ;;
    esac
done
if [ $# -ne 2 ]; then
    Usage
fi

FILE1="$1"
FILE2="$2"
FILE1_toDiff="tmp.$$.File1_toDiff"
FILE2_toDiff="tmp.$$.File2_toDiff"
FILE1_ids="tmp.$$.File1_ids"
FILE2_ids="tmp.$$.File2_ids"
FILE1_matches="tmp.$$.File1_matches"
FILE2_matches="tmp.$$.File2_matches"

if [ "$includeIDs" == "0" ]; then # No IDs, compare counts of matches
    cut  -f 8,10 $FILE1 | sort |uniq -c > $FILE1_toDiff # matchtype matchingText
    cut  -f 8,10 $FILE2 | sort |uniq -c > $FILE2_toDiff
    diff $FILE1_toDiff $FILE2_toDiff 

else    # include IDs in the diff. This lets you see which refs were affected
    cut  -f 1 $FILE1 > $FILE1_ids     # -f 1 ID field
    cut  -f 1 $FILE2 > $FILE2_ids
    cut  -f 8,10 $FILE1 > $FILE1_matches  # -f 8,10: matchtype, matchText
    cut  -f 8,10 $FILE2 > $FILE2_matches
    paste $FILE1_ids $FILE1_matches | sort | uniq -c > $FILE1_toDiff
    paste $FILE2_ids $FILE2_matches | sort | uniq -c > $FILE2_toDiff
    diff $FILE1_toDiff $FILE2_toDiff 
fi

rm -f tmp.$$.*
