---
type: business-rules
program: COCRDUPC
program_type: online
status: draft
confidence: high
last_pass: 5
calls: []
called_by: []
uses_copybooks:
- COCOM01Y
- COCRDUP
- COTTL01Y
- CSDAT01Y
- CSMSG01Y
- CSMSG02Y
- CSSTRPFY
- CSUSR01Y
- CVACT02Y
- CVCRD01Y
- CVCUS01Y
reads:
- CARDDAT
writes:
- CARDDAT
db_tables: []
transactions:
- CCUP
mq_queues: []
---

# COCRDUPC -- Business Rules

## Program Purpose

COCRDUPC is a CICS online program that implements the credit card detail update workflow. It accepts an account number and card number from the user, fetches the associated card record from the CARDDAT file, presents the card details for editing, validates the user-supplied changes, obtains a confirmation key-press (PF5), and writes the updated record back using an optimistic locking / locked-update pattern. The program is entered under transaction CCUP and can be reached either directly from the main menu (COMEN01C) or from the card list screen (COCRDLIC / CCLI).

The program implements a multi-pass conversation using CICS pseudo-conversational technique: each RETURN stores session state in the COMMAREA (CARDDEMO-COMMAREA + WS-THIS-PROGCOMMAREA), and the next invocation picks up where it left off.

Note: The YYYY-STORE-PFKEY paragraph is not defined in COCRDUPC itself; it is included via `COPY 'CSSTRPFY'` at line 1528, which is a PROCEDURE DIVISION COPY that inlines the paragraph code directly into the compiled program.

## Input / Output

| Direction | Resource     | Type   | Description                                                          |
| --------- | ------------ | ------ | -------------------------------------------------------------------- |
| IN        | CARDDAT      | CICS   | VSAM card master file; keyed by 16-digit card number (READ for fetch)|
| IN/OUT    | CARDDAT      | CICS   | READ UPDATE + REWRITE to update card record                          |
| IN        | CCRDUPAI     | CICS   | BMS map CCRDUPA in mapset COCRDUP; receives user input fields        |
| OUT       | CCRDUPAO     | CICS   | BMS map CCRDUPA in mapset COCRDUP; sends screen to terminal          |
| IN/OUT    | DFHCOMMAREA  | CICS   | 2000-byte COMMAREA carries CARDDEMO-COMMAREA + WS-THIS-PROGCOMMAREA  |

## Business Rules

### Program Entry and Initialisation

| #  | Rule                             | Condition                                                                                         | Action                                                                                                                          | Source Location       |
| -- | -------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| 1  | Fresh entry from menu            | EIBCALEN = 0, OR (CDEMO-FROM-PROGRAM = LIT-MENUPGM ('COMEN01C') AND NOT CDEMO-PGM-REENTER)      | Initialise CARDDEMO-COMMAREA and WS-THIS-PROGCOMMAREA; set CDEMO-PGM-ENTER; set CCUP-DETAILS-NOT-FETCHED                       | 0000-MAIN lines 388-401 |
| 2  | Restore COMMAREA on re-entry     | EIBCALEN > 0 and not a fresh-from-menu entry                                                      | Move DFHCOMMAREA(1:LENGTH OF CARDDEMO-COMMAREA) to CARDDEMO-COMMAREA; move remainder to WS-THIS-PROGCOMMAREA                   | 0000-MAIN lines 396-400 |
| 3  | PF key normalisation             | PF13-PF24 received                                                                                | CSSTRPFY (inlined via COPY 'CSSTRPFY' at line 1528) maps PF13-PF24 to their PF1-PF12 equivalents before any routing logic sees the AID | YYYY-STORE-PFKEY (CSSTRPFY copybook, inlined at line 1528) |
| 4  | Valid AID gate                   | AID must be Enter, PF3, (PF5 when CCUP-CHANGES-OK-NOT-CONFIRMED), or (PF12 when NOT CCUP-DETAILS-NOT-FETCHED) | If AID is not one of these, force AID to Enter (PFK-INVALID path sets CCARD-AID-ENTER)                               | 0000-MAIN lines 413-424 |

### Routing / Dispatch (0000-MAIN EVALUATE)

| #  | Rule                             | Condition                                                                                         | Action                                                                                                                          | Source Location       |
| -- | -------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| 5  | Exit to calling program (PF3)    | CCARD-AID-PFK03                                                                                   | SYNCPOINT; XCTL to CDEMO-FROM-PROGRAM (or COMEN01C if none). Clears account/card in COMMAREA if last mapset was COCRDLI.       | 0000-MAIN lines 435-476 |
| 6  | Exit after successful update     | CCUP-CHANGES-OKAYED-AND-DONE AND CDEMO-LAST-MAPSET = LIT-CCLISTMAPSET ('COCRDLI')                | Same XCTL exit as PF3. Clears CDEMO-ACCT-ID and CDEMO-CARD-NUM before XCTL.                                                   | 0000-MAIN lines 436-476 |
| 7  | Exit after failed update         | CCUP-CHANGES-FAILED AND CDEMO-LAST-MAPSET = LIT-CCLISTMAPSET ('COCRDLI')                         | Same XCTL exit as PF3.                                                                                                         | 0000-MAIN lines 438-476 |
| 8  | Return to caller default         | CDEMO-FROM-TRANID is LOW-VALUES or SPACES on any exit path                                       | Route to LIT-MENUTRANID ('CM00') and LIT-MENUPGM ('COMEN01C')                                                                 | 0000-MAIN lines 442-454 |
| 9  | Entry from card list (COCRDLIC)  | CDEMO-PGM-ENTER AND CDEMO-FROM-PROGRAM = LIT-CCLISTPGM ('COCRDLIC'), OR PF12 AND CDEMO-FROM-PROGRAM = 'COCRDLIC' | Accept search keys from COMMAREA; PERFORM 9000-READ-DATA; set CCUP-SHOW-DETAILS; send map                        | 0000-MAIN lines 482-497 |
| 10 | Fresh entry / no details yet     | CCUP-DETAILS-NOT-FETCHED AND CDEMO-PGM-ENTER, OR CDEMO-FROM-PROGRAM = LIT-MENUPGM AND NOT CDEMO-PGM-REENTER | Initialise WS-THIS-PROGCOMMAREA; send map prompting for account/card; set CDEMO-PGM-REENTER; keep CCUP-DETAILS-NOT-FETCHED | 0000-MAIN lines 502-511 |
| 11 | After completed/failed update    | CCUP-CHANGES-OKAYED-AND-DONE or CCUP-CHANGES-FAILED (not from COCRDLIC)                         | Re-initialise WS-THIS-PROGCOMMAREA, WS-MISC-STORAGE, CDEMO-ACCT-ID, CDEMO-CARD-NUM; set CDEMO-PGM-ENTER; send fresh search screen | 0000-MAIN lines 517-528 |
| 12 | Normal processing path           | WHEN OTHER (details shown, user making edits)                                                     | PERFORM 1000-PROCESS-INPUTS, PERFORM 2000-DECIDE-ACTION, PERFORM 3000-SEND-MAP                                                 | 0000-MAIN lines 535-542 |

### Input Validation -- Search Key Phase (CCUP-DETAILS-NOT-FETCHED)

| #  | Rule                               | Condition                                                                              | Action                                                                                            | Source Location            |
| -- | ---------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | -------------------------- |
| 13 | Account number mandatory           | CC-ACCT-ID = LOW-VALUES, SPACES, or CC-ACCT-ID-N = ZEROS                             | INPUT-ERROR; FLG-ACCTFILTER-BLANK; WS-RETURN-MSG set to "Account number not provided"; zero CDEMO-ACCT-ID and CCUP-NEW-ACCTID | 1210-EDIT-ACCOUNT lines 725-735 |
| 14 | Account number must be numeric     | CC-ACCT-ID IS NOT NUMERIC (and not blank)                                             | INPUT-ERROR; FLG-ACCTFILTER-NOT-OK; WS-RETURN-MSG = 'ACCOUNT FILTER,IF SUPPLIED MUST BE A 11 DIGIT NUMBER' | 1210-EDIT-ACCOUNT lines 740-750 |
| 15 | Account number valid               | CC-ACCT-ID IS NUMERIC (11 digits, non-zero)                                           | FLG-ACCTFILTER-ISVALID; copy to CDEMO-ACCT-ID and CCUP-NEW-ACCTID                                 | 1210-EDIT-ACCOUNT lines 751-754 |
| 16 | Card number mandatory              | CC-CARD-NUM = LOW-VALUES, SPACES, or CC-CARD-NUM-N = ZEROS                           | INPUT-ERROR; FLG-CARDFILTER-BLANK; WS-RETURN-MSG set to "Card number not provided"; zero CDEMO-CARD-NUM and CCUP-NEW-CARDID | 1220-EDIT-CARD lines 768-779 |
| 17 | Card number must be numeric        | CC-CARD-NUM IS NOT NUMERIC (and not blank)                                            | INPUT-ERROR; FLG-CARDFILTER-NOT-OK; WS-RETURN-MSG = 'CARD ID FILTER,IF SUPPLIED MUST BE A 16 DIGIT NUMBER' | 1220-EDIT-CARD lines 784-794 |
| 18 | Card number valid                  | CC-CARD-NUM IS NUMERIC (16 digits)                                                    | FLG-CARDFILTER-ISVALID; CC-CARD-NUM-N to CDEMO-CARD-NUM; CC-CARD-NUM to CCUP-NEW-CARDID           | 1220-EDIT-CARD lines 795-798 |
| 19 | No search criteria at all          | FLG-ACCTFILTER-BLANK AND FLG-CARDFILTER-BLANK                                        | Set NO-SEARCH-CRITERIA-RECEIVED; WS-RETURN-MSG = "No input received"; skip further edits          | 1200-EDIT-MAP-INPUTS lines 656-661 |

### Input Validation -- Card Update Phase (details already fetched)

| #  | Rule                                    | Condition                                                                                               | Action                                                                                            | Source Location                  |
| -- | --------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | -------------------------------- |
| 20 | No change bypass                        | FUNCTION UPPER-CASE(CCUP-NEW-CARDDATA) = FUNCTION UPPER-CASE(CCUP-OLD-CARDDATA) (case-insensitive compare of 59-byte group) | Set NO-CHANGES-DETECTED; WS-RETURN-MSG = "No change detected with respect to values fetched."; skip field edits | 1200-EDIT-MAP-INPUTS lines 680-693 |
| 21 | Confirmation/done state bypass          | NO-CHANGES-DETECTED, OR CCUP-CHANGES-OK-NOT-CONFIRMED, OR CCUP-CHANGES-OKAYED-AND-DONE                 | Mark all four field flags ISVALID (cardname, cardstatus, expmon, expyear); skip field edits; GO TO EXIT | 1200-EDIT-MAP-INPUTS lines 685-692 |
| 22 | Card embossed name mandatory            | CCUP-NEW-CRDNAME = LOW-VALUES, SPACES, or ZEROS                                                         | INPUT-ERROR; FLG-CARDNAME-BLANK; WS-RETURN-MSG = "Card name not provided"                         | 1230-EDIT-NAME lines 811-819 |
| 23 | Card embossed name alphabetic only      | After INSPECT CONVERTING LIT-ALL-ALPHA-FROM (A-Z + a-z, 52 chars) TO SPACES, FUNCTION TRIM result length != 0 | INPUT-ERROR; FLG-CARDNAME-NOT-OK; WS-RETURN-MSG = "Card name can only contain alphabets and spaces" | 1230-EDIT-NAME lines 822-836 |
| 24 | Card active status mandatory            | CCUP-NEW-CRDSTCD = LOW-VALUES, SPACES, or ZEROS                                                         | INPUT-ERROR; FLG-CARDSTATUS-BLANK; WS-RETURN-MSG = "Card Active Status must be Y or N"            | 1240-EDIT-CARDSTATUS lines 850-858 |
| 25 | Card active status must be Y or N       | FLG-YES-NO-CHECK NOT IN ('Y', 'N') (88-level FLG-YES-NO-VALID)                                        | INPUT-ERROR; FLG-CARDSTATUS-NOT-OK; WS-RETURN-MSG = "Card Active Status must be Y or N"           | 1240-EDIT-CARDSTATUS lines 861-872 |
| 26 | Expiry month mandatory                  | CCUP-NEW-EXPMON = LOW-VALUES, SPACES, or ZEROS                                                          | INPUT-ERROR; FLG-CARDEXPMON-BLANK; WS-RETURN-MSG = "Card expiry month must be between 1 and 12"   | 1250-EDIT-EXPIRY-MON lines 883-892 |
| 27 | Expiry month range 1-12                 | CARD-MONTH-CHECK-N (PIC 9(2) redefine of CCUP-NEW-EXPMON) NOT IN 1 THRU 12 (88-level VALID-MONTH)    | INPUT-ERROR; FLG-CARDEXPMON-NOT-OK; WS-RETURN-MSG = "Card expiry month must be between 1 and 12"  | 1250-EDIT-EXPIRY-MON lines 896-907 |
| 28 | Expiry year mandatory                   | CCUP-NEW-EXPYEAR = LOW-VALUES, SPACES, or ZEROS                                                         | INPUT-ERROR; FLG-CARDEXPYEAR-BLANK; WS-RETURN-MSG = "Invalid card expiry year"                    | 1260-EDIT-EXPIRY-YEAR lines 916-924 |
| 29 | Expiry year range 1950-2099             | CARD-YEAR-CHECK-N (PIC 9(4) redefine of CCUP-NEW-EXPYEAR) NOT IN 1950 THRU 2099 (88-level VALID-YEAR) | INPUT-ERROR; FLG-CARDEXPYEAR-NOT-OK; WS-RETURN-MSG = "Invalid card expiry year"                   | 1260-EDIT-EXPIRY-YEAR lines 930-943 |
| 30 | All field edits pass                    | INPUT-ERROR is NOT set after all four field edit paragraphs                                             | Set CCUP-CHANGES-OK-NOT-CONFIRMED; prompts user for PF5 confirmation                              | 1200-EDIT-MAP-INPUTS lines 710-714 |

### Error Message Priority

| #  | Rule                               | Condition                                                                 | Action                                                                               | Source Location                            |
| -- | ---------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------ |
| 31 | First-error-wins message guard     | WS-RETURN-MSG-OFF (PIC X(75) = SPACES) before setting any error message   | All error-message SET/MOVE statements are guarded by `IF WS-RETURN-MSG-OFF`. Once any error message is set, subsequent validation errors do not overwrite it. The message that appears reflects the first validation failure encountered in the sequence: 1210 -> 1220 -> 1230 -> 1240 -> 1250 -> 1260 | All validation paragraphs (lines 730, 743, 769, 784, 812, 823, 851, 862, 884, 897, 917, 931) |

### Map Input Normalisation

| #  | Rule                                | Condition                                          | Action                                                                        | Source Location             |
| -- | ----------------------------------- | -------------------------------------------------- | ----------------------------------------------------------------------------- | --------------------------- |
| 32 | Sentinel value '*' treated as blank | Screen field = '*' or SPACES for ACCTSIDI, CARDSIDI, CRDNAMEI, CRDSTCDI, EXPMONI, EXPYEARI | Field is set to LOW-VALUES (treated as not supplied); CCUP-NEW-DETAILS initialised at start of paragraph | 1100-RECEIVE-MAP lines 578-635 |
| 33 | Expiry day passthrough              | Always                                             | EXPDAYI is moved directly to CCUP-NEW-EXPDAY without any '*' or SPACES normalisation and without validation (day is not validated at screen input). CCUP-NEW-EXPDAY is then used in the 9200 WRITE path STRING statement (line 1471) -- the day field is marked DFHBMDAR (dark) so CICS typically returns LOW-VALUES or the transmitted value for a non-modified protected field | 1100-RECEIVE-MAP line 621; 9200-WRITE-PROCESSING line 1471 |

### Action Decision (2000-DECIDE-ACTION)

| #  | Rule                                        | Condition                                                                                      | Action                                                                                              | Source Location               |
| -- | ------------------------------------------- | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ----------------------------- |
| 34 | No-op when details not yet fetched          | CCUP-DETAILS-NOT-FETCHED (falls through to next WHEN in EVALUATE)                             | No action -- falls through to PF12 WHEN clause without executing any statements                    | 2000-DECIDE-ACTION line 954   |
| 35 | Fetch card on PF12 refresh                  | CCARD-AID-PFK12 AND FLG-ACCTFILTER-ISVALID AND FLG-CARDFILTER-ISVALID                        | PERFORM 9000-READ-DATA; if FOUND-CARDS-FOR-ACCOUNT set CCUP-SHOW-DETAILS                           | 2000-DECIDE-ACTION lines 958-965 |
| 36 | Promote to confirmed when changes OK        | CCUP-SHOW-DETAILS AND NOT INPUT-ERROR AND NOT NO-CHANGES-DETECTED                             | Set CCUP-CHANGES-OK-NOT-CONFIRMED                                                                   | 2000-DECIDE-ACTION lines 971-977 |
| 37 | Persist error state                         | CCUP-CHANGES-NOT-OK                                                                            | CONTINUE (errors remain on screen)                                                                  | 2000-DECIDE-ACTION line 983   |
| 38 | Save on PF5 confirmation                    | CCUP-CHANGES-OK-NOT-CONFIRMED AND CCARD-AID-PFK05                                             | PERFORM 9200-WRITE-PROCESSING; evaluate result and set CCUP-CHANGES-OKAYED-AND-DONE / lock error / update failed | 2000-DECIDE-ACTION lines 988-1001 |
| 39 | Lock error after confirmed save             | 9200-WRITE-PROCESSING returns COULD-NOT-LOCK-FOR-UPDATE                                       | Set CCUP-CHANGES-OKAYED-LOCK-ERROR ('L')                                                            | 2000-DECIDE-ACTION line 994   |
| 40 | REWRITE failure after confirmed save        | 9200-WRITE-PROCESSING returns LOCKED-BUT-UPDATE-FAILED                                        | Set CCUP-CHANGES-OKAYED-BUT-FAILED ('F')                                                            | 2000-DECIDE-ACTION line 996   |
| 41 | Concurrent modification detected            | 9200-WRITE-PROCESSING returns DATA-WAS-CHANGED-BEFORE-UPDATE                                  | Set CCUP-SHOW-DETAILS (refresh card from reloaded values); user sees updated data from DB           | 2000-DECIDE-ACTION line 998   |
| 42 | Successful save                             | 9200-WRITE-PROCESSING completes without error (WHEN OTHER in inner EVALUATE)                  | Set CCUP-CHANGES-OKAYED-AND-DONE ('C'); WS-INFO-MSG will show "Changes committed to database"       | 2000-DECIDE-ACTION line 1000  |
| 43 | Re-display after confirmation not given     | CCUP-CHANGES-OK-NOT-CONFIRMED AND NOT CCARD-AID-PFK05 (second WHEN clause)                   | CONTINUE -- screen re-displays with PF5 confirmation prompt still active                            | 2000-DECIDE-ACTION line 1006  |
| 44 | Reset after update done (standalone entry)  | CCUP-CHANGES-OKAYED-AND-DONE (reached in DECIDE-ACTION, not via XCTL path)                   | Set CCUP-SHOW-DETAILS; if CDEMO-FROM-TRANID = LOW-VALUES or SPACES: zero CDEMO-ACCT-ID, CDEMO-CARD-NUM, LOW-VALUES to CDEMO-ACCT-STATUS | 2000-DECIDE-ACTION lines 1011-1018 |
| 45 | Unhandled state ABEND                       | WHEN OTHER in 2000-DECIDE-ACTION                                                               | Set ABEND-CODE '0001', ABEND-MSG 'UNEXPECTED DATA SCENARIO'; PERFORM ABEND-ROUTINE (CICS ABEND ABCODE '9999') | 2000-DECIDE-ACTION lines 1019-1026 |

### Data Read (9000-READ-DATA / 9100-GETCARD-BYACCTCARD)

| #  | Rule                                | Condition                                                          | Action                                                                                                   | Source Location                |
| -- | ----------------------------------- | ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- | ------------------------------ |
| 46 | Card record read by card number     | Always on read                                                     | EXEC CICS READ FILE(LIT-CARDFILENAME='CARDDAT ') RIDFLD(WS-CARD-RID-CARDNUM) KEYLENGTH(16); key is the 16-char card number | 9100-GETCARD-BYACCTCARD lines 1382-1390 |
| 47 | Card found                          | DFHRESP(NORMAL)                                                    | Set FOUND-CARDS-FOR-ACCOUNT (88-level on WS-INFO-MSG = "Details of selected card shown above"); populate CCUP-OLD-DETAILS from CARD-RECORD | 9100-GETCARD-BYACCTCARD lines 1393-1394 |
| 48 | Card not found                      | DFHRESP(NOTFND)                                                    | INPUT-ERROR; FLG-ACCTFILTER-NOT-OK; FLG-CARDFILTER-NOT-OK; WS-RETURN-MSG = "Did not find cards for this search condition" | 9100-GETCARD-BYACCTCARD lines 1395-1401 |
| 49 | Card read system error              | DFHRESP other than NORMAL or NOTFND                                | INPUT-ERROR; FLG-ACCTFILTER-NOT-OK only (FLG-CARDFILTER-NOT-OK is NOT set on system errors, unlike NOTFND); format WS-FILE-ERROR-MESSAGE: "File Error: READ on CARDDAT  returned RESP nnn ,RESP2 nnn"; WS-FILE-ERROR-MESSAGE moved directly to WS-RETURN-MSG (not guarded by WS-RETURN-MSG-OFF) | 9100-GETCARD-BYACCTCARD lines 1402-1411 |
| 50 | Embossed name case normalisation    | Always on read (when FOUND-CARDS-FOR-ACCOUNT)                      | INSPECT CARD-EMBOSSED-NAME CONVERTING LIT-LOWER (26 chars) TO LIT-UPPER (26 chars) -- stored uppercase in CCUP-OLD-CRDNAME | 9000-READ-DATA lines 1356-1358 |
| 51 | Expiry date parsing                 | Always on read (when FOUND-CARDS-FOR-ACCOUNT)                      | Extract CARD-EXPIRAION-DATE(1:4) to CCUP-OLD-EXPYEAR, (6:2) to CCUP-OLD-EXPMON, (9:2) to CCUP-OLD-EXPDAY (format YYYY-MM-DD) | 9000-READ-DATA lines 1361-1366  |

### Data Integrity and Locking (9200-WRITE-PROCESSING / 9300-CHECK-CHANGE-IN-REC)

| #  | Rule                                     | Condition                                                                          | Action                                                                                                          | Source Location                    |
| -- | ---------------------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| 52 | Exclusive lock required before update    | READ UPDATE issued before REWRITE                                                  | EXEC CICS READ FILE(LIT-CARDFILENAME) UPDATE RIDFLD(WS-CARD-RID-CARDNUM); if not DFHRESP(NORMAL): INPUT-ERROR, COULD-NOT-LOCK-FOR-UPDATE, GO TO EXIT | 9200-WRITE-PROCESSING lines 1427-1449 |
| 53 | Optimistic change detection              | After READ UPDATE, before REWRITE                                                  | PERFORM 9300-CHECK-CHANGE-IN-REC: normalise name to uppercase then compare CARD-CVV-CD, CARD-EMBOSSED-NAME, CARD-EXPIRAION-DATE(1:4)/(6:2)/(9:2), CARD-ACTIVE-STATUS against CCUP-OLD-* values | 9300-CHECK-CHANGE-IN-REC lines 1499-1519 |
| 54 | Concurrent modification abort            | Any of the six fields differs (CVV-CD, EMBOSSED-NAME, expiry year, month, day, active status) | SET DATA-WAS-CHANGED-BEFORE-UPDATE; copy the six DB values into CCUP-OLD-* (refresh snapshot); WS-RETURN-MSG = "Record changed by some one else. Please review"; GO TO 9200-WRITE-PROCESSING-EXIT (skips REWRITE) | 9300-CHECK-CHANGE-IN-REC lines 1510-1518 |
| 55 | Expiry date formatting for write         | Always on update path after change check passes                                    | STRING CCUP-NEW-EXPYEAR '-' CCUP-NEW-EXPMON '-' CCUP-NEW-EXPDAY DELIMITED BY SIZE INTO CARD-UPDATE-EXPIRAION-DATE | 9200-WRITE-PROCESSING lines 1467-1474 |
| 56 | CVV code passthrough                     | Always on update                                                                   | CCUP-NEW-CVV-CD moved to CARD-CVV-CD-X (PIC X(3) redefine); CARD-CVV-CD-N (PIC 9(3) redefine) moved to CARD-UPDATE-CVV-CD (PIC 9(3)). CVV is not editable by user; old value preserved | 9200-WRITE-PROCESSING lines 1464-1465 |
| 57 | Expiry day write uses screen-received value | Always on update                                                               | CCUP-NEW-EXPDAY (received from EXPDAYI in 1100-RECEIVE-MAP line 621, no sentinel normalisation) is used in the STRING for CARD-UPDATE-EXPIRAION-DATE (line 1471). For screen DISPLAY, CCUP-OLD-EXPDAY is used instead (3200-SETUP-SCREEN-VARS line 1123, with line 1122 commented out confirming this is intentional split). Since EXPDAYA has attribute DFHBMDAR (dark/protected), CICS typically returns LOW-VALUES for the field unless the terminal transmits modified data indicator. | 3200-SETUP-SCREEN-VARS line 1123; 9200-WRITE-PROCESSING line 1471 |
| 58 | REWRITE failure                          | EXEC CICS REWRITE RESP not DFHRESP(NORMAL)                                        | Set LOCKED-BUT-UPDATE-FAILED; WS-RETURN-MSG = "Update of record failed"                                         | 9200-WRITE-PROCESSING lines 1488-1492 |

### Screen Attribute Rules (3300-SETUP-SCREEN-ATTRS)

| #  | Rule                                   | Condition                                                         | Action                                                                            | Source Location               |
| -- | -------------------------------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------------------- | ----------------------------- |
| 59 | Search fields editable, detail protected | CCUP-DETAILS-NOT-FETCHED                                         | ACCTSID and CARDSID = DFHBMFSE (unprotected); CRDNAME, CRDSTCD, EXPMON, EXPYEAR = DFHBMPRF (protected); EXPDAYA attribute line is commented out | 3300-SETUP-SCREEN-ATTRS lines 1173-1180 |
| 60 | Search fields protected after fetch    | CCUP-SHOW-DETAILS or CCUP-CHANGES-NOT-OK                         | ACCTSID and CARDSID = DFHBMPRF; CRDNAME, CRDSTCD, EXPMON, EXPYEAR = DFHBMFSE (editable) | 3300-SETUP-SCREEN-ATTRS lines 1181-1190 |
| 61 | All fields protected on confirmation   | CCUP-CHANGES-OK-NOT-CONFIRMED or CCUP-CHANGES-OKAYED-AND-DONE   | All input fields = DFHBMPRF (read-only while awaiting PF5 or after commit)        | 3300-SETUP-SCREEN-ATTRS lines 1191-1199 |
| 62 | Screen attribute fallback (WHEN OTHER) | WHEN OTHER -- unhandled CCUP-CHANGE-ACTION value                  | ACCTSID and CARDSID = DFHBMFSE; CRDNAME, CRDSTCD, EXPMON, EXPYEAR = DFHBMPRF (same as CCUP-DETAILS-NOT-FETCHED pattern) | 3300-SETUP-SCREEN-ATTRS lines 1200-1207 |
| 63 | Search field error highlighted in red  | FLG-ACCTFILTER-NOT-OK or FLG-CARDFILTER-NOT-OK                  | DFHRED applied to ACCTSIDC or CARDSIDC regardless of CDEMO-PGM-REENTER state      | 3300-SETUP-SCREEN-ATTRS lines 1243-1261 |
| 64 | Search field blank shows asterisk      | FLG-ACCTFILTER-BLANK AND CDEMO-PGM-REENTER (or FLG-CARDFILTER-BLANK AND CDEMO-PGM-REENTER) | '*' moved to ACCTSIDO/CARDSIDO and DFHRED applied; asterisk is suppressed on the very first entry (CDEMO-PGM-ENTER) | 3300-SETUP-SCREEN-ATTRS lines 1247-1261 |
| 65 | Error detail field highlighted in red  | Any FLG-*-NOT-OK or FLG-*-BLANK when CCUP-CHANGES-NOT-OK        | DFHRED applied to the colour attribute of the offending field                     | 3300-SETUP-SCREEN-ATTRS lines 1263-1307 |
| 66 | Blank detail error field shows asterisk| FLG-*-BLANK AND CCUP-CHANGES-NOT-OK (for CRDNAME, CRDSTCD, EXPMON, EXPYEAR) | '*' moved to the output field so user sees a placeholder                     | 3300-SETUP-SCREEN-ATTRS lines 1268-1307 |
| 67 | Expiry day always dark                 | Always                                                            | DFHBMDAR applied to EXPDAYC -- day field is display-only, not user-enterable      | 3300-SETUP-SCREEN-ATTRS line 1285 |
| 68 | Account/card colour reset from list    | CDEMO-LAST-MAPSET = LIT-CCLISTMAPSET ('COCRDLI')                 | DFHDFCOL (default colour) applied to ACCTSIDC and CARDSIDC; prevents any residual red highlight from COCRDLIC appearing on this screen | 3300-SETUP-SCREEN-ATTRS lines 1238-1241 |
| 69 | Info message area brightness           | WS-NO-INFO-MESSAGE (SPACES or LOW-VALUES)                         | DFHBMDAR (dark) applied to INFOMSGA; when there IS an info message DFHBMBRY (bright) is applied instead | 3300-SETUP-SCREEN-ATTRS lines 1309-1313 |
| 70 | F-key highlight on confirmation prompt | PROMPT-FOR-CONFIRMATION                                           | DFHBMBRY applied to FKEYSC (PF key list area highlights to draw attention to PF5) | 3300-SETUP-SCREEN-ATTRS lines 1315-1317 |

### Cursor Positioning (3300-SETUP-SCREEN-ATTRS)

| #  | Rule                                   | Condition                                               | Action                                                                    | Source Location               |
| -- | -------------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------- | ----------------------------- |
| 71 | Cursor to card name after fetch        | FOUND-CARDS-FOR-ACCOUNT or NO-CHANGES-DETECTED          | MOVE -1 TO CRDNAMEL -- cursor positioned at card name field               | 3300-SETUP-SCREEN-ATTRS lines 1212-1214 |
| 72 | Cursor to account field on acct error  | FLG-ACCTFILTER-NOT-OK or FLG-ACCTFILTER-BLANK           | MOVE -1 TO ACCTSIDL                                                       | 3300-SETUP-SCREEN-ATTRS lines 1215-1217 |
| 73 | Cursor to card field on card error     | FLG-CARDFILTER-NOT-OK or FLG-CARDFILTER-BLANK           | MOVE -1 TO CARDSIDL                                                       | 3300-SETUP-SCREEN-ATTRS lines 1218-1220 |
| 74 | Cursor to card name field on name error| FLG-CARDNAME-NOT-OK or FLG-CARDNAME-BLANK               | MOVE -1 TO CRDNAMEL                                                       | 3300-SETUP-SCREEN-ATTRS lines 1221-1223 |
| 75 | Cursor to status field on status error | FLG-CARDSTATUS-NOT-OK or FLG-CARDSTATUS-BLANK           | MOVE -1 TO CRDSTCDL                                                       | 3300-SETUP-SCREEN-ATTRS lines 1224-1226 |
| 76 | Cursor to month field on month error   | FLG-CARDEXPMON-NOT-OK or FLG-CARDEXPMON-BLANK           | MOVE -1 TO EXPMONL                                                        | 3300-SETUP-SCREEN-ATTRS lines 1227-1229 |
| 77 | Cursor to year field on year error     | FLG-CARDEXPYEAR-NOT-OK or FLG-CARDEXPYEAR-BLANK         | MOVE -1 TO EXPYEARL                                                       | 3300-SETUP-SCREEN-ATTRS lines 1230-1232 |
| 78 | Cursor to account field (default)      | WHEN OTHER in cursor EVALUATE                            | MOVE -1 TO ACCTSIDL -- default cursor home is the account number field    | 3300-SETUP-SCREEN-ATTRS lines 1233-1234 |

### Screen Variable Population (3200-SETUP-SCREEN-VARS)

| #  | Rule                                  | Condition                          | Action                                                                                | Source Location                    |
| -- | ------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------- | ---------------------------------- |
| 79 | Skip field population on fresh entry  | CDEMO-PGM-ENTER                    | CONTINUE -- entire field population block skipped; output map fields retain INITIALIZE values | 3200-SETUP-SCREEN-VARS lines 1084-1086 |
| 80 | Zero account/card suppressed on screen| NOT CDEMO-PGM-ENTER AND CC-ACCT-ID-N = 0 or CC-CARD-NUM-N = 0 | LOW-VALUES moved to ACCTSIDO or CARDSIDO rather than the numeric zero value; prevents displaying '00000000000' on screen | 3200-SETUP-SCREEN-VARS lines 1087-1097 |
| 81 | Clear detail fields when no fetch     | CCUP-DETAILS-NOT-FETCHED           | CRDNAMEO, CRDSTCDO, EXPDAYO, EXPMONO, EXPYEARO all set to LOW-VALUES. Note: CRDNAMEO appears twice in the MOVE LOW-VALUES TO statement (lines 1101-1102) -- this is a harmless coding defect (duplicate target); the effective result is the same. | 3200-SETUP-SCREEN-VARS lines 1100-1106 |
| 82 | Populate from OLD values after fetch  | CCUP-SHOW-DETAILS                  | CCUP-OLD-CRDNAME/CRDSTCD/EXPDAY/EXPMON/EXPYEAR moved to respective output fields      | 3200-SETUP-SCREEN-VARS lines 1107-1112 |
| 83 | Populate from NEW values during edit  | CCUP-CHANGES-MADE ('E','N','C','L','F') | CCUP-NEW-CRDNAME/CRDSTCD/EXPMON/EXPYEAR moved to output; CCUP-OLD-EXPDAY always used for EXPDAYO (commented-out line 1122 confirms this is intentional split from write path) | 3200-SETUP-SCREEN-VARS lines 1113-1123 |
| 84 | Default fallback to OLD values        | WHEN OTHER in screen vars EVALUATE | CCUP-OLD-* values moved to all output fields                                          | 3200-SETUP-SCREEN-VARS lines 1124-1130 |

### Information Message Routing (3250-SETUP-INFOMSG)

| #  | Rule                          | State                               | Message displayed (WS-INFO-MSG 88-level VALUE)                                   | Source Location               |
| -- | ----------------------------- | ----------------------------------- | -------------------------------------------------------------------------------- | ----------------------------- |
| 85 | Prompt for search keys (enter)| CDEMO-PGM-ENTER                     | "Please enter Account and Card Number"                                           | 3250-SETUP-INFOMSG line 1141  |
| 86 | Prompt for search keys (state)| CCUP-DETAILS-NOT-FETCHED            | "Please enter Account and Card Number"                                           | 3250-SETUP-INFOMSG line 1143  |
| 87 | Prompt for search keys (empty)| WS-NO-INFO-MESSAGE (SPACES or LOW-VALUES on WS-INFO-MSG) | "Please enter Account and Card Number"                              | 3250-SETUP-INFOMSG lines 1157-1158 |
| 88 | Card found confirmation       | CCUP-SHOW-DETAILS                   | "Details of selected card shown above"                                           | 3250-SETUP-INFOMSG line 1145  |
| 89 | Prompt to correct errors      | CCUP-CHANGES-NOT-OK                 | "Update card details presented above."                                           | 3250-SETUP-INFOMSG line 1147  |
| 90 | Prompt for PF5 confirmation   | CCUP-CHANGES-OK-NOT-CONFIRMED       | "Changes validated.Press F5 to save"                                             | 3250-SETUP-INFOMSG line 1149  |
| 91 | Update success message        | CCUP-CHANGES-OKAYED-AND-DONE        | "Changes committed to database"                                                  | 3250-SETUP-INFOMSG line 1151  |
| 92 | Update lock failure message   | CCUP-CHANGES-OKAYED-LOCK-ERROR      | "Changes unsuccessful. Please try again"                                         | 3250-SETUP-INFOMSG line 1153  |
| 93 | Update write failure message  | CCUP-CHANGES-OKAYED-BUT-FAILED      | "Changes unsuccessful. Please try again"                                         | 3250-SETUP-INFOMSG line 1155  |

### ABEND Handling

| #  | Rule                          | Condition                             | Action                                                                                   | Source Location          |
| -- | ----------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------ |
| 94 | CICS ABEND handler registered | Program entry                         | EXEC CICS HANDLE ABEND LABEL(ABEND-ROUTINE); all CICS abends routed to ABEND-ROUTINE     | 0000-MAIN lines 370-372  |
| 95 | ABEND-ROUTINE execution       | Any CICS abend or explicit PERFORM ABEND-ROUTINE | Move LIT-THISPGM to ABEND-CULPRIT; EXEC CICS SEND FROM(ABEND-DATA) ERASE NOHANDLE; EXEC CICS HANDLE ABEND CANCEL; EXEC CICS ABEND ABCODE('9999') | ABEND-ROUTINE lines 1531-1552 |
| 96 | Default abend message         | ABEND-MSG = LOW-VALUES on entry to ABEND-ROUTINE | Move 'UNEXPECTED ABEND OCCURRED.' to ABEND-MSG                              | ABEND-ROUTINE lines 1533-1535 |

## Calculations

| Calculation          | Formula / Logic                                                                                                     | Input Fields                                          | Output Field                    | Source Location                  |
| -------------------- | ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | ------------------------------- | -------------------------------- |
| Expiry date assembly | STRING CCUP-NEW-EXPYEAR '-' CCUP-NEW-EXPMON '-' CCUP-NEW-EXPDAY DELIMITED BY SIZE                                 | CCUP-NEW-EXPYEAR (PIC X(4)), CCUP-NEW-EXPMON (PIC X(2)), CCUP-NEW-EXPDAY (PIC X(2), received from EXPDAYI -- not normalised for sentinel values) | CARD-UPDATE-EXPIRAION-DATE (PIC X(10)) "YYYY-MM-DD" | 9200-WRITE-PROCESSING lines 1467-1474 |
| Expiry date parsing  | Substring extraction: (1:4) = year, (6:2) = month, (9:2) = day from CARD-EXPIRAION-DATE                           | CARD-EXPIRAION-DATE PIC X(10) in format YYYY-MM-DD   | CCUP-OLD-EXPYEAR, CCUP-OLD-EXPMON, CCUP-OLD-EXPDAY | 9000-READ-DATA lines 1361-1366  |
| Name case conversion on read | INSPECT CARD-EMBOSSED-NAME CONVERTING LIT-LOWER (26 lowercase chars) TO LIT-UPPER (26 uppercase chars)   | CARD-EMBOSSED-NAME (PIC X(50))                        | CARD-EMBOSSED-NAME (in place)   | 9000-READ-DATA lines 1356-1358  |
| Name case conversion on check | INSPECT CARD-EMBOSSED-NAME CONVERTING LIT-LOWER TO LIT-UPPER (in 9300, applied to freshly-locked DB record before comparison) | CARD-EMBOSSED-NAME from READ UPDATE              | CARD-EMBOSSED-NAME (in place)   | 9300-CHECK-CHANGE-IN-REC lines 1499-1501 |
| Name alpha check     | INSPECT CARD-NAME-CHECK CONVERTING LIT-ALL-ALPHA-FROM (52 chars: A-Z + a-z) TO LIT-ALL-SPACES-TO (52 spaces); then FUNCTION LENGTH(FUNCTION TRIM(CARD-NAME-CHECK)) = 0 means all-alpha | CCUP-NEW-CRDNAME copied to CARD-NAME-CHECK (PIC X(50)) | Implicit: zero trim length = valid, non-zero = invalid | 1230-EDIT-NAME lines 823-828 |
| CVV numeric coercion | CCUP-NEW-CVV-CD (PIC X(3)) moved to CARD-CVV-CD-X; then CARD-CVV-CD-N (PIC 9(3) redefine) moved to CARD-UPDATE-CVV-CD (PIC 9(3)) | CCUP-NEW-CVV-CD (user's old CVV, not changed by screen) | CARD-UPDATE-CVV-CD (PIC 9(3))  | 9200-WRITE-PROCESSING lines 1464-1465 |
| Current date formatting | FUNCTION CURRENT-DATE to WS-CURDATE-DATA; year substring WS-CURDATE-YEAR(3:2) extracts 2-digit year for MM/DD/YY display | FUNCTION CURRENT-DATE (returns YYYYMMDD...) | WS-CURDATE-MM-DD-YY (displayed as CURDATEO) | 3100-SCREEN-INIT lines 1055-1068 |

## Error Handling

| Condition                                | Action                                                                                      | Return Code / Message                                              | Source Location                       |
| ---------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ------------------------------------- |
| Account number blank or zero             | INPUT-ERROR; FLG-ACCTFILTER-BLANK                                                           | "Account number not provided"                                      | 1210-EDIT-ACCOUNT lines 725-732       |
| Account number not numeric               | INPUT-ERROR; FLG-ACCTFILTER-NOT-OK                                                          | 'ACCOUNT FILTER,IF SUPPLIED MUST BE A 11 DIGIT NUMBER'             | 1210-EDIT-ACCOUNT lines 740-746       |
| Card number blank or zero                | INPUT-ERROR; FLG-CARDFILTER-BLANK                                                           | "Card number not provided"                                         | 1220-EDIT-CARD lines 768-774          |
| Card number not numeric                  | INPUT-ERROR; FLG-CARDFILTER-NOT-OK                                                          | 'CARD ID FILTER,IF SUPPLIED MUST BE A 16 DIGIT NUMBER'             | 1220-EDIT-CARD lines 784-790          |
| Both search fields blank or zero         | NO-SEARCH-CRITERIA-RECEIVED                                                                 | "No input received"                                                | 1200-EDIT-MAP-INPUTS lines 656-659    |
| Card name blank or zero                  | INPUT-ERROR; FLG-CARDNAME-BLANK                                                             | "Card name not provided"                                           | 1230-EDIT-NAME lines 811-818          |
| Card name contains non-alpha             | INPUT-ERROR; FLG-CARDNAME-NOT-OK                                                            | "Card name can only contain alphabets and spaces"                  | 1230-EDIT-NAME lines 831-834          |
| Card status blank or zero                | INPUT-ERROR; FLG-CARDSTATUS-BLANK                                                           | "Card Active Status must be Y or N"                                | 1240-EDIT-CARDSTATUS lines 850-856    |
| Card status not Y or N                   | INPUT-ERROR; FLG-CARDSTATUS-NOT-OK                                                          | "Card Active Status must be Y or N"                                | 1240-EDIT-CARDSTATUS lines 861-870    |
| Expiry month blank or zero               | INPUT-ERROR; FLG-CARDEXPMON-BLANK                                                           | "Card expiry month must be between 1 and 12"                       | 1250-EDIT-EXPIRY-MON lines 883-891    |
| Expiry month out of range (not 1-12)     | INPUT-ERROR; FLG-CARDEXPMON-NOT-OK                                                          | "Card expiry month must be between 1 and 12"                       | 1250-EDIT-EXPIRY-MON lines 898-906    |
| Expiry year blank or zero                | INPUT-ERROR; FLG-CARDEXPYEAR-BLANK                                                          | "Invalid card expiry year"                                         | 1260-EDIT-EXPIRY-YEAR lines 916-924   |
| Expiry year out of range (not 1950-2099) | INPUT-ERROR; FLG-CARDEXPYEAR-NOT-OK                                                         | "Invalid card expiry year"                                         | 1260-EDIT-EXPIRY-YEAR lines 930-942   |
| Card record NOTFND on read               | INPUT-ERROR; FLG-ACCTFILTER-NOT-OK; FLG-CARDFILTER-NOT-OK (both flags set)                 | "Did not find cards for this search condition"                     | 9100-GETCARD-BYACCTCARD lines 1395-1401 |
| Card file I/O error on read (WHEN OTHER) | INPUT-ERROR; FLG-ACCTFILTER-NOT-OK only (FLG-CARDFILTER-NOT-OK is NOT set); WS-FILE-ERROR-MESSAGE written directly to WS-RETURN-MSG (bypasses WS-RETURN-MSG-OFF guard) | "File Error: READ on CARDDAT  returned RESP nnn ,RESP2 nnn" | 9100-GETCARD-BYACCTCARD lines 1402-1411 |
| Cannot lock record for UPDATE            | INPUT-ERROR; COULD-NOT-LOCK-FOR-UPDATE; abort write path                                    | "Could not lock record for update"                                 | 9200-WRITE-PROCESSING lines 1443-1448 |
| Concurrent modification detected        | DATA-WAS-CHANGED-BEFORE-UPDATE; refresh CCUP-OLD-* from DB; abort write; re-show details   | "Record changed by some one else. Please review"                   | 9300-CHECK-CHANGE-IN-REC lines 1510-1518 |
| REWRITE fails                            | LOCKED-BUT-UPDATE-FAILED                                                                    | "Update of record failed"                                          | 9200-WRITE-PROCESSING lines 1490-1492 |
| Unhandled program state                  | ABEND-CODE '0001'; CICS ABEND ABCODE('9999')                                                | 'UNEXPECTED DATA SCENARIO'                                         | 2000-DECIDE-ACTION lines 1020-1026    |
| Any CICS abend                           | ABEND-ROUTINE: display ABEND-DATA; HANDLE ABEND CANCEL; CICS ABEND ABCODE('9999')          | ABCODE '9999'                                                      | ABEND-ROUTINE lines 1531-1552         |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. 0000-MAIN -- Entry point; initialises CC-WORK-AREA, WS-MISC-STORAGE, WS-COMMAREA; registers CICS ABEND handler
2. YYYY-STORE-PFKEY (CSSTRPFY) -- Maps raw EIBAID to common CCARD-AID-* flag; normalises PF13-PF24 to PF1-PF12. This paragraph is inlined into the PROCEDURE DIVISION via `COPY 'CSSTRPFY'` at line 1528 (quoted-form PROCEDURE DIVISION copy).
3. 0000-MAIN EVALUATE -- Main routing dispatcher; eight branches covering all valid session states; uses GO TO COMMON-RETURN to exit each branch
4. COMMON-RETURN -- Merges CARDDEMO-COMMAREA + WS-THIS-PROGCOMMAREA into WS-COMMAREA (PIC X(2000)); EXEC CICS RETURN TRANSID('CCUP') COMMAREA(WS-COMMAREA) LENGTH; executes after any branch that does not XCTL
5. 1000-PROCESS-INPUTS -- Top-level input processor; called on normal edit path; also sets CCARD-NEXT-PROG/MAPSET/MAP literals
6. 1100-RECEIVE-MAP -- EXEC CICS RECEIVE MAP(LIT-THISMAP='CCRDUPA') MAPSET(LIT-THISMAPSET='COCRDUP ') INTO(CCRDUPAI); normalises '*' and SPACES to LOW-VALUES for all input fields except EXPDAYI
7. 1200-EDIT-MAP-INPUTS -- Validation dispatcher; routes to search-key edits (1210+1220) OR card-data edits (1230+1240+1250+1260) depending on CCUP-DETAILS-NOT-FETCHED state
8. 1210-EDIT-ACCOUNT -- Validates account number: mandatory/non-zero, numeric; sets FLG-ACCTFILTER-*
9. 1220-EDIT-CARD -- Validates card number: mandatory/non-zero, numeric; sets FLG-CARDFILTER-*
10. 1230-EDIT-NAME -- Validates embossed name: mandatory, alphabetic-and-spaces only; sets FLG-CARDNAME-*
11. 1240-EDIT-CARDSTATUS -- Validates active status: mandatory, Y or N only; sets FLG-CARDSTATUS-*
12. 1250-EDIT-EXPIRY-MON -- Validates expiry month: mandatory/non-zero, 1-12; sets FLG-CARDEXPMON-*
13. 1260-EDIT-EXPIRY-YEAR -- Validates expiry year: mandatory/non-zero, 1950-2099; sets FLG-CARDEXPYEAR-*
14. 2000-DECIDE-ACTION -- Decides next program state based on current CCUP-CHANGE-ACTION and input flags; triggers read or write as needed; ABENDs on unhandled state
15. 9000-READ-DATA -- Initialises CCUP-OLD-DETAILS; calls 9100; normalises CARD-EMBOSSED-NAME to uppercase; parses expiry date substrings into CCUP-OLD-EXPYEAR/MON/DAY
16. 9100-GETCARD-BYACCTCARD -- EXEC CICS READ FILE('CARDDAT ') RIDFLD(WS-CARD-RID-CARDNUM) KEYLENGTH(LENGTH OF WS-CARD-RID-CARDNUM) INTO(CARD-RECORD); handles NORMAL / NOTFND / OTHER responses
17. 9200-WRITE-PROCESSING -- READ UPDATE for exclusive lock; calls 9300 for change detection; assembles CARD-UPDATE-RECORD; EXEC CICS REWRITE FILE('CARDDAT ')
18. 9300-CHECK-CHANGE-IN-REC -- Normalises DB name to uppercase; compares six fields (CVV, name, exp year/month/day, status) against CCUP-OLD-* snapshot; refreshes snapshot on mismatch; uses GO TO 9200-WRITE-PROCESSING-EXIT (not its own EXIT paragraph) when concurrent modification detected
19. 3000-SEND-MAP -- Orchestrates all screen preparation sub-paragraphs in sequence
20. 3100-SCREEN-INIT -- Clears output map (MOVE LOW-VALUES TO CCRDUPAO); populates title, transaction ID, program name, current date (MM/DD/YY using 2-digit year WS-CURDATE-YEAR(3:2)) and time (HH:MM:SS)
21. 3200-SETUP-SCREEN-VARS -- Populates output map fields from CCUP-OLD-* or CCUP-NEW-* depending on CCUP-CHANGE-ACTION state; expiry day display always taken from OLD (line 1123); write path uses CCUP-NEW-EXPDAY (line 1471); suppresses zero account/card from display
22. 3250-SETUP-INFOMSG -- Sets WS-INFO-MSG 88-level based on current state; moves to INFOMSGO; moves WS-RETURN-MSG to ERRMSGO
23. 3300-SETUP-SCREEN-ATTRS -- Sets protect/unprotect attributes, error highlighting (DFHRED), asterisk placeholders, cursor position, and info-message brightness for each field
24. 3400-SEND-SCREEN -- EXEC CICS SEND MAP(CCARD-NEXT-MAP) MAPSET(CCARD-NEXT-MAPSET) FROM(CCRDUPAO) CURSOR ERASE FREEKB
25. ABEND-ROUTINE -- Last-resort error handler; populates ABEND-CULPRIT with LIT-THISPGM; issues CICS SEND of ABEND-DATA; cancels HANDLE ABEND; issues CICS ABEND '9999'
