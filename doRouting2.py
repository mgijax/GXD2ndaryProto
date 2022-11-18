#!/usr/bin/env python3
'''
  Purpose: Apply a potential GXD secondary triage routing algorithm to
              a test set & evaluate.

  Inputs:  (stdin) Sample file of GXD classified reference records.
            See refSample.py for the fields of these records.

            A bunch of vocab (text) files with fixed filenames.
  
  Outputs: a file of Routing assignments, 1 line for each reference
           a "Details" file: a summary of the logic & vocab terms searched for.
           a Summary file of Precision and Recall
           files of matches (see Output filenames below)

           You pass a filename base prefix, e.g., 'Try1/' as a cmd line param
           and the output files are named:
               Try1/Routings.txt
               Try1/Details.txt
               Try1/*Matches.txt
               Try1/Summary.txt
           Summary and other info is also written to stdout.
'''
import sys
import time
import argparse
import unittest
import figureText
from  GXD2aryRouter import GXDrouter
import GXD2aryRefSample as SampleLib
from sklearnHelperLib import predictionType
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

# Input files for various vocabs
SKIPJOURNALFILENAME = '/Users/jak/work/GXD2ndaryProto/skipJournals.txt'
CAT1EXCLUDEFILENAME = '/Users/jak/work/GXD2ndaryProto/cat1Exclude.txt'
CAT2TERMFILENAME    = '/Users/jak/work/GXD2ndaryProto/cat2Terms.txt'
CAT2EXCLUDEFILENAME = '/Users/jak/work/GXD2ndaryProto/cat2Exclude.txt'
AGEEXCLUDEFILENAME  = '/Users/jak/work/GXD2ndaryProto/ageExclude.txt'

# Output filenames
args.routingsFilename  = "%sRoutings.txt" % args.baseName
args.detailsFilename   = "%sDetails.txt"  % args.baseName
args.summaryFilename   = "%sSummary.txt"  % args.baseName

fileSplitModulus = 4    # split big files based on this modulus,
                        #  see match output files below.

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
                    'TextLength',
                    ] + sampleObjType.getExtraInfoFieldNames()) + '\n'

def formatRouting(r, routing, predType, goodJournal, numCat1Matches,
                    numCat1Excludes, numAgeMatches, numAgeExcludes,
                    numCat2Matches, numCat2Excludes, textLen):
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
                    str(textLen),
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

    # get testSet from stdin. Set samples to list of samples (refs) to route
    testSet = SampleLib.ClassifiedSampleSet(sampleObjType=sampleObjType)
    testSet.read(sys.stdin)
    verbose('read %d refs to determine routing\n' % testSet.getNumSamples())
    verbose("%8.3f seconds\n\n" %  (time.time()-startTime))

    if args.nToDo > 0:
        samples = testSet.getSamples()[:args.nToDo]
    else:
        samples = testSet.getSamples()

    # open routings output file
    routingsFile = open(args.routingsFilename, 'w')
    routingsFile.write(timeString + '\n')
    routingsFile.write(routingHdr)

    # open all the match output files
    # The files are split by type of match (Cat1, Cat2, Age), and by predType
    #  (TP, FP, TN, FN). TP's are split up into subfiles based on last two
    #  digits of the reference ID)
    # This is all because the match files get too big to import into Excel
    #  and Google Sheets.
    matchesFile = {}   # matchesFile[(cat,predType)] = output file for matches
    for cat in ['Cat1', 'Cat2', 'Age']:
        for predType in ['FP', 'TN', 'FN']:
            fileName = '%s%s%smatches.txt' % (args.baseName, cat, predType)
            fp = open(fileName, 'w')
            #print("opening '%s' for output" % fileName)
            matchesFile[(cat, predType)] = fp

        for predType in ['TP']:
            for dig in range(fileSplitModulus):
                fileName = '%s%s%s_%dmatches.txt' % (args.baseName, cat,
                                                                predType, dig)
                fp = open(fileName, 'w')
                #print("opening '%s' for output" % fileName)
                matchesFile[(cat, predType, dig)] = fp

    for fp in matchesFile.values():
        fp.write(timeString + ' ')
        fp.write(matchesHdr)

    # initialize reference counts
    numProcessed = 0            # total number of references processed
    allCounts  = {'TP': 0, 'FP': 0, 'TN': 0, 'FN': 0}   # for all refs
    keepCounts = {'TP': 0, 'FP': 0, 'TN': 0, 'FN': 0}   # for keep refs
    discCounts = {'TP': 0, 'FP': 0, 'TN': 0, 'FN': 0}   # for discard refs

    # for each record, routeThisRef(), gather counts, write routing & matches
    for i, ref in enumerate(samples):
        refID = ref.getID()
        conf = ref.getField('confidence')
        text = ref.getDocument()
        textLen = len(text)

        routing = gxdRouter.routeThisRef(text, ref.getField('journal'))
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
                                            numCat2Matches, numCat2Excludes,
                                            textLen)
        routingsFile.write(r)

        # Cat1 match report
        matchRpt = formatMatches(refID, routing, predType, 
                goodJournal, numCat1Matches, numAgeMatches, numCat2Matches,
                gxdRouter.getCat1Matches() + gxdRouter.getCat1Excludes(), conf)
        matchesFile[getMatchFileKey('Cat1', predType, refID)].write(matchRpt)

        # Age match report
        matchRpt = formatMatches(refID, routing, predType, 
                goodJournal, numCat1Matches, numAgeMatches, numCat2Matches,
                gxdRouter.getAgeMatches() + gxdRouter.getAgeExcludes(), conf)
        matchesFile[getMatchFileKey('Age', predType, refID)].write(matchRpt)

        # Cat2 match report
        matchRpt = formatMatches(refID, routing, predType, 
                goodJournal, numCat1Matches, numAgeMatches, numCat2Matches,
                gxdRouter.getCat2Matches() + gxdRouter.getCat2Excludes(), conf)
        matchesFile[getMatchFileKey('Cat2', predType, refID)].write(matchRpt)

    # end routing loop

    # close Routing and Match files
    routingsFile.close()
    for f in matchesFile.values():
        f.close()

    # write details output file
    detailsFile = open(args.detailsFilename, 'w')
    detailsFile.write(timeString + '\n')
    detailsFile.write(gxdRouter.getExplanation())
    detailsFile.close()

    # compute Precision, Recall, write summary
    summary = 'Summary\n'
    for counts, label in [(allCounts, 'Overall'), (keepCounts, 'Keeps'),
                                                    (discCounts, 'Discards')]:
        numRefs = sum(counts.values())
        summary += "%s - Total Refs: %d\n" % (label, numRefs)

        summaryLineItems = []
        p, r, npv = computeMetrics(counts)
        summaryLineItems.append("Precision %.2f" % p)
        summaryLineItems.append("Recall %.2f" % r)
        summaryLineItems.append("NPV %.2f" % npv)
        summary += '   '.join(summaryLineItems) + '\n'

        summary += "    TP      FP      TN      FN\n"
        countLineItems = []
        numRefs = 0
        for predType in ['TP', 'FP', 'TN', 'FN']:
            countLineItems.append("%6d" % counts[predType])
        summary += ', '.join(countLineItems) + '\n'

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

def getMatchFileKey(cat, predType, refID):
    """ Compute and return the key into the dict of Match output files
        For predTypes FP, TN, FN, this is just (cat, predType)
        For predType TP, the output files are split based on the modulus of
            the last two digits of the reference ID
            (because there are so many TP, the files get too big to import
            into Excel or Google Sheets)
    """
    if predType == 'TP':
        lastDig = int(refID[-2:])
        dig = lastDig % fileSplitModulus
        key = (cat, predType, dig)
    else:
        key = (cat, predType)
    return key
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
