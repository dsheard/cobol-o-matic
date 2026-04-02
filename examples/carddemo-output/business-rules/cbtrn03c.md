---
type: business-rules
subtype: program
program: CBTRN03C
program_type: batch
status: draft
confidence: high
last_pass: 5
calls:
- CEE3ABD
called_by: []
uses_copybooks:
- CVACT03Y
- CVTRA03Y
- CVTRA04Y
- CVTRA05Y
- CVTRA07Y
reads:
- DATE-PARMS-FILE
- TRANCATG-FILE
- TRANSACT-FILE
- TRANTYPE-FILE
- XREF-FILE
writes:
- REPORT-FILE
db_tables: []
transactions: []
mq_queues: []
---

# CBTRN03C -- Business Rules

## Program Purpose

CBTRN03C is a batch COBOL program that prints a transaction detail report (named "Daily Transaction Report") for the CardDemo credit card application. It reads a date-range parameter file to determine a reporting window, then reads all transaction records sequentially, filters them by the date range, enriches each transaction with account cross-reference data, a transaction type description, and a transaction category description, and writes a formatted report with per-page totals, per-account totals, and a grand total. The report is 133 characters wide and groups lines by card number with subtotals at each card boundary and at every 20-line page break.

## Input / Output

| Direction | Resource         | Type | Description                                                                         |
| --------- | ---------------- | ---- | ----------------------------------------------------------------------------------- |
| IN        | TRANSACT-FILE    | File | Sequential file of transaction records (TRAN-RECORD, 350 bytes). Key fields: TRAN-PROC-TS, TRAN-CARD-NUM, TRAN-TYPE-CD, TRAN-CAT-CD, TRAN-AMT, TRAN-ID, TRAN-SOURCE. FD layout: FD-TRANS-DATA (304 bytes) + FD-TRAN-PROC-TS (26 bytes) + FD-FILLER (20 bytes). |
| IN        | XREF-FILE        | File | KSDS indexed by card number (FD-XREF-CARD-NUM, 16 bytes). Maps card number to customer ID and account ID (XREF-ACCT-ID). |
| IN        | TRANTYPE-FILE    | File | KSDS indexed by transaction type code (FD-TRAN-TYPE, 2 bytes). Provides TRAN-TYPE-DESC (50 bytes). |
| IN        | TRANCATG-FILE    | File | KSDS indexed by composite key (FD-TRAN-CAT-KEY = FD-TRAN-TYPE-CD X(2) + FD-TRAN-CAT-CD 9(4)). Provides TRAN-CAT-TYPE-DESC. |
| IN        | DATE-PARMS-FILE  | File | Sequential file; first record contains WS-START-DATE (X(10)) at positions 1-10 and WS-END-DATE (X(10)) at positions 12-21 (separated by one filler byte). FD record is X(80). |
| OUT       | REPORT-FILE      | File | Sequential output file (FD-REPTFILE-REC, 133 bytes). Contains report headers, transaction detail lines, page totals, account totals, and grand total. |

## Business Rules

### Date Range Filtering

| #  | Rule                             | Condition                                                                             | Action                                                               | Source Location          |
| -- | -------------------------------- | ------------------------------------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------ |
| 1  | Read reporting date range        | Always on startup                                                                    | Read DATE-PARMS-FILE INTO WS-DATEPARM-RECORD; extract WS-START-DATE (positions 1-10) and WS-END-DATE (positions 12-21) from first record. | 0550-DATEPARM-READ (line 220) |
| 2  | Skip transactions outside window | TRAN-PROC-TS(1:10) < WS-START-DATE OR TRAN-PROC-TS(1:10) > WS-END-DATE              | NEXT SENTENCE -- exits the entire PERFORM UNTIL loop (see Notes). Transaction is bypassed; not written to report and not included in any totals. All subsequent transactions in the file are also skipped. | Main loop, lines 173-178 |
| 3  | Include transactions inside window | TRAN-PROC-TS(1:10) >= WS-START-DATE AND TRAN-PROC-TS(1:10) <= WS-END-DATE         | CONTINUE -- transaction proceeds to lookup and report-write processing. | Main loop, lines 173-175 |

### Account Break Detection

| #  | Rule                              | Condition                                                         | Action                                                                                    | Source Location          |
| -- | --------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ------------------------ |
| 4  | Detect new card number            | WS-CURR-CARD-NUM NOT= TRAN-CARD-NUM                               | If not first record (WS-FIRST-TIME = 'N'), write account totals line (plus blank separator) and reset WS-ACCOUNT-TOTAL to zero. Then update WS-CURR-CARD-NUM and perform XREF lookup to resolve account ID. | Main loop, lines 181-188 |
| 5  | First-record flag                 | WS-FIRST-TIME = 'Y' on entry to 1100-WRITE-TRANSACTION-REPORT     | Set WS-FIRST-TIME to 'N', copy WS-START-DATE to REPT-START-DATE and WS-END-DATE to REPT-END-DATE, then PERFORM 1120-WRITE-HEADERS (writes 4 lines: report name, blank line, TRANSACTION-HEADER-1, TRANSACTION-HEADER-2 separator). | 1100-WRITE-TRANSACTION-REPORT, lines 275-280 |

### Page Break Logic

| #  | Rule                           | Condition                                                                 | Action                                                                                         | Source Location                           |
| -- | ------------------------------ | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ----------------------------------------- |
| 6  | Page break at 20-line intervals | FUNCTION MOD(WS-LINE-COUNTER, WS-PAGE-SIZE) = 0  (WS-PAGE-SIZE = 20)    | Perform 1110-WRITE-PAGE-TOTALS (writes page total line + blank separator, accumulates to grand total, resets page total to zero -- increments WS-LINE-COUNTER by 2), then perform 1120-WRITE-HEADERS (writes 4 header lines, increments WS-LINE-COUNTER by 4). | 1100-WRITE-TRANSACTION-REPORT, lines 282-285 |
| 7  | Page size constant             | WS-PAGE-SIZE VALUE 20                                                     | Hard-coded; a page is 20 lines. WS-LINE-COUNTER is incremented for all written lines including report headers, blank separators, total lines, and detail lines -- not detail lines only. | WORKING-STORAGE, line 131                 |
| 8  | First-call MOD check ordering  | First-time headers are written (incrementing WS-LINE-COUNTER to 4) BEFORE the MOD check executes | MOD(4, 20) = 4 (not 0), so no spurious page-break trigger on the first transaction. The first-time check at lines 275-280 precedes the MOD check at line 282 within 1100-WRITE-TRANSACTION-REPORT. | 1100-WRITE-TRANSACTION-REPORT, lines 275-285 |

### Reference Data Lookups

| #  | Rule                              | Condition                              | Action                                                                                                 | Source Location        |
| -- | --------------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------ | ---------------------- |
| 9  | Card-to-account cross-reference   | Called once per unique card number     | RANDOM READ on XREF-FILE keyed by FD-XREF-CARD-NUM (set from TRAN-CARD-NUM). Reads into CARD-XREF-RECORD; retrieves XREF-ACCT-ID (11-digit account ID) used in the detail report line. | 1500-A-LOOKUP-XREF (line 484) |
| 10 | Transaction type description      | Called for every in-range transaction  | RANDOM READ on TRANTYPE-FILE keyed by FD-TRAN-TYPE (set from TRAN-TYPE-CD). Reads into TRAN-TYPE-RECORD; retrieves TRAN-TYPE-DESC (50 chars) which is moved to TRAN-REPORT-TYPE-DESC (truncated to 15 chars in detail report). | 1500-B-LOOKUP-TRANTYPE (line 494) |
| 11 | Transaction category description  | Called for every in-range transaction  | RANDOM READ on TRANCATG-FILE keyed by composite FD-TRAN-CAT-KEY (FD-TRAN-TYPE-CD + FD-TRAN-CAT-CD set from TRAN-TYPE-CD and TRAN-CAT-CD). Reads into TRAN-CAT-RECORD; retrieves TRAN-CAT-TYPE-DESC (50 chars) moved to TRAN-REPORT-CAT-DESC (truncated to 29 chars in detail report). | 1500-C-LOOKUP-TRANCATG (line 504) |

### Report Detail Line Assembly

| #  | Rule                                   | Condition              | Action                                                                                                       | Source Location   |
| -- | -------------------------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------------ | ----------------- |
| 12 | Assemble detail report line            | For every included transaction | INITIALIZE TRANSACTION-DETAIL-REPORT, then MOVE: TRAN-ID -> TRAN-REPORT-TRANS-ID, XREF-ACCT-ID -> TRAN-REPORT-ACCOUNT-ID, TRAN-TYPE-CD -> TRAN-REPORT-TYPE-CD, TRAN-TYPE-DESC -> TRAN-REPORT-TYPE-DESC, TRAN-CAT-CD -> TRAN-REPORT-CAT-CD, TRAN-CAT-TYPE-DESC -> TRAN-REPORT-CAT-DESC, TRAN-SOURCE -> TRAN-REPORT-SOURCE, TRAN-AMT -> TRAN-REPORT-AMT. Write via 1111-WRITE-REPORT-REC; increment WS-LINE-COUNTER by 1. | 1120-WRITE-DETAIL (line 361) |

### Report Header Structure

| #  | Rule                                   | Condition              | Action                                                                                                       | Source Location   |
| -- | -------------------------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------------ | ----------------- |
| 13 | Header block on each new page          | Called by 1100-WRITE-TRANSACTION-REPORT on first transaction and at each page break | PERFORM 1120-WRITE-HEADERS: writes REPORT-NAME-HEADER (line 1), WS-BLANK-LINE (line 2), TRANSACTION-HEADER-1 column header (line 3), TRANSACTION-HEADER-2 separator (line 4). Each write increments WS-LINE-COUNTER; 4 total increments per header block. | 1120-WRITE-HEADERS (line 324) |
| 14 | Account total block at card break      | Called when WS-CURR-CARD-NUM != TRAN-CARD-NUM and WS-FIRST-TIME = 'N' | PERFORM 1120-WRITE-ACCOUNT-TOTALS: moves WS-ACCOUNT-TOTAL to REPT-ACCOUNT-TOTAL, writes REPORT-ACCOUNT-TOTALS line, then writes TRANSACTION-HEADER-2 blank separator. Resets WS-ACCOUNT-TOTAL to 0. Increments WS-LINE-COUNTER by 2. | 1120-WRITE-ACCOUNT-TOTALS (line 306) |
| 15 | Page total block at page boundary      | Called at every 20-line boundary (MOD check) and at EOF | PERFORM 1110-WRITE-PAGE-TOTALS: moves WS-PAGE-TOTAL to REPT-PAGE-TOTAL, writes REPORT-PAGE-TOTALS line, adds WS-PAGE-TOTAL to WS-GRAND-TOTAL, resets WS-PAGE-TOTAL to 0, writes TRANSACTION-HEADER-2 blank separator. Increments WS-LINE-COUNTER by 2. | 1110-WRITE-PAGE-TOTALS (line 293) |
| 16 | Grand total block at EOF               | Called once at EOF branch of main loop | PERFORM 1110-WRITE-GRAND-TOTALS: moves WS-GRAND-TOTAL to REPT-GRAND-TOTAL, writes REPORT-GRAND-TOTALS line. Does NOT increment WS-LINE-COUNTER (no ADD in this paragraph). | 1110-WRITE-GRAND-TOTALS (line 318) |

## Calculations

| Calculation       | Formula / Logic                                                               | Input Fields                       | Output Field       | Source Location                              |
| ----------------- | ----------------------------------------------------------------------------- | ---------------------------------- | ------------------ | -------------------------------------------- |
| Page running total | ADD TRAN-AMT TO WS-PAGE-TOTAL (accumulates within current page)             | TRAN-AMT                           | WS-PAGE-TOTAL      | 1100-WRITE-TRANSACTION-REPORT, line 287      |
| Account running total | ADD TRAN-AMT TO WS-ACCOUNT-TOTAL (accumulates for current card number)  | TRAN-AMT                           | WS-ACCOUNT-TOTAL   | 1100-WRITE-TRANSACTION-REPORT, line 288      |
| Grand running total | ADD WS-PAGE-TOTAL TO WS-GRAND-TOTAL (when page total flushes)              | WS-PAGE-TOTAL                      | WS-GRAND-TOTAL     | 1110-WRITE-PAGE-TOTALS, line 297             |
| Reset page total  | MOVE 0 TO WS-PAGE-TOTAL (after each page flush)                               | --                                 | WS-PAGE-TOTAL      | 1110-WRITE-PAGE-TOTALS, line 298             |
| Reset account total | MOVE 0 TO WS-ACCOUNT-TOTAL (after each account break write)               | --                                 | WS-ACCOUNT-TOTAL   | 1120-WRITE-ACCOUNT-TOTALS, line 310          |
| Page-break modulo | FUNCTION MOD(WS-LINE-COUNTER, WS-PAGE-SIZE) = 0; WS-PAGE-SIZE = 20          | WS-LINE-COUNTER, WS-PAGE-SIZE      | (boolean test)     | 1100-WRITE-TRANSACTION-REPORT, line 282      |
| EOF stale-data add (anomaly) | When END-OF-FILE = 'Y' is detected inside the loop after a READ returns EOF, TRAN-AMT is added to WS-PAGE-TOTAL and WS-ACCOUNT-TOTAL before writing page and grand totals. This ADD operates on the record buffer content from the last READ (which was an EOF read); the TRAN-AMT value is indeterminate and may corrupt the final totals. | TRAN-AMT (stale buffer), WS-PAGE-TOTAL, WS-ACCOUNT-TOTAL | WS-PAGE-TOTAL, WS-ACCOUNT-TOTAL | Main loop, lines 200-201 |

## Error Handling

| Condition                                           | Action                                                                                        | Return Code / ABCODE | Source Location         |
| --------------------------------------------------- | --------------------------------------------------------------------------------------------- | -------------------- | ------------------------ |
| DATEPARM-STATUS = '00' on READ                      | Set APPL-RESULT = 0 (APPL-AOK). Display date range and continue.                            | 0 (OK)               | 0550-DATEPARM-READ (line 220) |
| DATEPARM-STATUS = '10' on READ (EOF)                | Set APPL-RESULT = 16 (APPL-EOF). Set END-OF-FILE = 'Y'; processing loop will not execute.   | 16                   | 0550-DATEPARM-READ (line 220) |
| DATEPARM-STATUS = OTHER on READ                     | DISPLAY 'ERROR READING DATEPARM FILE'. Move status to IO-STATUS. Perform 9910-DISPLAY-IO-STATUS. Perform 9999-ABEND-PROGRAM (DISPLAY 'ABENDING PROGRAM', then CALL 'CEE3ABD' with ABCODE=999). | 12 / 999 abend | 0550-DATEPARM-READ (line 220) |
| TRANFILE-STATUS = '00' on sequential READ           | Set APPL-RESULT = 0 (APPL-AOK). Continue.                                                   | 0 (OK)               | 1000-TRANFILE-GET-NEXT (line 248) |
| TRANFILE-STATUS = '10' (EOF) on sequential READ     | Set APPL-RESULT = 16 (APPL-EOF). Set END-OF-FILE = 'Y'; terminates processing loop.         | 16                   | 1000-TRANFILE-GET-NEXT (line 248) |
| TRANFILE-STATUS = OTHER on sequential READ          | DISPLAY 'ERROR READING TRANSACTION FILE'. Move status to IO-STATUS. Perform 9910-DISPLAY-IO-STATUS. Perform 9999-ABEND-PROGRAM. | 12 / 999 abend | 1000-TRANFILE-GET-NEXT (line 248) |
| TRANREPT-STATUS != '00' on WRITE                    | DISPLAY 'ERROR WRITING REPTFILE'. Move status to IO-STATUS. Perform 9910-DISPLAY-IO-STATUS. Perform 9999-ABEND-PROGRAM. | 12 / 999 abend | 1111-WRITE-REPORT-REC (line 343) |
| XREF-FILE INVALID KEY on RANDOM READ                | DISPLAY 'INVALID CARD NUMBER : ' FD-XREF-CARD-NUM. Move 23 to IO-STATUS. Perform 9910-DISPLAY-IO-STATUS. Perform 9999-ABEND-PROGRAM. | 23 / 999 abend | 1500-A-LOOKUP-XREF (line 484) |
| TRANTYPE-FILE INVALID KEY on RANDOM READ            | DISPLAY 'INVALID TRANSACTION TYPE : ' FD-TRAN-TYPE. Move 23 to IO-STATUS. Perform 9910-DISPLAY-IO-STATUS. Perform 9999-ABEND-PROGRAM. | 23 / 999 abend | 1500-B-LOOKUP-TRANTYPE (line 494) |
| TRANCATG-FILE INVALID KEY on RANDOM READ            | DISPLAY 'INVALID TRAN CATG KEY : ' FD-TRAN-CAT-KEY. Move 23 to IO-STATUS. Perform 9910-DISPLAY-IO-STATUS. Perform 9999-ABEND-PROGRAM. | 23 / 999 abend | 1500-C-LOOKUP-TRANCATG (line 504) |
| TRANFILE-STATUS != '00' on OPEN                     | DISPLAY 'ERROR OPENING TRANFILE'. Move status to IO-STATUS. Perform 9910-DISPLAY-IO-STATUS. Perform 9999-ABEND-PROGRAM. | 12 / 999 abend | 0000-TRANFILE-OPEN (line 376) |
| TRANREPT-STATUS != '00' on OPEN OUTPUT              | DISPLAY 'ERROR OPENING REPTFILE'. Move status to IO-STATUS. Perform 9910-DISPLAY-IO-STATUS. Perform 9999-ABEND-PROGRAM. | 12 / 999 abend | 0100-REPTFILE-OPEN (line 394) |
| CARDXREF-STATUS != '00' on OPEN                     | DISPLAY 'ERROR OPENING CROSS REF FILE'. Move status to IO-STATUS. Perform 9910-DISPLAY-IO-STATUS. Perform 9999-ABEND-PROGRAM. | 12 / 999 abend | 0200-CARDXREF-OPEN (line 412) |
| TRANTYPE-STATUS != '00' on OPEN                     | DISPLAY 'ERROR OPENING TRANSACTION TYPE FILE'. Move status to IO-STATUS. Perform 9910-DISPLAY-IO-STATUS. Perform 9999-ABEND-PROGRAM. | 12 / 999 abend | 0300-TRANTYPE-OPEN (line 430) |
| TRANCATG-STATUS != '00' on OPEN                     | DISPLAY 'ERROR OPENING TRANSACTION CATG FILE'. Move status to IO-STATUS. Perform 9910-DISPLAY-IO-STATUS. Perform 9999-ABEND-PROGRAM. | 12 / 999 abend | 0400-TRANCATG-OPEN (line 448) |
| DATEPARM-STATUS != '00' on OPEN                     | DISPLAY 'ERROR OPENING DATE PARM FILE'. Move status to IO-STATUS. Perform 9910-DISPLAY-IO-STATUS. Perform 9999-ABEND-PROGRAM. | 12 / 999 abend | 0500-DATEPARM-OPEN (line 466) |
| TRANFILE-STATUS != '00' on CLOSE                    | DISPLAY 'ERROR CLOSING POSTED TRANSACTION FILE'. Move status to IO-STATUS. Perform 9910-DISPLAY-IO-STATUS. Perform 9999-ABEND-PROGRAM. | 12 / 999 abend | 9000-TRANFILE-CLOSE (line 514) |
| TRANREPT-STATUS != '00' on CLOSE                    | DISPLAY 'ERROR CLOSING REPORT FILE'. Move status to IO-STATUS. Perform 9910-DISPLAY-IO-STATUS. Perform 9999-ABEND-PROGRAM. | 12 / 999 abend | 9100-REPTFILE-CLOSE (line 532) |
| CARDXREF-STATUS != '00' on CLOSE                    | DISPLAY 'ERROR CLOSING CROSS REF FILE'. Move status to IO-STATUS. Perform 9910-DISPLAY-IO-STATUS. Perform 9999-ABEND-PROGRAM. | 12 / 999 abend | 9200-CARDXREF-CLOSE (line 551) |
| TRANTYPE-STATUS != '00' on CLOSE                    | DISPLAY 'ERROR CLOSING TRANSACTION TYPE FILE'. Move status to IO-STATUS. Perform 9910-DISPLAY-IO-STATUS. Perform 9999-ABEND-PROGRAM. | 12 / 999 abend | 9300-TRANTYPE-CLOSE (line 569) |
| TRANCATG-STATUS != '00' on CLOSE                    | DISPLAY 'ERROR CLOSING TRANSACTION CATG FILE'. Move status to IO-STATUS. Perform 9910-DISPLAY-IO-STATUS. Perform 9999-ABEND-PROGRAM. | 12 / 999 abend | 9400-TRANCATG-CLOSE (line 587) |
| DATEPARM-STATUS != '00' on CLOSE                    | DISPLAY 'ERROR CLOSING DATE PARM FILE'. Move status to IO-STATUS. Perform 9910-DISPLAY-IO-STATUS. Perform 9999-ABEND-PROGRAM. | 12 / 999 abend | 9500-DATEPARM-CLOSE (line 605) |
| IO-STATUS not numeric OR IO-STAT1 = '9' (VSE/VSAM extended file error) | Format extended status: place IO-STAT1 in position 1 of IO-STATUS-04; load IO-STAT2 as right byte of TWO-BYTES-BINARY; copy numeric value to IO-STATUS-0403 (3-digit). DISPLAY 'FILE STATUS IS: NNNN' IO-STATUS-04. | (diagnostic display) | 9910-DISPLAY-IO-STATUS (line 633) |
| IO-STATUS is numeric                                | MOVE '0000' TO IO-STATUS-04; move IO-STATUS into positions 3-4. DISPLAY 'FILE STATUS IS: NNNN' IO-STATUS-04. | (diagnostic display) | 9910-DISPLAY-IO-STATUS (line 633) |

### Abend Mechanism

All fatal error paths call 9999-ABEND-PROGRAM (line 626), which first executes `DISPLAY 'ABENDING PROGRAM'`, then sets TIMING = 0 and ABCODE = 999, then CALL 'CEE3ABD' USING ABCODE, TIMING. CEE3ABD is the Language Environment abnormal termination service; it terminates the job with a user abend code of 999. Note: 9999-ABEND-PROGRAM has no EXIT statement (unlike all other paragraphs in the program).

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. PROCEDURE DIVISION (main inline) -- DISPLAY 'START OF EXECUTION OF PROGRAM CBTRN03C'
2. 0000-TRANFILE-OPEN -- OPEN INPUT TRANSACT-FILE; abend on failure
3. 0100-REPTFILE-OPEN -- OPEN OUTPUT REPORT-FILE; abend on failure
4. 0200-CARDXREF-OPEN -- OPEN INPUT XREF-FILE; abend on failure
5. 0300-TRANTYPE-OPEN -- OPEN INPUT TRANTYPE-FILE; abend on failure
6. 0400-TRANCATG-OPEN -- OPEN INPUT TRANCATG-FILE; abend on failure
7. 0500-DATEPARM-OPEN -- OPEN INPUT DATE-PARMS-FILE; abend on failure
8. 0550-DATEPARM-READ -- READ DATE-PARMS-FILE INTO WS-DATEPARM-RECORD; display date range on success; set END-OF-FILE='Y' on EOF; abend on other error
9. PERFORM UNTIL END-OF-FILE = 'Y' (main processing loop):
   - a. IF END-OF-FILE = 'N' (always true on first iteration; set 'Y' by 1000-TRANFILE-GET-NEXT inside the loop):
     - PERFORM 1000-TRANFILE-GET-NEXT -- READ TRANSACT-FILE sequentially; set END-OF-FILE='Y' on EOF, abend on other error
     - Date filter: if TRAN-PROC-TS(1:10) outside [WS-START-DATE, WS-END-DATE] then NEXT SENTENCE -- exits the entire PERFORM UNTIL loop (see Notes)
     - IF END-OF-FILE = 'N' (valid record, not EOF):
       - DISPLAY TRAN-RECORD (debug display)
       - If new card number (WS-CURR-CARD-NUM != TRAN-CARD-NUM): optionally PERFORM 1120-WRITE-ACCOUNT-TOTALS (if not first record), then PERFORM 1500-A-LOOKUP-XREF
       - PERFORM 1500-B-LOOKUP-TRANTYPE -- RANDOM READ TRANTYPE-FILE by TRAN-TYPE-CD
       - PERFORM 1500-C-LOOKUP-TRANCATG -- RANDOM READ TRANCATG-FILE by (TRAN-TYPE-CD, TRAN-CAT-CD)
       - PERFORM 1100-WRITE-TRANSACTION-REPORT:
         - On first record: PERFORM 1120-WRITE-HEADERS (4 lines)
         - On each 20-line boundary: PERFORM 1110-WRITE-PAGE-TOTALS (2 lines) then PERFORM 1120-WRITE-HEADERS (4 lines)
         - ADD TRAN-AMT to WS-PAGE-TOTAL and WS-ACCOUNT-TOTAL
         - PERFORM 1120-WRITE-DETAIL -- format and write one detail line via 1111-WRITE-REPORT-REC; increment WS-LINE-COUNTER
     - ELSE (END-OF-FILE = 'Y' -- EOF anomaly branch):
       - DISPLAY 'TRAN-AMT ' TRAN-AMT; DISPLAY 'WS-PAGE-TOTAL' WS-PAGE-TOTAL
       - ADD TRAN-AMT TO WS-PAGE-TOTAL, WS-ACCOUNT-TOTAL (uses stale buffer value)
       - PERFORM 1110-WRITE-PAGE-TOTALS -- write page total, accumulate to grand total
       - PERFORM 1110-WRITE-GRAND-TOTALS -- write grand total line (does NOT increment WS-LINE-COUNTER)
10. 9000-TRANFILE-CLOSE -- CLOSE TRANSACT-FILE; abend on failure
11. 9100-REPTFILE-CLOSE -- CLOSE REPORT-FILE; abend on failure
12. 9200-CARDXREF-CLOSE -- CLOSE XREF-FILE; abend on failure
13. 9300-TRANTYPE-CLOSE -- CLOSE TRANTYPE-FILE; abend on failure
14. 9400-TRANCATG-CLOSE -- CLOSE TRANCATG-FILE; abend on failure
15. 9500-DATEPARM-CLOSE -- CLOSE DATE-PARMS-FILE; abend on failure
16. PROCEDURE DIVISION (main inline) -- DISPLAY 'END OF EXECUTION OF PROGRAM CBTRN03C', GOBACK

## Notes

- **NEXT SENTENCE exits entire PERFORM loop (critical defect):** The `NEXT SENTENCE` at line 177 (date filter ELSE branch) transfers control to the next sentence in COBOL, where a sentence is terminated by a period. The only period following line 177 within the main body is at line 206 (`END-PERFORM.`). This means the first out-of-range transaction encountered causes NEXT SENTENCE to exit the entire PERFORM UNTIL loop, not just skip the current iteration. All remaining transactions in the file -- whether in-range or not -- are never processed. The prior analysis note was incorrect in stating NEXT SENTENCE "exits to the period that closes the outer IF END-OF-FILE = 'N' block at line 205"; END-IF at line 205 is not a period/sentence terminator. This is a critical reporting defect: the report will be incomplete if the first out-of-range record appears before the last in-range record.
- **EOF stale-buffer anomaly (modernisation flag):** When the main loop detects END-OF-FILE='Y', it executes `ADD TRAN-AMT TO WS-PAGE-TOTAL WS-ACCOUNT-TOTAL` before calling the page and grand total writers (lines 200-201). At this point TRAN-RECORD holds whatever was in the I/O buffer from the EOF read attempt -- TRAN-AMT is indeterminate. This will corrupt the final page total and grand total by an unpredictable amount. A modernised replacement must NOT add TRAN-AMT at EOF; it should write totals using only the amounts already accumulated.
- **Debug DISPLAY in production loop:** Line 180 contains `DISPLAY TRAN-RECORD` inside the main loop for every in-range transaction. This is a debug statement left in production code and will produce large volumes of output on SYSOUT for any sizeable transaction file.
- **REPORT-FILE is write-only:** REPORT-FILE is opened OUTPUT only and does not appear in the reads list.
- **WS-LINE-COUNTER counts all written lines:** Header lines, blank separators, total lines, and detail lines all increment WS-LINE-COUNTER. With a 4-line header block, a 2-line page total block, and 2-line account total block, effective detail lines per page varies depending on how many card breaks fall within a page.
- **Account totals not written for last card group:** 1120-WRITE-ACCOUNT-TOTALS is only performed at a card break (when the next card number is encountered). The final card group's account total is never written to the report because no subsequent card change triggers it. Only the page total and grand total appear at end-of-file.
- **Grand total paragraph does not increment WS-LINE-COUNTER:** 1110-WRITE-GRAND-TOTALS (line 318) writes one record but has no ADD to WS-LINE-COUNTER, unlike all other write paragraphs. This means the final grand total line does not participate in the line-counter accounting.
- **Close paragraphs use obfuscated arithmetic idioms:** 9000-TRANFILE-CLOSE (line 514) and 9100-REPTFILE-CLOSE (line 532) use `ADD 8 TO ZERO GIVING APPL-RESULT` (equivalent to MOVE 8) and `SUBTRACT APPL-RESULT FROM APPL-RESULT` (equivalent to MOVE 0) instead of plain MOVE statements. All other open/close paragraphs use standard MOVE. This is a coding inconsistency with no functional difference.
- **Open paragraphs pre-initialize APPL-RESULT to 8:** Every OPEN paragraph (0000 through 0500) begins with `MOVE 8 TO APPL-RESULT.` (terminated by a period, making it a standalone sentence) before executing the OPEN statement. APPL-RESULT value 8 is neither APPL-AOK (0) nor APPL-EOF (16); if the post-OPEN FILE STATUS test were somehow skipped, the error branch would trigger. In practice the FILE STATUS clause always updates after every OPEN, making this a defensive (if unusual) initialisation pattern.
- **9999-ABEND-PROGRAM lacks EXIT:** This paragraph (line 626) is the only paragraph in the program without an EXIT statement. Because CALL 'CEE3ABD' terminates the job, EXIT is never reached in practice, but the absence is a structural inconsistency.
- **Copybooks used:** CVTRA05Y (TRAN-RECORD layout), CVACT03Y (CARD-XREF-RECORD layout), CVTRA03Y (TRAN-TYPE-RECORD layout), CVTRA04Y (TRAN-CAT-RECORD layout), CVTRA07Y (report line layouts -- TRANSACTION-DETAIL-REPORT, REPORT-PAGE-TOTALS, REPORT-ACCOUNT-TOTALS, REPORT-GRAND-TOTALS, REPORT-NAME-HEADER, TRANSACTION-HEADER-1, TRANSACTION-HEADER-2).
