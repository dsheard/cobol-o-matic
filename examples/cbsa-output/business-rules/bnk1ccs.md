---
type: business-rules
program: BNK1CCS
program_type: online
status: draft
confidence: high
last_pass: 5
calls:
- CRECUST
- ABNDPROC
called_by: []
uses_copybooks:
- ABNDINFO
- BNK1CCM
- DFHAID
reads: []
writes: []
db_tables: []
transactions:
- OCCS
mq_queues: []
---

# BNK1CCS -- Business Rules

## Program Purpose

BNK1CCS is the Create Customer Screen program in the CBSA CICS Banking application. It presents the BNK1CCM BMS map to a terminal user, collects new customer data (title, first name, initials, surname, address lines 1-3, and date of birth), validates every input field, and then delegates actual customer record creation to the back-end program CRECUST via EXEC CICS LINK. The program operates under transaction OCCS and communicates its terminal upper-case translation state across pseudo-conversational returns so that mixed-case data entry is preserved correctly.

## Input / Output

| Direction | Resource    | Type | Description                                                     |
| --------- | ----------- | ---- | --------------------------------------------------------------- |
| IN        | BNK1CC      | CICS | BMS map receive (map BNK1CC within mapset BNK1CCM) -- customer data keyed by the terminal operator |
| OUT       | BNK1CC      | CICS | BMS map send (map BNK1CC within mapset BNK1CCM) -- confirmation or error messages to terminal |
| OUT       | CRECUST     | CICS | EXEC CICS LINK -- customer creation request with SUBPGM-PARMS  |
| OUT       | ABNDPROC    | CICS | EXEC CICS LINK -- abend handler invoked on any CICS failure     |
| IN/OUT    | DFHCOMMAREA | CICS | Pseudo-conversational commarea (PIC X(5)) carrying UCTRANS saved state |

## Business Rules

### Screen Entry and Navigation

| #  | Rule                          | Condition                                        | Action                                                                                                                              | Source Location |
| -- | ----------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 1  | First-time entry               | EIBCALEN = ZERO (no commarea on first invocation) | Clear all map fields to spaces/LOW-VALUE, set cursor on CUSTTIT, set SEND-ERASE flag, store terminal UCTRANS setting, send map     | A010 line 170   |
| 2  | PA key pressed                 | EIBAID = DFHPA1, DFHPA2, or DFHPA3               | CONTINUE -- no action taken, return to OCCS                                                                                         | A010 line 194   |
| 3  | PF3 pressed -- return to menu  | EIBAID = DFHPF3                                  | Restore terminal UCTRANS setting, EXEC CICS RETURN TRANSID('OMEN') IMMEDIATE -- routes back to main menu                           | A010 line 200   |
| 4  | PF12 pressed -- end session    | EIBAID = DFHPF12                                 | Send termination message 'Session Ended', restore terminal UCTRANS, EXEC CICS RETURN (no TRANSID -- ends conversation)              | A010 line 219   |
| 5  | CLEAR key pressed              | EIBAID = DFHCLEAR                                | EXEC CICS SEND MAP('BNK1CCM') MAPONLY ERASE FREEKB (inline, not via SEND-MAP paragraph -- no RESP check), restore UCTRANS, EXEC CICS RETURN TRANSID('OCCS') COMMAREA(WS-COMM-AREA) -- no LENGTH clause (contrast with main RETURN at line 279 which specifies LENGTH(248)). Note: the inline SEND passes the mapset name 'BNK1CCM' as the MAP parameter with no MAPSET clause; SM010 correctly uses MAP('BNK1CC') MAPSET('BNK1CCM') -- this inconsistency is a latent defect. | A010 lines 235-251 |
| 6  | ENTER key pressed              | EIBAID = DFHENTER                                | Perform PROCESS-MAP (receive map, validate, create customer if valid, send map with result)                                          | A010 line 256   |
| 7  | Any other key                  | WHEN OTHER (all unrecognised AID values)         | Display message 'Invalid key pressed.' with alarm, redisplay data-only                                                              | A010 line 262   |

### Upper-Case Translation Management

| #  | Rule                               | Condition                                                      | Action                                                                                                           | Source Location            |
| -- | ---------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | -------------------------- |
| 8  | Disable UCTRANS on first entry      | EIBCALEN = ZERO -- STORE-TERM-DEF                              | EXEC CICS INQUIRE TERMINAL to read current UCTRANST; save to STORED-UCTRANS and WS-COMM-TERM; if UCTRAN or TRANIDONLY, set NOUCTRAN(451) for the session | STD010 lines 1100-1196     |
| 9  | Disable UCTRANS before map receive  | Always -- RECEIVE-MAP                                          | EXEC CICS INQUIRE TERMINAL; if UCTRAN or TRANIDONLY, set NOUCTRAN so mixed-case names are preserved; UCTRANS is NOT re-enabled after the receive -- it stays disabled until RTD010 restores it on session exit | RM010 lines 392-476        |
| 10 | RECEIVE MAP with ASIS option        | Always on ENTER path                                           | EXEC CICS RECEIVE MAP BNK1CC MAPSET BNK1CCM INTO(BNK1CCI) TERMINAL ASIS -- ASIS preserves the exact case of input data as typed, bypassing any 3270 translation; this works in concert with NOUCTRAN set by rule 9 | RM010 lines 500-508        |
| 11 | Restore UCTRANS on exit/abend       | PF3, PF12, CLEAR, or any CICS error path                       | Read saved UCTRANS from WS-COMM-TERM (via DFHCOMMAREA) and EXEC CICS SET TERMINAL UCTRANST back to original value   | RTD010 lines 1202-1277     |
| 12 | Map input fields pre-initialised before receive | Always before RECEIVE MAP in RM010          | All BNK1CCI input fields set to LOW-VALUES/SPACES/0 (CUSTTITI, CHRISTNI, CUSTINSI, CUSTSNI, CUSTAD1I-3I, DOBDDI, DOBMMI, DOBYYI, SORTCI, CUSTNO2I, CREDSCI, SCRDTDDI, SCRDTMMI, SCRDTYYI, MESSAGEI) before RECEIVE MAP -- defensive pattern to prevent stale data from prior invocations | RM010 lines 481-498 |

### Input Validation (ED010 -- EDIT-DATA SECTION)

| #  | Rule                              | Condition                                                                                        | Action                                                                                                                                                    | Source Location      |
| -- | --------------------------------- | ------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- |
| 13 | Customer number must be blank      | CUSTNO2L > 0 (customer number field has length, i.e. a value is present)                         | Message: 'Please clear screen before creating new user'; set cursor on CUSTTIT; set VALID-DATA-SW = 'N'; GO TO ED999                                       | ED010 lines 581-587  |
| 14 | Title is mandatory                 | CUSTTITL < 1 OR CUSTTITI = SPACES OR CUSTTITI = LOW-VALUES                                       | Message: 'Valid titles are: Mr,Mrs,Miss,Ms,Dr,Professor,Drs,Lord,Sir,Lady'; set cursor on CUSTTIT; set VALID-DATA-SW = 'N'; GO TO ED999                    | ED010 lines 589-600  |
| 15 | Title must be a recognised value   | CUSTTITL > 0 and CUSTTITI does not match any accepted value in EVALUATE                          | Message: 'Valid titles are: Mr,Mrs,Miss,Ms,Dr,Drs,Professor,Lord,Sir,Lady'; set cursor on CUSTTIT; set VALID-DATA-SW = 'N'; GO TO ED999                    | ED010 lines 604-780  |
| 16 | Title normalisation -- Mr          | CUSTTITI = 'MR________', 'Mr________', 'MR        ', 'mr________'; 'Mr         ' (Mr + 9 spaces) passes without normalisation (CONTINUE only) | MOVE 'Mr' TO CUSTTITI (canonical form); 'Mr         ' variant just CONTINUEs without normalisation | ED010 lines 607-620  |
| 17 | Title normalisation -- Mrs         | CUSTTITI = 'MRS_______', 'Mrs_______', 'MRS       ', 'mrs_______'; 'Mrs       ' (Mrs + 7 spaces) passes with CONTINUE | MOVE 'Mrs' TO CUSTTITI; 'Mrs       ' variant just CONTINUEs | ED010 lines 621-634  |
| 18 | Title normalisation -- Miss        | CUSTTITI = 'MISS______', 'Miss______', 'MISS      ', 'Miss      ', 'miss______'                  | MOVE 'Miss' TO CUSTTITI (all variants normalise)                                                                                                          | ED010 lines 635-649  |
| 19 | Title normalisation -- Ms          | CUSTTITI = 'MS________', 'Ms________', 'ms________', 'MS        ', 'Ms        ', 'ms        '   | MOVE 'Ms' TO CUSTTITI                                                                                                                                     | ED010 lines 650-667  |
| 20 | Title normalisation -- Dr          | CUSTTITI = 'DR________', 'Dr________', 'DR        ', 'Dr        ', 'dr        ', 'dr________'   | MOVE 'Dr' TO CUSTTITI                                                                                                                                     | ED010 lines 668-685  |
| 21 | Title normalisation -- Drs         | CUSTTITI = 'DRS_______', 'Drs_______', 'DRS       ', 'Drs       ', 'drs       ', 'drs_______'   | MOVE 'Drs' TO CUSTTITI                                                                                                                                    | ED010 lines 686-703  |
| 22 | Title normalisation -- Professor    | CUSTTITI = 'PROFESSOR_', 'Professor_', 'PROFESSOR ', 'Professor '                                | MOVE 'Professor' TO CUSTTITI                                                                                                                              | ED010 lines 704-715  |
| 23 | Title normalisation -- Lord        | CUSTTITI = 'LORD______', 'Lord______', 'LORD      ', 'Lord      ', 'lord      ', 'lord______'   | MOVE 'Lord' TO CUSTTITI                                                                                                                                   | ED010 lines 716-733  |
| 24 | Title normalisation -- Lady        | CUSTTITI = 'LADY______', 'Lady______', 'LADY      ', 'Lady      ', 'lady      ', 'lady______'   | MOVE 'Lady' TO CUSTTITI                                                                                                                                   | ED010 lines 734-751  |
| 25 | Title normalisation -- Sir         | CUSTTITI = 'SIR_______', 'Sir_______', 'SIR       ', 'Sir       ', 'sir       ', 'sir_______'   | MOVE 'Sir' TO CUSTTITI                                                                                                                                    | ED010 lines 752-769  |
| 26 | First name is mandatory            | CHRISTNL < 1 OR CHRISTNI = '____________________' OR CHRISTNI = SPACES                          | Message: 'Please supply a valid First Name'; set cursor on CHRISTN; set VALID-DATA-SW = 'N'; GO TO ED999                                                   | ED010 lines 783-792  |
| 27 | Surname is mandatory               | CUSTSNL < 1 OR CUSTSNI = '____________________' OR CUSTSNI = SPACES                             | Message: 'Please supply a valid Surname'; set cursor on CUSTSN; set VALID-DATA-SW = 'N'; GO TO ED999                                                       | ED010 lines 794-803  |
| 28 | Address line 1 is mandatory        | CUSTAD1I(1:1) = '_' OR CUSTAD1L < 1 OR CUSTAD1I = SPACES                                        | Message: 'Please supply a valid Address Line 1'; set cursor on CUSTAD1; set VALID-DATA-SW = 'N'; GO TO ED999                                               | ED010 lines 805-814  |
| 29 | Date of birth day (DD) is mandatory | DOBDDL < 1 OR DOBDDI = '__'                                                                     | Message: 'Please supply a valid Date of Birth DD'; set cursor on DOBDD; set VALID-DATA-SW = 'N'; GO TO ED999                                               | ED010 lines 816-824  |
| 30 | Date of birth month (MM) is mandatory | DOBMML < 1 OR DOBMMI = '__'                                                                   | Message: 'Please supply a valid Date of Birth MM'; set cursor on DOBMM; set VALID-DATA-SW = 'N'; GO TO ED999                                               | ED010 lines 826-834  |
| 31 | Date of birth year (YYYY) is mandatory | DOBYYL < 4 OR DOBYYI = '____'                                                                | Message: 'Please supply a valid Date of Birth YYYY'; set cursor on DOBYY; set VALID-DATA-SW = 'N'; GO TO ED999                                             | ED010 lines 836-844  |
| 32 | DOB day must be numeric            | DOBDDI NOT NUMERIC                                                                               | Message: 'Non numeric Date of Birth DD entered'; set cursor on DOBDD; set VALID-DATA-SW = 'N'; GO TO ED999                                                  | ED010 lines 846-854  |
| 33 | DOB month must be numeric          | DOBMMI NOT NUMERIC                                                                               | Message: 'Non numeric Date of Birth MM entered'; set cursor on DOBMM; set VALID-DATA-SW = 'N'; GO TO ED999                                                  | ED010 lines 856-864  |
| 34 | DOB year must be numeric           | DOBYYI NOT NUMERIC                                                                               | Message: 'Non numeric Date of Birth YYYY entered'; set cursor on DOBYY; set VALID-DATA-SW = 'N'; GO TO ED999                                                | ED010 lines 866-874  |
| 35 | DOB day range: 01-31               | DOBDDI-NUM < 01 OR DOBDDI-NUM > 31 (after MOVE DOBDDI TO DOBDDI-CHAR, read via DOBDDI-REFORM redefine) | Message: 'Please supply a valid Date of Birth (DD)'; set cursor on DOBDD; set VALID-DATA-SW = 'N'; GO TO ED999                                      | ED010 lines 876-886  |
| 36 | DOB month range: 01-12             | DOBMMI-NUM < 01 OR DOBMMI-NUM > 12 (after MOVE DOBMMI TO DOBMMI-CHAR, read via DOBMMI-REFORM redefine) | Message: 'Please supply a valid Date of Birth (MM)'; set cursor on DOBMM; set VALID-DATA-SW = 'N'; GO TO ED999                                      | ED010 lines 888-897  |
| 37 | DOB year -- no range check         | No condition -- validation stops after numeric check for YYYY                                    | No year range validation exists in BNK1CCS; any numeric 4-digit year is accepted and passed to CRECUST; DOBYYI-CHAR/DOBYYI-NUM are defined in WORKING-STORAGE (lines 91-93) but never referenced in the PROCEDURE DIVISION -- dead code                    | ED010 (absent); DATA DIVISION lines 91-93 |
| 38 | Mandatory fields catch-all         | Any of CUSTTITL, CHRISTNL, CUSTSNL, CUSTAD1L, DOBDDL, DOBMML, or DOBYYL < 1 at end of edit    | Message: 'Missing expected data.'; EVALUATE finds first failing field and sets its length to -1 (cursor); set VALID-DATA-SW = 'N'; GO TO ED999              | ED010 lines 899-931  |

### Customer Creation Processing (CCD010 -- CRE-CUST-DATA SECTION)

| #  | Rule                                  | Condition                             | Action                                                                                                                                                      | Source Location       |
| -- | ------------------------------------- | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| 39 | SUBPGM-PARMS initialisation           | Always, before building fields        | INITIALIZE SUBPGM-PARMS; MOVE 'CUST' TO SUBPGM-EYECATCHER; MOVE 'N' TO SUBPGM-SUCCESS -- eyecatcher and default failure state set before LINK              | CCD010 lines 942-944  |
| 40 | Underscore removal before assembly    | Always (BMS fills unused characters with '_') | INSPECT CUSTTITI, CHRISTNI, CUSTINSI, CUSTSNI, CUSTAD1I, CUSTAD2I, CUSTAD3I REPLACING ALL '_' BY ' ' before building name and address strings | CCD010 lines 949-965  |
| 41 | Name assembly                         | Always                                | STRING title + space + first-name + space + initials + space + surname DELIMITED BY SPACE INTO SUBPGM-NAME (60 chars)                                       | CCD010 lines 954-961  |
| 42 | Address assembly                      | Always                                | STRING CUSTAD1I + CUSTAD2I + CUSTAD3I DELIMITED BY SIZE INTO SUBPGM-ADDRESS (160 chars)                                                                    | CCD010 lines 967-970  |
| 43 | DOB mapping to back-end               | Always                                | MOVE DOBDDI TO SUBPGM-BIRTH-DAY, DOBMMI TO SUBPGM-BIRTH-MONTH, DOBYYI TO SUBPGM-BIRTH-YEAR; stored as DDMMYYYY in PIC 9(8) SUBPGM-DATE-OF-BIRTH           | CCD010 lines 972-974  |
| 44 | CRECUST LINK with SYNCONRETURN        | Always after field assembly            | EXEC CICS LINK PROGRAM('CRECUST') COMMAREA(SUBPGM-PARMS) SYNCONRETURN -- create customer and commit on return                                              | CCD010 lines 976-982  |
| 45 | Creation failure -- generic           | SUBPGM-SUCCESS = 'N' (returned by CRECUST) | Message: 'Sorry but unable to create Customer record'; set VALID-DATA-SW = 'N'                                                                        | CCD010 lines 1048-1064 |
| 46 | Creation failure -- customer too old   | SUBPGM-FAIL-CODE = 'O'               | Message: 'Sorry, customer is too old. Please check D.O.B.'                                                                                                  | CCD010 lines 1052-1055 |
| 47 | Creation failure -- DOB in future      | SUBPGM-FAIL-CODE = 'Y'               | Message: 'Sorry, customer D.O.B. is in the future.'                                                                                                         | CCD010 lines 1056-1059 |
| 48 | Creation failure -- DOB invalid        | SUBPGM-FAIL-CODE = 'Z'               | Message: 'Sorry, customer D.O.B. is invalid.'                                                                                                               | CCD010 lines 1060-1063 |
| 49 | Creation success                       | SUBPGM-SUCCESS = 'Y'                 | Message: 'The Customer record has been successfully created'; display returned sort code (SUBPGM-SORTCODE) and customer number (SUBPGM-NUMBER) on map       | CCD010 lines 1067-1075 |
| 50 | Display returned data after creation   | Always (success or failure)           | Populate map output fields: DOBYYO, DOBMMO, DOBDDO from SUBPGM-DOB-GROUP; CUSTAD1O/2O/3O from SUBPGM-ADDRESS split; CREDSCO from SUBPGM-CREDIT-SCORE; credit-score review date DD/MM/YYYY from SUBPGM-CS-REVIEW-DATE(1:2/3:2/5:4) | CCD010 lines 1080-1093 |

### Process Map Dispatch (PM010)

| #  | Rule                        | Condition            | Action                                                               | Source Location |
| -- | --------------------------- | -------------------- | -------------------------------------------------------------------- | --------------- |
| 51 | Conditional customer create | VALID-DATA (88-level: VALID-DATA-SW = 'Y') after EDIT-DATA | PERFORM CRE-CUST-DATA -- only invoked when all validations pass | PM010 line 366  |
| 52 | Always alarm on redisplay   | After PROCESS-MAP regardless of outcome | SET SEND-DATAONLY-ALARM TO TRUE; PERFORM SEND-MAP                    | PM010 lines 370-374 |

## Calculations

| Calculation       | Formula / Logic                                                                                           | Input Fields                                      | Output Field   | Source Location      |
| ----------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | -------------- | -------------------- |
| Full name build   | CUSTTITI (trimmed at SPACE) + ' ' + CHRISTNI (trimmed) + ' ' + CUSTINSI (trimmed) + ' ' + CUSTSNI (full) | CUSTTITI, CHRISTNI, CUSTINSI, CUSTSNI             | SUBPGM-NAME    | CCD010 lines 954-961 |
| Full address build | CUSTAD1I (60) \|\| CUSTAD2I (60) \|\| CUSTAD3I (40) concatenated by SIZE                                | CUSTAD1I, CUSTAD2I, CUSTAD3I                      | SUBPGM-ADDRESS | CCD010 lines 967-970 |
| Abend time format | HH:MM:MM string (note: minutes repeated where seconds should appear -- source bug)                        | WS-TIME-NOW-GRP-HH, WS-TIME-NOW-GRP-MM           | ABND-TIME      | All error-handling paragraphs |

## Error Handling

| Condition                                        | Action                                                                                                         | Return Code / Abend | Source Location          |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- | ------------------- | ------------------------ |
| EXEC CICS RETURN TRANSID(OCCS) fails             | Build ABNDINFO-REC with EIBRESP/EIBRESP2, link ABNDPROC, DISPLAY WS-FAIL-INFO, EXEC CICS ABEND ABCODE('HBNK') | HBNK                | A010 lines 284-343       |
| SET TERMINAL UCTRANST fails (in RECEIVE-MAP)     | Build ABNDINFO-REC, link ABNDPROC, DISPLAY WS-FAIL-INFO 'BNK1CCS - RM010 (1) - SET TERMINAL UC FAIL', ABEND   | HBNK                | RM010 lines 415-474      |
| EXEC CICS RECEIVE MAP fails                      | Build ABNDINFO-REC, link ABNDPROC, DISPLAY WS-FAIL-INFO 'BNK1CCS - RM010 (2) - RECEIVE MAP FAIL', ABEND       | HBNK                | RM010 lines 510-570      |
| EXEC CICS LINK CRECUST fails                     | Build ABNDINFO-REC, link ABNDPROC, DISPLAY WS-FAIL-INFO 'BNK1CCS - CCD010 - LINK CRECUST FAIL', ABEND         | HBNK                | CCD010 lines 984-1042    |
| SET TERMINAL UCTRANST fails (in STORE-TERM-DEF)  | Build ABNDINFO-REC, link ABNDPROC, DISPLAY WS-FAIL-INFO 'BNK1CCS - STD010 - SET TERMINAL UC FAIL', ABEND      | HBNK                | STD010 lines 1134-1193   |
| SET TERMINAL UCTRANST fails (in RESTORE-TERM-DEF)| Build ABNDINFO-REC, link ABNDPROC, DISPLAY WS-FAIL-INFO 'BNK1CCS - RTD010 - SET TERMINAL UC FAIL', ABEND; note: this path calls ABEND-THIS-TASK directly without a prior RESTORE-TERM-DEF call (other paragraphs call RESTORE-TERM-DEF then ABEND-THIS-TASK); ATT010 repeats the SET TERMINAL attempt which may fail again | HBNK | RTD010 lines 1217-1273 |
| EXEC CICS SEND MAP ERASE fails                   | Build ABNDINFO-REC, link ABNDPROC, DISPLAY WS-FAIL-INFO 'BNK1CCS - SM010 - SEND MAP ERASE FAIL', ABEND        | HBNK                | SM010 lines 1296-1356    |
| EXEC CICS SEND MAP DATAONLY fails                | Build ABNDINFO-REC, link ABNDPROC, DISPLAY WS-FAIL-INFO 'BNK1CCS - SM010 - SEND MAP DATAONLY FAIL', ABEND     | HBNK                | SM010 lines 1375-1434    |
| EXEC CICS SEND MAP DATAONLY ALARM fails          | Build ABNDINFO-REC, link ABNDPROC, DISPLAY WS-FAIL-INFO 'BNK1CCS - SM010 - SEND MAP DATAONLY ALARM FAIL', ABEND | HBNK              | SM010 lines 1454-1513    |
| EXEC CICS SEND TEXT (termination msg) fails      | Build ABNDINFO-REC, link ABNDPROC, DISPLAY WS-FAIL-INFO 'BNK1CCS - STM010 - SEND TEXT FAIL', ABEND             | HBNK              | STM010 lines 1534-1592   |
| Unexpected CICS abend (HANDLE-ABEND label)       | Restore terminal UCTRANS, EXEC CICS ASSIGN ABCODE to capture original code, EXEC CICS HANDLE ABEND CANCEL to deregister handler, re-raise via EXEC CICS ABEND ABCODE(WS-ABCODE) NODUMP | WS-ABCODE (original abend code) | HA010 lines 1644-1658 |
| CRECUST returns SUBPGM-SUCCESS = 'N'             | Display message per fail-code (O/Y/Z/generic); set VALID-DATA-SW = 'N'; do NOT abend                           | None (soft error)   | CCD010 lines 1048-1064   |
| CLEAR key inline SEND MAP fails                  | No error handling -- EXEC CICS SEND MAP('BNK1CCM') MAPONLY ERASE FREEKB at line 236 has no RESP parameter and no subsequent check; failure is silently ignored | None | A010 line 236 |

**Abend code pattern:** All terminal CICS infrastructure failures use abend code `HBNK`. The ABEND-THIS-TASK section (ATT010) reads DFHCOMMAREA to recover the saved UCTRANS value, restores terminal UCTRANS, then issues EXEC CICS ABEND ABCODE('HBNK') NODUMP CANCEL.

**Note on ABND-TIME bug:** In every paragraph, the STRING that builds ABND-TIME uses WS-TIME-NOW-GRP-MM for both the minutes and seconds positions. The seconds field WS-TIME-NOW-GRP-SS is never referenced. This means the abend timestamp always shows MM:MM instead of MM:SS. Source lines 1006-1011 (CCD010), 1318-1323 (SM010), and equivalents in all other error-handling paragraphs.

**Note on commarea LENGTH anomaly:** The pseudo-conversational EXEC CICS RETURN TRANSID('OCCS') at line 279 specifies LENGTH(248) but passes WS-COMM-AREA which is defined as PIC X (1 byte) + PIC S9(8) COMP (4 bytes) = 5 bytes total. The LINKAGE SECTION DFHCOMMAREA is also defined as PIC X(5). The LENGTH(248) value is inconsistent with the actual commarea structure and is likely an unintentional coding error. The CLEAR-key RETURN at line 249 does not specify LENGTH at all, which is the more consistent behaviour.

**Note on CLEAR key map name anomaly:** The inline EXEC CICS SEND at line 236 specifies MAP('BNK1CCM') with no MAPSET clause. BNK1CCM is the mapset name; the individual map is BNK1CC. The SM010 send-map routine correctly uses MAP('BNK1CC') MAPSET('BNK1CCM'). CICS interprets the MAP parameter as both the map name and mapset when MAPSET is omitted, so it will look for a map named BNK1CCM within mapset BNK1CCM rather than map BNK1CC within mapset BNK1CCM. Combined with the absence of RESP checking, this is a latent defect in the CLEAR key path.

**Note on DOBYYI-NUM dead code:** The DATE-REFORMED group (lines 91-93) defines DOBYYI-CHAR (PIC XX) and DOBYYI-NUM (PIC 99) as a numeric overlay for the 4-character year field DOBYYI. Neither DOBYYI-CHAR nor DOBYYI-NUM is referenced anywhere in the PROCEDURE DIVISION. Unlike DD (validated 01-31 via DOBDDI-NUM) and MM (validated 01-12 via DOBMMI-NUM), no year range validation exists in BNK1CCS -- any numeric 4-digit year passes through to CRECUST. Additionally, DOBYYI-CHAR is only PIC XX (2 bytes) while DOBYYI is PIC XX (from the BMS map, 4 chars for YYYY); had it been used, the MOVE would have truncated the year to its first 2 characters.

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. A010 (PREMIERE SECTION) -- entry point; registers HANDLE ABEND label, dispatches on EIBAID
2. STORE-TERM-DEF (STD010) -- called on first entry only; stores and disables terminal UCTRANS
3. SEND-MAP (SM010) -- sends BNK1CC map (mapset BNK1CCM) with ERASE on first entry; returns to A010
4. A010 final EXEC CICS RETURN TRANSID('OCCS') COMMAREA(WS-COMM-AREA) LENGTH(248) -- pseudo-conversational return storing UCTRANS in commarea
5. [Next transaction invocation] A010 dispatches ENTER key to PROCESS-MAP
6. PROCESS-MAP (PM010) -- orchestrates receive/edit/create cycle
7. RECEIVE-MAP (RM010) -- pre-initialises all BNK1CCI fields to safe defaults, disables UCTRANS if needed, EXEC CICS RECEIVE MAP BNK1CC ASIS; UCTRANS is NOT re-enabled here
8. EDIT-DATA (ED010) -- validates all field rules sequentially; exits with VALID-DATA-SW = 'Y' or 'N'
9. CRE-CUST-DATA (CCD010) -- only if VALID-DATA; initialises SUBPGM-PARMS with eyecatcher 'CUST', builds name/address/DOB fields, EXEC CICS LINK CRECUST SYNCONRETURN, evaluates SUBPGM-SUCCESS
10. SEND-MAP (SM010) -- SEND-DATAONLY-ALARM; returns results to terminal
11. A010 final EXEC CICS RETURN TRANSID('OCCS') -- waits for next input
12. PF3 path: RESTORE-TERM-DEF (RTD010) then EXEC CICS RETURN TRANSID('OMEN') -- back to main menu
13. PF12 path: SEND-TERMINATION-MSG (STM010), RESTORE-TERM-DEF (RTD010), EXEC CICS RETURN
14. Any CICS error path: POPULATE-TIME-DATE (PTD10) -> EXEC CICS LINK ABNDPROC -> ABEND-THIS-TASK (ATT010) -> EXEC CICS ABEND ABCODE('HBNK')
15. HANDLE-ABEND (HA010) -- catches unexpected abends, restores UCTRANS, cancels abend handler, re-raises with original abend code
