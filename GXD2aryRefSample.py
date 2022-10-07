#!/usr/bin/env python3
#
# Library to support handling of reference records
# for experimenting with GXD secondary triage rules.
import re
from baseSampleDataLib import *
import figureText
import GXD2aryRouter
from utilsLib import TextMapping, TextTransformer
#-----------------------------------

FIELDSEP     = '|'      # field separator when reading/writing sample fields
RECORDEND    = ';;'     # record ending str when reading/writing sample files

figConverterLegCloseWords75 = figureText.Text2FigConverter( \
                                            conversionType='legCloseWords',
                                            numWords=75)
#-----------------------------------
# Options for controlling the Age TextMapping reporting
REPORTBYREFERENCE = True       # True = report transformations by reference
                                # False= aggregate across whole corpus
REPORTFIXTRANSFORMS = False     # T/F report "fix" transformations
                                # (only applies if REPORTBYREFERENCE==True)

textTransformer_age = GXD2aryRouter.AgeTextTransformer(context=210)

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
    ageMatchReport = ''         # string w/ transformed age matches.
                                #  1 line per Reference per transformation

    # ---------------------------
    #@classmethod
    #def addPreprocessorToReport(cls, processor):
    #    cls.preprocessorsToReport.add(processor)

    @classmethod
    def getPreprocessorReport(cls):
        """ Return report text from preprocessor objects
        """
        # Age TextMapping report
        if REPORTBYREFERENCE:
            # get header line from standard report
            stdHdr = textTransformer_age.getReport().split('\n')[1]

            # add ID column
            cols = stdHdr.split('\t')
            hdr = '\t'.join(['ID'] + cols)  + '\n'
            output = hdr + cls.ageMatchReport
        else:   # get std report with counts across the whole corpus
            output = textTransformer_age.getReport()

        return output

    @classmethod
    def addToAgeMatchReport(cls, ID, line):
        cls.ageMatchReport += ID + '\t' + line + '\n'
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

    def lower(self):        # preprocessor
        # lower case the text
        self.setField('text', self.getField('text').lower())
        return self
    # ---------------------------

    def rmNewLines(self):        # preprocessor
        # remove '\n' from the text to facilitate simple term searches
        self.setField('text', self.getField('text').replace('\n', ' '))
        return self
    # ---------------------------

    def figureTextLegCloseWords75(self):        # preprocessor
        # figure legends + 75 words around "figure" references in paragraphs
        self.setField('text', '\n\n'.join( \
            figConverterLegCloseWords75.text2FigText(self.getField('text'))))
        return self
    # ---------------------------

    def textTransform_age(self):                # preprocessor
        ''' Apply age text transformations
        '''
        tt = textTransformer_age
        self.setField('text', tt.transformText(self.getField('text')))

        if REPORTBYREFERENCE:
            # get textTransformer report lines for this ref,
            # add ref ID to each line and save these to cls.matchReport
            lines = tt.getReport().split('\n')

            for line in lines[2:]:  # add ref ID to the match report lines
                if line.strip() != '' and \
                    (REPORTFIXTRANSFORMS or not line.startswith('fix')):
                    self.addToAgeMatchReport(self.getID(), line)

            tt.resetMatches()       # clear the transformer matches for next ref
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
