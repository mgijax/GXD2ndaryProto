#!/usr/bin/env python3
'''
  Purpose: Define Age mappings for GXD secondary routing

        These mappings are a little different from the age mappings
        defined for the autolittriage relevanceClassifier and gxdhtclassifier
        since they are only matched against figure text and have been tuned by
        lots of trial and error for GXD 2ndary triage.

  Run this module as a script to run automated tests.

  To import and use the age mappings:
      import GXD2aryAge
      ageTransformer = GXD2aryAge.AgeTextTransformer()
      newText   = ageTransformer.transformText("some text")
      matches   = ageTransformer.getMatches() # to get MatchRcds for matches
      reportStr = ageTransformer.getReport()  # to get formatted match report
'''
import sys
import re
import unittest
from utilsLib import TextMapping, TextTransformer, MatchRcd, spacedOutRegex
#-----------------------------------

class AgeTextTransformer (TextTransformer):
    """
    IS a TextTransformer to convert mouse age text to "__mouse_age" with
       specificiable context length - the number of chars to keep around
       each age match.
    """
    def __init__(self, context=210, fixContext=10):
        self.context    = context
        self.fixContext = fixContext
        ageMappings     = getAgeMappings(context=context, fixContext=fixContext)

        super().__init__(ageMappings, reFlags=re.IGNORECASE)

    def getContext(self):    return self.context
    def getFixContext(self): return self.fixContext
#-----------------------------------

def getAgeMappings(context=210, fixContext=10):
    """ Return list of age TextMapping objects with the specified number of
        characters for context to keep for each match.
        fixContext is the num of characters to keep for mappings that just
            fix weird text problems
    """
    return [ \
    # Be careful about the order of these mappings.
    # If two can overlap in their matching text, only the first one is applied.

    # Fix mappings: detect weird usages that would erroneously be mapped
    #  to mouse_age
    # by putting these "fix" mappings, 1st, if they match, none of the later
    # mappings will match (1st match wins), even if these don't change the text
    TextMapping('fix2',       # detect figure|table En (En is fig num)
                              # so En is not treated as eday
        r'\b(?:' +
            r'(?:figures?|fig[.s]?|tables?) e\d' +
        r')', lambda x: x,
        context=fixContext),
    TextMapping('fix1',       # correct 'F I G U R E n' so it doesn't
                              # look like embryonic day "E n". "T A B L E" too
        r'\b(?:' +
            spacedOutRegex('figure') +
            r'|' + spacedOutRegex('table') +
        r')\b', lambda x: ''.join(x.split()), # funct to squeeze out spaces
        context=fixContext),

    # Real age mappings
    TextMapping('dpc',
        # For dpc numbers: allow 0-29 even though most numbers >21 may not be
        #   mice. There tend to not be many matches > 21
        # (0-29 is easy to code as a regexpr: r'(?:\d|[12]\d)' )
        # Allow optional .0 and .5.  regexpr: r'(?:[.][05])?'
        r'\b(?:' +     
            # flavors of "days post conceptus" w/o numbers
            r'd(?:ays?)?(?:\s|-)post(?:\s|-)?' +
                    r'(?:concept(?:ions?|us)?|coit(?:us|um|al)?)' +

            # number 1st, optional space or -, then dpc
            r'|(?:\d|[12]\d)(?:[.][05])?(?:\s|-)?dpc' + 
            r'|(?:\d|[12]\d)(?:[.][05])?(?:\s|-)?d[.]p[.]c' +  # periods

            # dpc 1st, optional space or -, then number
            r'|d[.]?p[.]?c[.]?(?:\s|-)?(?:\d|[12]\d)(?:[.][05])?' +

            # 'd'|'day'|'days' 1st, space or - required), then number, then p.c.
            r'|d(?:ays?)?(?:\s|-)(?:\d|[12]\d)(?:[.][05])?(?:\s|-)?p[.]?c' +
        r')\b', '__mouse_age', context=context),

    TextMapping('eday',
        r'\b(?:' +
            r'embryonic\sdays?' + # spelled out, don't worry about numbers
            r'|[eg]d\s?\d' +       # ED or GD (embryonic|gestational)day+ 1 dig
            r'|[eg]d\s?1[0-9]' +   # ED or GD 2 digits: 10-19
            r'|[eg]d\s?20' +       # ED or GD 2 digits: 20

            r'|day\s\d[.]5' +      # day #.5 - single digit
            r'|day\s1\d[.]5' +     # day #.5 - 2 digits
            
            r'|\d[.]5\sdays?' +    # #.5 day - single digit
            r'|1\d[.]5\sdays?' +   # #.5 day - 2 digits

            r'|\d\sday\s(?:(?:mouse|mice)\s)?embryos?' +  # # day embryo - 1 dig
            r'|1\d\sday\s(?:(?:mouse|mice)\s)?embryos?' + # # day embryo - 2 dig

            # E1 E2 E3 are rarely used & often mean other things
            # E14 is often a cell line, not an age
            # Acceptable 2 decimal places:  .25 and .75 - regex: [.][27]5
            # Acceptable 1 decimal place:   .0 and .5   - regex: [.][05]
            r'|(?<![-])(?:' +     # not preceded by '-'
             r'e\d[.][27]5' +     # En  w/ 2 acceptable decimal places
             r'|e1\d[.][27]5' +   # E1n w/ 2 acceptable decimal places
             r'|e\s?\d[.][05]' +  # En or E n   w/ 1 acceptable dec place
             r'|e\s?1\d[.][05]' + # E1n or E 1n w/ 1 acceptable dec place
             r'|e\s?[4-9]' +      # E single digit
             r'|e\s1\d' +         # E (w/ space) double digits
             r'|e1[0123456789]' +  # E (no space) double digits - omit E14
             r'|e\s?20' +         # E double digits E20
            r')(?![.]\d|[%]|-bp|-ml|-mg)' + # not followed by decimal or
                                            #   % -bp -ml -mg

        r')\b', '__mouse_age', context=context),

    TextMapping('ts',
        r'\b(?:' +
            r'theiler\sstages?' +
            r'|TS(?:\s|-)?[7-9]' +  # 1 digit, 0-6 not used or are other things
            r'|TS(?:\s|-)?[12]\d' +   # 2 digits
        r')\b', '__mouse_age', context=context),
    TextMapping('ee',   # early embryo terms
                        # mesenchymal mesenchymes? ?
        r'\b(?:' +
            r'blastocysts?|blastomeres?|headfold|autopods?' +
            r'|embryonic\slysates?|embryo\slysates?' +
            r'|(?:(?:early|mid|late)(?:\s|-))?streak|morulae?|somites?' +
            r'|(?:limb(?:\s|-)?)buds?' +    # bud w/ limb in front
            r'|(?<!fin(?:\s|-))buds?' +     # bud w/o 'fin ' in front
            r'|(?:' +
                r'(?:[1248]|one|two|four|eight)(?:\s|-)cells?(?:\s|-)' +
                r'(?:' +   # "embryo" or "stage" must come after [1248] cell
                    r'stages?|' +
                    r'(?:' +
                        r'(?:(?:mouse|mice|cloned)(?:\s|-))?embryos?' +
                    r')' +
                r')' +
            r')' +
        r')\b', '__mouse_age', context=context),
    TextMapping('developmental',   # "developmental" terms
        r'\b(?:' +  # Do we want to add simply "embryos?"
            r'zygotes?' +
            r'|(?:mice|mouse)(?:\s|-)embryos?' +        # more general
            #r'|development(?:\s|-)of(?:\s|-)(?:(?:mice|mouse)(?:\s|-))?embryos?'+
            #r'|developing(?:\s|-)(?:(?:mice|mouse)(?:\s|-))?embryos?' +
            r'|development(?:al)?(?:\s|-)(?:(?:mice|mouse)(?:\s|-))?stages?' +
            r'|development(?:al)?(?:\s|-)(?:(?:mice|mouse)(?:\s|-))?ages?' +
            r'|embryo(?:nic)?(?:\s|-)(?:(?:mice|mouse)(?:\s|-))?stages?' +
            r'|embryo(?:nic)?(?:\s|-)(?:(?:mice|mouse)(?:\s|-))?ages?' +
            r'|embryo(?:nic)?(?:\s|-)development' +
            r'|(?:st)?ages?(?:\s|-)of(?:\s|-)?embryos?' +
            r'|development(?:al)?(?:\s|-)time(?:\s|-)courses?' +
        r')\b', '__mouse_age', context=context),
    TextMapping('fetus',   # fetus terms
        r'\b(?:' +
            r'fetus|fetuses' +
            r'|(?:fetal|foetal)(?!\s+(?:bovine|calf)\s+serum)' +
        r')\b', '__mouse_age', context=context),
    ]
# end getAgeMappings() -----------------------------------
    

#-----------------------------------

def doAutomatedTests():

    #sys.stdout.write("No automated tests at this time\n")
    #return
    sys.stdout.write("Running automated unit tests...\n")
    unittest.main(argv=[sys.argv[0], '-v'],)

class MyTests(unittest.TestCase):
    def setUp(self):
        self.tt = AgeTextTransformer()

    def test_AgeMappings0(self):
        text = "there are no mappings here"
        self.assertEqual(text, self.tt.transformText(text))

    def test_AgeMappings1_eday(self):
        tt = self.tt
        text = "s E0 E 1. E 2 E3, E0.5 E4-5 E9.75 e"      # single digit
        expt = "s E0 E 1. E 2 E3, __mouse_age __mouse_age-5 __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s E14 E14.5. E 14 E 14.5 E15-18 e"      # double digits
        expt = "s __mouse_age __mouse_age. __mouse_age __mouse_age __mouse_age-18 e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s E13 E19 E 16 E 17.5 E20 e"            # double digits
        expt = "s __mouse_age __mouse_age __mouse_age __mouse_age __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s E21 embryonic days 15-18 embryonic day 14-15 e"
        expt = "s E21 __mouse_age 15-18 __mouse_age 14-15 e"
        self.assertEqual(tt.transformText(text), expt)
        #print('\n' + tt.getReport())

    def test_AgeMappings2_dpc(self):
        tt = self.tt
        text = "s d-postcoit. 12-days-post-coitum 14 day postconceptus e"
        expt = "s __mouse_age. 12-__mouse_age 14 __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s 12 days post\nconception e"   # across line boundaries
        expt = "s 12 __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)

                    # dpc after numbers no space or ' ' or '-' before 'dpc'
        text = "s 2.5dpc 5 dpc 2-dpc e"
        expt = "s __mouse_age __mouse_age __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)

                    # dpc after numbers no space or ' ' or '-' before 'd.p.c'
        text = "s 2.5d.p.c. 5 d.p.c. 2.5-d.p.c. e"
        expt = "s __mouse_age. __mouse_age. __mouse_age. e"
        self.assertEqual(tt.transformText(text), expt)

                    # 'dpc' before numbers,
        text = "s dpc 5.5 dpc7.5, d.p.c.21.0, dpc-7.5 e"
        expt = "s __mouse_age __mouse_age, __mouse_age, __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)

                    # 'day'  before numbers, needs ' ' or -
        text = "s day-7-p.c. days 7.5pc, d 21.0 pc, day 10.0-p.c. e"
        expt = "s __mouse_age. __mouse_age, __mouse_age, __mouse_age. e"
        self.assertEqual(tt.transformText(text), expt)

                    # don't match numbers out of range, >29
        text = "s dpc70.5, 30-dpc, day-30.0-pc dpc 71 e"
        expt = "s dpc70.5, 30-dpc, day-30.0-pc dpc 71 e"
        self.assertEqual(tt.transformText(text), expt)
        #print('\n' + tt.getReport())

    def test_AgeMappings3_ts(self):
        tt = self.tt
        text = "s Theiler stages 4-5 just 1 TS23 ts 23 ts-7 e"
        expt = "s __mouse_age 4-5 just 1 __mouse_age __mouse_age __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)
        #print('\n' + tt.getReport())

    def test_AgeMappings4_ee(self):
        tt = self.tt
        text = "there are no mappings here, 1-cell, 2 cell, four cell"
        self.assertEqual(text, tt.transformText(text))
        text = "s Blastocysts fetus blastomeres early-streak e"
        expt = "s __mouse_age __mouse_age __mouse_age __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s 1-cell embryo one cell mice embryos 8 cell stage e"
        expt = "s __mouse_age __mouse_age __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s 1-cell-embryo one-cell-mice-embryos 8-cells-stage e"
        expt = "s __mouse_age __mouse_age __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)
        #print('\n' + tt.getReport())

    def test_AgeMappings4_developmental(self):
        tt = self.tt
        text = "s developmental ages, development-stage, embryonic mouse ages e"
        expt = "s __mouse_age, __mouse_age, __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s developmenting-mouse-embryos e"
        expt = "s developmenting-__mouse_age e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s development of mice-embryos e"
        expt = "s development of __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s stages of embryos, age of embryos e"
        expt = "s __mouse_age, __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s zygote and development-time-courses e"
        expt = "s __mouse_age and __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)

#-----------------------------------

if __name__ == "__main__":
    unittest.main()
