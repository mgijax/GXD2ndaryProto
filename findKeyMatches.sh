#!/bin/bash

# Compare two routing files and report matches that contributed to the routing
#  differences.
# Given a predType (TP, FP, TN FN)
#       2 routing files R1 & R2,
#       2 match files M1 & M2
# report contributing matches to predType prediction in R1-R2
#
# Note: this uses Jim's setops (set operations) utility to compute the
#  difference R1-R2.
#  Also for M1 M2 differences (instead of using diff) because sometimes the
#   matches come out in different orders (for the same references),and we don't 
#   want different match orders to appear as part of the match differences.
# Maybe there is a way to do set difference with the Unix join command,
#   but I've never figured out how to make that work.
#
function Usage() {
    cat - <<ENDTEXT

$0 [Options]  TP|FP|TN|FN  R1 R2 M1 M2
  For the specified routing type in R1 - R2, compare the matches in M1 & M2.
  Writes multi-section report to stdout.

  Options:
  --context     - include pre/post context text in match files. Default: no
                    With this option, diff output includes context.
                    W/O  this option, diff omits context and aggregates matches
                         to the matching text.
  --excludes    - include the exclude matches in the comparison. Default: omit
  --keep        - keep generated tmp files, including the key matches
                    (primarily for debugging)
  Example:
  findKeyMatches.sh FP R1/Routings.txt R2/Routings.txt R1/Cat1FPmatches.txt R2/Cat1TNmatches.txt
                reports on the matches that are for FP in R1 but TN in R2
ENDTEXT
    exit 5
}

### set defaults
includeContext=0        # include the surrounding context in the output matches 
excludes=0              # include exclude matches
keepTmpFiles=0          # keep tmp files when done, don't delete them

### process options
while [ $# -gt 0 ]; do
    case "$1" in
    -h|--help)       Usage ;;
    --context)       includeContext=1; shift ;;
    --excludes)      excludes=1;       shift ;;
    --keep)          keepTmpFiles=1;   shift ;;
    -*|--*) echo "invalid option $1"; Usage ;;
    *) break; ;;
    esac
done

# set which fields to include in the final output files of relevant matches
if [ "$includeContext" -eq "1" ]; then
    finalCutFields='1,8,9,10,11'  # id matchType preText matchText postText
else
    finalCutFields='1,8,10'  # id matchType matchText
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
echo output from:   findKeyMatches.sh $1 $2 $3 $4 $5

### Get IDs of predTypes in R1 - R2 into $Wanted_IDs
R1_IDs=tmp.$$.R1_IDs
R2_IDs=tmp.$$.R2_IDs
cut -d '|' -f 1,4 $R1 | grep "$predType" | cut -d '|' -f 1 >$R1_IDs
cut -d '|' -f 1,4 $R2 | grep "$predType" | cut -d '|' -f 1 >$R2_IDs
Wanted_IDs=tmp.$$.Wanted_IDs
setops --diff $R1_IDs $R2_IDs | sort > $Wanted_IDs

NumIDs=`cat $Wanted_IDs | wc -l`

#echo $NumIDs $predType routings found in $R1 not in $R2 >&2

if [ "$NumIDs" -eq "0" ]; then
    echo "Done: there are no $predType routings found in $R1 not in $R2"
    exit 1
fi

echo
echo Section 1: $NumIDs $predType references in $R1 not in $R2
cat $Wanted_IDs

### pull out the matches for each wanted ID
M1WantedMatches=tmp.$$.M1WantedMatches
M2WantedMatches=tmp.$$.M2WantedMatches

idString='^(foofoo'       # build egrep pattern of Wanted_IDs
for id in $( cat $Wanted_IDs ); do
    idString="${idString}|$id"
done
idString="${idString})"

#echo egrep for "$idString" >&2 # debug
egrep "$idString" $M1 > $M1WantedMatches
echo progress: done 1st egrep for matches >&2
egrep "$idString" $M2 > $M2WantedMatches
echo progress: done 2nd egrep for matches >&2

### Clean up the wanted matches, i.e., throw away the count columns
# when we do the diff, we don't want the count columns because we ONLY want
# to see the difference in matches between M1 and M2.
M1WantedMatchesClean=tmp.$$.M1WantedMatchesClean
M2WantedMatchesClean=tmp.$$.M2WantedMatchesClean

if [ "$excludes" -eq "1" ]; then        # keep excludes
    cut -f $finalCutFields $M1WantedMatches > $M1WantedMatchesClean
    cut -f $finalCutFields $M2WantedMatches > $M2WantedMatchesClean
else    # throw away exclude matches
    cut -f $finalCutFields $M1WantedMatches | egrep -v "\texclude" > $M1WantedMatchesClean
    cut -f $finalCutFields $M2WantedMatches | egrep -v "\texclude" > $M2WantedMatchesClean
fi

### diff the two sets of cleaned up matches using "setops --diff"
#   so match order doesn't matter.
OnlyInM1=tmp.$$.OnlyInM1
OnlyInM2=tmp.$$.OnlyInM2
echo
echo "Section 2a: Matches in: $M1 - $M2"
setops --diff $M1WantedMatchesClean $M2WantedMatchesClean | sort > $OnlyInM1
cat $OnlyInM1

echo
echo "Section 2b: Matches in: $M2 - $M1"
setops --diff $M2WantedMatchesClean $M1WantedMatchesClean | sort > $OnlyInM2
cat $OnlyInM2

### Do some aggregating magic to report matchText that made the differences
### and the count of references affected by that matchText
# This only works w/o --context output. Could make this work by removing the
#   pre/post text columns and rerunning the match diff.
if [ $includeContext -eq "0" ]; then
    echo
    echo "Section 3a: Matches, and count of refs, in M1-M2 that chged routings"

    # This outputs matches in the R1-R2 set.
    # grep "<":       get matches in R1 & not in R2 (ID, matchType, matchText)
    # sort -u:        throw out duplicate matchText from the same reference
    # cut -f 2,3:     just grab matchType and matchText
    # sort | uniq -c: output one line/matchText w/ count
    #grep "<" $DiffOutput | sort -u | cut -f 2,3 | sort | uniq -c
    sort -u $OnlyInM1 | cut -f 2,3 | sort | uniq -c

    # This outputs matches in the R2-R1 set.
    echo
    echo "Section 3b: Matches, and count of refs, in M2-M1 that chged routings"
    #grep ">" $DiffOutput | sort -u | cut -f 2,3 | sort | uniq -c
    sort -u $OnlyInM2 | cut -f 2,3 | sort | uniq -c
fi

### Delete tmp files
if [ "$keepTmpFiles" -eq "0" ]; then
    rm -f tmp.$$.*
fi
