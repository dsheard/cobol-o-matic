---
type: integration
subtype: interfaces
status: draft
confidence: high
last_pass: 5
---

# External Interfaces

All external system touchpoints identified in the CardDemo COBOL source.

## Interface Summary

| Interface | Type | Direction | Used By Programs | Description |
| --------- | ---- | --------- | ---------------- | ----------- |
| AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS | File | BOTH | CBACT01C, CBACT04C, CBTRN01C, CBTRN02C, CBSTM03B, COACTVWC, COACTUPC, COBIL00C, COPAUA0C | Account master VSAM KSDS |
| AWS.M2.CARDDEMO.CARDDATA.VSAM.KSDS | File | BOTH | CBACT02C, CBTRN01C, CBEXPORT, COCRDLIC, COCRDSLC, COCRDUPC | Credit card master VSAM KSDS |
| AWS.M2.CARDDEMO.CUSTDATA.VSAM.KSDS | File | BOTH | CBCUS01C, CBTRN01C, CBSTM03B, COACTVWC, COACTUPC, COPAUA0C | Customer master VSAM KSDS |
| AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS | File | IN | CBACT03C, CBACT04C, CBTRN01C, CBTRN02C, CBTRN03C, CBSTM03B, CBEXPORT, COBIL00C, COTRN02C, COACTVWC, COACTUPC, COPAUA0C | Card-to-account cross-reference VSAM KSDS |
| AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS | File | BOTH | CBACT04C, CBTRN01C, CBTRN02C, CBEXPORT, COBIL00C, COTRN00C, COTRN01C, COTRN02C | Transaction master VSAM KSDS |
| AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS | File | BOTH | CBACT04C, CBTRN02C | Transaction category balance VSAM KSDS |
| AWS.M2.CARDDEMO.DISCGRP.VSAM.KSDS | File | IN | CBACT04C | Discount group VSAM KSDS |
| AWS.M2.CARDDEMO.TRANTYPE.VSAM.KSDS | File | IN | CBTRN03C | Transaction type lookup VSAM KSDS |
| AWS.M2.CARDDEMO.TRANCATG.VSAM.KSDS | File | IN | CBTRN03C | Transaction category lookup VSAM KSDS |
| AWS.M2.CARDDEMO.USRSEC.VSAM.KSDS | File | BOTH | COSGN00C, COUSR00C, COUSR01C, COUSR02C, COUSR03C | User security VSAM KSDS (CICS DDNAME USRSEC) |
| AWS.M2.CARDDEMO.TRXFL.VSAM.KSDS | File | IN | CBSTM03B (via CBSTM03A) | Transaction file re-keyed by card+tran ID; created by SORT step in CREASTMT.JCL; read by CBSTM03B for statement generation |
| AWS.M2.CARDDEMO.DALYTRAN.PS | File | IN | CBTRN01C, CBTRN02C | Daily transaction input sequential file |
| AWS.M2.CARDDEMO.DALYREJS (GDG) | File | OUT | CBTRN02C | Daily rejected transactions GDG |
| AWS.M2.CARDDEMO.TRANREPT (GDG) | File | OUT | CBTRN03C | Transaction report GDG |
| AWS.M2.CARDDEMO.DATEPARM | File | IN | CBTRN03C | Date parameter file |
| AWS.M2.CARDDEMO.TRANSACT.DALY (GDG) | File | IN | CBTRN03C | Filtered/sorted daily transactions GDG; produced by SORT step in TRANREPT.jcl |
| AWS.M2.CARDDEMO.EXPORT.DATA | File | BOTH | CBEXPORT, CBIMPORT | Multi-record export VSAM for migration |
| AWS.M2.CARDDEMO.ACCTDATA.PSCOMP | File | OUT | CBACT01C | Account data compressed output |
| AWS.M2.CARDDEMO.ACCTDATA.ARRYPS | File | OUT | CBACT01C | Account array format output |
| AWS.M2.CARDDEMO.ACCTDATA.VBPS | File | OUT | CBACT01C | Account variable-block output |
| AWS.M2.CARDDEMO.CUSTDATA.IMPORT | File | OUT | CBIMPORT | Customer import output (normalised) |
| AWS.M2.CARDDEMO.ACCTDATA.IMPORT | File | OUT | CBIMPORT | Account import output (normalised) |
| AWS.M2.CARDDEMO.CARDXREF.IMPORT | File | OUT | CBIMPORT | Card xref import output (normalised) |
| AWS.M2.CARDDEMO.TRANSACT.IMPORT | File | OUT | CBIMPORT | Transaction import output (normalised) |
| AWS.M2.CARDDEMO.IMPORT.ERRORS | File | OUT | CBIMPORT | Import error report |
| AWS.M2.CARDDEMO.SYSTRAN (GDG) | File | OUT | CBACT04C | System-generated transactions GDG |
| AWS.M2.CARDDEMO.TRANSACT.BKUP (GDG) | File | BOTH | TRANREPT/COMBTRAN JCL | Transaction backup GDG (SORT utility) |
| AWS.M2.CARDDEMO.TRANSACT.COMBINED | File | BOTH | COMBTRAN JCL | Combined sorted transactions |
| AWS.M2.CARDDEMO.STATEMNT.PS | File | OUT | CBSTM03A | Customer statement plain-text output; DD name STMTFILE in CREASTMT.JCL step STEP040 |
| AWS.M2.CARDDEMO.STATEMNT.HTML | File | OUT | CBSTM03A | Customer statement HTML output; DD name HTMLFILE in CREASTMT.JCL step STEP040 |
| AWS.M2.CARDDEMO.TRXFL.SEQ | File | BOTH | CREASTMT JCL (SORT step) | Intermediate sequential sort work file; created then loaded into TRXFL.VSAM.KSDS by CREASTMT STEP010/STEP020 |
| CARDOUT (no JCL DD in CBIMPORT.jcl) | File | OUT | CBIMPORT | Card import output — SELECT CARD-OUTPUT ASSIGN TO CARDOUT in CBIMPORT.cbl; no corresponding DD in CBIMPORT.jcl; possible JCL omission |
| ACCTDAT | File (CICS) | BOTH | COBIL00C, COACTVWC, COACTUPC, COPAUA0C | Account data file accessed via CICS; DSNAME AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS (CSD) |
| CARDDAT | File (CICS) | BOTH | COCRDSLC, COCRDUPC, COACTVWC | Card data file accessed via CICS; DSNAME AWS.M2.CARDDEMO.CARDDATA.VSAM.KSDS (CSD) |
| CUSTDAT | File (CICS) | BOTH | COACTVWC, COACTUPC, COPAUA0C | Customer data file accessed via CICS; DSNAME AWS.M2.CARDDEMO.CUSTDATA.VSAM.KSDS (CSD) |
| CXACAIX | File (CICS) | IN | COBIL00C, COTRN02C, COACTVWC, COACTUPC | Card-xref alternate index path (CICS); DSNAME AWS.M2.CARDDEMO.CARDXREF.VSAM.AIX.PATH (CSD) |
| CARDAIX | File (CICS) | IN | COCRDSLC | Card file alternate index by account (CICS); DSNAME AWS.M2.CARDDEMO.CARDDATA.VSAM.AIX.PATH (CSD) |
| CCXREF | File (CICS) | IN | COTRN02C, COPAUA0C | Card xref file (CICS, direct access); DSNAME AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS (CSD) |
| TRANSACT (CICS) | File (CICS) | BOTH | COBIL00C, COTRN00C, COTRN01C, COTRN02C | Transaction VSAM accessed via CICS; DSNAME AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS (CSD) |
| USRSEC (CICS) | File (CICS) | BOTH | COSGN00C, COUSR00C, COUSR01C, COUSR02C, COUSR03C | User security VSAM via CICS; DSNAME AWS.M2.CARDDEMO.USRSEC.VSAM.KSDS (CSD) |
| JOBS (CICS TD Queue) | Messaging | OUT | CORPT00C | Extra-partition TD queue (DDNAME INREADER — JES internal reader) used to trigger batch report job |
| CARD.DEMO.REPLY.ACCT (MQ Queue) | Messaging | OUT | COACCT01 | MQ reply queue for account data responses (app-vsam-mq variant) |
| CARD.DEMO.REPLY.DATE (MQ Queue) | Messaging | OUT | CODATE01 | MQ reply queue for date service responses (app-vsam-mq variant) |
| CARD.DEMO.ERROR (MQ Queue) | Messaging | OUT | COACCT01, CODATE01 | MQ error queue for both vsam-mq variant programs |
| Dynamic MQ request queue | Messaging | IN | COPAUA0C, COACCT01, CODATE01 | Input MQ queue name received via EXEC CICS RETRIEVE (trigger) |
| Dynamic MQ reply queue | Messaging | OUT | COPAUA0C | Reply queue name from MQMD-REPLYTOQ; MQPUT1 used to send auth response |
| CARDDEMO.TRANSACTION_TYPE (DB2) | DB2 | BOTH | COTRTLIC, COTRTUPC, COBTUPDT | DB2 table: transaction type codes and descriptions |
| IMS PSBPAUTB / PAUTSUM0 (IMS/DL/I) | IMS/DB | BOTH | COPAUA0C, COPAUS1C, CBPAUP0C | IMS pending authorization summary root segment |
| IMS PSBPAUTB / PAUTDTL1 (IMS/DL/I) | IMS/DB | BOTH | COPAUA0C, CBPAUP0C | IMS pending authorization detail child segment |
| COSGN00 / COSGN0A | CICS Screen | BOTH | COSGN00C | Login screen (BMS mapset COSGN00, map COSGN0A) |
| COADM01 / COADM1A | CICS Screen | BOTH | COADM01C | Admin menu screen |
| COMEN01 / COMEN1A | CICS Screen | BOTH | COMEN01C | Main menu screen |
| COACTVW / CACTVWA | CICS Screen | BOTH | COACTVWC | Account view screen |
| COACTUP / CACTUPA | CICS Screen | BOTH | COACTUPC | Account update screen |
| COBIL00 / COBIL0A | CICS Screen | BOTH | COBIL00C | Bill payment screen |
| COCRDLI / CCRDLIA | CICS Screen | BOTH | COCRDLIC | Credit card list screen |
| COCRDSL / CCRDSLA | CICS Screen | BOTH | COCRDSLC | Credit card detail select screen |
| COCRDUP / CCRDUPA | CICS Screen | BOTH | COCRDUPC | Credit card update screen |
| CORPT00 / CORPT0A | CICS Screen | BOTH | CORPT00C | Report request screen |
| COTRN00 / COTRN0A | CICS Screen | BOTH | COTRN00C | Transaction list screen |
| COTRN01 / COTRN1A | CICS Screen | BOTH | COTRN01C | Transaction detail screen |
| COTRN02 / COTRN2A | CICS Screen | BOTH | COTRN02C | Transaction add screen |
| COUSR00 / COUSR0A | CICS Screen | BOTH | COUSR00C | User list screen |
| COUSR01 / COUSR1A | CICS Screen | BOTH | COUSR01C | User add screen |
| COUSR02 / COUSR2A | CICS Screen | BOTH | COUSR02C | User update screen |
| COUSR03 / COUSR3A | CICS Screen | BOTH | COUSR03C | User delete screen |
| CEE3ABD | External Call | OUT | CBACT01C, CBACT02C, CBACT03C, CBACT04C, CBCUS01C, CBEXPORT, CBIMPORT, CBTRN01C, CBTRN02C, CBTRN03C, CBSTM03A | LE/370 abnormal termination handler |
| MVSWAIT | External Call | OUT | COBSWAIT | MVS wait service |
| COBDATFT | External Call | OUT | CBACT01C | Date/time formatting utility; CALL 'COBDATFT' USING CODATECN-REC; source not in inventory |
| CSUTLDTC | Internal Call | BOTH | CORPT00C, COTRN02C | Internal date utility subprogram |


## File Interfaces

| DD Name / Path | Organisation | Record Layout | Read By | Written By | Description |
| -------------- | ------------ | ------------- | ------- | ---------- | ----------- |
| ACCTFILE / AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS | VSAM KSDS | CVACT01Y | CBACT01C, CBACT04C, CBTRN01C, CBTRN02C, CBSTM03B | CBACT04C, CBTRN02C | Account master |
| CARDFILE / AWS.M2.CARDDEMO.CARDDATA.VSAM.KSDS | VSAM KSDS | CVACT02Y | CBACT02C, CBTRN01C, CBEXPORT | — | Credit card master (batch read) |
| CUSTFILE / AWS.M2.CARDDEMO.CUSTDATA.VSAM.KSDS | VSAM KSDS | CVCUS01Y | CBCUS01C, CBTRN01C, CBSTM03B | — | Customer master |
| XREFFILE / AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS | VSAM KSDS | CVACT03Y | CBACT03C, CBACT04C, CBTRN01C, CBTRN02C, CBSTM03B, CBEXPORT | — | Card-to-account cross-reference (batch) |
| CARDXREF DD / AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS | VSAM KSDS | CVACT03Y | CBTRN03C | — | Card-to-account cross-reference (TRANREPT.jcl DD name CARDXREF) |
| TRANFILE / AWS.M2.CARDDEMO.TRANSACT.DALY (GDG) | Sequential GDG | CVTRA05Y | CBTRN03C | — | Filtered daily transactions input to CBTRN03C (produced by SORT step in TRANREPT.jcl) |
| TRANFILE / AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS | VSAM KSDS | CVTRA05Y | CBTRN01C, CBTRN02C, CBEXPORT | CBTRN02C | Transaction VSAM (batch read/write programs other than CBTRN03C) |
| TCATBALF / AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS | VSAM KSDS | CVTRA01Y | CBACT04C, CBTRN02C | CBTRN02C | Transaction category balance |
| DISCGRP / AWS.M2.CARDDEMO.DISCGRP.VSAM.KSDS | VSAM KSDS | — | CBACT04C | — | Discount/interest group rates |
| TRANTYPE / AWS.M2.CARDDEMO.TRANTYPE.VSAM.KSDS | VSAM KSDS | CVTRA03Y | CBTRN03C | — | Transaction type descriptions |
| TRANCATG / AWS.M2.CARDDEMO.TRANCATG.VSAM.KSDS | VSAM KSDS | CVTRA04Y | CBTRN03C | — | Transaction category descriptions |
| DALYTRAN / AWS.M2.CARDDEMO.DALYTRAN.PS | Sequential PS | CVTRA06Y | CBTRN01C, CBTRN02C | — | Daily transaction input feed |
| DALYREJS / AWS.M2.CARDDEMO.DALYREJS (GDG) | Sequential GDG | CVTRA05Y | — | CBTRN02C | Rejected daily transactions |
| DATEPARM / AWS.M2.CARDDEMO.DATEPARM | Sequential PS | — | CBTRN03C | — | Date parameter file for report |
| TRANREPT / AWS.M2.CARDDEMO.TRANREPT (GDG) | Sequential GDG | — | — | CBTRN03C | Formatted transaction report |
| EXPFILE / AWS.M2.CARDDEMO.EXPORT.DATA | VSAM KSDS | CVEXPORT | CBIMPORT | CBEXPORT | Multi-record export/import staging file |
| OUTFILE / AWS.M2.CARDDEMO.ACCTDATA.PSCOMP | Sequential PS | CVACT01Y | — | CBACT01C | Compressed account output |
| ARRYFILE / AWS.M2.CARDDEMO.ACCTDATA.ARRYPS | Sequential PS | CVACT01Y | — | CBACT01C | Array-format account output |
| VBRCFILE / AWS.M2.CARDDEMO.ACCTDATA.VBPS | Sequential VB | CVACT01Y | — | CBACT01C | Variable-block account output |
| CUSTOUT / AWS.M2.CARDDEMO.CUSTDATA.IMPORT | Sequential PS | CVCUS01Y | — | CBIMPORT | Normalised customer import output |
| ACCTOUT / AWS.M2.CARDDEMO.ACCTDATA.IMPORT | Sequential PS | CVACT01Y | — | CBIMPORT | Normalised account import output |
| XREFOUT / AWS.M2.CARDDEMO.CARDXREF.IMPORT | Sequential PS | CVACT03Y | — | CBIMPORT | Normalised card xref import output |
| TRNXOUT / AWS.M2.CARDDEMO.TRANSACT.IMPORT | Sequential PS | CVTRA05Y | — | CBIMPORT | Normalised transaction import output |
| ERROUT / AWS.M2.CARDDEMO.IMPORT.ERRORS | Sequential PS | — | — | CBIMPORT | Import error records |
| CARDOUT (no JCL DD) | Sequential PS | CVACT02Y | — | CBIMPORT | Card import output — defined in CBIMPORT.cbl (SELECT CARD-OUTPUT ASSIGN TO CARDOUT) but no DD in CBIMPORT.jcl; possible JCL omission |
| TRANSACT (DD) / AWS.M2.CARDDEMO.SYSTRAN (GDG) | Sequential GDG | CVTRA05Y | — | CBACT04C | System-generated interest transactions |
| TRNXFILE / AWS.M2.CARDDEMO.TRXFL.VSAM.KSDS | VSAM KSDS | COSTM01 (composite key TRNX-CARD-NUM X(16) + TRNX-ID X(16)) | CBSTM03B (called by CBSTM03A) | CREASTMT.JCL SORT+IDCAMS steps | Transaction file re-keyed by card+tran ID; built by CREASTMT.JCL from TRANSACT VSAM; read by CBSTM03B for statement generation |
| STMTFILE / AWS.M2.CARDDEMO.STATEMNT.PS | Sequential PS | 80-byte text | — | CBSTM03A | Customer statement plain-text output (CREASTMT.JCL step STEP040 DD STMTFILE) |
| HTMLFILE / AWS.M2.CARDDEMO.STATEMNT.HTML | Sequential PS | 100-byte HTML | — | CBSTM03A | Customer statement HTML output (CREASTMT.JCL step STEP040 DD HTMLFILE) |
| TRNXFILE, XREFFILE, CUSTFILE, ACCTFILE (CBSTM03B DDs) | VSAM KSDS | CVTRA05Y / CVACT03Y / CVCUS01Y / CVACT01Y | CBSTM03B (called by CBSTM03A) | — | CBSTM03A reads these files indirectly via CALL to CBSTM03B subprogram; CBSTM03B performs actual VSAM I/O using the DD names |
| ACCTDAT (CICS) / AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS | VSAM KSDS | CVACT01Y | COBIL00C, COACTVWC, COACTUPC, COPAUA0C | COBIL00C, COACTUPC | Account file accessed via CICS (CSD: DSNAME confirmed) |
| CARDDAT (CICS) / AWS.M2.CARDDEMO.CARDDATA.VSAM.KSDS | VSAM KSDS | CVCRD01Y | COCRDSLC, COCRDUPC, COACTVWC | COCRDUPC | Card data accessed via CICS (CSD: DSNAME confirmed) |
| CUSTDAT (CICS) / AWS.M2.CARDDEMO.CUSTDATA.VSAM.KSDS | VSAM KSDS | CVCUS01Y | COACTVWC, COACTUPC, COPAUA0C | COACTUPC | Customer data accessed via CICS (CSD: DSNAME confirmed) |
| CXACAIX (CICS) / AWS.M2.CARDDEMO.CARDXREF.VSAM.AIX.PATH | VSAM AIX | CVACT03Y | COBIL00C, COTRN02C, COACTVWC, COACTUPC | — | Card-to-acct xref alternate index path (CSD: DSNAME confirmed) |
| CARDAIX (CICS) / AWS.M2.CARDDEMO.CARDDATA.VSAM.AIX.PATH | VSAM AIX | CVCRD01Y | COCRDSLC | — | Card AIX by account number (CSD: DSNAME confirmed) |
| CCXREF (CICS) / AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS | VSAM KSDS | CVACT03Y | COTRN02C, COPAUA0C | — | Card xref direct read (CSD: DSNAME confirmed) |
| TRANSACT (CICS) / AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS | VSAM KSDS | CVTRA05Y | COBIL00C, COTRN00C, COTRN01C, COTRN02C | COBIL00C, COTRN02C | Transaction file via CICS (CSD: DSNAME confirmed) |
| USRSEC (CICS) / AWS.M2.CARDDEMO.USRSEC.VSAM.KSDS | VSAM KSDS | CSUSR01Y | COSGN00C, COUSR00C, COUSR02C, COUSR03C | COUSR01C, COUSR02C, COUSR03C | User security file via CICS (CSD: DSNAME confirmed) |


## Database Interfaces

| Table / Segment | Operations | Programs | Key Columns | Description |
| --------------- | ---------- | -------- | ----------- | ----------- |
| CARDDEMO.TRANSACTION_TYPE (DB2) | SELECT (cursor forward/backward), UPDATE | COTRTLIC | TR_TYPE | Transaction type list and paging — app-transaction-type-db2 variant |
| CARDDEMO.TRANSACTION_TYPE (DB2) | SELECT, UPDATE | COTRTUPC | TR_TYPE | Transaction type update — app-transaction-type-db2 variant |
| CARDDEMO.TRANSACTION_TYPE (DB2) | INSERT, UPDATE, DELETE | COBTUPDT | TR_TYPE | Batch maintenance of transaction type table — app-transaction-type-db2 variant |

**IMS/DL/I Interfaces (app-authorization-ims-db2-mq variant):**

| Table / Segment | Operations | Programs | Key Columns | Description |
| --------------- | ---------- | -------- | ----------- | ----------- |
| PSB=PSBPAUTB / PAUTSUM0 (root segment) | GU, REPL, ISRT, GN | COPAUA0C, COPAUS1C, CBPAUP0C | ACCNTID (account ID) | Pending authorization summary root segment in IMS DL/I database |
| PSB=PSBPAUTB / PAUTDTL1 (child segment) | GNP, ISRT, DLET | COPAUA0C, COPAUS1C, CBPAUP0C | PA-AUTHORIZATION-KEY | Pending authorization detail child segment in IMS DL/I database |

The core CardDemo application (app/cbl) uses VSAM files exclusively — no EXEC SQL or EXEC DLI statements are present in the main source directory.


## Messaging Interfaces

| Queue / Topic | Direction | Programs | Message Format | Description |
| ------------- | --------- | -------- | -------------- | ----------- |
| JOBS (CICS TD Queue; DDNAME=INREADER) | PUT | CORPT00C | JCL-RECORD (80 bytes, fixed) | Extra-partition transient data queue backed by the JES internal reader (INREADER DD per CSD); WRITEQ TD QUEUE('JOBS') submits a batch report job record to the JES input stream |
| Dynamic request queue (MQ, name from CICS RETRIEVE trigger) | GET | COACCT01 | Account query message (card num + function code) | CICS online program in app-vsam-mq variant; retrieves input queue name from MQ trigger message |
| CARD.DEMO.REPLY.ACCT (MQ Queue) | PUT | COACCT01 | Account data response (text) | MQ reply queue for account data service in app-vsam-mq variant |
| Dynamic request queue (MQ, name from CICS RETRIEVE trigger) | GET | CODATE01 | Date query message | CICS online program in app-vsam-mq variant; retrieves input queue name from MQ trigger message |
| CARD.DEMO.REPLY.DATE (MQ Queue) | PUT | CODATE01 | Date/time response (text) | MQ reply queue for date service in app-vsam-mq variant |
| CARD.DEMO.ERROR (MQ Queue) | PUT | COACCT01, CODATE01 | Error display message | Shared error queue for app-vsam-mq variant programs |
| Dynamic request queue (MQ, name from CICS RETRIEVE trigger) | GET | COPAUA0C | Authorization request CSV message (card num, amount, merchant data) | CICS online program in app-authorization variant; reads authorization requests |
| Dynamic reply queue (MQ, from MQMD-REPLYTOQ) | PUT (MQPUT1) | COPAUA0C | Authorization response CSV (card num, transaction ID, auth code, reason code, approved amount) | Reply queue set by requester in MQ message descriptor |

No CICS TS (temporary storage) queues were found in any variant.


## CICS Interfaces

### Core Application (app/cbl — CARDDEMO.CSD)

| Transaction | Program | Map/Mapset | Comm Area | Description |
| ----------- | ------- | ---------- | --------- | ----------- |
| CC00 | COSGN00C | COSGN0A / COSGN00 | CARDDEMO-COMMAREA (COCOM01Y) | Signon / login screen |
| CA00 | COADM01C | COADM1A / COADM01 | CARDDEMO-COMMAREA (COCOM01Y) | Admin menu |
| CM00 | COMEN01C | COMEN1A / COMEN01 | CARDDEMO-COMMAREA (COCOM01Y) | Main menu; XCTLs to selected program |
| CAVW | COACTVWC | CACTVWA / COACTVW | CARDDEMO-COMMAREA (COCOM01Y) | View account details |
| CAUP | COACTUPC | CACTUPA / COACTUP | CARDDEMO-COMMAREA (COCOM01Y) | Update account and customer details |
| CB00 | COBIL00C | COBIL0A / COBIL00 | CARDDEMO-COMMAREA (COCOM01Y) | Bill payment processing |
| CCLI | COCRDLIC | CCRDLIA / COCRDLI | CARDDEMO-COMMAREA (COCOM01Y) | Credit card list (browse) |
| CCDL | COCRDSLC | CCRDSLA / COCRDSL | CARDDEMO-COMMAREA (COCOM01Y) | Credit card detail select |
| CCUP | COCRDUPC | CCRDUPA / COCRDUP | CARDDEMO-COMMAREA (COCOM01Y) | Credit card update |
| CDV1 | COCRDSEC | — | — | Developer/search transaction (CSD CARDDEMO group); COCRDSEC source not in app/cbl inventory — external or removed program |
| CR00 | CORPT00C | CORPT0A / CORPT00 | CARDDEMO-COMMAREA (COCOM01Y) | Report request; writes to JOBS TD queue |
| CT00 | COTRN00C | COTRN0A / COTRN00 | CARDDEMO-COMMAREA (COCOM01Y) | Transaction list (browse) |
| CT01 | COTRN01C | COTRN1A / COTRN01 | CARDDEMO-COMMAREA (COCOM01Y) | Transaction detail view |
| CT02 | COTRN02C | COTRN2A / COTRN02 | CARDDEMO-COMMAREA (COCOM01Y) | Add new transaction |
| CU00 | COUSR00C | COUSR0A / COUSR00 | CARDDEMO-COMMAREA (COCOM01Y) | User list (browse) |
| CU01 | COUSR01C | COUSR1A / COUSR01 | CARDDEMO-COMMAREA (COCOM01Y) | Add user |
| CU02 | COUSR02C | COUSR2A / COUSR02 | CARDDEMO-COMMAREA (COCOM01Y) | Update user |
| CU03 | COUSR03C | COUSR3A / COUSR03 | CARDDEMO-COMMAREA (COCOM01Y) | Delete user |

Note: The CARDDEMO.CSD contains a single CSD file covering all core application resources. BMS map source files are not present in the app/bms directory (compile-time artefacts only). Map and mapset names are confirmed from CSD DEFINE MAPSET entries and program WORKING-STORAGE VALUE clauses. The CC00 transaction entry in the CSD points to COSGN00C (the authoritative DEFINE TRANSACTION entry); the TRANSID(CC00) attribute on the DEFINE PROGRAM(COCRDLIC) entry is a program attribute, not a transaction routing override.

### app-vsam-mq Variant

| Transaction | Program | Map/Mapset | Comm Area | Description |
| ----------- | ------- | ---------- | --------- | ----------- |
| CDRA | COACCT01 | — | — | Account data MQ service; triggered via MQ trigger; reads ACCTDAT, replies on CARD.DEMO.REPLY.ACCT |
| CDRD | CODATE01 | — | — | Date/time MQ service; triggered via MQ trigger; replies on CARD.DEMO.REPLY.DATE |

### app-authorization-ims-db2-mq Variant

| Transaction | Program | Map/Mapset | Comm Area | Description |
| ----------- | ------- | ---------- | --------- | ----------- |
| CP00 | COPAUA0C | — | DFHCOMMAREA PIC X(4096) | Card authorization decision engine; reads MQ request queue, validates via IMS/VSAM, writes MQ reply |
| CPVS | COPAUS0C | COPAU0A / COPAU00 | CARDDEMO-COMMAREA (COCOM01Y) | Authorization summary view screen; reads IMS PAUTSUM0 |
| CPVD | COPAUS1C | COPAU1A / COPAU01 | CARDDEMO-COMMAREA (COCOM01Y) | Authorization detail view screen; reads/updates IMS PAUTSUM0/PAUTDTL1 |
| CPVD | COPAUS2C | COPAU1A / COPAU01 | CARDDEMO-COMMAREA (COCOM01Y) | Authorization detail variant (same transaction as COPAUS1C per CSD) |

Note: CSD defines CPVD with primary program COPAUS1C. COPAUS2C shares the same transaction ID.

### app-transaction-type-db2 Variant

| Transaction | Program | Map/Mapset | Comm Area | Description |
| ----------- | ------- | ---------- | --------- | ----------- |
| CTLI | COTRTLIC | CTRTLIA / COTRTLI | CARDDEMO-COMMAREA (COCOM01Y) | Transaction type list with DB2 paging (linked to COADM01C/CA00) |
| CTTU | COTRTUPC | CTRTUPA / COTRTUP | CARDDEMO-COMMAREA (COCOM01Y) | Transaction type add/update/delete via DB2 |

**CICS XCTL flows observed in core source:**

| From Program | To Program (literal / variable) | Condition |
| ------------ | ------------------------------- | --------- |
| COSGN00C | COADM01C | Admin user authenticated |
| COSGN00C | COMEN01C | Regular user authenticated |
| COMEN01C | CDEMO-MENU-OPT-PGMNAME(WS-OPTION) | Menu option selected (dynamic target) |
| COCRDLIC | COMEN01C (LIT-MENUPGM) | F3 / back to menu |
| COCRDLIC | CCARD-NEXT-PROG | Card selected (dynamic — drives to COCRDUPC or COCRDSLC) |
| COCRDSLC | CDEMO-TO-PROGRAM | Navigation driven by commarea |
| COCRDUPC | CDEMO-TO-PROGRAM | Navigation driven by commarea |
| COACTVWC | CDEMO-TO-PROGRAM | Navigation driven by commarea |
| COACTUPC | CDEMO-TO-PROGRAM | Navigation driven by commarea |
| COTRTLIC | COADM01C (LIT-ADMINPGM) | F3 / back to admin menu |
| COTRTLIC | COTRTUPC (LIT-ADDTPGM) | Row selected for update |


## External System Boundary

Systems or applications referenced but outside the analysed codebase:

| System | Interface Type | Direction | Evidence |
| ------ | -------------- | --------- | -------- |
| CEE3ABD (LE/370 runtime) | CALL | OUT | CALL 'CEE3ABD' in all batch programs; Language Environment abnormal termination handler |
| MVSWAIT (MVS system service) | CALL | OUT | CALL 'MVSWAIT' in COBSWAIT; MVS wait/sleep service |
| COBDATFT (date/time service) | CALL | OUT | CALL 'COBDATFT' USING CODATECN-REC in CBACT01C (line 231); date/time formatting utility; source not found in app/cbl inventory |
| COCRDSEC (missing program) | CICS XCTL target | IN | CSD CARDDEMO group defines TRANSACTION(CDV1) PROGRAM(COCRDSEC); source not found in app/cbl; developer/search program removed or not included in this source set |
| DFHCSDUP (CICS utility) | JCL PGM | OUT | CBADMCDJ.jcl; used to define CICS CSD resources for the application group |
| SORT (IBM DFSORT/SYNCSORT) | JCL PGM | BOTH | COMBTRAN.jcl, TRANREPT.jcl, CREASTMT.JCL; external sort utility used to sort/filter transaction datasets and build TRXFL.VSAM.KSDS |
| IDCAMS (VSAM utility) | JCL PGM | BOTH | COMBTRAN.jcl, CBEXPORT.jcl, CREASTMT.JCL; used to REPRO data into VSAM and define/delete clusters |
| REPROC (PROC) | JCL PROC | BOTH | TRANREPT.jcl; system procedure for dataset unload (AWS.M2.CARDDEMO.PROC library) |
| AWS.M2.CARDDEMO.LOADLIB | Load library | IN | All batch JCL STEPLIB; external load library for compiled programs |
| JES Internal Reader (INREADER) | CICS TD Queue | OUT | JOBS TD queue DDNAME=INREADER per CSD; CORPT00C submits JCL records to the JES input stream via WRITEQ TD |
| CICS Region | CICS | BOTH | All online programs (EXEC CICS); CICS TS/TP infrastructure for screen management and file access |
| IBM MQ Series | MQ | BOTH | CALL 'MQOPEN', 'MQGET', 'MQPUT', 'MQPUT1', 'MQCLOSE' in COACCT01, CODATE01, COPAUA0C; external MQ broker for async messaging |
| IMS/DL/I subsystem | IMS | BOTH | EXEC DLI SCHD/GU/GN/GNP/REPL/ISRT/DLET/TERM in COPAUA0C, COPAUS1C, CBPAUP0C; external IMS database containing pending authorization segments |
| DB2 subsystem (plan AWS01PLN / CARDDEMO) | DB2 | BOTH | EXEC SQL in COTRTLIC, COTRTUPC, COBTUPDT; external DB2 instance hosting CARDDEMO.TRANSACTION_TYPE table; CSD DB2ENTRY definitions reference plans AWS01PLN and CARDDEMO |
| DSNTIAC (DB2 callable interface) | CALL | OUT | LIT-DSNTIAC VALUE 'DSNTIAC' in COTRTLIC; DB2 error message formatting utility |
| CEEDAYS (LE calendar service) | CALL | OUT | CALL 'CEEDAYS' in CSUTLDTC; Language Environment date conversion API |
