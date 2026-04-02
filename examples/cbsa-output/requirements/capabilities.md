---
type: requirements
subtype: capabilities
status: draft
confidence: high
last_pass: 1
---

# Functional Capabilities

Derived functional capabilities describing what this COBOL application does, synthesized from business rules, data flows, and integration analysis.

---

## Capabilities

### Navigation and Session Management

| Property        | Value                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Description     | Presents a BMS 3270 main menu to tellers and CSRs, validates their menu selection, and routes them to the correct transaction. Manages the pseudo-conversational session lifecycle including graceful session termination on PF3/PF12. |
| Source Programs | BNKMENU                                                                                                                 |
| Input           | BMS map BNK1ME (BNK1MAI mapset), single-character ACTION field from 3270 terminal                                       |
| Output          | CICS RETURN TRANSID to one of ODCS, ODAC, OCCS, OCAC, OUAC, OCRA, OTFN, OCCA; 'Session Ended' message on termination  |
| Business Rules  | Valid selections are 1-7 and A; PA keys are no-ops; PF3/PF12 terminate session; CLEAR ends session without message; any other key shows 'Invalid key pressed.' with alarm; MAPFAIL redisplays blank menu (with minor UX defect causing spurious validation message) |
| Data Entities   | COMMUNICATION-AREA (1 byte pseudo-conversational token), BNK1MEI/BNK1MEO (map I/O areas)                               |

---

### Customer Enquiry

| Property        | Value                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Description     | Retrieves a single customer record by customer number, returning all customer attributes (name, address, DOB, credit score, credit-score review date) to the presentation layer. |
| Source Programs | BNK1DCS (presentation), INQCUST (data access)                                                                          |
| Input           | Customer number entered on BMS map BNK1DCM (BNK1DC mapset); INQCUST-COMMAREA                                           |
| Output          | BMS map BNK1DCM populated with customer details; INQCUST-COMMAREA returned to callers                                  |
| Business Rules  | Customer number must be supplied; VSAM KSDS lookup by composite key (SORTCODE + CUSTOMER-NUMBER); 'N' success flag returned when not found; any VSAM error causes ABEND |
| Data Entities   | CUSTOMER (VSAM KSDS), INQCUST copybook (COMMAREA), CUSTOMER copybook (record layout)                                   |

---

### Customer Creation with Credit Scoring

| Property        | Value                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Description     | Creates a new customer record after validating the customer's title and date of birth, running parallel asynchronous credit checks against five simulated credit agencies, averaging the returned scores, and persisting the customer to VSAM with a PROCTRAN audit row. Serialises customer number allocation using CICS ENQ/DEQ on a sort-code-scoped resource. |
| Source Programs | BNK1CCS (presentation), CRECUST (backend), CRDTAGY1, CRDTAGY2, CRDTAGY3, CRDTAGY4, CRDTAGY5 (async credit stubs)      |
| Input           | BMS map BNK1CCM; CRECUST COMMAREA (name, address, DOB, credit score fields); CIPCREDCHANN containers CIPA-CIPE          |
| Output          | CUSTOMER VSAM record written; PROCTRAN row inserted (type 'OCC'); assigned customer number and sort code returned in COMMAREA |
| Business Rules  | Title must be from allowed list (Professor, Mr, Mrs, Miss, Ms, Dr, Drs, Lord, Sir, Lady, or blank); DOB must be valid calendar date via CEEDAYS/CEELOCT LE calls; DOB year >= 1601; DOB not in future; customer age <= 150 years; five async child transactions OCR1-OCR5 launched via CICS RUN TRANSID; parent waits 3 seconds then FETCH ANY NOSUSPEND; credit score = integer average of received scores (no rounding); review date = random 1-20 days from today; ENQ resource name = 'CBSACUST' + 6-char sortcode; new customer number = LAST-CUSTOMER-NUMBER + 1 from VSAM control record; SYSIDERR on VSAM retried up to 100 times |
| Data Entities   | CUSTOMER (VSAM KSDS), PROCTRAN (DB2), CIPCREDCHANN CICS channel, CUSTCTRL (control record), CRECUST copybook, CUSTOMER copybook |

---

### Account Enquiry

| Property        | Value                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Description     | Retrieves a single account record from the DB2 ACCOUNT table by account number and sort code. Supports a special sentinel value (99999999) to retrieve the highest-numbered account for the branch. Used by both the display-account and update-account screens. |
| Source Programs | BNK1DAC (display presentation), BNK1UAC (update presentation), INQACC (data access)                                   |
| Input           | INQACC-COMMAREA (account number); BMS maps BNK1DAM / BNK1UAM                                                           |
| Output          | All 12 ACCOUNT fields returned in INQACC-COMMAREA; INQACC-SUCCESS flag 'Y'/'N'                                         |
| Business Rules  | Sort code is always the hardcoded installation constant (987654); INQACC-ACCNO=99999999 triggers last-account lookup via ORDER BY DESC FETCH FIRST 1 ROW; standard path uses DB2 cursor; SQLCODE +100 returns success='N'; all other non-zero SQLCODEs cause ABEND 'HRAC' or 'HNCS' via ABNDPROC; DB2 dates reformatted from YYYY-MM-DD to day/month/year components |
| Data Entities   | ACCOUNT (DB2), ACCDB2 copybook, INQACC copybook, ACCOUNT copybook                                                      |

---

### Accounts Enquiry by Customer

| Property        | Value                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Description     | Retrieves all accounts (up to 20) belonging to a given customer number from the DB2 ACCOUNT table. Used by the customer-accounts list screen, and internally by CREACC (account count enforcement) and DELCUS (account iteration for deletion). |
| Source Programs | BNK1CCA (presentation), INQACCCU (data access)                                                                         |
| Input           | INQACCCU-COMMAREA (customer number, max count); BMS map BNK1ACC                                                         |
| Output          | ODO array of up to 20 ACCOUNT-DETAILS rows plus NUMBER-OF-ACCOUNTS count, INQACCCU success flag                        |
| Business Rules  | Sort code is always the hardcoded constant; DB2 cursor SELECT by ACCOUNT_CUSTOMER_NUMBER; returns up to 20 rows; also calls INQCUST to cross-reference customer; success='N' if customer not found |
| Data Entities   | ACCOUNT (DB2), CUSTOMER (VSAM KSDS), INQACCCU copybook (ODO array layout), ACCDB2 copybook                             |

---

### Account Creation

| Property        | Value                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Description     | Creates a new bank account for an existing customer. Validates customer existence, enforces a maximum of 10 accounts per customer, validates account type, serialises account number allocation via CICS ENQ/DEQ on the CONTROL DB2 table counter, inserts the ACCOUNT row, and writes a PROCTRAN audit record. |
| Source Programs | BNK1CAC (presentation), CREACC (backend)                                                                               |
| Input           | BMS map BNK1CAM; CREACC COMMAREA (customer number, account type, interest rate, overdraft limit, balances)              |
| Output          | ACCOUNT DB2 row inserted; PROCTRAN row inserted (type 'OCA'); new account number and sort code returned in COMMAREA     |
| Business Rules  | Customer must exist (INQCUST call); customer must have fewer than 10 existing accounts (INQACCCU call, limit > 9 rejected); account type must be one of ISA, MORTGAGE, SAVING, CURRENT, LOAN; ENQ resource = 'CBSAACCT' + 6-char sortcode; account number = CONTROL.ACCOUNT-LAST + 1 (DB2 SELECT + UPDATE); CONTROL.ACCOUNT-COUNT also incremented; DB2 CONTROL failures cause ABEND 'HNCS'; ACCOUNT INSERT failure returns fail code '7'; PROCTRAN failure causes ABEND 'HWPT'; next statement date = opened date + 30 days (simple, not month-aware for all months); PROCTRAN amount = zero for account creation |
| Data Entities   | ACCOUNT (DB2), CONTROL (DB2), PROCTRAN (DB2), CUSTOMER (VSAM), CREACC copybook, ACCDB2 copybook, ACCTCTRL copybook     |

---

### Account Update

| Property        | Value                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Description     | Allows a CSR to amend the account type, interest rate, and overdraft limit for an existing account. Balances and statement dates are read-only through this function. No PROCTRAN audit record is written. |
| Source Programs | BNK1UAC (presentation), UPDACC (data access), INQACC (read before update)                                             |
| Input           | BMS map BNK1UAM; UPDACC COMMAREA (account number, type, interest rate, overdraft limit)                                |
| Output          | ACCOUNT DB2 row updated (three fields only); updated record returned in COMMAREA; COMM-SUCCESS flag                    |
| Business Rules  | Account type must not be blank (only validation in UPDACC itself; other field validation delegated to BNK1UAC); only ACCOUNT_TYPE, ACCOUNT_INTEREST_RATE, ACCOUNT_OVERDRAFT_LIMIT are written; balances are never modified; sort code is hardcoded constant; SELECT then UPDATE in same CICS UoW; no PROCTRAN record; no ABEND logic wired up (uses COMM-SUCCESS='N' + CICS RETURN for errors) |
| Data Entities   | ACCOUNT (DB2), ACCDB2 copybook, UPDACC copybook                                                                        |

---

### Account Deletion

| Property        | Value                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Description     | Deletes a single bank account from the DB2 ACCOUNT table. Records the actual balance at deletion time in a PROCTRAN audit row (type 'ODA'). Called both from the display-account screen and from the customer deletion cascade. |
| Source Programs | BNK1DAC (presentation), DELACC (data access)                                                                           |
| Input           | BMS map BNK1DAM (PF5 key); DELACC-COMMAREA (account number)                                                            |
| Output          | ACCOUNT DB2 row deleted; PROCTRAN row inserted with account balance at time of deletion (type 'ODA'); success/fail flag |
| Business Rules  | Account retrieved by sort code + account number; account not found returns fail code '1'; DELETE failure returns fail code '3'; PROCTRAN write failure causes ABEND 'HWPT'; PROCTRAN amount = actual balance at deletion time; PROCTRAN description includes customer number, account type, last/next statement dates |
| Data Entities   | ACCOUNT (DB2), PROCTRAN (DB2), ACCDB2 copybook, DELACC copybook                                                        |

---

### Customer Update

| Property        | Value                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Description     | Allows a CSR to update customer attributes (name, address, DOB, credit score) on an existing VSAM customer record. Accessible from the display-customer screen via PF10. |
| Source Programs | BNK1DCS (presentation), UPDCUST (data access)                                                                          |
| Input           | BMS map BNK1DCM (PF10 key); UPDCUST COMMAREA (customer key, name, address, DOB, credit score, review date)             |
| Output          | CUSTOMER VSAM record rewritten; success/fail flag returned in COMMAREA                                                  |
| Business Rules  | VSAM READ FOR UPDATE then REWRITE; sort code is hardcoded constant; no PROCTRAN record written; errors return COMM-SUCCESS='N'; abend infrastructure defined but not wired (similar to UPDACC) |
| Data Entities   | CUSTOMER (VSAM KSDS), CUSTOMER copybook, UPDCUST copybook                                                              |

---

### Customer Deletion (Full Cascade)

| Property        | Value                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Description     | Deletes a customer and all their associated accounts in a cascading operation. Verifies customer existence, iterates over all accounts (up to 20) and deletes each via DELACC, then deletes the VSAM customer record with token-based optimistic locking, and finally writes a PROCTRAN audit row (type 'ODC'). Any failure after deletion has started causes an ABEND to prevent partial deletes. |
| Source Programs | BNK1DCS (presentation), DELCUS (orchestrator), INQCUST, INQACCCU, DELACC                                               |
| Input           | BMS map BNK1DCM (PF5 key); DELCUS COMMAREA (customer number)                                                           |
| Output          | All ACCOUNT rows for customer deleted (via DELACC, which writes individual PROCTRAN 'ODA' records); CUSTOMER VSAM record deleted; single PROCTRAN row inserted (type 'ODC') |
| Business Rules  | Customer must exist (INQCUST call); up to 20 accounts retrieved via INQACCCU with SYNCONRETURN; each account deleted by iterating DELACC LINK (return code not inspected -- DELACC is trusted to ABEND on failure); CUSTOMER READ with UPDATE+TOKEN then DELETE with TOKEN (optimistic locking); SYSIDERR on READ or DELETE retried up to 100 times with 3-second delay; NOTFND on CUSTOMER READ treated as concurrent deletion (silent skip, continue); any other READ/DELETE error ABENDs with 'WPV6'/'WPV7'; PROCTRAN INSERT failure ABENDs with 'HWPT' NODUMP |
| Data Entities   | CUSTOMER (VSAM KSDS), ACCOUNT (DB2), PROCTRAN (DB2), DELCUS copybook, INQCUST copybook, INQACCCU copybook              |

---

### Debit / Credit Funds

| Property        | Value                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Description     | Applies a teller withdrawal, teller deposit, payment-link debit, or payment-link credit to an existing account balance. Validates the transaction based on account type and facility type (teller vs. payment link). Updates both available and actual balances atomically with a PROCTRAN audit record. |
| Source Programs | BNK1CRA (presentation), DBCRFUN (backend)                                                                              |
| Input           | BMS map BNK1CDM; PAYDBCR COMMAREA (account number, signed amount, facility type)                                       |
| Output          | ACCOUNT DB2 row updated (balances); PROCTRAN row inserted (type 'DEB', 'CRE', 'PDR', or 'PCR'); updated balances returned |
| Business Rules  | Amount is signed PIC S9(10)V99 (negative = debit, positive = credit); COMM-FACILTYPE=496 means payment link; MORTGAGE and LOAN accounts reject all payment-link debits/credits (fail code '4'); payment-link debits check available balance (fail code '3' if insufficient); teller debits bypass balance check; DB2 UPDATE and PROCTRAN INSERT are in the same CICS UoW; PROCTRAN INSERT failure triggers SYNCPOINT ROLLBACK (undoes balance update); ROLLBACK failure causes ABEND 'HROL'; VSAM RLS abends (AFCR/AFCS/AFCT) trigger SYNCPOINT ROLLBACK and soft return; DB2 SQLCODE 923 triggers Storm Drain diagnostic display |
| Data Entities   | ACCOUNT (DB2), PROCTRAN (DB2), PAYDBCR copybook, ACCDB2 copybook                                                       |

---

### Fund Transfer

| Property        | Value                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Description     | Transfers a specified amount between two accounts by debiting the source and crediting the target in DB2. Implements deadlock-safe update ordering (lower account number first). Writes a PROCTRAN record linking source to destination. No overdraft check is performed. |
| Source Programs | BNK1TFN (presentation), XFRFUN (backend)                                                                               |
| Input           | BMS map BNK1TFM; XFRFUN COMMAREA (from account/sort code, to account/sort code, amount)                                |
| Output          | ACCOUNT DB2 rows for both accounts updated; PROCTRAN row inserted (Transfer type, keyed on FROM account); updated balances returned |
| Business Rules  | Amount must be positive (fail code '4' if <= 0); FROM and TO must differ (ABEND 'SAME' if equal); sort code is unconditionally overwritten to installation constant (cross-bank transfers silently fail); lower account number updated first to prevent DB2 deadlocks; TO account not found triggers SYNCPOINT ROLLBACK (fail code '2'); PROCTRAN INSERT failure is logged as data inconsistency and causes ABEND 'WPCD'; DB2 deadlock (-911 / SQLERRD(3)=13172872) retried up to 5 times with 1-second DELAY + SYNCPOINT ROLLBACK; ROLLBACK failure causes ABEND 'HROL' |
| Data Entities   | ACCOUNT (DB2), PROCTRAN (DB2), XFRFUN copybook, ACCDB2 copybook                                                        |

---

### Centralised Abend Logging

| Property        | Value                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Description     | A write-through persistence service invoked by all application programs on unrecoverable errors. Accepts a populated ABNDINFO record via DFHCOMMAREA and writes it to the ABNDFILE VSAM KSDS, providing a single collection point for all application abends. |
| Source Programs | ABNDPROC                                                                                                                |
| Input           | DFHCOMMAREA (ABNDINFO layout: APPLID, TRANID, date, time, abend code, program, RESP, RESP2, SQLCODE, 600-byte freeform text) |
| Output          | ABNDFILE VSAM KSDS record written; key = UNIX microsecond timestamp (8 bytes COMP-3) + CICS task number (4 bytes)      |
| Business Rules  | Program performs no computation or validation; accepts and writes verbatim; VSAM write failure logs four DISPLAY lines to CICS log and returns silently (record abandoned, no re-abend); key uniqueness depends entirely on caller populating ABND-UTIME-KEY and ABND-TASKNO-KEY correctly |
| Data Entities   | ABNDFILE (VSAM KSDS), ABNDINFO copybook                                                                                 |

---

### Utility Services

| Property        | Value                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Description     | Two minimal CICS services that return static configuration values: GETCOMPY returns the application company name ('CICS Bank Sample Application') and GETSCODE returns the configured sort code (987654). Both are intended for use by external callers (e.g., REST API or web UI layers) that need these values without parsing application data. |
| Source Programs | GETCOMPY, GETSCODE                                                                                                      |
| Input           | DFHCOMMAREA (single-field layout)                                                                                       |
| Output          | COMPANY-NAME PIC X(40) or SORTCODE PIC X(6) populated in COMMAREA                                                      |
| Business Rules  | No validation; no database access; immediate EXEC CICS RETURN; literals hardcoded in source; GETCOMPY is called by the Java web UI layer (CompanyNameResource.java) |
| Data Entities   | GETCOMPY copybook (COMPANY-NAME), GETSCODE copybook (SORTCODE), SORTCODE copybook                                       |

---

### Test Data Initialisation

| Property        | Value                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Description     | A batch program that recreates the CBSA application datastores from scratch. Accepts a JCL PARM defining the customer number range, increment, and random seed. Generates synthetic customers (random name, address, DOB, credit score) and 1-5 accounts per customer, writes them to VSAM and DB2, and seeds the CONTROL table counters. This is a destructive operation: existing ACCOUNT and CONTROL rows for the sort code are deleted before any inserts. |
| Source Programs | BANKDATA (batch), plus JCL steps BANKDAT0 and BANKDAT1 (IDCAMS) to recreate VSAM clusters                              |
| Input           | JCL PARM='start,end,step,seed'; no transaction input                                                                    |
| Output          | CUSTOMER VSAM records (one per customer plus control sentinel); ACCOUNT DB2 rows (1-5 per customer); CONTROL DB2 rows (ACCOUNT-LAST, ACCOUNT-COUNT) |
| Business Rules  | END-KEY must be >= START-KEY; STEP-KEY must be non-zero; existing ACCOUNT + CONTROL rows for sort code deleted before insert; each customer gets 1-5 accounts with types ISA/SAVING/CURRENT/LOAN/MORTGAGE in rotation; LOAN and MORTGAGE balances are negative; fixed interest rates per account type (ISA=2.10%, SAVING=1.75%, CURRENT=0.00%, LOAN=17.90%, MORTGAGE=5.25%); last/next statement dates hard-coded to 01.07.2021/01.08.2021; DB2 COMMIT every 1,000 iterations and after each customer's accounts; max customer age boundary year 2000; max account opened year 2014; control sentinel record (sortcode=000000, number=9999999999) written to VSAM |
| Data Entities   | CUSTOMER (VSAM KSDS), ACCOUNT (DB2), CONTROL (DB2), SORTCODE copybook, ACCDB2 copybook, ACCTCTRL copybook, CUSTCTRL copybook |

---

## Capability Map

| #  | Capability                           | Programs                                                     | Complexity | Description                                                                 |
| -- | ------------------------------------ | ------------------------------------------------------------ | ---------- | --------------------------------------------------------------------------- |
| 1  | Navigation and Session Management    | BNKMENU                                                      | Low        | 3270 BMS menu routing and pseudo-conversational session control             |
| 2  | Customer Enquiry                     | BNK1DCS, INQCUST                                             | Low        | VSAM lookup of a single customer record by customer number                  |
| 3  | Customer Creation with Credit Scoring| BNK1CCS, CRECUST, CRDTAGY1-5                                 | High       | Async multi-agency credit check, counter serialisation, VSAM write          |
| 4  | Account Enquiry                      | BNK1DAC, BNK1UAC, INQACC                                     | Low        | DB2 cursor lookup of a single account; last-account sentinel mode           |
| 5  | Accounts Enquiry by Customer         | BNK1CCA, INQACCCU                                            | Low        | DB2 cursor returning up to 20 accounts for a customer                       |
| 6  | Account Creation                     | BNK1CAC, CREACC                                              | High       | DB2 CONTROL counter management, 10-account limit, multi-table atomic insert |
| 7  | Account Update                       | BNK1UAC, UPDACC, INQACC                                      | Low        | Three-field DB2 UPDATE; no PROCTRAN; minimal validation                     |
| 8  | Account Deletion                     | BNK1DAC, DELACC                                              | Medium     | DB2 DELETE with PROCTRAN balance-at-deletion audit record                   |
| 9  | Customer Update                      | BNK1DCS, UPDCUST                                             | Low        | VSAM REWRITE of customer attributes                                         |
| 10 | Customer Deletion (Full Cascade)     | BNK1DCS, DELCUS, INQCUST, INQACCCU, DELACC                   | High       | Cascading delete with token locking, SYSIDERR retry, SYNCONRETURN           |
| 11 | Debit / Credit Funds                 | BNK1CRA, DBCRFUN                                             | Medium     | Signed balance update with facility-type routing and PROCTRAN atomicity     |
| 12 | Fund Transfer                        | BNK1TFN, XFRFUN                                              | High       | Deadlock-safe two-account DB2 update with retry loop and PROCTRAN           |
| 13 | Centralised Abend Logging            | ABNDPROC                                                     | Low        | Write-through VSAM persistence for all application abend diagnostics        |
| 14 | Utility Services                     | GETCOMPY, GETSCODE                                           | Low        | Static value lookups for company name and sort code                         |
| 15 | Test Data Initialisation             | BANKDATA (batch), IDCAMS (JCL)                               | Medium     | Batch destructive reload of VSAM and DB2 datastores with synthetic data     |

---

## Gaps and Assumptions

| Capability                           | Gap / Assumption                                                                                                                          | Confidence | Rationale                                                                                                                               |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Customer Creation with Credit Scoring | Credit agency stubs (CRDTAGY1-5) are explicitly dummy implementations; real credit bureau integration is not present in the source         | high       | Program comments and random-score logic confirm stub nature                                                                             |
| Account Enquiry                      | GETCOMPY and GETSCODE callers outside the COBOL source are not analysed; the Java CompanyNameResource.java is referenced but not in scope  | high       | GETCOMPY business-rules file explicitly notes Java web UI caller                                                                        |
| Utility Services                     | GETCOMPY is called by a Java web UI layer; other external consumers of GETSCODE are unknown                                               | medium     | No COBOL callers found in source; CSD registration implies external API use                                                             |
| Fund Transfer                        | No overdraft limit enforcement exists in XFRFUN; the program explicitly documents this omission                                           | high       | Business rules file and source comments confirm 'No checking is made on overdraft limits'                                               |
| Accounts Enquiry by Customer         | Hard limit of 20 accounts per customer in INQACCCU COMMAREA; BANKDATA rule 16 mentions a design comment of max 10 from alternate-key index | medium     | CREACC enforces > 9 accounts as the operational limit; INQACCCU ODO is dimensioned 20 as a technical maximum                            |
| Test Data Initialisation             | Statement dates are hard-coded to 01.07.2021 / 01.08.2021 in BANKDATA; generated data will not reflect current dates unless modified      | high       | BANKDATA business-rules rule 25 and 26 confirm hardcoded literals                                                                       |
| Customer Deletion (Full Cascade)     | DELCUS does not inspect DELACC return code; account-deletion failures are silently delegated to DELACC ABENDs                             | high       | Confirmed by DELCUS business-rules rule 7 and data integrity note                                                                       |
| Orphan copybooks (NEWACCNO, NEWCUSNO, PROCISRT, CONTDB2, CONTROLI) | These copybooks define service interfaces not found in any analysed program; they may reference programs outside this codebase | low | Identified as orphans in copybook inventory; no callers in scope |
