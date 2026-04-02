---
type: business-rules
program: BNK1DCS
program_type: online
status: draft
confidence: high
last_pass: 4
calls: []
called_by: []
uses_copybooks:
- ABNDINFO
- BNK1DCM
- DELCUS
- INQCUST
- UPDCUST
reads: []
writes: []
db_tables: []
transactions:
- ODCS
mq_queues: []
---

# BNK1DCS -- Business Rules

## Program Purpose

BNK1DCS is the Display Customer screen program in the CBSA CICS Banking application. It handles online customer record display, validation, update, and deletion via a BMS map interface. The program responds to ENTER (inquiry and update submission), PF5 (delete customer), and PF10 (unlock fields for update). It is invoked under transaction ID ODCS and delegates data operations to the INQCUST, DELCUS, and UPDCUST programs via EXEC CICS LINK (with SYNCONRETURN). On the first invocation (EIBCALEN = ZERO) it stores the terminal uppercase-translation setting and disables it so that mixed-case customer names are accepted; the setting is restored on exit. All unrecoverable CICS errors are forwarded to the abend handler ABNDPROC via EXEC CICS LINK and then force-abended with abend code HBNK.

## Input / Output

| Direction | Resource    | Type | Description                                                      |
| --------- | ----------- | ---- | ---------------------------------------------------------------- |
| IN        | BNK1DCM     | CICS | BMS map input -- customer number, name, address fields           |
| OUT       | BNK1DCM     | CICS | BMS map output -- customer data, messages, attributes            |
| IN/OUT    | DFHCOMMAREA | CICS | Communication area (266 bytes) carrying customer and update state |
| LINK      | INQCUST     | CICS | Customer inquiry -- called with SYNCONRETURN                     |
| LINK      | DELCUS      | CICS | Customer deletion -- called with SYNCONRETURN                    |
| LINK      | UPDCUST     | CICS | Customer update -- called with SYNCONRETURN                      |
| LINK      | ABNDPROC    | CICS | Abend handler -- called on any unrecoverable CICS error          |

## Business Rules

### Entry Dispatch -- First Invocation (A010)

| #  | Rule                                          | Condition                        | Action                                                                                                     | Source Location |
| -- | --------------------------------------------- | -------------------------------- | ---------------------------------------------------------------------------------------------------------- | --------------- |
| 1  | First invocation -- send empty map            | EIBCALEN = ZERO                  | MOVE LOW-VALUE TO BNK1DCO; MOVE -1 TO CUSTNOL; SET SEND-ERASE; INITIALIZE WS-COMM-AREA; PERFORM STORE-TERM-DEF; save STORED-UCTRANS to WS-COMM-TERM; PERFORM SEND-MAP | A010 |
| 2  | PA key pressed -- no-op                       | EIBAID = DFHPA1 OR DFHPA2 OR DFHPA3 | CONTINUE (no action taken)                                                                              | A010            |
| 3  | PF3 pressed -- return to main menu            | EIBAID = DFHPF3                  | PERFORM RESTORE-TERM-DEF; EXEC CICS RETURN TRANSID('OMEN') IMMEDIATE                                      | A010            |
| 4  | PF5 pressed -- delete customer                | EIBAID = DFHPF5                  | PERFORM PROCESS-MAP                                                                                        | A010            |
| 5  | PF10 pressed -- update customer               | EIBAID = DFHPF10                 | PERFORM PROCESS-MAP                                                                                        | A010            |
| 6  | AID or PF12 pressed -- end session            | EIBAID = DFHAID OR DFHPF12      | PERFORM RESTORE-TERM-DEF; PERFORM SEND-TERMINATION-MSG; EXEC CICS RETURN                                  | A010            |
| 7  | CLEAR pressed -- erase screen and return      | EIBAID = DFHCLEAR                | PERFORM RESTORE-TERM-DEF; EXEC CICS SEND CONTROL ERASE FREEKB; EXEC CICS RETURN                          | A010            |
| 8  | ENTER pressed -- process input                | EIBAID = DFHENTER                | PERFORM PROCESS-MAP                                                                                        | A010            |
| 9  | Unrecognised key -- invalid key message       | WHEN OTHER                       | MOVE 'Invalid key pressed.' TO MESSAGEO; MOVE -1 TO CUSTNOL; SET SEND-DATAONLY-ALARM; PERFORM SEND-MAP   | A010            |
| 10 | COMMAREA propagation on subsequent invocations | EIBCALEN NOT = ZERO             | Copy all DFHCOMMAREA fields (COMM-TERM, COMM-EYE, COMM-SCODE, COMM-CUSTNO, COMM-NAME, COMM-ADDR, COMM-DOB, COMM-CREDIT-SCORE, COMM-CS-REVIEW-DATE, COMM-UPD) to WS-COMM-AREA | A010 |
| 11 | Pseudo-conversational RETURN                  | Always (after EVALUATE)          | EXEC CICS RETURN TRANSID('ODCS') COMMAREA(WS-COMM-AREA) LENGTH(266)                                      | A010            |

### Action Key Routing (PM010)

| #  | Rule                                    | Condition                                         | Action                                                          | Source Location |
| -- | --------------------------------------- | ------------------------------------------------- | --------------------------------------------------------------- | --------------- |
| 12 | ENTER without update flag -- inquiry    | EIBAID = DFHENTER AND COMM-UPD NOT = 'Y'          | Perform EDIT-DATA, then if VALID-DATA perform GET-CUST-DATA; else initialize INQCUST-COMMAREA and set PCB pointer to NULL | PM010           |
| 13 | ENTER with update flag -- submit update | EIBAID = DFHENTER AND COMM-UPD = 'Y'              | Perform EDIT-DATA2; if VALID-DATA perform UPDATE-CUST-DATA      | PM010           |
| 14 | PF5 -- delete customer                  | EIBAID = DFHPF5                                   | Perform EDIT-DATA, then VALIDATE-DATA; if VALID-DATA perform DEL-CUST-DATA; set cursor to CUSTNOL = -1 | PM010           |
| 15 | PF10 -- unlock for update               | EIBAID = DFHPF10                                  | Perform EDIT-DATA, then VALIDATE-DATA; if VALID-DATA perform UNPROT-CUST-DATA and display message 'Amend data then press <ENTER>.' | PM010           |
| 16 | Send map after all key processing       | Always (unconditional)                            | SET SEND-DATAONLY-ALARM TO TRUE; PERFORM SEND-MAP               | PM010           |

### Validation -- Customer Number (ED010 / EDIT-DATA)

| #  | Rule                                    | Condition                                         | Action                                                          | Source Location |
| -- | --------------------------------------- | ------------------------------------------------- | --------------------------------------------------------------- | --------------- |
| 17 | Customer number must be entered         | CUSTNOL = ZERO OR CUSTNOI = LOW-VALUES            | Set MESSAGEO = 'Please enter a customer number.'; VALID-DATA-SW = 'N'; cursor to CUSTNOL = -1; GO TO ED999 | ED010           |
| 18 | Customer number must be numeric         | CUSTNOI NOT NUMERIC (checked after CICS BIF DEEDIT) | Set MESSAGEO = 'Please enter a customer number.'; VALID-DATA-SW = 'N'; cursor to CUSTNOL = -1 | ED010           |

### Validation -- Customer Name Title (ED2010 / EDIT-DATA2)

| #  | Rule                                       | Condition                                                                                                                  | Action                                                                                                                | Source Location |
| -- | ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | --------------- |
| 19 | Customer name must start with a valid title | WS-UNSTR-TITLE (first word of CUSTNAMI) must equal one of: 'Professor', 'Mr', 'Mrs', 'Miss', 'Ms', 'Dr', 'Drs', 'Lord', 'Sir', 'Lady' | If no match: MESSAGEO = 'Valid titles are: Mr,Mrs,Miss,Ms,Dr,Professor,Drs,Lord,Sir,Lady'; VALID-DATA-SW = 'N'; cursor to CUSTNAML = -1 | ED2010          |
| 20 | Title extracted from name using UNSTRING    | First space-delimited token of CUSTNAMI moved to WS-UNSTR-TITLE (PIC X(9))                                                | Compared in EVALUATE against valid title literals                                                                     | ED2010          |

### Validation -- Customer Address (ED2010 / EDIT-DATA2)

| #  | Rule                                    | Condition                                         | Action                                                          | Source Location |
| -- | --------------------------------------- | ------------------------------------------------- | --------------------------------------------------------------- | --------------- |
| 21 | Address must not be all spaces          | CUSTAD1I = SPACES AND CUSTAD2I = SPACES AND CUSTAD3I = SPACES | MESSAGEO = 'Address must not be all spaces - please reenter'; VALID-DATA-SW = 'N'; cursor to CUSTAD1L = -1 | ED2010          |

### Validation -- Sort Code / Customer Number (VD010 / VALIDATE-DATA)

| #  | Rule                                           | Condition                           | Action                                                                                               | Source Location |
| -- | ---------------------------------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------- | --------------- |
| 22 | INQCUST sort code must not be '000000'         | INQCUST-SCODE = '000000'            | VALID-DATA-SW = 'N'; MESSAGEO = 'The Sort code / Customer number combination is not VALID.'          | VD010           |
| 23 | Customer number from map must not be zero or max | CUSTNOI = ZERO OR CUSTNOI = '9999999999' | VALID-DATA-SW = 'N'; MESSAGEO = 'The customer number is not VALID.'                             | VD010           |

### Data Validity Switch

| #  | Rule                                    | Condition               | Action                    | Source Location |
| -- | --------------------------------------- | ----------------------- | ------------------------- | --------------- |
| 24 | VALID-DATA flag controls downstream flow | 88-level VALID-DATA VALUE 'Y' on VALID-DATA-SW | All downstream PERFORM branches (GET-CUST-DATA, UPDATE-CUST-DATA, DEL-CUST-DATA, UNPROT-CUST-DATA) are conditional on VALID-DATA being true | PM010, ED010, ED2010, VD010 |

### Customer Inquiry Response (GCD010)

| #  | Rule                                              | Condition                                        | Action                                                                                                           | Source Location |
| -- | ------------------------------------------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- | --------------- |
| 25 | Customer not found after INQCUST call             | INQCUST-NAME = SPACES AND INQCUST-ADDR = SPACES  | MESSAGEO = 'Sorry, but that customer number was not found.'; clear all map output fields; VALID-DATA-SW = 'N'; GO TO GCD999 | GCD010          |
| 26 | Success message with action hints                 | CUSTNOI NOT = ZERO AND NOT = '9999999999' (after successful lookup) | MESSAGEO = 'Customer lookup successful. <PF5> to Delete. <PF10> to Update.' | GCD010          |
| 27 | Success message without action hints              | CUSTNOI = ZERO OR CUSTNOI = '9999999999'         | MESSAGEO = 'Customer lookup successful.' (no PF key hints)                                                       | GCD010          |
| 28 | Address split from single field to three lines    | After successful INQCUST                         | INQCUST-ADDR (160 chars) moved to COMM-ADDR-SPLIT; split to CUSTAD1O (60), CUSTAD2O (60), CUSTAD3O (40)         | GCD010          |
| 29 | Date of birth split from YYYYMMDD to DD/MM/YYYY   | After successful INQCUST                         | INQCUST-DOB moved via COMM-DOB-SPLIT to DOBDDO, DOBMMO, DOBYYO                                                  | GCD010          |
| 30 | Credit score formatted from numeric to display    | After successful INQCUST                         | INQCUST-CREDIT-SCORE moved to CREDIT-SCORE-9; CREDIT-SCORE-X (PIC X(3)) moved to CREDSCO                        | GCD010          |

### Customer Deletion Response (DCD010)

| #  | Rule                                          | Condition                                                             | Action                                                                                                         | Source Location |
| -- | --------------------------------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | --------------- |
| 31 | Delete fail -- customer not found             | COMM-DEL-SUCCESS = 'N' AND COMM-DEL-FAIL-CD = '1'                    | MESSAGEO = 'Sorry but that Cust no was not found. Customer NOT deleted.'; VALID-DATA-SW = 'N'; cursor to CUSTNO2L; GO TO DCD999 | DCD010          |
| 32 | Delete fail -- datastore error                | COMM-DEL-SUCCESS = 'N' AND COMM-DEL-FAIL-CD = '2'                    | MESSAGEO = 'Sorry but a datastore error occurred. Action NOT applied.'; VALID-DATA-SW = 'N'; GO TO DCD999      | DCD010          |
| 33 | Delete fail -- delete error                   | COMM-DEL-SUCCESS = 'N' AND COMM-DEL-FAIL-CD = '3'                    | MESSAGEO = 'Sorry but a delete error occurred. Customer NOT deleted.'; VALID-DATA-SW = 'N'; GO TO DCD999       | DCD010          |
| 34 | Delete fail -- unspecified error              | COMM-DEL-SUCCESS = 'N' AND COMM-DEL-FAIL-CD not in {1,2,3}           | MESSAGEO = 'Sorry but an error occurred. Customer NOT deleted.'; VALID-DATA-SW = 'N'; GO TO DCD999             | DCD010          |
| 35 | Delete success -- clear map and confirm       | COMM-DEL-SUCCESS NOT = 'N' (implied success)                         | Clear all map output fields; MESSAGEO = 'Customer [CUSTNO] and associated accounts were successfully deleted.' | DCD010          |

### Customer Update -- Data Assembly (UPDCD010)

| #  | Rule                                                   | Condition              | Action                                                                                                                               | Source Location |
| -- | ------------------------------------------------------ | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | --------------- |
| 36 | Address three lines concatenated to single field       | Before LINK to UPDCUST | STRING CUSTAD1I CUSTAD2I CUSTAD3I DELIMITED BY SIZE INTO COMM-ADDR (160 chars) -- no separator inserted between segments             | UPDCD010        |
| 37 | DOB assembled from screen fields DD/MM/YYYY            | Before LINK to UPDCUST | DOBDDI to COMM-DOBX-DD; DOBMMI to COMM-DOBX-MM; DOBYYI to COMM-DOBX-YYYY; numeric COMM-DOB-UPD-9 moved to COMM-DOB of UPDCUST-COMMAREA | UPDCD010        |
| 38 | Credit score assembled from display to numeric         | Before LINK to UPDCUST | CREDSCI moved to CREDIT-SCORE-X; CREDIT-SCORE-9 (PIC 9(3)) moved to COMM-CREDIT-SCORE of UPDCUST-COMMAREA                          | UPDCD010        |
| 39 | Credit score review date assembled from screen DD/MM/YYYY | Before LINK to UPDCUST | SCRDTDDI, SCRDTMMI, SCRDTYYI moved to COMM-CS-REVIEWX-DD/MM/YYYY; COMM-CS-REVIEW-UPD-9 moved to COMM-CS-REVIEW-DATE               | UPDCD010        |

### Customer Update Response (UPDCD010)

| #  | Rule                                          | Condition                                                               | Action                                                                                                           | Source Location |
| -- | --------------------------------------------- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | --------------- |
| 40 | Update fail -- customer not found             | COMM-UPD-SUCCESS = 'N' AND COMM-UPD-FAIL-CD = '1'                      | MESSAGEO = 'Sorry but that Cust no was not found. Customer NOT updated.'; VALID-DATA-SW = 'N'; cursor to CUSTNO2L; GO TO UPDCD999 | UPDCD010        |
| 41 | Update fail -- datastore error                | COMM-UPD-SUCCESS = 'N' AND COMM-UPD-FAIL-CD = '2'                      | MESSAGEO = 'Sorry but a datastore error occurred. Customer NOT updated.'; VALID-DATA-SW = 'N'; cursor to CUSTNO2L; GO TO UPDCD999 | UPDCD010        |
| 42 | Update fail -- update error                   | COMM-UPD-SUCCESS = 'N' AND COMM-UPD-FAIL-CD = '3'                      | MESSAGEO = 'Sorry but an update error occurred. Customer NOT updated.'; VALID-DATA-SW = 'N'; cursor to CUSTNO2L; GO TO UPDCD999 | UPDCD010        |
| 43 | Update fail -- unknown error                  | COMM-UPD-SUCCESS = 'N' AND COMM-UPD-FAIL-CD not in {1,2,3}             | MESSAGEO = 'Sorry but an unknown error occurred. Customer NOT updated.'; VALID-DATA-SW = 'N'; cursor to CUSTNO2L; GO TO UPDCD999 | UPDCD010        |
| 44 | Update success -- display refreshed data and protect fields | COMM-UPD-SUCCESS NOT = 'N'                                  | Populate all map output fields from UPDCUST-COMMAREA response; MESSAGEO = 'Customer [CUSTNO] was updated successfully'; PERFORM PROT-CUST-DATA | UPDCD010        |

### Terminal Uppercase Translation Management (STD010 / RTD010 / RM010)

| #  | Rule                                                 | Condition                                                  | Action                                                                                          | Source Location |
| -- | ---------------------------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | --------------- |
| 45 | Store terminal UCTRAN setting on first invocation    | EIBCALEN = ZERO (via STORE-TERM-DEF)                       | EXEC CICS INQUIRE TERMINAL; MOVE WS-UCTRANS TO STORED-UCTRANS; if UCTRAN or TRANIDONLY, SET NOUCTRAN to allow mixed case | STD010          |
| 46 | Disable uppercase translation before RECEIVE MAP     | WS-UCTRANS = DFHVALUE(UCTRAN) OR DFHVALUE(TRANIDONLY)     | EXEC CICS SET TERMINAL UCTRANST(NOUCTRAN) -- allows mixed-case name input                       | RM010           |
| 47 | Restore terminal UCTRAN on exit                      | Always on PF3, PF12, CLEAR, or abend recovery             | MOVE WS-COMM-TERM TO WS-UCTRANS; EXEC CICS SET TERMINAL UCTRANST(WS-UCTRANS) -- restores original setting | RTD010          |

### BMS Map Send Variants (SM010)

| #  | Rule                                   | Condition          | Action                                                                                   | Source Location |
| -- | -------------------------------------- | ------------------ | ---------------------------------------------------------------------------------------- | --------------- |
| 48 | Send map with full erase               | SEND-ERASE = '1'   | EXEC CICS SEND MAP('BNK1DC') MAPSET('BNK1DCM') FROM(BNK1DCO) ERASE CURSOR FREEKB        | SM010           |
| 49 | Send map data only (no erase)          | SEND-DATAONLY = '2'| EXEC CICS SEND MAP('BNK1DC') MAPSET('BNK1DCM') FROM(BNK1DCO) DATAONLY CURSOR FREEKB    | SM010           |
| 50 | Send map data only with audible alarm  | SEND-DATAONLY-ALARM = '3' | EXEC CICS SEND MAP('BNK1DC') MAPSET('BNK1DCM') FROM(BNK1DCO) DATAONLY CURSOR ALARM FREEKB | SM010      |

### Session Termination (STM010)

| #  | Rule                                   | Condition          | Action                                                                    | Source Location |
| -- | -------------------------------------- | ------------------ | ------------------------------------------------------------------------- | --------------- |
| 51 | Session end message sent to terminal   | PF12 or AID key    | EXEC CICS SEND TEXT FROM(END-OF-SESSION-MESSAGE='Session Ended') ERASE FREEKB | STM010      |

### Abend Handling (ATT010 / AH010)

| #  | Rule                                       | Condition                        | Action                                                                                       | Source Location |
| -- | ------------------------------------------ | -------------------------------- | -------------------------------------------------------------------------------------------- | --------------- |
| 52 | Force task abend with code HBNK            | After ABNDPROC LINK fails        | DISPLAY WS-FAIL-INFO; EXEC CICS ABEND ABCODE('HBNK') NODUMP CANCEL                          | ATT010          |
| 53 | HANDLE ABEND label set at entry            | Unconditional at program start   | EXEC CICS HANDLE ABEND LABEL(ABEND-HANDLING); on abend: PERFORM RESTORE-TERM-DEF then ABEND-THIS-TASK | A010, AH010     |

### Screen Field Protection -- Unlock for Update (UCD010 / UNPROT-CUST-DATA)

| #  | Rule                                                         | Condition                              | Action                                                                                                                              | Source Location |
| -- | ------------------------------------------------------------ | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 54 | Preserve current screen data in COMMAREA before unprotecting | PF10 path; always in UCD010            | All visible output fields (SORTCO, CUSTNO2O, CUSTNAMO, CUSTAD1-3O, DOBDDO/MMO/YYO, CREDSCO, SCRDTDDO/MMO/YYO) copied to DFHCOMMAREA | UCD010          |
| 55 | Set COMM-UPD flag to 'Y' to track update mode               | Always in UCD010                       | MOVE 'Y' TO COMM-UPD OF DFHCOMMAREA -- subsequent ENTER press routes to UPDATE-CUST-DATA instead of GET-CUST-DATA                  | UCD010          |
| 56 | Customer name field made editable (green, unprotected)       | Always in UCD010                       | MOVE DFHGREEN TO CUSTNAMC; MOVE 'A' TO CUSTNAMA; MOVE DFHUNDLN TO CUSTNAMH; MOVE -1 TO CUSTNAML (cursor here)                     | UCD010          |
| 57 | Customer address lines 1-3 made editable (green, unprotected) | Always in UCD010                      | MOVE DFHGREEN/DFHUNDLN/'A' to CUSTAD1C/H/A, CUSTAD2C/H/A, CUSTAD3C/H/A                                                            | UCD010          |
| 58 | Customer number dynamically protected during update mode     | Always in UCD010                       | MOVE DFHBMASK TO CUSTNOA (MDT-skip attribute) -- prevents user editing the customer number while name/address are editable          | UCD010          |
| 59 | Customer number display changed to neutral/no-underline      | Always in UCD010                       | MOVE DFHNEUTR TO CUSTNOC; MOVE HIGH-VALUES TO CUSTNOH -- visually distinguishes protected field from editable fields                | UCD010          |

### Screen Field Protection -- Re-protect After Update (PCD010 / PROT-CUST-DATA)

| #  | Rule                                                         | Condition                              | Action                                                                                                                              | Source Location |
| -- | ------------------------------------------------------------ | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 60 | Reload all display fields from UPDCUST-COMMAREA response     | After successful update (PCD010)       | COMM-SCODE, COMM-CUSTNO, COMM-NAME from UPDCUST-COMMAREA moved to map output; COMM-ADDR split to 3 lines; DOB split to DD/MM/YYYY; credit score and CS review date moved to output fields | PCD010          |
| 61 | Refresh DFHCOMMAREA with confirmed post-update values        | Always in PCD010                       | COMM-EYE='CUST', COMM-SCODE, COMM-CUSTNO, COMM-NAME, COMM-ADDR (re-concatenated), COMM-DOB (reassembled), COMM-CREDIT-SCORE, COMM-CS-REVIEW-DATE written back to DFHCOMMAREA | PCD010          |
| 62 | Set COMM-UPD flag to 'N' to exit update mode                 | Always in PCD010                       | MOVE 'N' TO COMM-UPD -- subsequent ENTER press routes to GET-CUST-DATA (inquiry) not UPDATE-CUST-DATA                              | PCD010          |
| 63 | Customer number (CUSTNO2) re-protected after update          | Always in PCD010                       | MOVE DFHNEUTR TO CUSTNO2C; MOVE DFHBMPRF TO CUSTNO2A (protected, fset) -- field is read-only after update completes                | PCD010          |
| 64 | Customer name field re-protected after update                | Always in PCD010                       | MOVE DFHNEUTR TO CUSTNAMC; MOVE DFHBMPRF TO CUSTNAMA; MOVE HIGH-VALUES TO CUSTNAMH -- returns to protected display-only state      | PCD010          |
| 65 | Customer address lines 1-3 re-protected after update         | Always in PCD010                       | MOVE DFHNEUTR/DFHBMPRF/HIGH-VALUES to CUSTAD1-3C/A/H -- all address lines returned to display-only state                           | PCD010          |
| 66 | Customer number (CUSTNO) field made editable again           | Always in PCD010                       | MOVE DFHBMFSE TO CUSTNOA (unprotected, fset); MOVE DFHGREEN TO CUSTNOC; MOVE DFHUNDLN TO CUSTNOH -- customer number re-enabled for next inquiry | PCD010          |
| 67 | Cursor positioned at customer number field after re-protect  | Always in PCD010                       | MOVE -1 TO CUSTNOL -- ready for user to enter a new customer number for the next transaction                                        | PCD010          |

## Calculations

| Calculation | Formula / Logic                                                 | Input Fields                     | Output Field       | Source Location |
| ----------- | --------------------------------------------------------------- | -------------------------------- | ------------------ | --------------- |
| Title extraction | UNSTRING WS-VALIDATE-NAME DELIMITED BY SPACE INTO WS-UNSTR-TITLE | CUSTNAMI (via WS-VALIDATE-NAME) | WS-UNSTR-TITLE (PIC X(9)) | ED2010     |
| Message composition (update prompt) | STRING 'Amend data then press <ENTER>.' DELIMITED BY SIZE, ' ' DELIMITED BY SIZE INTO MESSAGEO | Literal strings | MESSAGEO | PM010   |
| Message composition (invalid title) | STRING 'Valid titles are: Mr,Mrs,Miss,Ms,Dr,Professor,' DELIMITED BY SIZE, 'Drs,Lord,Sir,Lady' DELIMITED BY SIZE INTO MESSAGEO | Literal strings | MESSAGEO | ED2010  |
| Message composition (invalid address) | STRING 'Address must not be all spaces' DELIMITED BY SIZE, ' - please reenter' DELIMITED BY SIZE INTO MESSAGEO | Literal strings | MESSAGEO | ED2010  |
| Address pack (update) | STRING CUSTAD1I(60) DELIMITED BY SIZE, CUSTAD2I(60) DELIMITED BY SIZE, CUSTAD3I(40) DELIMITED BY SIZE INTO COMM-ADDR(160) | CUSTAD1I, CUSTAD2I, CUSTAD3I | COMM-ADDR of UPDCUST-COMMAREA | UPDCD010 |
| DOB assembly (update) | DOBDDI to COMM-DOBX-DD; DOBMMI to COMM-DOBX-MM; DOBYYI to COMM-DOBX-YYYY; redefined as PIC 9(8) COMM-DOB-UPD-9 | DOBDDI, DOBMMI, DOBYYI | COMM-DOB of UPDCUST-COMMAREA | UPDCD010 |
| Credit score reformat | CREDSCI to CREDIT-SCORE-X (PIC X(3)); CREDIT-SCORE-9 (PIC 9(3)) via REDEFINES | CREDSCI | COMM-CREDIT-SCORE of UPDCUST-COMMAREA | UPDCD010 |
| CS review date assembly | SCRDTDDI, SCRDTMMI, SCRDTYYI to COMM-CS-REVIEWX fields; COMM-CS-REVIEW-UPD-9 (REDEFINES numeric) | SCRDTDDI, SCRDTMMI, SCRDTYYI | COMM-CS-REVIEW-DATE of UPDCUST-COMMAREA | UPDCD010 |
| Current date/time retrieval | EXEC CICS ASKTIME ABSTIME; EXEC CICS FORMATTIME DDMMYYYY DATESEP | EIB clock | WS-ORIG-DATE (DD/MM/YYYY), WS-TIME-NOW (HHMMSS) | PTD10 |
| Abend time string | STRING HH ':' MM ':' MM INTO ABND-TIME (note: MM used twice -- apparent bug, SS not used) | WS-TIME-NOW-GRP-HH, WS-TIME-NOW-GRP-MM | ABND-TIME | A010, RM010, GCD010, DCD010, UPDCD010, SM010, STD010, RTD010, STM010 |
| Address split (display) | COMM-ADDR (160) moved to COMM-ADDR-SPLIT; COMM-ADDR-SPLIT1(60) to CUSTAD1O; COMM-ADDR-SPLIT2(60) to CUSTAD2O; COMM-ADDR-SPLIT3(40) to CUSTAD3O | COMM-ADDR of UPDCUST-COMMAREA | CUSTAD1O, CUSTAD2O, CUSTAD3O | PCD010 |
| DOB split (re-display) | COMM-DOB of UPDCUST-COMMAREA moved to COMM-DOB-SPLIT; COMM-DOB-SPLIT-DD to DOBDDO; COMM-DOB-SPLIT-MM to DOBMMO; COMM-DOB-SPLIT-YYYY to DOBYYO | COMM-DOB of UPDCUST-COMMAREA | DOBDDO, DOBMMO, DOBYYO | PCD010 |

## Error Handling

| Condition                             | Action                                              | Return Code              | Source Location |
| ------------------------------------- | --------------------------------------------------- | ------------------------ | --------------- |
| Customer number empty or LOW-VALUES   | Set VALID-DATA-SW = 'N'; display message; GO TO ED999 | VALID-DATA-SW = 'N'    | ED010           |
| Customer number not numeric           | Set VALID-DATA-SW = 'N'; display message             | VALID-DATA-SW = 'N'     | ED010           |
| Customer name has invalid title       | Set VALID-DATA-SW = 'N'; display valid titles list   | VALID-DATA-SW = 'N'     | ED2010          |
| All address lines are spaces          | Set VALID-DATA-SW = 'N'; display address message     | VALID-DATA-SW = 'N'     | ED2010          |
| INQCUST sort code = '000000'          | Set VALID-DATA-SW = 'N'; display sort code message   | VALID-DATA-SW = 'N'     | VD010           |
| Customer number = ZERO or '9999999999' | Set VALID-DATA-SW = 'N'; display customer number message | VALID-DATA-SW = 'N' | VD010           |
| INQCUST returns empty NAME and ADDR   | VALID-DATA-SW = 'N'; display 'Sorry, but that customer number was not found.'; clear map fields | VALID-DATA-SW = 'N' | GCD010 |
| DELCUS FAIL-CD = '1'                  | VALID-DATA-SW = 'N'; 'Sorry but that Cust no was not found. Customer NOT deleted.' | VALID-DATA-SW = 'N' | DCD010 |
| DELCUS FAIL-CD = '2'                  | VALID-DATA-SW = 'N'; 'Sorry but a datastore error occurred. Action NOT applied.' | VALID-DATA-SW = 'N' | DCD010 |
| DELCUS FAIL-CD = '3'                  | VALID-DATA-SW = 'N'; 'Sorry but a delete error occurred. Customer NOT deleted.' | VALID-DATA-SW = 'N' | DCD010 |
| DELCUS FAIL-CD other                  | VALID-DATA-SW = 'N'; 'Sorry but an error occurred. Customer NOT deleted.' | VALID-DATA-SW = 'N' | DCD010 |
| UPDCUST FAIL-CD = '1'                 | VALID-DATA-SW = 'N'; 'Sorry but that Cust no was not found. Customer NOT updated.' | VALID-DATA-SW = 'N' | UPDCD010 |
| UPDCUST FAIL-CD = '2'                 | VALID-DATA-SW = 'N'; 'Sorry but a datastore error occurred. Customer NOT updated.' | VALID-DATA-SW = 'N' | UPDCD010 |
| UPDCUST FAIL-CD = '3'                 | VALID-DATA-SW = 'N'; 'Sorry but an update error occurred. Customer NOT updated.' | VALID-DATA-SW = 'N' | UPDCD010 |
| UPDCUST FAIL-CD other                 | VALID-DATA-SW = 'N'; 'Sorry but an unknown error occurred. Customer NOT updated.' | VALID-DATA-SW = 'N' | UPDCD010 |
| EXEC CICS RETURN TRANSID('ODCS') fails | LINK ABNDPROC with ABNDINFO-REC; PERFORM ABEND-THIS-TASK; ABEND ABCODE('HBNK') | WS-CICS-RESP != DFHRESP(NORMAL) | A010 |
| EXEC CICS SET TERMINAL UC fails (RM010) | LINK ABNDPROC; PERFORM ABEND-THIS-TASK              | WS-CICS-RESP != DFHRESP(NORMAL) | RM010          |
| EXEC CICS RECEIVE MAP fails           | LINK ABNDPROC; PERFORM ABEND-THIS-TASK              | WS-CICS-RESP != DFHRESP(NORMAL) | RM010          |
| EXEC CICS LINK INQCUST fails          | LINK ABNDPROC; PERFORM ABEND-THIS-TASK              | WS-CICS-RESP != DFHRESP(NORMAL) | GCD010         |
| EXEC CICS LINK DELCUS fails           | LINK ABNDPROC; PERFORM ABEND-THIS-TASK              | WS-CICS-RESP != DFHRESP(NORMAL) | DCD010         |
| EXEC CICS LINK UPDCUST fails          | LINK ABNDPROC; PERFORM ABEND-THIS-TASK              | WS-CICS-RESP != DFHRESP(NORMAL) | UPDCD010       |
| EXEC CICS SEND MAP (ERASE) fails      | LINK ABNDPROC; PERFORM ABEND-THIS-TASK              | WS-CICS-RESP != DFHRESP(NORMAL) | SM010          |
| EXEC CICS SEND MAP (DATAONLY) fails   | LINK ABNDPROC; PERFORM ABEND-THIS-TASK              | WS-CICS-RESP != DFHRESP(NORMAL) | SM010          |
| EXEC CICS SEND MAP (ALARM) fails      | LINK ABNDPROC; PERFORM ABEND-THIS-TASK              | WS-CICS-RESP != DFHRESP(NORMAL) | SM010          |
| EXEC CICS SET TERMINAL (STD010) fails | LINK ABNDPROC; PERFORM ABEND-THIS-TASK              | WS-CICS-RESP != DFHRESP(NORMAL) | STD010         |
| EXEC CICS SET TERMINAL (RTD010) fails | LINK ABNDPROC; PERFORM ABEND-THIS-TASK (no RESTORE-TERM-DEF -- prevents AICA loop) | WS-CICS-RESP != DFHRESP(NORMAL) | RTD010 |
| EXEC CICS SEND TEXT (STM010) fails    | LINK ABNDPROC; PERFORM ABEND-THIS-TASK              | WS-CICS-RESP != DFHRESP(NORMAL) | STM010         |
| HANDLE ABEND fires                    | AH010: PERFORM RESTORE-TERM-DEF; PERFORM ABEND-THIS-TASK | Async abend condition       | AH010          |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. A010 -- Entry point; sets HANDLE ABEND label; EVALUATE TRUE on EIBCALEN/EIBAID to dispatch
2. STORE-TERM-DEF (STD010) -- Called on first invocation to save and disable terminal uppercase translation
3. SEND-MAP (SM010) -- Sends BMS map (ERASE variant on first invocation)
4. PROCESS-MAP (PM010) -- Main action dispatcher; called for PF5, PF10, ENTER
5. RECEIVE-MAP (RM010) -- Disables UCTRAN, performs EXEC CICS RECEIVE MAP ASIS, re-enables; moves CUSTNOI/SORTCI to INQCUST fields
6. EDIT-DATA (ED010) -- Validates customer number (empty and numeric checks); uses BIF DEEDIT
7. EDIT-DATA2 (ED2010) -- Validates customer name title (UNSTRING + EVALUATE) and address (not all spaces)
8. VALIDATE-DATA (VD010) -- Validates sort code not '000000' and customer number not ZERO or '9999999999'
9. GET-CUST-DATA (GCD010) -- EXEC CICS LINK PROGRAM('INQCUST') SYNCONRETURN; maps response fields to BMS output
10. DEL-CUST-DATA (DCD010) -- EXEC CICS LINK PROGRAM('DELCUS') SYNCONRETURN; interprets COMM-DEL-FAIL-CD
11. UPDATE-CUST-DATA (UPDCD010) -- Packs input fields; EXEC CICS LINK PROGRAM('UPDCUST') SYNCONRETURN; interprets COMM-UPD-FAIL-CD; calls PROT-CUST-DATA on success
12. UNPROT-CUST-DATA (UCD010) -- Unprotects CUSTNAM and CUSTAD1-3 map fields for editing (PF10 path); dynamically protects CUSTNO; sets COMM-UPD = 'Y'; preserves screen data in DFHCOMMAREA
13. PROT-CUST-DATA (PCD010) -- Re-protects all editable fields after successful update; reloads display data from UPDCUST-COMMAREA; sets COMM-UPD = 'N'; repositions cursor to CUSTNO for next inquiry
14. SEND-MAP (SM010) -- Always called at end of PM010 with SEND-DATAONLY-ALARM flag
15. RESTORE-TERM-DEF (RTD010) -- Restores terminal UCTRAN from WS-COMM-TERM on exit / before abend
16. SEND-TERMINATION-MSG (STM010) -- Sends 'Session Ended' text on PF12/AID
17. POPULATE-TIME-DATE (PTD10) -- ASKTIME + FORMATTIME; used to populate ABNDINFO-REC timestamps
18. ABEND-THIS-TASK (ATT010) -- DISPLAY WS-FAIL-INFO; EXEC CICS ABEND ABCODE('HBNK') NODUMP CANCEL
19. LINK ABNDPROC -- Called before ATT010 on every CICS error path to record diagnostics in ABNDINFO-REC
20. AH010 (ABEND-HANDLING label) -- Catches async abends; RESTORE-TERM-DEF then force abend
