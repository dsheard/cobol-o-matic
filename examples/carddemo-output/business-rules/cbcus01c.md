---
type: business-rules
program: CBCUS01C
program_type: batch
status: draft
confidence: high
last_pass: 4
calls:
- CEE3ABD
called_by: []
uses_copybooks:
- CVCUS01Y
reads:
- CUSTFILE-FILE
writes: []
db_tables: []
transactions: []
mq_queues: []
---

# CBCUS01C -- Business Rules

## Program Purpose

CBCUS01C is a batch COBOL program that performs a full sequential read of the customer master file (CUSTFILE) and prints every customer record to SYSOUT. It is a diagnostic/reporting utility: it opens the indexed VSAM KSDS file in sequential mode, reads records one at a time until end-of-file, displays each CUSTOMER-RECORD, then closes the file and terminates. On any I/O error it displays the file status code and abnormally ends via LE routine CEE3ABD with abend code 999.

**Note -- double-display per record (source lines 96 and 78):** due to a structural overlap in the code, every successfully-read record is displayed twice. `DISPLAY CUSTOMER-RECORD` appears first inside `1000-CUSTFILE-GET-NEXT` (when CUSTFILE-STATUS = '00', line 96, executed during the PERFORM call), then again in the main loop (when the inner `IF END-OF-FILE = 'N'` at line 77 is true after the PERFORM returns, executing the DISPLAY at line 78). This means each record produces two output lines per read cycle -- the first from inside the paragraph, the second from the calling loop.

**Note -- two-level redundant EOF guard in main loop (lines 75 and 77):** the PERFORM UNTIL at line 74 already guarantees END-OF-FILE = 'N' whenever the loop body executes. Despite this, there is an outer `IF END-OF-FILE = 'N'` at line 75 (always true at that point) wrapping the PERFORM, and then a second inner `IF END-OF-FILE = 'N'` at line 77 after the PERFORM (also redundant because a read that sets EOF='Y' causes either an abend or returns with EOF='Y', making the DISPLAY at line 78 the only live output path). Both extra checks are structurally dead logic.

Source version: CardDemo_v2.0-25-gdb72e6b-235 (2025-04-29).

## Input / Output

| Direction | Resource      | Type    | Description                                                                                                                         |
| --------- | ------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| IN        | CUSTFILE-FILE | File    | VSAM KSDS customer master file; ORGANIZATION INDEXED, ACCESS SEQUENTIAL. DD name CUSTFILE. Record key FD-CUST-ID (9 digits). Record length 500 bytes. |
| OUT       | SYSOUT        | DISPLAY | Each CUSTOMER-RECORD (500 bytes) is written to standard output via DISPLAY -- twice per record (see note above). File status diagnostic messages also written to SYSOUT on error. |

## Customer Record Layout (CVCUS01Y)

The 500-byte CUSTOMER-RECORD printed to SYSOUT contains these fields:

| Field                   | Picture    | Description                          |
| ----------------------- | ---------- | ------------------------------------ |
| CUST-ID                 | 9(09)      | Customer ID (matches record key)     |
| CUST-FIRST-NAME         | X(25)      | First name                           |
| CUST-MIDDLE-NAME        | X(25)      | Middle name                          |
| CUST-LAST-NAME          | X(25)      | Last name                            |
| CUST-ADDR-LINE-1        | X(50)      | Address line 1                       |
| CUST-ADDR-LINE-2        | X(50)      | Address line 2                       |
| CUST-ADDR-LINE-3        | X(50)      | Address line 3                       |
| CUST-ADDR-STATE-CD      | X(02)      | State code                           |
| CUST-ADDR-COUNTRY-CD    | X(03)      | Country code                         |
| CUST-ADDR-ZIP           | X(10)      | ZIP / postal code                    |
| CUST-PHONE-NUM-1        | X(15)      | Primary phone number                 |
| CUST-PHONE-NUM-2        | X(15)      | Secondary phone number               |
| CUST-SSN                | 9(09)      | Social Security Number               |
| CUST-GOVT-ISSUED-ID     | X(20)      | Government-issued ID                 |
| CUST-DOB-YYYY-MM-DD     | X(10)      | Date of birth (YYYY-MM-DD format)    |
| CUST-EFT-ACCOUNT-ID     | X(10)      | EFT account identifier               |
| CUST-PRI-CARD-HOLDER-IND| X(01)      | Primary card holder indicator        |
| CUST-FICO-CREDIT-SCORE  | 9(03)      | FICO credit score                    |
| FILLER                  | X(168)     | Unused padding to 500 bytes          |

## Business Rules

### File Open

| #  | Rule                              | Condition                                    | Action                                                                                                  | Source Location      |
| -- | --------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------- | -------------------- |
| 1  | Customer file must open cleanly   | CUSTFILE-STATUS = '00' after OPEN INPUT      | Set APPL-RESULT = 0 (APPL-AOK), continue to read loop                                                  | 0000-CUSTFILE-OPEN   |
| 2  | Customer file open failure        | CUSTFILE-STATUS != '00' after OPEN INPUT     | Set APPL-RESULT = 12, display 'ERROR OPENING CUSTFILE', display file status, call Z-ABEND-PROGRAM      | 0000-CUSTFILE-OPEN   |

### Sequential Read Loop

| #  | Rule                                              | Condition                                                                | Action                                                                                                                                       | Source Location                |
| -- | ------------------------------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| 3  | Loop continues while not end-of-file              | PERFORM UNTIL END-OF-FILE = 'Y' (initial value 'N')                     | Repeatedly invoke 1000-CUSTFILE-GET-NEXT until END-OF-FILE = 'Y'                                                                            | PROCEDURE DIVISION line 74     |
| 4  | Redundant outer EOF guard (dead logic)            | `IF END-OF-FILE = 'N'` at line 75 wraps the PERFORM and post-PERFORM IF  | Always true when loop body executes (PERFORM UNTIL already guarantees END-OF-FILE='N' at entry); no functional effect -- dead conditional     | PROCEDURE DIVISION line 75     |
| 5  | Redundant inner EOF guard after read (dead logic) | `IF END-OF-FILE = 'N'` at line 77 after PERFORM 1000-CUSTFILE-GET-NEXT  | Always true when a record was successfully read (EOF='Y' branch either abends or ends the loop next iteration); no functional effect -- dead conditional | PROCEDURE DIVISION line 77 |
| 6  | Successful sequential read (first display)        | CUSTFILE-STATUS = '00' after READ CUSTFILE-FILE INTO CUSTOMER-RECORD     | Set APPL-RESULT = 0 (APPL-AOK); DISPLAY CUSTOMER-RECORD -- first of two displays per record; occurs inside the PERFORM of 1000-CUSTFILE-GET-NEXT | 1000-CUSTFILE-GET-NEXT line 96 |
| 7  | Main loop second display after read               | `IF END-OF-FILE = 'N'` true at line 77 after PERFORM returns             | DISPLAY CUSTOMER-RECORD -- second of two displays per record; occurs in the calling loop at line 78 after PERFORM 1000-CUSTFILE-GET-NEXT returns | PROCEDURE DIVISION line 78     |
| 8  | End-of-file detection (two-step via 88-level)     | CUSTFILE-STATUS = '10' after READ sets APPL-RESULT = 16; 88 APPL-EOF condition fires | MOVE 'Y' TO END-OF-FILE; PERFORM UNTIL exits on next iteration; no display or abend                                                | 1000-CUSTFILE-GET-NEXT lines 99, 108 |
| 9  | Unexpected read error                             | CUSTFILE-STATUS not '00' and not '10' (APPL-RESULT = 12, not AOK or EOF) | Set APPL-RESULT = 12; display 'ERROR READING CUSTOMER FILE'; display file status; call Z-ABEND-PROGRAM                                      | 1000-CUSTFILE-GET-NEXT lines 101, 110-113 |

### File Close

| #  | Rule                              | Condition                                    | Action                                                                                                    | Source Location      |
| -- | --------------------------------- | -------------------------------------------- | --------------------------------------------------------------------------------------------------------- | -------------------- |
| 10 | Customer file must close cleanly  | CUSTFILE-STATUS = '00' after CLOSE           | Set APPL-RESULT = 0 (APPL-AOK via SUBTRACT self from self), continue to GOBACK                           | 9000-CUSTFILE-CLOSE  |
| 11 | Customer file close failure       | CUSTFILE-STATUS != '00' after CLOSE          | Set APPL-RESULT = 12 (via ADD 12 TO ZERO GIVING APPL-RESULT); display 'ERROR CLOSING CUSTOMER FILE'; display file status; call Z-ABEND-PROGRAM | 9000-CUSTFILE-CLOSE |

### Abend Handling

| #  | Rule                               | Condition                                   | Action                                                                                                                         | Source Location    |
| -- | ---------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------ |
| 12 | Program abend on unrecoverable I/O | APPL-RESULT = 12 (not AOK, not EOF)         | Display 'ABENDING PROGRAM'; set TIMING = 0, ABCODE = 999; CALL 'CEE3ABD' USING ABCODE, TIMING (LE abnormal termination); program does not return | Z-ABEND-PROGRAM    |

### I/O Status Display

| #  | Rule                                        | Condition                                    | Action                                                                                                                                                                                                     | Source Location       |
| -- | ------------------------------------------- | -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| 13 | Non-numeric or vendor-extended status code  | IO-STATUS NOT NUMERIC OR IO-STAT1 = '9'      | Extract first byte as-is into IO-STATUS-04(1:1); zero TWO-BYTES-BINARY then MOVE IO-STAT2 to TWO-BYTES-RIGHT; MOVE TWO-BYTES-BINARY to IO-STATUS-0403 (character-to-binary conversion); DISPLAY 'FILE STATUS IS: NNNN' concatenated with IO-STATUS-04 | Z-DISPLAY-IO-STATUS   |
| 14 | Standard 2-digit numeric file status code   | IO-STATUS IS NUMERIC AND IO-STAT1 != '9'     | MOVE '0000' to IO-STATUS-04; overlay positions 3-4 with the 2-character IO-STATUS value (MOVE IO-STATUS TO IO-STATUS-04(3:2)); DISPLAY 'FILE STATUS IS: NNNN' concatenated with IO-STATUS-04               | Z-DISPLAY-IO-STATUS   |

## Calculations

| Calculation                         | Formula / Logic                                                                       | Input Fields             | Output Field   | Source Location                                                  |
| ----------------------------------- | ------------------------------------------------------------------------------------- | ------------------------ | -------------- | ---------------------------------------------------------------- |
| Initialize APPL-RESULT before open  | MOVE 8 TO APPL-RESULT (sentinel before OPEN -- if file system hangs, result = 8)      | Literal 8                | APPL-RESULT    | 0000-CUSTFILE-OPEN line 119                                      |
| Reset APPL-RESULT to zero (open ok) | MOVE 0 TO APPL-RESULT on CUSTFILE-STATUS = '00'                                       | Literal 0                | APPL-RESULT    | 0000-CUSTFILE-OPEN line 122                                      |
| Set APPL-RESULT to error (open)     | MOVE 12 TO APPL-RESULT on open failure                                                | Literal 12               | APPL-RESULT    | 0000-CUSTFILE-OPEN line 124                                      |
| Reset APPL-RESULT to zero (read ok) | MOVE 0 TO APPL-RESULT on CUSTFILE-STATUS = '00'                                       | Literal 0                | APPL-RESULT    | 1000-CUSTFILE-GET-NEXT line 95                                   |
| Set APPL-RESULT for EOF             | MOVE 16 TO APPL-RESULT on CUSTFILE-STATUS = '10'; 88 APPL-EOF condition fires         | Literal 16               | APPL-RESULT    | 1000-CUSTFILE-GET-NEXT line 99                                   |
| Set APPL-RESULT to error (read)     | MOVE 12 TO APPL-RESULT on any other status                                            | Literal 12               | APPL-RESULT    | 1000-CUSTFILE-GET-NEXT line 101                                  |
| Initialize APPL-RESULT before close | ADD 8 TO ZERO GIVING APPL-RESULT (sentinel before CLOSE)                              | Literal 8, ZERO          | APPL-RESULT    | 9000-CUSTFILE-CLOSE line 137                                     |
| Reset APPL-RESULT to zero (close)   | SUBTRACT APPL-RESULT FROM APPL-RESULT (self-subtract = zero) on CUSTFILE-STATUS = '00' | APPL-RESULT             | APPL-RESULT    | 9000-CUSTFILE-CLOSE line 140                                     |
| Set APPL-RESULT to error (close)    | ADD 12 TO ZERO GIVING APPL-RESULT on close failure                                    | Literal 12, ZERO         | APPL-RESULT    | 9000-CUSTFILE-CLOSE line 142                                     |
| Convert status byte 2 to integer    | MOVE 0 TO TWO-BYTES-BINARY; MOVE IO-STAT2 TO TWO-BYTES-RIGHT; TWO-BYTES-BINARY (BINARY redefine of TWO-BYTES-ALPHA) holds integer value; MOVE to IO-STATUS-0403 | IO-STAT2, TWO-BYTES-BINARY | IO-STATUS-0403 | Z-DISPLAY-IO-STATUS lines 165-167 |

## Error Handling

| Condition                             | Action                                                                                      | Return Code | Source Location         |
| ------------------------------------- | ------------------------------------------------------------------------------------------- | ----------- | ----------------------- |
| CUSTFILE-STATUS != '00' on OPEN       | DISPLAY 'ERROR OPENING CUSTFILE'; PERFORM Z-DISPLAY-IO-STATUS; PERFORM Z-ABEND-PROGRAM      | Abend 999   | 0000-CUSTFILE-OPEN      |
| CUSTFILE-STATUS = '10' on READ        | Set END-OF-FILE = 'Y' (via APPL-EOF 88-level); loop terminates normally                    | None        | 1000-CUSTFILE-GET-NEXT  |
| CUSTFILE-STATUS not '00'/'10' on READ | DISPLAY 'ERROR READING CUSTOMER FILE'; PERFORM Z-DISPLAY-IO-STATUS; PERFORM Z-ABEND-PROGRAM | Abend 999   | 1000-CUSTFILE-GET-NEXT  |
| CUSTFILE-STATUS != '00' on CLOSE      | DISPLAY 'ERROR CLOSING CUSTOMER FILE'; PERFORM Z-DISPLAY-IO-STATUS; PERFORM Z-ABEND-PROGRAM | Abend 999   | 9000-CUSTFILE-CLOSE     |
| Any unrecoverable I/O error           | DISPLAY 'ABENDING PROGRAM'; MOVE 0 TO TIMING; MOVE 999 TO ABCODE; CALL 'CEE3ABD' USING ABCODE, TIMING | Abend 999 | Z-ABEND-PROGRAM      |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. PROCEDURE DIVISION inline (line 71) -- DISPLAY 'START OF EXECUTION OF PROGRAM CBCUS01C'
2. 0000-CUSTFILE-OPEN (line 72) -- MOVE 8 TO APPL-RESULT; OPEN INPUT CUSTFILE-FILE; check CUSTFILE-STATUS; abend if != '00'
3. PERFORM UNTIL END-OF-FILE = 'Y' (line 74) -- main read loop; outer `IF END-OF-FILE = 'N'` at line 75 (redundant outer guard)
4. 1000-CUSTFILE-GET-NEXT (line 76) -- READ CUSTFILE-FILE INTO CUSTOMER-RECORD; on status '00': DISPLAY CUSTOMER-RECORD (first display); on status '10': MOVE 16 to APPL-RESULT then via 88 APPL-EOF MOVE 'Y' to END-OF-FILE; on other status: abend
5. Inner `IF END-OF-FILE = 'N'` (line 77) -- redundant inner guard; when true: DISPLAY CUSTOMER-RECORD (second display, line 78)
6. Loop repeats from step 3 until END-OF-FILE = 'Y'
7. 9000-CUSTFILE-CLOSE (line 83) -- ADD 8 TO ZERO GIVING APPL-RESULT; CLOSE CUSTFILE-FILE; check CUSTFILE-STATUS; abend if != '00'
8. PROCEDURE DIVISION inline (line 85) -- DISPLAY 'END OF EXECUTION OF PROGRAM CBCUS01C'; GOBACK

Error sub-routines (called on I/O failure only):

- Z-DISPLAY-IO-STATUS (line 161) -- copies CUSTFILE-STATUS to IO-STATUS; formats IO-STAT1/IO-STAT2 into IO-STATUS-04 (4-character printable diagnostic); handles both standard numeric (2-digit, IO-STAT1 != '9') and vendor-extended ('9x', IO-STAT1 = '9') status codes by different formatting paths; DISPLAY output is literal string 'FILE STATUS IS: NNNN' followed by IO-STATUS-04 (the 'NNNN' is a fixed label in the source, not a substitution token)
- Z-ABEND-PROGRAM (line 154) -- DISPLAY 'ABENDING PROGRAM'; MOVE 0 TO TIMING; MOVE 999 TO ABCODE; CALL 'CEE3ABD' USING ABCODE, TIMING; program does not return from this call; this paragraph has no EXIT statement (unlike all other paragraphs)
