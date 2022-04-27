#!/usr/bin/env python3
#
# Library to support handling of reference records
# for experimenting with GXD secondary triage rules.
import re
from baseSampleDataLib import *
import figureText
#import utilsLib
from utilsLib import TextMapping, TextTransformer
#-----------------------------------

FIELDSEP     = '|'      # field separator when reading/writing sample fields
RECORDEND    = ';;'     # record ending str when reading/writing sample files

figConverterLegCloseWords50 = figureText.Text2FigConverter( \
                                            conversionType='legCloseWords',
                                            numWords=50)
#-----------------------------------
AgeMappings = [
    TextMapping('eday',
        # Original: was too broad
        # r'\b(?:(?:e\s?|(?:e(?:mbryonic)?\sdays?\s))\d\d?(?:[.]\d\d?)?)\b',
        # E1 E2 E3 are rarely used & often mean other things
        # E14 is often a cell line, not an age
        r'\b(?:' +
            r'e\s?\d[.]\d\d?' +    # E single digit w/ decimal place or two
            r'|e\s?1\d[.]\d\d?' +  # E double digit w/ decimal place or two
            r'|e\s?[4-9]' +        # E single digit
            r'|e\s1\d' +           # E (w/ space) double digits
            r'|e1[012356789]' +    # E (no space) double digits - omit E14
            r'|e\s?20' +           # E double digits
            r'|embryonic\sdays?\s\d\d?(?:[.]\d\d?)?' + # spelled out, opt decim
        r')\b', '__mouse_age', context=0),
    TextMapping('dpc',
        r'\b(?:' +
            r'days?\spost\s(?:conception|conceptus|coitum)' +
            r'|\d\d?dpc' +         # dpc w/ a digit or two before (no space)
            r'|dpc' +              # dpc as a word by itself
        r')\b', '__mouse_age', context=0),
    TextMapping('ts',
        r'\b(?:' +
            r'theiler\sstages?|TS(?:\s|-)?\d\d?' +
        r')\b', '__mouse_age', context=0),
    TextMapping('ee',   # early embryo
        r'\b(?:' +
            r'blastocysts?|blastomeres?|fetus|fetuses' +
            r'|(?:(?:early|mid|late)(?:\s|-))?streak|morula|somites?' +
            r'|(?:' +
                r'(?:[1248]|one|two|four|eight)(?:\s|-)cell\s' +
                r'(?:' +   # "embryo" or "stage" must come after [1248] cell
                    r'stages?|' +
                    r'(?:' +
                        r'(?:(?:mouse|mice|cloned)\s)?embryos?' +
                    r')' +
                r')' +
            r')' +
        r')\b', '__mouse_age'),
    TextMapping('postnatal',    # 11/1/2021: leave Pnn out of mapping, these are
                                #   often gene symbols or cell lines
        r'\b(?:' +
            r'postnatal|neonatal|new(?:\s|-)?borns?|adults?|ages?' +
            #r'|P\d\d?' +  # note this matches P53 P63 P73 - common gene syn's
        r')\b', '__mouse_age', context=0),
    ]

textTransformer_age = TextTransformer(AgeMappings)

#-----------------------------------

class RefSample (BaseSample):
    """
    Represents a reference from the db and its GXD status, extracted text, etc.
    classified or not.

    HAS: ID, text

    Provides various methods to preprocess a sample record
    (preprocess the text prior to vectorization)
    """
    sampleClassNames = ['No','Yes']
    y_positive = 1	# sampleClassNames[y_positive] is the "positive" class
    y_negative = 0	# ... negative

    # fields of a sample as an input/output record (as text), in order
    fieldNames = [ \
            'ID'           ,
            'text'         ,
            ]
    fieldSep  = FIELDSEP
    recordEnd = RECORDEND
    preprocessorsToReport = set()  # set of objects w/ a getReports() method
                                   #   to include in getPreprocessorReport()

    # ---------------------------
    @classmethod
    def addPreprocessorToReport(cls, processor):
        cls.preprocessorsToReport.add(processor)

    @classmethod
    def getPreprocessorReport(cls):
        """ Return report text from preprocessor objects
        """
        text = ''
        for p in cls.preprocessorsToReport:
            text += p.getReport() + '\n'
        return text

    #----------------------
    # "preprocessor" functions.
    #  Each preprocessor should modify this sample and return itself
    #----------------------

    def standard(self):	# preprocessor
        '''
        "Standard" preprocessing steps we are using for production
        '''
        pass
        return self
    # ---------------------------

    def rmNewLines(self):        # preprocessor
        # remove '\n' from the text to facilitate simple term searches
        self.setField('text', self.getField('text').replace('\n', ' '))
        return self
    # ---------------------------

    def figureTextLegCloseWords50(self):        # preprocessor
        # figure legends + 50 words around "figure" references in paragraphs
        self.setField('text', '\n\n'.join( \
            figConverterLegCloseWords50.text2FigText(self.getField('text'))))
        return self
    # ---------------------------

    def textTransform_age(self):                # preprocessor
        '''
        Apply text transformations
        '''
        tt = textTransformer_age
        self.addPreprocessorToReport(tt)
        self.setField('text', tt.transformText(self.getField('text')))
        return self
    # ---------------------------
# end class RefSample ------------------------

class ClassifiedRefSample (RefSample, ClassifiedSample):
    """
    A Reference that has been classified as selected/rejected by GXD
    """
    fieldNames = [ \
            'knownClassName',
            'ID',
            '_refs_key',
            'relevance',
            'confidence',
            'orig TP/FP',
            'GXD status',
            'journal',
            'text',
            ]
    extraInfoFieldNames = [ \
            'relevance',
            'confidence',
            'GXD status',
            'journal',
            ]
    #----------------------

# end class ClassifiedRefSample ------------------------

if __name__ == "__main__":
    pass
