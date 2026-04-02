---
type: business-rules
program: CBACT02C
program_type: batch
status: draft
confidence: high
last_pass: 5
calls:
- CEE3ABD
called_by: []
uses_copybooks:
- CVACT02Y
reads:
- CARDFILE-FILE
writes: []
db_tables: []
transactions: []
mq_queues: []
---

# CBACT02C -- Business Rules

## Program Purpose

CBACT02C is a batch COBOL program that performs a full sequential read of the card data VSAM KSDS file (CARDFILE) and prints every card record to SYSOUT. It is a diagnostic or reporting utility -- it opens the file, loops through every record in key sequence, DISPLAYs each CARD-RECORD, then closes the file and exits. No updates or writes are performed. On any I/O error it displays a formatted file status code and ABENDs via the IBM Language Environment CEE3ABD callable service.

The DISPLAY of CARD-RECORD outputs all fields in the 150-byte record including sensitive data: CARD-NUM (16 bytes), CARD-ACCT-ID (11 digits), CARD-CVV-CD (3 digits), CARD-EMBOSSED-NAME (50 bytes), CARD-EXPIRAION-DATE (10 bytes), CARD-ACTIVE-STATUS (1 byte), and FILLER (59 bytes). There is no masking or redaction of any field before output.

## Input / Output

| Direction | Resource     | Type | Description                                                            |
| --------- | ------------ | ---- | ---------------------------------------------------------------------- |
| IN        | CARDFILE     | File | VSAM KSDS card data file; DD name CARDFILE; sequential read, INPUT mode; record key FD-CARD-NUM (16 bytes); record length 150 bytes |
| OUT       | SYSOUT       | File | DISPLAY output -- each CARD-RECORD printed in full (all 150 bytes including sensitive card fields); file-status errors and program start/end banners also written here |

## Business Rules

### File Open

| #  | Rule                        | Condition                        | Action                                                                                          | Source Location    |
| -- | --------------------------- | -------------------------------- | ----------------------------------------------------------------------------------------------- | ------------------ |
| 1  | CARDFILE open success       | CARDFILE-STATUS = '00' after OPEN INPUT | Set APPL-RESULT to 0 (APPL-AOK); continue processing                                   | 0000-CARDFILE-OPEN |
| 2  | CARDFILE open failure       | CARDFILE-STATUS != '00' after OPEN INPUT | Set APPL-RESULT to 12; DISPLAY 'ERROR OPENING CARDFILE'; display formatted I/O status; DISPLAY 'ABENDING PROGRAM'; CALL CEE3ABD to ABEND with code 999 | 0000-CARDFILE-OPEN |

### Sequential Record Read

| #  | Rule                            | Condition                              | Action                                                                                                         | Source Location        |
| -- | ------------------------------- | -------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ---------------------- |
| 3  | Successful record read          | CARDFILE-STATUS = '00' after READ      | Set APPL-RESULT to 0 (APPL-AOK); CARD-RECORD is populated from FD-CARDFILE-REC                                 | 1000-CARDFILE-GET-NEXT |
| 4  | End-of-file detection           | CARDFILE-STATUS = '10' after READ      | Set APPL-RESULT to 16 (APPL-EOF); subsequently move 'Y' to END-OF-FILE flag to terminate read loop             | 1000-CARDFILE-GET-NEXT |
| 5  | Unexpected read error           | CARDFILE-STATUS is neither '00' nor '10' after READ | Set APPL-RESULT to 12; DISPLAY 'ERROR READING CARDFILE'; display formatted I/O status; DISPLAY 'ABENDING PROGRAM'; CALL CEE3ABD to ABEND with code 999 | 1000-CARDFILE-GET-NEXT |
| 6  | Record display gating           | END-OF-FILE = 'N' after a successful read | DISPLAY CARD-RECORD (full 150-byte card record to SYSOUT, including CARD-NUM, CARD-ACCT-ID, CARD-CVV-CD, CARD-EMBOSSED-NAME, CARD-EXPIRAION-DATE, CARD-ACTIVE-STATUS, and 59-byte FILLER, all unmasked) | PROCEDURE DIVISION main loop (lines 77-79) |

### Read Loop Control

| #  | Rule                        | Condition                    | Action                                                       | Source Location                          |
| -- | --------------------------- | ---------------------------- | ------------------------------------------------------------ | ---------------------------------------- |
| 7  | Loop continuation guard     | END-OF-FILE = 'N' at top of loop | PERFORM 1000-CARDFILE-GET-NEXT to read next record        | PROCEDURE DIVISION main loop (line 75)   |
| 8  | Loop termination            | END-OF-FILE = 'Y'            | Exit PERFORM UNTIL loop; proceed to close file               | PROCEDURE DIVISION main loop (line 74)   |

### File Close

| #  | Rule                        | Condition                         | Action                                                                                          | Source Location     |
| -- | --------------------------- | --------------------------------- | ----------------------------------------------------------------------------------------------- | ------------------- |
| 9  | CARDFILE close success      | CARDFILE-STATUS = '00' after CLOSE | Set APPL-RESULT to 0 (APPL-AOK); continue to GOBACK                                           | 9000-CARDFILE-CLOSE |
| 10 | CARDFILE close failure      | CARDFILE-STATUS != '00' after CLOSE | Set APPL-RESULT to 12; DISPLAY 'ERROR CLOSING CARDFILE'; display formatted I/O status; DISPLAY 'ABENDING PROGRAM'; CALL CEE3ABD to ABEND with code 999 | 9000-CARDFILE-CLOSE |

## Calculations

| Calculation             | Formula / Logic                                                                                         | Input Fields          | Output Field       | Source Location     |
| ----------------------- | ------------------------------------------------------------------------------------------------------- | --------------------- | ------------------ | ------------------- |
| APPL-RESULT initialise (open)  | `MOVE 8 TO APPL-RESULT` before OPEN; set to 0 on success (`MOVE 0 TO APPL-RESULT`), set to 12 on failure (`MOVE 12 TO APPL-RESULT`) -- guards against partial open leaving indeterminate status | Literal 8, CARDFILE-STATUS | APPL-RESULT | 0000-CARDFILE-OPEN (line 119) |
| APPL-RESULT initialise (close) | `ADD 8 TO ZERO GIVING APPL-RESULT` (equivalent to MOVE 8) before CLOSE; set to 0 via `SUBTRACT APPL-RESULT FROM APPL-RESULT` on success, set to 12 via `ADD 12 TO ZERO GIVING APPL-RESULT` on failure | Literal 8, CARDFILE-STATUS | APPL-RESULT | 9000-CARDFILE-CLOSE (lines 137-142) |
| IO-STATUS decode (non-numeric or STAT1='9') | Copy IO-STAT1 as first byte of IO-STATUS-04; zero TWO-BYTES-BINARY; move IO-STAT2 to TWO-BYTES-RIGHT (right byte of BINARY overlay); copy TWO-BYTES-BINARY integer value to IO-STATUS-0403 -- converts vendor-specific single-byte code to integer for display | IO-STAT1, IO-STAT2, TWO-BYTES-BINARY | IO-STATUS-04, IO-STATUS-0403 | 9910-DISPLAY-IO-STATUS (lines 162-168) |
| IO-STATUS decode (numeric)     | `MOVE '0000' TO IO-STATUS-04` then `MOVE IO-STATUS TO IO-STATUS-04(3:2)` -- overlays the two decimal status bytes at positions 3-4 of the 4-digit display field | IO-STATUS             | IO-STATUS-04       | 9910-DISPLAY-IO-STATUS (lines 170-172) |

## Error Handling

| Condition                                      | Action                                                                                         | Return Code | Source Location        |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------- | ----------- | ---------------------- |
| CARDFILE OPEN fails (status != '00')           | DISPLAY 'ERROR OPENING CARDFILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM  | ABEND 999   | 0000-CARDFILE-OPEN     |
| CARDFILE READ fails (status != '00' and != '10') | DISPLAY 'ERROR READING CARDFILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | ABEND 999   | 1000-CARDFILE-GET-NEXT |
| CARDFILE CLOSE fails (status != '00')          | DISPLAY 'ERROR CLOSING CARDFILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM  | ABEND 999   | 9000-CARDFILE-CLOSE    |
| I/O status non-numeric or STAT1 = '9' (platform-specific error) | Decode two-byte vendor status code via BINARY overlay; DISPLAY 'FILE STATUS IS: NNNN' followed by decoded IO-STATUS-04 | (display only) | 9910-DISPLAY-IO-STATUS |
| I/O status numeric                             | Format decimal status into IO-STATUS-04 at offset 3:2; DISPLAY 'FILE STATUS IS: NNNN' followed by IO-STATUS-04 | (display only) | 9910-DISPLAY-IO-STATUS |
| ABEND invocation                               | DISPLAY 'ABENDING PROGRAM'; MOVE 0 TO TIMING; MOVE 999 TO ABCODE; CALL 'CEE3ABD' USING ABCODE, TIMING -- terminates program with LE abend code 999, no dump delay | ABEND 999   | 9999-ABEND-PROGRAM     |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. Inline (PROCEDURE DIVISION entry) -- DISPLAY 'START OF EXECUTION OF PROGRAM CBACT02C'
2. 0000-CARDFILE-OPEN -- opens CARDFILE-FILE for INPUT; ABENDs on failure
3. PERFORM UNTIL END-OF-FILE = 'Y' (main read loop):
   a. IF END-OF-FILE = 'N': PERFORM 1000-CARDFILE-GET-NEXT -- reads next card record sequentially
   b. IF END-OF-FILE still 'N' after read: DISPLAY CARD-RECORD (all 150 bytes unmasked) to SYSOUT
4. 9000-CARDFILE-CLOSE -- closes CARDFILE-FILE; ABENDs on failure
5. Inline -- DISPLAY 'END OF EXECUTION OF PROGRAM CBACT02C'
6. GOBACK -- returns to operating system / job step

Error sub-flow (any I/O failure):
- 9910-DISPLAY-IO-STATUS -- formats and displays the two-byte file status code; handles both numeric (standard COBOL) and non-numeric / '9x' (platform-specific) status codes
- 9999-ABEND-PROGRAM -- DISPLAY 'ABENDING PROGRAM'; CALL 'CEE3ABD' with ABCODE=999, TIMING=0 to force abnormal termination

## Notes

- The inner loop structure (PERFORM UNTIL with nested IF END-OF-FILE = 'N') means that once END-OF-FILE is set to 'Y' inside 1000-CARDFILE-GET-NEXT, the outer PERFORM UNTIL exits cleanly without attempting another display. This is a defensive double-guard pattern.
- CARD-RECORD is read via `READ CARDFILE-FILE INTO CARD-RECORD`, which reads from the FD buffer (FD-CARDFILE-REC, 150 bytes) into the WORKING-STORAGE CARD-RECORD structure defined by COPY CVACT02Y. The record key FD-CARD-NUM maps to CARD-NUM in CVACT02Y.
- CARD-RECORD layout (CVACT02Y): CARD-NUM X(16), CARD-ACCT-ID 9(11), CARD-CVV-CD 9(03), CARD-EMBOSSED-NAME X(50), CARD-EXPIRAION-DATE X(10), CARD-ACTIVE-STATUS X(01), FILLER X(59). Total: 150 bytes. Note the field name typo: CARD-EXPIRAION-DATE (missing 'T') is the actual field name in the copybook.
- There is a commented-out `DISPLAY CARD-RECORD` at line 96 (inside 1000-CARDFILE-GET-NEXT) -- this dead code suggests the display was originally in the read paragraph and was later moved to the main loop to allow EOF gating.
- APPL-RESULT 88-level conditions: APPL-AOK (value 0) = operation succeeded; APPL-EOF (value 16) = end of file reached. Value 12 = I/O error requiring ABEND. Value 8 = initial sentinel set before open/close to detect failure to execute the I/O verb.
- The file status '10' (end of file on sequential read) is treated as a normal condition, not an error.
- The DISPLAY message for IO-STATUS contains the literal label 'FILE STATUS IS: NNNN' followed by the IO-STATUS-04 value -- the 'NNNN' is a static label string, not a format specifier; the actual decoded status appears after it as a separate operand.
