#!/bin/bash

# diff two routing files to report new FN, etc.
#
function Usage() {
    cat - <<ENDTEXT

$0 FN|FP|TN|TP oldRoutingFile newRoutingFile
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
OLDROUTING="$2"
NEWROUTING="$3"
OLDROUTING_short="tmp.$$.old.short"
NEWROUTING_short="tmp.$$.new.short"

# get files with truncated routings, so the counts don't cause diffs
# -f 1-4:    ID, knownClassName, routing, predType
cut -d "|" -f 1-4 $OLDROUTING | grep $PREDTYPE> $OLDROUTING_short
cut -d "|" -f 1-4 $NEWROUTING | grep $PREDTYPE> $NEWROUTING_short
diff $OLDROUTING_short $NEWROUTING_short | egrep "[<>]"

rm -f $OLDROUTING_short $NEWROUTING_short
