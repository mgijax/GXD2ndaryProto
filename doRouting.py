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
import GXDrefSample as SampleLib
from sklearnHelperLib import predictionType
#from utilsLib import removeNonAscii
#-----------------------------------

sampleObjType = SampleLib.ClassifiedRefSample

#-----------------------------------

def getArgs():

    parser = argparse.ArgumentParser( \
        description='test routing algorithm for GXD 2ndary triage proto, read testSet from stdin')

    parser.add_argument('baseName', action='store',
        help="output base file name. 'test' to just run automated tests. " +
            "'static' to output static term analysis to stdout.")

    parser.add_argument('-l', '--limit', dest='nToDo',
        required=False, type=int, default=0, 		# 0 means ALL
        help="only process this many references. Default is no limit")

    parser.add_argument('--textlength', dest='maxTextLength',
        type=int, required=False, default=None,
        help="only include the 1st n chars of text fields (for debugging)")

    parser.add_argument('-q', '--quiet', dest='verbose', action='store_false',
        required=False, help="skip helpful messages to stderr")

    #defaultHost = os.environ.get('PG_DBSERVER', 'bhmgidevdb01')
    #defaultDatabase = os.environ.get('PG_DBNAME', 'prod')

    #parser.add_argument('-s', '--server', dest='server', action='store',
    #    required=False, default=defaultHost,
    #    help='db server. Shortcuts:  adhoc, prod, dev, test. (Default %s)' %
    #            defaultHost)

    #parser.add_argument('-d', '--database', dest='database', action='store',
    #    required=False, default=defaultDatabase,
    #    help='which database. Example: mgd (Default %s)' % defaultDatabase)

    args =  parser.parse_args()

    #if args.server == 'adhoc':
    #    args.host = 'mgi-adhoc.jax.org'
    #    args.db = 'mgd'
    #elif args.server == 'prod':
    #    args.host = 'bhmgidb01.jax.org'
    #    args.db = 'prod'
    #elif args.server == 'dev':
    #    args.host = 'mgi-testdb4.jax.org'
    #    args.db = 'jak'
    #elif args.server == 'test':
    #    args.host = 'bhmgidevdb01.jax.org'
    #    args.db = 'prod'
    #else:
    #    args.host = args.server
    #    args.db = args.database

    return args
#-----------------------------------

args = getArgs()
args.routingsFilename = "%sRoutings.txt" % args.baseName
args.detailsFilename  = "%sDetails.txt" % args.baseName
args.details2Filename = "%sDetails.1line.txt" % args.baseName
args.matchesFilename  = "%sMatches.txt" % args.baseName
args.summaryFilename  = "%sSummary.txt" % args.baseName

SKIPJOURNALFILENAME='/Users/jak/work/GXD2ndaryProto/skipJournals.txt'

#-----------------------------------
class GXDrouter (object):
    cat1Terms = ['__mouse_age']
    #cat1Terms = ['embryo', '__mouse_age']
    # Not using the x.upper() right now as we are not replacing these terms
    cat1TermsDict = {x.lower() : x.upper() for x in cat1Terms}

    cat1Exclude= [
        "anat embryol",
        "embryonic stem",
        "embryogenesis",
        "embryonic lethal",
        "embryo lethal",
        "human embryonic",
        "rat embryo",
        "chick embryo",
        "cultured embryo",
        "embryo culture",
        "embryoid body",
        "zebrafish embryo",
        "embryology",
        "embryonic science",
        "drosophila embryo",
        "embryonic fibroblast",
        "embryo fibroblast",
        "embryoid bodies",
        "embryo implantation",
        "embryos die",
        "embryonic-lethal",
        "embryonic death",
        "embryonically lethal",
        "embryonated",
        "manipulating the mouse embryo: a laboratory manual",
        "chimera embryo",
        "embryonal",
        "embryonic viability",
        "chicken embryo",
        "embryo manip",
        "embryonic mortality",
        "postembryon",
        "embryonic carcinoma",
        "Anat. Embryol.",
        "embryo injection",
        "carcinoembryonic",
        "HEK293T  embryo",
        "d'embryologie",
        "embryonic cell line",
        "embryonic kidney cells",
        "embryonic myosin",
        "embryonic myogenesis",
        "microinjected embryo",
        "injected embryo",
        "human embryo",
        "embryonic chick",
        "bovine embryo",
        "Xenopus embryo",
        "embryonic kidney 293",
        "embryo production",
        "embryo survival",
        "embryo transfer",
        "embryo yield",
        "embryo loss",
        "embryo resorption",
        "embryo treated",
        "transferred embryo",
        "embryo exposed",
        "embryos were injected",
        "embryos were cultured",
        "porcine embryo",
        "embryo medium",
        "laevis embryo",
        "in vitro embryo",
        "hpf embryo",
        "treated embryo",
        "embryos were treated",
        "cattle embryo",
        "goat embryo",
        "embryonic rat",
        "transgenic embryo",
        "urchin embryo",
        "embryos microinject",
        "chimeric embryo",
        "embryonic culture",
        "medaka embryo",
        "avian embryo",
        "embryo was dissociated",
        "fish embryo",
        "embryonic medium",
        "broiler embryo",
        "parthenogenetic embryo",
        "elegans embryo",
        "worm embryo",
        "fly embryo",
        "ivp embryo",
        "embryos injected",
        "embryonic engineering",
        "embryonic alkaline phosphatase",
        "embryo-grade",
        ]
    # mapping of lower case exclude terms to what to replace them with
    #  (for now, map them to upper case so they won't be matched by cat1Terms)
    cat1ExcludeDict = {x.lower() : x.upper() for x in cat1Exclude}

    cat2Terms = ['immunoblot',
                'immunolabel',
                'immunostain',
                'immunoreact',
                'immunolocali',
                'immunofluorescen',
                'immunohistochem',
                'Northern',
                'Western',
                'in situ',
                'in-situ',
                'knock-in',
                'RT PCR',
                'RT-PCR',
                'qRT PCR',
                'qRT-PCR',
                'RT qPCR',
                'RT-qPCR',
                'Real time pcr',
                'Real-time pcr',
                'Real time qpcr',
                'Real-time qpcr',
                'quantitative PCR',
                'qPCR',
                'pcr',
                'GFP',
                'lacz',
                'Xgal',
                'X-gal',
                'X gal',
                'section',
                'whole mount',
                'whole-mount',
                'mount',
                'mRNA level',
                'smFish',
                #'__mouse_age',
                ]
    cat2Terms = [               # Connies new set of terms 5/10/2022
                'blot',
                'digoxygenin',
                'expression',
                'gfp',
                'immuno',
                'in situ',
                'in-situ',
                'knockin',
                'knock in',     # Connie didn't include this
                'knock-in',
                'lacz',
                ' mount',
                'mrna level',
                'northern',
                'pcr',
                'reporter',
                'rnascope',
                'section',
                'smfish',
                'stain',
                'western',
                'x gal',
                'xgal',
                'x-gal',
                ]
    #cat2Terms = ['__mouse_age']
    # Not using the x.upper() right now as we are not replacing these terms
    cat2TermsDict = {x.lower() : x.upper() for x in cat2Terms}

    def __init__(self, numChars=20):
        self.numChars = numChars  # num of chars of surrounding context to keep
        self.skipJournals = { line[:-1] for line in open(SKIPJOURNALFILENAME, 'r') }

    def getExplanation(self):
        output = ''
        output += 'Category1 terms in figtext:\n'
        for t in sorted(self.cat1TermsDict.keys()):
            output += "\t'%s'\n" % t

        output += 'Category2 terms in figtext:\n'
        for t in sorted(self.cat2TermsDict.keys()):
            output += "\t'%s'\n" % t

        output += 'Category1 Exclude terms:\n'
        for t in sorted(self.cat1ExcludeDict.keys()):
            output += "\t'%s'\n" % t

        output += 'Route=No for these journals:\n'
        for t in sorted(self.skipJournals):
            output += "\t'%s'\n" % t

        output += '-' * 50 + '\n'
        return output

    def routeThisRef_someFullText(self, ref):
    #def routeThisRef(self, ref):
        """ Given a reference (ClassifiedRefSample), return "Yes" or "No"
            Assumes the text of each reference is full text.
            Searches the full text for cat1 terms, applies figtext extraction
            for the cat2 terms
        """
        cat1MaCounts = {'total': 0}        # { 'matched term': count }
        cat1MaContexts = {}                # { 'matched term': [ (pre, post) ] }

        cat1ExcludeMaCounts = {'total': 0} # { 'matched term': count }

        cat2MaCounts = {'total': 0}        # { 'matched term': count }
        cat2MaContexts = {}                # { 'matched term': [ (pre, post) ] }

        self.cat1ExcludeMaCounts = cat1ExcludeMaCounts

        self.cat1MaCounts = cat1MaCounts
        self.cat1MaContexts = cat1MaContexts

        self.cat2MaCounts = cat2MaCounts
        self.cat2MaContexts = cat2MaContexts

        if ref.getField('journal') in self.skipJournals:
            return 'No'

        routing = "No"  # default routing (until we find matches)

        # go through text, replacing any cat1Exclude terms
        fullText = ref.getDocument()
        newText = fullText.replace('\n', ' ')
        for term, replacement in self.cat1ExcludeDict.items():
            splits = newText.split(term)
            newText = replacement.join(splits)
            # update counts for this term
            numMatches = (len(splits) -1)
            if numMatches:
                cat1ExcludeMaCounts[term] = numMatches
                cat1ExcludeMaCounts['total'] += numMatches

        # get cat1Term matches against full text
        self.getPositiveMatches(newText, self.cat1TermsDict.keys(),
                                                cat1MaCounts, cat1MaContexts)

        # get cat2 matches against figure text without age transformations
        ref.figureTextLegCloseWords50()
        #ref.textTransform_age()
        figText = ref.getDocument()
        self.getPositiveMatches(figText, self.cat2TermsDict.keys(),
                                                cat2MaCounts, cat2MaContexts)
        # determine routing
        if cat1MaCounts['total'] and cat2MaCounts['total']:
            routing = "Yes"

        return routing

    #def routeThisRef_figText(self, ref):
    def routeThisRef(self, ref):
        """ Given a reference (ClassifiedRefSample), return "Yes" or "No"
            Just use the text from each reference as is in the dataset,
                it is either all figure text or all full text
        """
        cat1MaCounts = {'total': 0}        # { 'matched term': count }
        cat1MaContexts = {}                # { 'matched term': [ (pre, post) ] }

        cat1ExcludeMaCounts = {'total': 0} # { 'matched term': count }

        cat2MaCounts = {'total': 0}        # { 'matched term': count }
        cat2MaContexts = {}                # { 'matched term': [ (pre, post) ] }

        self.cat1ExcludeMaCounts = cat1ExcludeMaCounts

        self.cat1MaCounts = cat1MaCounts
        self.cat1MaContexts = cat1MaContexts

        self.cat2MaCounts = cat2MaCounts
        self.cat2MaContexts = cat2MaContexts

        if ref.getField('journal') in self.skipJournals:
            return 'No'

        routing = "No"  # default routing (until we find matches)
        text = ref.getDocument()

        # go through text, replacing any cat1Exclude terms
        newText = text.replace('\n', ' ')
        for term, replacement in self.cat1ExcludeDict.items():
            splits = newText.split(term)
            newText = replacement.join(splits)
            # update counts for this term
            numMatches = (len(splits) -1)
            if numMatches:
                cat1ExcludeMaCounts[term] = numMatches
                cat1ExcludeMaCounts['total'] += numMatches

        # get cat1Term matches
        self.getPositiveMatches(newText, self.cat1TermsDict.keys(),
                                                cat1MaCounts, cat1MaContexts)

        # get cat2 matches
        self.getPositiveMatches(newText, self.cat2TermsDict.keys(),
                                                cat2MaCounts, cat2MaContexts)
        # determine routing
        if cat1MaCounts['total'] and cat2MaCounts['total']:
            routing = "Yes"

        return routing

    def getPositiveMatches(self, text, terms, maCounts, maContexts):
        """ Find all matches to 'terms' in 'text'
            Update maCounts[term] to number of term matches
            Update maContexts[term] to [ (pre, post) ... ] of surrounding
                pre and post text to each match
        """
        ctxLen = self.numChars
        textLen = len(text)
        for term in terms:
            termLen = len(term)
            maContexts[term] = []

            # find all matches to the term
            start = 0   # where to start the search from
            matchStart = text.find(term, start)
            while matchStart != -1:
                # update match counts
                maCounts[term] = maCounts.get(term, 0) +1
                maCounts['total'] += 1

                # store pre/post char context for this match
                preStart = max(0, matchStart-ctxLen)
                postEnd  = min(textLen, matchStart + termLen + ctxLen)
                pre  = text[ preStart: matchStart]
                post = text[ matchStart+termLen: postEnd]
                maContexts[term].append((pre,post))

                # find next match
                start = matchStart + termLen
                matchStart = text.find(term, start)

    def getCat1MaCounts(self): return self.cat1MaCounts
    def getCat1MaContexts(self): return self.cat1MaContexts
    def getCat1ExcludeMaCounts(self): return self.cat1ExcludeMaCounts

    def getCat2MaCounts(self): return self.cat2MaCounts
    def getCat2MaContexts(self): return self.cat2MaContexts
#-----------------------------------

FIELDSEP = '|'
routingHdr = FIELDSEP.join(['ID',
                    'knownClassName',
                    'routing',
                    'predType',
                    'Cat1 matches',
                    'Cat1 Exclude matches',
                    'Cat2 matches',
                    ] + sampleObjType.getExtraInfoFieldNames()) + '\n'

def formatRouting(r, routing, predType, numCat1Matches, numCat1ExcludeMatches,
                numCat2Matches):
    t = FIELDSEP.join([r.getID(),
                    r.getKnownClassName(),
                    routing,
                    predType,
                    str(numCat1Matches),
                    str(numCat1ExcludeMatches),
                    str(numCat2Matches),
                    ] + r.getExtraInfo()) + '\n'
    return t

def formatMatches(matches):
    output = ''
    for term, contexts in matches.items():
        if contexts:
            output += "%s:\n" % term
            for pre, post in contexts:
                output += "\t'%s%s%s'\n" % (pre, term.upper(), post)
    return output

def formatMatches2(ref, routing, predType, cat1MaContexts, cat2MaContexts):
    """ format cat1 and cat2 match contexts in 1 line for Jackie's 
        spreadsheet
    """
    output = '\t'.join([ref.getID(),
                        ref.getKnownClassName(),
                        routing,
                        predType,
                        ])
    for term in sorted(cat1MaContexts.keys()):
        termOutput = '|'.join([ "'%s%s%s'" % (pre, term.upper(), post) \
                                    for pre, post in cat1MaContexts[term]])
        output += '\t' + termOutput

    for term in sorted(cat2MaContexts.keys()):
        termOutput = '|'.join([ "'%s%s%s'" % (pre, term.upper(), post) \
                                    for pre, post in cat2MaContexts[term]])
        output += '\t' + termOutput

    return output + '\n'

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
    routingsFile.write(routingHdr)

    detailsFile = open(args.detailsFilename, 'w')
    detailsFile.write(timeString + '\n')
    detailsFile.write(gxdRouter.getExplanation())
    detailsFile.write(routingHdr + '\n')

    details2File = open(args.details2Filename, 'w')
    details2File.write(timeString + '\n')

    allCounts  = {'TP': 0, 'FP': 0, 'TN': 0, 'FN': 0}   # for all refs
    keepCounts = {'TP': 0, 'FP': 0, 'TN': 0, 'FN': 0}   # for keep refs
    discCounts = {'TP': 0, 'FP': 0, 'TN': 0, 'FN': 0}   # for discard refs

    numProcessed = 0            # total number of references processed

    if args.nToDo > 0: samples = testSet.getSamples()[:args.nToDo]
    else: samples = testSet.getSamples()

    # for each record, routeThisRef(), gather counts, write list of routings
    for i, ref in enumerate(samples):
        routing = gxdRouter.routeThisRef(ref)
        numCat1Matches = gxdRouter.getCat1MaCounts()['total']
        numCat1ExcludeMatches = gxdRouter.getCat1ExcludeMaCounts()['total']
        numCat2Matches = gxdRouter.getCat2MaCounts()['total']

        predType = predictionType(ref.getKnownClassName(), routing,
                                                        positiveClass='Yes')
        allCounts[predType] += 1

        relevance = ref.getField('relevance')
        if relevance == 'keep':
            keepCounts[predType] += 1
        else:
            discCounts[predType] += 1

        numProcessed += 1

        r = formatRouting(ref, routing, predType, numCat1Matches,
                                        numCat1ExcludeMatches, numCat2Matches)
        routingsFile.write(r)

        matchReport = formatMatches(gxdRouter.getCat1MaContexts())
        matchReport += formatMatches(gxdRouter.getCat2MaContexts())
        excludeReport = formatExcludes(gxdRouter.getCat1ExcludeMaCounts())
        detailsFile.write(r)
        detailsFile.write(matchReport)
        detailsFile.write(excludeReport)
        detailsFile.write('\n')

        if i == 0:      # 1st record, output header for 1line details file
            hdr2 = '\t'.join(['ID',
                            'knownClassName',
                            'routing',
                            'predType',
                            ]
                            + sorted(gxdRouter.getCat1MaContexts().keys())
                            + sorted(gxdRouter.getCat2MaContexts().keys())
                            ) + '\n'
            details2File.write(hdr2)
        details2Report = formatMatches2(ref, routing, predType,
                                                gxdRouter.getCat1MaContexts(),
                                                gxdRouter.getCat2MaContexts(),)
        details2File.write(details2Report)
    # end routing loop

    routingsFile.close()
    detailsFile.close()
    details2File.close()

    # write overall matches (aggregated across all references)
    # not implemented yet.

    # compute Precision, Recall, write summary
    summary = 'Summary\n'
    for counts, label in [(allCounts, 'Overall'), (keepCounts, 'Keeps'),
                                                    (discCounts, 'Discards')]:
        summary += label + '\n'
        for predType in ['TP', 'FP', 'TN', 'FN']:
            summary += "%s: %d\n" % (predType, counts[predType])

        p, r, npv = computeMetrics(counts)
        summary += "Precision: %.2f%%\n" % p
        summary += "Recall   : %.2f%%\n" % r
        summary += "NPV      : %.2f%%\n" % npv
        summary += '\n'

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
    elif args.baseName == 'static': doStaticAnalysis()
    else: process()

    exit(0)
#-----------------------------------
class TermStats (object):
    def __init__(self, term, numPos, numNeg):
        self.term = term
        self.numPos = numPos
        self.numNeg = numNeg

def doStaticAnalysis():
    startTime = time.time()
    timeString = time.ctime()
    verbose(timeString + '\n')
    gxdRouter = GXDrouter(numChars=30)
    #converter = figureText.Text2FigConverter(conversionType='legCloseWords')

    testSet = SampleLib.ClassifiedSampleSet(sampleObjType=sampleObjType)
    testSet.read(sys.stdin)

    if args.nToDo > 0: samples = testSet.getSamples()[:args.nToDo]
    else: samples = testSet.getSamples()

    verbose('read %d refs for static analysis\n' % testSet.getNumSamples())
    verbose("%8.3f seconds\n\n" %  (time.time()-startTime))

    totalNumPos = testSet.getNumPositives()
    totalNumNeg = testSet.getNumNegatives()
    TermsAndStats = []
    header = "'%s'\t%s\t%s\t%s\t%s\t%s\n" % ('term', 'numPos', 'numNeg',
                                        'posFraction', 'negFraction', 'dValue')
    sys.stdout.write(header)

    ageCategories = ['__eday', '__dpc', '__ts', '__early_embryo',
                    '__developmental', '__fetus_al']
    for term in gxdRouter.cat1Terms + gxdRouter.cat2Terms + ageCategories:
        term = term.lower()
        numPos = 0
        numNeg = 0
        for i, ref in enumerate(samples):
            if i % 200 == 0: verbose('.')

            text = ref.getDocument()
            #text = ' '.join(converter.text2FigText(text))   # doesn't work yet

            # remove exclude terms first
            newText = text.replace('\n', ' ')
            for exTerm, replacement in gxdRouter.cat1ExcludeDict.items():
                splits = newText.split(exTerm)
                newText = replacement.join(splits)

            if newText.find(term) != -1:
                if ref.isPositive():
                    numPos += 1
                else:
                    numNeg += 1
        ts = TermStats(term, numPos, numNeg)
        ts.posFraction = numPos / totalNumPos
        ts.negFraction = numNeg / totalNumNeg
        ts.dValue = ts.posFraction - ts.negFraction     # discrimative value
        TermsAndStats.append(ts)

        sys.stdout.write("'%s'\t%d\t%d\t%.2f\t%.2f\t%.2f\n" % \
                        (ts.term, ts.numPos, ts.numNeg,
                        ts.posFraction, ts.negFraction, ts.dValue))
    verbose("%8.3f seconds\n\n" %  (time.time()-startTime))
    return
#-----------------------------------
if __name__ == "__main__":
    main()
