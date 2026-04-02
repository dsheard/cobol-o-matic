---
type: business-rules
program: BNK1TFN
program_type: online
status: draft
confidence: high
last_pass: 5
calls: []
called_by: []
uses_copybooks:
- ABNDINFO
- BNK1TFM
- DFHAID
reads: []
writes: []
db_tables: []
transactions:
- OTFN
mq_queues: []
---

# BNK1TFN -- Business Rules

## Program Purpose

BNK1TFN is the CICS BMS online program for transferring funds between two accounts within the same bank. It presents the transfer funds screen (map BNK1TF from mapset BNK1TFM), receives and validates user input (FROM account number, TO account number, and transfer amount), then delegates the actual transfer to the back-end program XFRFUN via EXEC CICS LINK. On return it displays updated balances (actual and available) for both accounts, or an appropriate error message if the transfer failed. The transaction ID for pseudo-conversational return is OTFN.

Note: the `calls` frontmatter field is intentionally empty because it tracks `CALL` statements only. XFRFUN and ABNDPROC are invoked via EXEC CICS LINK (not a COBOL CALL), which is documented in the Input/Output and Error Handling sections below.

## Input / Output

| Direction | Resource  | Type | Description                                                    |
| --------- | --------- | ---- | -------------------------------------------------------------- |
| IN        | BNK1TF    | CICS | BMS map (mapset BNK1TFM) -- receives FROM account no, TO account no, amount |
| OUT       | BNK1TF    | CICS | BMS map (mapset BNK1TFM) -- displays balances, sort codes, and result message |
| OUT       | COMMAREA  | CICS | 29-byte pseudo-conversational commarea passed to EXEC CICS RETURN TRANSID(OTFN); fields WS-COMMAREA-FACCNO/TACCNO/AMT are never populated -- commarea is always zeros; its sole purpose is to make EIBCALEN > 0 on subsequent invocations |
| OUT       | XFRFUN    | CICS | EXEC CICS LINK to transfer-processing back-end; passes SUBPGM-PARMS commarea (GCD010 line 496) |
| OUT       | ABNDPROC  | CICS | EXEC CICS LINK to abend-handler on any CICS failure; invoked via WS-ABEND-PGM VALUE 'ABNDPROC' (line 160) |

## Business Rules

### Keyboard / AID Routing

| #  | Rule                       | Condition                            | Action                                                                 | Source Location |
| -- | -------------------------- | ------------------------------------ | ---------------------------------------------------------------------- | --------------- |
| 1  | First-time invocation      | EIBCALEN = ZERO                      | Clear map output area (LOW-VALUE to BNK1TFO), set SEND-ERASE flag, PERFORM SEND-MAP | A010 |
| 2  | PA key pressed             | EIBAID = DFHPA1 OR DFHPA2 OR DFHPA3 | CONTINUE (no action, fall through to EXEC CICS RETURN TRANSID(OTFN))  | A010 |
| 3  | PF3 pressed -- return to menu | EIBAID = DFHPF3                   | EXEC CICS RETURN TRANSID('OMEN') IMMEDIATE                             | A010 |
| 4  | AID or PF12 pressed -- end session | EIBAID = DFHAID OR DFHPF12  | PERFORM SEND-TERMINATION-MSG, then EXEC CICS RETURN (no transid -- ends task) | A010 |
| 5  | CLEAR pressed              | EIBAID = DFHCLEAR                    | EXEC CICS SEND CONTROL ERASE FREEKB, then EXEC CICS RETURN             | A010 |
| 6  | ENTER pressed -- process   | EIBAID = DFHENTER                    | PERFORM PROCESS-MAP (receive, validate, transfer, display)             | A010 |
| 7  | Any other key              | WHEN OTHER                           | Move LOW-VALUES to BNK1TFO, move 'Invalid key pressed.' to MESSAGEO, set SEND-DATAONLY-ALARM, PERFORM SEND-MAP | A010 |

### Input Validation (EDIT-DATA / ED010)

| #  | Rule                              | Condition                                       | Action                                                                        | Source Location |
| -- | --------------------------------- | ----------------------------------------------- | ----------------------------------------------------------------------------- | --------------- |
| 8  | FROM account number must be numeric | EXEC CICS BIF DEEDIT on FACCNOI; then IF FACCNOI NOT NUMERIC | Move 'Please enter a FROM account no  ' to MESSAGEO; set VALID-DATA-SW = 'N'; GO TO ED999 | ED010 |
| 9  | TO account number must be numeric | EXEC CICS BIF DEEDIT on TACCNOI; then IF TACCNOI NOT NUMERIC | Move 'Please enter a TO account no    ' to MESSAGEO; set VALID-DATA-SW = 'N'; GO TO ED999 | ED010 |
| 10 | FROM and TO accounts must differ  | IF FACCNOI = TACCNOI                            | Move 'The FROM & TO account should be different ' to MESSAGEO; set VALID-DATA-SW = 'N'; GO TO ED999 | ED010 |
| 11 | Account number 00000000 is not valid | IF FACCNOI = '00000000' OR TACCNOI = '00000000' | Move 'Account no 00000000 is not valid          ' to MESSAGEO; set VALID-DATA-SW = 'N'; GO TO ED999 | ED010 |
| 12 | Amount field must be validated    | Reached only if above rules all pass            | PERFORM VALIDATE-AMOUNT                                                       | ED010           |

### Amount Validation (VALIDATE-AMOUNT SECTION / VA010)

The VALIDATE-AMOUNT paragraph is the entry point of the `VALIDATE-AMOUNT SECTION` (line 988). It is invoked by `PERFORM VALIDATE-AMOUNT` from ED010. The section provides two paths: a fast path for purely numeric input (no decimal point), and a full character-by-character analysis path for input containing a decimal point.

| #  | Rule                                        | Condition                                                           | Action                                                                                    | Source Location |
| -- | ------------------------------------------- | ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | --------------- |
| 13 | Amount field must not be empty              | IF AMTL = ZERO                                                      | Move 'The Amount entered must be numeric.' to MESSAGEO; VALID-DATA-SW = 'N'; AMTL = -1; GO TO VA999 | VA010 (line 994) |
| 14 | If amount field is purely numeric, convert  | IF AMTI(1:AMTL) IS NUMERIC                                          | COMPUTE WS-AMOUNT-AS-FLOAT = FUNCTION NUMVAL(AMTI(1:AMTL)); proceed to positivity check  | VA010 (line 1002) |
| 15 | Numeric amount must be positive (fast path) | WS-AMOUNT-AS-FLOAT <= 0 (within the NUMERIC branch)                 | Move 'Please supply a positive amount.' to MESSAGEO; VALID-DATA-SW = 'N'; AMTL = -1; GO TO VA999 | VA010 (line 1009) |
| 16 | Amount must not be entirely spaces          | IF WS-NUM-COUNT-TOTAL (INSPECT leading spaces) = AMTL               | Move 'The Amount entered must be numeric.' to MESSAGEO; VALID-DATA-SW = 'N'; AMTL = -1; GO TO VA999 | VA010 (line 1029) |
| 17 | Negative amounts are rejected               | IF WS-NUM-COUNT-MINUS > 0 (any '-' character found)                 | Move 'Please supply a positive amount.' to MESSAGEO; VALID-DATA-SW = 'N'; AMTL = -1; GO TO VA999 | VA010 (line 1086) |
| 18 | Embedded spaces in amount are rejected      | IF WS-NUM-COUNT-SPACE > 0                                           | Move 'Please supply a numeric amount without embedded  spaces.' to MESSAGEO; VALID-DATA-SW = 'N'; AMTL = -1; GO TO VA999 | VA010 (line 1103) |
| 19 | All characters must be digit or decimal     | IF WS-NUM-COUNT-TOTAL (digits + '.') < WS-AMOUNT-UNSTR-L           | Move 'Please supply a numeric amount.' to MESSAGEO; VALID-DATA-SW = 'N'; AMTL = -1; GO TO VA999 | VA010 (line 1115) |
| 20 | At most one decimal point allowed           | IF WS-NUM-COUNT-POINT > 1                                           | Move 'Use one decimal point for amount only.' to MESSAGEO; VALID-DATA-SW = 'N'; AMTL = -1; GO TO VA999 | VA010 (line 1133) |
| 21 | At most two decimal places allowed          | IF WS-NUM-COUNT-POINT = 1 AND digits after '.' > 2; the check re-calculates the decimal position by counting characters before '.', adds 2, then re-counts numeric digits after the new offset; only rejects if re-counted total > 2 | Move 'Only up to two decimal places are supported.' to MESSAGEO; VALID-DATA-SW = 'N'; AMTL = -1; GO TO VA999 | VA010 (lines 1145-1186) |
| 22 | Amount must be non-zero (final check)       | IF WS-AMOUNT-AS-FLOAT = ZERO (after NUMVAL conversion)              | Move 'Please supply a non-zero amount.' to MESSAGEO; VALID-DATA-SW = 'N'; AMTL = -1; GO TO VA999 | VA010 (line 1193) |

### Transfer Result Handling (GET-ACC-DATA / GCD010)

| #  | Rule                                     | Condition                                              | Action                                                                                       | Source Location |
| -- | ---------------------------------------- | ------------------------------------------------------ | -------------------------------------------------------------------------------------------- | --------------- |
| 23 | FROM account not found in XFRFUN         | SUBPGM-SUCCESS = 'N' AND SUBPGM-FAIL-CODE = '1'       | Move 'Sorry the FROM ACCOUNT no was not found. Transfer not applied. ' to MESSAGEO; GO TO GCD999 | GCD010 (line 587) |
| 24 | TO account not found in XFRFUN           | SUBPGM-SUCCESS = 'N' AND SUBPGM-FAIL-CODE = '2'       | Move 'Sorry the TO ACCOUNT no was not found. Transfer not applied. ' to MESSAGEO; GO TO GCD999 | GCD010 (line 595) |
| 25 | Transfer failed due to unexpected error (DEFECTIVE -- message is overwritten) | SUBPGM-SUCCESS = 'N' AND SUBPGM-FAIL-CODE = '3'  | Sets MESSAGEO to 'Sorry but the transfer could not be applied due to an unexpected error.' but unlike fail-codes 1, 2, 4, and OTHER there is NO GO TO GCD999 here; execution falls through to the `IF SUBPGM-SUCCESS NOT = 'Y'` check (line 629) which overwrites MESSAGEO with 'unable to determine success'. The "unexpected error" message is never actually displayed. | GCD010 (lines 603-608) |
| 26 | Amount was zero (rejected by XFRFUN)     | SUBPGM-SUCCESS = 'N' AND SUBPGM-FAIL-CODE = '4'       | Move 'Please supply an amount greater than zero.' to MESSAGEO; GO TO GCD999                  | GCD010 (line 610) |
| 27 | Transfer failed for any other reason     | SUBPGM-SUCCESS = 'N' AND SUBPGM-FAIL-CODE = OTHER     | Move 'Sorry but the transfer could not be applied due to an error.' to MESSAGEO; GO TO GCD999 | GCD010 (line 617) |
| 28 | Success status indeterminate (also triggered by fail-code 3 fallthrough) | SUBPGM-SUCCESS NOT = 'Y' after EVALUATE END-EVALUATE | Move 'Sorry but the transfer could not be applied unable to determine success.' to MESSAGEO; GO TO GCD999. This condition fires for fail-code '3' as well as genuinely indeterminate states because fail-code '3' has no GO TO (see rule 25). | GCD010 (line 629) |
| 29 | Transfer succeeded                       | SUBPGM-SUCCESS = 'Y'                                   | Move 'Transfer successfully applied.             ' to MESSAGEO; display updated balances      | GCD010 (line 638) |
| 34 | XFRFUN error downgrades VALID-DATA-SW    | SUBPGM-SUCCESS = 'N' (any fail-code)                   | MOVE 'N' TO VALID-DATA-SW (line 584) -- GCD010 explicitly resets the validation flag to 'N' on any transfer failure, so SM010 will send with ALARM regardless of what ED010/VA010 previously set | GCD010 (line 584) |

### Data Flow to XFRFUN

| #  | Rule                                      | Condition | Action                                                                                       | Source Location |
| -- | ----------------------------------------- | --------- | -------------------------------------------------------------------------------------------- | --------------- |
| 30 | Pack parameters before LINK to XFRFUN     | Always    | INITIALIZE SUBPGM-PARMS; MOVE FACCNOI TO SUBPGM-FACCNO; MOVE TACCNOI TO SUBPGM-TACCNO; MOVE 'N' TO SUBPGM-SUCCESS; MOVE WS-AMOUNT-AS-FLOAT TO SUBPGM-AMT | GCD010 (lines 485-494) |
| 31 | SYNCONRETURN used on LINK to XFRFUN       | Always    | EXEC CICS LINK PROGRAM('XFRFUN') SYNCONRETURN -- ensures syncpoint on return, protecting integrity of the transfer | GCD010 (line 501) |
| 32 | Balances zeroed before result evaluation  | Always, immediately after LINK returns | Zero out all four display balance fields (FROM-ACTUAL, FROM-AVAILABLE, TO-ACTUAL, TO-AVAILABLE) and move zeros to screen output fields FACTBALO, FAVBALO, TACTBALO, TAVBALO before evaluating SUBPGM-SUCCESS; on error paths these zero values remain on screen | GCD010 (lines 570-577) |
| 33 | Account and sort code mapped twice on success | SUBPGM-SUCCESS = 'Y' only | SUBPGM-FACCNO/FSCODE/TACCNO/TSCODE are moved to screen output at lines 566-569 (before success check) and again at lines 645-648 (after success confirmed); the second MOVE is redundant | GCD010 (lines 566-569 and 645-648) |

### Send-Map Mutual Exclusion (SEND-MAP / SM010)

| #  | Rule                                        | Condition                  | Action                                                                                        | Source Location |
| -- | ------------------------------------------- | -------------------------- | --------------------------------------------------------------------------------------------- | --------------- |
| 35 | SEND-ERASE exits SM010 after transmission   | SEND-ERASE = TRUE          | After EXEC CICS SEND MAP ... ERASE, GO TO SM999 unconditionally (line 740); the SEND-DATAONLY and SEND-DATAONLY-ALARM blocks are therefore never evaluated when SEND-ERASE is set | SM010 (line 740) |
| 36 | SEND-DATAONLY exits SM010 after transmission | SEND-DATAONLY = TRUE       | After EXEC CICS SEND MAP ... DATAONLY, GO TO SM999 unconditionally (line 815); the SEND-DATAONLY-ALARM block is therefore never evaluated when SEND-DATAONLY is set | SM010 (line 815) |
| 37 | SEND-DATAONLY-ALARM falls through to SM999  | SEND-DATAONLY-ALARM = TRUE | No GO TO after this block; execution falls naturally to SM999; this is the last evaluated branch | SM010 (line 821-891) |

## Calculations

| Calculation                    | Formula / Logic                                                                                        | Input Fields                              | Output Field           | Source Location      |
| ------------------------------ | ------------------------------------------------------------------------------------------------------ | ----------------------------------------- | ---------------------- | -------------------- |
| Amount conversion (fast path)  | WS-AMOUNT-AS-FLOAT = FUNCTION NUMVAL(AMTI(1:AMTL)) when AMTI is purely numeric; sets VALID-DATA-SW='Y' and exits VA010 immediately; note this fast path also bypasses the MOVE SPACES TO MESSAGEO at line 1203 | AMTI (screen input), AMTL (field length)  | WS-AMOUNT-AS-FLOAT     | VA010 (line 1006)    |
| Trim leading spaces from amount | WS-AMOUNT-UNSTR-L = AMTL - WS-NUM-COUNT-TOTAL (leading spaces); strip via UNSTRING starting at offset WS-NUM-COUNT-TOTAL+1 | AMTI, AMTL, WS-NUM-COUNT-TOTAL            | WS-AMOUNT-UNSTR, WS-AMOUNT-UNSTR-L | VA010 (lines 1037-1048) |
| Trim trailing spaces from amount | Reverse WS-AMOUNT-UNSTR into WS-AMOUNT-UNSTR-REVERSE; INSPECT for leading spaces; SUBTRACT trailing-space count from WS-AMOUNT-UNSTR-L | WS-AMOUNT-UNSTR, WS-AMOUNT-UNSTR-L | WS-AMOUNT-UNSTR-L      | VA010 (lines 1053-1061) |
| Decimal-place count            | INSPECT WS-AMOUNT-UNSTR(1:WS-AMOUNT-UNSTR-L) TALLYING WS-NUM-COUNT-TOTAL FOR ALL '0'-'9' and '.'; if count > 2: find decimal position (characters before '.'), add 2, then re-count digits after that offset; reject if second count > 2 | WS-AMOUNT-UNSTR, WS-AMOUNT-UNSTR-L | WS-NUM-COUNT-POINT, WS-NUM-COUNT-TOTAL | VA010 (lines 1128-1187) |
| Amount conversion (general path) | WS-AMOUNT-AS-FLOAT = FUNCTION NUMVAL(WS-AMOUNT-UNSTR(1:WS-AMOUNT-UNSTR-L)) after full format validation | WS-AMOUNT-UNSTR, WS-AMOUNT-UNSTR-L      | WS-AMOUNT-AS-FLOAT     | VA010 (line 1190)    |
| Balance display formatting     | Each of SUBPGM-FACTBAL/FAVBAL/TACTBAL/TAVBAL (PIC S9(10)V99) moved to display picture PIC +9(10).99 before writing to screen output fields | SUBPGM-FACTBAL, SUBPGM-FAVBAL, SUBPGM-TACTBAL, SUBPGM-TAVBAL | FROM-ACTUAL-BALANCE-DISPLAY, FROM-AVAILABLE-BALANCE-DISPLAY, TO-ACTUAL-BALANCE-DISPLAY, TO-AVAILABLE-BALANCE-DISPLAY | GCD010 (lines 649-652) |

## Error Handling

| Condition                               | Action                                                                 | Return Code | Source Location       |
| --------------------------------------- | ---------------------------------------------------------------------- | ----------- | --------------------- |
| EXEC CICS RETURN TRANSID(OTFN) fails    | INITIALIZE ABNDINFO-REC, populate abend record (RESP, RESP2, APPLID, TASKNO, TRANID, date/time, ABND-CODE='HBNK', ABND-FREEFORM='A010 - RETURN TRANSID(OCCS) FAIL.' [NOTE: literal says 'OCCS' but actual transid is 'OTFN' -- stale copy-paste defect]), EXEC CICS LINK PROGRAM(ABNDPROC), then PERFORM ABEND-THIS-TASK | HBNK abend | A010 (line 255) |
| EXEC CICS RECEIVE MAP fails             | Same abend-info pattern; ABND-FREEFORM='RM010 - RECEIVE MAP FAIL.'; EXEC CICS LINK ABNDPROC; PERFORM ABEND-THIS-TASK | HBNK abend | RM010 (line 364) |
| EXEC CICS LINK XFRFUN fails             | Same abend-info pattern; ABND-FREEFORM='GCD010 - LINK XFRFUN FAIL.'; EXEC CICS LINK ABNDPROC; PERFORM ABEND-THIS-TASK | HBNK abend | GCD010 (line 504) |
| EXEC CICS SEND MAP ERASE fails          | Same abend-info pattern; ABND-FREEFORM='SM010 - SEND MAP ERASE FAIL.'; EXEC CICS LINK ABNDPROC; PERFORM ABEND-THIS-TASK | HBNK abend | SM010 (line 681) |
| EXEC CICS SEND MAP DATAONLY fails       | Same abend-info pattern; ABND-FREEFORM='SM010 - SEND MAP DATAONLY FAIL.'; EXEC CICS LINK ABNDPROC; PERFORM ABEND-THIS-TASK | HBNK abend | SM010 (line 756) |
| EXEC CICS SEND MAP DATAONLY ALARM fails | Same abend-info pattern; ABND-FREEFORM='SM010 - SEND MAP DATAONLY ALARM FAIL.'; EXEC CICS LINK ABNDPROC; PERFORM ABEND-THIS-TASK | HBNK abend | SM010 (line 832) |
| EXEC CICS SEND TEXT (termination) fails | Same abend-info pattern; ABND-FREEFORM='STM010 - SEND TEXT FAIL.'; EXEC CICS LINK ABNDPROC; PERFORM ABEND-THIS-TASK | HBNK abend | STM010 (line 910) |
| ABEND-THIS-TASK invoked                 | DISPLAY WS-FAIL-INFO (includes program name, message, RESP, RESP2, literal ' ABENDING TASK.'); EXEC CICS ABEND ABCODE('HBNK') NODUMP | HBNK | ATT010 (line 978) |

### Code Defects Noted

The following defects were found in the source and should be considered during modernisation:

1. **Stale transaction ID in abend message (A010, line 293)**: ABND-FREEFORM is set to `'A010 - RETURN TRANSID(OCCS) FAIL.'` but the actual EXEC CICS RETURN uses TRANSID('OTFN'). The same incorrect literal 'OCCS' also appears in WS-CICS-FAIL-MSG at line 308: `'BNK1TFN - A010 - RETURN TRANSID(OCCS) FAIL'`. This appears to be a copy-paste artefact from another program (likely BNKMENU which uses transaction OCCS/OMEN). All abend log records and console messages for this failure will incorrectly name the transaction.

2. **ABND-TIME populated with MM:MM instead of HH:MM:SS (all abend blocks)**: In every abend-info population block (A010 lines 277-282, RM010 lines 386-391, GCD010 lines 526-531, SM010 lines 703-708 and 778-783 and 854-859, STM010 lines 932-937), the time string is built as `WS-TIME-NOW-GRP-HH ':' WS-TIME-NOW-GRP-MM ':' WS-TIME-NOW-GRP-MM`. The third component should be `WS-TIME-NOW-GRP-SS` (seconds) but `WS-TIME-NOW-GRP-MM` (minutes) is used again. Field `WS-TIME-NOW-GRP-SS` is defined in WORKING-STORAGE (line 158) but is never referenced in the PROCEDURE DIVISION. All abend timestamps will show HH:MM:MM, making precise incident timing impossible.

3. **SUBPGM-FAIL-CODE '3' message is silently overwritten (GCD010, lines 603-635)**: When XFRFUN returns SUBPGM-SUCCESS='N' and SUBPGM-FAIL-CODE='3', the EVALUATE branch sets MESSAGEO to 'Sorry but the transfer could not be applied due to an unexpected error.' Unlike all other WHEN branches (1, 2, 4, OTHER), fail-code '3' has no `GO TO GCD999`. Execution falls through to END-EVALUATE, then END-IF, then reaches `IF SUBPGM-SUCCESS NOT = 'Y'` at line 629. Since SUBPGM-SUCCESS is still 'N', this condition is true and MESSAGEO is immediately overwritten with 'Sorry but the transfer could not be applied unable to determine success.' The specific "unexpected error" message is never visible to the user. The intended message for fail-code '3' is dead -- the user sees the same "unable to determine success" message as for all other unhandled states.

4. **Pseudo-conversational commarea carries no data (WS-COMMAREA, lines 125-128 and 247-252)**: The LINKAGE SECTION defines DFHCOMMAREA with sub-fields COMMAREA-FACCNO, COMMAREA-TACCNO, COMMAREA-AMT (to receive data from the prior invocation) and WORKING-STORAGE defines WS-COMMAREA with the same three sub-fields (to send data to the next invocation). However, neither DFHCOMMAREA's sub-fields nor WS-COMMAREA's sub-fields are ever referenced in the PROCEDURE DIVISION -- WS-COMMAREA is always passed as zeros to EXEC CICS RETURN. The commarea exists only to ensure EIBCALEN > 0 on the next invocation (so rule 1, the first-time check, fires only once). No actual field values are carried across the pseudo-conversational boundary; every invocation reads fresh data from the BMS map.

5. **Dead WORKING-STORAGE structures copied from another program (lines 83-110)**: Six groups of WORKING-STORAGE fields are defined but never referenced anywhere in the PROCEDURE DIVISION. These are: `COMM-DOB-SPLIT` (DD/MM/YYYY date split), `COMM-ADDR-SPLIT` (three-part address split of 160 characters total), `WS-CONVERSIONA` (13-character conversion area with redefinition), `WS-CONVERSIONB` (second 13-character conversion area with redefinition), and `WS-CONVERTED-VAL1` through `WS-CONVERTED-VAL4` (four PIC S9(10)V99 working values). These appear to be copy-paste residue from a customer or account maintenance program. They occupy WORKING-STORAGE but have no business function in BNK1TFN.

6. **Conditional DEBUG statements present (lines 1039 and 1152)**: Two DISPLAY statements prefixed with `D` in column 7 are COBOL conditional compile DEBUG lines. Line 1039 displays the leading-spaces count; line 1152 displays WS-NUM-COUNT-TOTAL during decimal validation. These are currently inactive because the `SOURCE-COMPUTER. IBM-370 WITH DEBUGGING MODE.` entry at line 21 is commented out. If a future compile inadvertently enables debugging mode, these DISPLAY statements would emit diagnostic output to the CICS console during every ENTER-key transaction.

7. **Dead one-byte COMMUNICATION-AREA field (line 66)**: `01 COMMUNICATION-AREA PIC X.` is defined in WORKING-STORAGE at line 66 but is never referenced in the PROCEDURE DIVISION. It is distinct from the 29-byte WS-COMMAREA (lines 125-128) used in EXEC CICS RETURN. This is a further dead WORKING-STORAGE field with no business function.

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. A010 (PREMIERE SECTION) -- main dispatch; evaluates EIBCALEN and EIBAID to route the request
2. SEND-MAP / SM010 -- sends BNK1TF map with ERASE on first entry; called directly from A010 for first-time and invalid-key cases
3. EXEC CICS RETURN TRANSID('OMEN') IMMEDIATE -- on PF3, transfers control to the main menu transaction immediately (does not fall through to RETURN at end of A010)
4. SEND-TERMINATION-MSG / STM010 -- sends 'Session Ended' text and ends the task on AID/PF12
5. PROCESS-MAP / PM010 -- called on ENTER; orchestrates receive, validate, transfer, display; unconditionally sets SEND-DATAONLY-ALARM before calling SEND-MAP regardless of validation outcome
6. RECEIVE-MAP / RM010 -- EXEC CICS RECEIVE MAP BNK1TF into BNK1TFI
7. EDIT-DATA / ED010 -- validates FACCNOI (numeric, non-zero account, not equal to TACCNOI), TACCNOI (numeric, non-zero account), then delegates to VALIDATE-AMOUNT
8. VALIDATE-AMOUNT SECTION / VA010 -- multi-step amount format and value validation; sets WS-AMOUNT-AS-FLOAT on success; uses both a fast path (purely numeric) and a full character-by-character analysis path (for amounts with decimal points); invoked as a SECTION PERFORM from ED010 line 472
9. GET-ACC-DATA / GCD010 -- packs SUBPGM-PARMS, EXEC CICS LINK PROGRAM('XFRFUN') SYNCONRETURN, interprets SUBPGM-SUCCESS and SUBPGM-FAIL-CODE, maps balances to screen (only called if VALID-DATA is true after ED010/VA010)
10. SEND-MAP / SM010 -- sends updated map with DATAONLY ALARM (flag set unconditionally in PM010 after EDIT-DATA/GET-ACC-DATA); SM010 evaluates SEND-FLAG in order: SEND-ERASE then SEND-DATAONLY then SEND-DATAONLY-ALARM; first matching flag causes a GO TO SM999 after transmission, making the three modes mutually exclusive
11. EXEC CICS RETURN TRANSID('OTFN') COMMAREA(WS-COMMAREA) LENGTH(29) -- pseudo-conversational return; WS-COMMAREA is all zeros (fields are never populated -- see Code Defect #4); commarea serves only as a non-zero-length sentinel
12. POPULATE-TIME-DATE / PTD010 -- EXEC CICS ASKTIME + FORMATTIME; used only inside abend-info population blocks
13. ABEND-THIS-TASK / ATT010 -- DISPLAY WS-FAIL-INFO + EXEC CICS ABEND ABCODE('HBNK') NODUMP; terminal error handler
