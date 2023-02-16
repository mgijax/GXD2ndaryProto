#!/usr/bin/env python3

# combine two dataSets, removing refs duplicates (refs w/ the same _refs_key)

import GXD2aryRefSample as SampleLib

sampleObjType = SampleLib.ClassifiedRefSample

ts3   = SampleLib.ClassifiedSampleSet(sampleObjType=sampleObjType)
p2005 = SampleLib.ClassifiedSampleSet(sampleObjType=sampleObjType)

ts3.read('testSet3.fulltext.txt')
print("ts3: %d records" % ts3.getNumSamples())

p2005.read('testSet.post2005.txt')
print("p2005: %d records" % p2005.getNumSamples())

ts3RefKeys = set()

for r in ts3.getSamples():
    k = r.getField('_refs_key')
    #print(k)
    ts3RefKeys.add(k)

intersect = 0
for p in p2005.getSamples():
    pk = p.getField('_refs_key')
    if pk in ts3RefKeys:
        intersect += 1
    else:
        ts3.addSample(p)

ts3.write('testSet.combined.fulltext.txt')
print("combined: %d records" % ts3.getNumSamples())
print("intersection: %d records" % intersect)
