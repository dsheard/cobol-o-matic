---
type: test-specifications
subtype: data-contracts
status: draft
confidence: high
last_pass: 5
---

# Data Contract Tests

Data format, invariant, and boundary tests for each data store. These tests verify that the modernized system preserves data semantics regardless of storage technology changes (e.g. VSAM to database, flat file to API).

---

## File Contracts

| File / Dataset | Business Purpose | Record Layout | Producers | Consumers | Key Fields |
| -------------- | ---------------- | ------------- | --------- | --------- | ---------- |
| CUSTOMER (VSAM KSDS) | Customer master data | CUSTOMER copybook (~265 bytes) | BANKDATA (batch init), CRECUST (create), UPDCUST (update) | INQCUST (read), UPDCUST (read+update), DELCUS (read+delete), CRECUST (control record) | CUSTOMER-SORTCODE (9(6)) + CUSTOMER-NUMBER (9(10)) = 16-byte composite key |
| ABNDFILE (VSAM KSDS) | Centralised abend/error log | ABNDINFO copybook (~655 bytes) | ABNDPROC | Monitoring/operations only | ABND-UTIME-KEY (S9(15) COMP-3, 8 bytes) + ABND-TASKNO-KEY (9(4), 4 bytes) = 12-byte composite key |

---

### CUSTOMER Contract Tests

| # | Invariant | Test | Derived From |
| - | --------- | ---- | ------------ |
| 1 | Eye-catcher must be 'CUST' on all customer data records | Read a customer record and assert the first 4 bytes equal the ASCII/EBCDIC encoding of 'CUST' | CRECUST business rule 37: CUSTOMER-EYECATCHER set to 'CUST' before WRITE |
| 2 | Key is always sortcode 987654 concatenated with a 10-digit customer number | Read any customer record; extract bytes 5-10 (sort code) and bytes 11-20 (customer number); assert sort code = '987654' | INQCUST BR-27, CRECUST BR-38; SORTCODE copybook constant |
| 3 | Customer number is unique across all customer records | Read all records; assert no two records share the same customer number (for the same sort code) | CRECUST BR-29: counter incremented by 1 for each new customer; ENQ serialises allocation |
| 4 | Customer number must be in the range 1 to 9999999998 | Read all customer data records (not the control record); assert customer number >= 1 and <= 9999999998 | PIC 9(10) range; BR-INQCUST-1 (sentinel 9999999999 is the control record marker, not a customer) |
| 5 | Customer name field length is exactly 60 characters (padded with spaces) | Read any customer record; assert name field is 60 bytes | CUSTOMER copybook: CUSTOMER-NAME PIC X(60) |
| 6 | Customer address field length is exactly 160 characters (padded with spaces) | Read any customer record; assert address field is 160 bytes | CUSTOMER copybook: CUSTOMER-ADDRESS PIC X(160) |
| 7 | Date of birth is stored as 8 numeric digits DDMMYYYY | Read a customer record; assert CUSTOMER-DATE-OF-BIRTH is exactly 8 numeric characters | CUSTOMER copybook: CUSTOMER-DATE-OF-BIRTH PIC 9(8); CRECUST BR-DOB-stored-with-slashes note |
| 8 | Credit score is a 3-digit numeric value in range 0-999 | Read any customer record; assert CUSTOMER-CREDIT-SCORE is 3 numeric digits; value 0-999 | CUSTOMER copybook: CUSTOMER-CREDIT-SCORE PIC 999 |
| 9 | Credit score review date is stored as 8 numeric digits DDMMYYYY | Read a customer record; assert CUSTOMER-CS-REVIEW-DATE is 8 numeric characters | CUSTOMER copybook: CUSTOMER-CS-REVIEW-DATE PIC 9(8) |
| 10 | Control record exists with sort code 000000 and number 9999999999 | Query the CUSTOMER store for the record with key sort code = '000000', number = '9999999999'; assert it exists and has eye-catcher 'CTRL' | CRECUST BR-41, BANKDATA; CUSTCTRL copybook |
| 11 | Control record LAST-CUSTOMER-NUMBER equals or exceeds the maximum customer number in data records | Read all customer data records; read control record LAST-CUSTOMER-NUMBER; assert control value >= max customer number in data records | CRECUST BR-29, BR-41: counter only increments, never decrements |
| 12 | Total customer count in control record >= number of customer data records | Assert control record NUMBER-OF-CUSTOMERS >= count of customer data records | CRECUST BR-41: control count incremented on each successful write |
| 13 | Customer name must begin with a recognised title or be blank | Read all customer records; for each, extract the first space-delimited token of CUSTOMER-NAME; assert it is one of: Professor, Mr, Mrs, Miss, Ms, Dr, Drs, Lord, Sir, Lady, or blank | CRECUST BR-1, UPDCUST BR-1: title is validated before any write |
| 14 | Sort code on every customer record equals the installation constant 987654 | Read all customer data records; assert CUSTOMER-SORTCODE = '987654' | CRECUST BR-38, INQCUST BR-27: sort code is always the installation constant |
| 15 | VSAM customer control sentinel NUMBER-OF-CUSTOMERS and LAST-CUSTOMER-NUMBER fields are both zero when written by BANKDATA | Read the VSAM sentinel record (sort code '000000', number '9999999999') after a BANKDATA batch run; assert NUMBER-OF-CUSTOMERS = 0 and LAST-CUSTOMER-NUMBER = 0 | BANKDATA BR-34, BR-35: customer count is tallied in memory but never written to the sentinel record; no DB2 CONTROL row is inserted for customer count |
| 16 | Customer name stored with canonical mixed-case title after creation via presentation layer | Read a customer record created via BNK1CCS with uppercase title (e.g. 'MR'); assert stored name begins with canonical form (e.g. 'Mr ') | BR-BNK1CCS-16: BNK1CCS normalises 'MR' to 'Mr' before LINK to CRECUST; stored record carries normalised form |

---

### ABNDFILE Contract Tests

| # | Invariant | Test | Derived From |
| - | --------- | ---- | ------------ |
| 1 | Each record has a unique composite key (timestamp + task number) | Read all records; assert no duplicate (ABND-UTIME-KEY, ABND-TASKNO-KEY) pairs | ABNDPROC BR-ABNDPROC-4: key is caller-populated; intended to be unique by construction |
| 2 | ABND-CODE field is exactly 4 characters | Read any record; assert ABND-CODE is exactly 4 bytes | ABNDINFO copybook: ABND-CODE PIC X(4) |
| 3 | ABND-APPLID is exactly 8 characters | Read any record; assert ABND-APPLID is exactly 8 bytes | ABNDINFO copybook: ABND-APPLID PIC X(8) |
| 4 | ABND-FREEFORM diagnostic text is at most 600 characters | Read any record; assert ABND-FREEFORM <= 600 bytes | ABNDINFO copybook: ABND-FREEFORM PIC X(600) |
| 5 | ABND-TRANID is exactly 4 characters | Read any record; assert ABND-TRANID is exactly 4 bytes | ABNDINFO copybook: ABND-TRANID PIC X(4) |
| 6 | ABND-TIME seconds field contains minutes value (known defect) | Read any abend record written by the application; assert ABND-TIME format is HH:MM:MM (not HH:MM:SS); the seconds position mirrors the minutes value | ABND-TIME-defect: pervasive source defect across all programs that populate ABNDINFO -- FORMATTIME MINUTES(WS-ABND-MINUTES) is moved to both MM and SS positions; affects audit record quality but not functional logic |

---

## Database Contracts

| Table / Segment | Business Purpose | Writers | Readers | Key Columns |
| --------------- | ---------------- | ------- | ------- | ----------- |
| ACCOUNT | Bank account master | BANKDATA (INSERT), CREACC (INSERT), DELACC (DELETE), UPDACC (UPDATE), DBCRFUN (UPDATE), XFRFUN (UPDATE) | INQACC, INQACCCU, DELACC, UPDACC, DBCRFUN, XFRFUN | ACCOUNT_SORTCODE (CHAR(6)), ACCOUNT_NUMBER (CHAR(8)) |
| PROCTRAN | Transaction audit log | CREACC, CRECUST, DELACC, DELCUS, DBCRFUN, XFRFUN | Reporting/audit consumers (no COBOL reader identified) | PROCTRAN_SORTCODE (CHAR(6)), PROCTRAN_NUMBER (CHAR(8)), PROCTRAN_DATE, PROCTRAN_TIME, PROCTRAN_REF |
| CONTROL | Sequence counters | BANKDATA (INSERT), CREACC (UPDATE) | CREACC (SELECT) | CONTROL_NAME (CHAR(32)) |

---

### ACCOUNT Contract Tests

| # | Invariant | Test | Derived From |
| - | --------- | ---- | ------------ |
| 1 | Eye-catcher must be 'ACCT' on every account row | SELECT ACCOUNT_EYECATCHER from all rows; assert all equal 'ACCT' | CREACC BR-21, BANKDATA: eye-catcher always set to 'ACCT' before INSERT |
| 2 | Sort code is always '987654' on every account row | SELECT ACCOUNT_SORTCODE; assert all = '987654' | CREACC BR-22, UPDACC BR-6, DBCRFUN BR-2, XFRFUN BR-35: sort code is the installation constant |
| 3 | Account number is 8 numeric characters, non-zero | SELECT ACCOUNT_NUMBER; assert all are 8 digits and not '00000000' | CREACC BR-14, BR-22: account number derived from sequential counter; minimum = 1 |
| 4 | Account type is one of the five allowed values | SELECT ACCOUNT_TYPE from all rows; assert each is one of: 'ISA     ', 'MORTGAGE', 'SAVING  ', 'CURRENT ', 'LOAN    ' (right-padded to 8 chars) | CREACC BR-5: type validated before INSERT; BANKDATA uses same five types |
| 5 | Account number is unique within a sort code | SELECT ACCOUNT_SORTCODE, ACCOUNT_NUMBER; assert no duplicates | CREACC BR-8, BR-14: ENQ serialises counter; counter incremented atomically |
| 6 | Customer number on account must reference an existing customer | For each ACCOUNT_CUSTOMER_NUMBER, verify a CUSTOMER record exists with matching number and sort code 987654 | Referential integrity implied by CREACC BR-1 (customer existence checked before account creation) |
| 7 | Interest rate is >= 0.00 | SELECT ACCOUNT_INTEREST_RATE; assert all >= 0.00 | CREACC: BANKDATA sets fixed positive rates; UPDACC silently strips negative sign from unsigned PIC |
| 8 | Account opened date is a valid date | SELECT ACCOUNT_OPENED; assert all rows have a valid YYYY-MM-DD date value; no nulls | CREACC BR-23: opened date set via CICS clock at insert time |
| 9 | Last statement date <= next statement date | SELECT ACCOUNT_LAST_STATEMENT, ACCOUNT_NEXT_STATEMENT; assert last <= next | CREACC BR-23, BR-24: last statement = opened date; next = opened + 30 days |
| 10 | Actual balance equals available balance at quiescent state | At quiescent state (no transactions in flight), SELECT ACCOUNT_AVAILABLE_BALANCE, ACCOUNT_ACTUAL_BALANCE; for standard accounts assert available = actual | DBCRFUN BR-16, BR-17: both balances updated by the same signed add; they start equal and are modified together |
| 11 | LOAN and MORTGAGE accounts may have negative balances; other account types may also go negative in production data via teller debit operations that bypass the available-balance check | SELECT balances WHERE ACCOUNT_TYPE NOT IN ('LOAN','MORTGAGE'); verify no negative available balance in data written solely by BANKDATA or payment-link operations; note: teller debit (COMM-FACILTYPE ≠ 496) bypasses the funds check per BR-DBCRFUN-10 and may legally produce negative balances on any account type | BANKDATA: LOAN/MORTGAGE balances initialised as negative; other types initialised >= 0; BR-DBCRFUN-10: teller debit bypasses available-balance check (confirmed by behavioral test T-111: CURRENT account debited below zero by teller, accepted as happy-path); non-LOAN/MORTGAGE negative balances are therefore valid in production if introduced by teller debit |
| 12 | Overdraft limit is >= 0 | SELECT ACCOUNT_OVERDRAFT_LIMIT; assert all >= 0 | PIC 9(8) (unsigned): cannot be negative |
| 13 | Account created via BNK1CAC with omitted overdraft limit has overdraft = 0 | Create account via BNK1CAC with overdraft field blank; SELECT ACCOUNT_OVERDRAFT_LIMIT for the new account; assert = 0 | BR-BNK1CAC-27: blank overdraft field defaults to ZERO before LINK to CREACC |
| 14 | Account type stored with canonical 8-character padded value | SELECT ACCOUNT_TYPE; assert each value is exactly 8 characters with trailing spaces; e.g. 'ISA     ' not 'ISA' | BR-BNK1CAC-15 through BR-BNK1CAC-19: BNK1CAC normalises all account type inputs to canonical padded form before LINK to CREACC |
| 15 | LOAN and MORTGAGE accounts rejected for interest rate = 0 via update screen | Attempt to update a LOAN or MORTGAGE account via the update screen with interest rate '0000.00'; assert request is rejected at the screen layer and no DB2 UPDATE is issued | BR-BNK1UAC-23: VD010 line 667 rejects zero interest rate for LOAN and MORTGAGE account types |

---

### PROCTRAN Contract Tests

| # | Invariant | Test | Derived From |
| - | --------- | ---- | ------------ |
| 1 | Eye-catcher is always 'PRTR' | SELECT PROCTRAN_EYECATCHER; assert all = 'PRTR' | CREACC BR-34, CRECUST BR-45, DELACC BR-12, DELCUS BR-20, DBCRFUN BR-25, XFRFUN BR-25: all writers set eyecatcher to 'PRTR' (88-level PROC-TRAN-VALID in PROCTRAN.cpy) |
| 2 | Transaction type is one of the known COBOL-tier codes | SELECT PROCTRAN_TYPE; assert each is one of: 'OCC' (branch new customer), 'OCA' (branch new account), 'ODA' (branch account deleted), 'ODC' (branch customer deleted), 'DEB' (teller withdrawal), 'CRE' (teller deposit), 'PDR' (payment link debit), 'PCR' (payment link credit), 'TFR' (fund transfer) | DBCRFUN BR-21 through BR-24, CREACC BR-31, CRECUST BR-44, DELACC BR-14, DELCUS BR-22, XFRFUN BR-25: type codes derived from 88-level values in PROCTRAN.cpy (PROC-TY-BRANCH-CREATE-CUSTOMER='OCC', PROC-TY-BRANCH-CREATE-ACCOUNT='OCA', PROC-TY-BRANCH-DELETE-ACCOUNT='ODA', PROC-TY-BRANCH-DELETE-CUSTOMER='ODC', PROC-TY-DEBIT='DEB', PROC-TY-CREDIT='CRE', PROC-TY-PAYMENT-DEBIT='PDR', PROC-TY-PAYMENT-CREDIT='PCR', PROC-TY-TRANSFER='TFR') |
| 3 | Sort code on every PROCTRAN row is '987654' | SELECT PROCTRAN_SORTCODE; assert all = '987654' | All writers use the installation sort code constant |
| 4 | For account-creation records (type 'OCA'), amount must be zero | SELECT PROCTRAN_AMOUNT WHERE PROCTRAN_TYPE = 'OCA'; assert all = 0 | CREACC BR-32: PROCTRAN amount for account creation is zero |
| 5 | For customer-creation records (type 'OCC'), amount must be zero | SELECT PROCTRAN_AMOUNT WHERE PROCTRAN_TYPE = 'OCC'; assert all = 0 | CRECUST BR-46: account number is zeros, amount not set to non-zero |
| 6 | For customer-deletion records (type 'ODC'), amount must be zero | SELECT PROCTRAN_AMOUNT WHERE PROCTRAN_TYPE = 'ODC'; assert all = 0 | DELCUS BR-23: amount = ZEROS for customer delete |
| 7 | For account-deletion records (type 'ODA'), amount must equal the actual balance at deletion time | For each 'ODA' record, the PROCTRAN_AMOUNT must match the actual balance recorded at the moment of deletion | DELACC BR-16: PROCTRAN amount = ACCOUNT-ACT-BAL-STORE saved from SELECT before DELETE |
| 8 | Date and time are populated on every row | SELECT PROCTRAN_DATE, PROCTRAN_TIME; assert neither is null or all-spaces | All writers call CICS ASKTIME/FORMATTIME at write time |
| 9 | Reference field contains a numeric task-number value | SELECT PROCTRAN_REF; assert each is a 12-character string representing a positive integer (CICS task number) | CRECUST BR-47, CREACC BR-35, DELACC BR-17, DELCUS, DBCRFUN BR-26, XFRFUN BR-28: all populate from EIBTASKN |
| 10 | For teller debit records (type 'DEB'), description is 'COUNTER WTHDRW' | SELECT PROCTRAN_DESC WHERE PROCTRAN_TYPE = 'DEB'; assert first 14 chars = 'COUNTER WTHDRW' | DBCRFUN BR-21 |
| 11 | For teller credit records (type 'CRE'), description is 'COUNTER RECVED' | SELECT PROCTRAN_DESC WHERE PROCTRAN_TYPE = 'CRE'; assert first 14 chars = 'COUNTER RECVED' | DBCRFUN BR-23 |
| 12 | Customer-creation PROCTRAN account number is all zeros | SELECT PROCTRAN_NUMBER WHERE PROCTRAN_TYPE = 'OCC'; assert all = '00000000' | CRECUST BR-46: HV-PROCTRAN-ACC-NUMBER = ZEROS for customer creation (no account yet) |
| 13 | Fund-transfer records (type 'TFR') are keyed on the FROM account | SELECT PROCTRAN_NUMBER WHERE PROCTRAN_TYPE = 'TFR'; assert PROCTRAN_NUMBER matches the FROM account number, not the TO account | XFRFUN BR-27: WTPD010 line 1581 -- HV-PROCTRAN-ACC-NUMBER = COMM-FACCNO (FROM account) |
| 14 | Fund-transfer description encodes the TO sort code and TO account number | SELECT PROCTRAN_DESC WHERE PROCTRAN_TYPE = 'TFR'; assert bytes 27-32 are a numeric sort code and bytes 33-40 are an 8-digit account number matching the TO account | XFRFUN BR-26: WTPD010 line 1610 -- PROC-TRAN-DESC-XFR-SORTCODE = COMM-TSCODE; PROC-TRAN-DESC-XFR-ACCOUNT = COMM-TACCNO |
| 15 | No PROCTRAN record exists for account update operations | After an account update via UPDACC, verify no new PROCTRAN row was inserted with the updated account number at the time of the operation | BR-UPDACC-3: UPDACC procedure division contains no PROCTRAN INSERT; absence of audit record is by design |
| 16 | No PROCTRAN record exists for customer update operations | After a customer update via UPDCUST, verify no new PROCTRAN row was inserted for that customer number at the time of the operation | BR-UPDCUST-18: UPDCUST procedure division contains no PROCTRAN INSERT; absence of audit record is by design |

---

### CONTROL Contract Tests

| # | Invariant | Test | Derived From |
| - | --------- | ---- | ------------ |
| 1 | ACCOUNT-LAST row must exist for the installation sort code | SELECT CONTROL_VALUE_NUM FROM CONTROL WHERE CONTROL_NAME = '987654-ACCOUNT-LAST'; assert row exists and value >= 0 | CREACC BR-12: row must be readable before any account creation; BANKDATA seeds it |
| 2 | ACCOUNT-COUNT row must exist | SELECT CONTROL_VALUE_NUM FROM CONTROL WHERE CONTROL_NAME = '987654-ACCOUNT-COUNT'; assert row exists | CREACC BR-17: count row must be selectable |
| 3 | ACCOUNT-LAST value >= actual number of account rows | SELECT CONTROL_VALUE_NUM WHERE CONTROL_NAME = '987654-ACCOUNT-LAST'; compare to COUNT(*) FROM ACCOUNT; assert control value >= count | CREACC BR-14: counter is incremented before INSERT; on failure INSERT does not occur but counter is not rolled back |
| 4 | ACCOUNT-COUNT value >= 0 | Assert CONTROL_VALUE_NUM for ACCOUNT-COUNT is non-negative | CREACC BR-19: incremented by 1 on each successful account creation |
| 5 | CONTROL_NAME is unique (primary key) | SELECT COUNT(*) GROUP BY CONTROL_NAME; assert no group > 1 | CONTROL_NAME is the key column for SELECT and UPDATE operations |
| 6 | No CUSTOMER-LAST or CUSTOMER-COUNT rows exist in CONTROL | SELECT * FROM CONTROL WHERE CONTROL_NAME LIKE '%CUSTOMER%'; assert 0 rows | BANKDATA BR-35: customer counter is tallied in memory only; no DB2 CONTROL rows are inserted for customers; only account-last and account-count rows exist |

---

## Message Contracts

| Queue / Channel | Business Purpose | Producers | Consumers | Message Format |
| --------------- | ---------------- | --------- | --------- | -------------- |
| CIPCREDCHANN (CICS Channel) | Async credit-score exchange | CRECUST (containers CIPA-CIPE), CRDTAGY1-5 (response scores) | CRDTAGY1-5 (read request), CRECUST (FETCH response scores) | WS-CONT-IN structure: eyecatcher, sort code, customer number, name, address, DOB, credit score, review date, success flag |

---

### CIPCREDCHANN Contract Tests

| # | Invariant | Test | Derived From |
| - | --------- | ---- | ------------ |
| 1 | Exactly 5 containers (CIPA, CIPB, CIPC, CIPD, CIPE) are PUT per customer creation attempt | Observe or intercept the credit-scoring channel; assert each creation attempt puts exactly 5 containers | CRECUST BR-8, BR-10: loop iterates from 1 to 5; containers named CIPA through CIPE |
| 2 | Each container carries the same customer data as the creation request | Verify that each container's customer number, name, DOB, and sort code match the inputs provided to the creation request | CRECUST BR-10, CRECUST calc: DFHCOMMAREA pushed into each container before child transaction starts |
| 3 | Credit score returned in each container is in range 1-999 | CRDTAGY1-5 each return a simulated credit score; verify each returned score is between 1 and 999 inclusive | CRDTAGY programs: random score generation; PIC 999 range; CRDTAGY1 BR-3 formula ((999-1)*RANDOM)+1 |
| 4 | Averaged credit score is integer division of total across received responses | Given N responses with scores S1..SN, verify final credit score = floor(SUM(S1..SN) / N) | CRECUST BR-calc-1: COMPUTE using integer division (no ROUNDED) |
| 5 | If no agency responses are received, credit score is set to 0 | Simulate all 5 agencies failing to respond; assert returned credit score = 0 and operation fails | CRECUST BR-17: zero retrieved count causes error |
| 6 | Credit score review date is set 1-20 calendar days after today | After a successful customer creation, assert review date is within [today+1, today+20] | CRECUST BR-calc-3: random offset 1-20 days from EIBTASKN seed |
| 7 | An individual agency may delay up to 3 seconds and may not respond before parent times out | In a test with all 5 agencies active, the parent (CRECUST) waits up to 3 seconds; any agency that delays 3 seconds may not have its score included in the average | CRDTAGY1 BR-1: delay = ((3-1)*RANDOM(SEED))+1; delay of 3 seconds may cause parent to proceed without this score; BR-6: 1-in-4 chance of exceeding parent timeout |

---

## Data Invariants

Cross-store consistency rules that must hold across the modernized system:

| # | Invariant | Stores Involved | Test | Derived From |
| - | --------- | --------------- | ---- | ------------ |
| 1 | Every account row references a customer that exists in the customer store | ACCOUNT (DB2) + CUSTOMER (VSAM) | For each ACCOUNT_CUSTOMER_NUMBER, verify a CUSTOMER record exists with sort code 987654 and that customer number | CREACC BR-1: customer existence is verified before any account INSERT |
| 2 | Every 'ODA' (account-delete) PROCTRAN row references an account that no longer exists in ACCOUNT | PROCTRAN (DB2) + ACCOUNT (DB2) | For each PROCTRAN row with type 'ODA', verify no ACCOUNT row exists with the matching PROCTRAN_NUMBER and sort code | DELACC: DELETE FROM ACCOUNT is performed before PROCTRAN INSERT; in the same unit of work |
| 3 | After a customer deletion, no ACCOUNT rows reference the deleted customer | ACCOUNT (DB2) + CUSTOMER (VSAM) | After a successful customer deletion, SELECT from ACCOUNT where ACCOUNT_CUSTOMER_NUMBER = deleted customer number; assert 0 rows | DELCUS BR-4, BR-5: all accounts deleted before customer deleted |
| 4 | CONTROL ACCOUNT-LAST value is always >= the maximum ACCOUNT_NUMBER in the ACCOUNT table | CONTROL (DB2) + ACCOUNT (DB2) | SELECT MAX(ACCOUNT_NUMBER) FROM ACCOUNT; compare to CONTROL ACCOUNT-LAST counter; assert control >= max | CREACC BR-14: counter incremented before INSERT; INSERT may fail but counter is not rolled back |
| 5 | Every PROCTRAN row with type 'OCC' corresponds to an existing customer in the customer store | PROCTRAN (DB2) + CUSTOMER (VSAM) | For each PROCTRAN 'OCC' row, extract customer number from PROCTRAN_DESC bytes 7-16 (PROC-DESC-CRECUS-CUSTOMER); verify customer exists in CUSTOMER store | CRECUST BR-48: PROCTRAN description encodes the customer number using PROC-TRAN-DESC-CRECUS layout in PROCTRAN.cpy |
| 6 | Every PROCTRAN row with type 'OCA' or financial types corresponds to an account that existed at some point | PROCTRAN (DB2) + ACCOUNT (DB2) | For each 'OCA' row, PROCTRAN_NUMBER should match an existing account (if not yet deleted) or have a corresponding 'ODA' row | CREACC BR-37, DELACC BR-14: account number and sort code are set on all account-level PROCTRAN rows |
| 7 | The customer store control record LAST-CUSTOMER-NUMBER is always >= the maximum customer number in data records | CUSTOMER (VSAM) - control record + data records | Read the control record (key 000000/9999999999); compare LAST-CUSTOMER-NUMBER to MAX(CUSTOMER-NUMBER) across all data records; assert control >= max | CRECUST BR-29, BR-41: counter only increases |
| 8 | Total ACCOUNT row count is approximated by CONTROL ACCOUNT-COUNT; count may exceed actual rows after deletions | ACCOUNT (DB2) + CONTROL (DB2) | COUNT(*) from ACCOUNT vs CONTROL_VALUE_NUM for ACCOUNT-COUNT; note: DELACC does not decrement the count, so count may exceed actual rows over time | CREACC BR-19: count incremented on creation; DELACC does not decrement |
| 9 | BANKDATA batch run leaves no CUSTOMER-LAST or CUSTOMER-COUNT rows in DB2 CONTROL | CONTROL (DB2) + CUSTOMER (VSAM) | After a full BANKDATA batch run, SELECT from CONTROL WHERE CONTROL_NAME LIKE '%CUSTOMER%'; assert 0 rows; customer counts exist only in-memory during batch execution | BANKDATA BR-34, BR-35: NUMBER-OF-CUSTOMERS accumulated in memory is never persisted to DB2; only account counters are written |
| 10 | Customer name canonical form is preserved end-to-end from BNK1CCS input to CUSTOMER VSAM record | CUSTOMER (VSAM) | Create customer via BNK1CCS with mixed-case or uppercase title (e.g. 'MR'); retrieve stored CUSTOMER record via INQCUST; assert stored name begins with canonical title 'Mr ' (not 'MR' or 'mr') | BR-BNK1CCS-16: BNK1CCS normalises title in the presentation layer before LINK to CRECUST; the normalised value is stored in VSAM without further transformation |
| 11 | No PROCTRAN record exists for any account update operation; ACCOUNT_TYPE, ACCOUNT_INTEREST_RATE, ACCOUNT_OVERDRAFT_LIMIT may be updated without leaving an audit trail | PROCTRAN (DB2) + ACCOUNT (DB2) | Perform account update via UPDACC; scan PROCTRAN for any row referencing the updated account at the time of update; assert no such row | BR-UPDACC-3: UPDACC contains no PROCTRAN INSERT in its procedure division; absence of audit is by design |
| 12 | No PROCTRAN record exists for any customer update operation; CUSTOMER-NAME and CUSTOMER-ADDRESS may be changed without leaving an audit trail | PROCTRAN (DB2) + CUSTOMER (VSAM) | Perform customer update via UPDCUST; scan PROCTRAN for any row referencing the updated customer at the time of update; assert no such row | BR-UPDCUST-18: UPDCUST contains no PROCTRAN INSERT in its procedure division; absence of audit is by design |
