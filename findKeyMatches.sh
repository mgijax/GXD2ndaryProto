#!/bin/bash

# Given a predType (FN TN, ...)
#       2 routing files R1 & R2,
#       2 match files M1 & M2
# report contributing matches to predType prediction in R1-R2
#
function Usage() {
    cat - <<ENDTEXT

$0 [Options]  FN|TP|TN|FP  R1 R2 M1 M2
  For the specified routing type in R1 - R2, compare the matches in M1 & M2

  Options:
  --context       - include pre/post context text in match files (default: no)
  --keep          - keep generated tmp files, including the key matches
  --age           - M1 & M2 are AgeMatch files, not regular match files
  --keepexcludes  - keep the exclude matches in the comparison
ENDTEXT
    exit 5
}

# set defaults
includeContext=0        # include the surrounding context in the output matches 
keepTmpFiles=0          # keep tmp files when done, don't delete them
ageMatchFiles=0         # input match files are AgeMatches. These have diff
                        #   columns than other match files.
keepExcludes=0           

# process options
while [ $# -gt 0 ]; do
    case "$1" in
    -h|--help)       Usage ;;
    --context)       includeContext=1; shift ;;
    --keep)          keepTmpFiles=1;   shift ;;
    --age)           ageMatchFiles=1;  shift ;;
    --keepexcludes)  keepExcludes=1;   shift ;;
    -*|--*) echo "invalid option $1"; Usage ;;
    *) break; ;;
    esac
done

# set which fields to include in the final output files of relevant matches
if [ "$includeContext" -eq "1" ]; then
    if [ "$ageMatchFiles" -eq "1" ]; then
        finalCutFields='1,4,5,6,7'  # id matchType preText matchText postText
    else
        finalCutFields='1,8,9,10,11'  # id matchType preText matchText postText
    fi
else
    if [ "$ageMatchFiles" -eq "1" ]; then
        finalCutFields='1,4,6'  # id matchType matchText
    else
        finalCutFields='1,8,10'  # id matchType matchText
    fi
fi

# process positional params, there should be 5
if [ $# -ne 5 ]; then
    Usage
fi
predType="$1"
R1="$2"
R2="$3"
M1="$4"
M2="$5"

# Get IDs of predTypes in R1 - R2 into $Wanted_IDs
R1_IDs=tmp.$$.R1_IDs
R2_IDs=tmp.$$.R2_IDs
cut -d '|' -f 1,4 $R1 | grep "$predType" | cut -d '|' -f 1 >$R1_IDs
cut -d '|' -f 1,4 $R2 | grep "$predType" | cut -d '|' -f 1 >$R2_IDs
Wanted_IDs=tmp.$$.Wanted_IDs
setops --diff $R1_IDs $R2_IDs > $Wanted_IDs

NumIDs=`cat $Wanted_IDs | wc -l`

echo $NumIDs $predType routings found in $R1 not in $R2 >&2

if [ "$NumIDs" -eq "0" ]; then
    echo no $predType routings found in $R1 not in $R2
    exit 1
fi

echo $NumIDs $predType in $R1 not in $R2, comparing matches $M1 to $M2
cat $Wanted_IDs

# pull out the matches for each wanted ID
M1WantedMatches=tmp.$$.M1WantedMatches
M2WantedMatches=tmp.$$.M2WantedMatches

idString='^(foofoo'       # build egrep pattern of Wanted_IDs
for id in $( cat $Wanted_IDs ); do
    idString="${idString}|$id"
done
idString="${idString})"

#echo egrep for "$idString" >&2 # debug
egrep "$idString" $M1 > $M1WantedMatches
echo done 1st egrep for matches >&2
egrep "$idString" $M2 > $M2WantedMatches
echo done 2nd egrep for matches >&2

# Clean up the wanted matches
M1WantedMatchesClean=tmp.$$.M1WantedMatchesClean
M2WantedMatchesClean=tmp.$$.M2WantedMatchesClean

if [ "$keepExcludes" -eq "1" ]; then
    cut -f $finalCutFields $M1WantedMatches > $M1WantedMatchesClean
    cut -f $finalCutFields $M2WantedMatches > $M2WantedMatchesClean
else
    cut -f $finalCutFields $M1WantedMatches | egrep -v "\texclude" > $M1WantedMatchesClean
    cut -f $finalCutFields $M2WantedMatches | egrep -v "\texclude" > $M2WantedMatchesClean
fi

# Finally, diff the two sets of cleaned up matches
DiffOutput=tmp.$$.diff.out
diff $M1WantedMatchesClean $M2WantedMatchesClean > $DiffOutput

cat $DiffOutput

# output matching text and counts of refs that were affected.
# This only works w/o --context output and not on --age
#  would need to make this smarter for those options
grep "<" $DiffOutput | sort -u | cut -f 3 | sort | uniq -c

if [ "$keepTmpFiles" -eq "0" ]; then
    rm -f tmp.$$.*
fi
