---
type: business-rules
program: COTRN01C
program_type: online
status: draft
confidence: high
last_pass: 5
calls: []
called_by:
- COTRN00C
uses_copybooks:
- COCOM01Y
- COTRN01
- COTTL01Y
- CSDAT01Y
- CSMSG01Y
- CVTRA05Y
reads:
- TRANSACT
writes: []
db_tables: []
transactions:
- CT01
mq_queues: []
---

# COTRN01C -- Business Rules

## Program Purpose

COTRN01C is a CICS online program that displays the full detail of a single transaction record from the TRANSACT VSAM file. It is launched from the transaction list screen (COTRN00C / CT00) with a pre-selected transaction ID passed via the COMMAREA, or allows the user to enter a transaction ID manually. All displayed fields are read-only; the screen is a pure inquiry function with no update capability. The program returns control to the caller (typically COTRN00C) when the user presses PF3, or to the main menu (COMEN01C) if no caller is recorded.

## Input / Output

| Direction | Resource    | Type       | Description                                                        |
| --------- | ----------- | ---------- | ------------------------------------------------------------------ |
| IN        | TRANSACT    | CICS/VSAM  | Transaction master file; keyed read by TRAN-ID (16-byte key)       |
| IN        | COTRN1A     | CICS BMS   | BMS map COTRN1A in mapset COTRN01; receives user-entered Tran ID   |
| IN        | DFHCOMMAREA | CICS       | Inter-program communication area (CARDDEMO-COMMAREA)               |
| OUT       | COTRN1A     | CICS BMS   | BMS map COTRN1A; sends transaction detail to the terminal          |

## Business Rules

### Session Initialisation

| #  | Rule                                | Condition                                  | Action                                                                                     | Source Location      |
| -- | ----------------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------ | -------------------- |
| 1  | No COMMAREA -- redirect to sign-on  | EIBCALEN = 0                               | Move 'COSGN00C' to CDEMO-TO-PROGRAM; PERFORM RETURN-TO-PREV-SCREEN (XCTL to sign-on)      | MAIN-PARA (line 94)  |
| 2  | First entry -- initialise screen    | EIBCALEN > 0 AND NOT CDEMO-PGM-REENTER     | SET CDEMO-PGM-REENTER TO TRUE; initialise COTRN1AO to LOW-VALUES; set cursor on TRNIDINI (TRNIDINL = -1); cursor set unconditionally before evaluating pre-selected ID | MAIN-PARA (line 99)  |
| 3  | Pre-selected transaction from list  | CDEMO-CT01-TRN-SELECTED NOT = SPACES AND NOT = LOW-VALUES (first entry only) | Move CDEMO-CT01-TRN-SELECTED to TRNIDINI; PERFORM PROCESS-ENTER-KEY immediately without waiting for user input; then PERFORM SEND-TRNVIEW-SCREEN unconditionally (see design note below) | MAIN-PARA (line 103) |
| 4  | Re-entry -- receive screen first    | CDEMO-PGM-REENTER is TRUE (CDEMO-PGM-CONTEXT = 1) | PERFORM RECEIVE-TRNVIEW-SCREEN then EVALUATE EIBAID for key pressed                | MAIN-PARA (line 111) |

### AID Key Routing

| #  | Rule                                | Condition            | Action                                                                                                               | Source Location       |
| -- | ----------------------------------- | -------------------- | -------------------------------------------------------------------------------------------------------------------- | --------------------- |
| 5  | Enter key -- look up transaction    | EIBAID = DFHENTER    | PERFORM PROCESS-ENTER-KEY                                                                                            | MAIN-PARA (line 113)  |
| 6  | PF3 -- return to calling program    | EIBAID = DFHPF3 AND CDEMO-FROM-PROGRAM not blank | Move CDEMO-FROM-PROGRAM to CDEMO-TO-PROGRAM; PERFORM RETURN-TO-PREV-SCREEN        | MAIN-PARA (line 115)  |
| 7  | PF3 -- return to main menu if no caller | EIBAID = DFHPF3 AND CDEMO-FROM-PROGRAM = SPACES OR LOW-VALUES | Move 'COMEN01C' to CDEMO-TO-PROGRAM; PERFORM RETURN-TO-PREV-SCREEN           | MAIN-PARA (line 116)  |
| 8  | PF4 -- clear screen                 | EIBAID = DFHPF4      | PERFORM CLEAR-CURRENT-SCREEN: blank all screen fields and re-display empty form                                      | MAIN-PARA (line 123)  |
| 9  | PF5 -- go to transaction list       | EIBAID = DFHPF5      | Move 'COTRN00C' to CDEMO-TO-PROGRAM; PERFORM RETURN-TO-PREV-SCREEN                                                  | MAIN-PARA (line 125)  |
| 10 | Any other key -- invalid key error  | EIBAID = anything else | Move 'Y' to WS-ERR-FLG; move CCDA-MSG-INVALID-KEY to WS-MESSAGE; PERFORM SEND-TRNVIEW-SCREEN                      | MAIN-PARA (line 128)  |

### Transaction ID Validation (PROCESS-ENTER-KEY)

| #  | Rule                                | Condition                                        | Action                                                                                                                   | Source Location              |
| -- | ----------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ | ---------------------------- |
| 11 | Transaction ID is mandatory         | TRNIDINI OF COTRN1AI = SPACES OR LOW-VALUES      | Move 'Y' to WS-ERR-FLG; move 'Tran ID can NOT be empty...' to WS-MESSAGE; set TRNIDINL = -1; PERFORM SEND-TRNVIEW-SCREEN | PROCESS-ENTER-KEY (line 147) |
| 12 | Transaction ID present -- proceed   | TRNIDINI OF COTRN1AI NOT = SPACES OR LOW-VALUES  | Set TRNIDINL = -1; clear all 13 output display fields (TRNIDI...MZIPI) to SPACES; move TRNIDINI to TRAN-ID; PERFORM READ-TRANSACT-FILE | PROCESS-ENTER-KEY (line 153) |
| 13 | ERR-FLG not reset within PROCESS-ENTER-KEY | ERR-FLG-ON from prior error survives into PROCESS-ENTER-KEY | If WS-ERR-FLG is already 'Y' on entry, the field-clear block (line 158) and the field-populate block (line 176) are both skipped; only the initial EVALUATE re-runs. ERR-FLG is only reset to 'N' at MAIN-PARA entry (line 88). | PROCESS-ENTER-KEY (lines 158, 176) |

### Field Population After Successful Read

| #  | Rule                                       | Condition             | Action                                                                                                                                                                                                    | Source Location              |
| -- | ------------------------------------------ | --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| 14 | Populate all transaction detail fields     | NOT ERR-FLG-ON after READ-TRANSACT-FILE | Move TRAN-AMT to WS-TRAN-AMT; move 13 TRAN-RECORD fields to corresponding screen output fields: TRNIDI (TRAN-ID), CARDNUMI (TRAN-CARD-NUM), TTYPCDI (TRAN-TYPE-CD), TCATCDI (TRAN-CAT-CD), TRNSRCI (TRAN-SOURCE), TRNAMTI (WS-TRAN-AMT formatted), TDESCI (TRAN-DESC), TORIGDTI (TRAN-ORIG-TS), TPROCDTI (TRAN-PROC-TS), MIDI (TRAN-MERCHANT-ID), MNAMEI (TRAN-MERCHANT-NAME), MCITYI (TRAN-MERCHANT-CITY), MZIPI (TRAN-MERCHANT-ZIP); PERFORM SEND-TRNVIEW-SCREEN | PROCESS-ENTER-KEY (line 176) |
| 15 | Transaction amount display formatting      | Always when populating | TRAN-AMT (PIC S9(09)V99, signed packed decimal) is moved to WS-TRAN-AMT (PIC +99999999.99) for display -- sign is preserved and decimal point inserted for screen display | PROCESS-ENTER-KEY (line 177) |

### Navigation / Return Control

| #  | Rule                                        | Condition                                            | Action                                                                                                                       | Source Location                |
| -- | ------------------------------------------- | ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| 16 | RETURN-TO-PREV-SCREEN -- default target     | CDEMO-TO-PROGRAM = LOW-VALUES OR SPACES              | Move 'COSGN00C' to CDEMO-TO-PROGRAM as safety default before XCTL                                                           | RETURN-TO-PREV-SCREEN (line 199) |
| 17 | Set navigation breadcrumb before XCTL       | Always on RETURN-TO-PREV-SCREEN                      | Move WS-TRANID ('CT01') to CDEMO-FROM-TRANID; move WS-PGMNAME ('COTRN01C') to CDEMO-FROM-PROGRAM; move ZEROS to CDEMO-PGM-CONTEXT | RETURN-TO-PREV-SCREEN (line 202) |
| 18 | Transfer control to target program          | Always on RETURN-TO-PREV-SCREEN                      | EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA(CARDDEMO-COMMAREA) -- control does not return to this program              | RETURN-TO-PREV-SCREEN (line 205) |
| 19 | Pseudo-conversational return                | After every screen send (final statement in MAIN-PARA) | EXEC CICS RETURN TRANSID(WS-TRANID) COMMAREA(CARDDEMO-COMMAREA) -- WS-TRANID VALUE 'CT01'; program exits and re-enters on next terminal input | MAIN-PARA (line 136) |

### Screen Clear

| #  | Rule                                   | Condition        | Action                                                                                                                  | Source Location               |
| -- | -------------------------------------- | ---------------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| 20 | PF4 clears all input and output fields | EIBAID = DFHPF4  | PERFORM INITIALIZE-ALL-FIELDS: sets TRNIDINL = -1; moves SPACES to TRNIDINI, TRNIDI, CARDNUMI, TTYPCDI, TCATCDI, TRNSRCI, TRNAMTI, TDESCI, TORIGDTI, TPROCDTI, MIDI, MNAMEI, MCITYI, MZIPI, and WS-MESSAGE; then PERFORM SEND-TRNVIEW-SCREEN | CLEAR-CURRENT-SCREEN (line 301) |

### Screen Send Semantics

| #  | Rule                                | Condition        | Action                                                                                         | Source Location              |
| -- | ----------------------------------- | ---------------- | ---------------------------------------------------------------------------------------------- | ---------------------------- |
| 21 | Full terminal erase on every send   | Every SEND-TRNVIEW-SCREEN call | EXEC CICS SEND MAP('COTRN1A') MAPSET('COTRN01') FROM(COTRN1AO) ERASE CURSOR -- ERASE option clears the entire terminal screen before writing the map; no partial field updates are possible | SEND-TRNVIEW-SCREEN (line 219) |
| 22 | Cursor positioned on Tran ID input  | TRNIDINL = -1 on SEND | BMS places the cursor at the TRNIDINI field whenever TRNIDINL is -1; this is set on validation errors, on successful lookup, and on screen clear | PROCESS-ENTER-KEY (lines 151, 154); INITIALIZE-ALL-FIELDS (line 311) |

## Calculations

| Calculation              | Formula / Logic                                                      | Input Fields          | Output Field    | Source Location              |
| ------------------------ | -------------------------------------------------------------------- | --------------------- | --------------- | ---------------------------- |
| Transaction amount format | MOVE TRAN-AMT TO WS-TRAN-AMT: implicit COBOL picture editing converts S9(09)V99 packed decimal to +99999999.99 edit pattern with explicit sign and decimal point for screen display | TRAN-AMT (PIC S9(09)V99) | WS-TRAN-AMT (PIC +99999999.99) | PROCESS-ENTER-KEY (line 177) |
| Current date extraction  | MOVE FUNCTION CURRENT-DATE TO WS-CURDATE-DATA; year last two digits extracted with WS-CURDATE-YEAR(3:2); assembled as MM/DD/YY via WS-CURDATE-MM-DD-YY | FUNCTION CURRENT-DATE | CURDATEO OF COTRN1AO | POPULATE-HEADER-INFO (line 245) |
| Current time extraction  | Hours, minutes, seconds extracted from CURRENT-DATE result into WS-CURTIME-HH, WS-CURTIME-MM, WS-CURTIME-SS; assembled as HH:MM:SS via WS-CURTIME-HH-MM-SS | FUNCTION CURRENT-DATE | CURTIMEO OF COTRN1AO | POPULATE-HEADER-INFO (line 258) |

## Error Handling

| Condition                                    | Action                                                                                                                           | Return Code           | Source Location                 |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | --------------------- | ------------------------------- |
| EIBCALEN = 0 (no COMMAREA)                   | XCTL to COSGN00C -- program cannot operate without a session context                                                             | n/a (XCTL, no return) | MAIN-PARA (line 94)             |
| Transaction ID entered as spaces or low-values | Move 'Y' to WS-ERR-FLG; display 'Tran ID can NOT be empty...' in ERRMSGO; reposition cursor on input field; resend screen     | ERR-FLG-ON = 'Y'      | PROCESS-ENTER-KEY (line 147)    |
| CICS READ NOTFND (DFHRESP(NOTFND))           | Move 'Y' to WS-ERR-FLG; display 'Transaction ID NOT found...' in ERRMSGO; set TRNIDINL = -1; PERFORM SEND-TRNVIEW-SCREEN        | ERR-FLG-ON = 'Y'      | READ-TRANSACT-FILE (line 283)   |
| CICS READ any other non-NORMAL response      | DISPLAY 'RESP:' WS-RESP-CD 'REAS:' WS-REAS-CD to operator console; move 'Y' to WS-ERR-FLG; display 'Unable to lookup Transaction...' in ERRMSGO; set TRNIDINL = -1; PERFORM SEND-TRNVIEW-SCREEN | ERR-FLG-ON = 'Y'      | READ-TRANSACT-FILE (line 289)   |
| Invalid AID key pressed                      | Move 'Y' to WS-ERR-FLG; move CCDA-MSG-INVALID-KEY to WS-MESSAGE; PERFORM SEND-TRNVIEW-SCREEN                                    | ERR-FLG-ON = 'Y'      | MAIN-PARA (line 128)            |
| CDEMO-TO-PROGRAM blank on navigation         | Move 'COSGN00C' as safe fallback target before XCTL                                                                              | n/a                   | RETURN-TO-PREV-SCREEN (line 199) |
| CICS RECEIVE errors (RECEIVE-TRNVIEW-SCREEN) | RESP and RESP2 are captured into WS-RESP-CD and WS-REAS-CD but are never evaluated -- RECEIVE errors are silently ignored        | none checked          | RECEIVE-TRNVIEW-SCREEN (line 232) |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. MAIN-PARA -- entry point; initialises ERR-FLG-OFF and USR-MODIFIED-NO; clears WS-MESSAGE and ERRMSGO; tests EIBCALEN
2. RETURN-TO-PREV-SCREEN -- called when EIBCALEN = 0; XCTL to COSGN00C (no return)
3. RECEIVE-TRNVIEW-SCREEN -- called on re-entry; receives BMS map COTRN1A from terminal into COTRN1AI
4. EVALUATE EIBAID -- dispatches to PROCESS-ENTER-KEY, RETURN-TO-PREV-SCREEN, CLEAR-CURRENT-SCREEN, or error handler
5. PROCESS-ENTER-KEY -- validates TRNIDINI not empty; clears 13 display fields; moves TRNIDINI to TRAN-ID; calls READ-TRANSACT-FILE; populates 13 display fields if no error; calls SEND-TRNVIEW-SCREEN on success
6. READ-TRANSACT-FILE -- EXEC CICS READ DATASET(WS-TRANSACT-FILE) INTO(TRAN-RECORD) LENGTH(LENGTH OF TRAN-RECORD) RIDFLD(TRAN-ID) KEYLENGTH(LENGTH OF TRAN-ID) UPDATE; EVALUATE WS-RESP-CD for NORMAL / NOTFND / OTHER
7. SEND-TRNVIEW-SCREEN -- calls POPULATE-HEADER-INFO; moves WS-MESSAGE to ERRMSGO; EXEC CICS SEND MAP('COTRN1A') MAPSET('COTRN01') FROM(COTRN1AO) ERASE CURSOR
8. POPULATE-HEADER-INFO -- gets FUNCTION CURRENT-DATE; populates CCDA-TITLE01/02, WS-TRANID, WS-PGMNAME, date (MM/DD/YY), and time (HH:MM:SS) into map header fields
9. CLEAR-CURRENT-SCREEN -- calls INITIALIZE-ALL-FIELDS then SEND-TRNVIEW-SCREEN
10. INITIALIZE-ALL-FIELDS -- sets TRNIDINL = -1; moves SPACES to TRNIDINI and all 13 output fields plus WS-MESSAGE
11. EXEC CICS RETURN TRANSID(WS-TRANID) COMMAREA(CARDDEMO-COMMAREA) -- pseudo-conversational return; always the last statement in MAIN-PARA

### Notable Design Points

- **Unintended UPDATE lock**: The CICS READ at READ-TRANSACT-FILE (line 275) is issued with the UPDATE option even though COTRN01C is a view-only program and never issues a REWRITE or UNLOCK. This acquires an exclusive VSAM lock on the TRANSACT record for the duration of the CICS task. This is likely unintentional and may cause contention if the same record is viewed concurrently or while COTRN02C is adding records.

- **Double screen send on pre-selected entry**: When CDEMO-CT01-TRN-SELECTED is populated on first entry (line 103), PROCESS-ENTER-KEY is called (which itself calls SEND-TRNVIEW-SCREEN on both success and error paths), and then SEND-TRNVIEW-SCREEN is called again unconditionally at line 109. This results in two BMS SEND calls per task on the pre-selected path, regardless of whether PROCESS-ENTER-KEY succeeded or produced an error.

- **RECEIVE errors silently ignored**: RECEIVE-TRNVIEW-SCREEN captures RESP/RESP2 into WS-RESP-CD/WS-REAS-CD but the values are never evaluated. Any CICS RECEIVE error (e.g. MAPFAIL) is silently swallowed; the program continues as if input was received normally.

- **Unused working storage**: WS-USR-MODIFIED (and its 88-levels USR-MODIFIED-YES / USR-MODIFIED-NO) is initialised at line 89 and never referenced again anywhere in the PROCEDURE DIVISION. Similarly, WS-TRAN-DATE (PIC X(08) VALUE '00/00/00') is defined but never used.

- **CDEMO-CT01-TRN-SEL-FLG ignored**: The COMMAREA field CDEMO-CT01-TRN-SEL-FLG (a single-byte selection flag set by COTRN00C) is present in the COCOM01Y copybook but is never tested in COTRN01C. The program tests only CDEMO-CT01-TRN-SELECTED (the 16-byte transaction ID value) to determine whether a pre-selected transaction is available.

- **Pre-loaded Tran ID from COMMAREA**: CDEMO-CT01-TRN-SELECTED in the COMMAREA allows COTRN00C to pre-load the transaction ID, bypassing manual entry on the first invocation.

- **Re-entry flag**: The program uses CDEMO-PGM-CONTEXT (88 CDEMO-PGM-REENTER VALUE 1) as the pseudo-conversational re-entry flag -- value 0 means first entry, value 1 means the terminal has already seen the screen.

- **Exact-key VSAM read**: KEYLENGTH(LENGTH OF TRAN-ID) is specified on the CICS READ, meaning VSAM performs a generic-key or exact-key read depending on whether the key length matches the full defined key length of the TRANSACT file. Since TRAN-ID is 16 bytes and this is the full key, this is an exact-key lookup.
