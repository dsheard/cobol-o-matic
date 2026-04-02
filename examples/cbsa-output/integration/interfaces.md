---
type: integration
subtype: interfaces
status: draft
confidence: high
last_pass: 2
---

# External Interfaces

All external system touchpoints identified in the COBOL source for the CICS Banking Sample Application (CBSA).

## Interface Summary

| Interface | Type | Direction | Used By Programs | Description |
| --------- | ---- | --------- | ---------------- | ----------- |
| CUSTOMER | File (VSAM KSDS) | BOTH | BANKDATA, CRECUST, UPDCUST, INQCUST, DELCUS | Core customer master store |
| ABNDFILE | File (VSAM KSDS) | OUT | ABNDPROC | Abend audit log |
| ACCOUNT | DB2 Table | BOTH | BANKDATA, CREACC, INQACC, INQACCCU, UPDACC, DELACC, DBCRFUN, XFRFUN | Account master table (schema: IBMUSER) |
| PROCTRAN | DB2 Table | OUT | CRECUST, CREACC, DELACC, DELCUS, DBCRFUN, XFRFUN | Transaction audit/processing log (schema: IBMUSER) |
| CONTROL | DB2 Table | BOTH | BANKDATA, CREACC | Sequence control (account counters) (schema: STTESTER) |
| BNK1MAI / BNK1ME | CICS BMS Map | BOTH | BNKMENU | Main menu screen |
| BNK1CAM / BNK1CA | CICS BMS Map | BOTH | BNK1CAC | Create account screen |
| BNK1CCM / BNK1CC | CICS BMS Map | BOTH | BNK1CCS | Create customer screen |
| BNK1CDM / BNK1CD | CICS BMS Map | BOTH | BNK1CRA | Credit/debit funds screen |
| BNK1DAM / BNK1DA | CICS BMS Map | BOTH | BNK1DAC | Display account screen |
| BNK1DCM / BNK1DC | CICS BMS Map | BOTH | BNK1DCS | Display/update customer screen |
| BNK1TFM / BNK1TF | CICS BMS Map | BOTH | BNK1TFN | Transfer funds screen |
| BNK1UAM / BNK1UA | CICS BMS Map | BOTH | BNK1UAC | Update account screen |
| BNK1ACC / BNK1ACC | CICS BMS Map | BOTH | BNK1CCA | Accounts-for-customer list screen |
| BNK1TFM / BNK1B2 | CICS BMS Map | -- | (none) | Alternate transfer map; defined in BNK1B2M.bms within mapset BNK1TFM but not referenced by any program in source |
| CIPCREDCHANN | CICS Channel/Container | BOTH | CRECUST, CRDTAGY1-5 | Credit agency async channel |
| ABNDPROC | CICS Program (internal) | BOTH | All programs (error path) | Centralised abend handler |
| INQACC | CICS Program (internal) | BOTH | BNK1DAC, BNK1UAC | Inquire account back-end |
| INQACCCU | CICS Program (internal) | BOTH | BNK1CCA, CREACC, DELCUS | Inquire accounts for customer |
| INQCUST | CICS Program (internal) | BOTH | BNK1DCS, CREACC, DELCUS, INQACCCU | Inquire customer back-end |
| CREACC | CICS Program (internal) | BOTH | BNK1CAC | Create account back-end |
| CRECUST | CICS Program (internal) | BOTH | BNK1CCS | Create customer back-end |
| UPDACC | CICS Program (internal) | BOTH | BNK1UAC | Update account back-end |
| UPDCUST | CICS Program (internal) | BOTH | BNK1DCS | Update customer back-end |
| DELACC | CICS Program (internal) | BOTH | BNK1DAC, DELCUS | Delete account back-end |
| DELCUS | CICS Program (internal) | BOTH | BNK1DCS | Delete customer back-end |
| DBCRFUN | CICS Program (internal) | BOTH | BNK1CRA | Debit/credit function back-end |
| XFRFUN | CICS Program (internal) | BOTH | BNK1TFN | Transfer function back-end |
| GETCOMPY | CICS Program (internal) | BOTH | (Java web layer only) | Returns application company name; no COBOL callers in source |
| GETSCODE | CICS Program (internal) | BOTH | (Java web layer only) | Returns bank sort code; no COBOL callers in source |
| OCR1-OCR5 (CRDTAGY1-5) | CICS Async Transaction | BOTH | CRECUST | Credit agency child transactions |
| HBNKACCT{sortcode} | CICS ENQ Resource | BOTH | CREACC | EXEC CICS ENQ/DEQ resource lock guarding account counter reads/writes in the CONTROL DB2 table |
| HBNKCUST{sortcode} | CICS ENQ Resource | BOTH | CRECUST | EXEC CICS ENQ/DEQ resource lock guarding customer counter reads/writes in the CUSTOMER VSAM control record |

## File Interfaces

| DD Name / Path | Organisation | Record Layout | Read By | Written By | Description |
| -------------- | ------------ | ------------- | ------- | ---------- | ----------- |
| CUSTOMER | VSAM KSDS | CUSTOMER copybook | INQCUST, DELCUS, UPDCUST, CRECUST | CRECUST, UPDCUST, BANKDATA | Customer master VSAM file; key = SORTCODE(6) + CUSTOMER-NUMBER(10). Also holds a control record (key 0000009999999999) that stores LAST-CUSTOMER-NUMBER and NUMBER-OF-CUSTOMERS; CRECUST reads and rewrites this control record to allocate new customer numbers. |
| ABNDFILE | VSAM KSDS | ABNDINFO copybook | (none observed) | ABNDPROC | Abend audit store; written on every application abend via ABNDPROC. Key = UTIME (S9(15) COMP-3) + TASKNO (9(4)). |
| CUSTOMER-FILE (batch) | VSAM KSDS (INDEXED) | CUSTOMER copybook | (none in batch) | BANKDATA | Batch alias for the CUSTOMER VSAM file; opened OUTPUT by BANKDATA during data initialisation using standard COBOL FD/WRITE (not EXEC CICS). |

## Database Interfaces

| Table / Segment | Operations | Programs | Key Columns | Description |
| --------------- | ---------- | -------- | ----------- | ----------- |
| ACCOUNT | SELECT (cursor), INSERT, UPDATE, DELETE | BANKDATA (INSERT, DELETE), CREACC (INSERT), INQACC (SELECT cursor + singleton), INQACCCU (SELECT cursor), UPDACC (SELECT, UPDATE), DELACC (SELECT, DELETE), DBCRFUN (SELECT, UPDATE), XFRFUN (SELECT x2, UPDATE x2) | ACCOUNT_SORTCODE, ACCOUNT_NUMBER; secondary: ACCOUNT_CUSTOMER_NUMBER | DB2 account master table. Schema owner: IBMUSER. Columns include eyecatcher, customer number, sort code, account number, type, interest rate, dates, overdraft limit, available/actual balances. |
| PROCTRAN | INSERT | CRECUST, CREACC, DELACC, DELCUS, DBCRFUN, XFRFUN | PROCTRAN_SORTCODE, PROCTRAN_NUMBER | DB2 transaction audit log. Schema owner: IBMUSER. Records every significant financial or customer event. Columns: eyecatcher, sort code, account number, date, time, ref, type, description, amount. |
| CONTROL | SELECT, INSERT, UPDATE, DELETE | BANKDATA (INSERT, DELETE), CREACC (SELECT, UPDATE) | CONTROL_NAME | DB2 sequence control table. Schema owner: STTESTER (as declared in CONTDB2.cpy; CREATE TABLE uses IBMUSER schema per CRETB03.jcl -- schema may vary by installation). Stores named counters such as `{sortcode}-ACCOUNT-LAST` and `{sortcode}-ACCOUNT-COUNT`. |

## Messaging Interfaces

No MQ or CICS TS/TD queue interfaces were found in the source. The application uses the CICS Async API (EXEC CICS RUN TRANSID / GET CONTAINER / PUT CONTAINER) with a named channel instead of traditional queuing.

| Queue / Topic | Direction | Programs | Message Format | Description |
| ------------- | --------- | -------- | -------------- | ----------- |
| CIPCREDCHANN (CICS Channel) | BOTH (PUT + GET) | CRECUST (PUT input + GET results), CRDTAGY1-5 (GET input + PUT results) | WS-CONT-IN structure in CRDTAGY programs (247 bytes) | Async credit-scoring channel. CRECUST puts customer data in containers CIPA/CIPB/CIPC/CIPD/CIPE and fires transactions OCR1-OCR5 via EXEC CICS RUN TRANSID. Each CRDTAGY program reads the container, generates a credit score, and puts it back. CRECUST then fetches the results after a timeout. |

## CICS Interfaces

| Transaction | Program | Map / Mapset | Comm Area | Description |
| ----------- | ------- | ------------ | --------- | ----------- |
| OMEN | BNKMENU | BNK1ME / BNK1MAI | COMMUNICATION-AREA (1 byte) | Main menu. Entry point for the BMS front-end. Returns TRANSID for each function. |
| ODCS | BNK1DCS | BNK1DC / BNK1DCM | INQCUST/DELCUS/UPDCUST commarea | Display/delete/update customer screen. Invoked from BNKMENU. |
| ODAC | BNK1DAC | BNK1DA / BNK1DAM | INQACC/DELACC commarea | Display/delete account screen. Invoked from BNKMENU. |
| OCCS | BNK1CCS | BNK1CC / BNK1CCM | CRECUST commarea | Create customer screen. Invoked from BNKMENU. |
| OCAC | BNK1CAC | BNK1CA / BNK1CAM | CREACC commarea | Create account screen. Invoked from BNKMENU. |
| OUAC | BNK1UAC | BNK1UA / BNK1UAM | INQACC/UPDACC commarea | Update account screen. Invoked from BNKMENU. |
| OCRA | BNK1CRA | BNK1CD / BNK1CDM | DBCRFUN commarea | Credit/debit funds screen. Invoked from BNKMENU. |
| OTFN | BNK1TFN | BNK1TF / BNK1TFM | XFRFUN commarea | Transfer funds screen. Invoked from BNKMENU. |
| OCCA | BNK1CCA | BNK1ACC / BNK1ACC | INQACCCU commarea | List accounts for a customer. Invoked from BNKMENU. |
| OCR1 | CRDTAGY1 | (none) | WS-CONT-IN via CIPCREDCHANN (container CIPA) | Credit agency 1 (async). Invoked by CRECUST via EXEC CICS RUN TRANSID. Transaction ID constructed at runtime: STRING 'OCR' WS-CC-CNT. |
| OCR2 | CRDTAGY2 | (none) | WS-CONT-IN via CIPCREDCHANN (container CIPB) | Credit agency 2 (async). Invoked by CRECUST via EXEC CICS RUN TRANSID. |
| OCR3 | CRDTAGY3 | (none) | WS-CONT-IN via CIPCREDCHANN (container CIPC) | Credit agency 3 (async). Invoked by CRECUST via EXEC CICS RUN TRANSID. |
| OCR4 | CRDTAGY4 | (none) | WS-CONT-IN via CIPCREDCHANN (container CIPD) | Credit agency 4 (async). Invoked by CRECUST via EXEC CICS RUN TRANSID. |
| OCR5 | CRDTAGY5 | (none) | WS-CONT-IN via CIPCREDCHANN (container CIPE) | Credit agency 5 (async). Invoked by CRECUST via EXEC CICS RUN TRANSID. |
| (not assigned) | GETCOMPY | (none) | GETCompanyOperation commarea (company-name PIC X(40)) | Returns application company name. No CICS transaction ID found in COBOL source; invoked by Java web layer (CompanyNameResource.java) via EXEC CICS LINK. |
| (not assigned) | GETSCODE | (none) | GETSORTCODEOperation commarea (SORTCODE PIC X(6)) | Returns bank sort code (literal 987654). No CICS transaction ID found in COBOL source; invoked by Java web layer (SortCodeResource.java) via EXEC CICS LINK. |

## External System Boundary

Systems or applications referenced but outside the analysed codebase:

| System | Interface Type | Direction | Evidence |
| ------ | -------------- | --------- | -------- |
| DB2 subsystem | DB2 | BOTH | EXEC SQL statements in BANKDATA, CREACC, INQACC, INQACCCU, UPDACC, DELACC, DBCRFUN, XFRFUN, CRECUST, DELCUS. Tables: ACCOUNT (IBMUSER), PROCTRAN (IBMUSER), CONTROL (STTESTER/IBMUSER depending on installation). |
| VSAM file system | File | BOTH | SELECT...ASSIGN TO VSAM in BANKDATA; EXEC CICS FILE('CUSTOMER') and FILE('ABNDFILE') in multiple CICS programs. |
| CICS (BMS terminal) | CICS Screen | BOTH | EXEC CICS SEND MAP / RETURN TRANSID in all BNK1xxx screen programs; 3270 terminal assumed. |
| CICS ENQ/DEQ (resource locking) | CICS | BOTH | EXEC CICS ENQ RESOURCE(NCS-ACC-NO-NAME) in CREACC (resource = 'HBNKACCT' + sortcode, 16 bytes) guards the account counter in the CONTROL DB2 table. EXEC CICS ENQ RESOURCE(NCS-CUST-NO-NAME) in CRECUST (resource = 'HBNKCUST' + sortcode, 16 bytes) guards the customer counter in the CUSTOMER VSAM control record. These are standard CICS resource enqueues, not the CICS Named Counter Service product. |
| Java web layer | HTTP/CICS LINK | IN | GETCOMPY and GETSCODE are linked to by Java RESTful resources (CompanyNameResource.java, SortCodeResource.java) in the CBSA web application. No COBOL programs in the source invoke these programs. |
| DFHCSDUP (CSD utility) | JCL/Install | IN | CBSACSD.jcl uses DFHCSDUP to load transaction/program definitions from a BANK member PDS. The BANK member was not available for direct parsing; transaction-to-program mappings (OMEN, ODCS, ODAC, etc.) are inferred from EXEC CICS RETURN TRANSID statements in program source. |
| CEEGMT / CEEDATM | CALL (LE runtime) | IN | Called by BANKDATA for date/time services. These are IBM Language Environment (LE) runtime routines, not COBOL programs in the source inventory. |
| ACCLOAD | Batch Program | -- | Build JCL (ACCLOAD.jcl) references this batch COBOL program but no source exists in the analysed codebase. Likely an account-load utility outside the base source set. |
| ACCOFFL | Batch Program | -- | Build JCL (ACCOFFL.jcl) references this batch COBOL program but no source exists in the analysed codebase. Likely an account offline/extract utility outside the base source set. |
| EXTDCUST | Batch Program | -- | Build JCL (EXTDCUST.jcl) references this batch COBOL program but no source exists in the analysed codebase. Likely a customer extract utility outside the base source set. |
