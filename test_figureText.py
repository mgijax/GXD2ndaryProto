#!/usr/bin/env python3

"""
These are tests for figureText.py
Usage:   python test_figureText.py [-v]
"""
import unittest
from figureText import *

class figureText_basic_tests(unittest.TestCase):

    def test_getFigureBlurbs(self):
        # test string with increasing number of intervening words between 'fig'
        testDoc = """
        initial first words table fig
        blah1 fig
        blah2 blah3 fig
        blah4 blah5 blah6 fig
        blah7 blah8 blah9 blah10 fig
        blah11 blah12 blah13 blah14 blah15 fig
        blah16 blah17 blah18 blah19 blah20 blah21 fig
        blah22 blah23 blah24 blah25 blah26 blah27 blah28 fig
        final words
        """
        ## surrounding 2 words
        blurbs = getFigureBlurbs(testDoc, numWords=2)
        exp = 'first words table fig blah1 fig blah2 blah3 fig blah4 blah5 blah6 fig blah7 blah8'       # gather overlapping words up to blah8
        self.assertEqual(blurbs[0], exp)

        exp = 'blah9 blah10 fig blah11 blah12'
        self.assertEqual(blurbs[1], exp)

        exp = 'blah14 blah15 fig blah16 blah17'
        self.assertEqual(blurbs[2], exp)

        exp = 'blah20 blah21 fig blah22 blah23'
        self.assertEqual(blurbs[3], exp)

        exp = 'blah27 blah28 fig final words'
        self.assertEqual(blurbs[4], exp)

        ## surrounding 3 words
        blurbs = getFigureBlurbs(testDoc, numWords=3)
        exp = 'initial first words table fig blah1 fig blah2 blah3 fig blah4 blah5 blah6 fig blah7 blah8 blah9 blah10 fig blah11 blah12 blah13 blah14 blah15 fig blah16 blah17 blah18'
        self.assertEqual(blurbs[0], exp)

        exp = 'blah19 blah20 blah21 fig blah22 blah23 blah24'
        self.assertEqual(blurbs[1], exp)

        exp = 'blah26 blah27 blah28 fig final words'
        self.assertEqual(blurbs[2], exp)


    def test_paragraphIterator(self):
        text = 'abc\n\ndef ghi\n\nthe end'      # 3 paragraphs
        paragraphs = list(paragraphIterator(text))
        self.assertEqual(paragraphs[0], 'abc')
        self.assertEqual(paragraphs[1], 'def ghi')
        self.assertEqual(paragraphs[2], 'the end')

        text = ''                         # empty string
        paragraphs = list(paragraphIterator(text))
        self.assertEqual(paragraphs[0], '')

        text = 'abc def'                  # 1 para, no para boundaries
        paragraphs = list(paragraphIterator(text))
        self.assertEqual(paragraphs[0], 'abc def')

        text = '\n\nabc def\n\n'          # 3 para, boundaries
        paragraphs = list(paragraphIterator(text))
        self.assertEqual(paragraphs[0], '')
        self.assertEqual(paragraphs[1], 'abc def')
        self.assertEqual(paragraphs[2], '')

    def test_validation(self):
        with self.assertRaises(AttributeError):
            t2f = Text2FigConverter(conversionType='foo')

    def test_legends(self):
        t2f = Text2FigConverter(conversionType='legends')

        text = "Figures are good."      # Plural, not a legend
        exp = []
        self.assertEqual(exp, t2f.text2FigText(text))

        text = "start of text. Fig 1 is interesting,\n\nI mean it. Really."
        exp = []
        self.assertEqual(exp, t2f.text2FigText(text))

        text = "start of text.\n\nFig 1 is\ninteresting,\n\nI mean it. Really."
        exp = ['Fig 1 is\ninteresting,']
        self.assertEqual(exp, t2f.text2FigText(text))

        text = "start of text.\n\nF I G 1 is interesting,\n\nI mean it. Really."
        exp = ['F I G 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))

        text = "start\n\nF I Gu RE 1 is interesting,\n\nI mean it. Really."
        exp = ['F I Gu RE 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))
    
        text = "start\n\nO n l i n e f i gure 1 is interesting,\n\nReally."
        exp = ['O n l i n e f i gure 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))
    
        text = "start\n\nO n l i n e table 1 is interesting,\n\nReally."
        exp = ['O n l i n e table 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))
    
        text = "start\n\nExtended D a t a  fig 1 is interesting,\n\nReally."
        exp = ['Extended D a t a  fig 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))
    
        text = "start\n\nSupplemental figure 1 is interesting,\n\nReally."
        exp = ['Supplemental figure 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))
    
        text = "start\n\nS u p p  t a b le 1 is interesting,\n\nReally."
        exp = ['S u p p  t a b le 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))
    
    def test_legendsAndWords(self):
        t2f = Text2FigConverter(conversionType='legCloseWords',numWords=2)

        text = "Figures are good. Really."
        exp = [' Figures are good.']
        self.assertEqual(exp, t2f.text2FigText(text))

        text = "start of text. Fig 1 is interesting,\n\nI mean it. Really."
        exp = ['of text. Fig 1 is']
        self.assertEqual(exp, t2f.text2FigText(text))

        text = "That Table 1 is cool.\n\nTable 1 caption.\n\nI mean it. Really."
        exp = ['That Table 1 is', 'Table 1 caption.']
        self.assertEqual(exp, t2f.text2FigText(text))

        text = "start of text.\n\nFig 1 is\ninteresting,\n\nI mean it. Really."
        exp = ['Fig 1 is\ninteresting,']
        self.assertEqual(exp, t2f.text2FigText(text))

        text = "start of text.\n\nF I G 1 is interesting,\n\nI mean it. Really."
        exp = ['F I G 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))

        text = "start\n\nF I Gu RE 1 is interesting,\n\nI mean it. Really."
        exp = ['F I Gu RE 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))
    
        text = "start\n\nO n l i n e f i gure 1 is interesting,\n\nReally."
        exp = ['O n l i n e f i gure 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))
    
        text = "start\n\nO n l i n e table 1 is interesting,\n\nReally."
        exp = ['O n l i n e table 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))
    
        text = "start\n\nExtended D a t a  fig 1 is interesting,\n\nReally."
        exp = ['Extended D a t a  fig 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))
    
        text = "start\n\nSupplemental figure 1 is interesting,\n\nReally."
        exp = ['Supplemental figure 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))
    
        text = "start\n\nS u p p  t a b le 1 is interesting,\n\nReally."
        exp = ['S u p p  t a b le 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))
    

    def test_legendsAndParagraphs(self):
        t2f = Text2FigConverter(conversionType='legParagraphs')

        text = "Figures are good. Really."       # Plural can start paragraph
        exp = ['Figures are good. Really.']
        self.assertEqual(exp, t2f.text2FigText(text))

        text = "start of text. Fig 1 is interesting,\n\nI mean it. Really."
        exp = ['start of text. Fig 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))

        text = "That Table 1 is cool.\n\nTable 1 caption.\n\nI mean it. Really."
        exp = ['That Table 1 is cool.', 'Table 1 caption.']
        self.assertEqual(exp, t2f.text2FigText(text))

        text = "start of text.\n\nFig 1 is\ninteresting,\n\nI mean it. Really."
        exp = ['Fig 1 is\ninteresting,']
        self.assertEqual(exp, t2f.text2FigText(text))

        text = "start of text.\n\nF I G 1 is interesting,\n\nI mean it. Really."
        exp = ['F I G 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))

        text = "start\n\nF I Gu RE 1 is interesting,\n\nI mean it. Really."
        exp = ['F I Gu RE 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))
    
        text = "start\n\nO n l i n e f i gure 1 is interesting,\n\nReally."
        exp = ['O n l i n e f i gure 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))
    
        text = "start\n\nO n l i n e table 1 is interesting,\n\nReally."
        exp = ['O n l i n e table 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))
    
        text = "start\n\nExtended D a t a  fig 1 is interesting,\n\nReally."
        exp = ['Extended D a t a  fig 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))
    
        text = "start\n\nSupplemental figure 1 is interesting,\n\nReally."
        exp = ['Supplemental figure 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))
    
        text = "start\n\nS u p p  t a b le 1 is interesting,\n\nReally."
        exp = ['S u p p  t a b le 1 is interesting,']
        self.assertEqual(exp, t2f.text2FigText(text))

    def test_boundaryConditions(self):
        simpleTestDoc = "no paragraph start but figure text\n\n"
        exp = ["start but figure text"]
        blurbs = text2FigText_LegendAndWords(simpleTestDoc, numWords=2)
        self.assertEqual(exp, blurbs)

        simpleTestDoc = "\n\nno paragraph end figure"
        exp = ["paragraph end figure"]
        blurbs = text2FigText_LegendAndWords(simpleTestDoc, numWords=2)
        self.assertEqual(exp, blurbs)

        simpleTestDoc = "no paragraph start or end figure"
        exp = ["or end figure"]
        blurbs = text2FigText_LegendAndWords(simpleTestDoc, numWords=2)
        self.assertEqual(exp, blurbs)

        simpleTestDoc = ""
        exp = []
        blurbs = text2FigText_LegendAndWords(simpleTestDoc, numWords=2)
        self.assertEqual(exp, blurbs)

        # one char paragraphs
        simpleTestDoc = "s\n\n figure 1 blah\n\nD\n\n a fig sentence\n\nE"
        exp = ["figure 1 blah", "a fig sentence"]
        blurbs = text2FigText_LegendAndWords(simpleTestDoc, numWords=2)
        self.assertEqual(exp, blurbs)
        
        # only a paragraph boundary
        simpleTestDoc = "\n\n"
        exp = []
        blurbs = text2FigText_LegendAndWords(simpleTestDoc, numWords=2)
        self.assertEqual(exp, blurbs)

if __name__ == '__main__':
    unittest.main()
