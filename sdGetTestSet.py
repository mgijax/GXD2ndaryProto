#!/usr/bin/env python3
'''
  Purpose:
           run sql to get test set
           (minor) Data transformations include:
            replacing non-ascii chars with ' '
            replacing FIELDSEP and RECORDSEP chars in the doc text w/ ' '

            To run automated tests: python sdGetKnownSamples.py test

  Outputs:      Delimited file to stdout
                See RefSample.ClassifiedSample for output format
'''
import sys
import os
import time
import argparse
import unittest
import db
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

    parser.add_argument('option', action='store', default='counts',
        choices=['samples', 'test'],
        help='get samples or just run automated tests')

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

#-----------------------------------

def doSamples():
    ''' Write known samples to stdout.
    '''
    startTime = time.time()
    verbose("%s\nHitting database %s %s as mgd_public\n" % \
                                        (time.ctime(), args.host, args.db,))
    # Build sql
    q = """
    -- select TP's: originally routed, and selected by curators
    select b._refs_key, a.accid "ID", rt.term "relevance", r.confidence,
        st.term "GXD status", 'TP' "orig TP/FP", b.journal
    from bib_refs b join bib_workflow_status s
        on (b._refs_key = s._refs_key and s.iscurrent =1
            and s._group_key = 31576665) -- current GXD status
    join bib_workflow_status s2 on (b._refs_key = s2._refs_key
        and s2._group_key = 31576665 and s2._createdby_key = 1618) -- 2nd triage
    join bib_workflow_relevance r on (b._refs_key = r._refs_key
        and r._createdby_key = 1617) -- relevance_classifier
    join acc_accession a on (b._refs_key = a._object_key
        and a._mgitype_key = 1 and a._logicaldb_key = 1
        and a.prefixpart = 'MGI:')
    join voc_term st on (s._status_key = st._term_key)
    join voc_term s2t on (s2._status_key = s2t._term_key)
    join voc_term rt on (r._relevance_key = rt._term_key)
    where
    b.isreviewarticle = 0
    and s2._status_key = 31576670 -- routed
    and s._status_key in (31576671, 31576673, 31576674) -- chosen, indexed, full-coded
    union
    -- select FP's: originally routed, but rejected by curators
    select b._refs_key, a.accid "ID", rt.term "relevance", r.confidence,
        st.term "GXD status", 'FP' "orig TP/FP", b.journal
    from bib_refs b join bib_workflow_status s
        on (b._refs_key = s._refs_key and s.iscurrent =1
            and s._group_key = 31576665) -- current GXD status
    join bib_workflow_status s2 on (b._refs_key = s2._refs_key
        and s2._group_key = 31576665 and s2._createdby_key = 1618) -- 2nd triage
    join bib_workflow_relevance r on (b._refs_key = r._refs_key
        and r._createdby_key = 1617) -- relevance_classifier
    join acc_accession a on (b._refs_key = a._object_key
        and a._mgitype_key = 1 and a._logicaldb_key = 1
        and a.prefixpart = 'MGI:')
    join voc_term st on (s._status_key = st._term_key)
    join voc_term s2t on (s2._status_key = s2t._term_key)
    join voc_term rt on (r._relevance_key = rt._term_key)
    where
    b.isreviewarticle = 0
    and s2._status_key = 31576670 -- routed
    and s._status_key in (31576672) -- Rejected
    """
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

def sqlRecord2ClassifiedSample(r,               # sql Result record
    text,
    ):
    """
    Return a ClassifiedSample object for the sql record
    Encapsulates knowledge of ClassifiedSample.setFields() field names
    """
    newR = {}
    newSample = sampleObjType()

    if r['GXD status'] == 'Rejected':
        knownClassName = 'No'
    elif r['GXD status'] in ['Chosen', 'Indexed', 'Full-coded']:
        knownClassName = 'Yes'
    else:
        raise ValueError("Invalid GXD status '%s'\n" % r['GXD status'])

    ## populate the Sample fields
    newR['knownClassName'] = knownClassName
    newR['ID']             = str(r['ID'])
    newR['_refs_key']      = str(r['_refs_key'])
    newR['relevance']      = str(r['relevance'])
    newR['confidence']     = str(r['confidence'])
    newR['orig TP/FP']     = str(r['orig TP/FP'])
    newR['GXD status']     = str(r['GXD status'])
    newR['journal']        = str(r['journal'])
    newR['text']           = text

    return newSample.setFields(newR)
#-----------------------------------

def getText4Ref(refKey):
    """ Return extracted text (string) - in lower case -
        for the specified _refs_key
    """
    # sql to get extracted text, omitting reference and supplemental sections
    extractedSql = '''
        select distinct lower(d.extractedText) as extractedText
        from bib_workflow_data d
        where d._refs_key = %s
        and d._extractedtext_key not in (48804491, 48804492)
        and d.extractedText is not null
    '''
    results = db.sql(extractedSql % (refKey), 'auto')
    textparts = [ r['extractedtext'] for r in results]

    return '\n\n'.join(textparts)
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

    if   args.option == 'test':    doAutomatedTests()
    elif args.option == 'samples': doSamples()
    else: sys.stderr.write("invalid option: '%s'\n" % args.option)

    exit(0)
#-----------------------------------
if __name__ == "__main__":
    main()
