#!/bin/bash

# remove counts from Match files so matches can be compared w/o count diffs
#
function Usage() {
    cat - <<ENDTEXT

    $0 file

    Remove count columns from a match file. Write to stdout.
ENDTEXT
    exit 5
}

# set defaults
includeIDs=0
while [ $# -gt 0 ]; do
    case "$1" in
    -h|--help) Usage ;;
    -*|--*) echo "invalid option $1"; Usage ;;
    *) break; ;;
    esac
done
if [ $# -ne 1 ]; then
    Usage
fi

cut -f 1-3,8-11 $1
