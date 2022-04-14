#!/usr/bin/env python3
#
# Library to support handling of reference records
# for experimenting with GXD secondary triage rules.
import re
from baseSampleDataLib import *
#import utilsLib
#-----------------------------------

FIELDSEP     = '|'      # field separator when reading/writing sample fields
RECORDEND    = ';;'     # record ending str when reading/writing sample files

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
            'orig TP/FP',
            'GXD status',
            'journal',
            ]
    #----------------------

# end class ClassifiedRefSample ------------------------

if __name__ == "__main__":
    pass
