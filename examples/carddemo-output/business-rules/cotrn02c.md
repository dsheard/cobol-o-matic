---
type: business-rules
program: COTRN02C
program_type: online
status: draft
confidence: high
last_pass: 5
calls:
- CSUTLDTC
called_by: []
uses_copybooks:
- COCOM01Y
- COTRN02
- COTTL01Y
- CSDAT01Y
- CSMSG01Y
- CVACT01Y
- CVACT03Y
- CVTRA05Y
reads:
- CCXREF
- CXACAIX
- TRANSACT
writes:
- TRANSACT
db_tables: []
transactions:
- CT02
mq_queues: []
---

# COTRN02C -- Business Rules

## Program Purpose

COTRN02C is a CICS online program that adds a new transaction record to the TRANSACT file in the CardDemo credit card management system. It presents a data-entry screen (map COTRN2A / mapset COTRN02) where the operator enters account or card number, transaction type, category, source, description, amount, dates, and merchant details. The program validates all input fields, looks up the account/card cross-reference, auto-generates the next sequential transaction ID by reading backwards from the end of the TRANSACT file, and writes the new TRAN-RECORD after the operator confirms with 'Y'. PF3 returns to the previous screen, PF4 clears the screen, and PF5 copies the last transaction on file into the input fields.

## Input / Output

| Direction | Resource | Type | Description |
| --------- | -------- | ---- | ----------- |
| IN        | COTRN2A (mapset COTRN02) | CICS BMS Map | Add-transaction data entry screen |
| IN        | CXACAIX  | CICS VSAM (KSDS alternate index) | Account-to-card cross-reference, keyed by account ID |
| IN        | CCXREF   | CICS VSAM (KSDS) | Card-to-account cross-reference, keyed by card number |
| IN/OUT    | TRANSACT | CICS VSAM (KSDS) | Transaction master file -- read for last ID, written with new record |
| IN        | DFHCOMMAREA | CICS COMMAREA | Session state passed from calling program |
| OUT       | COTRN2A (mapset COTRN02) | CICS BMS Map | Screen output: confirmation message, error highlight, cursor placement |
| OUT       | TRANSACT | CICS VSAM WRITE | Newly created TRAN-RECORD |

## Business Rules

### Entry / Session Routing

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 1  | Cold start -- no commarea | `EIBCALEN = 0` | Transfer control (XCTL) to COSGN00C (sign-on screen) | MAIN-PARA line 115-117 |
| 2  | First entry from another program | `NOT CDEMO-PGM-REENTER` (flag is not yet set) | Set re-enter flag; initialise screen to LOW-VALUES; cursor to Account ID field | MAIN-PARA line 120-123 |
| 3  | Pre-selected transaction from calling screen | `CDEMO-CT02-TRN-SELECTED NOT = SPACES AND LOW-VALUES` on first entry | Move selected value to CARDNINI and immediately PERFORM PROCESS-ENTER-KEY before showing the screen | MAIN-PARA line 124-129 |
| 4  | Re-entry after ENTER key | `EIBAID = DFHENTER` | PERFORM PROCESS-ENTER-KEY | MAIN-PARA line 134-135 |
| 5  | Re-entry after PF3 | `EIBAID = DFHPF3` | If CDEMO-FROM-PROGRAM is blank, set destination to COMEN01C; otherwise restore CDEMO-FROM-PROGRAM as destination; then XCTL | MAIN-PARA line 136-143 |
| 6  | Re-entry after PF4 | `EIBAID = DFHPF4` | PERFORM CLEAR-CURRENT-SCREEN (initialise all fields and redisplay) | MAIN-PARA line 144-145 |
| 7  | Re-entry after PF5 | `EIBAID = DFHPF5` | PERFORM COPY-LAST-TRAN-DATA (retrieve last transaction for the resolved card/account and pre-populate fields) | MAIN-PARA line 146-147 |
| 8  | Invalid attention identifier | Any AID other than ENTER, PF3, PF4, PF5 | Set ERR-FLG-ON; display CCDA-MSG-INVALID-KEY; redisplay screen | MAIN-PARA line 148-151 |
| 9  | XCTL safety fallback | `CDEMO-TO-PROGRAM = LOW-VALUES OR SPACES` at time of XCTL | Override destination with 'COSGN00C' before issuing XCTL | RETURN-TO-PREV-SCREEN line 502-504 |
| 10 | Commarea handshake on exit | Unconditional in RETURN-TO-PREV-SCREEN before XCTL | Stamp CDEMO-FROM-TRANID with WS-TRANID ('CT02'), CDEMO-FROM-PROGRAM with WS-PGMNAME ('COTRN02C'), and CDEMO-PGM-CONTEXT with ZEROS so the receiving program knows this program's identity | RETURN-TO-PREV-SCREEN line 505-507 |

### Confirmation Validation

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 11 | Confirm = Y -- proceed to add | `CONFIRMI = 'Y' or 'y'` | PERFORM ADD-TRANSACTION | PROCESS-ENTER-KEY line 169-172 |
| 12 | Confirm = N or blank -- prompt | `CONFIRMI = 'N', 'n', SPACES, or LOW-VALUES` | Set ERR-FLG-ON; message "Confirm to add this transaction..."; cursor to CONFIRML; redisplay | PROCESS-ENTER-KEY line 173-181 |
| 13 | Confirm = invalid value | Any other value in CONFIRMI | Set ERR-FLG-ON; message "Invalid value. Valid values are (Y/N)..."; cursor to CONFIRML; redisplay | PROCESS-ENTER-KEY line 182-187 |

### Key-Field Validation (VALIDATE-INPUT-KEY-FIELDS)

One of account ID or card number must be provided; they are mutually exclusive input paths. Validation stops at the first key error and redisplays the screen before data-field validation is reached.

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 14 | Account ID supplied -- must be numeric | `ACTIDINI NOT = SPACES/LOW-VALUES` AND `ACTIDINI IS NOT NUMERIC` | Set ERR-FLG-ON; message "Account ID must be Numeric..."; cursor to ACTIDINL; redisplay | VALIDATE-INPUT-KEY-FIELDS line 196-203 |
| 15 | Account ID supplied -- look up cross-reference | `ACTIDINI NOT = SPACES/LOW-VALUES` and numeric | Convert to numeric (NUMVAL), store in XREF-ACCT-ID; also write back zero-padded numeric value to ACTIDINI on screen; PERFORM READ-CXACAIX-FILE; move returned XREF-CARD-NUM to CARDNINI | VALIDATE-INPUT-KEY-FIELDS line 204-209 |
| 16 | Card number supplied -- must be numeric | `CARDNINI NOT = SPACES/LOW-VALUES` AND `CARDNINI IS NOT NUMERIC` | Set ERR-FLG-ON; message "Card Number must be Numeric..."; cursor to CARDNINL; redisplay | VALIDATE-INPUT-KEY-FIELDS line 210-217 |
| 17 | Card number supplied -- look up cross-reference | `CARDNINI NOT = SPACES/LOW-VALUES` and numeric | Convert to numeric (NUMVAL), store in XREF-CARD-NUM; also write back zero-padded numeric value to CARDNINI on screen; PERFORM READ-CCXREF-FILE; move returned XREF-ACCT-ID to ACTIDINI | VALIDATE-INPUT-KEY-FIELDS line 218-223 |
| 18 | Neither account ID nor card number supplied | Both ACTIDINI and CARDNINI are SPACES or LOW-VALUES (WHEN OTHER) | Set ERR-FLG-ON; message "Account or Card Number must be entered..."; cursor to ACTIDINL; redisplay | VALIDATE-INPUT-KEY-FIELDS line 224-229 |

### Data-Field Mandatory Presence Validation (VALIDATE-INPUT-DATA-FIELDS -- first EVALUATE block)

If ERR-FLG-ON (i.e., a key-field error was already detected), all data fields are blanked before these checks run, preventing stale screen data from passing validation.

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 19 | Transaction Type Code is mandatory | `TTYPCDI = SPACES OR LOW-VALUES` | Set ERR-FLG-ON; message "Type CD can NOT be empty..."; cursor to TTYPCDL; redisplay | VALIDATE-INPUT-DATA-FIELDS line 252-257 |
| 20 | Transaction Category Code is mandatory | `TCATCDI = SPACES OR LOW-VALUES` | Set ERR-FLG-ON; message "Category CD can NOT be empty..."; cursor to TCATCDL; redisplay | VALIDATE-INPUT-DATA-FIELDS line 258-263 |
| 21 | Transaction Source is mandatory | `TRNSRCI = SPACES OR LOW-VALUES` | Set ERR-FLG-ON; message "Source can NOT be empty..."; cursor to TRNSRCL; redisplay | VALIDATE-INPUT-DATA-FIELDS line 264-269 |
| 22 | Transaction Description is mandatory | `TDESCI = SPACES OR LOW-VALUES` | Set ERR-FLG-ON; message "Description can NOT be empty..."; cursor to TDESCL; redisplay | VALIDATE-INPUT-DATA-FIELDS line 270-275 |
| 23 | Transaction Amount is mandatory | `TRNAMTI = SPACES OR LOW-VALUES` | Set ERR-FLG-ON; message "Amount can NOT be empty..."; cursor to TRNAMTL; redisplay | VALIDATE-INPUT-DATA-FIELDS line 276-281 |
| 24 | Origination Date is mandatory | `TORIGDTI = SPACES OR LOW-VALUES` | Set ERR-FLG-ON; message "Orig Date can NOT be empty..."; cursor to TORIGDTL; redisplay | VALIDATE-INPUT-DATA-FIELDS line 282-287 |
| 25 | Processing Date is mandatory | `TPROCDTI = SPACES OR LOW-VALUES` | Set ERR-FLG-ON; message "Proc Date can NOT be empty..."; cursor to TPROCDTL; redisplay | VALIDATE-INPUT-DATA-FIELDS line 288-293 |
| 26 | Merchant ID is mandatory | `MIDI = SPACES OR LOW-VALUES` | Set ERR-FLG-ON; message "Merchant ID can NOT be empty..."; cursor to MIDL; redisplay | VALIDATE-INPUT-DATA-FIELDS line 294-299 |
| 27 | Merchant Name is mandatory | `MNAMEI = SPACES OR LOW-VALUES` | Set ERR-FLG-ON; message "Merchant Name can NOT be empty..."; cursor to MNAMEL; redisplay | VALIDATE-INPUT-DATA-FIELDS line 300-305 |
| 28 | Merchant City is mandatory | `MCITYI = SPACES OR LOW-VALUES` | Set ERR-FLG-ON; message "Merchant City can NOT be empty..."; cursor to MCITYL; redisplay | VALIDATE-INPUT-DATA-FIELDS line 306-311 |
| 29 | Merchant Zip is mandatory | `MZIPI = SPACES OR LOW-VALUES` | Set ERR-FLG-ON; message "Merchant Zip can NOT be empty..."; cursor to MZIPL; redisplay | VALIDATE-INPUT-DATA-FIELDS line 312-317 |

### Data-Field Format Validation (VALIDATE-INPUT-DATA-FIELDS -- subsequent EVALUATE blocks)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 30 | Transaction Type Code must be numeric | `TTYPCDI IS NOT NUMERIC` | Set ERR-FLG-ON; message "Type CD must be Numeric..."; cursor to TTYPCDL; redisplay | VALIDATE-INPUT-DATA-FIELDS line 323-328 |
| 31 | Transaction Category Code must be numeric | `TCATCDI IS NOT NUMERIC` | Set ERR-FLG-ON; message "Category CD must be Numeric..."; cursor to TCATCDL; redisplay | VALIDATE-INPUT-DATA-FIELDS line 329-334 |
| 32 | Amount format: sign character required | `TRNAMTI(1:1) NOT EQUAL '-' AND '+'` | Set ERR-FLG-ON; message "Amount should be in format -99999999.99"; cursor to TRNAMTL; redisplay | VALIDATE-INPUT-DATA-FIELDS line 340-348 |
| 33 | Amount format: 8 digit integer part must be numeric | `TRNAMTI(2:8) NOT NUMERIC` | Same action as rule 32 | VALIDATE-INPUT-DATA-FIELDS line 341 |
| 34 | Amount format: decimal point at position 10 | `TRNAMTI(10:1) NOT = '.'` | Same action as rule 32 | VALIDATE-INPUT-DATA-FIELDS line 342 |
| 35 | Amount format: 2 decimal digits must be numeric | `TRNAMTI(11:2) IS NOT NUMERIC` | Same action as rule 32 | VALIDATE-INPUT-DATA-FIELDS line 343 |
| 36 | Origination Date format: positions 1-4 must be numeric (YYYY) | `TORIGDTI(1:4) IS NOT NUMERIC` | Set ERR-FLG-ON; message "Orig Date should be in format YYYY-MM-DD"; cursor to TORIGDTL; redisplay | VALIDATE-INPUT-DATA-FIELDS line 354-363 |
| 37 | Origination Date format: position 5 must be '-' | `TORIGDTI(5:1) NOT EQUAL '-'` | Same action as rule 36 | VALIDATE-INPUT-DATA-FIELDS line 355 |
| 38 | Origination Date format: positions 6-7 must be numeric (MM) | `TORIGDTI(6:2) NOT NUMERIC` | Same action as rule 36 | VALIDATE-INPUT-DATA-FIELDS line 356 |
| 39 | Origination Date format: position 8 must be '-' | `TORIGDTI(8:1) NOT EQUAL '-'` | Same action as rule 36 | VALIDATE-INPUT-DATA-FIELDS line 357 |
| 40 | Origination Date format: positions 9-10 must be numeric (DD) | `TORIGDTI(9:2) NOT NUMERIC` | Same action as rule 36 | VALIDATE-INPUT-DATA-FIELDS line 358 |
| 41 | Processing Date format: positions 1-4 must be numeric (YYYY) | `TPROCDTI(1:4) IS NOT NUMERIC` | Set ERR-FLG-ON; message "Proc Date should be in format YYYY-MM-DD"; cursor to TPROCDTL; redisplay | VALIDATE-INPUT-DATA-FIELDS line 369-378 |
| 42 | Processing Date format: position 5 must be '-' | `TPROCDTI(5:1) NOT EQUAL '-'` | Same action as rule 41 | VALIDATE-INPUT-DATA-FIELDS line 370 |
| 43 | Processing Date format: positions 6-7 must be numeric (MM) | `TPROCDTI(6:2) NOT NUMERIC` | Same action as rule 41 | VALIDATE-INPUT-DATA-FIELDS line 371 |
| 44 | Processing Date format: position 8 must be '-' | `TPROCDTI(8:1) NOT EQUAL '-'` | Same action as rule 41 | VALIDATE-INPUT-DATA-FIELDS line 372 |
| 45 | Processing Date format: positions 9-10 must be numeric (DD) | `TPROCDTI(9:2) NOT NUMERIC` | Same action as rule 41 | VALIDATE-INPUT-DATA-FIELDS line 373 |

### Calendar Validation via CSUTLDTC (VALIDATE-INPUT-DATA-FIELDS)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 46 | Origination Date must be a valid calendar date | CALL CSUTLDTC with TORIGDTI and format 'YYYY-MM-DD'; if CSUTLDTC-RESULT-SEV-CD NOT = '0000' AND CSUTLDTC-RESULT-MSG-NUM NOT = '2513' | Set ERR-FLG-ON; message "Orig Date - Not a valid date..."; cursor to TORIGDTL; redisplay | VALIDATE-INPUT-DATA-FIELDS line 389-407 |
| 47 | Processing Date must be a valid calendar date | CALL CSUTLDTC with TPROCDTI and format 'YYYY-MM-DD'; if CSUTLDTC-RESULT-SEV-CD NOT = '0000' AND CSUTLDTC-RESULT-MSG-NUM NOT = '2513' | Set ERR-FLG-ON; message "Proc Date - Not a valid date..."; cursor to TPROCDTL; redisplay | VALIDATE-INPUT-DATA-FIELDS line 409-427 |
| 48 | CSUTLDTC message 2513 is tolerated | `CSUTLDTC-RESULT-MSG-NUM = '2513'` | No error raised -- this specific message number is explicitly suppressed (likely a warning, not a hard error) | VALIDATE-INPUT-DATA-FIELDS line 400, 420 |

### Merchant ID Format Validation

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 49 | Merchant ID must be numeric | `MIDI IS NOT NUMERIC` | Set ERR-FLG-ON; message "Merchant ID must be Numeric..."; cursor to MIDL; redisplay | VALIDATE-INPUT-DATA-FIELDS line 430-436 |

### Transaction ID Generation

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 50 | New transaction ID = last existing ID + 1 | Unconditional at start of ADD-TRANSACTION | Move HIGH-VALUES to TRAN-ID; STARTBR TRANSACT at HIGH-VALUES; READPREV to get the last (highest-key) record; ENDBR; add 1 to numeric copy of TRAN-ID; use as new key | ADD-TRANSACTION line 444-451 |
| 51 | Empty file case | READPREV returns DFHRESP(ENDFILE) | TRAN-ID is set to ZEROS; after +1 the first transaction ID becomes 1 | READPREV-TRANSACT-FILE line 688-689 |

### Transaction Record Field Mapping (ADD-TRANSACTION)

All screen input fields are mapped directly to TRAN-RECORD fields before the write. There is no server-side enrichment beyond the auto-generated TRAN-ID and the resolved card number.

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 56 | Card number always stored from CARDNINI | Unconditional after key validation | TRAN-CARD-NUM receives CARDNINI, which holds either the operator-entered card number or the card number resolved from the account-ID cross-reference lookup | ADD-TRANSACTION line 459 |
| 57 | Date fields stored as 10-char strings, not timestamps | Unconditional | TORIGDTI and TPROCDTI (10-char YYYY-MM-DD strings) are moved directly into TRAN-ORIG-TS and TRAN-PROC-TS. Despite the "-TS" (timestamp) suffix on the record fields, only the 10-character date portion is populated; no time component is appended | ADD-TRANSACTION line 464-465 |

### Transaction Write Outcome

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 52 | Successful write | `DFHRESP(NORMAL)` after EXEC CICS WRITE | INITIALIZE-ALL-FIELDS (clear screen); display success message in green: "Transaction added successfully. Your Tran ID is \<id\>." | WRITE-TRANSACT-FILE line 724-734 |
| 53 | Duplicate key on write | `DFHRESP(DUPKEY)` or `DFHRESP(DUPREC)` | Set ERR-FLG-ON; message "Tran ID already exist..."; cursor to ACTIDINL; redisplay | WRITE-TRANSACT-FILE line 735-741 |

### Copy Last Transaction (PF5)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 54 | PF5 copies last transaction fields from file | `NOT ERR-FLG-ON` after key-field validation and READPREV | Populate TTYPCDI, TCATCDI, TRNSRCI, TRNAMTI (via WS-TRAN-AMT-E edit), TDESCI, TORIGDTI, TPROCDTI, MIDI, MNAMEI, MCITYI, MZIPI from TRAN-RECORD read; then PERFORM PROCESS-ENTER-KEY to revalidate | COPY-LAST-TRAN-DATA line 480-495 |
| 55 | PF5 with key-field error -- STARTBR/READPREV still execute | `ERR-FLG-ON` after VALIDATE-INPUT-KEY-FIELDS | STARTBR-TRANSACT-FILE, READPREV-TRANSACT-FILE, and ENDBR-TRANSACT-FILE at lines 475-478 run unconditionally regardless of ERR-FLG-ON; only the field-population block (lines 480-493) is conditioned on `NOT ERR-FLG-ON`. This means a browse of TRANSACT is always performed on PF5, even when the account/card key is invalid. | COPY-LAST-TRAN-DATA line 473-495 |

## Calculations

| Calculation | Formula / Logic | Input Fields | Output Field | Source Location |
| ----------- | --------------- | ------------ | ------------ | --------------- |
| Account ID numeric conversion | `COMPUTE WS-ACCT-ID-N = FUNCTION NUMVAL(ACTIDINI OF COTRN2AI)`. Result also written back to ACTIDINI, normalising the screen value to zero-padded numeric form before the cross-reference lookup overwrites it with the resolved card number. | ACTIDINI (screen input, PIC X) | WS-ACCT-ID-N (PIC 9(11)); ACTIDINI on screen | VALIDATE-INPUT-KEY-FIELDS line 204-207 |
| Card number numeric conversion | `COMPUTE WS-CARD-NUM-N = FUNCTION NUMVAL(CARDNINI OF COTRN2AI)`. Result also written back to CARDNINI, normalising the screen value before the resolved account ID overwrites it. | CARDNINI (screen input, PIC X) | WS-CARD-NUM-N (PIC 9(16)); CARDNINI on screen | VALIDATE-INPUT-KEY-FIELDS line 218-221 |
| Amount numeric conversion (validation) | `COMPUTE WS-TRAN-AMT-N = FUNCTION NUMVAL-C(TRNAMTI OF COTRN2AI)` then move to edited field WS-TRAN-AMT-E and back to screen. This normalises the display format. Reached only when all preceding presence and format checks passed (each failing check exits via EXEC CICS RETURN). | TRNAMTI (PIC X, signed decimal string) | WS-TRAN-AMT-N (PIC S9(9)V99), WS-TRAN-AMT-E (PIC +99999999.99) | VALIDATE-INPUT-DATA-FIELDS line 383-386 |
| Amount numeric conversion (write) | `COMPUTE WS-TRAN-AMT-N = FUNCTION NUMVAL-C(TRNAMTI OF COTRN2AI)` | TRNAMTI (screen input) | WS-TRAN-AMT-N then TRAN-AMT (PIC S9(09)V99) | ADD-TRANSACTION line 456-458 |
| Next transaction ID | `ADD 1 TO WS-TRAN-ID-N` after reading last TRAN-ID from file as numeric | TRAN-ID (PIC X(16) from last READPREV) | WS-TRAN-ID-N (PIC 9(16)), then new TRAN-ID | ADD-TRANSACTION line 448-451 |
| Display date formatting | Extract month, day, 2-digit year from FUNCTION CURRENT-DATE result for screen header | WS-CURDATE-DATA | WS-CURDATE-MM-DD-YY -> CURDATEO | POPULATE-HEADER-INFO line 561-565 |
| Display time formatting | Extract hours, minutes, seconds from FUNCTION CURRENT-DATE result for screen header | WS-CURDATE-DATA | WS-CURTIME-HH-MM-SS -> CURTIMEO | POPULATE-HEADER-INFO line 567-571 |

## Error Handling

| Condition | Action | Return Code | Source Location |
| --------- | ------ | ----------- | --------------- |
| CXACAIX READ -- record not found | Set ERR-FLG-ON; message "Account ID NOT found..."; cursor to ACTIDINL; PERFORM SEND-TRNADD-SCREEN | DFHRESP(NOTFND) | READ-CXACAIX-FILE line 591-596 |
| CXACAIX READ -- unexpected error | DISPLAY 'RESP:' WS-RESP-CD 'REAS:' WS-REAS-CD; set ERR-FLG-ON; message "Unable to lookup Acct in XREF AIX file..."; cursor to ACTIDINL; redisplay | DFHRESP(OTHER) | READ-CXACAIX-FILE line 597-603 |
| CCXREF READ -- record not found | Set ERR-FLG-ON; message "Card Number NOT found..."; cursor to CARDNINL; redisplay | DFHRESP(NOTFND) | READ-CCXREF-FILE line 624-629 |
| CCXREF READ -- unexpected error | DISPLAY 'RESP:' WS-RESP-CD 'REAS:' WS-REAS-CD; set ERR-FLG-ON; message "Unable to lookup Card # in XREF file..."; cursor to CARDNINL; redisplay | DFHRESP(OTHER) | READ-CCXREF-FILE line 630-636 |
| TRANSACT STARTBR -- file empty (NOTFND at HIGH-VALUES) | Set ERR-FLG-ON; message "Transaction ID NOT found..."; cursor to ACTIDINL; redisplay. NOTE: STARTBR at HIGH-VALUES on a non-empty KSDS positions at end-of-file (NORMAL); NOTFND here effectively means the file contains no records at all. | DFHRESP(NOTFND) | STARTBR-TRANSACT-FILE line 655-660 |
| TRANSACT STARTBR -- unexpected error | DISPLAY 'RESP:' WS-RESP-CD 'REAS:' WS-REAS-CD; set ERR-FLG-ON; message "Unable to lookup Transaction..."; cursor to ACTIDINL; redisplay | DFHRESP(OTHER) | STARTBR-TRANSACT-FILE line 661-667 |
| TRANSACT READPREV -- end of file | Set TRAN-ID = ZEROS (file is empty; first ID will be 1) | DFHRESP(ENDFILE) | READPREV-TRANSACT-FILE line 688-689 |
| TRANSACT READPREV -- unexpected error | DISPLAY 'RESP:' WS-RESP-CD 'REAS:' WS-REAS-CD; set ERR-FLG-ON; message "Unable to lookup Transaction..."; cursor to ACTIDINL; redisplay | DFHRESP(OTHER) | READPREV-TRANSACT-FILE line 690-696 |
| TRANSACT WRITE -- duplicate key | Set ERR-FLG-ON; message "Tran ID already exist..."; cursor to ACTIDINL; redisplay | DFHRESP(DUPKEY) / DFHRESP(DUPREC) | WRITE-TRANSACT-FILE line 735-741 |
| TRANSACT WRITE -- unexpected error | DISPLAY 'RESP:' WS-RESP-CD 'REAS:' WS-REAS-CD; set ERR-FLG-ON; message "Unable to Add Transaction..."; cursor to ACTIDINL; redisplay | DFHRESP(OTHER) | WRITE-TRANSACT-FILE line 742-748 |
| CSUTLDTC Orig Date invalid calendar date | Set ERR-FLG-ON; message "Orig Date - Not a valid date..."; cursor to TORIGDTL; redisplay | CSUTLDTC-RESULT-SEV-CD != '0000' AND MSG-NUM != '2513' | VALIDATE-INPUT-DATA-FIELDS line 397-406 |
| CSUTLDTC Proc Date invalid calendar date | Set ERR-FLG-ON; message "Proc Date - Not a valid date..."; cursor to TPROCDTL; redisplay | CSUTLDTC-RESULT-SEV-CD != '0000' AND MSG-NUM != '2513' | VALIDATE-INPUT-DATA-FIELDS line 417-426 |
| ENDBR-TRANSACT-FILE -- no error handling | EXEC CICS ENDBR has no RESP parameter; any CICS error from ENDBR is silently absorbed | None trapped | ENDBR-TRANSACT-FILE line 704-706 |
| RECEIVE-TRNADD-SCREEN -- no error check | EXEC CICS RECEIVE captures RESP/RESP2 into WS-RESP-CD/WS-REAS-CD but the values are never evaluated; MAPFAIL or other receive errors are silently ignored | None checked | RECEIVE-TRNADD-SCREEN line 541-547 |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. MAIN-PARA -- entry point; checks EIBCALEN, loads commarea, dispatches on first-entry vs re-entry and on EIBAID value
2. RETURN-TO-PREV-SCREEN -- stamps commarea (CDEMO-FROM-TRANID='CT02', CDEMO-FROM-PROGRAM='COTRN02C', CDEMO-PGM-CONTEXT=ZEROS); defaults CDEMO-TO-PROGRAM to 'COSGN00C' if blank; then EXEC CICS XCTL to CDEMO-TO-PROGRAM -- exits the program
3. RECEIVE-TRNADD-SCREEN -- EXEC CICS RECEIVE MAP COTRN2A INTO COTRN2AI -- reads operator input
4. PROCESS-ENTER-KEY -- orchestrates all validation and the add operation:
   a. VALIDATE-INPUT-KEY-FIELDS -- validates account ID or card number; performs cross-reference lookup
   b. VALIDATE-INPUT-DATA-FIELDS -- validates all 11 data fields for presence, then numeric/format rules, then calls CSUTLDTC twice for calendar validation; formats amount
   c. EVALUATE CONFIRMI -- branches to ADD-TRANSACTION (Y/y) or prompts/errors (N/n/blank/other)
5. ADD-TRANSACTION -- generates next transaction ID and writes record:
   a. STARTBR-TRANSACT-FILE -- positions browse at HIGH-VALUES (end of file)
   b. READPREV-TRANSACT-FILE -- reads last record to obtain current maximum TRAN-ID
   c. ENDBR-TRANSACT-FILE -- closes browse (no error handling on ENDBR)
   d. Increments TRAN-ID by 1, initialises TRAN-RECORD, maps all screen fields to record fields
   e. WRITE-TRANSACT-FILE -- EXEC CICS WRITE; on success clears screen and displays success message with new TRAN-ID
6. COPY-LAST-TRAN-DATA (PF5) -- validates key fields; then unconditionally performs STARTBR/READPREV/ENDBR to read last transaction; if `NOT ERR-FLG-ON` populates screen data fields; then calls PROCESS-ENTER-KEY
7. CLEAR-CURRENT-SCREEN (PF4) -- INITIALIZE-ALL-FIELDS then SEND-TRNADD-SCREEN
8. SEND-TRNADD-SCREEN -- POPULATE-HEADER-INFO (date/time/titles), EXEC CICS SEND MAP COTRN2A ERASE; then EXEC CICS RETURN TRANSID(CT02) -- suspends and returns control to CICS with transaction CT02
9. EXEC CICS RETURN TRANSID(CT02) COMMAREA(CARDDEMO-COMMAREA) at end of MAIN-PARA -- normal pseudo-conversational return

**Note on validation sequencing:** The two VALIDATE paragraphs are always called in sequence before the CONFIRMI check. However, the first key-field error encountered causes an immediate SEND-TRNADD-SCREEN (which itself does EXEC CICS RETURN), so subsequent validation logic is never reached for a given interaction. This means the EVALUATE in VALIDATE-INPUT-DATA-FIELDS checking for blank fields is effectively unreachable when ERR-FLG-ON is already set from a key-field error, except that the blank-clearing of data fields at lines 237-249 still executes before the EVALUATE to clean the screen.

**Note on PF5 STARTBR always executes:** In COPY-LAST-TRAN-DATA, the STARTBR-TRANSACT-FILE / READPREV-TRANSACT-FILE / ENDBR-TRANSACT-FILE sequence at lines 475-478 runs unconditionally -- before the `IF NOT ERR-FLG-ON` guard at line 480. If key-field validation already set ERR-FLG-ON (e.g., invalid account), the browse of TRANSACT still executes. This is an unnecessary file I/O when the key is invalid, but is functionally harmless because the READPREV result is discarded in that code path.

**Note on amount normalisation reachability:** The `COMPUTE WS-TRAN-AMT-N = FUNCTION NUMVAL-C(TRNAMTI)` at line 383 followed by reformatting at lines 385-386 appears unconditional within VALIDATE-INPUT-DATA-FIELDS. However, every WHEN clause in the five preceding EVALUATE blocks calls SEND-TRNADD-SCREEN, which issues EXEC CICS RETURN and terminates the task. Line 383 is therefore only reached when every preceding EVALUATE took the WHEN OTHER / CONTINUE path -- meaning all presence and format checks passed and ERR-FLG-ON is still off. The computation is not reached in error cases despite lacking an explicit ERR-FLG guard.

**Note on TRAN-ORIG-TS / TRAN-PROC-TS field name mismatch:** The TRAN-RECORD fields are named with a "-TS" suffix implying timestamps, but the program populates them from TORIGDTI and TPROCDTI, which are 10-character date strings in YYYY-MM-DD format. No time component is added. Any consuming program that expects full ISO timestamps in these fields will receive only the date portion.

**Note on dead code -- WS-ACCTDAT-FILE:** WORKING-STORAGE defines `WS-ACCTDAT-FILE PIC X(08) VALUE 'ACCTDAT '` but this variable is never referenced anywhere in the PROCEDURE DIVISION. The ACCTDAT file is not accessed by this program.

**Note on dead code -- WS-TRAN-AMT and WS-TRAN-DATE:** WORKING-STORAGE defines `WS-TRAN-AMT PIC +99999999.99` (line 53) and `WS-TRAN-DATE PIC X(08) VALUE '00/00/00'` (line 54). Neither variable is referenced anywhere in the PROCEDURE DIVISION. The program uses WS-TRAN-AMT-E (PIC +99999999.99, line 59) and WS-TRAN-AMT-N for amount handling; WS-TRAN-DATE has no functional purpose in this program.
