---
type: business-rules
program: INQACCCU
program_type: online
status: draft
confidence: high
last_pass: 4
calls: []
called_by:
- BNK1CCA
- CREACC
- DELCUS
uses_copybooks:
- ABNDINFO
- ACCDB2
- ACCOUNT
- CUSTOMER
- INQACCCU
- INQCUST
- SORTCODE
reads: []
writes: []
db_tables:
- ACCOUNT
transactions: []
mq_queues: []
---

# INQACCCU -- Business Rules

## Program Purpose

INQACCCU is an online CICS program that retrieves all accounts associated with a given customer number. It accepts a customer number via DFHCOMMAREA, validates the customer exists by linking to INQCUST, then queries the ACCOUNT DB2 table using a cursor to return up to 20 account records. Results are returned to the caller in the COMMAREA (INQACCCU copybook structure).

## Input / Output

| Direction | Resource        | Type | Description                                                         |
| --------- | --------------- | ---- | ------------------------------------------------------------------- |
| IN        | DFHCOMMAREA     | CICS | Input customer number (CUSTOMER-NUMBER, PIC 9(10)) and control flags |
| OUT       | DFHCOMMAREA     | CICS | NUMBER-OF-ACCOUNTS, COMM-SUCCESS, COMM-FAIL-CODE, CUSTOMER-FOUND, ACCOUNT-DETAILS array (OCCURS 1 TO 20 DEPENDING ON NUMBER-OF-ACCOUNTS) |
| IN/OUT    | ACCOUNT (DB2)   | DB2  | Read via ACC-CURSOR; queries by ACCOUNT_CUSTOMER_NUMBER and ACCOUNT_SORTCODE |
| LINK      | INQCUST         | CICS | Customer existence check via EXEC CICS LINK PROGRAM('INQCUST ') |
| LINK      | ABNDPROC        | CICS | Abend handler linked on unrecoverable errors (WS-ABEND-PGM VALUE 'ABNDPROC') |

## Commarea Structure Notes

The INQACCCU copybook defines `ACCOUNT-DETAILS` as a variable-length table using `OCCURS 1 TO 20 DEPENDING ON NUMBER-OF-ACCOUNTS`. Callers must use NUMBER-OF-ACCOUNTS as the ODO object to correctly size the COMMAREA. Each ACCOUNT-DETAILS entry contains COMM-OPENED, COMM-LAST-STMT-DT, and COMM-NEXT-STMT-DT as PIC 9(8) formatted DDMMYYYY. Each date field also has a REDEFINES group with named sub-fields (e.g., COMM-OPENED-GROUP with COMM-OPENED-DAY, COMM-OPENED-MONTH, COMM-OPENED-YEAR) accessible to callers. The COMM-PCB-POINTER POINTER field in the COMMAREA is populated by the copybook but is not referenced anywhere in the INQACCCU PROCEDURE DIVISION. CUSTOMER-FOUND (PIC X) is part of the COMMAREA output -- callers can inspect it directly in addition to COMM-SUCCESS.

## Business Rules

### Input Validation

| #  | Rule                              | Condition                                           | Action                                                                                                 | Source Location |
| -- | --------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | --------------- |
| 1  | Customer number must not be zero  | `CUSTOMER-NUMBER IN DFHCOMMAREA = ZERO`             | Set CUSTOMER-FOUND = 'N', NUMBER-OF-ACCOUNTS = 0, exit CUSTOMER-CHECK (GO TO CC999)                   | CC010 (line 835) |
| 2  | Customer number must not be 9999999999 | `CUSTOMER-NUMBER IN DFHCOMMAREA = '9999999999'` | Set CUSTOMER-FOUND = 'N', NUMBER-OF-ACCOUNTS = 0, exit CUSTOMER-CHECK (GO TO CC999)                   | CC010 (line 841) |
| 3  | Customer must exist in system     | `INQCUST-INQ-SUCCESS = 'Y'` after LINK to INQCUST  | If 'Y': set CUSTOMER-FOUND = 'Y'. If not 'Y': set CUSTOMER-FOUND = 'N', NUMBER-OF-ACCOUNTS = 0        | CC010 (line 855) |

### Routing / Control

| #  | Rule                                      | Condition                    | Action                                                                                               | Source Location     |
| -- | ----------------------------------------- | ---------------------------- | ---------------------------------------------------------------------------------------------------- | ------------------- |
| 4  | Abort processing when customer not found  | `CUSTOMER-FOUND = 'N'` (after CUSTOMER-CHECK) | Set COMM-SUCCESS = 'N', COMM-FAIL-CODE = '1', perform GET-ME-OUT-OF-HERE (return to CICS)  | A010 (lines 215-219) |
| 5  | Maximum 20 accounts returned per customer | `NUMBER-OF-ACCOUNTS = 20` in FETCH loop    | Exit PERFORM loop regardless of remaining cursor rows                                                | FD010 (lines 463-464) |
| 6  | Initial state: processing not yet succeeded | Always on entry              | COMM-SUCCESS initialised to 'N', COMM-FAIL-CODE initialised to '0' before any processing begins     | A010 (lines 196-197) |

### Account Data Retrieval

| #  | Rule                                                       | Condition                  | Action                                                                                                          | Source Location     |
| -- | ---------------------------------------------------------- | -------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------------- |
| 7  | Cursor query filters by customer number AND sort code      | ACC-CURSOR declaration     | SELECT from ACCOUNT WHERE ACCOUNT_CUSTOMER_NUMBER = :HV-ACCOUNT-CUST-NO AND ACCOUNT_SORTCODE = :HV-ACCOUNT-SORTCODE FOR FETCH ONLY | Lines 74-93 (SQL DECLARE) |
| 8  | Sort code value comes from SORTCODE copybook constant      | `MOVE SORTCODE TO HV-ACCOUNT-SORTCODE` | The institution sort code is injected into the cursor query parameters                                | RAD010 (line 244)   |
| 9  | No accounts found (SQL +100) is a valid success condition  | `SQLCODE = +100` during FETCH | Set COMM-SUCCESS = 'Y', exit FETCH-DATA loop (GO TO FD999). Caller receives zero accounts.            | FD010 (lines 485-488) |
| 10 | Successful retrieval sets success flag                     | All rows fetched without error | Set COMM-SUCCESS = 'Y'                                                                                 | RAD010 (line 448)   |

### Account Field Mapping (FD010 per-row population)

Each fetched row is mapped from DB2 host variables into the ACCOUNT-DETAILS(NUMBER-OF-ACCOUNTS) table entry. The following fields are populated for each account:

| #  | Rule                                        | Condition     | Action                                                                   | Source Location       |
| -- | ------------------------------------------- | ------------- | ------------------------------------------------------------------------ | --------------------- |
| 11 | Eye-catcher copied from DB2                 | Each FETCH row | MOVE HV-ACCOUNT-EYECATCHER TO COMM-EYE(NUMBER-OF-ACCOUNTS)             | FD010 (line 587-588)  |
| 12 | Customer number copied from DB2             | Each FETCH row | MOVE HV-ACCOUNT-CUST-NO TO COMM-CUSTNO(NUMBER-OF-ACCOUNTS)             | FD010 (line 589-590)  |
| 13 | Sort code copied from DB2                   | Each FETCH row | MOVE HV-ACCOUNT-SORTCODE TO COMM-SCODE(NUMBER-OF-ACCOUNTS)             | FD010 (line 591-592)  |
| 14 | Account number copied from DB2              | Each FETCH row | MOVE HV-ACCOUNT-ACC-NO TO COMM-ACCNO(NUMBER-OF-ACCOUNTS)               | FD010 (line 593-594)  |
| 15 | Account type copied from DB2                | Each FETCH row | MOVE HV-ACCOUNT-ACC-TYPE TO COMM-ACC-TYPE(NUMBER-OF-ACCOUNTS)          | FD010 (line 595-596)  |
| 16 | Interest rate copied from DB2               | Each FETCH row | MOVE HV-ACCOUNT-INT-RATE TO COMM-INT-RATE(NUMBER-OF-ACCOUNTS)          | FD010 (line 597-598)  |
| 17 | Overdraft limit copied from DB2             | Each FETCH row | MOVE HV-ACCOUNT-OVERDRAFT-LIM TO COMM-OVERDRAFT(NUMBER-OF-ACCOUNTS)    | FD010 (line 608-609)  |
| 18 | Actual balance copied from DB2              | Each FETCH row | MOVE HV-ACCOUNT-ACTUAL-BAL TO COMM-ACTUAL-BAL(NUMBER-OF-ACCOUNTS)      | FD010 (line 628-629)  |
| 19 | Available balance copied from DB2           | Each FETCH row | MOVE HV-ACCOUNT-AVAIL-BAL TO COMM-AVAIL-BAL(NUMBER-OF-ACCOUNTS)        | FD010 (line 630-631)  |

### Date Reformatting

| #  | Rule                                            | Condition              | Action                                                                                                                                      | Source Location       |
| -- | ----------------------------------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| 20 | Account opened date reformatted from DB2 format | Always, for each row   | DB2 date (YYYY-MM-DD in HV-ACCOUNT-OPENED) moved to DB2-DATE-REFORMAT then STRINGed as DDMMYYYY into COMM-OPENED(n)                        | FD010 (lines 599-606) |
| 21 | Last statement date reformatted from DB2 format | Always, for each row   | DB2 date (HV-ACCOUNT-LAST-STMT) moved to DB2-DATE-REFORMAT then STRINGed as DDMMYYYY into COMM-LAST-STMT-DT(n)                             | FD010 (lines 610-617) |
| 22 | Next statement date reformatted from DB2 format | Always, for each row   | DB2 date (HV-ACCOUNT-NEXT-STMT) moved to DB2-DATE-REFORMAT then STRINGed as DDMMYYYY into COMM-NEXT-STMT-DT(n)                             | FD010 (lines 619-626) |

### Storm Drain (DB2 Connection Loss Detection)

| #  | Rule                                              | Condition                    | Action                                                                                              | Source Location       |
| -- | ------------------------------------------------- | ---------------------------- | --------------------------------------------------------------------------------------------------- | --------------------- |
| 23 | SQLCODE 923 triggers Storm Drain condition        | `SQLCODE = 923`              | Set STORM-DRAIN-CONDITION = 'DB2 Connection lost ', display diagnostic message                     | CFSDD010 (line 664)   |
| 24 | Any other non-zero SQLCODE is not Storm Drain     | `WHEN OTHER`                 | Set STORM-DRAIN-CONDITION = 'Not Storm Drain     '                                                  | CFSDD010 (line 667)   |

### ABEND Handling

| #  | Rule                                                     | Condition                          | Action                                                                                                                           | Source Location         |
| -- | --------------------------------------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ----------------------- |
| 25 | DB2 deadlock (AD2Z) produces diagnostic display then re-raises | `MY-ABEND-CODE = 'AD2Z'`      | Display SQLCODE, account number, SQLSTATE, SQLERRMC, SQLERRD(1-6); WS-STORM-DRAIN remains 'N' so abend is re-raised at line 817 with NODUMP CANCEL | AH010 (lines 708-721)   |
| 26 | VSAM RLS abend AFCR is Storm Drain candidate             | `MY-ABEND-CODE = 'AFCR'`           | Empty WHEN -- falls through to AFCT handling                                                                                    | AH010 (line 728)        |
| 27 | VSAM RLS abend AFCS is Storm Drain candidate             | `MY-ABEND-CODE = 'AFCS'`           | Empty WHEN -- falls through to AFCT handling                                                                                    | AH010 (line 730)        |
| 28 | VSAM RLS abend AFCT triggers Storm Drain handling        | `MY-ABEND-CODE = 'AFCT'`           | Set WS-STORM-DRAIN = 'Y', display message, EXEC CICS SYNCPOINT ROLLBACK; on rollback failure link to ABNDPROC and abend 'HROL'; set COMM-SUCCESS = 'N', EXEC CICS RETURN (no TRANSID -- terminates task) | AH010 (lines 732-813) |
| 29 | Any abend not matching storm drain codes is re-raised    | `WS-STORM-DRAIN = 'N'`             | EXEC CICS ABEND ABCODE(MY-ABEND-CODE) NODUMP CANCEL                                                                             | AH010 (lines 817-823)   |

## Calculations

| Calculation           | Formula / Logic                                                                                              | Input Fields                                                        | Output Field                         | Source Location       |
| --------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------- | ------------------------------------ | --------------------- |
| Account count         | `ADD 1 TO NUMBER-OF-ACCOUNTS GIVING NUMBER-OF-ACCOUNTS`                                                     | NUMBER-OF-ACCOUNTS (current)                                        | NUMBER-OF-ACCOUNTS                   | FD010 (line 583)      |
| Date reformat: opened | STRING DB2-DATE-REF-DAY, DB2-DATE-REF-MNTH, DB2-DATE-REF-YR DELIMITED BY SIZE                              | HV-ACCOUNT-OPENED (DB2 format YYYY-MM-DD via DB2-DATE-REFORMAT)    | COMM-OPENED(NUMBER-OF-ACCOUNTS)      | FD010 (lines 601-605) |
| Date reformat: last stmt | STRING DB2-DATE-REF-DAY, DB2-DATE-REF-MNTH, DB2-DATE-REF-YR DELIMITED BY SIZE                           | HV-ACCOUNT-LAST-STMT (DB2 format via DB2-DATE-REFORMAT)            | COMM-LAST-STMT-DT(NUMBER-OF-ACCOUNTS) | FD010 (lines 612-616) |
| Date reformat: next stmt | STRING DB2-DATE-REF-DAY, DB2-DATE-REF-MNTH, DB2-DATE-REF-YR DELIMITED BY SIZE                           | HV-ACCOUNT-NEXT-STMT (DB2 format via DB2-DATE-REFORMAT)            | COMM-NEXT-STMT-DT(NUMBER-OF-ACCOUNTS) | FD010 (lines 621-625) |

## Error Handling

| Condition                                           | Action                                                                                                                                       | Return Code          | Source Location         |
| --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- | ----------------------- |
| Customer not found (INQCUST returns failure)        | COMM-SUCCESS = 'N', COMM-FAIL-CODE = '1', EXEC CICS RETURN                                                                                  | COMM-FAIL-CODE = '1' | A010 (lines 215-219)    |
| SQLCODE non-zero on ACC-CURSOR OPEN                 | COMM-SUCCESS = 'N', CUSTOMER-FOUND = 'N', COMM-FAIL-CODE = '2', NUMBER-OF-ACCOUNTS = 0, EXEC CICS SYNCPOINT ROLLBACK, GO TO RAD999           | COMM-FAIL-CODE = '2' | RAD010 (lines 252-337)  |
| SQLCODE non-zero on ACC-CURSOR FETCH                | COMM-SUCCESS = 'N', CUSTOMER-FOUND = 'N', COMM-FAIL-CODE = '3', NUMBER-OF-ACCOUNTS = 0, EXEC CICS SYNCPOINT ROLLBACK, GO TO FD999            | COMM-FAIL-CODE = '3' | FD010 (lines 490-580)   |
| SQLCODE non-zero on ACC-CURSOR CLOSE                | COMM-SUCCESS = 'N', CUSTOMER-FOUND = 'N', COMM-FAIL-CODE = '4', EXEC CICS SYNCPOINT ROLLBACK, GO TO RAD999                                   | COMM-FAIL-CODE = '4' | RAD010 (lines 352-445)  |
| SYNCPOINT ROLLBACK fails (WS-CICS-RESP not NORMAL) after cursor OPEN | Populate ABNDINFO-REC (EIBRESP, EIBRESP2, APPLID, task, TRANID, date/time), ABND-CODE = 'HROL', LINK to ABNDPROC, EXEC CICS ABEND ABCODE('HROL') CANCEL | ABEND 'HROL' | RAD010 (lines 271-334)  |
| SYNCPOINT ROLLBACK fails after cursor CLOSE         | Same abend handler pattern as cursor OPEN failure; ABND-FREEFORM = 'RAD010(2)- Unable to perform Syncpoint Rollback...'                       | ABEND 'HROL'         | RAD010 (lines 374-442)  |
| SYNCPOINT ROLLBACK fails after FETCH error          | Same abend handler pattern; ABND-FREEFORM = 'FD010 - Unable to perform Syncpoint Rollback...'                                                 | ABEND 'HROL'         | FD010 (lines 513-576)   |
| SYNCPOINT ROLLBACK fails after VSAM RLS abend       | Same abend handler pattern; ABND-FREEFORM = 'AH010 -Unable to perform SYNCPOINT ROLLBACK...'                                                  | ABEND 'HROL'         | AH010 (lines 750-806)   |
| DB2 connection lost (SQLCODE 923)                   | STORM-DRAIN-CONDITION = 'DB2 Connection lost ', diagnostic DISPLAY; processing continues to COMM-FAIL-CODE assignment                         | Storm Drain flag set | CFSDD010 (lines 664-678) |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. A010 -- Entry point: initialise COMM-SUCCESS = 'N' and COMM-FAIL-CODE = '0'; register ABEND-HANDLING label via EXEC CICS HANDLE ABEND; move SORTCODE to REQUIRED-SORT-CODE OF CUSTOMER-KY (line 203)
2. CUSTOMER-CHECK (CC010) -- Validate customer number is not zero or 9999999999; EXEC CICS LINK PROGRAM('INQCUST ') with INQCUST-COMMAREA; set CUSTOMER-FOUND based on INQCUST-INQ-SUCCESS
3. A010 (post CUSTOMER-CHECK) -- If CUSTOMER-FOUND = 'N': set COMM-FAIL-CODE = '1', PERFORM GET-ME-OUT-OF-HERE (returns to CICS immediately)
4. READ-ACCOUNT-DB2 (RAD010) -- Move customer number and sort code to cursor host variables; EXEC SQL OPEN ACC-CURSOR; check SQLCODE
5. FETCH-DATA (FD010) -- PERFORM UNTIL SQLCODE NOT = 0 OR NUMBER-OF-ACCOUNTS = 20: EXEC SQL FETCH FROM ACC-CURSOR; handle SQLCODE +100 (no data) as success; reformat dates; populate COMM account array
6. RAD010 (post fetch) -- EXEC SQL CLOSE ACC-CURSOR; check SQLCODE; on success set COMM-SUCCESS = 'Y'
7. GET-ME-OUT-OF-HERE (GMOFH010) -- EXEC CICS RETURN; GOBACK (terminal exit point)
8. CHECK-FOR-STORM-DRAIN-DB2 (CFSDD010) -- Called on any non-zero SQLCODE; EVALUATE SQLCODE WHEN 923 set Storm Drain condition; DISPLAY if Storm Drain condition met
9. ABEND-HANDLING (AH010) -- CICS abend handler: EVALUATE MY-ABEND-CODE for AD2Z (DB2 deadlock diagnostics then re-raise with NODUMP CANCEL), AFCR/AFCS/AFCT (VSAM RLS Storm Drain with rollback); re-raise non-Storm-Drain abends
10. POPULATE-TIME-DATE (PTD010) -- EXEC CICS ASKTIME / FORMATTIME; populates WS-U-TIME, WS-ORIG-DATE, WS-TIME-NOW for abend diagnostic records

## Dead Code (WORKING-STORAGE Only)

The following WORKING-STORAGE fields are defined but never referenced in the PROCEDURE DIVISION. They appear to be remnants of a prior multi-datastore (VSAM/DB2 switchable) version of this program:

| Field                  | Definition                                      | Notes                                            |
| ---------------------- | ----------------------------------------------- | ------------------------------------------------ |
| DATA-STORE-TYPE        | PIC X with 88 DATASTORE-TYPE-DB2 VALUE '2' and 88 DATASTORE-TYPE-VSAM VALUE 'V' | Suggests the program once supported both DB2 and VSAM datastores dynamically |
| EXIT-BROWSE-LOOP       | PIC X VALUE 'N'                                 | Loop control flag never used                     |
| RETURNED-DATA          | 01 group with 12 sub-fields mirroring account layout | Never populated in PROCEDURE DIVISION       |
| DESIRED-KEY            | DESIRED-KEY-CUSTOMER PIC 9(10), DESIRED-KEY-SORTCODE PIC 9(6) | Never used                       |
| FETCH-DATA-CNT         | PIC 9(4) COMP                                   | Never incremented or tested                      |
| WS-CUST-ALT-KEY-LEN    | PIC S9(4) COMP VALUE +10                        | Never used                                       |
| CUSTOMER-AREA          | 01 group containing COPY CUSTOMER               | Populated by CUSTOMER copybook but never referenced in PROCEDURE DIVISION |
| OUTPUT-DATA            | 01 group containing COPY ACCOUNT                | Never populated or referenced                    |

## Code Defects Observed

| #  | Location             | Defect                                                                                                                          |
| -- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| 1  | RAD010 (line 297)    | ABND-TIME STRING uses WS-TIME-NOW-GRP-MM twice instead of HH:MM:SS -- seconds component is minutes again (same defect repeated at FD010 line 539, RAD010 line 400, and AH010 line 769) |
| 2  | RAD010 (line 309)    | ABND-FREEFORM message spells "Synpoint" (missing 'c') in the RAD010 cursor OPEN failure path: 'RAD010 - Unable to perform Synpoint Rollback' |
| 3  | RAD010 (line 326)    | DISPLAY message also spells "Synpoint" in the cursor OPEN failure path |
| 4  | RAD010 (lines 433-435) | DISPLAY message in cursor CLOSE rollback failure path incorrectly says 'DB2 CURSOR OPEN' instead of 'DB2 CURSOR CLOSE' |
| 5  | AH010 (line 798)     | DISPLAY message prints 'INQACCC' (missing trailing 'U') instead of 'INQACCCU' in the VSAM RLS abend rollback failure path |
| 6  | Frontmatter (prior)  | db_tables listed both ACC and ACCOUNT; only ACCOUNT is referenced in SQL. ACC is the cursor name (ACC-CURSOR), not a table. Corrected to ACCOUNT only. |
