---
type: business-rules
program: CRECUST
program_type: online
status: draft
confidence: high
last_pass: 5
calls:
- ABNDPROC
- CEEDAYS
- CEELOCT
called_by:
- BNK1CCS
uses_copybooks:
- ABNDINFO
- CEEIGZCT
- CRECUST
- CUSTCTRL
- CUSTOMER
- PROCDB2
- PROCTRAN
- SORTCODE
reads:
- CUSTOMER
writes:
- CUSTOMER
db_tables:
- PROCTRAN
transactions: []
mq_queues: []
---

# CRECUST -- Business Rules

## Program Purpose

CRECUST creates a new customer record in the CBSA banking system. It is called
by BNK1CCS (the customer creation screen handler) and receives customer details
via a COMMAREA. The program:

1. Validates the customer title against an allowed-values list.
2. Performs an asynchronous credit check by spawning up to 5 child transactions
   (OCR1 -- OCR5), waiting 3 seconds, then fetching and averaging the returned
   credit scores.
3. Validates the customer date of birth using IBM Language Environment routines
   (CEEDAYS, CEELOCT).
4. Enqueues a CICS ENQ lock on resource name 'CBSACUST' + sortcode to serialise
   access to the CUSTOMER counter, increments the counter (VSAM control record),
   and releases the ENQ after use. Note: the program uses "NCS" naming
   conventions in field names but does NOT use the CICS Named Counter Server
   (DFHNCNTL EXEC CICS INCREMNTER/DECREMNTER). Serialisation is via CICS ENQ/DEQ
   and VSAM READ FOR UPDATE / REWRITE.
5. Writes the new customer record to the CUSTOMER VSAM file.
6. Updates the CUSTOMER control record (sortcode 000000, number 9999999999) to
   increment the total customer count and record the latest customer number.
7. Writes an audit row to the PROCTRAN DB2 table with transaction type 'OCC'.
8. Returns the assigned sortcode and customer number in the COMMAREA.

If any step fails the program sets COMM-SUCCESS = 'N', sets COMM-FAIL-CODE to a
diagnostic character, DEQs the ENQ lock if it was acquired, and returns to the
caller.

Note: The program header comment states "decrement the Named Counter (restoring
it to the start position)" on failure; however no SUBTRACT or decrement
instruction is present anywhere in the PROCEDURE DIVISION. Only DEQ is performed
on failure paths -- the counter value is not restored.

## Input / Output

| Direction | Resource          | Type   | Description                                                                   |
| --------- | ----------------- | ------ | ----------------------------------------------------------------------------- |
| IN        | DFHCOMMAREA       | CICS   | CRECUST copybook: customer name, address, DOB, credit fields                  |
| IN/OUT    | CUSTOMER (VSAM)   | File   | KSDS; new customer record written; control record updated (two separate reads) |
| OUT       | PROCTRAN (DB2)    | DB     | Audit row inserted for each new customer (type 'OCC')                         |
| IN/OUT    | CBSACUST+sort ENQ | CICS   | CICS ENQ/DEQ resource name; serialises CUSTOMER number allocation (not DFHNCNTL) |
| OUT       | OCR1 -- OCR5      | CICS   | Async child transactions for credit agency checks                             |

## Business Rules

### Title Validation

| #  | Rule                            | Condition                                                                                                                                      | Action                                                     | Source Location |
| -- | ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | --------------- |
| 1  | Title must be from allowed list | UNSTRING COMM-NAME first token into WS-UNSTR-TITLE; EVALUATE against: 'Professor', 'Mr', 'Mrs', 'Miss', 'Ms', 'Dr', 'Drs', 'Lord', 'Sir', 'Lady', or blank | If no match: COMM-SUCCESS='N', COMM-FAIL-CODE='T', GOBACK | P010 (line 365--412) |
| 2  | Blank title is valid            | WS-UNSTR-TITLE = spaces (9 spaces)                                                                                                             | WS-TITLE-VALID set to 'Y'; processing continues            | P010 (line 401--402) |

### Date of Birth Validation

| #  | Rule                               | Condition                                                         | Action                                                        | Source Location       |
| -- | ---------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------- | --------------------- |
| 3  | Birth year must be >= 1601         | COMM-BIRTH-YEAR < 1601                                            | WS-DATE-OF-BIRTH-ERROR='Y', COMM-FAIL-CODE='O', exit DOB check | DOBC010 (line 1427--1431) |
| 4  | Date of birth must be a valid date | CALL CEEDAYS: converts YYYYMMDD to Lilian day number; checks CE status | If NOT CEE000: WS-DATE-OF-BIRTH-ERROR='Y', COMM-FAIL-CODE='Z', DISPLAY error, exit | DOBC010 (line 1437--1449) |
| 5  | Customer age must not exceed 150 years | WS-CUSTOMER-AGE (= today's year - COMM-BIRTH-YEAR) > 150       | WS-DATE-OF-BIRTH-ERROR='Y', COMM-FAIL-CODE='O', exit DOB check | DOBC010 (line 1466--1470) |
| 6  | Date of birth must not be in the future | WS-TODAY-LILLIAN < WS-DATE-OF-BIRTH-LILLIAN                 | WS-DATE-OF-BIRTH-ERROR='Y', COMM-FAIL-CODE='Y'               | DOBC010 (line 1472--1475) |
| 7  | DOB error causes caller to abort   | WS-DATE-OF-BIRTH-ERROR = 'Y' (after PERFORM DATE-OF-BIRTH-CHECK) | COMM-SUCCESS='N', PERFORM GET-ME-OUT-OF-HERE (EXEC CICS RETURN) | P010 (line 452--457)  |

### Credit Check (Asynchronous)

| #  | Rule                                           | Condition                                                              | Action                                                                  | Source Location       |
| -- | ---------------------------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------- | --------------------- |
| 8  | Exactly 5 credit agency checks are launched    | PERFORM VARYING WS-CC-CNT FROM 1 BY 1 UNTIL > 5                       | Transactions OCR1--OCR5 started via EXEC CICS RUN TRANSID               | CC010 (line 579--674) |
| 9  | Channel name is fixed                          | Always                                                                 | WS-CHANNEL-NAME = 'CIPCREDCHANN    '                                    | CC010 (line 574)      |
| 10 | Container names map 1:1 to agencies            | WS-CC-CNT 1=CIPA, 2=CIPB, 3=CIPC, 4=CIPD, 5=CIPE                     | DFHCOMMAREA pushed into matching container before child transaction starts | CC010 (line 590--610) |
| 11 | Container EVALUATE has unreachable branches    | WHEN 6=CIPF, 7=CIPG, 8=CIPH, 9=CIPI defined but loop only iterates to 5 | Dead WHEN clauses; can never execute; no functional impact unless loop bound is changed | CC010 (line 601--609) |
| 12 | PUT CONTAINER failure aborts creation          | DFHRESP NOT NORMAL on EXEC CICS PUT CONTAINER                          | COMM-SUCCESS='N', COMM-FAIL-CODE='A', DISPLAY diagnostic, GET-ME-OUT-OF-HERE | CC010 (line 623--635) |
| 13 | RUN TRANSID failure aborts creation            | DFHRESP NOT NORMAL on EXEC CICS RUN TRANSID                            | COMM-SUCCESS='N', COMM-FAIL-CODE='B', DISPLAY diagnostic, GET-ME-OUT-OF-HERE | CC010 (line 647--659) |
| 14 | After launching all children, delay 3 seconds  | Always (to allow child transactions time to complete)                  | EXEC CICS DELAY FOR SECONDS(3)                                           | CC010 (line 681--683) |
| 15 | FETCH ANY with NOSUSPEND collects results       | Loop UNTIL WS-FINISHED-FETCHING = 'Y'                                 | Each completed child fetched immediately without blocking                | CC010 (line 689--1062) |
| 16 | NOTFINISHED + RESP2=52: no more replies pending | DFHRESP(NOTFINISHED) AND RESP2=52                                      | If WS-RETRIEVED-CNT = 0: error (fail code 'C'); else compute average and set review date | CC010 (line 715--800) |
| 17 | NOTFINISHED + zero responses is a credit check error | DFHRESP(NOTFINISHED), RESP2=52, WS-RETRIEVED-CNT = 0            | COMM-CREDIT-SCORE=0, COMM-CS-REVIEW-DATE=today, WS-CREDIT-CHECK-ERROR='Y', COMM-FAIL-CODE='C', GET-ME-OUT-OF-HERE | CC010 (line 722--741) |
| 18 | NOTFND + RESP2=1 + zero responses: credit check error | DFHRESP(NOTFND) AND RESP2=1 AND WS-RETRIEVED-CNT = 0           | COMM-CREDIT-SCORE=0, COMM-CS-REVIEW-DATE=today, WS-CREDIT-CHECK-ERROR='Y'; COMM-FAIL-CODE is NOT set (distinct from NOTFINISHED path) | CC010 (line 831--848) -- DEFECT: missing fail code |
| 19 | INVREQ + RESP2=1: no child transactions exist  | DFHRESP(INVREQ) AND RESP2=1                                            | COMM-CREDIT-SCORE=0, review date=today, COMM-FAIL-CODE='D', GET-ME-OUT-OF-HERE | CC010 (line 805--826) |
| 20 | NOTFND + RESP2=1 + responses received: end of list | DFHRESP(NOTFND) AND RESP2=1 AND WS-RETRIEVED-CNT > 0             | Compute average credit score and random review date; WS-FINISHED-FETCHING='Y' | CC010 (line 849--903) |
| 21 | GET CONTAINER failure aborts                   | DFHRESP NOT NORMAL on EXEC CICS GET CONTAINER                          | COMM-CREDIT-SCORE=0, review date=today, COMM-FAIL-CODE='E', GET-ME-OUT-OF-HERE | CC010 (line 958--980) |
| 22 | Child ABEND status aborts creation             | COMPSTATUS = DFHVALUE(ABEND)                                           | COMM-CREDIT-SCORE=0, review date=today, COMM-FAIL-CODE='F', GET-ME-OUT-OF-HERE | CC010 (line 990--1006) |
| 23 | Child SECERROR status aborts creation          | COMPSTATUS = DFHVALUE(SECERROR)                                        | COMM-CREDIT-SCORE=0, review date=today, COMM-FAIL-CODE='G', GET-ME-OUT-OF-HERE | CC010 (line 1009--1031) |
| 24 | Unknown COMPSTATUS aborts creation             | COMPSTATUS = WHEN OTHER                                                | COMM-CREDIT-SCORE=0, review date=today, COMM-FAIL-CODE='H', GET-ME-OUT-OF-HERE | CC010 (line 1034--1056) |
| 25 | Credit check error in caller sets score = 0   | WS-CREDIT-CHECK-ERROR = 'Y' after PERFORM CREDIT-CHECK                | COMM-CREDIT-SCORE=0, COMM-CS-REVIEW-DATE=today, COMM-FAIL-CODE='G', GET-ME-OUT-OF-HERE | P010 (line 429--448) |

### Named Counter Serialisation

| #  | Rule                                       | Condition                                                | Action                                                                 | Source Location         |
| -- | ------------------------------------------ | -------------------------------------------------------- | ---------------------------------------------------------------------- | ----------------------- |
| 26 | CUSTOMER counter must be ENQ'd before use  | Always -- before reading/incrementing the counter        | EXEC CICS ENQ RESOURCE(NCS-CUST-NO-NAME) LENGTH(16)                   | ENC010 (line 504--515)  |
| 27 | NCS name encodes sortcode                  | SORTCODE moved into NCS-CUST-NO-TEST-SORT before ENQ/DEQ | Counter name = 'CBSACUST' + 6-char sortcode + 2 spaces                | ENC010 (line 501--502)  |
| 28 | ENQ failure aborts creation                | DFHRESP NOT NORMAL on EXEC CICS ENQ                      | COMM-SUCCESS='N', COMM-FAIL-CODE='3', GET-ME-OUT-OF-HERE              | ENC010 (line 511--515)  |
| 29 | Customer number derived from control record| GET-LAST-CUSTOMER-VSAM reads control record (sortcode 000000, number 9999999999) for UPDATE, adds 1 to LAST-CUSTOMER-NUMBER, REWRITEs | New customer number = previous LAST-CUSTOMER-NUMBER + 1; result copied to COMM-NUMBER, CUSTOMER-NUMBER, NCS-CUST-NO-VALUE, and REQUIRED-CUST-NUMBER2 (unused dead-write variable) | GLCV010 (line 1344--1416) |
| 30 | CUSTOMER file READ SYSIDERR retried        | DFHRESP(SYSIDERR) on READ or REWRITE in GLCV010          | Retry loop up to 100 times with 3-second delay between attempts        | GLCV010 (line 1356--1412) |
| 31 | READ failure (non-SYSIDERR) aborts creation| DFHRESP NOT NORMAL (not SYSIDERR) on initial READ in GLCV010 | COMM-SUCCESS='N', COMM-FAIL-CODE='4', DEQ, GET-ME-OUT-OF-HERE    | GLCV010 (line 1374--1379) |
| 32 | REWRITE failure (non-SYSIDERR) aborts      | DFHRESP NOT NORMAL (not SYSIDERR) on initial REWRITE in GLCV010 | COMM-SUCCESS='N', COMM-FAIL-CODE='4', DEQ, GET-ME-OUT-OF-HERE   | GLCV010 (line 1405--1411) |
| 33 | SYSIDERR retry exhaustion falls through silently | READ or REWRITE returns SYSIDERR on all 100 retries (retry loop exits via SYSIDERR-RETRY > 100) | The ELSE branch containing the NOT-NORMAL abort is skipped; code continues to ADD 1 and REWRITE on unread data -- silent corruption | GLCV010 (line 1356--1412) -- DEFECT |
| 34 | NCS must be DEQ'd on success and failure   | After WRITE-CUSTOMER-VSAM success or any write failure   | EXEC CICS DEQ RESOURCE(NCS-CUST-NO-NAME) LENGTH(16)                   | DNC010 (line 529--543)  |
| 35 | DEQ failure sets fail code                 | DFHRESP NOT NORMAL on EXEC CICS DEQ                      | COMM-SUCCESS='N', COMM-FAIL-CODE='5', GET-ME-OUT-OF-HERE              | DNC010 (line 536--540)  |
| 36 | NCS counter is NOT decremented on failure  | Program header says restore counter; no SUBTRACT exists  | Counter value is permanently incremented even when customer write fails; only DEQ is issued | DEFECT -- no SUBTRACT in PROCEDURE DIVISION |

### CUSTOMER VSAM Write

| #  | Rule                                          | Condition                                                     | Action                                                                | Source Location          |
| -- | --------------------------------------------- | ------------------------------------------------------------- | --------------------------------------------------------------------- | ------------------------ |
| 37 | Customer record written with eyecatcher 'CUST'| Always                                                        | CUSTOMER-EYECATCHER set to 'CUST' before EXEC CICS WRITE             | WCV010 (line 1076)       |
| 38 | Customer record key = sortcode + customer no  | Always                                                        | CUSTOMER-KEY (CUSTOMER-SORTCODE + CUSTOMER-NUMBER), KEYLENGTH=16     | WCV010 (line 1087--1095) |
| 39 | WRITE SYSIDERR retried up to 100 times        | DFHRESP(SYSIDERR) on EXEC CICS WRITE FILE('CUSTOMER')         | Loop max 100 iterations, 3-second delay each; retry WRITE            | WCV010 (line 1097--1117) |
| 40 | WRITE failure (after retries) aborts creation | DFHRESP NOT NORMAL after retry loop                           | COMM-SUCCESS='N', COMM-FAIL-CODE='1', DEQ, GET-ME-OUT-OF-HERE        | WCV010 (line 1122--1127) |
| 41 | Control record updated after each new customer| After successful customer WRITE                               | READ FOR UPDATE control record (sort=000000, no=9999999999); NUMBER-OF-CUSTOMERS +1; LAST-CUSTOMER-NUMBER = new number; REWRITE | WCV010 (line 1129--1146) |
| 42 | Control record READ/REWRITE has no error check| EXEC CICS READ UPDATE and EXEC CICS REWRITE at lines 1133-1146 have no RESP/RESP2 clauses | Silent failure: if the control-record update fails, the program continues to COMM-SUCCESS='Y' without detecting the error | WCV010 (line 1133--1146) -- DEFECT |
| 43 | COMM-SUCCESS set 'Y' only on full success     | After WRITE-CUSTOMER-VSAM and WRITE-PROCTRAN both succeed     | COMM-SUCCESS='Y', COMM-FAIL-CODE=' ', COMM-EYECATCHER='CUST', sortcode and number returned | WCV010 (line 1171--1173) |

### PROCTRAN Audit Write

| #  | Rule                                        | Condition              | Action                                                                    | Source Location          |
| -- | ------------------------------------------- | ---------------------- | ------------------------------------------------------------------------- | ------------------------ |
| 44 | Audit row type is always 'OCC'              | Always                 | HV-PROCTRAN-TYPE = 'OCC'                                                  | WPD010 (line 1223)       |
| 45 | Audit row eyecatcher is 'PRTR'             | Always                 | HV-PROCTRAN-EYECATCHER = 'PRTR'                                           | WPD010 (line 1195)       |
| 46 | Audit row account number is zeros          | Always (no account yet)| HV-PROCTRAN-ACC-NUMBER = ZEROS; mapped to PROCTRAN_NUMBER column          | WPD010 (line 1197)       |
| 47 | Audit row reference is EIBTASKN            | Always                 | HV-PROCTRAN-REF = 12-digit task number                                    | WPD010 (line 1198--1199) |
| 48 | Audit row description contains customer data| Always                | DESC(1:6)=sortcode, DESC(7:10)=custno, DESC(17:14)=name, DESC(31:10)=DOB  | WPD010 (line 1218--1221) |
| 49 | PROCTRAN INSERT failure triggers ABEND      | SQLCODE NOT = 0        | Link to ABNDPROC (WS-ABEND-PGM='ABNDPROC'), then EXEC CICS ABEND ABCODE('HWPT') | WPD010 (line 1256--1323) |

## Calculations

| Calculation                    | Formula / Logic                                                                                              | Input Fields                              | Output Field            | Source Location        |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------ | ----------------------------------------- | ----------------------- | ---------------------- |
| Average credit score           | COMPUTE WS-ACTUAL-CS-SCR = WS-TOTAL-CS-SCR / WS-RETRIEVED-CNT (integer division; no ROUNDED)                | WS-TOTAL-CS-SCR, WS-RETRIEVED-CNT         | COMM-CREDIT-SCORE       | CC010 (line 757--759)  |
| Cumulative credit score total  | COMPUTE WS-TOTAL-CS-SCR = WS-TOTAL-CS-SCR + WS-CHILD-DATA-CREDIT-SCORE (per successful FETCH)               | WS-CHILD-DATA-CREDIT-SCORE                | WS-TOTAL-CS-SCR         | CC010 (line 985--988)  |
| Credit score review date       | Random offset 1--20 days added to today; seed = EIBTASKN. COMPUTE WS-REVIEW-DATE-ADD = ((21-1) * FUNCTION RANDOM(WS-SEED)) + 1; COMPUTE WS-NEW-REVIEW-DATE-INT = INTEGER-OF-DATE(today) + WS-REVIEW-DATE-ADD; review date = DATE-OF-INTEGER(WS-NEW-REVIEW-DATE-INT) | EIBTASKN (seed), today's date | COMM-CS-REVIEW-DATE (DDMMYYYY) | CC010 (line 777--797, 883--901) |
| Customer age validation        | SUBTRACT COMM-BIRTH-YEAR FROM WS-TODAY-G-YEAR GIVING WS-CUSTOMER-AGE                                        | WS-TODAY-G-YEAR, COMM-BIRTH-YEAR          | WS-CUSTOMER-AGE (S9999) | DOBC010 (line 1463--1464) |
| Next customer number           | ADD 1 TO LAST-CUSTOMER-NUMBER IN CUSTOMER-CONTROL GIVING LAST-CUSTOMER-NUMBER; result moved to COMM-NUMBER, CUSTOMER-NUMBER, NCS-CUST-NO-VALUE, and REQUIRED-CUST-NUMBER2 (dead-write: defined in WORKING-STORAGE but never subsequently read) | LAST-CUSTOMER-NUMBER (control record) | COMM-NUMBER, CUSTOMER-NUMBER, NCS-CUST-NO-VALUE | GLCV010 (line 1381--1416) |
| Customer record length         | COMPUTE WS-CUST-REC-LEN = LENGTH OF OUTPUT-DATA                                                              | OUTPUT-DATA                               | WS-CUST-REC-LEN         | WCV010 (line 1085)     |
| COMMAREA length for container  | COMPUTE WS-PUT-CONT-LEN = LENGTH OF DFHCOMMAREA                                                              | DFHCOMMAREA                               | WS-PUT-CONT-LEN         | CC010 (line 577)       |
| DOB stored with slashes        | CUSTOMER-DATE-OF-BIRTH(1:2)/CUSTOMER-DATE-OF-BIRTH(3:2)/CUSTOMER-DATE-OF-BIRTH(5:4) concatenated into STORED-DOB | CUSTOMER-DATE-OF-BIRTH | STORED-DOB (DD/MM/YYYY) | WCV010 (line 1154--1158) |

## Error Handling

| Condition                                        | Action                                                              | Return Code              | Source Location           |
| ------------------------------------------------ | ------------------------------------------------------------------- | ------------------------ | ------------------------- |
| Invalid customer title                           | COMM-SUCCESS='N', GOBACK                                            | COMM-FAIL-CODE = 'T'     | P010 (line 408--412)      |
| Credit check PUT CONTAINER failed                | DISPLAY diagnostic, GET-ME-OUT-OF-HERE (EXEC CICS RETURN)           | COMM-FAIL-CODE = 'A'     | CC010 (line 623--635)     |
| Credit check RUN TRANSID failed                  | DISPLAY diagnostic, GET-ME-OUT-OF-HERE                              | COMM-FAIL-CODE = 'B'     | CC010 (line 647--659)     |
| FETCH ANY NOTFINISHED, zero responses            | DISPLAY diagnostic, GET-ME-OUT-OF-HERE                              | COMM-FAIL-CODE = 'C'     | CC010 (line 722--741)     |
| FETCH ANY NOTFND, zero responses                 | WS-CREDIT-CHECK-ERROR='Y', WS-FINISHED-FETCHING='Y'; no GET-ME-OUT-OF-HERE called | COMM-FAIL-CODE not set (missing) | CC010 (line 831--848) -- DEFECT |
| FETCH ANY INVREQ (no children)                   | DISPLAY diagnostic, GET-ME-OUT-OF-HERE                              | COMM-FAIL-CODE = 'D'     | CC010 (line 805--826)     |
| GET CONTAINER failed after successful FETCH      | DISPLAY diagnostic, GET-ME-OUT-OF-HERE                              | COMM-FAIL-CODE = 'E'     | CC010 (line 958--980)     |
| Child transaction ABENDed                        | GET-ME-OUT-OF-HERE                                                  | COMM-FAIL-CODE = 'F'     | CC010 (line 990--1006)    |
| Child transaction security error                 | DISPLAY diagnostic, GET-ME-OUT-OF-HERE                              | COMM-FAIL-CODE = 'G'     | CC010 (line 1009--1031)   |
| Child COMPSTATUS unknown                         | DISPLAY diagnostic, GET-ME-OUT-OF-HERE                              | COMM-FAIL-CODE = 'H'     | CC010 (line 1034--1056)   |
| Credit check error detected post-PERFORM         | DISPLAY diagnostic, GET-ME-OUT-OF-HERE                              | COMM-FAIL-CODE = 'G'     | P010 (line 429--448)      |
| DOB: year < 1601 or age > 150                    | WS-DATE-OF-BIRTH-ERROR='Y', GET-ME-OUT-OF-HERE                      | COMM-FAIL-CODE = 'O'     | DOBC010 (line 1427--1470) |
| DOB: CEEDAYS conversion failed                   | DISPLAY CEEDAYS error msg, GET-ME-OUT-OF-HERE                       | COMM-FAIL-CODE = 'Z'     | DOBC010 (line 1442--1449) |
| DOB: CEELOCT (today's Lilian) failed             | DISPLAY CEELOCT error msg, GET-ME-OUT-OF-HERE                       | COMM-FAIL-CODE not set   | DOBC010 (line 1456--1461) |
| DOB is in the future                             | WS-DATE-OF-BIRTH-ERROR='Y', GET-ME-OUT-OF-HERE                      | COMM-FAIL-CODE = 'Y'     | DOBC010 (line 1472--1475) |
| ENQ Named Counter failed                         | COMM-SUCCESS='N', GET-ME-OUT-OF-HERE                                | COMM-FAIL-CODE = '3'     | ENC010 (line 511--515)    |
| DEQ Named Counter failed                         | COMM-SUCCESS='N', GET-ME-OUT-OF-HERE                                | COMM-FAIL-CODE = '5'     | DNC010 (line 536--540)    |
| CUSTOMER READ/REWRITE (control for next num) failed (non-SYSIDERR) | DEQ, COMM-SUCCESS='N', GET-ME-OUT-OF-HERE          | COMM-FAIL-CODE = '4'     | GLCV010 (line 1374--1411) |
| CUSTOMER READ/REWRITE SYSIDERR retry exhausted (100 retries all SYSIDERR) | ELSE branch skipped; code falls through to ADD 1 on unread data | None raised -- silent data corruption | GLCV010 (line 1356--1412) -- DEFECT |
| CUSTOMER WRITE (new record) failed               | DEQ, COMM-SUCCESS='N', GET-ME-OUT-OF-HERE                           | COMM-FAIL-CODE = '1'     | WCV010 (line 1122--1127)  |
| Control record READ/REWRITE (post-write count update) fails silently | No RESP check; program proceeds to COMM-SUCCESS='Y' | None raised  | WCV010 (line 1133--1146) -- DEFECT |
| PROCTRAN INSERT failed (SQLCODE != 0)            | PERFORM POPULATE-TIME-DATE2 to capture timestamp; EXEC CICS LINK PROGRAM('ABNDPROC'); DEQ; EXEC CICS ABEND ABCODE('HWPT') | ABEND code 'HWPT' | WPD010 (line 1256--1323) |
| ABND-TIME string built with MM twice (bug)       | STRING uses WS-TIME-NOW-GRP-MM at both positions 3 and 5 instead of WS-TIME-NOW-GRP-SS at position 5 -- abend diagnostic time is HH:MM:MM not HH:MM:SS | ABEND diagnostic only; no functional impact on business data | WPD010 (line 1279--1285) -- DEFECT |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. P010 -- entry point: title validation, then dispatches to all sub-sections
2. POPULATE-TIME-DATE (PTD010) -- obtains current absolute time and formats DDMMYYYY + HHMMSS
3. CREDIT-CHECK (CC010) -- launches OCR1--OCR5 async, delays 3s, fetches and aggregates scores
4. DATE-OF-BIRTH-CHECK (DOBC010) -- calls CEEDAYS and CEELOCT to validate DOB; checks year range and future-date
5. ENQ-NAMED-COUNTER (ENC010) -- serialises access to CUSTOMER counter via CICS ENQ
6. UPD-NCS (UN010) -- PERFORMs GET-LAST-CUSTOMER-VSAM to allocate the next customer number
7. GET-LAST-CUSTOMER-VSAM (GLCV010) -- READ FOR UPDATE / ADD 1 / REWRITE on CUSTOMER control record; retries on SYSIDERR; silent fall-through if all retries fail
8. WRITE-CUSTOMER-VSAM (WCV010) -- writes new CUSTOMER record; updates control record count (no error check); triggers WRITE-PROCTRAN; DEQs ENQ
9. WRITE-PROCTRAN (WP010) -- dispatches to WRITE-PROCTRAN-DB2
10. WRITE-PROCTRAN-DB2 (WPD010) -- inserts PROCTRAN audit row; on SQL error PERFORMs POPULATE-TIME-DATE2 for abend timestamp then ABENDs with 'HWPT'
11. POPULATE-TIME-DATE2 (PTD2010) -- called only from WPD010 SQL error path; ASKTIME + FORMATTIME into WS-ORIG-DATE and WS-TIME-NOW for abend diagnostic record
12. DEQ-NAMED-COUNTER (DNC010) -- releases CICS ENQ on serialisation resource; called on success and on most failure paths
13. GET-ME-OUT-OF-HERE (GMOFH010) -- unconditional EXEC CICS RETURN; used as common exit from all error paths
14. CALL 'CEEDAYS' -- validates DOB is a real calendar date (LE runtime)
15. CALL 'CEELOCT' -- obtains today's Lilian day number for future-date comparison (LE runtime)
16. EXEC CICS LINK PROGRAM('ABNDPROC') -- invoked only on PROCTRAN SQL failure to record abend diagnostics
