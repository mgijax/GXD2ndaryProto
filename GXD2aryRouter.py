#!/usr/bin/env python3
'''
  Purpose: Define the classes that implement the GXD 2ary triage routing
            algorithm.
            To instantiate the class, you need vocabularies (lists of strings)
            for the vocabs listed below.

  To Test:  If you run this module as a script, it runs automated tests.
  
  To Use:
    import GXD2aryRouter
    import utilsLib
    ...
    ### instantiate the Router class
    router = GXD2aryRouter.GXDrouter(
                skipJournals,   # [journal names] whose articles don't route
                cat1Terms,      # [category 1 terms]
                cat1Exclude,    # [category 1 exclude terms]
                ageExclude,     # [age exclude terms]
                cat2Terms,      # [category 2 terms]
                cat2Exclude,    # [category 2 exclude terms]
                )
    ### to route a reference
    routing =  router.routeThisRef(refID, text, journal)
    if routing == 'Yes':
        # route it to GXD...

        # to get all the utilsLib.MatchRcds that describe why it was routed
        matches = router.getAllMatches()

        # (other subsets of getMatches() are supported too)
    else:
        # don't route it to GXD

        # to get all the utilsLib.MatchRcds that describe why it wasn't routed
        matches = router.getExcludeMatches()
'''
import sys
import re
import unittest
import figureText
import GXD2aryAge
from utilsLib import MatchRcd, TextMapping, TextMappingFromStrings, TextTransformer
#-----------------------------------

class TextMappingFromAgeExcludeTerms (TextMappingFromStrings):
    """
    Is a: TextMapping for matching age exclusion terms
    Does: converts ageExclude vocab terms (a list of strings) to regex's with
            ' ' converted to r'\s' (any whitespace)
            '_' converted to r'\b' (word boundary)
            '#' converted to r'\d' (any digit)
          This gives the curators to a way to make simple regex's from vocab
          terms.
    """

    def _str2regex(self, s):
        """ Return re.escape(s) string with
            '_' replaced w/ word boundaries (r'\b')
            ' ' replaced with r'\s' to match any whitespace
            '#' replaced with r'\d' to match any digit
        """
        regex = re.escape(s)
        regex = regex.replace(' ', 's')   # escape puts '\' before ' ' 
        regex = regex.replace('#', 'd')   # escape puts '\' before '#' 
        regex = regex.replace('_', r'\b') # escape does not put '\' before '_' 
        return regex
#-----------------------------------

class GXDrouter (object):
    """
    Is a: object that knows how to route references for GXD 2ary triage
    Has : vocabularies (lists of strings)
            see __init__() below
    Does: route a reference (return 'Yes' or 'No') given the reference text
            and its journal name.
    jak: need more info here
    """

    def __init__(self,
                skipJournals,   # [journal names] whose articles don't route
                cat1Terms,      # [category 1 terms]
                cat1Exclude,    # [category 1 exclude terms]
                ageExclude,     # [age exclude terms]
                cat2Terms,      # [category 2 terms]
                cat2Exclude,    # [category 2 exclude terms]
                numChars=30,    # n chars on each side of cat1/2 match to report
                ageContext=210, # n chars around age matches to keep & search
                ):
        self.numChars = numChars  # num of chars of surrounding context to keep
        self.skipJournals = {j for j in skipJournals} # set of journal names
        self.cat1Terms    = cat1Terms
        self.cat1Exclude  = cat1Exclude
        self.ageExclude   = ageExclude
        self.ageContext   = ageContext
        self.cat2Terms    = cat2Terms
        self.cat2Exclude  = cat2Exclude

        self.numFigTextWords = 75
        self.figTextConverter = figureText.Text2FigConverter( \
                                            conversionType='legCloseWords',
                                            numWords=self.numFigTextWords)
        self._buildCat1Detection()
        self._buildCat2Detection()
        self._buildMouseAgeDetection()
        return

    def _buildCat1Detection(self):
        # Set up for using text comparisons
        # mapping of lower case exclude terms to what to replace them with
        self.cat1TermsDict   = {x.lower() : x.upper() for x in self.cat1Terms}
        self.cat1ExcludeDict = {x.lower() : x.upper() for x in self.cat1Exclude}
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

        self.ageTextTransformer = GXD2aryAge.AgeTextTransformer( \
                                                    context=self.ageContext)
        self.mouseRE = re.compile(r'\b(?:mouse|mice)\b', re.IGNORECASE)

            # re to detect strings that would block an age exclude term
            # from causing the exclusion if they occur between
            # the exclude term and the matching age text:
            #   paragraph boundary OR '; '
            #   OR:  '. ' NOT preceded by 'fig' or 'et al' (common abbrevs)
            #   Using (?<!R) "negative look behind".
            #         R has to have a fixed width. So I'm matching 4 chars:
            #         \Wfig = any nonalphnumeric + 'fig'
            #         or 't al'
        #blockRegex = r'\n\n|[;]\s|(?<!\Wfig|t al)[.]\s'      # original
        blockRegex = r'\n\n|(?<!\Wfig|t al)[.]\s'             # w/o '; '

        ## organism ageExcludes
        self.ageExcludeOrgList = [  'bovine',
                                    'chick',
                                    'human',
                                    'larvae',
                                    'monkey',
                                    'porcine',
                                    'zebra',
                                    'xenopus',
                                    #'_bat_',   # brown adipose tissue abbrev
                                    #'_cat_',   # gene family
                                    '_pig_',
                                    '_rat_',
                                    '_rats_',
                                    'drosophila',
                                    'worm',
                                    'cynomolgus',
                                    'macaque',
                                    'opossum',
                                    'tadpole',
                                    'turtle',
                                    'hamilton and hamburger',
                                    'hamburger and hamilton',
                                    'hamburger hamilton',
                                    'hamburger-hamilton',
                                    '_hh##_',
                                    '_hh ##_',
                                    '_hh-##_',
                                    'chameleon',
                                    'equine',
                                    'quail',
                                    ]
        self.ageExcludeOrgTextMapping = TextMappingFromAgeExcludeTerms( \
        'excludeAgeOrg', self.ageExcludeOrgList, lambda x: x.upper(), context=0)

        self.ageExcludeOrgTextTransformer = TextTransformer( \
                                            [self.ageExcludeOrgTextMapping])
        self.ageExcludeOrgBlockRE = re.compile(blockRegex)  # . or para

        ## other ageExcludes
        self.ageExcludeTextMapping = TextMappingFromAgeExcludeTerms( \
                'excludeAge', self.ageExclude, lambda x: x.upper(), context=0)

        self.ageExcludeTextTransformer = TextTransformer( \
                                                [self.ageExcludeTextMapping])
        self.ageExcludeBlockRE = re.compile(blockRegex)  # ; or . or para
    # end _buildMouseAgeDetection()

    def _gotMouseAge(self, text):
        """ Return True if we find mouse age terms in text
        """
        newText = self.ageTextTransformer.transformText(text)

        # get ageMatches and throw away "fix" matches
        ageMatches = [ m for m in self.ageTextTransformer.getMatches()
                                        if not m.matchType.startswith('fix')] 
        # check for ageExclude matches
        for m in ageMatches:
            if self._isGoodAgeMatch(m) and self._isGoodAgeOrgMatch(m):
                self.ageMatches.append(m)
            else:
                self.ageExcludes.append(m)

        self.ageTextTransformer.resetMatches()
        return len(self.ageMatches)

    def _isGoodAgeOrgMatch(self, m # MatchRcd
                        ):
        """ Return True if the match looks like its about mouse and not
                some other organism.
            If not a good mouse age, return False and:
                Modify m.matchText, m.preText, or m.postText to highlight the
                    exclude term that indicates it is not a good match,
                Set m.matchType to 'excludeAgeOrg'
        """
        goodAgeMatch = True     # assume no exclusion terms detected

        # If matchText has 'mice|mouse', then it's a good match
        if self.mouseRE.search(m.matchText):
            return True
        
        # if preText has unblocked 'mice|mouse', then it's a good match
        for mouseMatch in self.mouseRE.finditer(m.preText):
            interveneText = m.preText[mouseMatch.end():]
            if not self.ageExcludeOrgBlockRE.search(interveneText):
                return True
        
        # if postText has unblocked 'mice|mouse', then it's a good match
        for mouseMatch in self.mouseRE.finditer(m.postText):
            interveneText = m.postText[:mouseMatch.start()]
            if not self.ageExcludeOrgBlockRE.search(interveneText):
                return True

        # If m.matchText has age organism exclusion term, then exclude
        # Another organism term should rarely be found in the matchText,
        #  but I suppose it is theoretically possible
        newText = self.ageExcludeOrgTextTransformer.transformText(m.matchText)
        excludeMatches = self.ageExcludeOrgTextTransformer.getMatches()

        for em in excludeMatches:       # for exclusion matches in matchText
            newMText = m.matchText[:em.start] + em.replText + \
                                                        m.matchText[em.end:]
            m.matchText = newMText
            goodAgeMatch = False
            break
        self.ageExcludeOrgTextTransformer.resetMatches()

        # If m.preText has unblocked age organism exclusion term, then exclude
        newText = self.ageExcludeOrgTextTransformer.transformText(m.preText)
        excludeMatches = self.ageExcludeOrgTextTransformer.getMatches()

        for em in excludeMatches:       # for exclusion matches in preText
            if not self.ageExcludeOrgBlockRE.search(m.preText[em.end:]):
                # no intervening text found that should block the exclude
                newPText = m.preText[:em.start] + em.replText + \
                                                            m.preText[em.end:]
                m.preText = newPText
                goodAgeMatch = False
                break
        self.ageExcludeOrgTextTransformer.resetMatches()

        # If m.postText has unblocked age organism exclusion term, then exlude
        newText = self.ageExcludeOrgTextTransformer.transformText(m.postText)
        excludeMatches = self.ageExcludeOrgTextTransformer.getMatches()

        for em in excludeMatches:      # for exclusion matches in postText
            if not self.ageExcludeOrgBlockRE.search(m.postText[:em.start]):
                # no intervening text found that should block the exclude
                newPText = m.postText[:em.start] + em.replText + \
                                                            m.postText[em.end:]
                m.postText = newPText
                goodAgeMatch = False
                break
        self.ageExcludeOrgTextTransformer.resetMatches()

        if not goodAgeMatch:
            m.matchType = 'excludeAgeOrg'
        return goodAgeMatch

    def _isGoodAgeMatch(self, m # MatchRcd
                        ):
        """ Return True if this looks like a good mouse age match.
            (i.e., no age exclusion terms found in the match or pre/post text)
            If not a good mouse age, return False and:
                Modify m.matchText, m.preText, or m.postText to highlight the
                    exclude term that indicates it is not a good match,
                Set m.matchType to 'excludeAge'
        """
        goodAgeMatch = True     # assume no exclusion terms detected

        # Search m.matchText for age exclusion terms
        newText = self.ageExcludeTextTransformer.transformText(m.matchText)
        excludeMatches = self.ageExcludeTextTransformer.getMatches()

        for em in excludeMatches:       # for exclusion matches in matchText
            newMText = m.matchText[:em.start] + em.replText + \
                                                        m.matchText[em.end:]
            m.matchText = newMText
            goodAgeMatch = False
            break
        self.ageExcludeTextTransformer.resetMatches()

        # Search m.preText for age exclusion terms
        newText = self.ageExcludeTextTransformer.transformText(m.preText)
        excludeMatches = self.ageExcludeTextTransformer.getMatches()

        for em in excludeMatches:       # for exclusion matches in preText
            if not self.hasAgeExcludeBlock(m.preText[em.end:]):
                # no intervening text found that should block the exclude
                newPText = m.preText[:em.start] + em.replText + \
                                                            m.preText[em.end:]
                m.preText = newPText
                goodAgeMatch = False
                break
        self.ageExcludeTextTransformer.resetMatches()

        # Search m.postText for age exclusion terms
        newText = self.ageExcludeTextTransformer.transformText(m.postText)
        excludeMatches = self.ageExcludeTextTransformer.getMatches()

        for em in excludeMatches:      # for exclusion matches in postText
            if not self.hasAgeExcludeBlock(m.postText[:em.start]):
                # no intervening text found that should block the exclude
                newPText = m.postText[:em.start] + em.replText + \
                                                            m.postText[em.end:]
                m.postText = newPText
                goodAgeMatch = False
                break
        self.ageExcludeTextTransformer.resetMatches()

        if not goodAgeMatch:
            m.matchType = 'excludeAge'
        return goodAgeMatch
    
    def hasAgeExcludeBlock(self, text):
        """ Return True/False if text contains ageExclude blocking text
        """
        if self.ageExcludeBlockRE.search(text):
            return True
        else:
            return False

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
        """ Return text that summarizes this routing algorithm
        """
        output = ''
        output += 'Category1 terms in full text:\n'
        for t in sorted(self.cat1TermsDict.keys()):
            output += "\t'%s'\n" % t

        output += 'Category1 Exclude terms:\n'
        for t in sorted(self.cat1ExcludeDict.keys()):
            output += "\t'%s'\n" % t

        output += 'Number of figure text words: %d\n' % self.numFigTextWords

        output += 'Category2 terms in figure text:\n'
        for t in sorted(self.cat2TermsDict.keys()):
            output += "\t'%s'\n" % t

        output += 'Category2 Exclude terms:\n'
        for t in sorted(self.cat2ExcludeDict.keys()):
            output += "\t'%s'\n" % t

        output += 'Mouse age regular expression - searched in figure text:\n'
        output += self.ageTextTransformer.getBigRegex() + '\n'

        output += 'Num chars around age matches to look for age excludes: %d\n'\
                                                    % self.ageContext
        output += 'Mouse Age Exclude terms:\n'
        for t in sorted(self.ageExclude):
            output += "\t'%s'\n" % t

        output += 'Mouse age exclude regular expression:\n'
        output += self.ageExcludeTextTransformer.getBigRegex() + '\n'

        output += 'Mouse age exclude blocking regular expression:\n'
        output += self.ageExcludeBlockRE.pattern + '\n'
        output += 'Mouse age exclude blocking logic for ". ":\n'
        output += '". " not following "fig" nor "et al"\n'

        output += 'Treating organism terms differently from other ageExcludes\n'
        output += 'Mouse Age Organism Exclude terms:\n'
        for t in sorted(self.ageExcludeOrgList):
            output += "\t'%s'\n" % t

        output += 'Mouse age Organism exclude regular expression:\n'
        output += self.ageExcludeOrgTextTransformer.getBigRegex() + '\n'

        output += 'Mouse age Organism exclude blocking regular expression:\n'
        output += self.ageExcludeOrgBlockRE.pattern + '\n'
        output += 'Mouse age exclude blocking logic for ". ":\n'
        output += '". " not following "fig" nor "et al"\n'

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
        """ Return list of positive matches for most recent article """
        return self.cat1Matches + self.ageMatches + self.cat2Matches

    def getExcludeMatches(self):
        return self.cat1Excludes + self.ageExcludes + self.cat2Excludes

    def getAllMatches(self):
        all = self.cat1Matches + self.cat1Excludes + self.ageMatches + \
                self.ageExcludes + self.cat2Matches + self.cat2Excludes
        return all
# end class GXDrouter -----------------------------------

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
    resultText = text           # resulting text if termDict is empty

    findText = text.replace('\n', ' ')  # So we can match terms across lines
                                        # This is the text to search in.

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
# end findMatches() -----------------------------------

# Automated tests
class FindMatchesTests(unittest.TestCase):
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

class AgeExcludeTests(unittest.TestCase):
    def setUp(self):
        ageExclude = ['_hh##_', 'hamburger hamilton']
        self.gr = GXDrouter([], [], [], ageExclude, [], [], numChars=30)

    # Note the "fig n" text is needed to force the text to be included
    #  as figure text in the routeThisRef() method.
    # Any paragraph w/o fig or figure will be omitted when looking for ages.

    def test_nullTest(self):
        # need '\n\nfig n.' for this to be treated as figure text
        doc = '\n\nfig 1. some text E14.5 more text'    # no age exclusion
        routing = self.gr.routeThisRef('id1', doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'eday')

    def test_regexChars1(self):
        # test _hh##_ matches digits and word boundaries and causes exclusion
        doc = '\n\nfig 1. (hh23) some text E14.5 more text' 
        routing = self.gr.routeThisRef('id1', doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'excludeAge')

        # test _hh##_ matches digits and word boundaries and causes exclusion
        doc = '\n\nfig 1. some text E14.5 more text (hh46)' 
        routing = self.gr.routeThisRef('id1', doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'excludeAge')

        # test _hh##_ matches word boundaries are required for exclusion
        doc = '\n\nfig 1. (hh23not_word_boundary) some text E14.5 more text' 
        routing = self.gr.routeThisRef('id1', doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'eday')

        # test ' ' in exclude term matches whitespace
        doc = '\n\nfig 1. (hamburger\nhamilton) some text E14.5 more text' 
        routing = self.gr.routeThisRef('id1', doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'excludeAge')

    def test_hasAgeExcludeBlock(self):
        # test no blocks
        doc = 'fig 1.1 (hh23)\nfig 2 some text E14.5 more text' 
        self.assertFalse(self.gr.hasAgeExcludeBlock(doc))

        # test '\n\n' blocks
        doc = 'fig 1.1 (hh23)\n\nfig 2 some text E14.5 more text' 
        self.assertTrue(self.gr.hasAgeExcludeBlock(doc))

        # test '; ' blocks
        doc = 'fig 1.1 (hh23); fig 2 some text E14.5 more text' 
        self.assertTrue(self.gr.hasAgeExcludeBlock(doc))

        # test '. ' blocks
        doc = 'fig 1.1 (hh23). fig 2 some text E14.5 more text' 
        self.assertTrue(self.gr.hasAgeExcludeBlock(doc))

        # test ' fig. ' does not block
        doc = 'fig 1.1 (hh23) fig. 2 some text E14.5 more text' 
        self.assertFalse(self.gr.hasAgeExcludeBlock(doc))

        # test ' fig.\n' does not block
        doc = 'fig 1.1 (hh23) fig.\n 2 some text E14.5 more text' 
        self.assertFalse(self.gr.hasAgeExcludeBlock(doc))

        # test '(fig. ' does not block
        doc = 'fig 1.1 (hh23) (fig. 2) some text E14.5 more text' 
        self.assertFalse(self.gr.hasAgeExcludeBlock(doc))

        # test 'config. ' does block
        doc = 'fig 1.1 (hh23) config. 2 some text E14.5 more text' 
        self.assertTrue(self.gr.hasAgeExcludeBlock(doc))

        # test 'et al. ' does not block
        doc = 'fig 1.1 (hh23) et al. some text E14.5 more text' 
        self.assertFalse(self.gr.hasAgeExcludeBlock(doc))

        # test 'et al.\n' does not block
        doc = 'fig 1.1 (hh23) et al.\nsome text E14.5 more text' 
        self.assertFalse(self.gr.hasAgeExcludeBlock(doc))

    def test_excludeBlocking(self):
        # test '\n\n' between exclude term & age text blocks the exclusion
        doc = '\n\nfig 1. (hh23)\n\nfig 2 some text E14.5 more text' 
        routing = self.gr.routeThisRef('id1', doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'eday')

        # test '\n\n' between exclude term & age text blocks the exclusion
        doc = '\n\nfig 1. some text E14.5 more text\n\n fig 2 (hh23)' 
        routing = self.gr.routeThisRef('id1', doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'eday')

        # test '.\n' between exclude term & age text blocks the exclusion
        doc = '\n\nfig 1. (hh23).\n some text E14.5 more text' 
        routing = self.gr.routeThisRef('id1', doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'eday')

        # test '. ' between exclude term & age text blocks the exclusion
        doc = '\n\nfig 1. some text E14.5 more text. new sentence hh46.' 
        routing = self.gr.routeThisRef('id1', doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'eday')

        # test ' fig. ' between exclude term & age text not block the exclusion
        doc = '\n\nfig 1. (hh23) fig. 54, some text E14.5 more text' 
        routing = self.gr.routeThisRef('id1', doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'excludeAge')

        # test '(fig. ' between exclude term & age text not block the exclusion
        doc = '\n\nfig 1. (hh23) (fig. 54), some text E14.5 more text' 
        routing = self.gr.routeThisRef('id1', doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'excludeAge')

        # test 'fig.\n' between exclude term & age text not block the exclusion
        doc = '\n\nfig 1. some text E14.5 more text fig.\n54 hh33' 
        routing = self.gr.routeThisRef('id1', doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'excludeAge')

        # test 'et al.' between exclude term & age text not block the exclusion
        doc = '\n\nfig 1. some text E14.5 more text et al. 54 hh33' 
        routing = self.gr.routeThisRef('id1', doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'excludeAge')

        # test ';' between exclude term & age text blocks the exclusion
        doc = '\n\nfig 1. (hh23); some text E14.5 more text' 
        routing = self.gr.routeThisRef('id1', doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'eday')

        #m = matches[0]
        #print()
        #print("%s: '%s' '%s' '%s'" % (m.matchType, m.preText, m.matchText, m.postText))
#-----------------------------------

if __name__ == "__main__":
    unittest.main()
