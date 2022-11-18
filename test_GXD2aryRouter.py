#!/usr/bin/env python3

"""
These are tests for GXD2aryRouter.py
Usage:   python test_GXD2aryRouter.py [-v]
"""
import unittest
from GXD2aryRouter import *

class FindMatchesTests(unittest.TestCase):
    # Test the findMatches() function
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

class ShortTextTests(unittest.TestCase):
    # Test that refs with short text get routed
    def setUp(self):
        ageExclude = ['_hh##_']
        self.gr = GXDrouter([], [], [], ageExclude, [], [], minTextLen=10)

    def test_shortText(self):
        doc = 'long enough, but no matches'
        routing = self.gr.routeThisRef(doc, 'journal')
        self.assertEqual(routing, 'No')

        doc = 'too short'
        routing = self.gr.routeThisRef(doc, 'journal')
        self.assertEqual(routing, 'Yes')

#-----------------------------------

class AgeExcludeTests(unittest.TestCase):
    # Test the age exclude logic
    def setUp(self):
        ageExclude = ['_hh##_', 'hamburger hamilton']
        self.gr = GXDrouter([], [], [], ageExclude, [], [], numChars=30)

    # Note the "fig n" text is needed to force the text to be included
    #  as figure text in the routeThisRef() method.
    # Any paragraph w/o fig or figure will be omitted when looking for ages.

    def test_AgeExcludeNullTest(self):
        # need '\n\nfig n.' for this to be treated as figure text
        doc = '\n\nfig 1. some text E14.5 more text'    # no age exclusion
        routing = self.gr.routeThisRef(doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'eday')

    def test_regexChars1(self):
        # test _hh##_ matches digits and word boundaries and causes exclusion
        doc = '\n\nfig 1. (hh23) some text E14.5 more text' 
        routing = self.gr.routeThisRef(doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'excludeAge')

        # test _hh##_ matches digits and word boundaries and causes exclusion
        doc = '\n\nfig 1. some text E14.5 more text (hh46)' 
        routing = self.gr.routeThisRef(doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'excludeAge')

        # test _hh##_ matches word boundaries are required for exclusion
        doc = '\n\nfig 1. (hh23not_word_boundary) some text E14.5 more text' 
        routing = self.gr.routeThisRef(doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'eday')

        # test ' ' in exclude term matches whitespace
        doc = '\n\nfig 1. (hamburger\nhamilton) some text E14.5 more text' 
        routing = self.gr.routeThisRef(doc, 'journal')
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
        routing = self.gr.routeThisRef(doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'eday')

        # test '\n\n' between exclude term & age text blocks the exclusion
        doc = '\n\nfig 1. some text E14.5 more text\n\n fig 2 (hh23)' 
        routing = self.gr.routeThisRef(doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'eday')

        # test '.\n' between exclude term & age text blocks the exclusion
        doc = '\n\nfig 1. (hh23).\n some text E14.5 more text' 
        routing = self.gr.routeThisRef(doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'eday')

        # test '. ' between exclude term & age text blocks the exclusion
        doc = '\n\nfig 1. some text E14.5 more text. new sentence hh46.' 
        routing = self.gr.routeThisRef(doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'eday')

        # test ' fig. ' between exclude term & age text not block the exclusion
        doc = '\n\nfig 1. (hh23) fig. 54, some text E14.5 more text' 
        routing = self.gr.routeThisRef(doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'excludeAge')

        # test '(fig. ' between exclude term & age text not block the exclusion
        doc = '\n\nfig 1. (hh23) (fig. 54), some text E14.5 more text' 
        routing = self.gr.routeThisRef(doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'excludeAge')

        # test 'fig.\n' between exclude term & age text not block the exclusion
        doc = '\n\nfig 1. some text E14.5 more text fig.\n54 hh33' 
        routing = self.gr.routeThisRef(doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'excludeAge')

        # test 'et al.' between exclude term & age text not block the exclusion
        doc = '\n\nfig 1. some text E14.5 more text et al. 54 hh33' 
        routing = self.gr.routeThisRef(doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'excludeAge')

        # test ';' between exclude term & age text blocks the exclusion
        doc = '\n\nfig 1. (hh23); some text E14.5 more text' 
        routing = self.gr.routeThisRef(doc, 'journal')
        matches = self.gr.getAllMatches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].matchType, 'eday')

        #m = matches[0]
        #print()
        #print("%s: '%s' '%s' '%s'" % (m.matchType, m.preText, m.matchText, m.postText))
#-----------------------------------

class AgeMappingTests(unittest.TestCase):
    # Test the age mappings
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
        expt = "s E21 __mouse_age-__mouse_age 14 e"
        self.assertEqual(tt.transformText(text), expt)

        # e exclusions
        text = "s -E18 E1.2.3 9.0E-7 foo-E14 E 14% E 17-ml E3-bp E3 mg E3\nmg e"
        self.assertEqual(tt.transformText(text), text)

        # e exclusions boundary cases: 'e# mgsomething' doesn't exclude age
        #   need word boundary after mg, ml, bp, etc.
        text = "s e 17-mgi, e17 mgi, e17 mg, e"
        expt = "s __mouse_age-mgi, __mouse_age mgi, e17 mg, e"
        self.assertEqual(tt.transformText(text), expt)

        # 0 w/ no decimals is not an age
        text = "s E0, gd0, 0 day old embryo, e 0, gestional day 0, e"
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
        text = "s 10.5 d old embryos. 0.75-day-old-mouse-embryo, e"
        expt = "s __mouse_age. __mouse_age, e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s 10.5 d old embryos. 0.75-day-old-mouse blastocysts, e"
        expt = "s __mouse_age. __mouse_age, e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s 10.25 d mice embryos. 7 day mouse embryo, e"
        expt = "s __mouse_age. __mouse_age, e"
        self.assertEqual(tt.transformText(text), expt)

                    # mice|mouse requires a dev_term after it to be an age
        text = "s 5.25 d old mice. 3 day mouse, 4.0 day gestation, e"
        expt = "s 5.25 d old mice. 3 day mouse, __mouse_age, e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s 5.25 days after fertilization, e"
        expt = "s __mouse_age, e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s 5.25 days post gestation, e"
        expt = "s __mouse_age, e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s 5.25 ed, 7-GD, 8GD, 9.5 gestational day. e"
        expt = "s __mouse_age, __mouse_age, __mouse_age, __mouse_age. e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s 9.5 embryonic day. 10 embryo day, e"
        expt = "s __mouse_age. 10 embryo day, e"
        self.assertEqual(tt.transformText(text), expt)

        # odd special case for 17.E mouse
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

    def test_AgeMappings5_developmental(self):
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

    def test_AgeMappings6_misc(self):
        tt = self.tt
        text = "s genepaint, allen brain atlas, allen-atlas, time series e"
        expt = "s __mouse_age, allen brain atlas, allen-atlas, time series e"
        self.assertEqual(tt.transformText(text), expt)

        text = "s embryo mouse-brain e"
        expt = "s __mouse_age e"
        self.assertEqual(tt.transformText(text), expt)
#-----------------------------------

if __name__ == '__main__':
    unittest.main()
