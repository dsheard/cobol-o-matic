---
type: business-rules
program: COTRN00C
program_type: online
status: draft
confidence: high
last_pass: 5
calls: []
called_by:
- COTRN01C
uses_copybooks:
- COCOM01Y
- COTRN00
- COTTL01Y
- CSDAT01Y
- CSMSG01Y
- CVTRA05Y
reads: []
writes: []
db_tables: []
transactions:
- CT00
mq_queues: []
---

# COTRN00C -- Business Rules

## Program Purpose

COTRN00C is a CICS online program that presents a paginated list of transactions read from the TRANSACT VSAM file. Users can browse up to 10 transactions per page, navigate forward (PF8) and backward (PF7), filter the starting position by entering a transaction ID, and select a single transaction for detail viewing (by entering 'S' in the selection field beside a row). A valid selection transfers control to COTRN01C via XCTL. The program operates under transaction ID CT00.

## Input / Output

| Direction | Resource     | Type | Description                                                         |
| --------- | ------------ | ---- | ------------------------------------------------------------------- |
| IN        | COTRN0A      | CICS | BMS map (mapset COTRN00) -- receives user keystrokes and selections |
| IN        | TRANSACT     | CICS | VSAM KSDS file browsed via STARTBR / READNEXT / READPREV / ENDBR   |
| IN        | DFHCOMMAREA  | CICS | Commarea carrying CARDDEMO-COMMAREA from calling program            |
| OUT       | COTRN0A      | CICS | BMS map (mapset COTRN00) -- sends the transaction list screen       |
| OUT       | COTRN01C     | CICS | XCTL transfer when user selects a transaction for detail view       |
| OUT       | COMEN01C     | CICS | XCTL transfer when user presses PF3 (return to main menu)           |
| OUT       | COSGN00C     | CICS | XCTL transfer when commarea is absent (unauthenticated access)      |

## Business Rules

### Entry and Session Initialisation

| #  | Rule                              | Condition                                 | Action                                                                                                                | Source Location            |
| -- | --------------------------------- | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| 1  | No commarea -- redirect to sign-on | `EIBCALEN = 0`                           | Set `CDEMO-TO-PROGRAM = 'COSGN00C'`, XCTL to sign-on screen via `RETURN-TO-PREV-SCREEN`                             | MAIN-PARA, line 107        |
| 2  | First entry -- display initial list | `NOT CDEMO-PGM-REENTER` (context = 0)   | Set `CDEMO-PGM-REENTER` to TRUE (context = 1), clear output map to LOW-VALUES, perform `PROCESS-ENTER-KEY` (which calls PROCESS-PAGE-FORWARD which calls SEND-TRNLST-SCREEN internally), then call `SEND-TRNLST-SCREEN` again directly. DEFECT: screen is painted twice on first entry -- see Defects section rule 60. | MAIN-PARA, lines 112--116  |
| 3  | Re-entry -- receive screen first  | `CDEMO-PGM-REENTER` (context = 1)        | RECEIVE map, then dispatch on EIBAID                                                                                  | MAIN-PARA, lines 118--134  |
| 4  | Persistent pseudo-conversation    | Always at end of MAIN-PARA                | `EXEC CICS RETURN TRANSID('CT00') COMMAREA(CARDDEMO-COMMAREA)` -- keeps transaction active                           | MAIN-PARA, lines 138--141  |

### Key Dispatch (EIBAID Routing)

| #  | Rule                        | Condition          | Action                                                                                         | Source Location          |
| -- | --------------------------- | ------------------ | ---------------------------------------------------------------------------------------------- | ------------------------ |
| 5  | ENTER key -- process input  | `EIBAID = DFHENTER` | Perform `PROCESS-ENTER-KEY`                                                                   | MAIN-PARA, lines 120--121 |
| 6  | PF3 -- return to main menu  | `EIBAID = DFHPF3`  | Set `CDEMO-TO-PROGRAM = 'COMEN01C'`, XCTL via `RETURN-TO-PREV-SCREEN`                         | MAIN-PARA, lines 123--124 |
| 7  | PF7 -- page backward        | `EIBAID = DFHPF7`  | Perform `PROCESS-PF7-KEY`                                                                      | MAIN-PARA, lines 125--126 |
| 8  | PF8 -- page forward         | `EIBAID = DFHPF8`  | Perform `PROCESS-PF8-KEY`                                                                      | MAIN-PARA, lines 127--128 |
| 9  | Any other key -- invalid    | `EIBAID = OTHER`   | Set `WS-ERR-FLG = 'Y'`, set cursor on TRNIDINI field, display message from `CCDA-MSG-INVALID-KEY`, send screen | MAIN-PARA, lines 130--133 |

### Transaction ID Filter Validation

| #  | Rule                                    | Condition                                                         | Action                                                                                                                  | Source Location                    |
| -- | --------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| 10 | Blank transaction ID -- browse from top | `TRNIDINI OF COTRN0AI = SPACES OR LOW-VALUES`                    | Move LOW-VALUES to TRAN-ID (STARTBR will position at beginning of file)                                                | PROCESS-ENTER-KEY, lines 206--207  |
| 11 | Transaction ID must be numeric          | `TRNIDINI OF COTRN0AI NOT = SPACES/LOW-VALUES` AND NOT NUMERIC   | Set `WS-ERR-FLG = 'Y'`, display 'Tran ID must be Numeric ...', set cursor, perform `SEND-TRNLST-SCREEN`. Execution then continues to `MOVE 0 TO CDEMO-CT00-PAGE-NUM` and `PERFORM PROCESS-PAGE-FORWARD` -- however ERR-FLG-ON causes PROCESS-PAGE-FORWARD to skip its main body (`IF NOT ERR-FLG-ON` at line 283), so no second page paint occurs. | PROCESS-ENTER-KEY, lines 209--218  |
| 12 | Valid numeric transaction ID            | `TRNIDINI OF COTRN0AI IS NUMERIC`                                | Move TRNIDINI to TRAN-ID for STARTBR positioning                                                                        | PROCESS-ENTER-KEY, lines 209--210  |
| 13 | ENTER always resets page counter to 0  | Always in PROCESS-ENTER-KEY before PROCESS-PAGE-FORWARD          | `MOVE 0 TO CDEMO-CT00-PAGE-NUM` -- page counter reset regardless of prior position, so PROCESS-PAGE-FORWARD increments to page 1 on every ENTER | PROCESS-ENTER-KEY, line 224 |

### Row Selection Validation

| #  | Rule                                         | Condition                                                                                      | Action                                                                                                            | Source Location                    |
| -- | -------------------------------------------- | ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| 14 | Selection field must be 'S' or 's'          | `CDEMO-CT00-TRN-SEL-FLG NOT = SPACES/LOW-VALUES` AND selection flag not 'S' or 's'           | Display 'Invalid selection. Valid value is S' is placed in WS-MESSAGE, cursor set to TRNIDINI; both `SET TRANSACT-EOF` and `PERFORM SEND-TRNLST-SCREEN` are commented out; WS-ERR-FLG is NOT set. Execution falls through to PROCESS-PAGE-FORWARD, which overwrites WS-MESSAGE with the refreshed page (DEFECT: error message is effectively lost -- see Defects rule 56). | PROCESS-ENTER-KEY, lines 196--203  |
| 15 | Valid selection 'S' -- navigate to detail   | `CDEMO-CT00-TRN-SEL-FLG = 'S' or 's'` AND `CDEMO-CT00-TRN-SELECTED NOT = SPACES/LOW-VALUES` | Set `CDEMO-TO-PROGRAM = 'COTRN01C'`, copy from/to program and tranid into commarea, set context = 0, XCTL to COTRN01C | PROCESS-ENTER-KEY, lines 186--195  |
| 16 | No row selected -- proceed to list display  | All `SEL000xI` fields are SPACES or LOW-VALUES                                                | Set `CDEMO-CT00-TRN-SEL-FLG` and `CDEMO-CT00-TRN-SELECTED` to SPACES, continue to browse                       | PROCESS-ENTER-KEY, lines 179--182  |
| 17 | Selection captured for rows 1-10 individually | `SEL0001I` through `SEL0010I NOT = SPACES AND LOW-VALUES` (evaluated in order via EVALUATE TRUE, first match wins) | Copy the corresponding `SELxxxxI` to `CDEMO-CT00-TRN-SEL-FLG` and `TRNIDxxI` to `CDEMO-CT00-TRN-SELECTED`    | PROCESS-ENTER-KEY, lines 148--182  |

### STARTBR Key Matching Behaviour

| #  | Rule                                         | Condition                            | Action                                                                                                                   | Source Location                    |
| -- | -------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ | ---------------------------------- |
| 18 | STARTBR uses EQUAL match (no GTEQ)          | GTEQ option is commented out         | STARTBR positions on an exact key match; if the supplied TRAN-ID is not found, DFHRESP(NOTFND) is returned (not a nearest-match browse) | STARTBR-TRANSACT-FILE, line 597   |
| 19 | LOW-VALUES key positions at start of file   | `TRAN-ID = LOW-VALUES`               | STARTBR with LOW-VALUES key and EQUAL (no GTEQ) will return NOTFND; program treats NOTFND as EOF and shows 'You are at the top of the page...' | STARTBR-TRANSACT-FILE, lines 605--611 |
| 20 | HIGH-VALUES key positions at end of file    | `TRAN-ID = HIGH-VALUES` (PF8 with no last ID) | STARTBR with HIGH-VALUES key and EQUAL will return NOTFND similarly; program treats NOTFND as EOF                   | STARTBR-TRANSACT-FILE, lines 605--611 |

### Pagination -- Forward (PF8 / Initial Load)

| #  | Rule                                               | Condition                                                         | Action                                                                                                                          | Source Location                     |
| -- | -------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| 21 | PF8 with no more pages -- suppress forward scroll  | `NEXT-PAGE-YES = 'N'` (NEXT-PAGE-NO is TRUE)                     | Display 'You are already at the bottom of the page...', set SEND-ERASE-NO, send screen without advancing                       | PROCESS-PF8-KEY, lines 267--273     |
| 22 | PF8 with last known transaction ID                 | `CDEMO-CT00-TRNID-LAST NOT = SPACES/LOW-VALUES`                  | Move `CDEMO-CT00-TRNID-LAST` to TRAN-ID for next STARTBR                                                                      | PROCESS-PF8-KEY, lines 259--263     |
| 23 | PF8 with no last ID                               | `CDEMO-CT00-TRNID-LAST = SPACES OR LOW-VALUES`                   | Move HIGH-VALUES to TRAN-ID (positions at end of file)                                                                          | PROCESS-PF8-KEY, lines 259--260     |
| 24 | Skip first record on forward browse (PF8)          | `EIBAID NOT = DFHENTER AND DFHPF7 AND DFHPF3` at line 285 -- condition is true when EIBAID is DFHPF8 (or any other unhandled key) | Perform one READNEXT before beginning to populate rows (skips the anchor record already shown on previous page)              | PROCESS-PAGE-FORWARD, lines 285--287 |
| 25 | Page forward loop reads up to 10 records           | `WS-IDX >= 11 OR TRANSACT-EOF OR ERR-FLG-ON` terminates loop     | PERFORM READNEXT-TRANSACT-FILE, POPULATE-TRAN-DATA, increment WS-IDX by 1 for each record read                                | PROCESS-PAGE-FORWARD, lines 297--303 |
| 26 | Peek-ahead determines if next page exists          | After filling 10 rows, if `TRANSACT-NOT-EOF AND ERR-FLG-OFF`     | Perform one additional READNEXT; if that read succeeds SET NEXT-PAGE-YES, else SET NEXT-PAGE-NO                                | PROCESS-PAGE-FORWARD, lines 305--313 |
| 27 | Page number incremented after successful full page | `TRANSACT-NOT-EOF AND ERR-FLG-OFF` after filling 10 rows          | `COMPUTE CDEMO-CT00-PAGE-NUM = CDEMO-CT00-PAGE-NUM + 1`                                                                        | PROCESS-PAGE-FORWARD, lines 306--307 |
| 28 | Partial page still increments page counter         | `WS-IDX > 1` when EOF reached before 10 rows                     | `COMPUTE CDEMO-CT00-PAGE-NUM = CDEMO-CT00-PAGE-NUM + 1`                                                                        | PROCESS-PAGE-FORWARD, lines 316--318 |
| 29 | Screen not sent if STARTBR fails with ERR-FLG     | `ERR-FLG-ON` after STARTBR (OTHER error only)                    | Entire page-forward block is skipped; error already displayed by STARTBR-TRANSACT-FILE. NOTE: STARTBR NOTFND does NOT set ERR-FLG-ON, so the page-forward block still executes after a NOTFND response -- see double-send note in Error Handling. | PROCESS-PAGE-FORWARD, lines 283--328 |
| 30 | Transaction ID input field blanked after page load | Always after PROCESS-PAGE-FORWARD logic completes (inside `IF NOT ERR-FLG-ON`) | `MOVE SPACE TO TRNIDINO OF COTRN0AO` at line 325                                                                 | PROCESS-PAGE-FORWARD, line 325      |

### Pagination -- Backward (PF7)

| #  | Rule                                              | Condition                                                           | Action                                                                                                                         | Source Location                      |
| -- | ------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------ |
| 31 | PF7 at first page -- suppress backward scroll    | `CDEMO-CT00-PAGE-NUM <= 1` (source checks `> 1` to permit, else suppresses) | Display 'You are already at the top of the page...', set SEND-ERASE-NO, send screen without scrolling              | PROCESS-PF7-KEY, lines 245--251      |
| 32 | PF7 pre-sets NEXT-PAGE-YES before browse         | Always at start of PROCESS-PF7-KEY, line 242                       | `SET NEXT-PAGE-YES TO TRUE` -- ensures the peek-behind in PROCESS-PAGE-BACKWARD can decrement the page counter correctly      | PROCESS-PF7-KEY, line 242            |
| 33 | PF7 with first known transaction ID              | `CDEMO-CT00-TRNID-FIRST NOT = SPACES/LOW-VALUES`                   | Move `CDEMO-CT00-TRNID-FIRST` to TRAN-ID for STARTBR                                                                          | PROCESS-PF7-KEY, lines 236--239      |
| 34 | PF7 with no first ID                             | `CDEMO-CT00-TRNID-FIRST = SPACES OR LOW-VALUES`                    | Move LOW-VALUES to TRAN-ID                                                                                                     | PROCESS-PF7-KEY, lines 236--237      |
| 35 | Backward loop reads up to 10 records in reverse  | `WS-IDX <= 0 OR TRANSACT-EOF OR ERR-FLG-ON` terminates loop; WS-IDX starts at 10 | PERFORM READPREV-TRANSACT-FILE, POPULATE-TRAN-DATA, decrement WS-IDX by 1 for each record                       | PROCESS-PAGE-BACKWARD, lines 351--357 |
| 36 | Skip anchor record on backward browse (PF7)      | `EIBAID NOT = DFHENTER AND DFHPF8` at line 339 -- condition is true when EIBAID is DFHPF7 (or any other unhandled key) | Perform one READPREV before beginning to populate rows                                                          | PROCESS-PAGE-BACKWARD, lines 339--341 |
| 37 | Page counter decremented on backward scroll      | `NEXT-PAGE-YES AND TRANSACT-NOT-EOF AND ERR-FLG-OFF AND CDEMO-CT00-PAGE-NUM > 1` | `SUBTRACT 1 FROM CDEMO-CT00-PAGE-NUM`                                                                         | PROCESS-PAGE-BACKWARD, lines 362--364 |
| 38 | Page counter reset to 1 at boundary              | Cannot subtract below 1 (else branch when `CDEMO-CT00-PAGE-NUM <= 1` or EOF) | `MOVE 1 TO CDEMO-CT00-PAGE-NUM`                                                                                          | PROCESS-PAGE-BACKWARD, lines 365--366 |

### Screen Display Rules

| #  | Rule                                           | Condition                                 | Action                                                                                                     | Source Location              |
| -- | ---------------------------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ---------------------------- |
| 39 | Screen erased on new page loads                | `SEND-ERASE-YES = 'Y'` (default)          | `EXEC CICS SEND MAP ... ERASE CURSOR` -- clears screen before painting                                    | SEND-TRNLST-SCREEN, line 534 |
| 40 | Screen NOT erased on boundary messages         | `SEND-ERASE-NO = 'N'`                     | `EXEC CICS SEND MAP ... CURSOR` without ERASE (ERASE option commented out in source) -- preserves current content, only updates message field | SEND-TRNLST-SCREEN, line 541 |
| 41 | Transaction ID input field cleared after list  | `NOT ERR-FLG-ON` after PROCESS-ENTER-KEY  | `MOVE SPACE TO TRNIDINO OF COTRN0AO` at line 228 -- blanks the filter field after successful browse from ENTER key | PROCESS-ENTER-KEY, line 228  |
| 42 | Page number shown in screen header             | Always when sending screen after page ops | `MOVE CDEMO-CT00-PAGE-NUM TO PAGENUMI OF COTRN0AI`                                                        | PROCESS-PAGE-FORWARD, line 324; PROCESS-PAGE-BACKWARD, line 373 |
| 43 | Screen rows cleared before each new page load  | Each page operation (forward/backward)    | PERFORM INITIALIZE-TRAN-DATA for WS-IDX 1 to 10, blanking TRNID, TDATE, TDESC, TAMT fields for all 10 rows | PROCESS-PAGE-FORWARD, lines 290--293; PROCESS-PAGE-BACKWARD, lines 344--347 |
| 44 | RECEIVE response codes captured but not tested | Always in RECEIVE-TRNLST-SCREEN          | WS-RESP-CD and WS-REAS-CD are populated from RESP/RESP2 but never evaluated; CICS errors from RECEIVE are silently ignored | RECEIVE-TRNLST-SCREEN, lines 556--562 |

### Data Population -- Row Display

| #  | Rule                                        | Condition                          | Action                                                                                                                 | Source Location              |
| -- | ------------------------------------------- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| 45 | Transaction date formatted from timestamp   | Always in POPULATE-TRAN-DATA       | Extract year (positions 3:2), month, and day from TRAN-ORIG-TS via WS-TIMESTAMP sub-fields, format as MM/DD/YY       | POPULATE-TRAN-DATA, lines 384--388 |
| 46 | First row in page anchors TRNID-FIRST       | `WS-IDX = 1`                       | `MOVE TRAN-ID TO TRNID01I OF COTRN0AI` AND `CDEMO-CT00-TRNID-FIRST` simultaneously                                  | POPULATE-TRAN-DATA, lines 392--393 |
| 47 | Last row in page anchors TRNID-LAST         | `WS-IDX = 10`                      | `MOVE TRAN-ID TO TRNID10I OF COTRN0AI` AND `CDEMO-CT00-TRNID-LAST` simultaneously                                   | POPULATE-TRAN-DATA, lines 438--439 |
| 48 | Amount formatted with sign and decimals     | Always in POPULATE-TRAN-DATA       | `MOVE TRAN-AMT TO WS-TRAN-AMT` where WS-TRAN-AMT is PIC +99999999.99 (edited with sign and two decimal places)     | POPULATE-TRAN-DATA, line 383 |
| 49 | Rows 2-9 do not update TRNID anchors        | `WS-IDX = 2` through `9`           | Only TRNID, TDATE, TDESC, TAMT screen fields are populated; commarea anchor fields unchanged                          | POPULATE-TRAN-DATA, lines 397--436 |
| 50 | POPULATE-TRAN-DATA WHEN OTHER -- no-op      | `WS-IDX` outside 1-10              | `CONTINUE` -- out-of-range index is silently ignored                                                                  | POPULATE-TRAN-DATA, lines 443--444 |
| 51 | INITIALIZE-TRAN-DATA WHEN OTHER -- no-op   | `WS-IDX` outside 1-10              | `CONTINUE` -- out-of-range index is silently ignored                                                                  | INITIALIZE-TRAN-DATA, lines 503--504 |

### Commarea Navigation Handoff

| #  | Rule                                               | Condition                                    | Action                                                                                                             | Source Location                      |
| -- | -------------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------ |
| 52 | Return-to-prev defaults to sign-on if no target    | `CDEMO-TO-PROGRAM = LOW-VALUES OR SPACES`    | `MOVE 'COSGN00C' TO CDEMO-TO-PROGRAM`                                                                             | RETURN-TO-PREV-SCREEN, lines 512--513 |
| 53 | From-tranid and from-program stamped before XCTL   | Always in RETURN-TO-PREV-SCREEN              | `MOVE WS-TRANID ('CT00') TO CDEMO-FROM-TRANID`, `MOVE WS-PGMNAME ('COTRN00C') TO CDEMO-FROM-PROGRAM`            | RETURN-TO-PREV-SCREEN, lines 515--516 |
| 54 | Context reset to 0 before XCTL                     | Always in RETURN-TO-PREV-SCREEN              | `MOVE ZEROS TO CDEMO-PGM-CONTEXT` -- target program will treat itself as first-entry                              | RETURN-TO-PREV-SCREEN, line 517      |
| 55 | ENDBR has no error handling                        | Always in ENDBR-TRANSACT-FILE                | `EXEC CICS ENDBR DATASET(WS-TRANSACT-FILE)` with no RESP clause -- CICS errors from ENDBR are silently ignored   | ENDBR-TRANSACT-FILE, lines 694--696  |

### Defects and Dead Code

| #  | Rule                                                  | Condition                                                     | Action                                                                                                                                                                                                                            | Source Location                            |
| -- | ----------------------------------------------------- | ------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| 56 | Invalid selection error message lost (dead code)      | `CDEMO-CT00-TRN-SEL-FLG` is not 'S' or 's'                  | Error message 'Invalid selection. Valid value is S' is placed in WS-MESSAGE, but both `SET TRANSACT-EOF` and `PERFORM SEND-TRNLST-SCREEN` are commented out. Execution falls through to PROCESS-PAGE-FORWARD, which calls SEND-TRNLST-SCREEN internally and overwrites WS-MESSAGE with the refreshed page data. The error is never displayed to the user. | PROCESS-ENTER-KEY, lines 197--202          |
| 57 | STARTBR NOTFND double-send defect                     | STARTBR returns DFHRESP(NOTFND)                               | NOTFND branch in STARTBR-TRANSACT-FILE calls SEND-TRNLST-SCREEN (first send). On return, `IF NOT ERR-FLG-ON` in PROCESS-PAGE-FORWARD is TRUE (NOTFND does not set ERR-FLG-ON), so PROCESS-PAGE-FORWARD continues and calls SEND-TRNLST-SCREEN again (second send). Screen is painted twice with the same content. | STARTBR-TRANSACT-FILE, lines 605--611; PROCESS-PAGE-FORWARD, line 326 |
| 58 | RECEIVE errors silently swallowed                     | Any CICS error on EXEC CICS RECEIVE                          | RESP and RESP2 are captured in WS-RESP-CD/WS-REAS-CD but never evaluated. Any AID key decode errors, MAPFAIL conditions, or other CICS errors from the RECEIVE are ignored without user notification.                            | RECEIVE-TRNLST-SCREEN, lines 556--562      |
| 59 | ENDBR errors silently swallowed                       | Any CICS error on EXEC CICS ENDBR                            | No RESP clause on the ENDBR command; the browse cursor close cannot be error-checked.                                                                                                                                             | ENDBR-TRANSACT-FILE, lines 694--696        |
| 60 | First-entry double-send defect                        | `NOT CDEMO-PGM-REENTER` (first entry, line 112)              | PROCESS-ENTER-KEY (line 115) calls PROCESS-PAGE-FORWARD (line 225), which calls SEND-TRNLST-SCREEN (line 326) -- first send. MAIN-PARA line 116 then calls SEND-TRNLST-SCREEN directly -- second send. Screen is painted twice with identical content on every first entry. | MAIN-PARA, lines 115--116; PROCESS-PAGE-FORWARD, line 326 |
| 61 | WS-PAGE-NUM field is dead working storage             | WS-PAGE-NUM (PIC S9(04) COMP, line 54) is never referenced in PROCEDURE DIVISION | All page counter operations use CDEMO-CT00-PAGE-NUM from the commarea. WS-PAGE-NUM is initialised to ZEROS by VALUE clause and never read or written. Dead field -- serves no runtime purpose. | WORKING-STORAGE, line 54                  |
| 62 | STARTBR NOTFND CONTINUE is unreachable no-op          | WHEN DFHRESP(NOTFND) at line 605                             | `CONTINUE` at line 606 executes as a no-op before `SET TRANSACT-EOF TO TRUE` at line 607. The CONTINUE provides no flow control -- subsequent statements in the same WHEN clause execute unconditionally. Same pattern in READNEXT ENDFILE at line 640. This appears to be a copy-paste artifact from the WHEN NORMAL branch, not intentional dead code, but it has no runtime effect. | STARTBR-TRANSACT-FILE, lines 605--607; READNEXT-TRANSACT-FILE, lines 639--641 |

## Calculations

| Calculation                    | Formula / Logic                                                              | Input Fields                              | Output Field              | Source Location                        |
| ------------------------------ | ---------------------------------------------------------------------------- | ----------------------------------------- | ------------------------- | -------------------------------------- |
| Page number reset on ENTER     | `MOVE 0 TO CDEMO-CT00-PAGE-NUM` before calling PROCESS-PAGE-FORWARD          | (literal 0)                               | CDEMO-CT00-PAGE-NUM       | PROCESS-ENTER-KEY, line 224            |
| Page number increment forward  | `COMPUTE CDEMO-CT00-PAGE-NUM = CDEMO-CT00-PAGE-NUM + 1`                     | CDEMO-CT00-PAGE-NUM                       | CDEMO-CT00-PAGE-NUM       | PROCESS-PAGE-FORWARD, lines 306--307, 317--318 |
| Page number decrement backward | `SUBTRACT 1 FROM CDEMO-CT00-PAGE-NUM`                                       | CDEMO-CT00-PAGE-NUM                       | CDEMO-CT00-PAGE-NUM       | PROCESS-PAGE-BACKWARD, line 364        |
| Row index increment (forward)  | `COMPUTE WS-IDX = WS-IDX + 1`                                               | WS-IDX                                    | WS-IDX                    | PROCESS-PAGE-FORWARD, line 301         |
| Row index decrement (backward) | `COMPUTE WS-IDX = WS-IDX - 1`                                               | WS-IDX                                    | WS-IDX                    | PROCESS-PAGE-BACKWARD, line 355        |
| Date extraction from timestamp | `WS-TIMESTAMP-DT-YYYY(3:2)` -> WS-CURDATE-YY, `WS-TIMESTAMP-DT-MM` -> WS-CURDATE-MM, `WS-TIMESTAMP-DT-DD` -> WS-CURDATE-DD; assembled as WS-CURDATE-MM-DD-YY | TRAN-ORIG-TS (PIC X(26)) via WS-TIMESTAMP | WS-TRAN-DATE (PIC X(08) = MM/DD/YY) | POPULATE-TRAN-DATA, lines 384--388 |
| Amount editing                 | `MOVE TRAN-AMT (PIC S9(09)V99) TO WS-TRAN-AMT (PIC +99999999.99)` -- implicit decimal alignment and sign insertion | TRAN-AMT | WS-TRAN-AMT               | POPULATE-TRAN-DATA, line 383           |
| Header date formatting         | `FUNCTION CURRENT-DATE` -> WS-CURDATE-DATA; extract MONTH, DAY, YEAR(3:2) into MM/DD/YY format | System clock | CURDATEO OF COTRN0AO | POPULATE-HEADER-INFO, lines 569--580 |
| Header time formatting         | Extract HOURS, MINUTE, SECOND from WS-CURDATE-DATA into HH:MM:SS format    | System clock (via WS-CURDATE-DATA)        | CURTIMEO OF COTRN0AO     | POPULATE-HEADER-INFO, lines 582--586   |

## Error Handling

| Condition                                        | Action                                                                                             | Return Code               | Source Location                             |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------------- | ------------------------- | ------------------------------------------- |
| EIBCALEN = 0 (no commarea)                       | XCTL to COSGN00C -- unauthenticated access redirected to sign-on                                  | n/a                       | MAIN-PARA, lines 107--109                   |
| Invalid attention key (not ENTER/PF3/PF7/PF8)   | Set ERR-FLG-ON, display CCDA-MSG-INVALID-KEY, set cursor on TRNIDINI, send screen                 | WS-ERR-FLG = 'Y'          | MAIN-PARA, lines 130--133                   |
| Transaction ID not numeric                       | Set ERR-FLG-ON, display 'Tran ID must be Numeric ...', set cursor on TRNIDINI, send screen         | WS-ERR-FLG = 'Y'          | PROCESS-ENTER-KEY, lines 212--217           |
| Invalid selection character (not S/s)            | Error message 'Invalid selection. Valid value is S' set in WS-MESSAGE; both SEND-TRNLST-SCREEN and SET TRANSACT-EOF are commented out; ERR-FLG NOT set; page refreshes instead of showing error (DEFECT) | n/a (ERR-FLG not set) | PROCESS-ENTER-KEY, lines 196--203 |
| PF7 at page 1 (already at top)                   | Display 'You are already at the top of the page...', SEND-ERASE-NO, send screen                   | n/a                       | PROCESS-PF7-KEY, lines 248--251             |
| PF8 with NEXT-PAGE-NO (already at bottom)        | Display 'You are already at the bottom of the page...', SEND-ERASE-NO, send screen                | n/a                       | PROCESS-PF8-KEY, lines 270--273             |
| STARTBR DFHRESP(NOTFND)                          | Set TRANSACT-EOF, display 'You are at the top of the page...', set cursor, send screen (first send). NOTFND does NOT set ERR-FLG-ON so PROCESS-PAGE-FORWARD's `IF NOT ERR-FLG-ON` block executes and calls SEND-TRNLST-SCREEN again (second send -- DEFECT: double-paint). | TRANSACT-EOF = 'Y' | STARTBR-TRANSACT-FILE, lines 605--611; PROCESS-PAGE-FORWARD, line 326 |
| STARTBR other CICS error                         | DISPLAY resp/reason codes to CICS log, set ERR-FLG-ON, display 'Unable to lookup transaction...', send screen | WS-ERR-FLG = 'Y'  | STARTBR-TRANSACT-FILE, lines 612--618       |
| READNEXT DFHRESP(ENDFILE)                        | Set TRANSACT-EOF, display 'You have reached the bottom of the page...', set cursor, send screen    | TRANSACT-EOF = 'Y'        | READNEXT-TRANSACT-FILE, lines 639--645      |
| READNEXT other CICS error                        | DISPLAY resp/reason codes, set ERR-FLG-ON, display 'Unable to lookup transaction...', send screen  | WS-ERR-FLG = 'Y'          | READNEXT-TRANSACT-FILE, lines 646--652      |
| READPREV DFHRESP(ENDFILE)                        | Set TRANSACT-EOF, display 'You have reached the top of the page...', set cursor, send screen       | TRANSACT-EOF = 'Y'        | READPREV-TRANSACT-FILE, lines 673--679      |
| READPREV other CICS error                        | DISPLAY resp/reason codes, set ERR-FLG-ON, display 'Unable to lookup transaction...', send screen  | WS-ERR-FLG = 'Y'          | READPREV-TRANSACT-FILE, lines 680--686      |
| RECEIVE error                                    | RESP/REAS codes captured in WS-RESP-CD/WS-REAS-CD but never evaluated -- RECEIVE errors are silently ignored | n/a              | RECEIVE-TRNLST-SCREEN, lines 556--562       |
| ENDBR error                                      | No RESP clause; CICS errors from ENDBR are silently ignored                                        | n/a                       | ENDBR-TRANSACT-FILE, lines 694--696         |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. MAIN-PARA -- entry point; initialises flags, checks EIBCALEN, dispatches on first-entry vs re-entry
2. RETURN-TO-PREV-SCREEN -- called immediately if EIBCALEN = 0; issues XCTL to COSGN00C
3. RECEIVE-TRNLST-SCREEN -- receives BMS map input on re-entry before key dispatch
4. PROCESS-ENTER-KEY -- handles ENTER: captures row selection, validates transaction ID, resets page counter to 0, calls PROCESS-PAGE-FORWARD
5. PROCESS-PF7-KEY -- handles PF7: guards page-1 boundary, pre-sets NEXT-PAGE-YES, sets anchor, calls PROCESS-PAGE-BACKWARD
6. PROCESS-PF8-KEY -- handles PF8: guards bottom boundary (NEXT-PAGE-NO), sets anchor, calls PROCESS-PAGE-FORWARD
7. PROCESS-PAGE-FORWARD -- STARTBR (EQUAL, no GTEQ), optional skip-read (PF8 only), 10-row READNEXT loop, peek-ahead, ENDBR, page counter update, SEND-TRNLST-SCREEN
8. PROCESS-PAGE-BACKWARD -- STARTBR (EQUAL, no GTEQ), optional skip-read (PF7 only), 10-row READPREV loop (index 10 down to 1), peek-behind for page counter, ENDBR, SEND-TRNLST-SCREEN
9. STARTBR-TRANSACT-FILE -- EXEC CICS STARTBR on TRANSACT dataset keyed by TRAN-ID; GTEQ commented out; handles NOTFND and OTHER errors
10. READNEXT-TRANSACT-FILE -- EXEC CICS READNEXT; handles ENDFILE and OTHER errors
11. READPREV-TRANSACT-FILE -- EXEC CICS READPREV; handles ENDFILE and OTHER errors
12. INITIALIZE-TRAN-DATA -- blanks all 10 display rows before repopulating (called once per page operation for WS-IDX 1 to 10)
13. POPULATE-TRAN-DATA -- moves TRAN-ID, formatted date (MM/DD/YY), TRAN-DESC, and edited TRAN-AMT to the appropriate screen row (determined by WS-IDX 1-10); row 1 updates CDEMO-CT00-TRNID-FIRST, row 10 updates CDEMO-CT00-TRNID-LAST
14. ENDBR-TRANSACT-FILE -- EXEC CICS ENDBR closes browse cursor after every page operation; no RESP checking
15. SEND-TRNLST-SCREEN -- POPULATE-HEADER-INFO, move WS-MESSAGE to ERRMSGO, EXEC CICS SEND (with or without ERASE)
16. POPULATE-HEADER-INFO -- obtains current date/time via FUNCTION CURRENT-DATE, formats as MM/DD/YY and HH:MM:SS, moves titles, tranid, pgmname to screen header fields
17. XCTL COTRN01C -- issued from within PROCESS-ENTER-KEY when a valid 'S' selection is confirmed; commarea carries TRAN-ID via CDEMO-CT00-TRN-SELECTED and context = 0
18. EXEC CICS RETURN (CT00) -- issued at end of MAIN-PARA to maintain the pseudo-conversational loop
