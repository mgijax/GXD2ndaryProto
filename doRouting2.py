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
'''
import sys
import os
import time
import argparse
import re
import unittest
import figureText
import GXDrefSample as SampleLib
from sklearnHelperLib import predictionType
from utilsLib import MatchRcd, TextMapping, TextMappingFromStrings, TextTransformer
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


class SimpleTextMappingFromStrings (TextMappingFromStrings):

    def _str2regex(self, s):
        """ replace spaces w/ r'\s', no forced word boundaries
        """
        parts = s.split()
        regex = r'\s'.join(map(re.escape, parts))
        return regex
#-----------------------------------

class GXDrouter (object):

    def __init__(self,
                skipJournals,   # [journal names] whose articles don't route
                cat1Terms,      # [category 1 terms]
                cat1Exclude,    # [category 1 exclude terms]
                ageExclude,     # [age exclude terms]
                cat2Terms,      # [category 2 terms]
                cat2Exclude,    # [category 2 exclude terms]
                numChars=30,    # n chars on each side of a match to report
                ):
        self.numChars = numChars  # num of chars of surrounding context to keep
        self.skipJournals = {j for j in skipJournals} # set of journal names
        self.cat1Terms    = cat1Terms
        self.cat1Exclude  = cat1Exclude
        self.ageExclude   = ageExclude
        self.cat2Terms    = cat2Terms
        self.cat2Exclude  = cat2Exclude

        self.figTextConverter = figureText.Text2FigConverter( \
                                            conversionType='legCloseWords',
                                            numWords=50)
        self._buildCat1Detection()
        self._buildCat2Detection()
        self._buildMouseAgeDetection()
        return

    def _buildCat1Detection(self):
        # Set up for using text comparisons
        # mapping of lower case exclude terms to what to replace them with
        self.cat1TermsDict   = {x.lower() : x.upper() for x in self.cat1Terms}
        self.cat1ExcludeDict = {x.lower() : x.upper() for x in self.cat1Exclude}

        # Set up for using TextTransformer - skipping for now
        #self.cat1ExcludeMapping = SimpleTextMappingFromStrings(
        #                                'embryoExclude',
        #                                self.cat1Exclude, lambda x: x.upper(),
        #                                context=0)
        #self.cat1Mapping = TextMapping('embryo', r'(?:embryo)',
        #                                lambda x: x.upper(), context=0)
        #self.cat1TextTransformer = TextTransformer([
        #    self.cat1ExcludeMapping,
        #    self.cat1Mapping,
        #    ])
        return

    def _gotCat1(self, text):
        """ Return True if text contains a cat1 term not in an exclude context.
        """
        # use text comparisons
        newText, self.cat1Excludes = findMatches(text,
                            self.cat1ExcludeDict, 'excludeCat1', self.numChars)
        newText, self.cat1Matches = findMatches(newText,
                            self.cat1TermsDict, 'cat1', self.numChars)
        return len(self.cat1Matches)
        # use TextTransformer - much slower, should investigate, 
        #tt = self.cat1TextTransformer
        #tt.resetMatches()
        #newText = tt.transformText(text)
        #matchRcds = self.cat1Mapping.getMatchRcds()
        #return len(matchRcds)
        ##if newText.find('embryo') == -1: return False
        ##else: return True

    def _buildCat2Detection(self):
        # Set up for using text comparisons
        # mapping of lower case exclude terms to what to replace them with
        self.cat2TermsDict   = {x.lower() : x.upper() for x in self.cat2Terms}
        self.cat2ExcludeDict = {x.lower() : x.upper() for x in self.cat2Exclude}
        return

    def _gotCat2(self, text):
        """ Return True if text contains a cat2 term not in an exclude context.
        """
        newText, self.cat2Excludes = findMatches(text,
                            self.cat2ExcludeDict, 'excludeCat2', self.numChars)
        newText, self.cat2Matches = findMatches(newText,
                            self.cat2TermsDict, 'cat2', self.numChars)
        return len(self.cat2Matches)

    def _buildMouseAgeDetection(self):
        self.ageTextTransformer = TextTransformer(SampleLib.AgeMappings)
        self.ageExcludeDict = {x.lower() : x.upper() for x in self.ageExclude}
            # re to detect strings that would prohibit an age exclude term
            #   from causing the exclusion if they occur between
            #   the exclude term and the matching age text:
            #     '; ' or  '. ' or '\n\n' (paragraph boundary)
        self.ageExcludeBlockRE = re.compile(r'[;.]\s|\n\n')

    def _gotMouseAge(self, text):
        """ Return True if we find mouse age terms in text
        """
        newText = self.ageTextTransformer.transformText(text)

        # get ageMatches and throw away "fix" matches
        ageMatches = [ m for m in self.ageTextTransformer.getMatches()
                                        if not m.matchType.startswith('fix')] 

        # check preText and postText to detect exclude age matches
        for m in ageMatches:
            if self._isGoodAgeMatch(m):
                self.ageMatches.append(m)
            else:
                self.ageExcludes.append(m)

        self.ageTextTransformer.resetMatches()
        return len(self.ageMatches)

    def _isGoodAgeMatch(self, m # MatchRcd
                        ):
        """ Return True if this looks like a good mouse age match.
            If not a good mouse age, return False and:
                Modify m.preText or m.postText to highlight the text that
                    indicates it is not a good match,
                Set m.matchType to 'excludeAge'
        """
        #return True
        goodAgeMatch = True     # assume no exclusion terms detected

        # search m.preText for age exclusion terms
        newText, preTextMatches = findMatches(m.preText, self.ageExcludeDict,
                                                                'excludeAge', 0)
        for em in preTextMatches:       # for exclusion matches in preText
            if not self.ageExcludeBlockRE.search(m.preText[em.end:]):
                # no intervening text found that should block the exclude
                newPreText = m.preText[:em.start] + em.replText + \
                                                            m.preText[em.end:]
                m.preText = newPreText
                goodAgeMatch = False
                break

        # search m.postText for age exclusion terms
        newText, postTextMatches = findMatches(m.postText, self.ageExcludeDict,
                                                                'excludeAge', 0)
        for em in postTextMatches:      # for exclusion matches in postText
            if not self.ageExcludeBlockRE.search(m.postText[:em.start]):
                # no intervening text found that should block the exclude
                newPostText = m.postText[:em.start] + em.replText + \
                                                            m.postText[em.end:]
                m.postText = newPostText
                goodAgeMatch = False
                break

        if not goodAgeMatch:
            m.matchType = 'excludeAge'
        return goodAgeMatch
    
    def routeThisRef(self, refID, text, journal):
        """ Given info about a reference, return "Yes" or "No"
            Assumes the text of each reference is full text.
            Assumes the text is all lower case.
            Checks journal.
            Searches the full text for cat1 terms.
            Searches figure text for mouse_age and cat2 terms.
        """
        self.cat1Matches = []
        self.cat1Excludes = []
        self.ageMatches = []
        self.ageExcludes = []
        self.cat2Matches = []
        self.cat2Excludes = []

        # uncomment out next line if we are not guarranteed that text is
        #  already all lower case.
        # text = text.lower() # to make things case insensitive

        # for reporting purposes, do all the checks, even though we could
        #   return "No" upon the first failed check

        if journal in self.skipJournals:
            self.goodJournal = 0
        else:
            self.goodJournal = 1

        gotCat1     = self._gotCat1(text)

        figText = '\n\n'.join(self.figTextConverter.text2FigText(text))
        gotMouseAge = self._gotMouseAge(figText)
        gotCat2     = self._gotCat2(figText)

        if gotCat1 and gotMouseAge and gotCat2 and self.goodJournal:
            return 'Yes'
        else:
            return 'No'

    def getExplanation(self):
        output = ''
        output += 'Category1 terms in full text:\n'
        for t in sorted(self.cat1TermsDict.keys()):
            output += "\t'%s'\n" % t

        output += 'Category1 Exclude terms:\n'
        for t in sorted(self.cat1ExcludeDict.keys()):
            output += "\t'%s'\n" % t

        output += 'Category2 terms in figure text:\n'
        for t in sorted(self.cat2TermsDict.keys()):
            output += "\t'%s'\n" % t

        output += 'Category2 Exclude terms:\n'
        for t in sorted(self.cat2ExcludeDict.keys()):
            output += "\t'%s'\n" % t

        output += 'Mouse age regular expression - searched in figure text:\n'
        output += self.ageTextTransformer.getBigRegex() + '\n'

        output += 'Mouse Age Exclude terms:\n'
        for t in sorted(self.ageExcludeDict.keys()):
            output += "\t'%s'\n" % t

        output += 'Route=No for these journals:\n'
        for t in sorted(self.skipJournals):
            output += "\t'%s'\n" % t

        output += '-' * 50 + '\n'
        return output

    def getGoodJournal(self):  return self.goodJournal
    def getCat1Matches(self):  return self.cat1Matches
    def getCat1Excludes(self): return self.cat1Excludes
    def getAgeMatches(self):   return self.ageMatches
    def getAgeExcludes(self):  return self.ageExcludes
    def getCat2Matches(self):  return self.cat2Matches
    def getCat2Excludes(self): return self.cat2Excludes

    def getPosMatches(self):
        return self.cat1Matches + self.ageMatches + self.cat2Matches

    def getExcludeMatches(self):
        return self.cat1Excludes + self.ageExcludes + self.cat2Excludes

    def getAllMatches(self):
        all = self.cat1Matches + self.cat1Excludes + self.ageMatches + \
                self.ageExcludes + self.cat2Matches + self.cat2Excludes
        return all

#-----------------------------------

def findMatches(text, termDict, matchType, ctxLen):
    """ find all matches in text for terms in the termDict:
            {'term': 'replacement text for the term'}.
        Return the modified text and list of MatchRcds for all the matches.
        In addition to the term replacements, the modified text has all
            '\n' replaced by ' '.
        Note: the order that the terms are matched against the text is random,
        so if some terms are substrings of other terms, which one matches
        first is undefined.
    """
    resultText = text           # resulting text if there are no terms to match

    findText = text.replace('\n', ' ')  # so we can match terms across lines
                                        # ..this is the text to search in.

    matchRcds = []                      # the matches to return

    textLen = len(text)

    for term, replacement in termDict.items():
        termLen = len(term)
        resultText = ''      # modified text from this term's transformations

        # find all matches to the term
        start = 0   # where to start the search from
        matchStart = findText.find(term, start)
        matchEnd = 0
        while matchStart != -1:     # got a match
            matchEnd = matchStart + termLen
            matchText = text[matchStart : matchEnd]

            preStart = max(0, matchStart-ctxLen)
            postEnd  = min(textLen, matchEnd + ctxLen)
            pre  = text[preStart : matchStart]
            post = text[matchEnd : postEnd]

            m = MatchRcd(matchType, matchStart, matchEnd, matchText,
                                                pre, post, replacement)
            matchRcds.append(m)

            resultText += findText[start : matchStart] + replacement

            # find next match
            start = matchEnd
            matchStart = findText.find(term, start)

        resultText += findText[matchEnd:]    # text after last match
        findText = resultText         # for next term, search the modified text

    return resultText, matchRcds
#-----------------------------------

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
    cat1Terms = ['embryo']

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

    #sys.stdout.write("No automated tests at this time\n")
    #return
    sys.stdout.write("Running automated unit tests...\n")
    unittest.main(argv=[sys.argv[0], '-v'],)

class MyTests(unittest.TestCase):
    def test_findMatches(self):
        termDict = {'the start': 'THE START', 'middle': 'MIDDLE',
                    'the end': 'THE END'}
        text     = 'the start. the middle.\nthe\nend'
        expected = 'THE START. the MIDDLE. THE END'
        newText, matches = findMatches(text, termDict, 'textMatches', 5)
        self.assertEqual(newText, expected)

        self.assertEqual(len(matches), 3)
        m = matches[1]
        self.assertEqual(m.postText, '.\nthe')
#-----------------------------------

def main():
    if   args.baseName == 'test': doAutomatedTests()
    else: process()

    exit(0)
#-----------------------------------
if __name__ == "__main__":
    main()
