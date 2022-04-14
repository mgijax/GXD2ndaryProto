#!/usr/bin/env python3
'''
  Purpose: Apply GXD secondary triage routing algorithm and evaluate.

  Inputs:  Sample file of classified reference records
  
  Outputs: a file Routing assignments, one line for each reference
           a file of text matches (to required and/or ignored text matches)
           a summary of Precision and Recall to stdout
'''
import sys
import os
import time
import argparse
import unittest
#import db
import refSample as SampleLib
from utilsLib import removeNonAscii
#-----------------------------------

sampleObjType = SampleLib.ClassifiedRefSample

# for the Sample output file
RECORDEND    = sampleObjType.getRecordEnd()
FIELDSEP     = sampleObjType.getFieldSep()
#-----------------------------------

def getArgs():

    parser = argparse.ArgumentParser( \
        description='Get test set for GXD 2ndary triage proto, write to stdout')

    parser.add_argument('inputFile', action='store',
        help="input file name. 'test' to run automated tests")

    parser.add_argument('-l', '--limit', dest='nResults',
        required=False, type=int, default=0, 		# 0 means ALL
        help="limit results to n references. Default is no limit")

    parser.add_argument('--textlength', dest='maxTextLength',
        type=int, required=False, default=None,
        help="only include the 1st n chars of text fields (for debugging)")

    parser.add_argument('-q', '--quiet', dest='verbose', action='store_false',
        required=False, help="skip helpful messages to stderr")

    defaultHost = os.environ.get('PG_DBSERVER', 'bhmgidevdb01')
    defaultDatabase = os.environ.get('PG_DBNAME', 'prod')

    parser.add_argument('-s', '--server', dest='server', action='store',
        required=False, default=defaultHost,
        help='db server. Shortcuts:  adhoc, prod, dev, test. (Default %s)' %
                defaultHost)

    parser.add_argument('-d', '--database', dest='database', action='store',
        required=False, default=defaultDatabase,
        help='which database. Example: mgd (Default %s)' % defaultDatabase)

    args =  parser.parse_args()

    if args.server == 'adhoc':
        args.host = 'mgi-adhoc.jax.org'
        args.db = 'mgd'
    elif args.server == 'prod':
        args.host = 'bhmgidb01.jax.org'
        args.db = 'prod'
    elif args.server == 'dev':
        args.host = 'mgi-testdb4.jax.org'
        args.db = 'jak'
    elif args.server == 'test':
        args.host = 'bhmgidevdb01.jax.org'
        args.db = 'prod'
    else:
        args.host = args.server
        args.db = args.database

    return args
#-----------------------------------

args = getArgs()
root, ext = os.path.splitext(args.inputFile)
args.predictionOutput = "%sPreds.txt" % root
args.matchesOutput    = "%sMatches.txt" % root

#-----------------------------------
class GXDrouter (object):
    def __init__(self):
        self.cat1Terms = ['embryo']
        self.cat1Ignore= [
            "embryonic lethal",
            "embryonic science",
            "embryonic death",
            "manipulating the mouse embryo: a laboratory manual",
            "Anat. Embryol.",
            "embryonic chick",
            "anat embryol",
            "embryonic stem",
            "embryogenesis",
            "drosophila embryo",
            "embryoid bodies",
            "d'embryologie",
            "microinjected embryo",
            "embryonic fibroblast",
            "embryo fibroblast",
            "human embryonic stem",
            "embryo implantation",
            "embryos die",
            "embryonic-lethal",
            "embryonically lethal",
            "embryonated",
            "chimera embryo",
            "embryonal stem",
            "embryonic viability",
            "chicken embryo",
            "embryo manip",
            "embryonic mortality",
            "postembryon",
            "embryonic carcinoma",
            "embryo injection",
            "carcinoembryonic",
            "HEK293T  embryo",
            "embryonic cell line",
            "embryonic kidney cells",
            "embryonic myosin",
            "embryonic myogenesis",
            "injected embryo",
            "human embryo",
            "embryonated chick",
            "embryo lethal",
            "human embryonic",
            "rat embryo",
            "chick embryo",
            "cultured embryo",
            "embryo culture",
            "embryoid body",
            "zebrafish embryo",
            "embryology",
            "bovine embryo",
            "embryonal rhabdomyosarcoma",
            "Xenopus embryo",
            "embryonic rat",
            "embryonic kidney 293",
            "embryonal fibroblast",
            ]


    def routeThisRef(self, text):
        """ given the text of a reference, return "Routed" or "Not Routed"
        """
        return "Routed" # (for now)
#-----------------------------------

def process():
    ''' go through the refs and determine routing
    '''
    startTime = time.time()
    verbose("%s\nHitting database %s %s as mgd_public\n" % \
                                        (time.ctime(), args.host, args.db,))
    # Build sql
    if args.nResults != 0:
        limitClause = 'limit %d\n' % args.nResults
        q += limitClause

    outputSampleSet = SampleLib.ClassifiedSampleSet(sampleObjType=sampleObjType)

    results = db.sql(q, 'auto')

    for i,r in enumerate(results):
        if i % 200 == 0: verbose("..%d" % i)
        text = getText4Ref(r['_refs_key'])
        text = cleanUpTextField(text) + '\n'
        try:
            sample = sqlRecord2ClassifiedSample(r, text )
            outputSampleSet.addSample(sample)
        except:         # if some error, try to report which record
            sys.stderr.write("Error on record %d:\n%s\n" % (i, str(r)))
            raise

    # Add meta-data to sample set
    outputSampleSet.setMetaItem('host', args.host)
    outputSampleSet.setMetaItem('db', args.db)
    outputSampleSet.setMetaItem('time', time.strftime("%Y/%m/%d-%H:%M:%S"))

    # Write output
    outputSampleSet.write(sys.stdout)

    verbose('\n')
    verbose("wrote %d samples:\n" % outputSampleSet.getNumSamples())
    verbose("%8.3f seconds\n\n" %  (time.time()-startTime))

    return
#-----------------------------------

def cleanUpTextField(text):

    if text == None:
        text = ''

    if args.maxTextLength:	# handy for debugging
        text = text[:args.maxTextLength]

    text = removeNonAscii(cleanDelimiters(text))
    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')
    return text
#-----------------------------------

def cleanDelimiters(text):
    """ remove RECORDEND and FIELDSEPs from text (replace w/ ' ')
    """
    return text.replace(RECORDEND,' ').replace(FIELDSEP,' ')
#-----------------------------------

def verbose(text):
    if args.verbose:
        sys.stderr.write(text)
        sys.stderr.flush()
#-----------------------------------

def doAutomatedTests():

    #sys.stdout.write("No automated tests at this time\n")
    #return

    sys.stdout.write("%s\nHitting database %s %s as mgd_public\n" % \
                                        (time.ctime(), args.host, args.db,))
    sys.stdout.write("Running automated unit tests...\n")
    unittest.main(argv=[sys.argv[0], '-v'],)

class MyTests(unittest.TestCase):
    def test_getText4Ref(self):
        t = getText4Ref('11943') # no text
        self.assertEqual(t, '')

        t = getText4Ref('361931') # multiple sections
        expText = 'lnk/ mice.\n\n\n\nfig. 5.' # boundry body-author fig legends
        found = t.find(expText)
        self.assertNotEqual(found, -1)

#-----------------------------------

def main():
    db.set_sqlServer  (args.host)
    db.set_sqlDatabase(args.db)
    db.set_sqlUser    ("mgd_public")
    db.set_sqlPassword("mgdpub")

    if   args.inputFile == 'test': doAutomatedTests()
    else: process()

    exit(0)
#-----------------------------------
if __name__ == "__main__":
    main()
