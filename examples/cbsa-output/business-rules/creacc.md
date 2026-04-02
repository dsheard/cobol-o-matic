---
type: business-rules
program: CREACC
program_type: online
status: draft
confidence: high
last_pass: 5
calls:
- INQCUST
- INQACCCU
- ABNDPROC
called_by:
- BNK1CAC
uses_copybooks:
- ABNDINFO
- ACCDB2
- ACCOUNT
- ACCTCTRL
- CREACC
- CUSTOMER
- INQACCCU
- INQCUST
- PROCDB2
- PROCTRAN
- SORTCODE
reads: []
writes: []
db_tables:
- ACCOUNT
- CONTROL
- PROCTRAN
transactions: []
mq_queues: []
---

# CREACC -- Business Rules

## Program Purpose

CREACC creates a new bank account record in the DB2 ACCOUNT table. It validates that the customer exists, enforces a maximum of 10 accounts per customer, validates the requested account type, and then acquires a new unique account number by enqueueing a CICS named counter (resource name `CBSAACCT` + sort-code + 2 spaces = 16 chars), incrementing the `ACCOUNT-LAST` control row in the CONTROL table, and updating the `ACCOUNT-COUNT` control row. On successful INSERT into ACCOUNT it writes an audit record to PROCTRAN (type `OCA`) and dequeues the named counter before returning the new account details to the caller via DFHCOMMAREA. If the ACCOUNT INSERT or PROCTRAN INSERT fails, the named counter is dequeued and the program abends.

## Input / Output

| Direction | Resource        | Type | Description                                                                 |
| --------- | --------------- | ---- | --------------------------------------------------------------------------- |
| IN/OUT    | DFHCOMMAREA     | CICS | Input: COMM-CUSTNO, COMM-ACC-TYPE, COMM-INT-RT, COMM-OVERDR-LIM, COMM-AVAIL-BAL, COMM-ACT-BAL. Output: COMM-NUMBER, COMM-SORTCODE, COMM-OPENED, COMM-LAST-STMT-DT, COMM-NEXT-STMT-DT, COMM-EYECATCHER ('ACCT'), COMM-SUCCESS, COMM-FAIL-CODE. |
| IN        | INQCUST         | CICS | Linked to verify that the requested customer exists before account creation. |
| IN        | INQACCCU        | CICS | Linked (SYNCONRETURN) to count existing accounts for the customer (max-10 enforcement). |
| IN/OUT    | ACCOUNT (DB2)   | DB2  | New account row is INSERTed on success.                                     |
| IN/OUT    | CONTROL (DB2)   | DB2  | SELECTed and UPDATEd for `ACCOUNT-LAST` (next account number) and `ACCOUNT-COUNT` (running account count). |
| OUT       | PROCTRAN (DB2)  | DB2  | Audit record INSERTed with transaction type `OCA` on successful account creation. |
| OUT       | ABNDPROC        | CICS | Linked to record abend details whenever a fatal DB2 or ENQ error occurs. WS-ABEND-PGM = 'ABNDPROC'. |

## Business Rules

### Validation -- Customer Existence

| #  | Rule                             | Condition                                                                              | Action                                                                                        | Source Location |
| -- | -------------------------------- | -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | --------------- |
| 1  | Customer must exist              | EIBRESP NOT = DFHRESP(NORMAL) after CICS LINK to INQCUST OR INQCUST-INQ-SUCCESS NOT = 'Y' | Set COMM-SUCCESS = 'N', COMM-FAIL-CODE = '1', PERFORM GET-ME-OUT-OF-HERE (EXEC CICS RETURN)  | P010, line 314  |

### Validation -- Account Count Limit

| #  | Rule                             | Condition                                                                              | Action                                                                                        | Source Location |
| -- | -------------------------------- | -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | --------------- |
| 2  | INQACCCU CICS link must succeed  | WS-CICS-RESP NOT = DFHRESP(NORMAL) after CICS LINK to INQACCCU                        | DISPLAY 'Error counting accounts', set COMM-SUCCESS = 'N', COMM-FAIL-CODE = '9', return     | P010, line 329  |
| 3  | INQACCCU must report success     | COMM-SUCCESS IN INQACCCU-COMMAREA = 'N'                                                | DISPLAY 'Error counting accounts', set COMM-SUCCESS = 'N', COMM-FAIL-CODE = '9', return     | P010, line 338  |
| 4  | Maximum 10 accounts per customer | NUMBER-OF-ACCOUNTS IN INQACCCU-COMMAREA > 9                                            | Set COMM-SUCCESS = 'N', COMM-FAIL-CODE = '8', PERFORM GET-ME-OUT-OF-HERE                    | P010, line 347  |

Note: CAC010 initialises NUMBER-OF-ACCOUNTS to 20 before the LINK as the maximum input parameter to INQACCCU. The actual count is returned by INQACCCU and then checked against > 9 in P010.

### Validation -- Account Type

| #  | Rule                                    | Condition                                                                                                                                                                                           | Action                                                                       | Source Location        |
| -- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------- |
| 5  | Account type must be one of five values | EVALUATE TRUE: COMM-ACC-TYPE(1:3) = 'ISA' OR COMM-ACC-TYPE(1:8) = 'MORTGAGE' OR COMM-ACC-TYPE(1:6) = 'SAVING' OR COMM-ACC-TYPE(1:7) = 'CURRENT' OR COMM-ACC-TYPE(1:4) = 'LOAN' -- any match is valid | Set COMM-SUCCESS = 'Y'                                                      | ATC010, line 1215      |
| 6  | Invalid account type                    | WHEN OTHER (none of the five valid values matched)                                                                                                                                                  | Set COMM-SUCCESS = 'N', COMM-FAIL-CODE = 'A', return via P010 check at 359 | ATC010, line 1222      |

### Routing -- Account Type Check Result

| #  | Rule                                        | Condition                             | Action                            | Source Location |
| -- | ------------------------------------------- | ------------------------------------- | --------------------------------- | --------------- |
| 7  | Abort if account type check failed          | COMM-SUCCESS OF DFHCOMMAREA = 'N' after PERFORM ACCOUNT-TYPE-CHECK | PERFORM GET-ME-OUT-OF-HERE (EXEC CICS RETURN) | P010, line 359 |

### Processing -- Named Counter (ENQ/DEQ)

| #  | Rule                                          | Condition                                                              | Action                                                                         | Source Location    |
| -- | --------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ------------------ |
| 8  | Enqueue named counter before number allocation | Always performed after validations pass                               | EXEC CICS ENQ RESOURCE(NCS-ACC-NO-NAME) LENGTH(16) -- NCS-ACC-NO-NAME = 'CBSAACCT' (8) + sort-code (6) + '  ' (2 spaces) = 16 chars | ENC010, line 390 |
| 9  | ENQ failure prevents account creation         | WS-CICS-RESP NOT = DFHRESP(NORMAL) after CICS ENQ                     | Set COMM-SUCCESS = 'N', COMM-FAIL-CODE = '3', PERFORM GET-ME-OUT-OF-HERE      | ENC010, line 397   |
| 10 | Dequeue named counter after processing        | Performed after successful ACCOUNT INSERT + PROCTRAN INSERT, or on INSERT failure | EXEC CICS DEQ RESOURCE(NCS-ACC-NO-NAME) LENGTH(16)                   | DNC010, line 412; WAD010 lines 863, 885; WPD010 line 1006 |
| 11 | DEQ failure                                   | WS-CICS-RESP NOT = DFHRESP(NORMAL) after CICS DEQ                     | Set COMM-SUCCESS = 'N', COMM-FAIL-CODE = '5', PERFORM GET-ME-OUT-OF-HERE      | DNC010, line 419   |

### Processing -- Account Number Allocation

| #  | Rule                                                    | Condition                                                          | Action                                                                                                                       | Source Location    |
| -- | ------------------------------------------------------- | ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| 12 | Read current last account number from CONTROL table     | Always (after ENQ)                                                 | SELECT CONTROL_NAME, CONTROL_VALUE_NUM, CONTROL_VALUE_STR FROM CONTROL WHERE CONTROL_NAME = :HV-CONTROL-NAME (= '<sortcode>-ACCOUNT-LAST') | FNA010, line 444   |
| 13 | CONTROL SELECT failure for ACCOUNT-LAST is fatal        | SQLCODE NOT = 0 after SELECT                                       | Populate ABNDINFO-REC, CICS LINK to ABNDPROC, EXEC CICS ABEND ABCODE('HNCS') NODUMP -- "CREACC - ACCOUNT NCS ... CANNOT BE ACCESSED AND DB2 SELECT FAILED" | FNA010, line 455 |
| 14 | Increment ACCOUNT-LAST counter and assign new number    | SQLCODE = 0 (SELECT succeeded)                                     | ADD 1 TO HV-CONTROL-VALUE-NUM GIVING COMM-NUMBER, ACCOUNT-NUMBER, REQUIRED-ACCT-NUMBER3, NCS-ACC-NO-VALUE, HV-CONTROL-VALUE-NUM | FNA010, line 525   |
| 15 | Write incremented ACCOUNT-LAST back to CONTROL table    | After ADD 1 to HV-CONTROL-VALUE-NUM                               | UPDATE CONTROL SET CONTROL_VALUE_NUM = :HV-CONTROL-VALUE-NUM WHERE CONTROL_NAME = :HV-CONTROL-NAME                         | FNA010, line 529   |
| 16 | CONTROL UPDATE failure for ACCOUNT-LAST is fatal        | SQLCODE NOT = 0 after UPDATE                                       | Populate ABNDINFO-REC, CICS LINK to ABNDPROC, EXEC CICS ABEND ABCODE('HNCS') NODUMP -- "CREACC - ACCOUNT NCS ... CANNOT BE ACCESSED AND DB2 UPDATE FAILED" | FNA010, line 534 |
| 17 | Read current account count from CONTROL table           | After ACCOUNT-LAST is updated                                      | SELECT from CONTROL WHERE CONTROL_NAME = :HV-CONTROL-NAME (= '<sortcode>-ACCOUNT-COUNT') | FNA010, line 611   |
| 18 | CONTROL SELECT failure for ACCOUNT-COUNT is fatal       | SQLCODE NOT = 0 after SELECT                                       | Populate ABNDINFO-REC, CICS LINK to ABNDPROC, EXEC CICS ABEND ABCODE('HNCS') NODUMP -- "CREACC - ACCOUNT NCS ... CANNOT BE ACCESSED AND DB2 SELECT FAILED" | FNA010, line 622   |
| 19 | Increment ACCOUNT-COUNT and write back to CONTROL table | SQLCODE = 0 (SELECT succeeded)                                     | ADD 1 TO HV-CONTROL-VALUE-NUM GIVING HV-CONTROL-VALUE-NUM, UPDATE CONTROL SET CONTROL_VALUE_NUM = :HV-CONTROL-VALUE-NUM    | FNA010, lines 691, 694 |
| 20 | CONTROL UPDATE failure for ACCOUNT-COUNT is fatal       | SQLCODE NOT = 0 after UPDATE                                       | Populate ABNDINFO-REC, CICS LINK to ABNDPROC, EXEC CICS ABEND ABCODE('HNCS') NODUMP -- "CREACC - ACCOUNT NCS ... CANNOT BE ACCESSED AND DB2 UPDATE FAILED" | FNA010, line 699   |

### Processing -- Account Row Write

| #  | Rule                                           | Condition                                   | Action                                                                                  | Source Location    |
| -- | ---------------------------------------------- | ------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------ |
| 21 | Eye-catcher for ACCOUNT row is 'ACCT'          | Always                                      | MOVE 'ACCT' TO HV-ACCOUNT-EYECATCHER                                                  | WAD010, line 778   |
| 22 | Account number is taken from named-counter value | Always (NCS-ACC-NO-VALUE set in FNA010)   | NCS-ACC-NO-DISP = NCS-ACC-NO-VALUE, HV-ACCOUNT-ACC-NO = NCS-ACC-NO-DISP(9:8) -- rightmost 8 digits of 16-digit counter value | WAD010, lines 782-783 |
| 23 | Account opened date and last statement date = today | Always                                 | Set via PERFORM CALCULATE-DATES (CICS ASKTIME / FORMATTIME DDMMYYYY)                  | WAD010, line 790   |
| 24 | Next statement date for ACCOUNT DB2 row = today + 30 days (simple, no month-aware adjustment) | Always (overrides CD010's month-aware value for the HV host variables) | COMPUTE WS-INTEGER = INTEGER-OF-DATE(today) + 30; COMPUTE WS-FUTURE-DATE = DATE-OF-INTEGER(WS-INTEGER); result moved into HV-ACCOUNT-NEXT-STMT-* | WAD010, lines 808-824 |
| 25 | Next statement date in LOCAL-STORAGE (ACCOUNT-NEXT-STMT-DATE) uses February-aware logic in CD010 | WS-ORIG-DATE-MM used in EVALUATE | All months except February: +30 days. Month 2: +28 days base, then if leap year (YYYY mod 4=0 AND (YYYY mod 100 != 0 OR YYYY mod 400=0)) add +1 day | CD010, lines 1137-1171 |
| 26 | ACCOUNT INSERT covers all mandatory columns     | Always                                      | Inserts: ACCOUNT_EYECATCHER, ACCOUNT_CUSTOMER_NUMBER, ACCOUNT_SORTCODE, ACCOUNT_NUMBER, ACCOUNT_TYPE, ACCOUNT_INTEREST_RATE, ACCOUNT_OPENED, ACCOUNT_OVERDRAFT_LIMIT, ACCOUNT_LAST_STATEMENT, ACCOUNT_NEXT_STATEMENT, ACCOUNT_AVAILABLE_BALANCE, ACCOUNT_ACTUAL_BALANCE | WAD010, lines 826-854 |
| 27 | ACCOUNT DB2 INSERT failure: dequeue and return  | SQLCODE NOT = 0 after INSERT INTO ACCOUNT   | Set COMM-SUCCESS = 'N', COMM-FAIL-CODE = '7', PERFORM DEQ-NAMED-COUNTER, PERFORM GET-ME-OUT-OF-HERE | WAD010, line 859 |
| 28 | On successful INSERT: write PROCTRAN audit record | SQLCODE = 0 after INSERT INTO ACCOUNT     | Store date fields into STORED-* working storage, PERFORM WRITE-PROCTRAN (which performs WRITE-PROCTRAN-DB2) | WAD010, line 883   |
| 29 | After PROCTRAN write: dequeue named counter     | Always (after PERFORM WRITE-PROCTRAN)       | PERFORM DEQ-NAMED-COUNTER                                                              | WAD010, line 885   |
| 30 | Return COMM-SUCCESS = 'Y' on complete success   | All steps succeeded                         | MOVE 'Y' TO COMM-SUCCESS, MOVE ' ' TO COMM-FAIL-CODE, MOVE 'ACCT' TO COMM-EYECATCHER, populate COMM-SORTCODE, COMM-NUMBER, COMM-OPENED, COMM-LAST-STMT-DT, COMM-NEXT-STMT-DT | WAD010, lines 890-914 |

Note: COMM-NEXT-STMT-DT is populated from HV-ACCOUNT-NEXT-STMT-DAY/MONTH/YEAR (the simple +30 host variables set in WAD010 lines 820-824), not from ACCOUNT-NEXT-STMT-DATE (set by CD010's February-aware calculation). The CD010 result stored in LOCAL-STORAGE is used only for ACCOUNT_LAST_STATEMENT (and the opened date fields), not for what is returned to the caller for next statement date.

### Processing -- PROCTRAN Audit Write

| #  | Rule                                              | Condition                                     | Action                                                                                         | Source Location    |
| -- | ------------------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------ |
| 31 | PROCTRAN record type for account creation is 'OCA' | Always                                       | MOVE 'OCA' TO HV-PROCTRAN-TYPE                                                                | WPD010, line 966   |
| 32 | PROCTRAN amount is zero for account creation      | Always                                        | MOVE 0 TO HV-PROCTRAN-AMOUNT                                                                  | WPD010, line 967   |
| 33 | PROCTRAN description layout                       | Always                                        | DESC(1:10) = STORED-CUSTNO (customer number), DESC(11:8) = STORED-ACCTYPE (account type), DESC(19:8) = STORED-LST-STMT (last statement date DDMMYYYY), DESC(27:8) = STORED-NXT-STMT (next statement date DDMMYYYY), DESC(35:6) = SPACES | WPD010, lines 960-964 |
| 34 | PROCTRAN eye-catcher is 'PRTR'                    | Always                                        | MOVE 'PRTR' TO HV-PROCTRAN-EYECATCHER                                                        | WPD010, line 937   |
| 35 | PROCTRAN reference = CICS task number             | Always                                        | MOVE EIBTASKN TO WS-EIBTASKN12, MOVE WS-EIBTASKN12 TO HV-PROCTRAN-REF (12-char field)       | WPD010, lines 940-941 |
| 36 | PROCTRAN INSERT failure is fatal (no NODUMP)      | SQLCODE NOT = 0 after INSERT INTO PROCTRAN    | DISPLAY 'In CREACC (WPD010) UNABLE TO WRITE TO PROCTRAN ROW DATASTORE ...', PERFORM DEQ-NAMED-COUNTER, populate ABNDINFO-REC, CICS LINK to ABNDPROC, EXEC CICS ABEND ABCODE('HWPT') -- note: no NODUMP on this ABEND | WPD010, line 999 |
| 37 | PROCTRAN sort-code and account-number linkage fields | Always                                     | MOVE SORTCODE TO HV-PROCTRAN-SORT-CODE (PROCTRAN_SORTCODE); MOVE STORED-ACCNO TO HV-PROCTRAN-ACC-NUMBER (PROCTRAN_NUMBER) -- these tie the audit row to the newly created account | WPD010, lines 938-939 |
| 39 | PROCTRAN date and time are independently captured at write time | Always                              | WPD010 performs its own EXEC CICS ASKTIME / FORMATTIME (lines 946-958) to populate HV-PROCTRAN-DATE and HV-PROCTRAN-TIME -- the audit timestamp reflects the time of the PROCTRAN INSERT, not the time of account creation recorded in CD010. A small discrepancy between the account opened date and PROCTRAN timestamp is possible if the transaction spans a date boundary. | WPD010, lines 946-958 |

### Anomalies and Code Defects

| #  | Rule                                              | Condition                                     | Action                                                                                         | Source Location    |
| -- | ------------------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------ |
| 38 | IMS PCB pointer nulled in CICS-only program       | Unconditional in CAC010 before CICS LINK to INQACCCU | `SET COMM-PCB-POINTER TO NULL` -- COMM-PCB-POINTER is an IMS/DL-I PCB pointer field appearing in a CICS-only program. This statement has no effect at runtime in a pure CICS environment but indicates the INQACCCU copybook was designed for both IMS and CICS dispatch | CAC010, line 1086 |
| 40 | CD010 next-statement date logic is February-only aware, not truly month-aware | Month 2 (February): +28 base + optional leap-year day. All other months: unconditional +30. | For months with 30 days (April, June, September, November), adding +30 from the 30th overshoots the month boundary. For months with 31 days (January, March, May, July, August, October, December), adding +30 does not land on the last day of the next month. This is a business logic limitation masquerading as month-awareness. Does not cause date calculation errors in practice for typical mid-month opening dates but is not end-of-month safe. | CD010, lines 1137-1171 |

## Calculations

| Calculation                   | Formula / Logic                                                                                                                   | Input Fields                                              | Output Field                                          | Source Location       |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------- | --------------------- |
| Next account number           | HV-CONTROL-VALUE-NUM (from CONTROL ACCOUNT-LAST row) + 1; result simultaneously assigned to multiple targets                      | HV-CONTROL-VALUE-NUM (DB2 CONTROL.CONTROL_VALUE_NUM)     | COMM-NUMBER, ACCOUNT-NUMBER, REQUIRED-ACCT-NUMBER3, NCS-ACC-NO-VALUE, HV-CONTROL-VALUE-NUM | FNA010, line 525      |
| Account count increment       | HV-CONTROL-VALUE-NUM (from CONTROL ACCOUNT-COUNT row) + 1                                                                         | HV-CONTROL-VALUE-NUM (DB2 CONTROL.CONTROL_VALUE_NUM)     | HV-CONTROL-VALUE-NUM (written back to CONTROL table)  | FNA010, line 691      |
| Account number from counter   | NCS-ACC-NO-VALUE right-justified to 16-digit display (NCS-ACC-NO-DISP); characters 9-16 (rightmost 8 digits) become the 8-char account number | NCS-ACC-NO-VALUE (PIC 9(16) COMP)                   | HV-ACCOUNT-ACC-NO (PIC X(8))                          | WAD010, lines 782-783 |
| Next statement date (WAD010 -- simple +30) | COMPUTE WS-INTEGER = INTEGER-OF-DATE(YYYYMMDD today); COMPUTE WS-INTEGER = WS-INTEGER + 30; COMPUTE WS-FUTURE-DATE = DATE-OF-INTEGER(WS-INTEGER). No month-aware or leap-year adjustment in WAD010. | WS-STDT-9-NUMERIC (today YYYYMMDD), WS-INTEGER | HV-ACCOUNT-NEXT-STMT-YEAR/MONTH/DAY (DB2 host vars)  | WAD010, lines 795-824 |
| Next statement date (CD010 -- February-aware) | COMPUTE WS-INTEGER = INTEGER-OF-DATE(today); EVALUATE month: +30 for all months except February; +28 base for month 2; if leap year (YYYY mod 4=0 AND (YYYY mod 100 != 0 OR YYYY mod 400=0)) then +29 instead of +28 | WS-STDT-9-NUMERIC, WS-ORIG-DATE-MM, WS-ORIG-DATE-YYYY | WS-INTEGER, then WS-FUTURE-DATE, then ACCOUNT-NEXT-STMT-DATE (LOCAL-STORAGE) | CD010, lines 1131-1178 |
| Account opened date           | Today's date from CICS ASKTIME/FORMATTIME DDMMYYYY with DATESEP (locale separator)                                                | WS-U-TIME (CICS ABSTIME)                                 | HV-ACCOUNT-OPENED-DAY/MONTH/YEAR (DD.MM.YYYY format with '.' delimiters), ACCOUNT-OPENED | CD010, lines 1109-1197 |
| Last statement date           | Same as opened date (copied from ACCOUNT-OPENED)                                                                                  | ACCOUNT-OPENED (set in CD010)                            | ACCOUNT-LAST-STMT-DATE, HV-ACCOUNT-LAST-STMT-DAY/MONTH/YEAR | CD010, lines 1191-1203 |
| STORED date compaction        | HV-ACCOUNT-LAST-STMT / HV-ACCOUNT-NEXT-STMT stored in DD.MM.YYYY (10 chars); compacted to DDMMYYYY (8 chars) for PROCTRAN DESC by extracting positions 1:2 (DD), 4:2 (MM), 7:4 (YYYY) and moving to STORED-LST-STMT / STORED-NXT-STMT | HV-ACCOUNT-LAST-STMT, HV-ACCOUNT-NEXT-STMT | STORED-LST-STMT (PIC X(8)), STORED-NXT-STMT (PIC X(8)) | WAD010, lines 876-881 |
| PROCTRAN audit timestamp      | Independent CICS ASKTIME / FORMATTIME with DATESEP('.') at write time                                                             | WS-U-TIME (CICS ABSTIME captured in WPD010)              | HV-PROCTRAN-DATE (DD.MM.YYYY), HV-PROCTRAN-TIME (HHMMSS)                                 | WPD010, lines 946-958 |

## Error Handling

| Condition                                                   | Action                                                                                    | Return Code           | Source Location         |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------------------- | --------------------- | ----------------------- |
| CICS LINK to INQCUST fails OR INQCUST-INQ-SUCCESS != 'Y'   | Set COMM-SUCCESS='N', COMM-FAIL-CODE='1', EXEC CICS RETURN                               | COMM-FAIL-CODE = '1'  | P010, line 314          |
| CICS LINK to INQACCCU fails (WS-CICS-RESP != NORMAL)        | DISPLAY 'Error counting accounts', set COMM-SUCCESS='N', COMM-FAIL-CODE='9', EXEC CICS RETURN | COMM-FAIL-CODE = '9' | P010, line 329         |
| INQACCCU returns COMM-SUCCESS='N'                           | DISPLAY 'Error counting accounts', set COMM-SUCCESS='N', COMM-FAIL-CODE='9', EXEC CICS RETURN | COMM-FAIL-CODE = '9' | P010, line 338         |
| Customer has more than 9 accounts (NUMBER-OF-ACCOUNTS > 9) | Set COMM-SUCCESS='N', COMM-FAIL-CODE='8', EXEC CICS RETURN                               | COMM-FAIL-CODE = '8'  | P010, line 347          |
| Account type not in {ISA, MORTGAGE, SAVING, CURRENT, LOAN} | Set COMM-SUCCESS='N', COMM-FAIL-CODE='A', EXEC CICS RETURN                               | COMM-FAIL-CODE = 'A'  | ATC010, line 1222       |
| CICS ENQ on named counter fails                             | Set COMM-SUCCESS='N', COMM-FAIL-CODE='3', EXEC CICS RETURN                               | COMM-FAIL-CODE = '3'  | ENC010, line 397        |
| CICS DEQ on named counter fails                             | Set COMM-SUCCESS='N', COMM-FAIL-CODE='5', EXEC CICS RETURN                               | COMM-FAIL-CODE = '5'  | DNC010, line 419        |
| DB2 SELECT on CONTROL (ACCOUNT-LAST) fails                 | Populate ABNDINFO, CICS LINK ABNDPROC, EXEC CICS ABEND ABCODE('HNCS') NODUMP -- "CREACC - ACCOUNT NCS ... CANNOT BE ACCESSED AND DB2 SELECT FAILED. SQLCODE=..." -- ABND-FREEFORM prefix 'FNAND010' | ABEND HNCS | FNA010, line 455 |
| DB2 UPDATE on CONTROL (ACCOUNT-LAST) fails                 | Populate ABNDINFO, CICS LINK ABNDPROC, EXEC CICS ABEND ABCODE('HNCS') NODUMP -- "CREACC - ACCOUNT NCS ... CANNOT BE ACCESSED AND DB2 UPDATE FAILED. SQLCODE=..." -- ABND-FREEFORM prefix 'FNAND010(2)' | ABEND HNCS | FNA010, line 534 |
| DB2 SELECT on CONTROL (ACCOUNT-COUNT) fails                | Populate ABNDINFO, CICS LINK ABNDPROC, EXEC CICS ABEND ABCODE('HNCS') NODUMP -- "CREACC - ACCOUNT NCS ... CANNOT BE ACCESSED AND DB2 SELECT FAILED. SQLCODE=..." -- ABND-FREEFORM prefix 'FNAND010(3)' | ABEND HNCS | FNA010, line 622        |
| DB2 UPDATE on CONTROL (ACCOUNT-COUNT) fails                | Populate ABNDINFO, CICS LINK ABNDPROC, EXEC CICS ABEND ABCODE('HNCS') NODUMP -- "CREACC - ACCOUNT NCS ... CANNOT BE ACCESSED AND DB2 UPDATE FAILED. SQLCODE=..." -- ABND-FREEFORM prefix 'FNAND010(4)' | ABEND HNCS | FNA010, line 699        |
| DB2 INSERT into ACCOUNT fails                              | Set COMM-SUCCESS='N', COMM-FAIL-CODE='7', PERFORM DEQ-NAMED-COUNTER, EXEC CICS RETURN   | COMM-FAIL-CODE = '7'  | WAD010, line 859        |
| DB2 INSERT into PROCTRAN fails                             | DISPLAY 'In CREACC (WPD010) UNABLE TO WRITE TO PROCTRAN ROW DATASTORE RESP CODE=... RESP2=...', PERFORM DEQ-NAMED-COUNTER, Populate ABNDINFO, CICS LINK ABNDPROC, EXEC CICS ABEND ABCODE('HWPT') -- no NODUMP | ABEND HWPT | WPD010, line 999 |

Note: ABND-TIME STRING construction at lines 480-485, 558-563, 646-652, 722-729, 1030-1036 uses `WS-TIME-NOW-GRP-MM` in both the minutes and seconds positions (should be WS-TIME-NOW-GRP-SS for seconds). This is a code defect: abend timestamp seconds field will always equal the minutes value.

Note: The four ABND-FREEFORM identifier strings in FNA010 use the prefix 'FNAND010' (with an extra 'N' and 'D') rather than matching the actual paragraph name 'FNA010'. This inconsistency does not affect runtime behaviour but complicates log analysis. The WPD010 failure freeform correctly uses 'WPD010' as its prefix.

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. P010 -- Entry point; initialise sort-code, account number to zero, INQCUST commarea; move COMM-CUSTNO to INQCUST-CUSTNO
2. EXEC CICS LINK PROGRAM('INQCUST ') -- Verify customer exists; fail with code '1' if EIBRESP != NORMAL or INQCUST-INQ-SUCCESS != 'Y'
3. CUSTOMER-ACCOUNT-COUNT (CAC010) -- Sets NUMBER-OF-ACCOUNTS=20, CUSTOMER-NUMBER=COMM-CUSTNO, nulls COMM-PCB-POINTER, then EXEC CICS LINK PROGRAM('INQACCCU') SYNCONRETURN to count customer accounts
4. P010 -- Check WS-CICS-RESP and INQACCCU COMM-SUCCESS; fail with code '9' if link/logic fails. Enforce NUMBER-OF-ACCOUNTS <= 9; fail with code '8' if exceeded
5. ACCOUNT-TYPE-CHECK (ATC010) -- EVALUATE COMM-ACC-TYPE against {ISA, MORTGAGE, SAVING, CURRENT, LOAN}; set COMM-SUCCESS='N'/COMM-FAIL-CODE='A' if invalid
6. P010 -- Check COMM-SUCCESS after ATC010; fail (EXEC CICS RETURN) if 'N'
7. ENQ-NAMED-COUNTER (ENC010) -- EXEC CICS ENQ RESOURCE('CBSAACCT' + sortcode + '  ') LENGTH(16) to serialise account number allocation; fail with code '3' if ENQ fails
8. FIND-NEXT-ACCOUNT (FNA010) -- SELECT/UPDATE CONTROL for ACCOUNT-LAST (get + increment + write back); SELECT/UPDATE CONTROL for ACCOUNT-COUNT (increment + write back); ABEND HNCS on any failure
9. WRITE-ACCOUNT-DB2 (WAD010) -- Build HOST-ACCOUNT-ROW, PERFORM CALCULATE-DATES (CD010) for opened/last-stmt dates, compute next-stmt date (simple +30 on host vars), INSERT 12 columns into ACCOUNT; on failure DEQ + return with code '7'
10. WRITE-PROCTRAN (WP010) -> WRITE-PROCTRAN-DB2 (WPD010) -- INSERT audit record into PROCTRAN with type 'OCA', eye-catcher 'PRTR', amount=0, EIBTASKN as reference, sort-code and new account number as linkage fields; independently captures current timestamp via ASKTIME/FORMATTIME; on failure DEQ + ABEND HWPT (no NODUMP)
11. DEQ-NAMED-COUNTER (DNC010) -- EXEC CICS DEQ to release the named-counter lock; fail with code '5' if DEQ fails
12. GET-ME-OUT-OF-HERE (GMOFH010) -- EXEC CICS RETURN (used for both normal and error exits)
13. POPULATE-TIME-DATE2 (PTD2010) -- EXEC CICS ASKTIME / FORMATTIME DDMMYYYY; called only during abend-info population to capture error timestamp
14. CALCULATE-DATES (CD010) -- EXEC CICS ASKTIME / FORMATTIME DDMMYYYY + TIME with locale DATESEP; sets ACCOUNT-OPENED, ACCOUNT-LAST-STMT-DATE (=today), and ACCOUNT-NEXT-STMT-DATE (February-aware +30 in LOCAL-STORAGE); also provides WS-ORIG-DATE for WAD010's own host-variable next-stmt calculation
