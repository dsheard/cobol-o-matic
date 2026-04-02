---
type: business-rules
program: DBCRFUN
program_type: online
status: draft
confidence: high
last_pass: 5
calls: []
called_by:
- BNK1CRA
uses_copybooks:
- ABNDINFO
- ACCDB2
- ACCOUNT
- PAYDBCR
- PROCDB2
- PROCTRAN
- SORTCODE
reads: []
writes: []
db_tables:
- ACCOUNT
- PROCTRAN
transactions: []
mq_queues: []
---

# DBCRFUN -- Business Rules

## Program Purpose

DBCRFUN is a CICS-attached DB2 subroutine that applies debit or credit transactions to a bank account over the counter (teller) or via a payment link. It receives an account number and signed amount in its COMMAREA, reads the DB2 ACCOUNT table, validates the transaction (checking account type and available funds for debits), updates both the available balance and actual balance in the ACCOUNT table, and inserts a record into the PROCTRAN (Processed Transaction) table. It returns the updated balances and a success/failure code to the calling program (BNK1CRA). It has no standalone CICS transaction ID -- it is always invoked as a linked sub-program.

The sort code used by this program is the hardcoded value **987654** (from the SORTCODE copybook).

## Input / Output

| Direction | Resource             | Type | Description                                                                  |
| --------- | -------------------- | ---- | ---------------------------------------------------------------------------- |
| IN        | DFHCOMMAREA          | CICS | PAYDBCR layout: COMM-ACCNO (8), COMM-AMT (signed), COMM-FACILTYPE (facility) |
| IN/OUT    | ACCOUNT (DB2 table)  | DB2  | Read and updated: balances debited/credited by COMM-AMT                      |
| OUT       | PROCTRAN (DB2 table) | DB2  | Transaction record inserted on successful account update                     |
| OUT       | DFHCOMMAREA          | CICS | COMM-SUCCESS (Y/N), COMM-FAIL-CODE, COMM-AV-BAL, COMM-ACT-BAL returned       |
| OUT       | ABNDPROC             | CICS | LINK to abend handler program on unrecoverable error                         |

## Business Rules

### Initialisation

| #  | Rule                       | Condition               | Action                                                              | Source Location |
| -- | -------------------------- | ----------------------- | ------------------------------------------------------------------- | --------------- |
| 1  | Default success to failure | Entry (A010)            | COMM-SUCCESS set to 'N'; COMM-FAIL-CODE set to '0' at program start | A010 (line 201) |
| 2  | Populate sort code         | Entry (A010)            | SORTCODE constant (987654) moved to COMM-SORTC and DESIRED-SORT-CODE | A010 (line 211) |
| 3  | Register abend handler     | Entry (A010)            | EXEC CICS HANDLE ABEND LABEL(ABEND-HANDLING) registered             | A010 (line 207) |

### Account Retrieval

| #  | Rule                                 | Condition                                    | Action                                                                    | Source Location      |
| -- | ------------------------------------ | -------------------------------------------- | ------------------------------------------------------------------------- | -------------------- |
| 4  | Retrieve account by sort code + acc# | SELECT from ACCOUNT WHERE sort code and acc# | All 12 account fields fetched into HOST-ACCOUNT-ROW host variables        | UAD010 (line 245)    |
| 5  | Account not found -- fail code 1     | SQLCODE = +100 (no rows)                     | COMM-SUCCESS='N', COMM-FAIL-CODE='1'; CHECK-FOR-STORM-DRAIN-DB2 performed; GO TO UAD999 | UAD010 (line 283) |
| 6  | Account DB2 error -- fail code 2     | SQLCODE NOT = 0 AND SQLCODE NOT = +100       | COMM-SUCCESS='N', COMM-FAIL-CODE='2'; CHECK-FOR-STORM-DRAIN-DB2 performed; GO TO UAD999 | UAD010 (line 286) |

### Debit Transaction Validation (COMM-AMT < 0)

| #  | Rule                                            | Condition                                                                    | Action                                                          | Source Location   |
| -- | ----------------------------------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------- | ----------------- |
| 7  | Reject debit to MORTGAGE via payment link       | COMM-AMT < 0 AND HV-ACCOUNT-ACC-TYPE = 'MORTGAGE' AND COMM-FACILTYPE = 496  | COMM-SUCCESS='N', COMM-FAIL-CODE='4'; GO TO UAD999              | UAD010 (line 330) |
| 8  | Reject debit to LOAN via payment link           | COMM-AMT < 0 AND HV-ACCOUNT-ACC-TYPE = 'LOAN    ' AND COMM-FACILTYPE = 496  | COMM-SUCCESS='N', COMM-FAIL-CODE='4'; GO TO UAD999              | UAD010 (line 332) |
| 9  | Insufficient funds check (payment link only)    | COMM-AMT < 0 AND (HV-ACCOUNT-AVAIL-BAL + COMM-AMT) < 0 AND COMM-FACILTYPE = 496 | COMM-SUCCESS='N', COMM-FAIL-CODE='3'; GO TO UAD999          | UAD010 (line 344) |
| 10 | Teller debit bypasses funds check               | COMM-AMT < 0 AND COMM-FACILTYPE NOT = 496                                    | No funds check performed; proceeds directly to balance update   | UAD010 (line 307) |

### Credit-Path Payment-Link MORTGAGE/LOAN Restriction

The IF block at lines 368-376 is positioned **outside** the `IF COMM-AMT < 0` scope and is explicitly labelled in source comments as the credit-path guard ("Check to see whether a Credit is being requested from a MORTGAGE or LOAN account", line 355). It fires unconditionally for every transaction that reaches this point -- including any debit that passed rules 7-8 without exiting. In practice, debit transactions to MORTGAGE/LOAN accounts via payment link are already rejected at rules 7-8, so this block is the effective guard for credit-path payment-link transactions to those account types. A teller debit to any account type will pass through this block without triggering it (since COMM-FACILTYPE is not 496 for teller transactions).

| #  | Rule                                                     | Condition                                                                   | Action                                                          | Source Location   |
| -- | -------------------------------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------- | ----------------- |
| 11 | Reject payment-link credit to MORTGAGE account           | HV-ACCOUNT-ACC-TYPE = 'MORTGAGE' AND COMM-FACILTYPE = 496 (no AMT guard)   | COMM-SUCCESS='N', COMM-FAIL-CODE='4'; GO TO UAD999              | UAD010 (line 368) |
| 12 | Reject payment-link credit to LOAN account               | HV-ACCOUNT-ACC-TYPE = 'LOAN    ' AND COMM-FACILTYPE = 496 (no AMT guard)   | COMM-SUCCESS='N', COMM-FAIL-CODE='4'; GO TO UAD999              | UAD010 (line 370) |
| 13 | Teller transactions to MORTGAGE or LOAN are allowed      | COMM-FACILTYPE NOT = 496 (teller facility)                                  | No account-type restriction applied for teller transactions     | UAD010 (line 368) |

### COMM-FACILTYPE Semantics

| #  | Rule                               | Condition             | Meaning                                                                          | Source Location     |
| -- | ---------------------------------- | --------------------- | -------------------------------------------------------------------------------- | ------------------- |
| 14 | COMM-FACILTYPE = 496 means PAYMENT | COMM-FACILTYPE = 496  | Transaction originated from payment link (not teller); triggers extra validations | UAD010 (line 325)  |
| 15 | Other COMM-FACILTYPE means Teller  | COMM-FACILTYPE NOT = 496 | Transaction originated from teller counter; bypasses MORTGAGE/LOAN restrictions | UAD010 (line 325) |

### Balance Update

| #  | Rule                                         | Condition                         | Action                                                                                                                               | Source Location   |
| -- | -------------------------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------- |
| 16 | Apply debit/credit to available bal          | Account retrieved and validated   | HV-ACCOUNT-AVAIL-BAL = HV-ACCOUNT-AVAIL-BAL + COMM-AMT (signed add)                                                                 | UAD010 (line 384) |
| 17 | Apply debit/credit to actual balance         | Account retrieved and validated   | HV-ACCOUNT-ACTUAL-BAL = HV-ACCOUNT-ACTUAL-BAL + COMM-AMT (signed add)                                                               | UAD010 (line 386) |
| 18 | DB2 UPDATE rewrites all 12 account columns   | Always on UPDATE path             | Full-row UPDATE sets all 12 ACCOUNT columns (including eyecatcher, customer no., sort code, acc no., type, interest rate, dates, overdraft limit) -- not just the balance columns | UAD010 (line 392) |
| 19 | DB2 UPDATE failure -- fail code 2            | SQLCODE NOT = 0 after UPDATE      | COMM-SUCCESS='N', COMM-FAIL-CODE='2'; CHECK-FOR-STORM-DRAIN-DB2; GO TO UAD999                                                        | UAD010 (line 425) |
| 20 | Return updated balances unconditionally      | After UPDATE (before SQLCODE check) | COMM-AV-BAL = HV-ACCOUNT-AVAIL-BAL; COMM-ACT-BAL = HV-ACCOUNT-ACTUAL-BAL moved at lines 416-419 before SQLCODE is tested -- so even on UPDATE failure, modified in-memory balances are returned to caller | UAD010 (line 416) |

### PROCTRAN Record Classification

| #  | Rule                                      | Condition                              | PROCTRAN-TYPE | PROCTRAN-DESC             | Source Location    |
| -- | ----------------------------------------- | -------------------------------------- | ------------- | ------------------------- | ------------------ |
| 21 | Teller withdrawal sets transaction type   | COMM-AMT < 0 AND COMM-FACILTYPE NOT = 496 | 'DEB'      | 'COUNTER WTHDRW'          | WTPD010 (line 492) |
| 22 | Payment debit sets transaction type       | COMM-AMT < 0 AND COMM-FACILTYPE = 496  | 'PDR'         | COMM-ORIGIN(1:14)         | WTPD010 (line 499) |
| 23 | Teller deposit sets transaction type      | COMM-AMT >= 0 AND COMM-FACILTYPE NOT = 496 | 'CRE'     | 'COUNTER RECVED'          | WTPD010 (line 505) |
| 24 | Payment credit sets transaction type      | COMM-AMT >= 0 AND COMM-FACILTYPE = 496 | 'PCR'         | COMM-ORIGIN(1:14)         | WTPD010 (line 512) |
| 25 | PROCTRAN eyecatcher is always 'PRTR'      | Always                                 | n/a           | HV-PROCTRAN-EYECATCHER = 'PRTR' | WTPD010 (line 466) |
| 26 | PROCTRAN reference is CICS task number    | Always                                 | n/a           | EIBTASKN moved to WS-EIBTASKN12 (PIC 9(12)) then to HV-PROCTRAN-REF (PIC X(12)) | WTPD010 (line 469) |
| 27 | PROCTRAN date format is DD.MM.YYYY        | Always                                 | n/a           | FORMATTIME DDMMYYYY with DATESEP('.'); stored via WS-ORIG-DATE-GRP-X (dot-literal fillers) | WTPD010 (line 479) |
| 28 | PROCTRAN amount is COMM-AMT as-is         | Always                                 | n/a           | HV-PROCTRAN-AMOUNT = COMM-AMT (signed; negative for debit) | WTPD010 (line 519) |

### PROCTRAN Write Outcome

| #  | Rule                                        | Condition                                       | Action                                                                                 | Source Location    |
| -- | ------------------------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------- | ------------------ |
| 29 | Successful PROCTRAN write marks success     | SQLCODE = 0 after INSERT INTO PROCTRAN          | COMM-SUCCESS='Y', COMM-FAIL-CODE='0'                                                   | WTPD010 (line 649) |
| 30 | Failed PROCTRAN write triggers rollback     | SQLCODE NOT = 0 after INSERT INTO PROCTRAN      | EXEC CICS SYNCPOINT ROLLBACK issued to undo account update; COMM-SUCCESS='N'; COMM-FAIL-CODE='02' | WTPD010 (line 554) |
| 31 | Rollback failure triggers ABEND HROL        | SYNCPOINT ROLLBACK WS-CICS-RESP NOT = DFHRESP(NORMAL) | LINK to ABNDPROC; EXEC CICS ABEND ABCODE('HROL') CANCEL                        | WTPD010 (line 569) |

### Storm Drain (DB2 Workload Management)

| #  | Rule                                        | Condition              | Action                                                              | Source Location      |
| -- | ------------------------------------------- | ---------------------- | ------------------------------------------------------------------- | -------------------- |
| 32 | SQLCODE 923 triggers storm drain condition  | SQLCODE = 923          | STORM-DRAIN-CONDITION = 'DB2 Connection lost'; diagnostic DISPLAY   | CFSDD010 (line 677)  |
| 33 | Any other SQLCODE does not trigger drain    | SQLCODE WHEN OTHER     | STORM-DRAIN-CONDITION = 'Not Storm Drain'; no action                | CFSDD010 (line 680)  |

### Abend Handling

| #  | Rule                                             | Condition                             | Action                                                                          | Source Location  |
| -- | ------------------------------------------------ | ------------------------------------- | ------------------------------------------------------------------------------- | ---------------- |
| 34 | DB2 deadlock abend AD2Z -- diagnostic then re-abend | MY-ABEND-CODE = 'AD2Z'             | DISPLAY SQLCODE, SQLSTATE, SQLERRMC, SQLERRD(1-6); WS-STORM-DRAIN stays 'N'; falls through END-EVALUATE to re-ABEND with AD2Z NODUMP CANCEL | AH010 (line 720) |
| 35 | VSAM RLS abend AFCR -- storm drain + rollback    | MY-ABEND-CODE = 'AFCR'                | WS-STORM-DRAIN='Y'; SYNCPOINT ROLLBACK; COMM-SUCCESS='N'; COMM-FAIL-CODE='2'; EXEC CICS RETURN | AH010 (line 742) |
| 36 | VSAM RLS abend AFCS -- storm drain + rollback    | MY-ABEND-CODE = 'AFCS'                | Same as AFCR                                                                    | AH010 (line 743) |
| 37 | VSAM RLS abend AFCT -- storm drain + rollback    | MY-ABEND-CODE = 'AFCT'                | Same as AFCR                                                                    | AH010 (line 744) |
| 38 | VSAM RLS rollback failure triggers ABEND HROL    | AFCR/AFCS/AFCT rollback RESP not NORMAL | LINK to ABNDPROC with freeform message; EXEC CICS ABEND ABCODE('HROL') CANCEL  | AH010 (line 756) |
| 39 | All other abends re-ABENDed with original code   | WS-STORM-DRAIN = 'N' (not a drain)    | EXEC CICS ABEND ABCODE(MY-ABEND-CODE) NODUMP CANCEL                            | AH010 (line 834) |

### COMM-FAIL-CODE Summary

| Fail Code | Meaning                                               |
| --------- | ----------------------------------------------------- |
| '0'       | Initialisation / success state                        |
| '1'       | Account not found (SQLCODE = +100 on SELECT)          |
| '2'       | DB2 error on SELECT or UPDATE, or PROCTRAN write fail |
| '3'       | Insufficient available funds (payment link debit only)|
| '4'       | Debit or credit to MORTGAGE or LOAN via payment link  |
| '02'      | PROCTRAN INSERT failure (note: two-char string form)  |

## Calculations

| Calculation                 | Formula / Logic                                                                       | Input Fields                              | Output Field             | Source Location   |
| --------------------------- | ------------------------------------------------------------------------------------- | ----------------------------------------- | ------------------------ | ----------------- |
| Available balance update    | HV-ACCOUNT-AVAIL-BAL = HV-ACCOUNT-AVAIL-BAL + COMM-AMT                               | HV-ACCOUNT-AVAIL-BAL, COMM-AMT (signed)   | HV-ACCOUNT-AVAIL-BAL     | UAD010 (line 384) |
| Actual balance update       | HV-ACCOUNT-ACTUAL-BAL = HV-ACCOUNT-ACTUAL-BAL + COMM-AMT                             | HV-ACCOUNT-ACTUAL-BAL, COMM-AMT (signed)  | HV-ACCOUNT-ACTUAL-BAL    | UAD010 (line 386) |
| Sufficient funds check      | WS-DIFFERENCE = HV-ACCOUNT-AVAIL-BAL + COMM-AMT (negative COMM-AMT = debit; result < 0 means insufficient) | HV-ACCOUNT-AVAIL-BAL, COMM-AMT | WS-DIFFERENCE | UAD010 (line 341) |

Note: COMM-AMT is a signed PIC S9(10)V99 field. A negative value represents a debit; a positive value represents a credit. All balance arithmetic is a single signed addition, so debits reduce and credits increase the balance.

## Error Handling

| Condition                                                  | Action                                                          | Return Code        | Source Location      |
| ---------------------------------------------------------- | --------------------------------------------------------------- | ------------------ | -------------------- |
| SQLCODE NOT = 0 on SELECT (account not found: +100)        | COMM-SUCCESS='N'; COMM-FAIL-CODE='1'; storm drain check; exit  | FAIL-CODE '1'      | UAD010 (line 283)    |
| SQLCODE NOT = 0 on SELECT (other DB2 error)                | COMM-SUCCESS='N'; COMM-FAIL-CODE='2'; storm drain check; exit  | FAIL-CODE '2'      | UAD010 (line 286)    |
| SQLCODE NOT = 0 on UPDATE ACCOUNT                          | COMM-SUCCESS='N'; COMM-FAIL-CODE='2'; storm drain check; exit  | FAIL-CODE '2'      | UAD010 (line 425)    |
| SQLCODE NOT = 0 on INSERT INTO PROCTRAN                    | DISPLAY error; SYNCPOINT ROLLBACK; COMM-SUCCESS='N'; FAIL-CODE='02'; storm drain check | FAIL-CODE '02' | WTPD010 (line 554) |
| SYNCPOINT ROLLBACK fails (PROCTRAN path, RESP NOT NORMAL)  | LINK ABNDPROC; ABEND HROL                                       | ABEND 'HROL'       | WTPD010 (line 569)   |
| Abend code AD2Z (DB2 deadlock)                             | Diagnostic DISPLAYs (SQLSTATE, SQLERRD); WS-STORM-DRAIN stays 'N'; re-ABENDs with AD2Z NODUMP | MY-ABEND-CODE | AH010 (line 720) |
| Abend codes AFCR, AFCS, AFCT (VSAM RLS)                    | WS-STORM-DRAIN='Y'; SYNCPOINT ROLLBACK; RETURN                  | FAIL-CODE '2'      | AH010 (line 742)     |
| VSAM RLS rollback fails                                    | LINK ABNDPROC; ABEND HROL CANCEL                                | ABEND 'HROL'       | AH010 (line 756)     |
| All other abends (WS-STORM-DRAIN = 'N')                    | EXEC CICS ABEND ABCODE(MY-ABEND-CODE) NODUMP CANCEL             | Original abend code | AH010 (line 834)    |
| Storm drain SQLCODE 923 encountered                        | DISPLAY diagnostic message; no automatic recovery within this check | n/a           | CFSDD010 (line 677)  |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. A010 (PREMIERE SECTION) -- entry point; initialises COMM-SUCCESS='N' and COMM-FAIL-CODE='0'; registers abend handler; sets sort code
2. PERFORM UPDATE-ACCOUNT-DB2 -- retrieves account from DB2, validates, updates both balances, calls WRITE-TO-PROCTRAN
3. UPDATE-ACCOUNT-DB2 (UAD010) -- SELECT account; validate debit/credit rules; COMPUTE new balances; UPDATE ACCOUNT; PERFORM WRITE-TO-PROCTRAN on success
4. WRITE-TO-PROCTRAN (WTP010) -- dispatcher that PERFORMs WRITE-TO-PROCTRAN-DB2
5. WRITE-TO-PROCTRAN-DB2 (WTPD010) -- builds PROCTRAN host row; determines transaction type code (DEB/CRE/PDR/PCR); INSERT INTO PROCTRAN; on failure issues SYNCPOINT ROLLBACK
6. PERFORM GET-ME-OUT-OF-HERE (GMOOH010) -- EXEC CICS RETURN; GOBACK (GOBACK is dead code -- CICS RETURN never returns)
7. CHECK-FOR-STORM-DRAIN-DB2 (CFSDD010) -- EVALUATE SQLCODE WHEN 923; diagnostic display if storm drain condition met
8. ABEND-HANDLING (AH010) -- registered via HANDLE ABEND; EVALUATE MY-ABEND-CODE for AD2Z / AFCR / AFCS / AFCT; re-ABENDs for all others
9. POPULATE-TIME-DATE (PTD10) -- ASKTIME / FORMATTIME utility called from abend handler paths only
10. EXEC CICS LINK PROGRAM('ABNDPROC') -- called with ABNDINFO-REC COMMAREA when unrecoverable rollback failure occurs

### Data integrity note

The program does NOT use explicit DB2 cursor FOR UPDATE or SELECT FOR UPDATE. The ACCOUNT UPDATE and PROCTRAN INSERT are in the same CICS unit of work; if the INSERT fails, a SYNCPOINT ROLLBACK undoes the UPDATE, maintaining consistency. The program relies on DB2 implicit row-level locking during UPDATE execution.

Note that COMM-AV-BAL and COMM-ACT-BAL are set from the in-memory host variables at line 416 **before** the UPDATE SQLCODE is tested at line 425. If the UPDATE fails, the caller will receive modified balance values in the COMMAREA even though COMM-SUCCESS='N' -- a potential source of caller-side confusion.

### Code defect note

Both abend-info population paths (WTPD010 lines 591-596 and AH010 lines 778-783) contain a copy-paste defect in the ABND-TIME STRING statement: `WS-TIME-NOW-GRP-MM` (minutes) is referenced twice; `WS-TIME-NOW-GRP-SS` (seconds) is never referenced. As a result, the seconds position of ABND-TIME in the abend diagnostic record always contains the minutes value, producing a timestamp of the form `HH:MM:MM` instead of `HH:MM:SS`.

### Dead code note

The following fields are defined in WORKING-STORAGE or LOCAL-STORAGE but are never referenced in the PROCEDURE DIVISION:

- `DATA-STORE-TYPE` (PIC X) with 88-levels `DATASTORE-TYPE-DLI` (VALUE '1'), `DATASTORE-TYPE-DB2` (VALUE '2'), `DATASTORE-TYPE-VSAM` (VALUE 'V') -- vestigial from a multi-datastore design that was not implemented; the program only uses DB2.
- `WS-SUFFICIENT-FUNDS` (PIC X VALUE 'N') -- declared for a funds-check flag that was never used; the program uses WS-DIFFERENCE directly.
- `NEW-ACCOUNT-AVAILABLE-BALANCE` (PIC S9(10)V99 VALUE 0) -- unused intermediate balance field; balance arithmetic uses HV-ACCOUNT-AVAIL-BAL directly.
- `NEW-ACCOUNT-ACTUAL-BALANCE` (PIC S9(10)V99 VALUE 0) -- same; unused.
- `WS-PASSED-DATA` group (WS-TEST-KEY, WS-SORT-CODE, WS-CUSTOMER-RANGE-TOP/MIDDLE/BOTTOM) -- never set or read in the PROCEDURE DIVISION.
- `WS-ACC-REC-LEN` (PIC S9(4) COMP VALUE 0) -- record length placeholder; unused (no VSAM I/O in this program).
- `DB2-DATE-REFORMAT` group (DB2-DATE-REF-YR/MNTH/DAY) -- date-reformatting area never used.
- `PROCTRAN-RIDFLD` (PIC S9(8) COMP) -- VSAM RIDFLD placeholder; unused.
- `FILE-RETRY`, `WS-EXIT-RETRY-LOOP`, `SYSIDERR-RETRY` -- retry-loop scaffolding carried over from a VSAM template; never referenced.
- `WS-SQLCODE-DISP` (PIC 9(9) VALUE 0, LOCAL-STORAGE line 122) -- a second SQLCODE display field that duplicates `SQLCODE-DISPLAY` (line 168); never referenced in the PROCEDURE DIVISION.
- `NUMERIC-AMOUNT-DISPLAY` (PIC +9(10).99, WORKING-STORAGE line 176) -- formatted amount field, never populated or read in the PROCEDURE DIVISION.
