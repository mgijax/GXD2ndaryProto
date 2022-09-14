#!/bin/bash

# diff two AgeMatch files
#
function Usage() {
    cat - <<ENDTEXT

$0 [--count [--id]] Matchfile1 Matchfile2

Compare two match files, omit routing details from the match files so only the
    differences in the matches are reported

    --count ignore pre/post text, only look at matchText and compare counts
            of distinct matchText

    --id    include the reference IDs in the diff
            This outputs differences in counts of matches within references.
                (so aggregated within references)
                IDs are output so you can see which refs have different matches.

            W/O --id, output is diff in counts of matchText across all refs.
                (so aggregated across all references in the corpus)

    with no --count, the ID, matchType, preText, matchText, postText are diffed
ENDTEXT
    exit 5
}

# Process args
counts=0
includeIDs=0
while [ $# -gt 0 ]; do
    case "$1" in
    -h|--help) Usage ;;
    --count|--counts) counts=1;     shift ;;
    --id|--ids)       includeIDs=1; shift ;;
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

                        # fields to diff if no counts
CUTFIELDS="1,8-11"      # ID, matchType, preText, matchText, postText

if [ "$counts" == "1" ]; then # do counts of matchTexts
    if [ "$includeIDs" == "1" ]; then
        CUTFIELDS="1,8,10"      # ID, matchtype, matchText, ignore context
    else
        CUTFIELDS="8,10"        # matchtype, matchText, ignore context
    fi
    cut  -f $CUTFIELDS $FILE1 | sort |uniq -c > $FILE1_toDiff
    cut  -f $CUTFIELDS $FILE2 | sort |uniq -c > $FILE2_toDiff

else     # no counts
    cut  -f $CUTFIELDS $FILE1 | sort > $FILE1_toDiff
    cut  -f $CUTFIELDS $FILE2 | sort > $FILE2_toDiff
fi

diff $FILE1_toDiff $FILE2_toDiff 
rm -f tmp.$$.*
