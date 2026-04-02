---
type: inventory
subtype: jcl-jobs
status: draft
confidence: high
last_pass: 5
---

# JCL Job Inventory

Catalog of all JCL jobs found in the source directory.

## Jobs

| Job Name | Source File | Steps | Programs Executed | Purpose |
| ---------- | ------------- | ----- | ----------------- | --------------- |
| ACCTFILE | ACCTFILE.jcl | 3 | IDCAMS | Delete and redefine account data VSAM KSDS cluster |
| CARDFILE | CARDFILE.jcl | 7 | SDSF, IDCAMS | Close CICS files, delete and redefine card data VSAM KSDS with AIX |
| CBADMCDJ | CBADMCDJ.jcl | 1 | DFHCSDUP | Define CICS resources (programs, transactions, mapsets) for CardDemo application |
| CBEXPORT | CBEXPORT.jcl | 2 | IDCAMS, CBEXPORT | Define export VSAM cluster then run CBEXPORT to create multi-record migration export file |
| CBIMPORT | CBIMPORT.jcl | 1 | CBIMPORT | Import multi-record export file and split into normalised sequential output files |
| CLOSEFIL | CLOSEFIL.jcl | 1 | SDSF | Close CICS files (SDSF SET command) |
| COMBTRAN | COMBTRAN.jcl | 2 | SORT, IDCAMS | Sort and merge daily and system-generated transactions, then load combined file into TRANSACT VSAM |
| CREASTMT | CREASTMT.JCL | 4 | IDCAMS, SORT, IDCAMS, CBSTM03A | Prepare transaction VSAM sorted by card/tran key, then generate account statements in plain text and HTML format |
| CUSTFILE | CUSTFILE.jcl | 4 | SDSF, IDCAMS | Close CICS files, delete and redefine customer data VSAM KSDS |
| DALYREJS | DALYREJS.jcl | 1 | IDCAMS | Define GDG base for daily rejected transactions dataset |
| DEFCUST | DEFCUST.jcl | 2 | IDCAMS | Define customer VSAM KSDS cluster (two-step: delete then define) |
| DEFGDGB | DEFGDGB.jcl | 1 | IDCAMS | Define GDG bases for various CardDemo datasets |
| DEFGDGD | DEFGDGD.jcl | 6 | IDCAMS, IEBGENER | Define GDG datasets and populate with seed data |
| DISCGRP | DISCGRP.jcl | 3 | IDCAMS | Delete and redefine disclosure group VSAM KSDS |
| DUSRSECJ | DUSRSECJ.jcl | 3 | IEFBR14, IEBGENER, IDCAMS | Define user security (USRSEC) VSAM KSDS and load seed data |
| ESDSRRDS | ESDSRRDS.jcl | 5 | IEFBR14, IEBGENER, IDCAMS | Define ESDS and RRDS VSAM files for various uses |
| FTPJCLS | FTPJCL.JCL | 1 | FTP | FTP utility job; sends a CardDemo file to a remote server via ASCII FTP |
| INTCALC | INTCALC.jcl | 1 | CBACT04C | Run interest and fees calculation against transaction category balance file |
| INTRDRJ1 | INTRDRJ1.JCL | 2 | IDCAMS, IEBGENER | Copy FTP test dataset and submit INTRDRJ2 job via internal reader |
| INTRDRJ2 | INTRDRJ2.JCL | 1 | IDCAMS | Copy FTP backup dataset; second stage of internal reader chain |
| OPENFIL | OPENFIL.jcl | 1 | SDSF | Open CICS files (SDSF SET command) |
| POSTTRAN | POSTTRAN.jcl | 1 | CBTRN02C | Post daily transaction file; update transaction category balance and transaction master VSAM |
| PRTCATBL | PRTCATBL.jcl | 2 | IEFBR14, SORT | Pre-delete output and sort/print transaction category balance file |
| READACCT | READACCT.jcl | 2 | IEFBR14, CBACT01C | Pre-delete outputs then read account VSAM and write to PS, array, and VB output files |
| READCARD | READCARD.jcl | 1 | CBACT02C | Read card data VSAM file and print records |
| READCUST | READCUST.jcl | 1 | CBCUS01C | Read customer data VSAM file and print records |
| READXREF | READXREF.jcl | 1 | CBACT03C | Read card cross-reference VSAM file and print records |
| REPTFILE | REPTFILE.jcl | 1 | IDCAMS | Define GDG base for transaction report output file |
| TCATBALF | TCATBALF.jcl | 3 | IDCAMS | Delete and redefine transaction category balance VSAM KSDS |
| TRANBKP | TRANBKP.jcl | 2 | IDCAMS | Unload (REPRO) and optionally delete transaction master VSAM for backup |
| TRANCATG | TRANCATG.jcl | 3 | IDCAMS | Delete and redefine transaction category code VSAM KSDS and load seed data |
| TRANFILE | TRANFILE.jcl | 7 | SDSF, IDCAMS | Close CICS files, delete and redefine transaction master VSAM KSDS with AIX |
| TRANIDX | TRANIDX.jcl | 3 | IDCAMS | Define alternate index and path on transaction master VSAM |
| TRANREPT | TRANREPT.jcl | 3 | REPROC (proc), SORT, CBTRN03C | Unload transaction VSAM, filter and sort by date range, produce formatted transaction report |
| TRANTYPE | TRANTYPE.jcl | 3 | IDCAMS | Delete and redefine transaction type code VSAM KSDS and load seed data |
| TXT2PDF1 | TXT2PDF1.JCL | 1 | IKJEFT1B | Convert plain text account statement file (STATEMNT.PS) to PDF using TXT2PDF REXX exec |
| WAITSTEP | WAITSTEP.jcl | 1 | COBSWAIT | Execute wait utility; pauses job stream for a configurable number of centiseconds |
| XREFFILE | XREFFILE.jcl | 6 | IDCAMS | Delete and redefine card cross-reference VSAM KSDS with AIX and path |

## Procedures (proc/)

| Proc Name | Source File | Steps | Purpose |
| ---------- | ------------- | ----- | ------- |
| REPROC | REPROC.prc | 1 | Parameterised IDCAMS REPRO utility proc; used to load or unload a VSAM file; called by TRANREPT.prc |
| TRANREPT | TRANREPT.prc | 3 | Full transaction report proc: invokes REPROC to unload TRANSACT VSAM, SORT to filter by date range, CBTRN03C to produce formatted report |

## Job Steps

| Job Name | Step Name | Program | DD Statements | Condition |
| ---------- | ----------- | ----------- | -------------------- | ---------------- |
| READACCT | PREDEL | IEFBR14 | DD01 (ACCTDATA.PSCOMP DELETE), DD02 (ACCTDATA.ARRYPS DELETE), DD03 (ACCTDATA.VBPS DELETE) | (none) |
| READACCT | STEP05 | CBACT01C | ACCTFILE, OUTFILE, ARRYFILE, VBRCFILE, SYSOUT, SYSPRINT | (none) |
| READCARD | STEP05 | CBACT02C | CARDFILE, SYSOUT, SYSPRINT | (none) |
| READCUST | STEP05 | CBCUS01C | CUSTFILE, SYSOUT, SYSPRINT | (none) |
| READXREF | STEP05 | CBACT03C | XREFFILE, SYSOUT, SYSPRINT | (none) |
| POSTTRAN | STEP15 | CBTRN02C | TRANFILE, DALYTRAN, XREFFILE, DALYREJS, ACCTFILE, TCATBALF, SYSPRINT, SYSOUT | (none) |
| INTCALC | STEP15 | CBACT04C | TCATBALF, XREFFILE, XREFFIL1, ACCTFILE, DISCGRP, TRANSACT, SYSPRINT, SYSOUT | PARM='2022071800' |
| CREASTMT | DELDEF01 | IDCAMS | SYSPRINT, SYSIN (DELETE/DEFINE TRXFL.VSAM.KSDS) | (none) |
| CREASTMT | STEP010 | SORT | SORTIN (TRANSACT.VSAM.KSDS), SORTOUT (TRXFL.SEQ), SYSIN (SORT+OUTREC) | (none) |
| CREASTMT | STEP020 | IDCAMS | INFILE (TRXFL.SEQ), OUTFILE (TRXFL.VSAM.KSDS), SYSIN (REPRO) | COND=(0,NE) |
| CREASTMT | STEP030 | IEFBR14 | HTMLFILE (DELETE), STMTFILE (DELETE) | COND=(0,NE) |
| CREASTMT | STEP040 | CBSTM03A | TRNXFILE, XREFFILE, ACCTFILE, CUSTFILE, STMTFILE, HTMLFILE, STEPLIB, SYSPRINT, SYSOUT | COND=(0,NE) |
| TRANREPT | STEP05R | REPROC (proc) | FILEIN (TRANSACT.VSAM.KSDS), FILEOUT (TRANSACT.BKUP) | (none) |
| TRANREPT | STEP05R | SORT | SORTIN (TRANSACT.BKUP), SORTOUT (TRANSACT.DALY), SYMNAMES, SYSIN | (none) |
| TRANREPT | STEP10R | CBTRN03C | TRANFILE, CARDXREF, TRANTYPE, TRANCATG, DATEPARM, TRANREPT, SYSOUT, SYSPRINT | (none) |
| COMBTRAN | STEP05R | SORT | SORTIN (TRANSACT.BKUP, SYSTRAN), SORTOUT (TRANSACT.COMBINED), SYMNAMES, SYSIN | (none) |
| COMBTRAN | STEP10 | IDCAMS | TRANSACT, TRANVSAM, SYSIN (REPRO), SYSPRINT | (none) |
| CBEXPORT | STEP01 | IDCAMS | SYSIN (DEFINE CLUSTER for EXPORT.DATA), SYSPRINT | (none) |
| CBEXPORT | STEP02 | CBEXPORT | CUSTFILE, ACCTFILE, XREFFILE, TRANSACT, CARDFILE, EXPFILE, SYSOUT, SYSPRINT | (none) |
| CBIMPORT | STEP01 | CBIMPORT | EXPFILE, CUSTOUT, ACCTOUT, XREFOUT, TRNXOUT, ERROUT, SYSOUT, SYSPRINT | (none) |
| WAITSTEP | WAIT | COBSWAIT | SYSIN (parm value in centiseconds), SYSOUT, SYSPRINT | (none) |
| CBADMCDJ | STEP1 | DFHCSDUP | DFHCSD, OUTDD, SYSPRINT, SYSIN (CSD definitions) | PARM='CSD(READWRITE)...' |
| TRANBKP | STEP05 | IDCAMS | TRANSACT (VSAM input), TRANBACK (PS output), SYSIN (REPRO), SYSPRINT | (none) |
| TRANBKP | STEP10 | IDCAMS | SYSIN (DELETE cluster), SYSPRINT | COND=(4,LT) |
| FTPJCLS | STEP1 | FTP | SYSIN (server IP, credentials, PUT command) | (none) |
| INTRDRJ1 | IDCAMS | IDCAMS | IN (FTP.TEST), OUT (FTP.TEST.BKUP), SYSIN (REPRO) | (none) |
| INTRDRJ1 | STEP01 | IEBGENER | SYSUT1 (INTRDRJ2 member), SYSUT2 (INTRDR), SYSIN DUMMY | (none) |
| INTRDRJ2 | IDCAMS | IDCAMS | IN (FTP.TEST.BKUP), OUT (FTP.TEST.BKUP.INTRDR), SYSIN (REPRO) | (none) |
| TXT2PDF1 | TXT2PDF | IKJEFT1B | STEPLIB (TXT2PDF.LOAD), SYSEXEC (TXT2PDF.EXEC), INDD (STATEMNT.PS), SYSPRINT, SYSTSPRT, SYSTSIN | COND=(0,NE) |

## DD Assignments

| Job Name | Step Name | DD Name | Dataset / File | Disposition |
| ---------- | ----------- | ---------- | ----------------------- | --------------- |
| READACCT | STEP05 | ACCTFILE | AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS | SHR |
| READACCT | STEP05 | OUTFILE | AWS.M2.CARDDEMO.ACCTDATA.PSCOMP | NEW,CATLG,DELETE |
| READACCT | STEP05 | ARRYFILE | AWS.M2.CARDDEMO.ACCTDATA.ARRYPS | NEW,CATLG,DELETE |
| READACCT | STEP05 | VBRCFILE | AWS.M2.CARDDEMO.ACCTDATA.VBPS | NEW,CATLG,DELETE |
| READCARD | STEP05 | CARDFILE | AWS.M2.CARDDEMO.CARDDATA.VSAM.KSDS | SHR |
| READCUST | STEP05 | CUSTFILE | AWS.M2.CARDDEMO.CUSTDATA.VSAM.KSDS | SHR |
| READXREF | STEP05 | XREFFILE | AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS | SHR |
| POSTTRAN | STEP15 | TRANFILE | AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS | SHR |
| POSTTRAN | STEP15 | DALYTRAN | AWS.M2.CARDDEMO.DALYTRAN.PS | SHR |
| POSTTRAN | STEP15 | XREFFILE | AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS | SHR |
| POSTTRAN | STEP15 | DALYREJS | AWS.M2.CARDDEMO.DALYREJS(+1) | NEW,CATLG,DELETE |
| POSTTRAN | STEP15 | ACCTFILE | AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS | SHR |
| POSTTRAN | STEP15 | TCATBALF | AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS | SHR |
| INTCALC | STEP15 | TCATBALF | AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS | SHR |
| INTCALC | STEP15 | XREFFILE | AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS | SHR |
| INTCALC | STEP15 | XREFFIL1 | AWS.M2.CARDDEMO.CARDXREF.VSAM.AIX.PATH | SHR |
| INTCALC | STEP15 | ACCTFILE | AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS | SHR |
| INTCALC | STEP15 | DISCGRP | AWS.M2.CARDDEMO.DISCGRP.VSAM.KSDS | SHR |
| INTCALC | STEP15 | TRANSACT | AWS.M2.CARDDEMO.SYSTRAN(+1) | NEW,CATLG,DELETE |
| CREASTMT | STEP040 | TRNXFILE | AWS.M2.CARDDEMO.TRXFL.VSAM.KSDS | SHR |
| CREASTMT | STEP040 | XREFFILE | AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS | SHR |
| CREASTMT | STEP040 | ACCTFILE | AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS | SHR |
| CREASTMT | STEP040 | CUSTFILE | AWS.M2.CARDDEMO.CUSTDATA.VSAM.KSDS | SHR |
| CREASTMT | STEP040 | STMTFILE | AWS.M2.CARDDEMO.STATEMNT.PS | NEW,CATLG,DELETE |
| CREASTMT | STEP040 | HTMLFILE | AWS.M2.CARDDEMO.STATEMNT.HTML | NEW,CATLG,DELETE |
| TRANREPT | STEP10R | TRANFILE | AWS.M2.CARDDEMO.TRANSACT.DALY(+1) | SHR |
| TRANREPT | STEP10R | CARDXREF | AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS | SHR |
| TRANREPT | STEP10R | TRANTYPE | AWS.M2.CARDDEMO.TRANTYPE.VSAM.KSDS | SHR |
| TRANREPT | STEP10R | TRANCATG | AWS.M2.CARDDEMO.TRANCATG.VSAM.KSDS | SHR |
| TRANREPT | STEP10R | DATEPARM | AWS.M2.CARDDEMO.DATEPARM | SHR |
| TRANREPT | STEP10R | TRANREPT | AWS.M2.CARDDEMO.TRANREPT(+1) | NEW,CATLG,DELETE |
| CBEXPORT | STEP02 | CUSTFILE | AWS.M2.CARDDEMO.CUSTDATA.VSAM.KSDS | SHR |
| CBEXPORT | STEP02 | ACCTFILE | AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS | SHR |
| CBEXPORT | STEP02 | XREFFILE | AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS | SHR |
| CBEXPORT | STEP02 | TRANSACT | AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS | SHR |
| CBEXPORT | STEP02 | CARDFILE | AWS.M2.CARDDEMO.CARDDATA.VSAM.KSDS | SHR |
| CBEXPORT | STEP02 | EXPFILE | AWS.M2.CARDDEMO.EXPORT.DATA | SHR |
| CBIMPORT | STEP01 | EXPFILE | AWS.M2.CARDDEMO.EXPORT.DATA | SHR |
| CBIMPORT | STEP01 | CUSTOUT | AWS.M2.CARDDEMO.CUSTDATA.IMPORT | NEW,CATLG,DELETE |
| CBIMPORT | STEP01 | ACCTOUT | AWS.M2.CARDDEMO.ACCTDATA.IMPORT | NEW,CATLG,DELETE |
| CBIMPORT | STEP01 | XREFOUT | AWS.M2.CARDDEMO.CARDXREF.IMPORT | NEW,CATLG,DELETE |
| CBIMPORT | STEP01 | TRNXOUT | AWS.M2.CARDDEMO.TRANSACT.IMPORT | NEW,CATLG,DELETE |
| CBIMPORT | STEP01 | ERROUT | AWS.M2.CARDDEMO.IMPORT.ERRORS | NEW,CATLG,DELETE |
| TXT2PDF1 | TXT2PDF | INDD | AWS.M2.CARDDEMO.STATEMNT.PS | SHR |

## CSD-Defined CICS Resources

CICS file, TDQ, and library definitions from CARDDEMO.CSD (applied by CBADMCDJ):

| Resource Type | Resource Name | Dataset / Details |
| ------------- | ------------- | ----------------- |
| FILE | ACCTDAT | AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS |
| FILE | CARDAIX | AWS.M2.CARDDEMO.CARDDATA.VSAM.AIX.PATH |
| FILE | CARDDAT | AWS.M2.CARDDEMO.CARDDATA.VSAM.KSDS |
| FILE | CCXREF | AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS |
| FILE | CUSTDAT | AWS.M2.CARDDEMO.CUSTDATA.VSAM.KSDS |
| FILE | CXACAIX | AWS.M2.CARDDEMO.CARDXREF.VSAM.AIX.PATH |
| FILE | TRANSACT | AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS |
| FILE | USRSEC | AWS.M2.CARDDEMO.USRSEC.VSAM.KSDS |
| TDQUEUE | JOBS | Extra-partition output TDQ; DDNAME=INREADER; used by CORPT00C to submit batch jobs |
| LIBRARY | CARDDLIB | AWS.M2.CARDDEMO.LOADLIB (enabled) |
| LIBRARY | COM2DOLL | AWS.M2.CARDDEMO.LOADLIB (disabled) |

## Unresolved Programs

Programs referenced in EXEC PGM= but not found in the program inventory:

| Program | Referenced In |
| -------------- | ----------------- |
| IDCAMS | Multiple setup/utility jobs (VSAM cluster management) -- system utility, not a COBOL program |
| IEFBR14 | READACCT.PREDEL, PRTCATBL.DELDEF, ESDSRRDS.PREDEL, DUSRSECJ.PREDEL, CREASTMT.STEP030 -- system no-op utility |
| IEBGENER | DEFGDGD, ESDSRRDS, DUSRSECJ, INTRDRJ1.STEP01 -- system data copy utility |
| SORT | COMBTRAN, PRTCATBL, TRANREPT, CREASTMT.STEP010 -- system sort utility |
| SDSF | CUSTFILE, TRANFILE, CARDFILE, OPENFIL, CLOSEFIL -- CICS file open/close via SDSF |
| DFHCSDUP | CBADMCDJ -- CICS system definition utility |
| FTP | FTPJCLS.STEP1 -- TCP/IP FTP client utility |
| IKJEFT1B | TXT2PDF1.TXT2PDF -- TSO/E batch terminal; used to run TXT2PDF REXX exec |
| REPROC | TRANREPT (called via proc REPROC) -- procedure, not a stand-alone program |
