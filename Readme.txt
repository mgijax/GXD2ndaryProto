Analysis and prototyping GXD secondary Triage - what files are where

See https://mgi-jira.atlassian.net/browse/WTS2-848

The test datasets are stored in WTS2-848/TestDataSets.
See http://bhmgiwk01lp.jax.org/mediawiki/index.php/sw:GXD2ndaryProto#Test_Sets

All the spreadsheets w/ data & analysis are in this google drive folder:
https://drive.google.com/drive/folders/1CriRWMvOUKvfXjw7xlp0M345GDvd7V2G

AND are stored in WTS2-848/AnalysisSpreadsheets

Initial analysis of the GXD secondary loader w/ refs & routings pulled from the
db with SQL (the SQL is in the TR) is here:
https://docs.google.com/spreadsheets/d/1JQdMDfTn1v-UwL9RDLF-zL_Kl5eu44awL6G8-edNqYo/edit#gid=111363377

    (Routing: just looking for "embryo" in a non-excluded context)
    Overall Precision 11.89% and Recall 100%

Contents of this directory      - MOST RECENT STUFF IS TOWARD THE BOTTOM

InitialFigText/
    Code from the initial attempt to hack the secondary triage loader (in
    the littriageload product) so that it would route just looking at figure
    text instead of the full extracted text.

    Routings and analysis are here:
    https://docs.google.com/spreadsheets/d/1JQdMDfTn1v-UwL9RDLF-zL_Kl5eu44awL6G8-edNqYo/edit#gid=494169610

    Overall Precision 27%. Did not compute Recall

NewRules/
    - new code base https://github.com/mgijax/GXD2ndaryProto
      with analysis scripts

    JustEmbryo/
        - results from just searching for embryo in a non-excluded context
        - sort of duplicates initual analysis but in new code base
        - Precision 11.92%  Recall 100%
        - No results are in a spreadsheet

    cat2.1/
        - results from 1st version that implemented cat 2 terms (assay types)
        - Precision 12.90%  Recall 98.95%
        - No results are in a spreadsheet

    cat2.2/
        - results from 2nd version that implemented cat 2 terms (assay types)
        - removed "knockin" from assay terms, added embryo exclude terms
        - Precision 13.19%  Recall 98.74%
        - No results are in a spreadsheet

    figText/
        - results from various versions of where we restrict the term searching
            to just figure text, not the full text
            cat 1 (embryo) and cat 2

            Analysis is in
            https://docs.google.com/spreadsheets/d/1buH8bQ_EOc6NNehleizs_Qxdzh-VOQSZhUzTHR1KZkQ/edit#gid=0

        Assay/
            - cat 2 are assay terms
            - Precision 30.53  Recall 83.82

        Age/
            - cat 2 are just age terms mapped to __mouse_age
            - includes adult and postnatal age terms in the mapping
            - Precision 32.03 Recall 85.83

        AgeAssay/
            - cat 2 are assay terms and __mouse_age
            - includes adult and postnatal age terms in the mapping
            - Precision 28.40 Recall 87.69

        AgeAssay2/
            - cat 2 are assay terms and tweaked __mouse_age
            - excludes adult and postnatal age terms in the mapping
            - includes headfold, (limb)bud, morulae
            - Precision 29.48  Recall 87.54

        AgeAssay3/
            - cat 2 are assay terms and tweaked __mouse_age as in AgeAssay2
            - added more assay terms, see Details.txt
            - Precision 28.16  Recall 87.89
            - TP 1749. FP 4491. TN 10483. FN 241 

        AgeAssay4/
            - cat 2 are assay terms and __mouse_age  from AgeAssay3
            - for 561 journals w/ no GXD papers, set routed = No
            - most of the 241 FN don't have "embryo" in figure text.
            - Precision 30.31   Recall 87.89
                    - Journal action gives 2pt bump in precision. good idea
            - TP 1749   FP 4022  TN 10952  FN 241

        AgeAssay5/
            - "embryo" in full text, cat 2 terms in figText
            - cat 2 are assay terms and __mouse_age  from AgeAssay3
            - for 561 journals w/ no GXD papers, set routed = No
            - Precision 14.49   Recall 99.70
                    - embryo in full text kills precision, add 7000 FP
            - TP 1984. FP 11706. TN 3268. FN 6

        AgeAssay6/      (jackie's idea)
            - all figure text
            - cat 1 is __mouse_age cat 2 are assay terms
            - for 561 journals w/ no GXD papers, set routed = No
            - Precision 35.49   Recall 93.02
                    - mouse_age as replacement for "embryo". good option
            - TP 1851.  FP 3364.  TN 11610. FN 139

        AgeAssay7/      (jim's tweak to jackie's idea)
            - all figure text
            - cat 1 is {embryo, __mouse_age} cat 2 are assay terms
            - for 561 journals w/ no GXD papers, set routed = No
            - diff between AgeAssay6 and AgeAssay7:  (in figtext)
                ~100 Yes's that have "embryo" but not mouse_age
                ~2100 No's that have "embryo" but not mouse_age
            - Precision 26.53   Recall 98.14
                    - mouse_age OR embryo in fig text great recall, P so so
            - TP 1953.  FP 5408.  TN 9566. FN 37

        AgeAssay8/      (connie's idea)
            - cat 1 is embryo against full text
            - cat 2 are assay terms in figure text
            - for 561 journals w/ no GXD papers, set routed = No
            - Precision 14.58   Recall 99.25
                    - embryo in full text kills precision
            - TP 1975.   FP 11572.   TN 3402.  FN 15

        AgeAssay9/   (ponder mouse_age as replacement for embryo in fulltext) 
            - cat 1 is mouse_age against full text
            - cat 2 are assay terms in figure text
            - for 561 journals w/ no GXD papers, set routed = No
            - Precision 22.58   Recall 97.24 ---  not as good as AgeAssay7
            - TP 1935.   FP 6633.   TN 8341.  FN 55

        Age3Assay6/      (Age3 compare to jackie's idea AgeAssay6)
            - all figure text
            - cat 1 is __mouse_age - new age terms
                - See NewRules/figText/age_mappings/age3*
            - cat 2 are the original assay terms
            - for 561 journals w/ no GXD papers, set routed = No
            - Precision 32.76   Recall 95.12
            - TP 1891.  FP 3881.  TN 11095. FN 97

        Age3Assay10/      (Age3 and new assay terms: redone: ' mount' & 'pcr')
            - all figure text
            - cat 1 is __mouse_age - new age terms
                - See NewRules/figText/age_mappings/age3*
            - cat 2 are new assay terms from Connie's analysis
            - for 561 journals w/ no GXD papers, set routed = No
            - Precision 32.15   Recall 95.47
            - TP 1898.  FP 4005.  TN 10971. FN 90

        Age4Assay10/      (Age4 and new assay terms: redone: ' mount' & 'pcr')
            - all figure text
            - cat 1 is __mouse_age - removes fetal bovine/calf serum ts0-6
                - See NewRules/figText/age_mappings/age4*
            - cat 2 are new assay terms from Connie's analysis
            - for 560 journals w/ no GXD papers, set routed = No
            - Precision 32.97   Recall 95.42
            - TP 1897.  FP 3856.  TN 11120. FN 91

--- route2/ ----------------------------------------------------------------
        - Reimplementation of routing logic all collapsed into one processor
        - includes "embryo" search in full text (w/ exclude terms)
        - journal skipping
        - mouse age detection in figure text
        - cat2 (assay) term search in figure text (w exclude terms)
        - redesigned match reports:
            ExcMatches.txt      - matches to exclude terms
            FNMatches.txt       - positive & excludematches for FN routings
            FPMatches.txt       - positive matches for FP routings
            TNMatches.txt       - positive matches for TN routings
            TPMatches.txt       - positive matches for TP routings
            AgeMatches.txt      - all age matches

        Age4Assay11/  6/7/2022    (Age4 and cat2 terms as in Age4Assay10)
            - embryo in full text, the age/cat2 in figure text
            - cat2 excludes "amount"
            - for 560 journals w/ no GXD papers, set routed = No
            - roughly the same as Age4Assay10
            - Precision 33.23   Recall 95.37
            - TP 1896.  FP 3809.  TN 11167. FN 92

        Age5Assay11/  6/7/2022    (Age5. Same cat2 terms as in Age4Assay11)
            - embryo in full text, the age/cat2 in figure text
            - Age5 - embryonic day restrictions
                * acceptable decimals only .0 .5 .25 .75
                * not preceded by '-' (eliminates mfg-e8, etc)
                * not followed '%' -bp -ml -mg
                * omit 'bud' if preceded by 'fin '
            - cat2 excludes "amount"
            - for 560 journals w/ no GXD papers, set routed = No
            - Slight improvement to precision, no add'l FN
            - Precision 33.51   Recall 95.37
            - TP 1896.  FP 3762.  TN 11214. FN 92

        Age6Assay11/  6/8/2022    (Age6. Initial age exclusion logic)
            - embryo in full text, the age/cat2 in figure text
            - Age6 - like Age5 but excludes age matches where
                * pre/post text (30) chars of the match contains an
                  age exclusion term (e.g., " inject", 'human', ...)
                * & is no blocking text between exclusion term & age text
                  ('; ' or '. ' or '\n\n' (paragraph boundary)
            - cat2 excludes "amount"
            - for 560 journals w/ no GXD papers, set routed = No
            - Adds two points to precision, lose 3 TP to FN
            - Precision 35.30   Recall 95.22
            - TP 1893.  FP 3470.  TN 11506. FN 95

        Age6Assay12/  6/8/2022    (Cat2 chgs: "expression" term tweaks)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: replace "expression" by more specific expression terms
            - cat2 excludes "amount"
            - for 560 journals w/ no GXD papers, set routed = No
            - Adds two points to precision, lose 3 TP to FN
            - Precision 35.45   Recall 95.22
            - TP 1893.  FP 3447.  TN 11529. FN 95

        Age6Assay13/  6/8/2022    (Cat2 chgs: immuno exclude terms)
            - embryo in full text, the age/cat2 in figure text
            - cat2 excludes "amount". add immunopre and immunorea
            - for 560 journals w/ no GXD papers, set routed = No
            - NO CHANGED ROUTINGS
            - Precision 35.45   Recall 95.22
            - TP 1893.  FP 3447.  TN 11529. FN 95

        Age6Assay14/  6/8/2022    (Cat2 chgs: replace 'pcr')
            - embryo in full text, the age/cat2 in figure text
            - Cat2: replace 'pcr' by more specific terms
            - cat2 excludes "amount". add chip pcr exclude terms
            - for 560 journals w/ no GXD papers, set routed = No
            - 15 FP -> TN, 1 additional FN
            - Precision 35.54   Recall 95.17
            - TP 1892.  FP 3432.  TN 11544. FN 96

        Age6Assay15/  6/8/2022    (Cat2 chgs: other term tweaks)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: other tweaks
            - cat2 excludes: tweaks, "amount" gone since "mount" is out of cat2
            - for 560 journals w/ no GXD papers, set routed = No
            - 150 FP -> TN, 19 additional FN
            - Precision 36.33   Recall 94.22
            - TP 1873.  FP 3282.  TN 11694. FN 115
            [ just trying to see:  Age6Assay15 but looking for mouse_age in FULL
                text instead of figure text, kills precision (>3000 more FP)
                - Precision 22.32   Recall 97.28
                - TP 1934.  FP 6729.  TN 8247. FN 54
            ]

        Age6Assay16/  6/9/2022    (Cat2 chgs: term tweaks)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: add sagittal view, section co-expression, overexpression
            - cat2 excludes: fix 'methods" section', remove immunorea
            - for 560 journals w/ no GXD papers, set routed = No
            - 20 FN -> TP, 85 TN -> FP
            - Precision 35.99   Recall 95.22
            - TP 1893.  FP 3367.  TN 11609. FN 95

        Age6Assay17/  6/10/2022    (Cat2 chgs: term tweaks)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: just "view" (remove sagittal view)
            - cat2 excludes: same as Age6Assay16
            - for 560 journals w/ no GXD papers, set routed = No
            - 36 TN -> FP   - so lost a few TN from Age6Assay16
            - Precision 35.74   Recall 95.22
            - TP 1893.  FP 3403.  TN 11573. FN 95

        Age6Assay18/  6/10/2022    (Cat2 chgs: term tweaks)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: remove "view", add sagittal frontal transverse coronal
            - cat2 excludes: same as Age6Assay16
            - for 560 journals w/ no GXD papers, set routed = No
            - 7 TN -> FP   - so lost a few TN from Age6Assay16
            - Precision 35.94   Recall 95.22
            - TP 1893.  FP 3374.  TN 11602. FN 95

        Age6Assay19/  6/10/2022    (Cat2 chgs: term tweaks)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: try {sagittal frontal transverse coronal} view
            - cat2 excludes: same as Age6Assay16
            - for 560 journals w/ no GXD papers, set routed = No
            - 2 TN -> FP   - so lost a few TN from Age6Assay16
            - Precision 35.97   Recall 95.22
            - TP 1893.  FP 3369.  TN 11607. FN 95

        Age7Assay16/  6/13/2022    (Age exclusion implementation chg)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: same as Age6Assay16
            - Age excludes: uses regex for word boundaries instead of " "
            - for 560 journals w/ no GXD papers, set routed = No
            - 14 FP -> TN   - compared to Age6Assay16
            - Precision 36.08   Recall 95.22
            - TP 1893.  FP 3353.  TN 11623. FN 95

        Age8Assay16/  6/13/2022    (Age: add embryo lysate terms)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: same as Age6Assay16
            - Age excludes: same as Age7
            - for 560 journals w/ no GXD papers, set routed = No
            - Precision 36.08   Recall 95.27
            - TP 1894.  FP 3355.  TN 11621. FN 94

        Age9Assay16/  6/13/2022 (Age: add day #.5, #.5 day, # day embryo, tweak)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: same as Age6Assay16
            - Age excludes: same as Age7
            - for 560 journals w/ no GXD papers, set routed = No
            - 12 FN -> TP, 59 TN -> FP (compared to Age8)
            - Precision 35.83   Recall 95.88
            - TP 1906.  FP 3414.  TN 11562. FN 82

        Age10Assay16/  6/13/2022 (Age: add back E14)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: same as Age6Assay16
            - Age excludes: same as Age7
            - for 560 journals w/ no GXD papers, set routed = No
            - 3 FN -> TP, 53 TN -> FP (compared to Age9)
            - Precision 35.51   Recall 96.03
            - TP 1909.  FP 3467.  TN 11509. FN 79
             
              (tried adding "postnatal" as age Exclude term, 
               TP 1899  FP 3449  TN 11527  FN 89. Many exclusions had an 
               embryonic age plus "as well as POSTNATAL" or "and POSTNATAL", 
               to not clear this is good)

        Age10Assay16_210_50/  6/13/2022 (Age: chg age exclude context 30 -> 210)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: same as Age6Assay16
            - Age excludes: same as Age7
            - (tried exclude context 120, 150, 180, 210 = best)
            - for 560 journals w/ no GXD papers, set routed = No
            - 4 TP -> FN, 235 FP -> TN (compared to Age10) - BEST YET?
            - Precision 37.48   Recall 95.82
            - TP 1905.  FP 3178.  TN 11798. FN 83

        Age10Assay16_210_100/  6/13/2022 (figText words: 50 -> 100, age context: 210)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: same as Age6Assay16
            - Age excludes: same as Age7
            - for 560 journals w/ no GXD papers, set routed = No
            - 6 FN -> TP, 103 TN -> FP (compared to Age11)
            - Precision 36.11   Recall 96.13
            - TP 1911.  FP 3381.  TN 11595. FN 77

        Age10Assay20/  6/13/2022 (cat2 "view" tweaks)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: sagittal coronal transverse frontal rostral caudal
            - Age excludes: same as Age7
            - for 560 journals w/ no GXD papers, set routed = No
            - 10 TN -> FP (compared to Assay16))
            - Precision 36.04   Recall 96.13
            - TP 1911.  FP 3391.  TN 11585. FN 77

        Age10Assay20_210_75/  6/13/2022 (figText words 75, age context 210)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: sagittal coronal transverse frontal rostral caudal
            - Age excludes: same as Age7
            - for 560 journals w/ no GXD papers, set routed = No
            - figtext 75 words seems pretty good
            - Precision 36.58   Recall 96.08
            - TP 1910.  FP 3311.  TN 11665. FN 78

        >>>>>>>>>>> DECIDED 6/14 TO USE 210 and 75 <<<<<<<<<<<<<

        Age10Assay21_210_75/  6/13/2022 (get rid of "view" words)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: lose: sagittal coronal transverse frontal rostral caudal
            - Age excludes: same as Age7
            - for 560 journals w/ no GXD papers, set routed = No
            - Precision 36.66   Recall 96.03
            - TP 1909.  FP 3299.  TN 11677. FN 79

        Age11Assay22/  6/20/2022 (trying new age exclude term, experiment 1)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: added "-gal stain" and "-galactosidase stain"
            - Age excludes: facs, cytometry
            - for 560 journals w/ no GXD papers, set routed = No
            - 10 FP->TN
            - Precision 36.73   Recall 96.03
            - TP 1909.  FP 3289.  TN 11687. FN 79

        Age12Assay22/  6/20/2022 (trying new age exclude terms, experiment 2)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: includes "-gal stain" and "-galactosidase stain"
            - Age excludes: chip-seq, atac-seq, microarray, ...
            - for 560 journals w/ no GXD papers, set routed = No
            - 19 FP->TN
            - Precision 36.86   Recall 96.03
            - TP 1909.  FP 3270.  TN 11706. FN 79

        Age13Assay22/  6/20/2022 (trying new age exclude terms, experiment 3)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: includes "-gal stain" and "-galactosidase stain"
            - Age excludes: rna-seq, rnaseq
            - for 560 journals w/ no GXD papers, set routed = No
            - 9 FP->TN
            - Precision 36.92   Recall 96.03
            - TP 1909.  FP 3261.  TN 11715. FN 79

        Age14Assay22/  6/20/2022 (trying new age exclude terms, experiment 4)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: includes "-gal stain" and "-galactosidase stain"
            - Age excludes: exposure, electodes, oil red, necrotic, dose
            -   "dose" might need word boundary at front "_dose"?
            - for 560 journals w/ no GXD papers, set routed = No
            - 195 FP->TN, 2 TP->FN. The New FN: MGI:6843985, MGI:6868083
            - Precision 38.35   Recall 95.93
            - TP 1907.  FP 3066.  TN 11910. FN 81

        Age15Assay22/  6/20/2022 (trying new age exclude terms, experiment 5)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: includes "-gal stain" and "-galactosidase stain"
            - Age excludes: giemsa, eioin, h&e, ...
            - for 560 journals w/ no GXD papers, set routed = No
            - 4 FP->TN, 1 TP->FN. The New FN: MGI:6712566
            - Precision 38.37   Recall 95.88
            - TP 1906.  FP 3062.  TN 11914. FN 82

        Age16Assay22/  6/20/2022 (trying new age exclude terms, experiment 6)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: includes "-gal stain" and "-galactosidase stain"
            - Age excludes: tropicalis, drosophila, worm, ...
            - for 560 journals w/ no GXD papers, set routed = No
            - 19 FP->TN, 0 TP->FN.
            - Precision 38.51   Recall 95.88
            - TP 1906.  FP 3043.  TN 11933. FN 82

        Age17Assay22/  6/20/2022 (trying new age exclude terms, experiment 7)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: includes "-gal stain" and "-galactosidase stain"
            - Age excludes: dox, tamoxifen
            - for 560 journals w/ no GXD papers, set routed = No
            - 8 FP->TN, 0 TP->FN.
            - Precision 38.58   Recall 95.88
            - TP 1906.  FP 3035.  TN 11941. FN 82

        Age18Assay22/  6/20/2022 (trying new age exclude terms, experiment 8)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: includes "-gal stain" and "-galactosidase stain"
            - Age excludes: chameleon, equine, quail, zikv, bursa
            - for 560 journals w/ no GXD papers, set routed = No
            - 1 FP->TN, 0 TP->FN.
            - Precision 38.58   Recall 95.88
            - TP 1906.  FP 3034.  TN 11942. FN 82

        Age19Assay22/  6/20/2022 (trying new age exclude terms, experiment 9)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: includes "-gal stain" and "-galactosidase stain"
            - Age: added "autopod" and "embryonic stage|age"
            - for 560 journals w/ no GXD papers, set routed = No
            - 3 FN->TP, 79 TN->FP
            - Precision 38.01   Recall 96.03
            - TP 1909.  FP 3113.  TN 11863. FN 79

        Age20Assay22/  6/20/2022 (trying new age exclude terms, experiment 10)
            - embryo in full text, the age/cat2 in figure text
            - Cat2: includes "-gal stain" and "-galactosidase stain"
            - Age: chged age excludes: lose pregnant terms, tumor,
                dose->more specific terms
            - for 560 journals w/ no GXD papers, set routed = No
            - 2 FN->TP, 61 TN->FP
            - Precision 37.58   Recall 96.13
            - TP 1911.  FP 3174.  TN 11802. FN 77

        Age20Assay22_post2005/  6/23/2022 (all GXD papers since 2005)
            - embryo in full text, the age/cat2 in figure text
            - for 382 journals w/ no GXD papers, set routed = No
            - Precision 100   Recall 96.81
            - TP 19692.  FP 0.  TN 0. FN 648

        Age20Assay22_knockins/  6/23/2022 (all knockin papers since 2005)
            - embryo in full text, the age/cat2 in figure text
             -for 382 journals w/ no GXD papers, set routed = No
            - Precision 100   Recall 97.83
            - TP 3288.  FP 0.  TN 0. FN 73

        Age20Assay22_j/  7/6/2022 (using shortened skipjournals from post2005)
            - Cat2: includes "-gal stain" and "-galactosidase stain"
            - 276 TN->FP
            - Precision 35.71   Recall 96.13
            - TP 1911.  FP 3441.  TN 11535. FN 77

        Age21Assay22/  7/12/2022 (regular testset)
            - Age: reworked DPC, allow '.'s and d number pc
            - no new FP - good (same as Age20Assay22_j)
            - Precision 35.71   Recall 96.13
            - TP 1911.  FP 3441.  TN 11535. FN 77
        Age21Assay22_p2005/  7/12/2022 (all GXD papers since 2005)
            - 12 FN->TP,   helped a bit
            - Precision 100   Recall 96.87
            - TP 19704.  FP 0.  TN 0. FN 636

        Age22Assay22/  7/13/2022 (regular testset)
            - Age: ee: allow '-'s (e.g., 1-cell-embryo)
                Developmental: allow '-'s. Add: mice embryo(s),
                    age|stage of embryo, developmental time course
            - 14 new TP, 235 new FP
            - Precision 33.18   Recall 96.83
            - TP 1925.  FP 3876.  TN 11100. FN 63
        Age22Assay22_p2005/  7/13/2022 (all GXD papers since 2005)
            - 90 FN->TP,
            - Precision 100   Recall 97.32
            - TP 19794.  FP 0.  TN 0. FN 546

        Age23Assay22/  7/13/2022 (regular testset)
            - Age: add misc age terms: genepaint, time series,
                allen brain|atlas|institute, embryo mouse brain
            - 1 new TP, 100 new FP (not a great trade off)
                Decision: genepaint is good to keep. Lose Allen & time series.
            - Precision 32.63   Recall 96.88
            - TP 1926.  FP 3976.  TN 11000. FN 62
        Age23Assay22_p2005/  7/13/2022 (all GXD papers since 2005)
            - 8 FN->TP,
            - Precision 100   Recall 97.35
            - TP 19802.  FP 0.  TN 0. FN 538

        Age24Assay22/  7/28/2022 (regular testset)
            - Age: reorg of eday:
                generalized #'s, 1-2dig followed by optional .0 .5 .25 .75
                allow space or '-' between terms.
                allow ed|gd|d|day(s) # (w/ no specific following text)
                allow gestational|embryo day #
                allow # followed by various: e.g., day (old) mice|mouse|embryo, 
                    ED|GD|gestional day, day(s) after fertilization
                allow #.decimal followed by "day(s) old"|embryo(s)
                remove: allen brain|atlas|institute, time series
            - 26 FN->TP, but 2307 TN->FP <-- KILLED PRECISION
            - Precision 23.70   Recall 98.19
            - TP 1952.  FP 6283.  TN 8693. FN 36
        Age24Assay22_p2005/  7/28/2022 (all GXD papers since 2005)
            - 112 FN->TP,
            - Precision 100   Recall 97.91
            - TP 19914.  FP 0.  TN 0. FN 426

        Age25Assay22/  7/29/2022 (regular testset)
            - Age: after "d|day number", require (word) embryo(s)|of gestation
            - 20 TP->FN, but 2377 FP->TN <-- RESTORED PRECISION
            - Precision 33.09   Recall 97.18
            - TP 1932.  FP 3906.  TN 11070. FN 56
                        Improved P and R over Age23
        Age25Assay22_p2005/  7/29/2022 (all GXD papers since 2005)
            - Precision 100   Recall 97.49
            - TP 19829.  FP 0.  TN 0. FN 511

        Age26Assay22/  8/1/2022 (regular testset)
            - Age: ee: embryonic optional_word lysate(s)|extract(s)
                   eday: number days after|post fertilization|gestation
                            (added "post" and "gestation")
            - 1 FN->TP, but 28 TN->FP
            - Precision 32.95   Recall 97.23
            - TP 1933.  FP 3934.  TN 11042. FN 55
        Age26Assay22_p2005/  8/1/2022 (all GXD papers since 2005)
            - 3 FN->TP
            - Precision 100   Recall 97.50
            - TP 19832.  FP 0.  TN 0. FN 508

        Age27Assay22/  8/1/2022 (regular testset)
            - remove cat1Exclude: embryogenesis
            - Age: remove ageExcludes: bat gross eosin survival xenopus
                                        inject diabet
            - 116 TN->FP
            - Precision 32.31   Recall 97.23
            - TP 1933.  FP 4050.  TN 10926. FN 55
        Age27Assay22_p2005/  8/1/2022 (all GXD papers since 2005)
            - 30 FN->TP
            - Precision 100   Recall 97.65
            - TP 19862.  FP 0.  TN 0. FN 478

        Age28Assay22/  8/1/2022 (regular testset)
            - remove cat1Exclude: embryogenesis
            - Age: change exclude logic: check for exclude term in matchText
                    AND no exclude if matchText contains mice|mouse
            - 138 TN->FP        -- HURTS PRECISION compared to Age27
            - Precision 31.61   Recall 97.38
            - TP 1936.  FP 4188.  TN 10788. FN 52

        Age29Assay22/  8/1/2022 (regular testset)
            - remove cat1Exclude: embryogenesis
            - Age: change exclude logic: check for exclude term in matchText
                    REMOVE: no exclude if matchText contains mice|mouse
            - 1 FP->TN        -- compared to Age27
                    tiny, tiny help, but the logic makes sense.
                    Avoids several "5 day pig embryo" terms, etc.
            - Precision 32.31   Recall 97.23
            - TP 1933.  FP 4049.  TN 10927. FN 55
        Age29Assay22_p2005/  8/1/2022 (all GXD papers since 2005)
            - no change compared to Age27
            - Precision 100   Recall 97.65
            - TP 19862.  FP 0.  TN 0. FN 478

        Age29Assay23/  8/3/2022 (regular testset)
            - Cat2: add alexa flour, confocal, wish
            - 14 TN->FP         - only "confocal" contributed to new routings
            - Precision 32.24   Recall 97.23
            - TP 1933.  FP 4063.  TN 10913. FN 55
        Age29Assay23_p2005/  8/3/2022 (all GXD papers since 2005)
            - 5 FN->TP,   - 3 from "confocal", 2 from "wish"
            - Precision 100   Recall 97.67
            - TP 19867.  FP 0.  TN 0. FN 473

        Age29Assay24/  8/3/2022 (regular testset)
            - Cat2: add view terms
            - 2 FN->TP, 34 TN->FP
            - Precision 32.08   Recall 97.33
            - TP 1935.  FP 4097.  TN 10879. FN 53
        Age29Assay24_p2005/  8/3/2022 (all GXD papers since 2005)
            - 11 FN->TP,
            - Precision 100   Recall 97.73
            - TP 19878.  FP 0.  TN 0. FN 462

        Age29Assay25/  8/3/2022 (regular testset)
            - Cat2: add stain terms
            - 7 TN->FP
            - Precision 32.04   Recall 97.33
            - TP 1935.  FP 4104.  TN 10872. FN 53
        Age29Assay25_p2005/  8/4/2022 (all GXD papers since 2005)
            - 5 FN->TP,
            - Precision 100   Recall 97.75
            - TP 19883.  FP 0.  TN 0. FN 457

        Age29Assay26/  8/4/2022 (regular testset)
            - Cat2: add "expression at" terms
            - 1 FN->TP, 42 TN->FP
            - Precision 31.84   Recall 97.38
            - TP 1936.  FP 4145.  TN 10831. FN 52
        Age29Assay26_p2005/  8/4/2022 (all GXD papers since 2005)
            - 7 FN->TP,
            - Precision 100   Recall 97.79
            - TP 19890.  FP 0.  TN 0. FN 450

        NC1Age29Assay26/  8/4/2022 (regular testset)
            - Cat1: add "the expression of" as cat1 term <-------------
            - 29 TN->FP
            - Precision 31.69   Recall 97.38
            - TP 1936.  FP 4174.  TN 10802. FN 52
        NC1Age29Assay26_p2005/  8/4/2022 (all GXD papers since 2005)
            - 55 FN->TP,
            - Precision 100   Recall 98.06
            - TP 19945.  FP 0.  TN 0. FN 395

        NC1Age30Assay27/  8/10/2022 (regular testset)
            - cat2: fix alexa fluor
            - AgeExclude logic: support "# _" patterns, hamburger tweaks
            - no changes
            - Precision 31.69   Recall 97.38
            - TP 1936.  FP 4174.  TN 10802. FN 52
        NC1Age30Assay27_p2005/  8/10/2022 (all GXD papers since 2005)
            - no changes
            - Precision 100   Recall 98.06
            - TP 19945.  FP 0.  TN 0. FN 395

        NC1Age31Assay27/  8/10/2022 (regular testset)
            - AgeExclude logic: ';' no longer blocks age exclusion
            - 1 TP->FN,  21 FP->TN
            - Precision 31.78   Recall 97.33
            - TP 1935.  FP 4153.  TN 10823. FN 53
        NC1Age31Assay27_p2005/  8/10/2022 (all GXD papers since 2005)
            - 6 TP->FN
            - Precision 100   Recall 98.03
            - TP 19939.  FP 0.  TN 0. FN 401

        NC1Age32Assay27/  8/10/2022 (regular testset)
            - AgeExclude logic: no blocking: '; ', and '. ' before fig & et al
            - 7 FP->TN
            - Precision 31.82   Recall 97.33
            - TP 1935.  FP 4146.  TN 10830. FN 53
        NC1Age32Assay27_p2005/  8/10/2022 (all GXD papers since 2005)
            - no change
            - Precision 100   Recall 98.03
            - TP 19939.  FP 0.  TN 0. FN 401

        NC1Age32Assay28/  8/15/2022 (regular testset)
            - Cat2 tweaks: remove low hit terms, add wmish
            - 14 FP->TN
            - Precision 31.89   Recall 97.33
            - TP 1935.  FP 4132.  TN 10844. FN 53
        NC1Age32Assay28_p2005/  8/15/2022 (all GXD papers since 2005)
            - no change
            - Precision 100   Recall 98.03
            - TP 19939.  FP 0.  TN 0. FN 401

--- route3/ Starting New results directory-------------------------------------

        NC1Age32Assay28/  8/24/2022 (combined regular+p2005 testset)
            - Baseline with the new combined testset
            - Precision 82.84   Recall 98.02   NPV 96.41
            -    TP      FP      TN      FN
            - 19950,   4132,  10844,    404

        NC1Age33Assay28/  8/24/2022 (combined regular+p2005 testset)
            - Age tweaks: allow '; ' to block ageExclusions again.
            - 22 TN->FP,  6 FN->TP
            - Precision 82.77   Recall 98.04   NPV 96.45
            -    TP      FP      TN      FN
            - 19956,   4154,  10822,    398

        NC1Age34Assay28/  8/25/2022 (combined regular+p2005 testset)
            - Age eday tweaks: require "embryo_term" after "# day old mice",
                               omit "0" as an eday number,
                               "e# ml" not an age (before, required '-')
            - 45 FP->TN,  4 TP->FN
            - Precision 82.92   Recall 98.02   NPV 96.43
            -    TP      FP      TN      FN
            - 19952,   4109,  10867,    402

        NC1Age35Assay28/  8/26/2022 (combined regular+p2005 testset)
            - Age tweaks: eday: remove weird special case.
                          Remove 'cat' from ageExclude terms
            - 1 TP->FN, 2 FN->TP
            - Precision 82.92   Recall 98.03   NPV 96.44
            -    TP      FP      TN      FN
            - 19953,   4109,  10867,    401

        NC1Age35Assay29/  8/26/2022 (combined regular+p2005 testset)
            - cat2 and cat1 exclude term additions 
            - 14 FP->TN
            - Precision 82.97   Recall 98.03   NPV 96.45
            -    TP      FP      TN      FN
            - 19953,   4095,  10881,    401

        NC1Age36Assay29/  9/13/2022 (combined regular+p2005 testset)
            - Splitting out ageExclude organism terms.
                Same blocking chars: paragraph, '. ', '; '
            - Precision 82.89   Recall 98.09   NPV 96.54
            -    TP      FP      TN      FN
            - 19965,   4121,  10855,    389
            TestSet3:
            - Precision 32.00   Recall 97.54   NPV 99.55
            -    TP      FP      TN      FN
            -   1939,   4121,  10855,     49

        NC1Age37Assay29/  9/13/2022 (combined regular+p2005 testset)
            - Splitting out ageExclude organism terms.
                Omit '; ' from blocking
            - Precision 82.94   Recall 98.06   NPV 96.50
            -    TP      FP      TN      FN
            - 19960,   4105,  10871,    394
            TestSet3:
            - Precision 32.07   Recall 97.48   NPV 99.54
            -    TP      FP      TN      FN
            -  1938,   4105,  10871,     50
