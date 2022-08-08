#!/usr/bin/env python3
'''
  Purpose: Do static text analysis on a GXD sample file

  Inputs:  Sample file of GXD routed (classified) reference records.
            See refSample.py for the fields of these records.
  
  Outputs: Static analysis report to stdout.
'''
import sys
import os
import time
import argparse
import unittest
import GXD2aryRefSample as SampleLib
from sklearnHelperLib import predictionType
#from utilsLib import removeNonAscii
#-----------------------------------

sampleObjType = SampleLib.ClassifiedRefSample

#-----------------------------------

def getArgs():

    parser = argparse.ArgumentParser( \
        description='do static text analyisis for GXD 2ndary triage proto. ' +
        'Write report to stdout.')

    parser.add_argument('sampleFileName', action='store',
        help="the sample file to read. (use one preprocessed for figtext?)")

    parser.add_argument('excludeFileName', action='store',
        help="file of exclude terms or 'none'")

    parser.add_argument('terms', nargs='+',
        help="terms that you want analysis for. '-' to read terms from stdin")

    parser.add_argument('-l', '--limit', dest='nToDo',
        required=False, type=int, default=0,            # 0 means ALL
        help="only process this many references. Default is no limit")

    parser.add_argument('-q', '--quiet', dest='verbose', action='store_false',
        required=False, help="skip helpful messages to stderr")

    args =  parser.parse_args()

    return args
#-----------------------------------

args = getArgs()

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
#-----------------------------------

def main():
    doStaticAnalysis()

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

    testSet = SampleLib.ClassifiedSampleSet(sampleObjType=sampleObjType)
    testSet.read(args.sampleFileName)

    if args.nToDo > 0: samples = testSet.getSamples()[:args.nToDo]
    else: samples = testSet.getSamples()

    if args.excludeFileName != 'none':
        exclude = [line.strip() for line in open(args.excludeFileName, 'r') \
                            if not line.startswith('#') and line.strip() != '']
    else:
        exclude = []

    excludeDict = {x.lower() : x.upper() for x in exclude}

    verbose('got %d exclude terms\n' % len(exclude))


    totalNumPos = testSet.getNumPositives()
    totalNumNeg = testSet.getNumNegatives()
    TermsAndStats = []

    t = "Analyzing %d refs from '%s'\n" % (len(samples), args.sampleFileName)
    sys.stdout.write(t)

    header = "%s\t%s\t%s\t%s\t%s\t%s\n" % ('term', 'numPos', 'numNeg',
                                        'posFraction', 'negFraction', 'dValue')
    sys.stdout.write(header)
    
    terms = []
    for term in args.terms:
        if term == '-':           # read terms from stdin
            terms += [line[:-1] for line in sys.stdin \
                            if not line.startswith('#') and line.strip() != '']
        else:
            terms.append(term)

    for term in terms:
        term = term.lower()
        numPos = 0
        numNeg = 0
        for i, ref in enumerate(samples):
            if i % 1000 == 0: verbose('.')

            text = ref.getDocument()

            # remove exclude terms first
            newText = text.replace('\n', ' ')
            for exTerm, replacement in excludeDict.items():
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
    sys.stdout.write("Total Pos Refs: %d\nTotal Neg Refs: %d\n" % \
                                                (totalNumPos, totalNumNeg))
    sys.stdout.write("Excluded terms:\n")
    for term in sorted(excludeDict.keys()):
        sys.stdout.write("'%s'\n" % term)

    verbose("%8.3f seconds\n\n" %  (time.time()-startTime))
    return
#-----------------------------------
if __name__ == "__main__":
    main()
