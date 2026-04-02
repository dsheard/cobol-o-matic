---
type: business-rules
program: CBACT03C
program_type: batch
status: draft
confidence: high
last_pass: 4
calls:
- CEE3ABD
called_by: []
uses_copybooks:
- CVACT03Y
reads:
- XREFFILE-FILE
writes: []
db_tables: []
transactions: []
mq_queues: []
---

# CBACT03C -- Business Rules

## Program Purpose

CBACT03C is a batch reporting program that sequentially reads and prints every record in the card account cross-reference VSAM KSDS file (XREFFILE). Each record associates a credit card number (16 chars) with a customer ID (9 digits) and an account ID (11 digits). The program opens the file, reads all records in key sequence, DISPLAYs each record to SYSOUT, closes the file, and terminates. Any I/O error that is not a normal end-of-file causes an immediate abnormal termination via CEE3ABD with abend code 999.

Note: Due to a duplication in the source code, each successfully-read record is displayed twice per iteration -- once inside paragraph 1000-XREFFILE-GET-NEXT (line 96, on the successful-read branch) and once in the calling main loop (line 78, after GET-NEXT returns with END-OF-FILE still 'N'). This appears to be a bug rather than intentional behaviour.

Note: Paragraph 1000-XREFFILE-GET-NEXT appears in the source file (line 92) before paragraph 0000-XREFFILE-OPEN (line 118). This is a source ordering anomaly -- both paragraphs are reachable only via PERFORM from the PROCEDURE DIVISION entry, so execution order is unaffected, but the numbering convention (0000 before 1000) is violated.

## Input / Output

| Direction | Resource     | Type | Description                                                                 |
| --------- | ------------ | ---- | --------------------------------------------------------------------------- |
| IN        | XREFFILE-FILE | File (VSAM KSDS, INDEXED organisation, ACCESS MODE SEQUENTIAL, RECORD KEY FD-XREF-CARD-NUM) | Card-to-account cross-reference file. Record length: 50 bytes. Contains card number, customer ID, and account ID. |
| OUT       | SYSOUT (DISPLAY) | Batch output | Each CARD-XREF-RECORD is written to the system output stream via DISPLAY (twice per record due to source duplication). |

## Business Rules

### File Open

| #   | Rule                     | Condition                              | Action                                                                                              | Source Location     |
| --- | ------------------------ | -------------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------- |
| 1   | Pre-set failure result   | Unconditional at open start            | MOVE 8 TO APPL-RESULT before attempting OPEN, so any path that does not set a result leaves a non-zero code | 0000-XREFFILE-OPEN (line 119) |
| 2   | Successful open          | XREFFILE-STATUS = '00' after OPEN INPUT | MOVE 0 TO APPL-RESULT (APPL-AOK condition becomes true)                                             | 0000-XREFFILE-OPEN (lines 121-122) |
| 3   | Failed open              | XREFFILE-STATUS not '00' after OPEN INPUT | MOVE 12 TO APPL-RESULT, display 'ERROR OPENING XREFFILE', display I/O status detail, then ABEND     | 0000-XREFFILE-OPEN (lines 123-133) |

### Sequential Read Loop

| #   | Rule                     | Condition                              | Action                                                                                              | Source Location     |
| --- | ------------------------ | -------------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------- |
| 4   | Loop termination         | END-OF-FILE = 'Y'                      | Exit PERFORM loop and proceed to file close                                                         | PROCEDURE DIVISION main loop (line 74) |
| 5   | Inner guard before read  | END-OF-FILE = 'N' at top of loop body  | Only PERFORM 1000-XREFFILE-GET-NEXT when flag is still 'N'. This guard is always true at loop entry (the UNTIL already guarantees it) and is therefore redundant, but it does no harm. | PROCEDURE DIVISION main loop (line 75) |
| 6   | Guard before main-loop DISPLAY | END-OF-FILE = 'N' after GET-NEXT | Only DISPLAY CARD-XREF-RECORD from the main loop when the just-completed read did not set EOF; prevents display of stale record on EOF | PROCEDURE DIVISION main loop (lines 77-79) |

### Record Read and EOF Detection

| #   | Rule                     | Condition                              | Action                                                                                              | Source Location     |
| --- | ------------------------ | -------------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------- |
| 7   | Successful record read -- first display | XREFFILE-STATUS = '00' after READ | MOVE 0 TO APPL-RESULT (APPL-AOK); DISPLAY CARD-XREF-RECORD immediately inside 1000-XREFFILE-GET-NEXT (first of two displays per record) | 1000-XREFFILE-GET-NEXT (lines 94-96) |
| 8   | End-of-file detected     | XREFFILE-STATUS = '10' after READ      | MOVE 16 TO APPL-RESULT (APPL-EOF condition becomes true)                                            | 1000-XREFFILE-GET-NEXT (lines 98-99) |
| 9   | Unexpected read error    | XREFFILE-STATUS neither '00' nor '10'  | MOVE 12 TO APPL-RESULT (neither APPL-AOK nor APPL-EOF)                                             | 1000-XREFFILE-GET-NEXT (lines 100-101) |
| 10  | Set EOF flag             | APPL-EOF (APPL-RESULT = 16)            | MOVE 'Y' TO END-OF-FILE; loop will terminate on next iteration test                                | 1000-XREFFILE-GET-NEXT (lines 107-108) |
| 11  | Read error abend         | APPL-RESULT not 0 and not 16 after READ | Display 'ERROR READING XREFFILE', display I/O status, call 9999-ABEND-PROGRAM                      | 1000-XREFFILE-GET-NEXT (lines 110-113) |
| 12  | Successful record read -- second display | END-OF-FILE still 'N' after 1000-XREFFILE-GET-NEXT returns | DISPLAY CARD-XREF-RECORD again from the main loop body (second of two displays per record; this is a duplication of rule 7) | PROCEDURE DIVISION main loop (line 78) |
| 13  | READ INTO target         | Unconditional on every READ            | READ XREFFILE-FILE INTO CARD-XREF-RECORD: data is placed directly into the WORKING-STORAGE structure CARD-XREF-RECORD (from copybook CVACT03Y), bypassing the FD-level FD-XREFFILE-REC buffer | 1000-XREFFILE-GET-NEXT (line 93) |

### File Close

| #   | Rule                     | Condition                              | Action                                                                                              | Source Location     |
| --- | ------------------------ | -------------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------- |
| 14  | Pre-set failure result   | Unconditional at close start           | ADD 8 TO ZERO GIVING APPL-RESULT before CLOSE, ensuring non-zero result if status not checked       | 9000-XREFFILE-CLOSE (line 137) |
| 15  | Successful close         | XREFFILE-STATUS = '00' after CLOSE     | SUBTRACT APPL-RESULT FROM APPL-RESULT (sets APPL-RESULT to 0, APPL-AOK true)                       | 9000-XREFFILE-CLOSE (lines 139-140) |
| 16  | Failed close             | XREFFILE-STATUS not '00' after CLOSE   | ADD 12 TO ZERO GIVING APPL-RESULT, display 'ERROR CLOSING XREFFILE', display I/O status, ABEND     | 9000-XREFFILE-CLOSE (lines 141-151) |

### Record Content (from copybook CVACT03Y)

| #   | Rule                     | Condition                              | Action                                                                                              | Source Location     |
| --- | ------------------------ | -------------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------- |
| 17  | Record structure         | Every XREFFILE record read             | CARD-XREF-RECORD contains: XREF-CARD-NUM PIC X(16) (card number), XREF-CUST-ID PIC 9(09) (customer ID), XREF-ACCT-ID PIC 9(11) (account ID), 14-byte FILLER. Total record length = 50 bytes. | CVACT03Y copybook   |

### I/O Status Decoding

| #   | Rule                     | Condition                              | Action                                                                                              | Source Location     |
| --- | ------------------------ | -------------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------- |
| 18  | Non-numeric or extended VSAM status  | IO-STATUS NOT NUMERIC OR IO-STAT1 = '9' | Decode via binary overlay: IO-STAT1 copied to IO-STATUS-04(1:1); IO-STAT2 binary value placed in TWO-BYTES-BINARY via TWO-BYTES-RIGHT; TWO-BYTES-BINARY moved to IO-STATUS-0403; display 'FILE STATUS IS: NNNN' followed by IO-STATUS-04 | 9910-DISPLAY-IO-STATUS (lines 162-168) |
| 19  | Standard numeric status  | IO-STATUS IS NUMERIC AND IO-STAT1 != '9' | Move '0000' to IO-STATUS-04; overlay positions 3-4 with IO-STATUS (2-byte value); display 'FILE STATUS IS: NNNN' followed by IO-STATUS-04 | 9910-DISPLAY-IO-STATUS (lines 169-173) |
| 20  | Display format quirk     | Unconditional on every status display  | The literal string 'FILE STATUS IS: NNNN' is always output verbatim (the 'NNNN' is a literal, not a placeholder), immediately followed by the decoded 4-digit IO-STATUS-04 value. Output therefore reads e.g. 'FILE STATUS IS: NNNN0010'. | 9910-DISPLAY-IO-STATUS (lines 168, 172) |

## Calculations

| Calculation | Formula / Logic                                              | Input Fields   | Output Field  | Source Location              |
| ----------- | ------------------------------------------------------------ | -------------- | ------------- | ---------------------------- |
| Set APPL-RESULT to 0 (open success)  | MOVE 0 TO APPL-RESULT                         | Literal 0      | APPL-RESULT   | 0000-XREFFILE-OPEN (line 122) |
| Set APPL-RESULT to 8 (pre-open guard) | MOVE 8 TO APPL-RESULT (literal assignment)   | Literal 8      | APPL-RESULT   | 0000-XREFFILE-OPEN (line 119) |
| Set APPL-RESULT to 0 (read success)  | MOVE 0 TO APPL-RESULT                         | Literal 0      | APPL-RESULT   | 1000-XREFFILE-GET-NEXT (line 95) |
| Set APPL-RESULT to 16 (EOF)          | MOVE 16 TO APPL-RESULT                        | Literal 16     | APPL-RESULT   | 1000-XREFFILE-GET-NEXT (line 99) |
| Set APPL-RESULT to 12 (error)        | MOVE 12 TO APPL-RESULT                        | Literal 12     | APPL-RESULT   | 1000-XREFFILE-GET-NEXT (line 101) |
| Set APPL-RESULT to 8 (pre-close guard) | ADD 8 TO ZERO GIVING APPL-RESULT             | Literal 8, ZERO | APPL-RESULT | 9000-XREFFILE-CLOSE (line 137) |
| Set APPL-RESULT to 0 (close success) | SUBTRACT APPL-RESULT FROM APPL-RESULT (self-subtract) | APPL-RESULT | APPL-RESULT | 9000-XREFFILE-CLOSE (line 140) |
| Set APPL-RESULT to 12 (close error)  | ADD 12 TO ZERO GIVING APPL-RESULT             | Literal 12, ZERO | APPL-RESULT | 9000-XREFFILE-CLOSE (line 142) |
| IO-STATUS decode (non-numeric or '9' status) | IO-STAT1 placed in IO-STATUS-04(1:1); IO-STAT2 binary value moved via TWO-BYTES-BINARY to IO-STATUS-0403; produces display string 'FILE STATUS IS: NNNN' + IO-STATUS-04 | IO-STAT1, IO-STAT2 | IO-STATUS-04 (IO-STATUS-0401 + IO-STATUS-0403) | 9910-DISPLAY-IO-STATUS (lines 162-168) |
| IO-STATUS decode (numeric status)    | '0000' moved to IO-STATUS-04; IO-STATUS copied into positions 3-4 of IO-STATUS-04; display 'FILE STATUS IS: NNNN' + IO-STATUS-04 | IO-STATUS | IO-STATUS-04 | 9910-DISPLAY-IO-STATUS (lines 170-172) |

## Error Handling

| Condition                              | Action                                                                                  | Return Code      | Source Location                         |
| -------------------------------------- | --------------------------------------------------------------------------------------- | ---------------- | --------------------------------------- |
| XREFFILE-STATUS not '00' on OPEN       | DISPLAY 'ERROR OPENING XREFFILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | ABEND 999    | 0000-XREFFILE-OPEN (lines 129-132)      |
| XREFFILE-STATUS not '00' and not '10' on READ | DISPLAY 'ERROR READING XREFFILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | ABEND 999 | 1000-XREFFILE-GET-NEXT (lines 110-113) |
| XREFFILE-STATUS not '00' on CLOSE      | DISPLAY 'ERROR CLOSING XREFFILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | ABEND 999    | 9000-XREFFILE-CLOSE (lines 147-150)     |
| Any I/O abend triggered                | DISPLAY 'ABENDING PROGRAM'; MOVE 0 TO TIMING; MOVE 999 TO ABCODE; CALL 'CEE3ABD' USING ABCODE, TIMING | ABCODE=999, TIMING=0 | 9999-ABEND-PROGRAM (lines 154-158) |
| 9999-ABEND-PROGRAM has no EXIT statement | If CEE3ABD were to return (not expected), execution would fall through to 9910-DISPLAY-IO-STATUS. This is a structural anomaly -- low practical risk as CEE3ABD is a LE termination service. | n/a | 9999-ABEND-PROGRAM (line 154-158) |
| IO-STATUS is non-numeric or IO-STAT1 = '9' | Decode via binary overlay: TWO-BYTES-BINARY receives binary value of IO-STAT2, decoded into IO-STATUS-0403; display 'FILE STATUS IS: NNNN' + IO-STATUS-04 | -- | 9910-DISPLAY-IO-STATUS (lines 162-168) |
| IO-STATUS is numeric and IO-STAT1 != '9' | Move '0000' to IO-STATUS-04; overlay positions 3-4 with numeric status; display 'FILE STATUS IS: NNNN' + IO-STATUS-04 | -- | 9910-DISPLAY-IO-STATUS (lines 169-173) |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. PROCEDURE DIVISION entry -- DISPLAY 'START OF EXECUTION OF PROGRAM CBACT03C'
2. 0000-XREFFILE-OPEN -- Opens XREFFILE-FILE for sequential INPUT; abends on failure
3. Main PERFORM UNTIL loop (END-OF-FILE = 'Y') -- Drives the entire sequential read pass
4. 1000-XREFFILE-GET-NEXT (called from loop) -- READs next record INTO CARD-XREF-RECORD; sets APPL-RESULT to 0 (ok), 16 (EOF), or 12 (error); on success DISPLAYs CARD-XREF-RECORD (first display); on error PERFORMs 9910 and 9999; on EOF sets END-OF-FILE='Y'
5. DISPLAY CARD-XREF-RECORD (inline, inside loop, line 78) -- Prints the cross-reference record a second time when END-OF-FILE is still 'N' after the read (duplication of the display at step 4)
6. 9000-XREFFILE-CLOSE -- Closes XREFFILE-FILE after loop exits; abends on failure
7. PROCEDURE DIVISION exit -- DISPLAY 'END OF EXECUTION OF PROGRAM CBACT03C'; GOBACK
8. 9910-DISPLAY-IO-STATUS (called on any I/O error) -- Decodes and displays the 2-byte file status code in human-readable form; handles both numeric (standard) and non-numeric/subcategory-9 (VSAM extended) status codes
9. 9999-ABEND-PROGRAM (called on any I/O error) -- DISPLAY 'ABENDING PROGRAM'; CALL 'CEE3ABD' with ABCODE=999, TIMING=0 to force abnormal termination; no EXIT statement present

Note: The main loop contains a double-guard pattern. The outer UNTIL (END-OF-FILE = 'Y') and the inner IF (END-OF-FILE = 'N' at line 75) are logically redundant with each other -- the inner IF is always true at loop entry. The second inner IF (line 77, END-OF-FILE = 'N' after GET-NEXT) is the meaningful guard that prevents displaying the last valid record a second time if GET-NEXT detects EOF.

Note: Each successfully-read record is displayed twice per iteration. The DISPLAY at line 96 (inside 1000-XREFFILE-GET-NEXT, on the XREFFILE-STATUS = '00' branch) and the DISPLAY at line 78 (in the main loop body, guarded by END-OF-FILE = 'N') both output CARD-XREF-RECORD for the same record. This appears to be a source-code duplication bug rather than intentional behaviour.

Note: Paragraph 1000-XREFFILE-GET-NEXT appears in the source before paragraph 0000-XREFFILE-OPEN (paragraphs are ordered 1000, 0000, 9000, 9999, 9910). This violates the numeric naming convention but has no runtime effect since all paragraphs are reached only via PERFORM.
