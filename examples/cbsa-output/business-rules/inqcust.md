---
type: business-rules
program: INQCUST
program_type: online
status: draft
confidence: high
last_pass: 4
calls: []
called_by:
- BNK1DCS
- CREACC
- DELCUS
- INQACCCU
uses_copybooks:
- ABNDINFO
- CUSTOMER
- INQCUST
- SORTCODE
reads:
- CUSTOMER
writes: []
db_tables: []
transactions: []
mq_queues: []
---

# INQCUST -- Business Rules

## Program Purpose

INQCUST is an online CICS program that retrieves a single customer record from the VSAM CUSTOMER file by customer number and returns all customer fields to the calling program via the DFHCOMMAREA. The program supports three input modes: (1) a specific customer number, (2) all zeros (0000000000), which causes a random customer to be selected, and (3) all nines (9999999999), which causes the last (highest-key) customer record currently in use to be retrieved. If no matching record exists, the commarea is returned with INQCUST-INQ-SUCCESS set to 'N' and a fail code. On unrecoverable errors the program links to ABNDPROC and issues a CICS ABEND.

The section READ-CUSTOMER-NCS is named as if it calls a Named Counter Server (NCS), but no EXEC CICS GET COUNTER / QUERY COUNTER is issued. The NCS-CUST-NO-VALUE field and NCS-CUST-NO-ACT-NAME ('HBNKCUST') are defined in WORKING-STORAGE but NCS-CUST-NO-VALUE is used as a plain working variable populated by the VSAM browse in GET-LAST-CUSTOMER-VSAM. The NCS infrastructure is unused.

## Input / Output

| Direction | Resource              | Type | Description                                                                 |
| --------- | --------------------- | ---- | --------------------------------------------------------------------------- |
| IN        | DFHCOMMAREA (INQCUST) | CICS | Customer number (INQCUST-CUSTNO) supplied by caller; also receives results  |
| IN/OUT    | CUSTOMER              | CICS | VSAM KSDS read by key (CUSTOMER-KY = sort code + customer number)           |
| OUT       | DFHCOMMAREA (INQCUST) | CICS | All customer fields plus INQCUST-INQ-SUCCESS and INQCUST-INQ-FAIL-CD        |
| OUT       | ABNDINFO-REC          | CICS | Abend detail record passed to ABNDPROC on error                             |

## Business Rules

### Input Routing -- Customer Number Interpretation

| #  | Rule                              | Condition                                                              | Action                                                                                                                     | Source Location          |
| -- | --------------------------------- | ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| 1  | Zero means random customer        | INQCUST-CUSTNO = 0000000000                                            | Retrieve highest customer number via GET-LAST-CUSTOMER-VSAM (VSAM browse); store result in NCS-CUST-NO-VALUE; generate a random number in range 1..max seeded by EIBTASKN | P010 lines 190-207       |
| 2  | All-nines means last customer     | INQCUST-CUSTNO = 9999999999                                            | Retrieve highest customer number via GET-LAST-CUSTOMER-VSAM (VSAM browse) and use that as the lookup key                  | P010 lines 190-198       |
| 3  | Specific customer number          | INQCUST-CUSTNO is any value other than 0000000000 or 9999999999        | Use supplied value directly as REQUIRED-CUST-NUMBER; proceed to VSAM read                                                 | P010 lines 178-179       |
| 4  | NCS lookup must succeed           | After READ-CUSTOMER-NCS, INQCUST-INQ-SUCCESS = 'N'                    | Call GET-ME-OUT-OF-HERE immediately (return to caller with failure indication) -- random/last-customer path is abandoned   | P010 lines 193-197       |

### VSAM Customer Read -- Retry and Not-Found Handling

| #  | Rule                                         | Condition                                                                                                        | Action                                                                                                                    | Source Location      |
| -- | -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | -------------------- |
| 5  | Successful read sets success flag            | WS-CICS-RESP = DFHRESP(NORMAL) on EXEC CICS READ FILE('CUSTOMER')                                               | Set EXIT-VSAM-READ = 'Y', INQCUST-INQ-SUCCESS = 'Y'; GO TO RCV999 (exit loop)                                            | RCV010 lines 276-280 |
| 6  | SYSIDERR triggers automatic retry            | WS-CICS-RESP = DFHRESP(SYSIDERR)                                                                                 | Retry EXEC CICS READ up to 100 times with a 3-second delay between each attempt; exit loop on NORMAL or non-SYSIDERR     | RCV010 lines 282-303 |
| 7  | Random-customer not-found triggers re-roll   | WS-CICS-RESP = DFHRESP(NOTFND) AND INQCUST-CUSTNO = 0000000000 AND INQCUST-RETRY < 1000                         | Call GENERATE-RANDOM-CUSTOMER-AGAIN (increments retry counter, generates new random number) and loop back                 | RCV010 lines 310-315 |
| 8  | Random-customer retry limit exceeded         | WS-CICS-RESP = DFHRESP(NOTFND) AND INQCUST-CUSTNO = 0000000000 AND INQCUST-RETRY >= 1000                        | Set EXIT-VSAM-READ = 'Y', INQCUST-INQ-SUCCESS = 'N', INQCUST-INQ-FAIL-CD = '1'; return failure to caller                 | RCV010 lines 316-320 |
| 9  | All-nines not-found triggers last-key lookup | WS-CICS-RESP = DFHRESP(NOTFND) AND INQCUST-CUSTNO = 9999999999 AND WS-V-RETRIED = 'N'                           | Call GET-LAST-CUSTOMER-VSAM directly, move NCS-CUST-NO-VALUE (stale -- see Defect 5) to REQUIRED-CUST-NUMBER, set WS-V-RETRIED = 'Y', GO TO RCV999 to loop back once only | RCV010 lines 323-331 |
| 10 | All-nines second not-found causes CVR1 abend | WS-CICS-RESP = DFHRESP(NOTFND) AND INQCUST-CUSTNO = 9999999999 AND WS-V-RETRIED = 'Y'                           | None of the guarded NOTFND branches match (rule 9 already fired, rule 11 excludes 9999999999); execution falls through to generic error handler (line 357) which abends with CVR1 -- NOTFND on second all-nines retry is treated as an unrecoverable error | RCV010 lines 357-420 |
| 11 | Specific customer not found                  | WS-CICS-RESP = DFHRESP(NOTFND) AND INQCUST-CUSTNO NOT = 9999999999 AND INQCUST-CUSTNO NOT = 0000000000          | Copy REQUIRED-CUST-NUMBER into OUTPUT-DATA customer number field; set INQCUST-INQ-SUCCESS = 'N', INQCUST-INQ-FAIL-CD = '1', blank INQCUST-ADDR, blank INQCUST-NAME; GO TO RCV999 | RCV010 lines 339-351 |
| 12 | Any other VSAM error causes abend            | WS-CICS-RESP NOT = DFHRESP(NORMAL) after all not-found and SYSIDERR checks                                       | Populate ABNDINFO-REC (RESP, RESP2, APPLID, task number, TRANID, date/time, abend code 'CVR1', freeform message 'RCV010 - CUSTOMER VSAM RECORD KEY=... GAVE VSAM RC=...'), link to ABNDPROC, then EXEC CICS ABEND ABCODE('CVR1') CANCEL | RCV010 lines 357-420 |

### VSAM Browse for Last Customer Number -- Retry and Error Handling

| #  | Rule                                      | Condition                                                                                             | Action                                                                                            | Source Location        |
| -- | ----------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ---------------------- |
| 13 | STARTBR SYSIDERR retry                    | WS-CICS-RESP = DFHRESP(SYSIDERR) after EXEC CICS STARTBR FILE('CUSTOMER') with HIGH-VALUES key       | Retry STARTBR up to 100 times with 3-second delay; exit on NORMAL or non-SYSIDERR                | GLCV010 lines 580-597  |
| 14 | STARTBR non-NORMAL failure                | WS-CICS-RESP IS NOT EQUAL TO DFHRESP(NORMAL) after STARTBR (including after retries)                 | Set INQCUST-INQ-SUCCESS = 'N', INQCUST-INQ-FAIL-CD = '9'; GO TO GLCVE999 (exit section without READPREV) | GLCV010 lines 603-607  |
| 15 | READPREV SYSIDERR retry                   | WS-CICS-RESP = DFHRESP(SYSIDERR) after EXEC CICS READPREV FILE('CUSTOMER')                           | Retry READPREV up to 100 times with 3-second delay; exit on NORMAL or non-SYSIDERR               | GLCV010 lines 616-634  |
| 16 | READPREV non-NORMAL failure               | WS-CICS-RESP IS NOT EQUAL TO DFHRESP(NORMAL) after READPREV (including after retries)                | Set INQCUST-INQ-SUCCESS = 'N', INQCUST-INQ-FAIL-CD = '9'; GO TO GLCVE999                         | GLCV010 lines 636-640  |
| 17 | READPREV populates last customer key      | READPREV with RIDFLD(CUSTOMER-KY2) succeeds                                                           | CICS updates CUSTOMER-KY2 (specifically REQUIRED-CUST-NUMBER2) with the actual key of the record read -- this is the last-in-use customer number. OUTPUT-DATA receives the full record. | GLCV010 lines 609-614  |
| 18 | ENDBR SYSIDERR retry                      | WS-CICS-RESP = DFHRESP(SYSIDERR) after EXEC CICS ENDBR FILE('CUSTOMER')                              | Retry ENDBR up to 100 times with 3-second delay; exit on NORMAL or non-SYSIDERR                  | GLCV010 lines 647-661  |
| 19 | ENDBR non-NORMAL failure (scope defect)   | WS-CICS-RESP IS NOT EQUAL TO DFHRESP(NORMAL) after ENDBR retries (line 663)                          | Set INQCUST-INQ-SUCCESS = 'N', INQCUST-INQ-FAIL-CD = '9'; GO TO GLCVE999. DEFECT: this IF is nested inside the outer `IF WS-CICS-RESP = DFHRESP(SYSIDERR)` at line 647, so a non-NORMAL, non-SYSIDERR initial ENDBR response bypasses this check and falls through to unconditionally set INQCUST-INQ-SUCCESS = 'Y' at line 669 | GLCV010 lines 663-667  |
| 20 | Successful browse sets success            | All three browse operations (STARTBR, READPREV, ENDBR) return DFHRESP(NORMAL) (and no scope defect triggers) | Set INQCUST-INQ-SUCCESS = 'Y'; REQUIRED-CUST-NUMBER2 holds the last-in-use customer number (updated by CICS via RIDFLD on READPREV) | GLCV010 line 669       |

### READ-CUSTOMER-NCS -- VSAM Highest-Key Delegation (Misnomer)

| #  | Rule                                  | Condition                                                    | Action                                                                                                         | Source Location     |
| -- | ------------------------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- | ------------------- |
| 21 | Highest-key value propagation on success | After GET-LAST-CUSTOMER-VSAM, INQCUST-INQ-SUCCESS = 'Y'  | Move REQUIRED-CUST-NUMBER2 (highest customer number found via VSAM browse) to NCS-CUST-NO-VALUE for use in random-number generation or as direct lookup key | RCN010 lines 251-254 |

### Abend Handling -- VSAM RLS Storm Drain

| #  | Rule                                       | Condition                                                                           | Action                                                                                                                                                | Source Location     |
| -- | ------------------------------------------ | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| 22 | VSAM RLS abend codes intercepted           | MY-ABEND-CODE = 'AFCR', 'AFCS', or 'AFCT' (VSAM RLS abend codes)                  | Set WS-STORM-DRAIN = 'Y'; issue EXEC CICS SYNCPOINT ROLLBACK; set INQCUST-INQ-SUCCESS = 'N', INQCUST-INQ-FAIL-CD = '2'; EXEC CICS RETURN (no re-abend) | AH010 lines 464-549 |
| 23 | SYNCPOINT ROLLBACK failure during storm drain | WS-CICS-RESP NOT = DFHRESP(NORMAL) after SYNCPOINT ROLLBACK                      | Populate ABNDINFO-REC with abend code 'HROL' and freeform message 'AH010 -Unable to perform SYNCPOINT ROLLBACK. Possible integrity issue following VSAM RLS abend. EIBRESP=... RESP2=...'; link to ABNDPROC; EXEC CICS ABEND ABCODE('HROL') CANCEL | AH010 lines 477-540 |
| 24 | Non-storm-drain abends re-abend            | WS-STORM-DRAIN = 'N' at end of ABEND-HANDLING section                              | EXEC CICS ABEND ABCODE(MY-ABEND-CODE) NODUMP -- re-raises the original abend code                                                                    | AH010 lines 552-558 |

### Commarea Output Population

| #  | Rule                              | Condition                         | Action                                                                                                                                                          | Source Location     |
| -- | --------------------------------- | --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| 25 | Successful customer data returned | INQCUST-INQ-SUCCESS = 'Y'         | Move all customer fields from OUTPUT-DATA to DFHCOMMAREA: INQCUST-EYE, INQCUST-SCODE, INQCUST-CUSTNO, INQCUST-NAME, INQCUST-ADDR, INQCUST-DOB, INQCUST-CREDIT-SCORE, INQCUST-CS-REVIEW-DT; set INQCUST-INQ-FAIL-CD = '0' | P010 lines 220-238  |
| 26 | Initial state of result flags     | Program entry (unconditional)     | INQCUST-INQ-SUCCESS = 'N', INQCUST-INQ-FAIL-CD = '0' on every invocation before any processing                                                                 | P010 lines 175-176  |

### VSAM Key Construction

| #  | Rule                     | Condition        | Action                                                                                                                                   | Source Location   |
| -- | ------------------------ | ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| 27 | VSAM read key composition | Every invocation | CUSTOMER-KY is composed as REQUIRED-SORT-CODE (6 digits, set from SORTCODE constant = 987654) concatenated with REQUIRED-CUST-NUMBER (10 digits) | P010 lines 178-179 |

## Calculations

| Calculation                    | Formula / Logic                                                                                               | Input Fields                          | Output Field        | Source Location |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------- | ------------------------------------- | ------------------- | --------------- |
| Initial random customer number | RANDOM-CUSTOMER = ((NCS-CUST-NO-VALUE - 1) * FUNCTION RANDOM(EIBTASKN)) + 1                                  | NCS-CUST-NO-VALUE, EIBTASKN (seed)    | RANDOM-CUSTOMER     | GRC010 line 698 |
| Retry random customer number   | RANDOM-CUSTOMER = ((NCS-CUST-NO-VALUE - 1) * FUNCTION RANDOM) + 1 (no seed; uses previous random state)      | NCS-CUST-NO-VALUE                     | RANDOM-CUSTOMER     | GRCA10 line 708 |
| Retry counter increment        | ADD 1 TO INQCUST-RETRY GIVING INQCUST-RETRY                                                                   | INQCUST-RETRY                         | INQCUST-RETRY       | GRCA10 line 707 |

## Error Handling

| Condition                                    | Action                                                                      | Return Code / Abend | Source Location      |
| -------------------------------------------- | --------------------------------------------------------------------------- | ------------------- | -------------------- |
| CICS READ NOTFND, specific customer          | Return initialised record; set fail flag; blank name/address                | INQCUST-INQ-FAIL-CD = '1' | RCV010 lines 339-351 |
| CICS READ NOTFND, random customer, >1000 retries | Return failure; do not re-roll                                         | INQCUST-INQ-FAIL-CD = '1' | RCV010 lines 316-320 |
| CICS READ NOTFND, all-nines, second attempt  | Falls through all NOTFND guards (none match); treated as generic VSAM error | CVR1 abend          | RCV010 lines 357-420 |
| CICS READ SYSIDERR                           | Retry up to 100 times with 3-second delay between each attempt              | None if resolved; CVR1 abend if unresolved | RCV010 lines 282-303 |
| CICS READ other error (after all IF checks)  | Populate ABNDINFO-REC (code CVR1, freeform 'RCV010 - CUSTOMER VSAM RECORD KEY=... GAVE VSAM RC=...'); link ABNDPROC; ABEND CANCEL | CVR1 | RCV010 lines 357-420 |
| CICS STARTBR SYSIDERR                        | Retry up to 100 times with 3-second delay                                   | Fail code '9' if not resolved | GLCV010 lines 580-597 |
| CICS STARTBR non-NORMAL (after retries)      | Set success = 'N', fail code = '9'; skip READPREV and ENDBR                 | INQCUST-INQ-FAIL-CD = '9' | GLCV010 lines 603-607 |
| CICS READPREV non-NORMAL (after retries)     | Set success = 'N', fail code = '9'; skip ENDBR                              | INQCUST-INQ-FAIL-CD = '9' | GLCV010 lines 636-640 |
| CICS ENDBR non-NORMAL after SYSIDERR retries | Set success = 'N', fail code = '9'                                          | INQCUST-INQ-FAIL-CD = '9' | GLCV010 lines 663-667 |
| CICS ENDBR non-NORMAL, non-SYSIDERR initial response | DEFECT: failure check is scoped inside SYSIDERR-only IF block; non-SYSIDERR ENDBR failure silently falls through to set INQCUST-INQ-SUCCESS = 'Y' | Incorrect success response | GLCV010 lines 647-669 |
| VSAM RLS abend AFCR, AFCS, or AFCT           | SYNCPOINT ROLLBACK; return with success = 'N', fail code = '2'              | INQCUST-INQ-FAIL-CD = '2' | AH010 lines 464-548  |
| SYNCPOINT ROLLBACK failure                   | Populate ABNDINFO-REC (code HROL); link ABNDPROC; ABEND CANCEL              | HROL                | AH010 lines 477-540  |
| Any other abend (not RLS storm drain)        | Re-abend with original abend code using NODUMP                              | MY-ABEND-CODE (passthrough) | AH010 lines 552-558 |
| NCS/browse lookup failure (zero or nine input) | Return immediately via GET-ME-OUT-OF-HERE                                 | INQCUST-INQ-SUCCESS = 'N' | P010 lines 193-197 |
| ABND-TIME string bug (both paths)            | STRING at RCV010 line 383 and AH010 line 504 uses WS-TIME-NOW-GRP-MM twice; WS-TIME-NOW-GRP-SS is never referenced -- abend time is recorded as HH:MM:MM instead of HH:MM:SS | Diagnostic data defect | RCV010 lines 379-385; AH010 lines 500-506 |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. P010 (entry) -- Set abend handler label (ABEND-HANDLING); initialise INQCUST-INQ-SUCCESS = 'N', INQCUST-INQ-FAIL-CD = '0'; set REQUIRED-SORT-CODE from SORTCODE constant (987654) and REQUIRED-CUST-NUMBER from INQCUST-CUSTNO
2. P010 -- If INQCUST-CUSTNO = 0 or 9999999999: PERFORM READ-CUSTOMER-NCS to obtain the highest customer number in use via VSAM browse
3. READ-CUSTOMER-NCS (RCN010) -- Delegates to GET-LAST-CUSTOMER-VSAM; on success propagates REQUIRED-CUST-NUMBER2 (from RIDFLD after READPREV) into NCS-CUST-NO-VALUE
4. GET-LAST-CUSTOMER-VSAM (GLCV010) -- Issues EXEC CICS STARTBR FILE('CUSTOMER') with HIGH-VALUES key (CUSTOMER-KY2), then READPREV (CICS updates CUSTOMER-KY2/REQUIRED-CUST-NUMBER2 with actual last key found), then ENDBR; each step has SYSIDERR retry loop (up to 100 attempts, 3-second delay each)
5. P010 -- If INQCUST-CUSTNO = 0: PERFORM GENERATE-RANDOM-CUSTOMER to compute a random customer number seeded by EIBTASKN
6. GENERATE-RANDOM-CUSTOMER (GRC010) -- Resets INQCUST-RETRY to zero; computes RANDOM-CUSTOMER = ((NCS-CUST-NO-VALUE - 1) * FUNCTION RANDOM(EIBTASKN)) + 1
7. P010 -- Sets EXIT-VSAM-READ = 'N', EXIT-DB2-READ = 'N', WS-D-RETRIED = 'N', WS-V-RETRIED = 'N'
8. P010 -- PERFORM READ-CUSTOMER-VSAM UNTIL EXIT-VSAM-READ = 'Y' (loop; may iterate multiple times for random-customer re-rolls)
9. READ-CUSTOMER-VSAM (RCV010) -- INITIALIZE OUTPUT-DATA; EXEC CICS READ FILE('CUSTOMER') by CUSTOMER-KY; evaluate RESP for NORMAL / SYSIDERR / NOTFND / other; on NOTFND with zero input and retry < 1000 calls GENERATE-RANDOM-CUSTOMER-AGAIN and loops; on unrecoverable error populates ABNDINFO-REC (with defective HH:MM:MM time) and links to ABNDPROC ('ABNDPROC') then ABENDs CANCEL with code CVR1
10. GENERATE-RANDOM-CUSTOMER-AGAIN (GRCA10) -- Increments INQCUST-RETRY; recomputes RANDOM-CUSTOMER without seeding
11. POPULATE-TIME-DATE (PTD010) -- Called from RCV010 and AH010 error paths; issues EXEC CICS ASKTIME (ABSTIME) and EXEC CICS FORMATTIME (DDMMYYYY + TIME with DATESEP using system default separator) to populate WS-U-TIME, WS-ORIG-DATE, and WS-TIME-NOW
12. P010 -- If INQCUST-INQ-SUCCESS = 'Y': move all OUTPUT-DATA customer fields to DFHCOMMAREA output fields; set INQCUST-INQ-FAIL-CD = '0'
13. P010 -- PERFORM GET-ME-OUT-OF-HERE (unconditional terminal call)
14. GET-ME-OUT-OF-HERE (GMOFH010) -- Issues EXEC CICS RETURN; program terminates
15. ABEND-HANDLING (AH010) -- Invoked only if CICS intercepts an abend via the HANDLE ABEND label; evaluates MY-ABEND-CODE for VSAM RLS codes AFCR/AFCS/AFCT (storm drain path: SYNCPOINT ROLLBACK, return with fail code '2') or any other code (re-abend NODUMP)

## Source Defects Noted

| # | Location | Description |
| - | -------- | ----------- |
| 1 | RCV010 lines 379-385 | ABND-TIME STRING uses WS-TIME-NOW-GRP-MM for both the second and third tokens; WS-TIME-NOW-GRP-SS is never referenced. Abend time is recorded as HH:MM:MM instead of HH:MM:SS. Same pattern repeated in AH010 lines 500-506. |
| 2 | GLCV010 lines 647-669 | The non-NORMAL failure check for ENDBR (line 663) is inside the outer `IF WS-CICS-RESP = DFHRESP(SYSIDERR)` block. If ENDBR returns a non-NORMAL, non-SYSIDERR response on first attempt, the failure check is skipped and INQCUST-INQ-SUCCESS is unconditionally set to 'Y' (line 669), masking the ENDBR error. |
| 3 | RCV010 lines 323-351 | When INQCUST-CUSTNO = 9999999999 and the record is not found on the second attempt (WS-V-RETRIED = 'Y'), none of the NOTFND guards match (rule 9 is exhausted; rule 11 excludes 9999999999). Execution falls through to the generic error handler which abends CVR1 rather than returning a graceful not-found response. |
| 4 | WORKING-STORAGE NCS-CUST-NO-STUFF | NCS counter infrastructure (NCS-CUST-NO-ACT-NAME = 'HBNKCUST', NCS-CUST-NO-INC, etc.) is defined but no EXEC CICS GET/PUT/QUERY COUNTER command is ever issued. Section READ-CUSTOMER-NCS is misnamed; it performs a VSAM browse, not an NCS operation. |
| 5 | RCV010 line 329 | On the all-nines NOTFND retry path (WS-V-RETRIED = 'N'), RCV010 calls GET-LAST-CUSTOMER-VSAM directly (line 326), which updates REQUIRED-CUST-NUMBER2 but does NOT update NCS-CUST-NO-VALUE. The immediately following MOVE at line 329 moves NCS-CUST-NO-VALUE (the stale value set earlier in P010 via READ-CUSTOMER-NCS) rather than the freshly obtained REQUIRED-CUST-NUMBER2. The retry key is therefore always the same value that was used for the first attempt, making the retry redundant. Fix: replace `MOVE NCS-CUST-NO-VALUE TO REQUIRED-CUST-NUMBER` with `MOVE REQUIRED-CUST-NUMBER2 TO REQUIRED-CUST-NUMBER`. |
| 6 | WORKING-STORAGE lines 62-70, 90-127 | Several WORKING-STORAGE fields are defined but never referenced in the PROCEDURE DIVISION: HIGHEST-CUST-NUMBER (PIC 9(10)), EXIT-IMS-READ (PIC X), WS-PASSED-DATA group (WS-TEST-KEY, WS-SORT-CODE, WS-CUSTOMER-RANGE), WS-SORT-DIV, WS-DISP-CUST-NO-VAL, VAR-REMIX, VAR-REMIX2, SQLCODE-DISPLAY, WS-INVOKING-PROGRAM, WS-POINTER / WS-POINTER-BYTES / WS-POINTER-NUMBER / WS-POINTER-NUMBER-DISPLAY. These appear to be residue from a prior program template or shared skeleton. |
| 7 | RCV010 lines 339-342 | The specific-customer NOTFND guard (rule 11) redundantly tests `WS-CICS-RESP = DFHRESP(NOTFND)` twice in the compound condition: `(WS-CICS-RESP = DFHRESP(NOTFND) AND INQCUST-CUSTNO NOT = 9999999999) AND (WS-CICS-RESP = DFHRESP(NOTFND) AND INQCUST-CUSTNO NOT = 0000000000)`. The second NOTFND test is logically redundant since RESP cannot change between the two sub-conditions. This is harmless but indicates a coding pattern error; the intended condition is simply `WS-CICS-RESP = DFHRESP(NOTFND) AND INQCUST-CUSTNO NOT = 9999999999 AND INQCUST-CUSTNO NOT = 0000000000`. |
