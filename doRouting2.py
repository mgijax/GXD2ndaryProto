#!/usr/bin/env python3
'''
  Purpose: Apply a potential GXD secondary triage routing algorithm & evaluate.

  Inputs:  Sample file of GXD routed (classified) reference records.
            See refSample.py for the fields of these records.
  
  Outputs: a file of Routing assignments, 1 line for each reference
           a file of "details" w/ a summary of what terms were searched for.
           files of matches (see Output filenames below)
           a summary file of Precision and Recall

           You pass filename base prefix, e.g., 'Try1' as a cmd line param
           and the output files are named:
               Try1Routings.txt
               Try1Details.txt
               Try1*Matches.txt
               Try1Summary.txt
           Summary and other info is also written to stdout.
'''
import sys
import os
import time
import argparse
import re
import unittest
import figureText
import GXD2aryAge
from  GXD2aryRouter import GXDrouter
import GXD2aryRefSample as SampleLib
from sklearnHelperLib import predictionType
#from utilsLib import MatchRcd, TextMapping, TextMappingFromStrings, TextTransformer
#-----------------------------------

sampleObjType = SampleLib.ClassifiedRefSample

#-----------------------------------

def getArgs():

    parser = argparse.ArgumentParser( \
        description='test routing algorithm for GXD 2ndary triage proto, read testSet from stdin')

    parser.add_argument('baseName', action='store',
        help="output base file name. 'test' to just run automated tests. ")

    parser.add_argument('-l', '--limit', dest='nToDo',
        required=False, type=int, default=0, 		# 0 means ALL
        help="only process this many references. Default is no limit")

    parser.add_argument('--textlength', dest='maxTextLength',
        type=int, required=False, default=None,
        help="only include the 1st n chars of text fields (for debugging)")

    parser.add_argument('-q', '--quiet', dest='verbose', action='store_false',
        required=False, help="skip helpful messages to stderr")

    args =  parser.parse_args()

    return args
#-----------------------------------

args = getArgs()

# Output filenames
args.routingsFilename  = "%sRoutings.txt" % args.baseName
args.ExcludeMatchesFilename = "%sExcMatches.txt" % args.baseName
args.AgeMatchesFilename = "%sAgeMatches.txt" % args.baseName
args.TPmatchesFilename = "%sTPMatches.txt" % args.baseName
args.FPmatchesFilename = "%sFPMatches.txt" % args.baseName
args.TNmatchesFilename = "%sTNMatches.txt" % args.baseName
args.FNmatchesFilename = "%sFNMatches.txt" % args.baseName
args.detailsFilename   = "%sDetails.txt" % args.baseName
args.summaryFilename   = "%sSummary.txt" % args.baseName

# Input files for various vocabs
SKIPJOURNALFILENAME='/Users/jak/work/GXD2ndaryProto/skipJournals.txt'
CAT1EXCLUDEFILENAME='/Users/jak/work/GXD2ndaryProto/cat1Exclude.txt'
CAT2TERMFILENAME='/Users/jak/work/GXD2ndaryProto/cat2Terms.txt'
CAT2EXCLUDEFILENAME='/Users/jak/work/GXD2ndaryProto/cat2Exclude.txt'
AGEEXCLUDEFILENAME='/Users/jak/work/GXD2ndaryProto/ageExclude.txt'

# Formatting for the output reports
routingFieldSep = '|'
routingHdr = routingFieldSep.join(['ID',
                    'knownClassName',
                    'routing',
                    'predType',
                    'goodJournal',
                    'Cat1 matches',
                    'Cat1 Excludes',
                    'Age matches',
                    'Age Excludes',
                    'Cat2 matches',
                    'Cat2 Excludes',
                    ] + sampleObjType.getExtraInfoFieldNames()) + '\n'

def formatRouting(r, routing, predType, goodJournal, numCat1Matches,
                    numCat1Excludes, numAgeMatches, numAgeExcludes,
                    numCat2Matches, numCat2Excludes):
    t = routingFieldSep.join([r.getID(),
                    r.getKnownClassName(),
                    routing,
                    predType,
                    str(goodJournal),
                    str(numCat1Matches),
                    str(numCat1Excludes),
                    str(numAgeMatches),
                    str(numAgeExcludes),
                    str(numCat2Matches),
                    str(numCat2Excludes),
                    ] + r.getExtraInfo()) + '\n'
    return t

matchesFieldSep = '\t'
matchesHdr = matchesFieldSep.join(['ID',
                    'routing',
                    'predType',
                    'goodJournal',
                    'Cat1 matches',
                    'Age matches',
                    'Cat2 matches',
                    'matchType',
                    'preText',
                    'matchText',
                    'postText',
                    'confidence',
                    ]) + '\n'

def formatMatches(ID, routing, predType, goodJournal, numCat1Matches,
                    numAgeMatches, numCat2Matches, matchRcds, confidence):
    output = ''
    for m in matchRcds:
        output += matchesFieldSep.join([
                   str(ID),
                   routing,
                   predType,
                   str(goodJournal),
                   str(numCat1Matches),
                   str(numAgeMatches),
                   str(numCat2Matches),
                   m.matchType,
                   "'%s'" % m.preText.replace('\n','\\n').replace('\t','\\t'),
                   "'%s'" % m.matchText.replace('\n','\\n').replace('\t','\\t'),
                   "'%s'" % m.postText.replace('\n','\\n').replace('\t','\\t'),
                   str(confidence),
                   ]) + '\n'
    return output

matchesNoCountsHdr = matchesFieldSep.join(['ID',
                    'routing',
                    'predType',
                    'matchType',
                    'preText',
                    'matchText',
                    'postText',
                    'confidence',
                    ]) + '\n'

def formatMatchesNoCounts(ID, routing, predType, matchRcds, confidence):
    output = ''
    for m in matchRcds:
        output += matchesFieldSep.join([
                   str(ID),
                   routing,
                   predType,
                   m.matchType,
                   "'%s'" % m.preText.replace('\n','\\n').replace('\t','\\t'),
                   "'%s'" % m.matchText.replace('\n','\\n').replace('\t','\\t'),
                   "'%s'" % m.postText.replace('\n','\\n').replace('\t','\\t'),
                   str(confidence),
                   ]) + '\n'
    return output

#-----------------------------------

def process():
    ''' go through the refs and determine routing
    '''
    startTime = time.time()
    timeString = time.ctime()
    verbose(timeString + '\n')

    # get journals to skip
    skipJournals = [line.strip() for line in open(SKIPJOURNALFILENAME, 'r') \
                            if not line.startswith('#') and line.strip() != '']

    # Category 1 terms:  just 'embryo'
    cat1Terms = ['embryo', 'the expression of']

    # get cat1Exclude terms
    cat1Exclude = [line.strip() for line in open(CAT1EXCLUDEFILENAME, 'r') \
                            if not line.startswith('#') and line.strip() != '']

    # get cat2 terms
    cat2Terms = [line.strip() for line in open(CAT2TERMFILENAME, 'r') \
                            if not line.startswith('#') and line.strip() != '']

    # get cat2Exclude terms
    cat2Exclude = [line.strip() for line in open(CAT2EXCLUDEFILENAME, 'r') \
                            if not line.startswith('#') and line.strip() != '']

    # get ageExclude terms - Note, no line.strip(). Spaces may be important
    ageExclude = [line[:-1] for line in open(AGEEXCLUDEFILENAME, 'r') \
                            if not line.startswith('#') and line.strip() != '']

    # initialize GXDrouter
    gxdRouter = GXDrouter(skipJournals, cat1Terms, cat1Exclude, ageExclude,
                                        cat2Terms, cat2Exclude, numChars=30)

    # get testSet from stdin
    testSet = SampleLib.ClassifiedSampleSet(sampleObjType=sampleObjType)
    testSet.read(sys.stdin)
    verbose('read %d refs to determine routing\n' % testSet.getNumSamples())
    verbose("%8.3f seconds\n\n" %  (time.time()-startTime))

    # set up output files and various counts
    routingsFile = open(args.routingsFilename, 'w')
    routingsFile.write(timeString + '\n')
    routingsFile.write(routingHdr)

    excludeMatchesFile = open(args.ExcludeMatchesFilename, 'w')
    excludeMatchesFile.write(timeString + '\n')
    excludeMatchesFile.write(matchesHdr)

    ageMatchesFile = open(args.AgeMatchesFilename, 'w')
    ageMatchesFile.write(timeString + '\n')
    ageMatchesFile.write(matchesNoCountsHdr)

    matchesFile = { 'TP': open(args.TPmatchesFilename, 'w'),
                    'FP': open(args.FPmatchesFilename, 'w'),
                    'TN': open(args.TNmatchesFilename, 'w'),
                    'FN': open(args.FNmatchesFilename, 'w'), }
    for f in matchesFile.values():
        f.write(timeString + '\n')
        f.write(matchesHdr)

    detailsFile = open(args.detailsFilename, 'w')
    detailsFile.write(timeString + '\n')
    detailsFile.write(gxdRouter.getExplanation())

    allCounts  = {'TP': 0, 'FP': 0, 'TN': 0, 'FN': 0}   # for all refs
    keepCounts = {'TP': 0, 'FP': 0, 'TN': 0, 'FN': 0}   # for keep refs
    discCounts = {'TP': 0, 'FP': 0, 'TN': 0, 'FN': 0}   # for discard refs

    numProcessed = 0            # total number of references processed

    if args.nToDo > 0: samples = testSet.getSamples()[:args.nToDo]
    else: samples = testSet.getSamples()

    # for each record, routeThisRef(), gather counts, write list of routings
    for i, ref in enumerate(samples):
        conf = ref.getField('confidence')
        routing = gxdRouter.routeThisRef(ref.getID(), ref.getDocument(),
                                                    ref.getField('journal'))
        numCat1Matches  = len(gxdRouter.getCat1Matches())
        numCat1Excludes = len(gxdRouter.getCat1Excludes())

        numAgeMatches   = len(gxdRouter.getAgeMatches())
        numAgeExcludes  = len(gxdRouter.getAgeExcludes())

        numCat2Matches  = len(gxdRouter.getCat2Matches())
        numCat2Excludes = len(gxdRouter.getCat2Excludes())

        predType = predictionType(ref.getKnownClassName(), routing,
                                                        positiveClass='Yes')
        allCounts[predType] += 1

        relevance = ref.getField('relevance')
        if relevance == 'keep':
            keepCounts[predType] += 1
        else:
            discCounts[predType] += 1

        numProcessed += 1

        goodJournal = gxdRouter.getGoodJournal()

        # Routings file
        r = formatRouting(ref, routing, predType, goodJournal, 
                                            numCat1Matches, numCat1Excludes,
                                            numAgeMatches,  numAgeExcludes,
                                            numCat2Matches, numCat2Excludes)
        routingsFile.write(r)

        # Exclude matches file
        m = formatMatches(ref.getID(), routing, predType, goodJournal,
                    numCat1Matches, numAgeMatches, numCat2Matches,
                    gxdRouter.getExcludeMatches(), conf)
        excludeMatchesFile.write(m)

        # Age match report, helpful for evaluating/debugging age mapping chgs
        m = formatMatchesNoCounts(ref.getID(), routing, predType, 
                gxdRouter.getAgeMatches() + gxdRouter.getAgeExcludes(), conf)
        ageMatchesFile.write(m)

        # Match files broken down by prediction type (TP, FP, ...)
        m = formatMatches(ref.getID(), routing, predType, goodJournal,
                    numCat1Matches, numAgeMatches, numCat2Matches,
                    gxdRouter.getPosMatches(), conf)
        matchesFile[predType].write(m)
        if predType == 'FN':    # report exclude matches for FN's
                                #  to help understand why not routed
            m = formatMatches(ref.getID(), routing, predType, goodJournal,
                        numCat1Matches, numAgeMatches, numCat2Matches,
                        gxdRouter.getExcludeMatches(), conf)
            matchesFile[predType].write(m)
    # end routing loop

    routingsFile.close()
    detailsFile.close()
    excludeMatchesFile.close()
    ageMatchesFile.close()
    for f in matchesFile.values():
        f.close()

    # compute Precision, Recall, write summary
    summary = 'Summary\n'
    for counts, label in [(allCounts, 'Overall'), (keepCounts, 'Keeps'),
                                                    (discCounts, 'Discards')]:
        summary += label + '\n'
        numRefs = 0
        for predType in ['TP', 'FP', 'TN', 'FN']:
            summary += "%s: %d\n" % (predType, counts[predType])
            numRefs += counts[predType]

        summary += "Total Refs: %d\n" % numRefs

        p, r, npv = computeMetrics(counts)
        summary += "Precision: %.2f%%\n" % p
        summary += "Recall   : %.2f%%\n" % r
        summary += "NPV      : %.2f%%\n" % npv
        summary += '\n'
    summary += "wrote %d routings to '%s'\n" % (numProcessed,
                                                    args.routingsFilename)
    summary += "%8.3f seconds\n\n" %  (time.time()-startTime)

    summaryFile = open(args.summaryFilename, 'w')
    summaryFile.write(timeString + '\n')
    summaryFile.write(summary)
    summaryFile.close()

    verbose(summary)

    return
#-----------------------------------

def computeMetrics(counts):
    if (counts['TP'] + counts['FP']) == 0: p = 0.0      # check for zero div
    else: p = counts['TP'] / (counts['TP'] + counts['FP']) * 100

    if (counts['TP'] + counts['FN']) == 0: r = 0.0      # check for zero div
    else: r = counts['TP'] / (counts['TP'] + counts['FN']) * 100

    if (counts['TN'] + counts['FN']) == 0: npv = 0.0      # check for zero div
    else: npv = counts['TN'] / (counts['TN'] + counts['FN']) * 100

    return p, r, npv
#-----------------------------------

def verbose(text):
    if args.verbose:
        sys.stderr.write(text)
        sys.stderr.flush()
#-----------------------------------

def doAutomatedTests():

    sys.stdout.write("No automated tests at this time\n")
    return
    #sys.stdout.write("Running automated unit tests...\n")
    #unittest.main(argv=[sys.argv[0], '-v'],)

#-----------------------------------

def main():
    if   args.baseName == 'test': doAutomatedTests()
    else: process()

    exit(0)
#-----------------------------------
if __name__ == "__main__":
    main()
