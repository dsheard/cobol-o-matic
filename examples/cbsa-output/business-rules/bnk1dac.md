---
type: business-rules
program: BNK1DAC
program_type: online
status: draft
confidence: high
last_pass: 5
calls:
- INQACC
- DELACC
- ABNDPROC
called_by: []
uses_copybooks:
- ABNDINFO
- BNK1DAM
- INQACC
- DFHAID
reads: []
writes: []
db_tables: []
transactions:
- ODAC
mq_queues: []
---

# BNK1DAC -- Business Rules

## Program Purpose

BNK1DAC is the Display Account / Delete Account CICS online program in the CBSA banking
application. It presents BMS map BNK1DA (mapset BNK1DAM) to the user, accepts an account
number, retrieves and displays the full account details by linking to INQACC, and -- on a
confirmed PF5 keypress -- deletes the account by linking to DELACC. It retains state across
screen interactions via COMMAREA under transaction ODAC.

## Input / Output

| Direction | Resource    | Type | Description                                                    |
| --------- | ----------- | ---- | -------------------------------------------------------------- |
| IN        | BNK1DA      | CICS | BMS map received from the terminal (account number entry)      |
| OUT       | BNK1DA      | CICS | BMS map sent to the terminal (account details or error msg)    |
| IN/OUT    | DFHCOMMAREA | CICS | Commarea (102 bytes) carrying WS-COMM-AREA across transactions |
| OUT       | INQACC      | CICS | LINK to INQACC program to retrieve account details            |
| OUT       | DELACC      | CICS | LINK to DELACC program to delete the account                  |
| OUT       | ABNDPROC    | CICS | LINK to abend handler on any CICS failure (most paragraphs)   |

## Business Rules

### Screen Navigation (A010 -- PREMIERE SECTION)

| #  | Rule                          | Condition                                | Action                                                                 | Source Location |
| -- | ----------------------------- | ---------------------------------------- | ---------------------------------------------------------------------- | --------------- |
| 1  | First invocation              | EIBCALEN = ZERO                          | Initialise WS-COMM-AREA; move LOW-VALUE to BNK1DAO; set cursor (ACCNOL = -1); SET SEND-ERASE; PERFORM SEND-MAP | A010 lines 196-201 |
| 2  | PA key -- ignore              | EIBAID = DFHPA1 OR DFHPA2 OR DFHPA3     | CONTINUE (no action)                                                   | A010 line 206   |
| 3  | PF3 -- return to main menu    | EIBAID = DFHPF3                          | EXEC CICS RETURN TRANSID('OMEN') IMMEDIATE (no error check on this RETURN) | A010 lines 212-218 |
| 4  | PF5 -- process delete request | EIBAID = DFHPF5                          | PERFORM PROCESS-MAP                                                    | A010 line 223   |
| 5  | PF12 -- end session           | EIBAID = DFHPF12                         | PERFORM SEND-TERMINATION-MSG; EXEC CICS RETURN (unconditional)         | A010 lines 230-235 |
| 6  | CLEAR -- erase screen         | EIBAID = DFHCLEAR                        | EXEC CICS SEND CONTROL ERASE FREEKB; EXEC CICS RETURN                 | A010 lines 240-247 |
| 7  | ENTER -- process enquiry      | EIBAID = DFHENTER                        | PERFORM PROCESS-MAP                                                    | A010 line 252   |
| 8  | Any other key -- invalid      | WHEN OTHER                               | Move LOW-VALUES to BNK1DAO; move 'Invalid key pressed.' to MESSAGEO; set cursor (ACCNOL = -1); SET SEND-DATAONLY-ALARM; PERFORM SEND-MAP | A010 lines 258-264 |

### Commarea Eyecatcher Validation (A010)

After the EVALUATE block (all cases), and only when EIBCALEN NOT = ZERO, BNK1DAC decides
what to carry forward in the COMMAREA that will be passed to TRANSID(ODAC) on RETURN.

| #  | Rule                              | Condition                                     | Action                                                                   | Source Location    |
| -- | --------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------ | ------------------ |
| 9  | Preserve INQACC data on return    | EIBCALEN NOT = ZERO AND INQACC-EYE = 'ACCT'  | Copy INQACC-EYE, CUSTNO, SCODE, ACCNO, ACC-TYPE, INT-RATE, OPENED, OVERDRAFT, LAST-STMT-DT, NEXT-STMT-DT, AVAIL-BAL, ACTUAL-BAL, SUCCESS into WS-COMM-AREA fields for use as the RETURN COMMAREA | A010 lines 274-288 |
| 10 | Invalid / absent eyecatcher       | EIBCALEN NOT = ZERO AND INQACC-EYE != 'ACCT' | INITIALIZE WS-COMM-AREA (discard stale or corrupt commarea data)         | A010 lines 289-291 |

Note: This logic runs unconditionally after the EVALUATE, including after PA-key CONTINUE and
after SEND-MAP on first entry. The eyecatcher check uses INQACC-EYE (from COPY INQACC), not
the 88-level PARMS-SUBPGM-EYE-VALID.

### Input Validation (EDIT-DATA -- ED010)

Invoked by PROCESS-MAP when ENTER is pressed.

| #  | Rule                              | Condition                               | Action                                                                   | Source Location    |
| -- | --------------------------------- | --------------------------------------- | ------------------------------------------------------------------------ | ------------------ |
| 11 | Account number mandatory          | ACCNOI = LOW-VALUES OR ACCNOL = 0       | Move 'Please enter an account number.' to MESSAGEO; set VALID-DATA-SW = 'N'; GO TO ED999 | ED010 lines 503-509 |
| 12 | Account number must be numeric    | ACCNOI NOT NUMERIC (after BIF DEEDIT)   | Move 'Please enter an account number.' to MESSAGEO; set VALID-DATA-SW = 'N' | ED010 lines 515-519 |

Note: EXEC CICS BIF DEEDIT is applied to ACCNOI at line 511 before the numeric check, stripping
editing characters (commas, decimal points, currency symbols) from the map input field.

### Pre-Delete Validation (VALIDATE-DATA -- VD010)

Invoked by PROCESS-MAP when PF5 is pressed. Reads COMM-SCODE and COMM-ACCNO from DFHCOMMAREA
(the inbound LINKAGE SECTION area, not WS-COMM-AREA) to confirm a prior successful enquiry
has been performed.

| #  | Rule                                      | Condition                                                     | Action                                                                               | Source Location    |
| -- | ----------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------ |
| 13 | Sortcode must be present for delete       | COMM-SCODE = ZEROES OR LOW-VALUES                             | Set VALID-DATA-SW = 'N'; move 'Please enter an account number.' to MESSAGEO; MOVE -1 TO ACCNOL (cursor to ACCNO field) | VD010 lines 530-538 |
| 14 | Account number must be present for delete | COMM-ACCNO = ZEROES OR LOW-VALUES                             | Same -- both conditions are combined in a single OR'd IF, so either alone triggers failure | VD010 lines 530-538 |

### Process-Map Dispatch Rules (PROCESS-MAP -- PM010)

| #  | Rule                                        | Condition                                | Action                                                              | Source Location    |
| -- | ------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------------- | ------------------ |
| 15 | ENTER path -- clear PARMS-SUBPGM on failure | VALID-DATA = 'N' after EDIT-DATA         | INITIALIZE PARMS-SUBPGM (prevents stale delete parms from DELACC link) | PM010 lines 388-390 |
| 16 | Always send map after processing            | Unconditional at end of PM010            | SET SEND-DATAONLY-ALARM TO TRUE; PERFORM SEND-MAP                   | PM010 lines 411-415 |

### Account Retrieval (GET-ACC-DATA -- GAD010)

| #  | Rule                                     | Condition                                                                | Action                                                                                               | Source Location    |
| -- | ---------------------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- | ------------------ |
| 17 | Set up INQACC commarea before link       | Always, before LINK to INQACC                                            | INITIALIZE PARMS-SUBPGM INQACC-COMMAREA; SET INQACC-PCB1-POINTER TO NULL; MOVE ACCNOI TO PARMS-SUBPGM-ACCNO AND INQACC-ACCNO | GAD010 lines 549-551 |
| 18 | Link to INQACC to retrieve account data  | VALID-DATA = 'Y' after EDIT-DATA                                         | EXEC CICS LINK PROGRAM('INQACC') COMMAREA(INQACC-COMMAREA) SYNCONRETURN                              | GAD010 lines 553-559 |
| 19 | Account not found                        | INQACC-ACC-TYPE = SPACES AND INQACC-INT-RATE = 0 AND INQACC-SUCCESS = 'N' | Move 'Sorry, but that account number was not found.' to MESSAGEO; clear all display fields (SORTCO, CUSTNOO, ACCNO2O, ACTYPEO, INTRTO, date fields, balances); set VALID-DATA-SW = 'N'; GO TO GAD999 | GAD010 lines 624-658 |
| 20 | Account found -- display data            | None of the not-found conditions match                                   | Populate SORTCO, CUSTNOO, ACCNO2O, ACTYPEO, INTRTO, OVERDRO from INQACC fields; split and display dates; display balances; move 'If you wish to delete the Account press <PF5>.' to MESSAGEO | GAD010 lines 664-696 |
| 21 | Date splitting -- opened date            | After successful lookup                                                  | INQACC-OPENED (8-digit YYYYMMDD stored as PIC 9(8)) moved to COMM-OPENED-SPLIT; subfields COMM-OPENED-SPLIT-DD (PIC 99), -MM (PIC 99), -YY (PIC 9999) moved to OPENDDO, OPENMMO, OPENYYO | GAD010 lines 670-673 |
| 22 | Date splitting -- last statement date    | After successful lookup                                                  | INQACC-LAST-STMT-DT moved to COMM-LAST-ST-SPLIT; LSTMTDDO, LSTMTMMO, LSTMTYYO populated            | GAD010 lines 677-680 |
| 23 | Date splitting -- next statement date    | After successful lookup                                                  | INQACC-NEXT-STMT-DT moved to COMM-NEXT-ST-SPLIT; NSTMTDDO, NSTMTMMO, NSTMTYYO populated            | GAD010 lines 682-685 |

### Account Deletion (DEL-ACC-DATA -- DAD010)

| #  | Rule                                          | Condition                                                      | Action                                                                                                                    | Source Location    |
| -- | --------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| 24 | Set up DELACC commarea before link            | Always, before LINK to DELACC                                  | INITIALIZE PARMS-SUBPGM; COMPUTE PARMS-SUBPGM-ACCNO = FUNCTION NUMVAL(ACCNO2I); SET PARMS-SUBPGM-DEL-PCB1/PCB2/PCB3 TO NULL | DAD010 lines 706-710 |
| 25 | Link to DELACC to delete the account          | VALID-DATA = 'Y' after VALIDATE-DATA (PF5 path)                | EXEC CICS LINK PROGRAM('DELACC') COMMAREA(PARMS-SUBPGM) SYNCONRETURN                                                     | DAD010 lines 712-718 |
| 26 | Delete failed -- account not found            | PARMS-SUBPGM-DEL-SUCCESS = 'N' AND PARMS-SUBPGM-DEL-FAIL-CD = '1' | Move sort code to SORTCO; message: 'Sorry, but that account number was not found. Account NOT deleted.'; set VALID-DATA-SW = 'N'; GO TO DAD999 | DAD010 lines 733-743 |
| 27 | Delete failed -- datastore error              | PARMS-SUBPGM-DEL-SUCCESS = 'N' AND PARMS-SUBPGM-DEL-FAIL-CD = '2' | Move sort code to SORTCO; message: 'Sorry, but a datastore error occurred. Account NOT deleted.'; set VALID-DATA-SW = 'N'; GO TO DAD999 | DAD010 lines 745-755 |
| 28 | Delete failed -- delete error (specific)      | PARMS-SUBPGM-DEL-SUCCESS = 'N' AND PARMS-SUBPGM-DEL-FAIL-CD = '3' | Move sort code to SORTCO; message: 'Sorry, but a delete error occurred. Account NOT deleted.'; set VALID-DATA-SW = 'N'; GO TO DAD999 | DAD010 lines 757-767 |
| 29 | Delete failed -- any other failure            | PARMS-SUBPGM-DEL-SUCCESS = 'N' (catch-all after codes 1-3)    | Move sort code to SORTCO; message: 'Sorry, but a delete error occurred. Account NOT deleted.'; set VALID-DATA-SW = 'N'; GO TO DAD999 | DAD010 lines 769-778 |
| 30 | Delete succeeded -- clear account fields      | PARMS-SUBPGM-DEL-SUCCESS != 'N' (all failure checks bypassed)  | Clear SORTCO, CUSTNOO, ACCNO2O, ACTYPEO, INTRTO, all date output fields, OVERDRO, AVBALO, ACTBALO; display 'Account [accno] was successfully deleted.' | DAD010 lines 783-814 |

Note: For deletion failure codes 1-3 and the catch-all, PARMS-SUBPGM-SCODE (the sort code
returned by DELACC in the commarea) is moved to the SORTCO display field before branching to
DAD999.

Note: DELACC commarea is populated using ACCNO2I (the map INPUT field, PIC X) via
FUNCTION NUMVAL, not from the displayed output field ACCNO2O. This means the account number
sent to DELACC is derived from what was last entered in the input field, not from the account
data returned by a prior INQACC call. If the map input field is stale or blank, NUMVAL may
yield zero, resulting in an incorrect delete request.

### Screen Send Logic (SEND-MAP -- SM010)

| #  | Rule                          | Condition                                 | Action                                                                                                                   | Source Location      |
| -- | ----------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | -------------------- |
| 31 | Send map with ERASE           | SEND-FLAG = '1' (88 SEND-ERASE)           | EXEC CICS SEND MAP('BNK1DA') MAPSET('BNK1DAM') FROM(BNK1DAO) ERASE FREEKB; on failure: ABNDPROC + ABEND-THIS-TASK        | SM010 lines 821-896  |
| 32 | Send data only (no alarm)     | SEND-FLAG = '2' (88 SEND-DATAONLY)        | **Defect:** if MESSAGEO IS NOT spaces AND IS NOT LOW-VALUES, overwrite it with 'Account lookup successful.' (existing non-empty messages are silently replaced); then EXEC CICS SEND MAP DATAONLY FREEKB; on failure: ABNDPROC + ABEND-THIS-TASK | SM010 lines 897-976  |
| 33 | Send data only with alarm     | SEND-FLAG = '3' (88 SEND-DATAONLY-ALARM)  | EXEC CICS SEND MAP DATAONLY ALARM FREEKB; on failure: ABNDPROC + ABEND-THIS-TASK                                         | SM010 lines 977-1052 |

Note on Rule 32 defect: The intent was presumably to display 'Account lookup successful.' only
when MESSAGEO is blank/empty. The actual code (lines 901-905) tests
`IF MESSAGEO IS NOT EQUAL SPACES AND MESSAGEO IS NOT EQUAL LOW-VALUES` and then overwrites --
meaning any populated message from GET-ACC-DATA or EDIT-DATA will be replaced by the generic
success message. The branch is therefore inverted.

## Calculations

| Calculation                  | Formula / Logic                                                                       | Input Fields                  | Output Field                 | Source Location    |
| ---------------------------- | ------------------------------------------------------------------------------------- | ----------------------------- | ---------------------------- | ------------------ |
| Account number from display  | COMPUTE PARMS-SUBPGM-ACCNO = FUNCTION NUMVAL(ACCNO2I)                                | ACCNO2I (map input field)     | PARMS-SUBPGM-ACCNO (PIC 9(8)) | DAD010 line 707   |
| Available balance display    | MOVE INQACC-AVAIL-BAL TO AVAILABLE-BALANCE-DISPLAY; then MOVE to AVBALO             | INQACC-AVAIL-BAL (S9(10)V99) | AVBALO via PIC +9(10).99      | GAD010 lines 687-689 |
| Actual balance display       | MOVE INQACC-ACTUAL-BAL TO ACTUAL-BALANCE-DISPLAY; then MOVE to ACTBALO              | INQACC-ACTUAL-BAL (S9(10)V99) | ACTBALO via PIC +9(10).99     | GAD010 lines 688-690 |
| Opened date split            | MOVE INQACC-OPENED TO COMM-OPENED-SPLIT (PIC 99 / 99 / 9999 subfields); extract DD/MM/YYYY | INQACC-OPENED (PIC 9(8))    | OPENDDO, OPENMMO, OPENYYO    | GAD010 lines 670-673 |
| Last statement date split    | MOVE INQACC-LAST-STMT-DT TO COMM-LAST-ST-SPLIT; extract DD/MM/YYYY                  | INQACC-LAST-STMT-DT (PIC 9(8)) | LSTMTDDO, LSTMTMMO, LSTMTYYO | GAD010 lines 677-680 |
| Next statement date split    | MOVE INQACC-NEXT-STMT-DT TO COMM-NEXT-ST-SPLIT; extract DD/MM/YYYY                  | INQACC-NEXT-STMT-DT (PIC 9(8)) | NSTMTDDO, NSTMTMMO, NSTMTYYO | GAD010 lines 682-685 |

## Error Handling

| Condition                                | Action                                                                                      | Return Code / Abend | Source Location        |
| ---------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------- | ---------------------- |
| EXEC CICS RETURN TRANSID(ODAC) fails     | INITIALIZE ABNDINFO-REC; populate ABND fields; EXEC CICS ASSIGN APPLID; PERFORM POPULATE-TIME-DATE; STRING abend freeform; LINK ABNDPROC; INITIALIZE WS-FAIL-INFO; PERFORM ABEND-THIS-TASK | ABEND 'HBNK' | A010 lines 303-360 |
| EXEC CICS RECEIVE MAP fails              | INITIALIZE ABNDINFO-REC; populate ABND fields; LINK ABNDPROC; INITIALIZE WS-FAIL-INFO; PERFORM ABEND-THIS-TASK | ABEND 'HBNK' | RM010 lines 434-492 |
| EXEC CICS LINK INQACC fails              | INITIALIZE ABNDINFO-REC; populate ABND fields; LINK ABNDPROC; INITIALIZE WS-FAIL-INFO; PERFORM ABEND-THIS-TASK | ABEND 'HBNK' | GAD010 lines 561-618 |
| INQACC-SUCCESS = 'N' (account not found) | Move error message to MESSAGEO; clear display fields; VALID-DATA-SW = 'N'; GO TO GAD999   | None (screen error) | GAD010 lines 624-658   |
| EXEC CICS LINK DELACC fails              | INITIALIZE WS-FAIL-INFO only; PERFORM ABEND-THIS-TASK (ABNDPROC is NOT linked -- diverges from all other error paths) | ABEND 'HBNK' | DAD010 lines 720-727 |
| DELACC returns DEL-FAIL-CD = '1'         | Display error; VALID-DATA-SW = 'N'; GO TO DAD999                                           | None (screen error) | DAD010 lines 733-743   |
| DELACC returns DEL-FAIL-CD = '2'         | Display error; VALID-DATA-SW = 'N'; GO TO DAD999                                           | None (screen error) | DAD010 lines 745-755   |
| DELACC returns DEL-FAIL-CD = '3'         | Display error; VALID-DATA-SW = 'N'; GO TO DAD999                                           | None (screen error) | DAD010 lines 757-767   |
| DELACC returns DEL-SUCCESS = 'N' other   | Display error; VALID-DATA-SW = 'N'; GO TO DAD999                                           | None (screen error) | DAD010 lines 769-778   |
| EXEC CICS SEND MAP ERASE fails           | INITIALIZE ABNDINFO-REC; populate ABND fields; LINK ABNDPROC; PERFORM ABEND-THIS-TASK       | ABEND 'HBNK'        | SM010 lines 836-893    |
| EXEC CICS SEND MAP DATAONLY fails        | INITIALIZE ABNDINFO-REC; populate ABND fields; LINK ABNDPROC; PERFORM ABEND-THIS-TASK       | ABEND 'HBNK'        | SM010 lines 916-972    |
| EXEC CICS SEND MAP DATAONLY ALARM fails  | INITIALIZE ABNDINFO-REC; populate ABND fields; LINK ABNDPROC; PERFORM ABEND-THIS-TASK       | ABEND 'HBNK'        | SM010 lines 992-1050   |
| EXEC CICS SEND TEXT (termination) fails  | INITIALIZE ABNDINFO-REC; populate ABND fields; LINK ABNDPROC; PERFORM ABEND-THIS-TASK       | ABEND 'HBNK'        | STM010 lines 1071-1128 |
| ABEND-THIS-TASK invoked                  | EXEC CICS ABEND ABCODE('HBNK') NODUMP                                                       | ABEND 'HBNK'        | ATT010 line 1136       |
| EXEC CICS ASKTIME fails (PTD010)         | No error check -- RESP/RESP2 not captured; failure is silent; ABND-TIME will be unpopulated | None                | PTD010 line 1149       |
| EXEC CICS FORMATTIME fails (PTD010)      | No error check -- RESP/RESP2 not captured; WS-ORIG-DATE and WS-TIME-NOW may be unpopulated  | None                | PTD010 line 1153       |

Notes:
- ABND-CODE is always set to 'HBNK' before linking ABNDPROC.
- ABND-FREEFORM carries a paragraph-specific diagnostic string, e.g. 'RM010 - RECEIVE MAP FAIL.' or 'GAD010  - LINK INQACC FAIL.' concatenated with EIBRESP/RESP2 values.
- The ABEND-THIS-TASK paragraph at DAD010 lines 720-727 is the only path that skips the ABNDPROC LINK; WS-FAIL-INFO is populated but ABNDINFO-REC is not -- abend details will NOT be recorded by the abend handler for this failure case.
- All abend time-string construction has a defect: WS-TIME-NOW-GRP-MM is concatenated twice in position HH:MM:MM instead of HH:MM:SS. This affects ABND-TIME in ABNDINFO-REC across all error paths (source lines 325-330, 456-461, 583-588, 858-863, 938-943, 1014-1019, 1093-1098).
- EXEC CICS RETURN TRANSID('OMEN') at lines 213-218 captures RESP/RESP2 but has NO subsequent error check -- unlike all other EXEC CICS statements in this program.
- Data structure defect: DFHCOMMAREA (Linkage Section, line 174) defines COMM-INT-RATE as PIC 9(6), but WS-COMM-AREA (line 114) defines WS-COMM-INT-RATE as PIC 9(4)V99. These are structurally incompatible; the RETURN commarea for subsequent invocations uses the WS-COMM-AREA layout (with implied decimal), but the inbound DFHCOMMAREA layout has no implied decimal. Interest rate data is misinterpreted on re-entry if non-zero.
- POPULATE-TIME-DATE (PTD010) issues EXEC CICS ASKTIME and EXEC CICS FORMATTIME with no RESP/RESP2 capture and no error check. If either call fails, ABND-DATE and ABND-TIME in ABNDINFO-REC will carry uninitialised or stale values when the abend record is written.

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. **A010 (PREMIERE SECTION)** -- Entry point; EVALUATE TRUE dispatches on EIBCALEN/EIBAID.
2. **SEND-MAP (SM010)** -- Called immediately on first entry (EIBCALEN = ZERO); sends blank map with ERASE.
3. **PROCESS-MAP (PM010)** -- Called when ENTER or PF5 is pressed.
   - 3a. **RECEIVE-MAP (RM010)** -- Reads BMS map BNK1DA (mapset BNK1DAM) from terminal into BNK1DAI.
   - 3b. If ENTER: **EDIT-DATA (ED010)** -- Validates ACCNOI (mandatory, numeric after BIF DEEDIT).
     - 3b-i. If VALID-DATA = 'Y': **GET-ACC-DATA (GAD010)** -- LINKs to INQACC; populates display fields.
     - 3b-ii. If VALID-DATA = 'N': INITIALIZE PARMS-SUBPGM (clear stale delete parms).
   - 3c. If PF5: **VALIDATE-DATA (VD010)** -- Checks COMM-SCODE and COMM-ACCNO in DFHCOMMAREA.
     - 3c-i. If VALID-DATA = 'Y': **DEL-ACC-DATA (DAD010)** -- LINKs to DELACC; displays result.
   - 3d. SET SEND-DATAONLY-ALARM; **SEND-MAP (SM010)** -- Sends updated map back to terminal.
4. **SEND-TERMINATION-MSG (STM010)** -- Called on PF12; sends 'Session Ended' text; EXEC CICS RETURN follows unconditionally.
5. **ABEND-THIS-TASK (ATT010)** -- Called after any CICS failure; issues EXEC CICS ABEND ABCODE('HBNK') NODUMP.
6. **POPULATE-TIME-DATE (PTD010)** -- Called within abend setup blocks; EXEC CICS ASKTIME (ABSTIME) then EXEC CICS FORMATTIME (DDMMYYYY with DATESEP) to populate WS-ORIG-DATE and WS-TIME-NOW. No error checking on either CICS call.
7. **EXEC CICS RETURN TRANSID('ODAC') COMMAREA(WS-COMM-AREA) LENGTH(102)** -- Always executed at end of A010 to re-queue the transaction (pseudo-conversational pattern). WS-COMM-AREA is populated from INQACC fields if INQACC-EYE = 'ACCT', otherwise INITIALIZED.
