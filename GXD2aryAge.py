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

            # 'd'|'day'|'days' 1st, space or - required, then number, then p.c.
            r'|d(?:ays?)?(?:\s|-)(?:\d|[12]\d)(?:[.][05])?(?:\s|-)?p[.]?c' +
        r')\b', '__mouse_age', context=context),

    TextMapping('eday',
        r'\b(?:' +
            # Acceptable numbers:
            #   any 1 or 2 digs 0-19 w/ .0 .5 .25 .75
            #   any 1 or 2 digs 0-20 w/o decimals.

            # ED|GD, optional space or -, acceptable number
            # ED short for embryonic day, GD short for gestational day
            r'(?:[eg]d(?:\s|-)?' +
               r'(?:(?:1\d|\d)[.][27]5' + # 1-2 digs w/ 2 decimal
                 r'|(?:1\d|\d)[.][05]' +  # 1-2 digs w/ 1 decimal
                 r'|(?:1\d|20|\d)' +      # 1-2 digs, no decimals
                 r')(?![.]\d))' +         # not followed by decimal

            # D|day(s), optional space or -, acceptable number, term
            r'|(?:(?:[eg]?d|days?)(?:\s|-)?' +
               r'(?:(?:1\d|\d)[.][27]5' + # 1-2 digs w/ 2 decimal
                 r'|(?:1\d|\d)[.][05]' +  # 1-2 digs w/ 1 decimal
                 r'|(?:1\d|20|\d))' +     # 1-2 digs, no decimals
                 r'(?:\s|-)' +          # ... space or -
                 r'(?:' +               # ... some term
                   r'(?:[a-z]+(?:\s|-))?embryos?' + # (opt word) embryo
                   r'|of(?:\s|-)gestation))' +

            # E, optional space or -, acceptable number
            #     (E1-3 are rarely used & often mean other things)
            #     (we allow E14 here since typically in figure text, it will
            #      be an age, not a cell line. In gxdhtclassifier, we omit E14)
            r'|(?:(?<![-])(?:' +     # not preceded by '-'
                                  # (if preceded by '-', often "-En" is part of
                                  #  a symbol or cell line. If En-En is truly
                                  #  an age range, the 1st age will match)
               r'e(?:\s|-)?(?:1\d|\d)[.][27]5' +  # 1-2 digs w/ 2 decimal
               r'|e(?:\s|-)?(?:1\d|\d)[.][05]' +  # 1-2 digs w/ 1 decimal
               r'|e(?:\s|-)?(?:1\d|20|[4-9])' +   # 1-2 digs, no decimals
               r')(?![.]\d|[%]|-bp|-ml|-mg))' + # not followed by decimal or
                                               #   % -bp -ml -mg
            # Embryonic/gestational term, space or -, acceptable number
            r'|(?:' +
               r'(?:(?:gestation(?:al)?|embryo(?:nic)?)(?:\s|-)days?' +
                 r'|embryonic)' +
               r'(?:\s|-)?' +  # optional space or -
               # number
               r'(?:1\d[.][27]5|\d[.][27]5' + # 1-2 digs w/ 2 decimals
               r'|1\d[.][05]|\d[.][05]' +     # 1-2 digs w/ 1 decimal
               r'|20|1\d|\d))' +               # 1-2 digs, no decimals

            # probably can delete this since we match "mice|mouse embryo" alone
            # mouse embryo (day number). e.g: "mouse-embryo-(day3.5)"
            #r'|(?:(?:mice|mouse)(?:\s|-)embryos?(?:\s|-)' +
            #   # day acceptable number in parens
            #   r'[(]day(?:\s|-)?' +
            #   r'(?:1\d[.][27]5|\d[.][27]5' + # 1-2 digs w/ 2 decimals
            #   r'|1\d[.][05]|\d[.][05]' +     # 1-2 digs w/ 1 decimal
            #   r'|20|1\d|\d)' +               # 1-2 digs, no decimals
            #   r'[)])' +

            # Number 1st, optional space or -, then some "day/embryo" term
            r'|(?:(?:1\d[.][27]5|\d[.][27]5' +    # 1-2 digs w/ 2 decimals
                r'|1\d[.][05]|\d[.][05]' +     # 1-2 digs w/ 1 decimal
                r'|20|1\d|\d)' +               # 1-2 digs, no decimals
               # num followed by...
               r'(?:\s|-)?' +          # optional space or -
               r'(?:' +
                 r'(?:' +         # d|day, optional "old" ...some term...
                   r'(?:d|days?)(?:\s|-)(?:old(?:\s|-))?' + # d|day, opt'l old
                   r'(?:embryos?|mice|mouse|gestation))' +
                 r'|(?:' +        # days after fertilization
                   r'days?(?:\s|-)after(?:\s|-)fertilization)' +
                 r'|(?:' +        # ed|gd|gestational day
                   r'(?:ed|gd|gestational(?:\s|-)days?))))' +

            # (odd cases) Number w/ required decimals, followed by ...
            r'|(?:(?:1\d[.][27]5|\d[.][27]5' +    # 1-2 digs w/ 2 decimals
                r'|1\d[.][05]|\d[.][05])' +    # 1-2 digs w/ 1 decimal
               # num followed by...
               r'(?:\s|-)?' +          # optional space or -
               r'(?:' +
                 r'days?(?:\s|-)old' +  # day old
                 r'|embryos?))' +

            # Odd special case to match "17.E mouse"
            r'|(?:(?:20|1\d|\d)[.]e(?:\s|-)mouse)' +  # 1-2 digs w/o decimals

            # final catch all
            r'|embryonic(?:\s|-)days?' + # spelled out, don't worry about nums
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
            r'|development(?:al)?(?:\s|-)time(?:\s|-)(?:series|courses?)' +
        r')\b', '__mouse_age', context=context),
    TextMapping('fetus',   # fetus terms
        r'\b(?:' +
            r'fetus|fetuses' +
            r'|(?:fetal|foetal)(?!\s+(?:bovine|calf)\s+serum)' +
        r')\b', '__mouse_age', context=context),
    TextMapping('misc',   # misc terms
        r'\b(?:' +
            r'genepaint' +
            r'|embryo(?:\s|-)mouse(?:\s|-)brain' +
        r')\b', '__mouse_age', context=context),
    ]
# end getAgeMappings() -----------------------------------
    
#-----------------------------------

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

        text = "s E14 E14.5. E-14 E 14.5 E15 e"      # double digits
        expt = "s __mouse_age __mouse_age. __mouse_age __mouse_age __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s E13 E19 E 16 E-17.5 E20 e"            # double digits
        expt = "s __mouse_age __mouse_age __mouse_age __mouse_age __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s E21 embryonic days 15-18 embryonic day 14 e"  # embryonic day
        expt = "s E21 __mouse_age-18 __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)

        # e exclusions
        text = "s -E18 E1.2.3 9.0E-7 foo-E14 E 14% E 17-ml E3-bp e"
        self.assertEqual(tt.transformText(text), text)

        text = "s E20.5, E1.0, E-11.25, E 12.5, E2.75. e"  # approved decimals
        expt = "s E20.5, __mouse_age, __mouse_age, __mouse_age, __mouse_age. e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s ED20.5, GD-1, ED-2.25, GD 12.5, ED2.75. e"  # ED and GD
        expt = "s ED20.5, __mouse_age, __mouse_age, __mouse_age, __mouse_age. e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s ED20.5, GD-1, ED-2.25, GD 12.5, ED2.75. e"  # ED and GD
        expt = "s ED20.5, __mouse_age, __mouse_age, __mouse_age, __mouse_age. e"
        self.assertEqual(tt.transformText(text), expt)

        # D, number, term
        text = "s D20.5 embryo , D 1.0 old embryos, D-11.25-embryo, e"
        expt = "s D20.5 embryo , __mouse_age, __mouse_age, e"
        self.assertEqual(tt.transformText(text), expt)

        # day, number, term
        text = "s day 19.5, day-1 of gestation, day2.25 embryo. e"
        expt = "s day 19.5, __mouse_age, __mouse_age. e"
        self.assertEqual(tt.transformText(text), expt)

        # gestational/embryonic days
        text = "s gestational days 10.5-11.5, embryo day-7. embryonic5 e"
        expt = "s __mouse_age-11.5, __mouse_age. __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)

        # Number followed by various terms
        text = "s 10.5 d old embryos. 0.75-day-old-mouse embryo, e"
        expt = "s __mouse_age. __mouse_age embryo, e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s 10.25 d mice embryos. 7 day mouse embryo, e"
        expt = "s __mouse_age embryos. __mouse_age embryo, e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s 5.25 d old mice. 3 day mouse, 4.0 day gestation, e"
        expt = "s __mouse_age. __mouse_age, __mouse_age, e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s 5.25 days after fertilization, e"
        expt = "s __mouse_age, e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s 5.25 ed, 7-GD, 8GD, 9.5 gestational day. e"
        expt = "s __mouse_age, __mouse_age, __mouse_age, __mouse_age. e"
        self.assertEqual(tt.transformText(text), expt)

        # Numbers that require an approved decimal, followed by various
        text = "s 5.5 day old, 7.5-embryo, e"
        expt = "s __mouse_age, __mouse_age, e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s 17.E-mouse, 5.E mouse. e"
        expt = "s __mouse_age, __mouse_age. e"
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

        text = "s 5 mice embryos, 7.5-mouse embryo, e"
        expt = "s 5 __mouse_age, 7.5-__mouse_age, e"
        self.assertEqual(tt.transformText(text), expt)

        # mice embryo (day number) - mice|mouse embryo matches w/o the number
        text = "s mouse embryo (day-6), mice-embryos-(day7.5), e"
        expt = "s __mouse_age (day-6), __mouse_age-(day7.5), e"
        self.assertEqual(tt.transformText(text), expt)

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

    def test_AgeMappings4_misc(self):
        tt = self.tt
        text = "s genepaint, allen brain atlas, allen-atlas, time series e"
        expt = "s __mouse_age, allen brain atlas, allen-atlas, time series e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s embryo mouse-brain e"
        expt = "s __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)

#-----------------------------------

if __name__ == "__main__":
    unittest.main()
