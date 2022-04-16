#!/usr/bin/env python3
'''
  Purpose: Apply a potential GXD secondary triage routing algorithm & evaluate.

  Inputs:  Sample file of GXD routed (classified) reference records.
            See refSample.py for the fields of these records.
  
  Outputs: a file of Routing assignments, 1 line for each reference
           a file of "details" for each routing assignment, e.g.,
                what term matches there were for each reference (+ context)
           a file of term matches across the whole corpus
               Positive words: context & counts
               Exclude words: counts
           a summary of Precision and Recall

           You pass filename base prefix, e.g., 'Try1' as a cmd line param
           and the output files are named:
               Try1Routings.txt
               Try1Details.txt
               Try1Matches.txt
               Try1Summary.txt
'''
import sys
import os
import time
import argparse
import unittest
#import db
import refSample as SampleLib
from sklearnHelperLib import predictionType
#from utilsLib import removeNonAscii
#-----------------------------------

sampleObjType = SampleLib.ClassifiedRefSample

#-----------------------------------

def getArgs():

    parser = argparse.ArgumentParser( \
        description='test routing algorithm for GXD 2ndary triage proto, read testSet from stdin')

    parser.add_argument('baseName', action='store',
        help="output base file name. 'test' to just run automated tests")

    parser.add_argument('-l', '--limit', dest='nToDo',
        required=False, type=int, default=0, 		# 0 means ALL
        help="only process this many references. Default is no limit")

    parser.add_argument('--textlength', dest='maxTextLength',
        type=int, required=False, default=None,
        help="only include the 1st n chars of text fields (for debugging)")

    parser.add_argument('-q', '--quiet', dest='verbose', action='store_false',
        required=False, help="skip helpful messages to stderr")

    defaultHost = os.environ.get('PG_DBSERVER', 'bhmgidevdb01')
    defaultDatabase = os.environ.get('PG_DBNAME', 'prod')

    parser.add_argument('-s', '--server', dest='server', action='store',
        required=False, default=defaultHost,
        help='db server. Shortcuts:  adhoc, prod, dev, test. (Default %s)' %
                defaultHost)

    parser.add_argument('-d', '--database', dest='database', action='store',
        required=False, default=defaultDatabase,
        help='which database. Example: mgd (Default %s)' % defaultDatabase)

    args =  parser.parse_args()

    if args.server == 'adhoc':
        args.host = 'mgi-adhoc.jax.org'
        args.db = 'mgd'
    elif args.server == 'prod':
        args.host = 'bhmgidb01.jax.org'
        args.db = 'prod'
    elif args.server == 'dev':
        args.host = 'mgi-testdb4.jax.org'
        args.db = 'jak'
    elif args.server == 'test':
        args.host = 'bhmgidevdb01.jax.org'
        args.db = 'prod'
    else:
        args.host = args.server
        args.db = args.database

    return args
#-----------------------------------

args = getArgs()
args.routingsFilename = "%sRoutings.txt" % args.baseName
args.detailsFilename  = "%sDetails.txt" % args.baseName
args.matchesFilename  = "%sMatches.txt" % args.baseName
args.summaryFilename  = "%sSummary.txt" % args.baseName

#-----------------------------------
class GXDrouter (object):
    cat1Terms = ['embryo']
    # mapping of lower case exclude terms to what to replace them with
    #  (for now, map them to upper case so they won't be matched by cat1Terms)
    cat1TermsDict = {x.lower() : x.upper() for x in cat1Terms}

    cat1Exclude= [
        "embryonic lethal",
        "embryonic science",
        "embryonic death",
        "manipulating the mouse embryo: a laboratory manual",
        "Anat. Embryol.",
        "embryonic chick",
        "anat embryol",
        "embryonic stem",
        "embryogenesis",
        "drosophila embryo",
        "embryoid bodies",
        "d'embryologie",
        "microinjected embryo",
        "embryonic fibroblast",
        "embryo fibroblast",
        "human embryonic stem",
        "embryo implantation",
        "embryos die",
        "embryonic-lethal",
        "embryonically lethal",
        "embryonated",
        "chimera embryo",
        "embryonal stem",
        "embryonic viability",
        "chicken embryo",
        "embryo manip",
        "embryonic mortality",
        "postembryon",
        "embryonic carcinoma",
        "embryo injection",
        "carcinoembryonic",
        "HEK293T  embryo",
        "embryonic cell line",
        "embryonic kidney cells",
        "embryonic myosin",
        "embryonic myogenesis",
        "injected embryo",
        "human embryo",
        "embryonated chick",
        "embryo lethal",
        "human embryonic",
        "rat embryo",
        "chick embryo",
        "cultured embryo",
        "embryo culture",
        "embryoid body",
        "zebrafish embryo",
        "embryology",
        "bovine embryo",
        "embryonal rhabdomyosarcoma",
        "Xenopus embryo",
        "embryonic rat",
        "embryonic kidney 293",
        "embryonal fibroblast",
        ]
    # mapping of lower case exclude terms to what to replace them with
    #  (for now, map them to upper case so they won't be matched by cat1Terms)
    cat1ExcludeDict = {x.lower() : x.upper() for x in cat1Exclude}

    def __init__(self, numChars=20):
        self.numChars = numChars  # num of chars of surrounding context to keep

    def getExplanation(self):
        output = 'Category1 terms:\n'
        for t in sorted(self.cat1TermsDict.keys()):
            output += "\t'%s'\n" % t

        output += 'Category1 Exclude terms:\n'
        for t in sorted(self.cat1ExcludeDict.keys()):
            output += "\t'%s'\n" % t
        output += '-' * 50 + '\n'
        return output

    def routeThisRef(self, text):
        """ given the text of a reference, return "Yes" or "No"
        """
        cat1MatchCounts = {'total': 0}  # { 'matched term': count }
        cat1Matches = {}                # { 'matched term': [ (pre, post) ] }
        cat1ExcludeMatchCounts = {'total': 0}  # { 'matched term': count }
        routing = "No"

        # go through text, replacing any cat1Exclude terms
        newText = text
        for term, replacement in self.cat1ExcludeDict.items():
            splits = newText.split(term)
            newText = replacement.join(splits)
            # update counts for this term
            numMatches = (len(splits) -1)
            if numMatches:
                cat1ExcludeMatchCounts[term] = numMatches
                cat1ExcludeMatchCounts['total'] += numMatches

        # get cat1Term matches
        ctxLen = self.numChars
        textLen = len(newText)
        for term in self.cat1TermsDict.keys():
            termLen = len(term)

            # find all matches to the term
            start = 0   # where to start the search from
            matchStart = newText.find(term, start)
            while matchStart != -1:
                # update match counts
                cat1MatchCounts[term] = cat1MatchCounts.get(term, 0) +1
                cat1MatchCounts['total'] += 1

                # store pre/post char context for this match
                preStart = max(0, matchStart-ctxLen)
                postEnd  = min(textLen, matchStart + termLen + ctxLen)
                pre  = newText[ preStart: matchStart]
                post = newText[ matchStart+termLen: postEnd]
                if not term in cat1Matches:
                    cat1Matches[term] = []
                cat1Matches[term].append((pre,post))

                # find next match
                start = matchStart + termLen
                matchStart = newText.find(term, start)

        if cat1MatchCounts['total']: routing = "Yes"

        self.cat1Matches = cat1Matches
        self.cat1ExcludeMatchCounts = cat1ExcludeMatchCounts

        return routing, cat1MatchCounts['total'], cat1ExcludeMatchCounts['total']

    def getCat1Matches(self): return self.cat1Matches
    def getCat1ExcludeMatchCounts(self): return self.cat1ExcludeMatchCounts
#-----------------------------------

FIELDSEP = '|'
hdr = FIELDSEP.join(['ID',
                    'knownClassName',
                    'routing',
                    'predType',
                    'Cat1 matches',
                    'Cat1 Exclude matches',
                    ] + sampleObjType.getExtraInfoFieldNames()) + '\n'

def formatRouting(r, routing, predType, numMatches, numExcludeMatches):
    t = FIELDSEP.join([r.getID(),
                    r.getKnownClassName(),
                    routing,
                    predType,
                    str(numMatches),
                    str(numExcludeMatches),
                    ] + r.getExtraInfo()) + '\n'
    return t

def formatMatches(matches):
    output = ''
    for term, contexts in matches.items():
        output += "%s:\n" % term
        numSpaces = len(term) +1
        for pre, post in contexts:
            output += " " * numSpaces
            output += "'%s%s%s'\n" % (pre, term.upper(), post)
    return output

def formatExcludes(counts):
    output = 'Exclude term match counts:\n'
    for term in sorted(counts.keys()):
        if term != 'total' and counts[term]:
            output += "%4d '%s'\n" % (counts[term], term)
    return output

#-----------------------------------

def process():
    ''' go through the refs and determine routing
    '''
    startTime = time.time()
    timeString = time.ctime()
    verbose(timeString + '\n')
    gxdRouter = GXDrouter(numChars=30)

    # get testSet from stdin
    testSet = SampleLib.ClassifiedSampleSet(sampleObjType=sampleObjType)
    testSet.read(sys.stdin)
    verbose('read %d refs to determine routing\n' % testSet.getNumSamples())
    verbose("%8.3f seconds\n\n" %  (time.time()-startTime))

    # set up output files and various counts
    routingsFile = open(args.routingsFilename, 'w')
    routingsFile.write(timeString + '\n')
    routingsFile.write(hdr)

    detailsFile = open(args.detailsFilename, 'w')
    detailsFile.write(timeString + '\n')
    detailsFile.write(gxdRouter.getExplanation())
    detailsFile.write(hdr + '\n')

    counts = {'TP': 0, 'FP': 0, 'TN': 0, 'FN': 0}
    numProcessed = 0

    if args.nToDo > 0: samples = testSet.getSamples()[:args.nToDo]
    else: samples = testSet.getSamples()

    # for each record, routeThisRef(), gather counts, write list of routings
    for ref in samples:
        text = ref.getDocument()
        routing, numMatches, numExcludeMatches = gxdRouter.routeThisRef(text)

        predType = predictionType(ref.getKnownClassName(), routing,
                                                        positiveClass='Yes')
        counts[predType] += 1
        numProcessed += 1

        r = formatRouting(ref, routing, predType, numMatches, numExcludeMatches)
        routingsFile.write(r)

        matchReport = formatMatches(gxdRouter.getCat1Matches())
        excludeReport = formatExcludes(gxdRouter.getCat1ExcludeMatchCounts())
        detailsFile.write(r)
        detailsFile.write(matchReport)
        detailsFile.write(excludeReport)
        detailsFile.write('\n')
    # end routing loop

    routingsFile.close()
    detailsFile.close()

    # write overall mappings to args.mappingsFilename

    # compute Precision, Recall, write summary
    p = counts['TP'] / (counts['TP'] + counts['FP']) * 100

    if (counts['TP'] + counts['FN']) == 0: r = 0.0      # check for zero div
    else: r = counts['TP'] / (counts['TP'] + counts['FN']) * 100

    if (counts['TN'] + counts['FN']) == 0: n = 0.0      # check for zero div
    else: n = counts['TN'] / (counts['TN'] + counts['FN']) * 100

    summary = 'Summary\n'
    for predType in ['TP', 'FP', 'TN', 'FN']:
        summary += "%s: %d\n" % (predType, counts[predType])

    summary += "Precision: %.2f%%\n" % p
    summary += "Recall   : %.2f%%\n" % r
    summary += "NPV      : %.2f%%\n" % n

    summaryFile = open(args.summaryFilename, 'w')
    summaryFile.write(timeString + '\n')
    summaryFile.write(summary)
    summaryFile.close()

    verbose(summary)
    verbose("wrote %d routings to '%s'\n" % (numProcessed,
                                                    args.routingsFilename))
    verbose("%8.3f seconds\n\n" %  (time.time()-startTime))

    return
#-----------------------------------

def verbose(text):
    if args.verbose:
        sys.stderr.write(text)
        sys.stderr.flush()
#-----------------------------------

def doAutomatedTests():

    sys.stdout.write("No automated tests at this time\n")
    return

    sys.stdout.write("Running automated unit tests...\n")
    unittest.main(argv=[sys.argv[0], '-v'],)

class MyTests(unittest.TestCase):
    pass
#    def test_getText4Ref(self):
#        t = getText4Ref('11943') # no text
#        self.assertEqual(t, '')
#
#        t = getText4Ref('361931') # multiple sections
#        expText = 'lnk/ mice.\n\n\n\nfig. 5.' # boundry body-author fig legends
#        found = t.find(expText)
#        self.assertNotEqual(found, -1)

#-----------------------------------

def main():
    if args.baseName == 'test': doAutomatedTests()
    else: process()

    exit(0)
#-----------------------------------
if __name__ == "__main__":
    main()
