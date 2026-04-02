---
type: business-rules
program: BNK1CRA
program_type: online
status: draft
confidence: high
last_pass: 5
calls:
- DBCRFUN
- ABNDPROC
called_by: []
uses_copybooks:
- ABNDINFO
- BNK1CDM
- DFHAID
reads: []
writes: []
db_tables: []
transactions:
- OCRA
mq_queues: []
---

# BNK1CRA -- Business Rules

## Program Purpose

BNK1CRA is the CICS online Credit/Debit Funds program in the CBSA Banking Sample Application. It presents a BMS screen (map BNK1CD in mapset BNK1CDM) that allows a terminal user to apply a monetary debit or credit to an existing bank account. The user supplies an account number, a sign character ('+' or '-'), and an amount. BNK1CRA validates all three inputs and then delegates the actual database update to the linked program DBCRFUN. After the update it displays the resulting actual and available balances. The program runs under transaction OCRA and persists its COMMAREA across pseudo-conversational cycles.

## Input / Output

| Direction | Resource | Type | Description |
| --------- | -------- | ---- | ----------- |
| IN        | BNK1CD / BNK1CDM | CICS BMS Map | Account number, sign character, and amount entered by terminal user |
| IN        | DFHCOMMAREA (21 bytes) | CICS COMMAREA | Account number (8), sign (1), amount (12) passed back from previous pseudo-conversational cycle |
| OUT       | BNK1CD / BNK1CDM | CICS BMS Map | Updated display: sort code, available balance, actual balance, message text |
| OUT       | DBCRFUN | CICS LINK | Debit/credit request: account number, signed amount, origin data |
| OUT       | ABNDPROC | CICS LINK | Abend handler invoked on any CICS error |
| OUT       | OMEN transaction | CICS RETURN TRANSID | Navigation to main menu on PF3 |

## Business Rules

### Screen Navigation / AID Key Routing

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 1 | First-time entry | `EIBCALEN = ZERO` | Clear map (LOW-VALUE to BNK1CDO), set cursor to ACCNO field (ACCNOL = -1), send map with ERASE | A010 lines 185-189 |
| 2 | PA key pressed | `EIBAID = DFHPA1 OR DFHPA2 OR DFHPA3` | CONTINUE -- ignore the key stroke, fall through to RETURN TRANSID | A010 lines 194-195 |
| 3 | PF3 pressed -- return to menu | `EIBAID = DFHPF3` | `EXEC CICS RETURN TRANSID('OMEN') IMMEDIATE` -- transfer control to main menu | A010 lines 200-206 |
| 4 | AID key or PF12 pressed -- end session | `EIBAID = DFHAID OR DFHPF12` | Send termination message ('Session Ended'), then `EXEC CICS RETURN` | A010 lines 212-217 |
| 5 | CLEAR key pressed | `EIBAID = DFHCLEAR` | Send CONTROL ERASE FREEKB to blank the screen, then `EXEC CICS RETURN` | A010 lines 222-229 |
| 6 | ENTER key pressed | `EIBAID = DFHENTER` | Process the map (PERFORM PROCESS-MAP) | A010 lines 234-235 |
| 7 | Any other AID key | WHEN OTHER | Set LOW-VALUES to BNK1CDO, display 'Invalid key pressed.', `MOVE 8 TO ACCNOL` (cursor positioned at offset 8 of ACCNO field), set SEND-DATAONLY-ALARM, send map | A010 lines 240-245 |

### COMMAREA Persistence

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 8 | Carry forward COMMAREA on non-first cycles | `EIBCALEN NOT = ZERO` | Copy COMM-ACCNO, COMM-SIGN, COMM-AMT from DFHCOMMAREA into WS-COMM-AREA before issuing RETURN | A010 lines 255-260 |
| 9 | Always issue pseudo-conversational RETURN | Unconditional (after EVALUATE) | `EXEC CICS RETURN TRANSID('OCRA') COMMAREA(WS-COMM-AREA) LENGTH(21)` | A010 lines 263-268 |

### Input Validation -- Account Number (ED010)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 10 | Account number must be numeric | `ACCNOI NOT NUMERIC` (after DEEDIT BIF strips non-numeric chars) | Message: 'Please enter an account number.', set VALID-DATA-SW = 'N', GO TO ED999 | ED010 lines 450-455 |
| 11 | Account number must not be zero | `ACCNOI = ZERO` | Message: 'Please enter a non zero account number.', set VALID-DATA-SW = 'N', GO TO ED999 | ED010 lines 457-462 |

### Input Validation -- Sign Character (ED010)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 12 | Sign must be '+' or '-' when sign field length is exactly 1 | `SIGNI NOT = '+' AND SIGNI NOT = '-' AND SIGNL = 1` | Message: 'Please enter + or - preceding the amount', set VALID-DATA-SW = 'N', GO TO ED999 | ED010 lines 464-469 |
| 12a | Sign field bypass when empty -- defaults to credit | `SIGNL = 0` (empty sign field, BMS reported zero length) | The condition `SIGNL = 1` is false so sign validation is entirely skipped. In UCD010, `IF SIGNI = '-'` will also be false (SIGNI contains spaces), so the amount is NOT negated -- the transaction is silently treated as a credit (positive). An empty sign field is never explicitly rejected. | ED010 line 464; UCD010 lines 494-496 |

### Input Validation -- Amount (VA010, VALIDATE-AMOUNT section)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 13 | Amount field must not be empty | `AMTL = ZERO` | Message: 'The Amount entered must be numeric.', set VALID-DATA-SW = 'N', cursor to AMT field (AMTL = -1), GO TO VA999 | VA010 lines 967-973 |
| 14 | If amount is entirely numeric, accept it immediately | `AMTI(1:AMTL) IS NUMERIC` | Compute `WS-AMOUNT-AS-FLOAT = FUNCTION NUMVAL(AMTI(1:AMTL))`, set VALID-DATA-SW = 'Y', GO TO VA999 | VA010 lines 976-982 |
| 15 | Amount must not be entirely spaces | `WS-NUM-COUNT-TOTAL = AMTL` (all leading spaces) | Message: 'The Amount entered must be numeric.', set VALID-DATA-SW = 'N', cursor to AMT field, GO TO VA999 | VA010 lines 991-997 |
| 16 | Amount must not contain embedded spaces | `WS-NUM-COUNT-SPACE > 0` (spaces found within trimmed amount) | Message: 'Please supply a numeric amount without embedded spaces.', set VALID-DATA-SW = 'N', cursor to AMT field, GO TO VA999 | VA010 lines 1047-1057 |
| 17 | Amount must consist only of digits and at most one decimal point | `WS-NUM-COUNT-TOTAL < WS-AMOUNT-UNSTR-L` (non-digit/non-period characters present) | Message: 'Please supply a numeric amount.', set VALID-DATA-SW = 'N', cursor to AMT field, GO TO VA999 | VA010 lines 1059-1067 |
| 18 | Amount must not contain more than one decimal point | `WS-NUM-COUNT-POINT > 1` | Message: 'Use one decimal point for amount only.', set VALID-DATA-SW = 'N', cursor to AMT field, GO TO VA999 | VA010 lines 1077-1086 |
| 19 | Amount must not have more than two decimal places | `WS-NUM-COUNT-POINT = 1` AND characters-after-decimal > 2 AND non-space digits after decimal > 2 (two-pass check: first TALLYING FOR CHARACTERS AFTER '.', then re-TALLYING only digits 0-9 after '.') | Message: 'Only up to two decimal places are supported.', set VALID-DATA-SW = 'N', cursor to AMT field, GO TO VA999 | VA010 lines 1091-1129 |
| 20 | Amount must not be zero | `WS-AMOUNT-AS-FLOAT = ZERO` (after NUMVAL conversion) | Message: 'Please supply a non-zero amount.', set VALID-DATA-SW = 'N', cursor to AMT field, GO TO VA999 | VA010 lines 1136-1145 |

### Debit / Credit Application (UCD010)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 21 | Only apply debit/credit if all validation passes | `VALID-DATA` (88-level, value 'Y') | PERFORM UPD-CRED-DATA | PM010 lines 350-351 |
| 22 | Negate amount for debit (negative sign) | `SIGNI = '-'` | `COMPUTE WS-AMOUNT-AS-FLOAT = WS-AMOUNT-AS-FLOAT * -1` | UCD010 lines 494-496 |
| 23 | Capture terminal origin data before linking | Unconditional | `EXEC CICS INQUIRE ASSOCIATION(EIBTASKN)` populates APPLID, USERID, FACILITY-NAME, NETWORK-ID, FACILITY-TYPE in SUBPGM-PARMS | UCD010 lines 503-509 |
| 24 | Delegate account update to DBCRFUN | Unconditional (when validation passes) | `EXEC CICS LINK PROGRAM('DBCRFUN') COMMAREA(SUBPGM-PARMS) SYNCONRETURN` | UCD010 lines 511-517 |

### DBCRFUN Result Handling (UCD010)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 25 | Account not found | `SUBPGM-SUCCESS = 'N'` AND `SUBPGM-FAIL-CODE = '1'` | Message: 'Sorry but the ACCOUNT no was not found for SORTCODE [sortcode]. Amount not applied.', set VALID-DATA-SW = 'N', GO TO UCD999 | UCD010 lines 586-594 |
| 26 | Unexpected error applying amount (code 2) | `SUBPGM-SUCCESS = 'N'` AND `SUBPGM-FAIL-CODE = '2'` | Message: 'Sorry but the AMOUNT could not be applied due to an unexpected error.', set VALID-DATA-SW = 'N', GO TO UCD999 | UCD010 lines 596-602 |
| 27 | Insufficient funds | `SUBPGM-SUCCESS = 'N'` AND `SUBPGM-FAIL-CODE = '3'` | Message: 'Sorry insufficient funds available to process the request.', set VALID-DATA-SW = 'N', GO TO UCD999 | UCD010 lines 604-610 |
| 28 | Unknown failure code from DBCRFUN | `SUBPGM-SUCCESS = 'N'` AND `SUBPGM-FAIL-CODE` not '1', '2', or '3' | Message: 'Sorry but the AMOUNT could not be applied due to an unexpected error. [fail-code]', set VALID-DATA-SW = 'N', GO TO UCD999 | UCD010 lines 612-619 |
| 29 | Successful debit/credit | `SUBPGM-SUCCESS NOT = 'N'` (else branch) | Message: 'Amount successfully applied to the account.', then populate map with account number, sort code, actual balance, available balance | UCD010 lines 622-637 |

### Map Send Mode Selection (SM010)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 30 | Send full map with erase | `SEND-ERASE` (flag = '1') | `EXEC CICS SEND MAP('BNK1CD') ... ERASE FREEKB`, then GO TO SM999 | SM010 lines 648-718 |
| 31 | Send data only (no alarm) | `SEND-DATAONLY` (flag = '2') | `EXEC CICS SEND MAP('BNK1CD') ... DATAONLY FREEKB`, then GO TO SM999 | SM010 lines 723-793 |
| 32 | Send data only with alarm | `SEND-DATAONLY-ALARM` (flag = '3') | `EXEC CICS SEND MAP('BNK1CD') ... DATAONLY ALARM FREEKB` | SM010 lines 798-868 |
| 33 | After PROCESS-MAP always send with alarm | Unconditional (PM010) | `SET SEND-DATAONLY-ALARM TO TRUE` before PERFORM SEND-MAP | PM010 line 354 |

## Calculations

| Calculation | Formula / Logic | Input Fields | Output Field | Source Location |
| --- | --- | --- | --- | --- |
| Negate amount for debit | `WS-AMOUNT-AS-FLOAT = WS-AMOUNT-AS-FLOAT * -1` when sign is '-' | WS-AMOUNT-AS-FLOAT (COMP-2 float), SIGNI | WS-AMOUNT-AS-FLOAT | UCD010 lines 494-496 |
| Convert validated amount to float | `WS-AMOUNT-AS-FLOAT = FUNCTION NUMVAL(AMTI(1:AMTL))` (fast path, all numeric) | AMTI (map amount field), AMTL (field length) | WS-AMOUNT-AS-FLOAT (COMP-2) | VA010 lines 977-978 |
| Convert trimmed amount string to float | `WS-AMOUNT-AS-FLOAT = FUNCTION NUMVAL(WS-AMOUNT-UNSTR(1:WS-AMOUNT-UNSTR-L))` (after leading/trailing space removal and decimal-point checks) | WS-AMOUNT-UNSTR (trimmed input string), WS-AMOUNT-UNSTR-L (effective length) | WS-AMOUNT-AS-FLOAT (COMP-2) | VA010 lines 1133-1134 |
| Strip leading spaces from amount | `WS-AMOUNT-UNSTR-L = AMTL - WS-NUM-COUNT-TOTAL` (leading space count) | AMTL, WS-NUM-COUNT-TOTAL | WS-AMOUNT-UNSTR-L | VA010 line 999 |
| Strip trailing spaces from amount | `WS-AMOUNT-UNSTR-L = WS-AMOUNT-UNSTR-L - WS-NUM-COUNT-TOTAL` (trailing space count via REVERSE) | WS-AMOUNT-UNSTR-L, WS-NUM-COUNT-TOTAL (trailing spaces) | WS-AMOUNT-UNSTR-L | VA010 lines 1021-1022 |
| COMMAREA length | Hardcoded LENGTH(21): ACCNO(8) + SIGN(1) + AMT(12) | COMM-ACCNO, COMM-SIGN, COMM-AMT | WS-COMM-AREA (21 bytes passed in COMMAREA) | A010 line 266 |

## Error Handling

| Condition | Action | Return Code / ABEND | Source Location |
| --- | --- | --- | --- |
| EXEC CICS RETURN TRANSID('OCRA') fails (RESP not NORMAL) | Initialize ABNDINFO-REC, set ABND-CODE='HBNK', STRING 'A010 - RETURN TRANSID(OCRA) FAIL.' into ABND-FREEFORM, LINK to ABNDPROC, then PERFORM ABEND-THIS-TASK | ABEND code 'HBNK', NODUMP | A010 lines 271-328 |
| EXEC CICS RECEIVE MAP fails (RESP not NORMAL) | Initialize ABNDINFO-REC, set ABND-CODE='HBNK', STRING 'RM010 - RECEIVE MAP FAIL.' into ABND-FREEFORM, LINK to ABNDPROC, then PERFORM ABEND-THIS-TASK. Note: WS-CICS-FAIL-MSG is incorrectly set to 'BNKMENU - RM010 - RECEIVE MAP FAIL' (copy-paste defect from BNKMENU source) | ABEND code 'HBNK', NODUMP | RM010 lines 378-434 |
| EXEC CICS LINK PROGRAM('DBCRFUN') fails (RESP not NORMAL) | Initialize ABNDINFO-REC, set ABND-CODE='HBNK', STRING 'UCD010 - LINK DBCRFUN FAIL.' into ABND-FREEFORM, LINK to ABNDPROC, then PERFORM ABEND-THIS-TASK | ABEND code 'HBNK', NODUMP | UCD010 lines 519-575 |
| EXEC CICS SEND MAP ERASE fails (RESP not NORMAL) | Initialize ABNDINFO-REC, STRING 'SM010 - SEND MAP ERASE FAIL.' into ABND-FREEFORM, LINK to ABNDPROC, then PERFORM ABEND-THIS-TASK | ABEND code 'HBNK', NODUMP | SM010 lines 658-714 |
| EXEC CICS SEND MAP DATAONLY fails (RESP not NORMAL) | Initialize ABNDINFO-REC, STRING 'SM010 - SEND MAP DATAONLY FAIL.' into ABND-FREEFORM, LINK to ABNDPROC, then PERFORM ABEND-THIS-TASK | ABEND code 'HBNK', NODUMP | SM010 lines 733-789 |
| EXEC CICS SEND MAP DATAONLY ALARM fails (RESP not NORMAL) | Initialize ABNDINFO-REC, STRING 'SM010 - SEND MAP DATAONLY ALARM FAIL.' into ABND-FREEFORM, LINK to ABNDPROC, then PERFORM ABEND-THIS-TASK | ABEND code 'HBNK', NODUMP | SM010 lines 809-865 |
| EXEC CICS SEND TEXT (termination message) fails (RESP not NORMAL) | Initialize ABNDINFO-REC, STRING 'STM010 - SEND TEXT FAIL.' into ABND-FREEFORM, LINK to ABNDPROC, then PERFORM ABEND-THIS-TASK | ABEND code 'HBNK', NODUMP | STM010 lines 887-943 |
| ABEND-THIS-TASK invoked | DISPLAY WS-FAIL-INFO (includes 'BNK1CRA', fail message, RESP, RESP2, 'ABENDING TASK.'), then EXEC CICS ABEND ABCODE('HBNK') NODUMP | ABEND code 'HBNK' | ATT010 lines 951-956 |
| DBCRFUN returns SUBPGM-SUCCESS = 'N' with fail code '1' | Display message 'Sorry but the ACCOUNT no was not found for SORTCODE [sortcode]. Amount not applied.' | No ABEND -- user message, validation flag 'N' | UCD010 lines 585-594 |
| DBCRFUN returns SUBPGM-SUCCESS = 'N' with fail code '2' | Display message 'Sorry but the AMOUNT could not be applied due to an unexpected error.' | No ABEND -- user message, validation flag 'N' | UCD010 lines 596-602 |
| DBCRFUN returns SUBPGM-SUCCESS = 'N' with fail code '3' | Display message 'Sorry insufficient funds available to process the request.' | No ABEND -- user message, validation flag 'N' | UCD010 lines 604-610 |
| DBCRFUN returns SUBPGM-SUCCESS = 'N' with unknown fail code | Display message 'Sorry but the AMOUNT could not be applied due to an unexpected error. [fail-code]' | No ABEND -- user message, validation flag 'N' | UCD010 lines 612-619 |
| Account number not numeric (ACCNOI after DEEDIT) | Message: 'Please enter an account number.' VALID-DATA-SW = 'N', GO TO ED999 | No ABEND | ED010 lines 450-455 |
| Account number is zero | Message: 'Please enter a non zero account number.' VALID-DATA-SW = 'N', GO TO ED999 | No ABEND | ED010 lines 457-462 |
| Sign character is not '+' or '-' (and SIGNL = 1) | Message: 'Please enter + or - preceding the amount' VALID-DATA-SW = 'N', GO TO ED999 | No ABEND | ED010 lines 464-469 |

### Source Code Defects Observed

| Defect | Location | Description |
| --- | --- | --- |
| ABND-TIME formatted as HH:MM:MM (seconds omitted) | A010 lines 293-298, RM010 lines 400-405, UCD010 lines 541-546, SM010 lines 680-685 and 755-760 and 831-836, STM010 lines 909-914 | The STRING that builds ABND-TIME uses `WS-TIME-NOW-GRP-MM` for both the second and third time components instead of `WS-TIME-NOW-GRP-MM` and `WS-TIME-NOW-GRP-SS`. Every ABND-TIME timestamp in ABNDINFO-REC will show minutes twice (e.g. '14:32:32' when actual time is '14:32:07'). This affects all CICS-error branches throughout the program. |
| RM010 WS-CICS-FAIL-MSG names wrong program | RM010 line 430 | `MOVE 'BNKMENU - RM010 - RECEIVE MAP FAIL ' TO WS-CICS-FAIL-MSG` -- should say 'BNK1CRA'. The DISPLAY output in ATT010 will misidentify the failing program as BNKMENU. This is a copy-paste error from BNKMENU's source. |
| UNSTRING reference modifier uses wrong length for leading-space case | VA010 line 1008 | `UNSTRING AMTI(WS-NUM-COUNT-TOTAL:AMTL)` uses the full map field length `AMTL` as the length operand after incrementing `WS-NUM-COUNT-TOTAL` to the start offset. The correct length argument should be `AMTL - (original leading-space count)` to avoid referencing bytes beyond the meaningful content. Because WS-AMOUNT-UNSTR is 13 bytes and AMTL is limited by the BMS map field size, the overflow is absorbed silently and functional impact is low, but the reference modifier is technically incorrect. |
| Empty sign field silently defaults to credit | ED010 line 464; UCD010 lines 494-496 | When SIGNL=0 the sign validation is skipped (condition requires SIGNL=1). In UCD010 the negation check `IF SIGNI = '-'` is also false for a space value, so the transaction silently becomes a credit. No error message is shown and no cursor placement occurs. A user who omits the sign will unknowingly apply a credit instead of receiving a clear validation error. |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. A010 (PREMIERE SECTION) -- Dispatch on AID key; first call initialises map, ENTER triggers PROCESS-MAP, PF3 exits to OMEN, AID/PF12 sends termination message; after EVALUATE copies COMMAREA and issues RETURN TRANSID('OCRA')
2. PROCESS-MAP (PM010) -- Orchestrates the receive-validate-update cycle; sets SEND-DATAONLY-ALARM before final SEND-MAP
3. RECEIVE-MAP (RM010) -- EXEC CICS RECEIVE MAP('BNK1CD') MAPSET('BNK1CDM') INTO(BNK1CDI); ABENDs on CICS error
4. EDIT-DATA (ED010) -- Applies DEEDIT BIF to ACCNOI; validates account number is numeric and non-zero; validates sign character (only when SIGNL = 1); then PERFORMs VALIDATE-AMOUNT
5. VALIDATE-AMOUNT (VA010) -- Full numeric and format validation of AMT field (empty, all-space, embedded-space, non-numeric chars, multiple decimal points, more than two decimal places, zero value); converts to WS-AMOUNT-AS-FLOAT (COMP-2)
6. UPD-CRED-DATA (UCD010) -- Only reached when VALID-DATA = 'Y'; negates amount for debit; captures origin via EXEC CICS INQUIRE ASSOCIATION; LINKs to DBCRFUN with SYNCONRETURN; handles all DBCRFUN fail codes; populates map with returned sort code and balances
7. SEND-MAP (SM010) -- Sends BNK1CD map in one of three modes (ERASE, DATAONLY, DATAONLY+ALARM) depending on SEND-FLAG value; ABENDs on any CICS SEND error
8. SEND-TERMINATION-MSG (STM010) -- EXEC CICS SEND TEXT FROM(END-OF-SESSION-MESSAGE='Session Ended') ERASE FREEKB; ABENDs on error
9. ABEND-THIS-TASK (ATT010) -- Final error handler: DISPLAY WS-FAIL-INFO then EXEC CICS ABEND ABCODE('HBNK') NODUMP
10. POPULATE-TIME-DATE (PTD010) -- EXEC CICS ASKTIME + FORMATTIME; used to populate ABNDINFO-REC timestamps before linking to ABNDPROC; called from all error-handling branches
11. EXEC CICS LINK PROGRAM('ABNDPROC') COMMAREA(ABNDINFO-REC) -- Called from every CICS-error branch before ABEND-THIS-TASK; passes structured abend information including task number, transaction ID, APPLID, timestamp, program name, RESP/RESP2 codes, and free-form error string
