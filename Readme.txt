Analysis and prototyping GXD secondary Triage - what files are where

See https://mgi-jira.atlassian.net/browse/WTS2-848

All the spreadsheets w/ data & analysis are in this google drive folder:
https://drive.google.com/drive/folders/1CriRWMvOUKvfXjw7xlp0M345GDvd7V2G

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
