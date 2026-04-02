---
type: business-rules
program: CBSTM03A
program_type: subprogram
status: draft
confidence: high
last_pass: 5
calls:
- CBSTM03B
- CEE3ABD
called_by: []
uses_copybooks:
- COSTM01
- CUSTREC
- CVACT01Y
- CVACT03Y
reads:
- HTML-FILE
- STMT-FILE
writes: []
db_tables: []
transactions: []
mq_queues: []
---

# CBSTM03A -- Business Rules

## Program Purpose

CBSTM03A is a batch COBOL program that generates account statements from transaction
data. For each account in the card cross-reference file (XREFFILE), it retrieves the
associated customer record (CUSTFILE), account record (ACCTFILE), and all transactions
(TRNXFILE) for the account's card numbers, then writes statement output in two parallel
formats: plain text (STMT-FILE, 80 chars/line) and HTML (HTML-FILE, 100 chars/line).

The program intentionally exercises five mainframe-specific techniques: TIOT control
block addressing, ALTER/GO TO statements, COMP and COMP-3 variables, a two-dimensional
in-memory transaction array, and subroutine calls. All VSAM file I/O is delegated to
the subroutine CBSTM03B via a parameter block (WS-M03B-AREA).

The file-open sequence is driven by a dispatch paragraph (0000-START) using ALTER
statements to redirect a single GO TO target, opening four files in sequence:
TRNXFILE -> XREFFILE -> CUSTFILE -> ACCTFILE, before falling through to the main
processing loop.

**JCL preprocessing note (CREASTMT.JCL STEP010):** Before CBSTM03A runs, a SORT
step reformats the raw transaction VSAM file. It sorts by card number (original
positions 263-278) then transaction ID (positions 1-16), then remaps the output
record so that card number occupies positions 1-16, the original data runs from
position 17 onwards, and reference data appears from position 279. CBSTM03A's
in-memory array logic depends on this card-number-first ordering for correct
grouping.

## Input / Output

| Direction | Resource  | Type | Description                                               |
| --------- | --------- | ---- | --------------------------------------------------------- |
| IN        | XREFFILE  | VSAM | Card cross-reference file; read sequentially via CBSTM03B |
| IN        | CUSTFILE  | VSAM | Customer master; keyed read by XREF-CUST-ID via CBSTM03B |
| IN        | ACCTFILE  | VSAM | Account master; keyed read by XREF-ACCT-ID via CBSTM03B  |
| IN        | TRNXFILE  | VSAM | Transaction master; read sequentially via CBSTM03B        |
| OUT       | STMT-FILE | File | Plain-text statement output, 80-byte records (STMTFILE DD)|
| OUT       | HTML-FILE | File | HTML statement output, 100-byte records (HTMLFILE DD)     |

## Business Rules

### File Open Dispatch (ALTER / GO TO Pattern)

| #  | Rule                              | Condition                                   | Action                                                                       | Source Location          |
| -- | --------------------------------- | ------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------ |
| 1  | Dispatch to correct open routine  | WS-FL-DD = 'TRNXFILE'                       | ALTER 8100-FILE-OPEN to PROCEED to 8100-TRNXFILE-OPEN; GO TO 8100-FILE-OPEN  | 0000-START lines 299-301 |
| 2  | Dispatch to correct open routine  | WS-FL-DD = 'XREFFILE'                       | ALTER 8100-FILE-OPEN to PROCEED to 8200-XREFFILE-OPEN; GO TO 8100-FILE-OPEN  | 0000-START lines 302-304 |
| 3  | Dispatch to correct open routine  | WS-FL-DD = 'CUSTFILE'                       | ALTER 8100-FILE-OPEN to PROCEED to 8300-CUSTFILE-OPEN; GO TO 8100-FILE-OPEN  | 0000-START lines 305-307 |
| 4  | Dispatch to correct open routine  | WS-FL-DD = 'ACCTFILE'                       | ALTER 8100-FILE-OPEN to PROCEED to 8400-ACCTFILE-OPEN; GO TO 8100-FILE-OPEN  | 0000-START lines 308-310 |
| 5  | Dispatch to transaction read loop | WS-FL-DD = 'READTRNX'                       | GO TO 8500-READTRNX-READ                                                     | 0000-START lines 311-312 |
| 6  | Terminate if unknown DD name      | WS-FL-DD = WHEN OTHER                       | GO TO 9999-GOBACK (normal exit)                                              | 0000-START lines 313-314 |

**WARNING: ALTER statements.** Lines 300, 303, 306, 309 use ALTER to dynamically
redirect the single GO TO inside paragraph 8100-FILE-OPEN at run time. This is the
only use of ALTER in the program. The effective dispatch target changes each time
0000-START is entered with a different WS-FL-DD value.

### TIOT Control Block Walk

| #  | Rule                               | Condition                                    | Action                                                              | Source Location      |
| -- | ---------------------------------- | -------------------------------------------- | ------------------------------------------------------------------- | -------------------- |
| 7  | Resolve PSA -> TCB -> TIOT chain   | Program entry (unconditional)                | SET ADDRESS OF PSA-BLOCK to PSAPTR (absolute zero), follow pointers | Lines 266-273        |
| 8  | Display each DD name in TIOT       | PERFORM UNTIL END-OF-TIOT OR TIO-LEN = LOW-VALUES | Display TIOCDDNM with 'valid UCB' or 'null UCB' annotation     | Lines 276-285        |
| 9  | Distinguish valid vs null UCB (in loop) | NOT NULL-UCB (UCB-ADDR NOT = LOW-VALUES) | Display ': [ddname] -- valid UCB'                                  | Lines 278-280        |
| 10 | Identify null UCB (in loop)        | NULL-UCB (UCB-ADDR = LOW-VALUES)             | Display ': [ddname] --  null UCB' (two spaces before 'null')        | Lines 281-282        |
| 11 | Advance TIOT pointer by segment    | Each iteration                               | COMPUTE BUMP-TIOT = BUMP-TIOT + LENGTH OF TIOT-SEG; SET ADDRESS OF TIOT-ENTRY | Lines 283-284 |
| 12 | Display final TIOT entry after loop | Post-PERFORM (loop termination entry)       | IF NOT NULL-UCB: Display ': [ddname] -- valid UCB'; ELSE Display ': [ddname] -- null  UCB' (two spaces before 'UCB' in null branch) | Lines 287-291 |

Note: Rule 12 fires once after the PERFORM loop exits, displaying the TIOT entry
that triggered end-of-loop (END-OF-TIOT or TIO-LEN = LOW-VALUES). This entry is
not displayed inside the loop, so this post-loop IF ensures it is always shown.

**Source discrepancy**: The in-loop null branch (line 281) uses `'--  null UCB'`
(two spaces before "null"), while the post-loop null branch (line 290) uses
`'-- null  UCB'` (two spaces before "UCB"). The spacing difference is inconsistent
in the source and produces subtly different output for the final TIOT entry.

### Main Processing Loop

| #  | Rule                              | Condition                      | Action                                                                      | Source Location           |
| -- | --------------------------------- | ------------------------------ | --------------------------------------------------------------------------- | ------------------------- |
| 13 | Loop until all XREF records read  | END-OF-FILE = 'Y'              | Exit PERFORM and close all files                                            | 1000-MAINLINE lines 317-329 |
| 14 | Process each XREF record          | END-OF-FILE = 'N'              | PERFORM 1000-XREFFILE-GET-NEXT, then conditionally process                 | 1000-MAINLINE lines 318-327 |
| 15 | Fetch customer, account, create statement only if XREF read succeeded | END-OF-FILE = 'N' after XREF read | PERFORM 2000-CUSTFILE-GET, 3000-ACCTFILE-GET, 5000-CREATE-STATEMENT | 1000-MAINLINE lines 320-323 |
| 16 | Reset card jump counter before transaction write | Before 4000-TRNXFILE-GET | MOVE 1 TO CR-JMP; MOVE ZERO TO WS-TOTAL-AMT | 1000-MAINLINE lines 324-325 |
| 17 | Write transactions for current account | After creating statement header | PERFORM 4000-TRNXFILE-GET                                        | 1000-MAINLINE line 326    |

### Transaction Array Population (8500-READTRNX-READ)

The transaction array (WS-TRNX-TABLE) is populated during the TRNXFILE read pass
before the XREF loop begins. It supports 51 card numbers (CR-CNT up to 51) and
10 transactions per card (TR-CNT up to 10).

| #  | Rule                                   | Condition                                   | Action                                                                              | Source Location             |
| -- | -------------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------------------- | --------------------------- |
| 18 | Same card number as previous record    | WS-SAVE-CARD = TRNX-CARD-NUM               | ADD 1 TO TR-CNT (increment transaction counter for current card)                   | 8500-READTRNX-READ line 820  |
| 19 | New card number encountered            | WS-SAVE-CARD NOT = TRNX-CARD-NUM           | MOVE TR-CNT to WS-TRCT(CR-CNT); ADD 1 to CR-CNT; MOVE 1 to TR-CNT (save old count, start new card slot) | 8500-READTRNX-READ lines 822-824 |
| 20 | Store transaction in 2D array          | Each record read                            | WS-CARD-NUM(CR-CNT) = TRNX-CARD-NUM; WS-TRAN-NUM(CR-CNT,TR-CNT) = TRNX-ID; WS-TRAN-REST(CR-CNT,TR-CNT) = TRNX-REST | 8500-READTRNX-READ lines 827-829 |
| 21 | Update WS-SAVE-CARD after each store   | Each record read (unconditional)            | MOVE TRNX-CARD-NUM TO WS-SAVE-CARD (line 830 -- ensures card-change detection on next record) | 8500-READTRNX-READ line 830 |
| 22 | Continue reading until EOF             | WS-M03B-RC = '00'                           | MOVE WS-M03B-FLDT to TRNX-RECORD; GO TO 8500-READTRNX-READ (self-loop via GO TO)   | 8500-READTRNX-READ lines 839-840 |
| 23 | Finalize last card's transaction count | WS-M03B-RC = '10' (EOF)                    | MOVE TR-CNT to WS-TRCT(CR-CNT); switch WS-FL-DD to 'XREFFILE'; GO TO 0000-START   | 8599-EXIT lines 850-852      |

### Transaction Matching and Statement Write (4000-TRNXFILE-GET)

| #  | Rule                               | Condition                                             | Action                                                                                | Source Location              |
| -- | ---------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------- | ---------------------------- |
| 24 | Match XREF card to array card slot | WS-CARD-NUM(CR-JMP) = XREF-CARD-NUM                  | Write all transactions for this card from the 2D array via PERFORM 6000-WRITE-TRANS  | 4000-TRNXFILE-GET lines 420-431 |
| 25 | Stop array scan if card exceeded   | WS-CARD-NUM(CR-JMP) > XREF-CARD-NUM OR CR-JMP > CR-CNT | Exit PERFORM VARYING (no write)                                                     | 4000-TRNXFILE-GET lines 418-419 |
| 26 | Accumulate total expenditure       | Each matching transaction                             | ADD TRNX-AMT TO WS-TOTAL-AMT                                                         | 4000-TRNXFILE-GET line 429   |
| 27 | Write separator then total line    | After inner PERFORM completes (unconditional)         | WRITE ST-LINE12 (80 dashes separator); MOVE WS-TOTAL-AMT to WS-TRN-AMT; MOVE WS-TRN-AMT to ST-TOTAL-TRAMT; WRITE ST-LINE14A ('Total EXP:' + '$' + Z(9).99- amount, 80 chars) | 4000-TRNXFILE-GET lines 433-436 |
| 28 | Write statement end delimiter      | After total (unconditional)                           | WRITE ST-LINE15 (80-char '***...END OF STATEMENT...***') to STMT-FILE; write 8 HTML closing lines: `<tr>`, `<td colspan="3" style="padding:0px 5px; background-color:#1d1d96b3;">` (HTML-L10), `<h3>End of Statement</h3>` (HTML-L75), `</td>`, `</tr>`, `</table>`, `</body>`, `</html>` | 4000-TRNXFILE-GET lines 437-454 |

### XREF File Read Routing

| #  | Rule                               | Condition              | Action                                                        | Source Location                |
| -- | ---------------------------------- | ---------------------- | ------------------------------------------------------------- | ------------------------------ |
| 29 | Successful sequential XREF read    | WS-M03B-RC = '00'      | CONTINUE (in EVALUATE); MOVE WS-M03B-FLDT to CARD-XREF-RECORD (unconditional, line 364, executed regardless of RC) | 1000-XREFFILE-GET-NEXT lines 353-364 |
| 30 | End of XREF file                   | WS-M03B-RC = '10'      | MOVE 'Y' TO END-OF-FILE; MOVE WS-M03B-FLDT to CARD-XREF-RECORD still executes (line 364 is outside EVALUATE) | 1000-XREFFILE-GET-NEXT lines 356-364 |
| 31 | Unexpected XREF read error         | WS-M03B-RC = OTHER     | DISPLAY 'ERROR READING XREFFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; PERFORM 9999-ABEND-PROGRAM | 1000-XREFFILE-GET-NEXT lines 358-361 |

Note: MOVE WS-M03B-FLDT TO CARD-XREF-RECORD at line 364 is unconditional -- it falls
outside the EVALUATE block and executes on all return codes before EXIT. On EOF (RC='10'),
the buffer is moved to CARD-XREF-RECORD even though END-OF-FILE='Y' will prevent it
from being processed by the mainline loop.

### Customer File Read Routing

| #  | Rule                               | Condition              | Action                                                        | Source Location          |
| -- | ---------------------------------- | ---------------------- | ------------------------------------------------------------- | ------------------------ |
| 32 | Successful keyed CUST read         | WS-M03B-RC = '00'      | CONTINUE; MOVE WS-M03B-FLDT to CUSTOMER-RECORD (line 388, unconditional) | 2000-CUSTFILE-GET lines 379-388 |
| 33 | Any CUST read error (incl not found) | WS-M03B-RC = OTHER   | DISPLAY 'ERROR READING CUSTFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; PERFORM 9999-ABEND-PROGRAM | 2000-CUSTFILE-GET lines 382-385 |

Note: CUST key = XREF-CUST-ID. There is no "not found" (RC='23') tolerance -- any
non-zero return code triggers abend.

### Account File Read Routing

| #  | Rule                               | Condition              | Action                                                        | Source Location          |
| -- | ---------------------------------- | ---------------------- | ------------------------------------------------------------- | ------------------------ |
| 34 | Successful keyed ACCT read         | WS-M03B-RC = '00'      | CONTINUE; MOVE WS-M03B-FLDT to ACCOUNT-RECORD (line 412, unconditional) | 3000-ACCTFILE-GET lines 403-412 |
| 35 | Any ACCT read error (incl not found) | WS-M03B-RC = OTHER   | DISPLAY 'ERROR READING ACCTFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; PERFORM 9999-ABEND-PROGRAM | 3000-ACCTFILE-GET lines 406-409 |

Note: ACCT key = XREF-ACCT-ID. Same zero-tolerance policy as CUSTFILE.

### File Open Validation

| #  | Rule                               | Condition                     | Action                                                        | Source Location              |
| -- | ---------------------------------- | ----------------------------- | ------------------------------------------------------------- | ---------------------------- |
| 36 | Successful TRNXFILE open           | WS-M03B-RC = '00' OR '04'    | CONTINUE                                                      | 8100-TRNXFILE-OPEN line 736  |
| 37 | Failed TRNXFILE open               | WS-M03B-RC = OTHER            | DISPLAY 'ERROR OPENING TRNXFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; PERFORM 9999-ABEND-PROGRAM | 8100-TRNXFILE-OPEN lines 739-741 |
| 38 | Initial TRNXFILE sequential read after open | WS-M03B-RC = '00' OR '04' | CONTINUE; MOVE WS-M03B-FLDT TO TRNX-RECORD; MOVE TRNX-CARD-NUM TO WS-SAVE-CARD; initialise CR-CNT=1, TR-CNT=0 | 8100-TRNXFILE-OPEN lines 748-762 |
| 39 | Failed initial TRNXFILE read       | WS-M03B-RC = OTHER            | DISPLAY 'ERROR READING TRNXFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; PERFORM 9999-ABEND-PROGRAM | 8100-TRNXFILE-OPEN lines 751-753 |
| 40 | Successful XREFFILE open           | WS-M03B-RC = '00' OR '04'    | CONTINUE; set WS-FL-DD='CUSTFILE'; GO TO 0000-START           | 8200-XREFFILE-OPEN lines 771-780 |
| 41 | Failed XREFFILE open               | WS-M03B-RC = OTHER            | DISPLAY 'ERROR OPENING XREFFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; PERFORM 9999-ABEND-PROGRAM | 8200-XREFFILE-OPEN lines 774-776 |
| 42 | Successful CUSTFILE open           | WS-M03B-RC = '00' OR '04'    | CONTINUE; set WS-FL-DD='ACCTFILE'; GO TO 0000-START           | 8300-CUSTFILE-OPEN lines 789-798 |
| 43 | Failed CUSTFILE open               | WS-M03B-RC = OTHER            | DISPLAY 'ERROR OPENING CUSTFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; PERFORM 9999-ABEND-PROGRAM | 8300-CUSTFILE-OPEN lines 792-794 |
| 44 | Successful ACCTFILE open           | WS-M03B-RC = '00' OR '04'    | CONTINUE; GO TO 1000-MAINLINE                                  | 8400-ACCTFILE-OPEN lines 807-815 |
| 45 | Failed ACCTFILE open               | WS-M03B-RC = OTHER            | DISPLAY 'ERROR OPENING ACCTFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; PERFORM 9999-ABEND-PROGRAM | 8400-ACCTFILE-OPEN lines 810-812 |

### File Close Validation

| #  | Rule                               | Condition                     | Action                                                        | Source Location              |
| -- | ---------------------------------- | ----------------------------- | ------------------------------------------------------------- | ---------------------------- |
| 46 | Successful TRNXFILE close          | WS-M03B-RC = '00' OR '04'    | CONTINUE                                                      | 9100-TRNXFILE-CLOSE line 862 |
| 47 | Failed TRNXFILE close              | WS-M03B-RC = OTHER            | DISPLAY 'ERROR CLOSING TRNXFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; PERFORM 9999-ABEND-PROGRAM | 9100-TRNXFILE-CLOSE lines 865-867 |
| 48 | Successful XREFFILE close          | WS-M03B-RC = '00' OR '04'    | CONTINUE                                                      | 9200-XREFFILE-CLOSE line 879 |
| 49 | Failed XREFFILE close              | WS-M03B-RC = OTHER            | DISPLAY 'ERROR CLOSING XREFFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; PERFORM 9999-ABEND-PROGRAM | 9200-XREFFILE-CLOSE lines 882-884 |
| 50 | Successful CUSTFILE close          | WS-M03B-RC = '00' OR '04'    | CONTINUE                                                      | 9300-CUSTFILE-CLOSE line 895 |
| 51 | Failed CUSTFILE close              | WS-M03B-RC = OTHER            | DISPLAY 'ERROR CLOSING CUSTFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; PERFORM 9999-ABEND-PROGRAM | 9300-CUSTFILE-CLOSE lines 898-900 |
| 52 | Successful ACCTFILE close          | WS-M03B-RC = '00' OR '04'    | CONTINUE                                                      | 9400-ACCTFILE-CLOSE line 911 |
| 53 | Failed ACCTFILE close              | WS-M03B-RC = OTHER            | DISPLAY 'ERROR CLOSING ACCTFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; PERFORM 9999-ABEND-PROGRAM | 9400-ACCTFILE-CLOSE lines 914-916 |

### Statement Content Derivation (5000-CREATE-STATEMENT)

| #  | Rule                               | Condition / Input              | Action / Output                                                    | Source Location              |
| -- | ---------------------------------- | ------------------------------ | ------------------------------------------------------------------ | ---------------------------- |
| 54 | Initialise statement lines         | Entry (unconditional)          | INITIALIZE STATEMENT-LINES (clears all ST-* fields before use)     | 5000-CREATE-STATEMENT line 459 |
| 55 | Write start-of-statement marker    | Entry (unconditional)          | WRITE FD-STMTFILE-REC FROM ST-LINE0 ('***...START OF STATEMENT...***', 80 asterisks/text) | 5000-CREATE-STATEMENT line 460 |
| 56 | HTML header written before name/address | Entry (unconditional)     | PERFORM 5100-WRITE-HTML-HEADER THRU 5100-EXIT                      | 5000-CREATE-STATEMENT line 461 |
| 57 | Customer full name construction    | CUST-FIRST-NAME, CUST-MIDDLE-NAME, CUST-LAST-NAME delimited by ' ' (single space) | STRING into ST-NAME (75 chars); name parts concatenated with single-space separators; each part truncated at first space | 5000-CREATE-STATEMENT lines 462-469 |
| 58 | Address line 1 and 2 (verbatim)    | CUST-ADDR-LINE-1, CUST-ADDR-LINE-2 | MOVE to ST-ADD1 (50 chars) and ST-ADD2 (50 chars)              | 5000-CREATE-STATEMENT lines 470-471 |
| 59 | Address line 3 construction        | CUST-ADDR-LINE-3, CUST-ADDR-STATE-CD, CUST-ADDR-COUNTRY-CD, CUST-ADDR-ZIP delimited by ' ' (single space) | STRING into ST-ADD3 (80 chars); each field truncated at first space | 5000-CREATE-STATEMENT lines 472-481 |
| 60 | Account ID on statement            | ACCT-ID                        | MOVE to ST-ACCT-ID (20 chars); displayed as 'Account ID         : [id]' | 5000-CREATE-STATEMENT line 483  |
| 61 | Current balance on statement       | ACCT-CURR-BAL (PIC S9(10)V99 from CVACT01Y) | MOVE to ST-CURR-BAL (PIC 9(9).99-); displayed as 'Current Balance    : [bal]'. **Data truncation risk**: ACCT-CURR-BAL has 10 integer digits; ST-CURR-BAL holds only 9. Balances >= $1,000,000,000.00 will silently truncate the leading integer digit. | 5000-CREATE-STATEMENT line 484 |
| 62 | FICO score on statement            | CUST-FICO-CREDIT-SCORE (3-digit) | MOVE to ST-FICO-SCORE (20 chars); displayed as 'FICO Score         : [score]' | 5000-CREATE-STATEMENT line 485 |
| 63 | HTML name/address/details written  | After plain fields set         | PERFORM 5200-WRITE-HTML-NMADBS THRU 5200-EXIT                      | 5000-CREATE-STATEMENT line 486 |
| 64 | Plain-text header lines written in fixed sequence | After both HTML performs | WRITE ST-LINE1 (name), ST-LINE2 (add1), ST-LINE3 (add2), ST-LINE4 (add3), ST-LINE5 (dashes), ST-LINE6 ('Basic Details'), ST-LINE5 (dashes), ST-LINE7 (Account ID), ST-LINE8 (Balance), ST-LINE9 (FICO), ST-LINE10 (dashes), ST-LINE11 ('TRANSACTION SUMMARY'), ST-LINE12 (dashes), ST-LINE13 (column headers), ST-LINE12 (dashes) | 5000-CREATE-STATEMENT lines 488-502 (15 writes total) |

Note: ST-LINE5 (80 dashes) appears twice in the sequence (lines 492 and 494) flanking
the 'Basic Details' heading. ST-LINE12 (80 dashes) appears twice in the sequence (lines
500 and 502) flanking the transaction column header line. This matches the visual
separator convention in the plain-text output.

### HTML Header Content (5100-WRITE-HTML-HEADER)

5100-WRITE-HTML-HEADER writes 22 HTML records to HTML-FILE using 88-level constant
values in HTML-FIXED-LN and the variable HTML-L11 (account number row). The paragraph
embeds hardcoded bank identity information as literal VALUES on the 88-level conditions.

| #  | Rule                               | Condition / Input              | Action / Output                                                    | Source Location              |
| -- | ---------------------------------- | ------------------------------ | ------------------------------------------------------------------ | ---------------------------- |
| 72 | Write HTML boilerplate header      | Entry (unconditional)          | Writes HTML-L01 through HTML-L08: `<!DOCTYPE html>`, `<html lang="en">`, `<head>`, `<meta charset="utf-8">`, `<title>HTML Table Layout</title>`, `</head>`, `<body style="margin:0px;">`, `<table align="center" frame="box" style="width:70%; font:12px Segoe UI,sans-serif;">` | 5100-WRITE-HTML-HEADER lines 508-523 |
| 73 | Write account number heading row   | ACCT-ID from ACCOUNT-RECORD    | MOVE ACCT-ID TO L11-ACCT; WRITE HTML-L11 (`<h3>Statement for Account Number: [ACCT-ID]</h3>`) within a colspan=3 blue header cell (`background-color:#1d1d96b3`) | 5100-WRITE-HTML-HEADER lines 529-534 |
| 74 | Hardcoded bank name on statement   | Value literal (unconditional)  | Writes HTML-L16: `<p style="font-size:16px">Bank of XYZ</p>` -- bank name is a hardcoded literal in the 88-level VALUE clause, not a parameter or configuration field | 5100-WRITE-HTML-HEADER lines 539-540 |
| 75 | Hardcoded bank address on statement | Value literal (unconditional) | Writes HTML-L17: `<p>410 Terry Ave N</p>` and HTML-L18: `<p>Seattle WA 99999</p>` -- bank address is hardcoded as literal VALUES, not configurable at runtime | 5100-WRITE-HTML-HEADER lines 541-544 |
| 76 | Write table header structure       | Entry (unconditional)          | Writes HTML-L22-35 (background-color:#f2f2f2 cell), HTML-L30-42 (background-color:#33FFD1 header row), HTML-L43 ('Transaction Summary' heading), column header cells HTML-L47/L48 (Tran ID, 25% green), HTML-L50/L51 (Tran Details, 55% green), HTML-L53/L54 (Amount, 20% right-aligned green) | 5100-WRITE-HTML-HEADER lines 535-553 |

Note: Rules 74 and 75 identify a hardcoded dependency. If the bank name or address
changes, the source code VALUE clause for HTML-L16, HTML-L17, HTML-L18 must be
modified and the program recompiled. There is no lookup table, configuration file,
or parameter for these values.

### Transaction Line Write (6000-WRITE-TRANS)

| #  | Rule                               | Input fields                   | Output                                                             | Source Location          |
| -- | ---------------------------------- | ------------------------------ | ------------------------------------------------------------------ | ------------------------ |
| 65 | Write one transaction plain-text   | TRNX-ID -> ST-TRANID (16 chars); TRNX-DESC -> ST-TRANDT (49 chars); TRNX-AMT -> ST-TRANAMT (PIC Z(9).99-) | WRITE FD-STMTFILE-REC FROM ST-LINE14 (format: Tran-ID + space + Tran-Details + '$' + amount) | 6000-WRITE-TRANS lines 676-679 |
| 66 | Write one transaction HTML row     | ST-TRANID, ST-TRANDT, ST-TRANAMT each wrapped with `<p>...</p>` using DELIMITED BY '*' | WRITE FD-HTMLFILE-REC: `<tr>` (HTML-LTRS), cell1 `<td style="width:25%;...text-align:left">` (HTML-L58) + `<p>` + ST-TRANID + `</p>` + `</td>`, cell2 `<td style="width:55%;...text-align:left">` (HTML-L61) + `<p>` + ST-TRANDT + `</p>` + `</td>`, cell3 `<td style="width:20%;...text-align:right">` (HTML-L64) + `<p>` + ST-TRANAMT + `</p>` + `</td>`, `</tr>` (HTML-LTRE); 11 records total | 6000-WRITE-TRANS lines 681-721 |
| 67 | STRING delimiter for HTML cell content | `'*'` (asterisk) used as STRING delimiter for all three HTML cell STRING operations | Because asterisk does not appear in Tran-ID, Tran-Details, or Amount fields, the full field value is included with no truncation. Distinct from the double-space delimiter used in 5200-WRITE-HTML-NMADBS for name/address. | 6000-WRITE-TRANS lines 687-715 |

### HTML Name/Address Block Truncation (5200-WRITE-HTML-NMADBS)

| #  | Rule                               | Condition                      | Action                                                             | Source Location              |
| -- | ---------------------------------- | ------------------------------ | ------------------------------------------------------------------ | ---------------------------- |
| 68 | Customer name truncated at double space in HTML | ST-NAME DELIMITED BY '  ' (two consecutive spaces) | STRING embeds name into HTML `<p>` tag; name content is truncated at the first occurrence of two consecutive spaces | 5200-WRITE-HTML-NMADBS lines 562-567 |
| 69 | Address line 1 truncated at double space in HTML | ST-ADD1 DELIMITED BY '  ' | STRING embeds add1 into `<p>` tag; content truncated at double space | 5200-WRITE-HTML-NMADBS lines 570-575 |
| 70 | Address line 2 truncated at double space in HTML | ST-ADD2 DELIMITED BY '  ' | STRING embeds add2 into `<p>` tag; content truncated at double space | 5200-WRITE-HTML-NMADBS lines 577-584 |
| 71 | Address line 3 truncated at double space in HTML | ST-ADD3 DELIMITED BY '  ' | STRING embeds add3 into `<p>` tag; content truncated at double space | 5200-WRITE-HTML-NMADBS lines 585-592 |

Note: Rules 68-71 apply the double-space truncation to HTML output only. The plain-text
fields (ST-ADD1, ST-ADD2 in 5000-CREATE-STATEMENT) are MOVEd verbatim. The address
fields in 5200 are terminated by `'  ' DELIMITED BY SIZE` (a literal double-space) after
the truncation point to ensure the HTML element is well-formed.

## Calculations

| Calculation         | Formula / Logic                                                            | Input Fields                    | Output Field     | Source Location                 |
| ------------------- | -------------------------------------------------------------------------- | ------------------------------- | ---------------- | ------------------------------- |
| TIOT pointer bump   | BUMP-TIOT = BUMP-TIOT + LENGTH OF TIOT-BLOCK (initial); then + LENGTH OF TIOT-SEG per entry | BUMP-TIOT (BINARY S9(08)), TIOT-BLOCK / TIOT-SEG lengths | TIOT-INDEX (POINTER alias of BUMP-TIOT) | Lines 272, 283 |
| XREF-CUST-ID key length | COMPUTE WS-M03B-KEY-LN = LENGTH OF XREF-CUST-ID (dynamic; prior MOVE ZERO resets field) | XREF-CUST-ID                    | WS-M03B-KEY-LN   | 2000-CUSTFILE-GET line 374      |
| XREF-ACCT-ID key length | COMPUTE WS-M03B-KEY-LN = LENGTH OF XREF-ACCT-ID (dynamic; prior MOVE ZERO resets field) | XREF-ACCT-ID                    | WS-M03B-KEY-LN   | 3000-ACCTFILE-GET line 398      |
| Total expenditure   | WS-TOTAL-AMT = WS-TOTAL-AMT + TRNX-AMT (accumulated per card match; reset to ZERO before each account) | TRNX-AMT (PIC S9(09)V99 DISPLAY per COSTM01); WS-TOTAL-AMT is COMP-3 accumulator | WS-TOTAL-AMT (PIC S9(9)V99 COMP-3) | 4000-TRNXFILE-GET line 429; reset at 1000-MAINLINE line 325 |
| Total to output field | MOVE WS-TOTAL-AMT TO WS-TRN-AMT; MOVE WS-TRN-AMT TO ST-TOTAL-TRAMT       | WS-TOTAL-AMT                    | ST-TOTAL-TRAMT (PIC Z(9).99-) | 4000-TRNXFILE-GET lines 433-434 |

## Error Handling

| Condition                          | Action                                                                               | Return Code   | Source Location           |
| ---------------------------------- | ------------------------------------------------------------------------------------ | ------------- | ------------------------- |
| ERROR OPENING TRNXFILE             | DISPLAY 'ERROR OPENING TRNXFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; CALL CEE3ABD | OTHER (not 00/04) | 8100-TRNXFILE-OPEN lines 739-741 |
| ERROR READING TRNXFILE (initial)   | DISPLAY 'ERROR READING TRNXFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; CALL CEE3ABD | OTHER (not 00/04) | 8100-TRNXFILE-OPEN lines 751-753 |
| ERROR READING TRNXFILE (in loop)   | DISPLAY 'ERROR READING TRNXFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; CALL CEE3ABD | OTHER (not 00/10) | 8500-READTRNX-READ lines 844-846 |
| ERROR OPENING XREFFILE             | DISPLAY 'ERROR OPENING XREFFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; CALL CEE3ABD | OTHER (not 00/04) | 8200-XREFFILE-OPEN lines 774-776 |
| ERROR READING XREFFILE             | DISPLAY 'ERROR READING XREFFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; CALL CEE3ABD | OTHER (not 00/10) | 1000-XREFFILE-GET-NEXT lines 359-361 |
| ERROR OPENING CUSTFILE             | DISPLAY 'ERROR OPENING CUSTFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; CALL CEE3ABD | OTHER (not 00/04) | 8300-CUSTFILE-OPEN lines 792-794 |
| ERROR READING CUSTFILE             | DISPLAY 'ERROR READING CUSTFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; CALL CEE3ABD | OTHER (not 00)    | 2000-CUSTFILE-GET lines 383-385 |
| ERROR OPENING ACCTFILE             | DISPLAY 'ERROR OPENING ACCTFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; CALL CEE3ABD | OTHER (not 00/04) | 8400-ACCTFILE-OPEN lines 810-812 |
| ERROR READING ACCTFILE             | DISPLAY 'ERROR READING ACCTFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; CALL CEE3ABD | OTHER (not 00)    | 3000-ACCTFILE-GET lines 407-409 |
| ERROR CLOSING TRNXFILE             | DISPLAY 'ERROR CLOSING TRNXFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; CALL CEE3ABD | OTHER (not 00/04) | 9100-TRNXFILE-CLOSE lines 865-867 |
| ERROR CLOSING XREFFILE             | DISPLAY 'ERROR CLOSING XREFFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; CALL CEE3ABD | OTHER (not 00/04) | 9200-XREFFILE-CLOSE lines 882-884 |
| ERROR CLOSING CUSTFILE             | DISPLAY 'ERROR CLOSING CUSTFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; CALL CEE3ABD | OTHER (not 00/04) | 9300-CUSTFILE-CLOSE lines 898-900 |
| ERROR CLOSING ACCTFILE             | DISPLAY 'ERROR CLOSING ACCTFILE'; DISPLAY 'RETURN CODE: ' WS-M03B-RC; CALL CEE3ABD | OTHER (not 00/04) | 9400-ACCTFILE-CLOSE lines 914-916 |
| Generic abend                      | DISPLAY 'ABENDING PROGRAM'; CALL 'CEE3ABD' (LE abnormal termination)                | n/a           | 9999-ABEND-PROGRAM line 923 |

Note: RC '00' = success; RC '04' = treated as success (warning); RC '10' = end of file
(only tolerated on sequential reads, not on opens or key reads). CUSTFILE and ACCTFILE
key reads do not tolerate RC='23' (record not found) -- a missing customer or account
will abend the program.

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. **PROCEDURE DIVISION entry (inline)** -- SET ADDRESS chain for PSA/TCB/TIOT; display job/step name from TIOT; walk TIOT entries displaying each DD name (including post-loop display of final/terminating entry); OPEN OUTPUT STMT-FILE HTML-FILE; INITIALIZE WS-TRNX-TABLE WS-TRN-TBL-CNTR
2. **0000-START** -- Dispatch paragraph (uses ALTER/GO TO). First entered with WS-FL-DD='TRNXFILE'. Called repeatedly via GO TO from close of each open paragraph to chain opens in sequence.
3. **8100-TRNXFILE-OPEN** -- CALL CBSTM03B (open TRNXFILE); CALL CBSTM03B (initial sequential read); initialise CR-CNT=1, TR-CNT=0, WS-SAVE-CARD; set WS-FL-DD='READTRNX'; GO TO 0000-START
4. **8500-READTRNX-READ** -- Self-loop via GO TO until EOF; populates 2D array WS-TRNX-TABLE; WS-SAVE-CARD updated on every iteration; on EOF: finalise WS-TRCT(CR-CNT); set WS-FL-DD='XREFFILE'; GO TO 0000-START
5. **8200-XREFFILE-OPEN** -- CALL CBSTM03B (open XREFFILE); set WS-FL-DD='CUSTFILE'; GO TO 0000-START
6. **8300-CUSTFILE-OPEN** -- CALL CBSTM03B (open CUSTFILE); set WS-FL-DD='ACCTFILE'; GO TO 0000-START
7. **8400-ACCTFILE-OPEN** -- CALL CBSTM03B (open ACCTFILE); GO TO 1000-MAINLINE
8. **1000-MAINLINE** -- PERFORM UNTIL END-OF-FILE='Y': PERFORM 1000-XREFFILE-GET-NEXT, conditionally PERFORM 2000-CUSTFILE-GET, 3000-ACCTFILE-GET, 5000-CREATE-STATEMENT, 4000-TRNXFILE-GET
9. **1000-XREFFILE-GET-NEXT** -- CALL CBSTM03B (sequential read XREFFILE); on RC='10' sets END-OF-FILE='Y'; on OTHER abends; MOVE WS-M03B-FLDT TO CARD-XREF-RECORD unconditionally (even on EOF)
10. **2000-CUSTFILE-GET** -- CALL CBSTM03B (keyed read CUSTFILE by XREF-CUST-ID); on non-zero RC abends; MOVE WS-M03B-FLDT TO CUSTOMER-RECORD unconditionally
11. **3000-ACCTFILE-GET** -- CALL CBSTM03B (keyed read ACCTFILE by XREF-ACCT-ID); on non-zero RC abends; MOVE WS-M03B-FLDT TO ACCOUNT-RECORD unconditionally
12. **5000-CREATE-STATEMENT** -- INITIALIZE STATEMENT-LINES; WRITE ST-LINE0 (start marker); PERFORM 5100-WRITE-HTML-HEADER THRU 5100-EXIT; populate ST-* fields; PERFORM 5200-WRITE-HTML-NMADBS THRU 5200-EXIT; WRITE plain-text lines ST-LINE1 through ST-LINE12 (15 writes in fixed sequence)
13. **5100-WRITE-HTML-HEADER** -- Writes 22 HTML records: HTML boilerplate (DOCTYPE through table open), account-number heading row (HTML-L11 with ACCT-ID), hardcoded bank name 'Bank of XYZ' (HTML-L16), hardcoded bank address '410 Terry Ave N' / 'Seattle WA 99999' (HTML-L17/L18), table column header structure (Transaction Summary heading, Tran ID / Tran Details / Amount column headers with colour coding); EXIT at 5100-EXIT
14. **5200-WRITE-HTML-NMADBS** -- Writes HTML name (DELIMITED BY '  '), address lines 1-3 (DELIMITED BY '  '), basic details (Account ID, Current Balance, FICO Score), and transaction summary column headers; EXIT at 5200-EXIT
15. **4000-TRNXFILE-GET** -- Searches 2D array for cards matching XREF-CARD-NUM; for each match: inner PERFORM VARYING writes each transaction via 6000-WRITE-TRANS; accumulates WS-TOTAL-AMT; writes ST-LINE12 (separator), ST-LINE14A (total), ST-LINE15 (end marker) plus 8 HTML closing lines
16. **6000-WRITE-TRANS** -- Writes one transaction line to STMT-FILE (ST-LINE14) and one HTML table row (11 records: `<tr>`, 3x cell-open/content/`</td>`, `</tr>` using DELIMITED BY '*') to HTML-FILE
17. **PERFORM 9100-TRNXFILE-CLOSE** -- CALL CBSTM03B (close TRNXFILE)
18. **PERFORM 9200-XREFFILE-CLOSE** -- CALL CBSTM03B (close XREFFILE)
19. **PERFORM 9300-CUSTFILE-CLOSE** -- CALL CBSTM03B (close CUSTFILE)
20. **PERFORM 9400-ACCTFILE-CLOSE** -- CALL CBSTM03B (close ACCTFILE)
21. **CLOSE STMT-FILE HTML-FILE** -- Close output files
22. **9999-GOBACK** -- GOBACK (normal program termination)
23. **9999-ABEND-PROGRAM** -- DISPLAY 'ABENDING PROGRAM'; CALL 'CEE3ABD' (LE abend, abnormal termination)

### Subroutine Interface (CBSTM03B)

All VSAM file I/O is delegated to CBSTM03B via the WS-M03B-AREA parameter block:

| Parameter field  | PIC         | Purpose                                        |
| ---------------- | ----------- | ---------------------------------------------- |
| WS-M03B-DD       | X(08)       | DD name to operate on: 'TRNXFILE', 'XREFFILE', 'CUSTFILE', 'ACCTFILE' |
| WS-M03B-OPER     | X(01)       | Operation: 'O'=Open, 'C'=Close, 'R'=Read seq, 'K'=Read by Key, 'W'=Write, 'Z'=Rewrite |
| WS-M03B-RC       | X(02)       | Return code from subroutine: '00'=OK, '04'=warn, '10'=EOF, '23'=not found, OTHER=error |
| WS-M03B-KEY      | X(25)       | Key value for keyed reads (CUSTFILE: XREF-CUST-ID; ACCTFILE: XREF-ACCT-ID) |
| WS-M03B-KEY-LN   | S9(4)       | Key length (COMPUTE from LENGTH OF key field)  |
| WS-M03B-FLDT     | X(1000)     | Record data buffer (in for write, out for read) |

### Array Dimensions and Limits

| Dimension        | Limit | COBOL definition                                          |
| ---------------- | ----- | --------------------------------------------------------- |
| Card slots       | 51    | WS-CARD-TBL OCCURS 51 TIMES (indexed by CR-CNT / CR-JMP) |
| Transactions per card | 10 | WS-TRAN-TBL OCCURS 10 TIMES (indexed by TR-CNT / TR-JMP) |

If more than 51 distinct card numbers exist in TRNXFILE, or more than 10 transactions
per card are present, the array subscript will overflow without a run-time bounds check
in this program. This is a latent capacity constraint.

### TRNX-RECORD Layout (COSTM01 copybook)

TRNX-RECORD is defined by copybook COSTM01 (the "altered layout for reporting"). The
layout places card number first, which matches the JCL SORT output order:

| Field              | PIC              | Offset | Notes                                            |
| ------------------ | ---------------- | ------ | ------------------------------------------------ |
| TRNX-CARD-NUM      | X(16)            | 1      | Sort key 1 (card number first after JCL SORT)   |
| TRNX-ID            | X(16)            | 17     | Sort key 2 (transaction ID)                      |
| TRNX-TYPE-CD       | X(02)            | 33     | Start of TRNX-REST (318 bytes total)             |
| TRNX-CAT-CD        | 9(04)            | 35     |                                                  |
| TRNX-SOURCE        | X(10)            | 39     |                                                  |
| TRNX-DESC          | X(100)           | 49     | Copied to ST-TRANDT in 6000-WRITE-TRANS          |
| TRNX-AMT           | S9(09)V99        | 149    | DISPLAY (no COMP/COMP-3); added to WS-TOTAL-AMT  |
| TRNX-MERCHANT-ID   | 9(09)            | 160    |                                                  |
| TRNX-MERCHANT-NAME | X(50)            | 169    |                                                  |
| TRNX-MERCHANT-CITY | X(50)            | 219    |                                                  |
| TRNX-MERCHANT-ZIP  | X(10)            | 269    |                                                  |
| TRNX-ORIG-TS       | X(26)            | 279    |                                                  |
| TRNX-PROC-TS       | X(26)            | 305    |                                                  |
| FILLER             | X(20)            | 331    |                                                  |

WS-TRAN-REST (PIC X(318) in the 2D array) corresponds exactly to TRNX-REST bytes 33-350
of TRNX-RECORD. TRNX-AMT is a sub-field of TRNX-REST, so when 4000-TRNXFILE-GET moves
WS-TRAN-REST back to TRNX-REST and then references TRNX-AMT, the amount is correctly
extracted via the COSTM01 field overlay.
