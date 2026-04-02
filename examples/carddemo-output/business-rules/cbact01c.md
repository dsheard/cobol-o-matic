---
type: business-rules
program: CBACT01C
program_type: batch
status: draft
confidence: high
last_pass: 3
calls:
- CEE3ABD
- COBDATFT
called_by: []
uses_copybooks:
- CODATECN
- CVACT01Y
reads:
- ACCTFILE-FILE
writes:
- OUT-FILE
- ARRY-FILE
- VBRC-FILE
db_tables: []
transactions: []
mq_queues: []
---

# CBACT01C -- Business Rules

## Program Purpose

CBACT01C is a batch COBOL program that sequentially reads all records from the ACCTFILE VSAM KSDS (account master file) and writes derived output to three separate output files: a fixed-length sequential flat file (OUT-FILE), a fixed-length sequential array record file (ARRY-FILE), and a variable-length record file (VBRC-FILE). For each account record read, the program displays the account fields to SYSOUT (twice: once as a raw record dump and once as labeled individual fields), formats the reissue date via an external date-conversion routine (COBDATFT), applies a default debit value when the cycle debit is zero, populates two variable-length record formats (VBR1 and VBR2), and writes all three output representations. The program abends with code 999 via CEE3ABD on any I/O error. Notably, only ACCTFILE is explicitly closed; the three output files (OUT-FILE, ARRY-FILE, VBRC-FILE) rely on implicit JCL/OS close at GOBACK.

## Input / Output

| Direction | Resource     | Type | Description                                                                                  |
| --------- | ------------ | ---- | -------------------------------------------------------------------------------------------- |
| IN        | ACCTFILE-FILE | File (VSAM KSDS, sequential access) | Account master file; record key FD-ACCT-ID (9(11)); record length 300 bytes |
| OUT       | OUT-FILE     | File (sequential fixed) | Fixed-length output of all account fields including formatted reissue date and default debit |
| OUT       | ARRY-FILE    | File (sequential fixed) | Array record output; account ID plus 5-occurrence balance/debit array (only slots 1-3 populated) |
| OUT       | VBRC-FILE    | File (sequential variable, 10-80 bytes per FD; actual minimum 12 bytes) | Variable-length records; two record types per account: VBR1 (12 bytes: ID + active status) and VBR2 (39 bytes: ID + bal + credit limit + reissue year) |

## Business Rules

### File Open / Initialisation

| #  | Rule                           | Condition                              | Action                                                                                     | Source Location   |
| -- | ------------------------------ | -------------------------------------- | ------------------------------------------------------------------------------------------ | ----------------- |
| 1  | ACCTFILE must open successfully | ACCTFILE-STATUS not equal '00' after OPEN INPUT | Display 'ERROR OPENING ACCTFILE', display I/O status, call CEE3ABD abend (code 999)        | 0000-ACCTFILE-OPEN |
| 2  | OUT-FILE must open successfully | OUTFILE-STATUS not equal '00' after OPEN OUTPUT | Display 'ERROR OPENING OUTFILE' + status, display I/O status, call CEE3ABD abend (code 999) | 2000-OUTFILE-OPEN |
| 3  | ARRY-FILE must open successfully | ARRYFILE-STATUS not equal '00' after OPEN OUTPUT | Display 'ERROR OPENING ARRAYFILE' + status, display I/O status, call CEE3ABD abend (code 999) | 3000-ARRFILE-OPEN |
| 4  | VBRC-FILE must open successfully | VBRCFILE-STATUS not equal '00' after OPEN OUTPUT | Display 'ERROR OPENING VBRC FILE' + status, display I/O status, call CEE3ABD abend (code 999) | 4000-VBRFILE-OPEN |
| 5  | APPL-RESULT is pre-set to 8 before each OPEN | Unconditional | MOVE 8 TO APPL-RESULT before each OPEN statement; 0 on success, 12 on failure              | 0000, 2000, 3000, 4000 |

### Account Record Read Loop

| #  | Rule                                   | Condition                                                    | Action                                                                          | Source Location        |
| -- | -------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------- | ---------------------- |
| 6  | Loop continues until end-of-file       | PERFORM UNTIL END-OF-FILE = 'Y'                              | Repeatedly call 1000-ACCTFILE-GET-NEXT; display record; stop on EOF flag        | PROCEDURE DIVISION main |
| 7  | Guard against re-entry at EOF          | IF END-OF-FILE = 'N' before reading                          | Only attempt the READ when flag is still 'N'                                    | PROCEDURE DIVISION main |
| 8  | Raw record display to SYSOUT after each successful read | END-OF-FILE = 'N' after 1000-ACCTFILE-GET-NEXT returns | DISPLAY ACCOUNT-RECORD (entire raw 300-byte record as one output line) -- this is in addition to the labeled field-by-field display in 1100 | PROCEDURE DIVISION main, line 151 |
| 9  | Labeled field-by-field display to SYSOUT | ACCTFILE-STATUS = '00' inside 1000 (unconditional for each successful read) | PERFORM 1100-DISPLAY-ACCT-RECORD: 11 labeled DISPLAY statements plus a separator line | 1100-DISPLAY-ACCT-RECORD (called from 1000) |
| 10 | Successful read triggers full processing pipeline | ACCTFILE-STATUS = '00'                             | MOVE 0 TO APPL-RESULT; INITIALIZE ARR-ARRAY-REC; perform 1100, 1300, 1350, 1400, 1450, 1500, 1550, 1575 | 1000-ACCTFILE-GET-NEXT |
| 11 | EOF detection on sequential read       | ACCTFILE-STATUS = '10'                                       | MOVE 16 TO APPL-RESULT (88 APPL-EOF triggers END-OF-FILE = 'Y')                | 1000-ACCTFILE-GET-NEXT |
| 12 | Unexpected read error causes abend     | ACCTFILE-STATUS not '00' and not '10'                        | MOVE 12 TO APPL-RESULT; display 'ERROR READING ACCOUNT FILE'; display I/O status; call CEE3ABD abend (code 999) | 1000-ACCTFILE-GET-NEXT |
| 13 | APPL-EOF sets end-of-file flag         | 88 APPL-EOF VALUE 16 (APPL-RESULT = 16)                      | MOVE 'Y' TO END-OF-FILE                                                         | 1000-ACCTFILE-GET-NEXT |

### Account Record Population for OUT-FILE

| #  | Rule                                                   | Condition                                        | Action                                                                                                     | Source Location      |
| -- | ------------------------------------------------------ | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- | -------------------- |
| 14 | All account fields are mapped to output record         | Unconditional for each successfully read record  | MOVE each source field (ACCT-ID, ACCT-ACTIVE-STATUS, ACCT-CURR-BAL, ACCT-CREDIT-LIMIT, ACCT-CASH-CREDIT-LIMIT, ACCT-OPEN-DATE, ACCT-EXPIRAION-DATE, ACCT-CURR-CYC-CREDIT, ACCT-GROUP-ID) to corresponding OUT-ACCT-* fields | 1300-POPUL-ACCT-RECORD |
| 15 | ACCT-ADDR-ZIP is silently excluded from OUT-FILE output | Unconditional | ACCT-ADDR-ZIP is present in ACCOUNT-RECORD (CVACT01Y) but is not moved to any OUT-ACCT-* field in 1300-POPUL-ACCT-RECORD; it is permanently dropped from all three output files | 1300-POPUL-ACCT-RECORD (absence) |
| 16 | Reissue date is formatted via external conversion      | Unconditional; CODATECN-TYPE = '2' (YYYY-MM-DD input); CODATECN-OUTTYPE = '2' (YYYYMMDD output) | MOVE ACCT-REISSUE-DATE TO CODATECN-INP-DATE and WS-REISSUE-DATE; CALL 'COBDATFT' USING CODATECN-REC; MOVE CODATECN-0UT-DATE TO OUT-ACCT-REISSUE-DATE | 1300-POPUL-ACCT-RECORD |
| 17 | Zero current cycle debit receives a default value      | ACCT-CURR-CYC-DEBIT EQUAL TO ZERO                | MOVE 2525.00 TO OUT-ACCT-CURR-CYC-DEBIT                                                                    | 1300-POPUL-ACCT-RECORD |
| 18 | Non-zero current cycle debit is not copied to output   | ACCT-CURR-CYC-DEBIT NOT EQUAL TO ZERO (implicit; no ELSE branch) | No MOVE performed; OUT-ACCT-CURR-CYC-DEBIT (COMP-3 in FD) retains whatever value is in the output record buffer (initialised to zero by the OS on first use, then retains the previous record's buffer value for subsequent records) | 1300-POPUL-ACCT-RECORD |

### OUT-FILE Write

| #  | Rule                             | Condition                                                                 | Action                                                                                           | Source Location      |
| -- | -------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | -------------------- |
| 19 | OUT-FILE write must succeed      | OUTFILE-STATUS not '00' AND not '10' after WRITE OUT-ACCT-REC             | Display 'ACCOUNT FILE WRITE STATUS IS:' + OUTFILE-STATUS; display I/O status; call CEE3ABD abend (code 999) | 1350-WRITE-ACCT-RECORD |

### Array Record Population for ARRY-FILE

| #  | Rule                                                      | Condition      | Action                                                                                                          | Source Location      |
| -- | --------------------------------------------------------- | -------------- | --------------------------------------------------------------------------------------------------------------- | -------------------- |
| 20 | ARRY-FILE record initialised before population            | Unconditional  | INITIALIZE ARR-ARRAY-REC (performed before 1400-POPUL-ARRAY-RECORD)                                             | 1000-ACCTFILE-GET-NEXT |
| 21 | Account ID is copied to array record                      | Unconditional  | MOVE ACCT-ID TO ARR-ACCT-ID                                                                                     | 1400-POPUL-ARRAY-RECORD |
| 22 | Array slot 1 receives actual current balance              | Unconditional  | MOVE ACCT-CURR-BAL TO ARR-ACCT-CURR-BAL(1)                                                                     | 1400-POPUL-ARRAY-RECORD |
| 23 | Array slot 1 cycle debit is hardcoded to 1005.00          | Unconditional  | MOVE 1005.00 TO ARR-ACCT-CURR-CYC-DEBIT(1)                                                                     | 1400-POPUL-ARRAY-RECORD |
| 24 | Array slot 2 receives actual current balance              | Unconditional  | MOVE ACCT-CURR-BAL TO ARR-ACCT-CURR-BAL(2)                                                                     | 1400-POPUL-ARRAY-RECORD |
| 25 | Array slot 2 cycle debit is hardcoded to 1525.00          | Unconditional  | MOVE 1525.00 TO ARR-ACCT-CURR-CYC-DEBIT(2)                                                                     | 1400-POPUL-ARRAY-RECORD |
| 26 | Array slot 3 balance is hardcoded to -1025.00             | Unconditional  | MOVE -1025.00 TO ARR-ACCT-CURR-BAL(3)                                                                          | 1400-POPUL-ARRAY-RECORD |
| 27 | Array slot 3 cycle debit is hardcoded to -2500.00         | Unconditional  | MOVE -2500.00 TO ARR-ACCT-CURR-CYC-DEBIT(3)                                                                    | 1400-POPUL-ARRAY-RECORD |
| 28 | Array slots 4 and 5 remain at initialised (zero) values   | Unconditional  | No MOVEs for slots 4 and 5; left at INITIALIZE values                                                           | 1400-POPUL-ARRAY-RECORD |

### ARRY-FILE Write

| #  | Rule                              | Condition                                                                   | Action                                                                                                           | Source Location     |
| -- | --------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------- |
| 29 | ARRY-FILE write must succeed      | ARRYFILE-STATUS not '00' AND not '10' after WRITE ARR-ARRAY-REC             | Display 'ACCOUNT FILE WRITE STATUS IS:' + ARRYFILE-STATUS; display I/O status; call CEE3ABD abend (code 999)    | 1450-WRITE-ARRY-RECORD |

### Variable-Length Record Population for VBRC-FILE

| #  | Rule                                                        | Condition      | Action                                                                                                           | Source Location      |
| -- | ----------------------------------------------------------- | -------------- | ---------------------------------------------------------------------------------------------------------------- | -------------------- |
| 30 | VBRC-REC1 initialised before population                     | Unconditional  | INITIALIZE VBRC-REC1 (performed before 1500-POPUL-VBRC-RECORD)                                                  | 1000-ACCTFILE-GET-NEXT |
| 31 | Both VBR record types receive the same account ID           | Unconditional  | MOVE ACCT-ID TO VB1-ACCT-ID and VB2-ACCT-ID                                                                    | 1500-POPUL-VBRC-RECORD |
| 32 | VBR1 receives account active status                         | Unconditional  | MOVE ACCT-ACTIVE-STATUS TO VB1-ACCT-ACTIVE-STATUS                                                               | 1500-POPUL-VBRC-RECORD |
| 33 | VBR2 receives current balance                               | Unconditional  | MOVE ACCT-CURR-BAL TO VB2-ACCT-CURR-BAL                                                                         | 1500-POPUL-VBRC-RECORD |
| 34 | VBR2 receives credit limit                                  | Unconditional  | MOVE ACCT-CREDIT-LIMIT TO VB2-ACCT-CREDIT-LIMIT                                                                 | 1500-POPUL-VBRC-RECORD |
| 35 | VBR2 receives the year portion of the reissue date directly from the source record | Unconditional | MOVE WS-ACCT-REISSUE-YYYY TO VB2-ACCT-REISSUE-YYYY. WS-ACCT-REISSUE-YYYY is the first 4 bytes of WS-ACCT-REISSUE-DATE, which was populated in 1300 by: MOVE ACCT-REISSUE-DATE TO WS-REISSUE-DATE (a REDEFINES of WS-ACCT-REISSUE-DATE). The year value therefore comes directly from ACCT-REISSUE-DATE characters 1-4 -- it is NOT derived from the COBDATFT conversion output (CODATECN-0UT-DATE). | 1500-POPUL-VBRC-RECORD |
| 36 | Both VBR records are displayed to SYSOUT before writing     | Unconditional  | DISPLAY 'VBRC-REC1:' VBRC-REC1; DISPLAY 'VBRC-REC2:' VBRC-REC2                                                 | 1500-POPUL-VBRC-RECORD |

### VBRC-FILE Write -- VBR1 Record

| #  | Rule                                            | Condition                                                                    | Action                                                                                                           | Source Location     |
| -- | ----------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------- |
| 37 | VBR1 record length is fixed at 12 bytes          | Unconditional                                                                | MOVE 12 TO WS-RECD-LEN; copy VBRC-REC1 into VBR-REC(1:12) before WRITE                                        | 1550-WRITE-VB1-RECORD |
| 38 | VBRC-FILE VBR1 write must succeed               | VBRCFILE-STATUS not '00' AND not '10' after WRITE VBR-REC                   | Display 'ACCOUNT FILE WRITE STATUS IS:' + VBRCFILE-STATUS; display I/O status; call CEE3ABD abend (code 999)    | 1550-WRITE-VB1-RECORD |

### VBRC-FILE Write -- VBR2 Record

| #  | Rule                                            | Condition                                                                    | Action                                                                                                           | Source Location     |
| -- | ----------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------- |
| 39 | VBR2 record length is fixed at 39 bytes          | Unconditional                                                                | MOVE 39 TO WS-RECD-LEN; copy VBRC-REC2 into VBR-REC(1:39) before WRITE                                        | 1575-WRITE-VB2-RECORD |
| 40 | VBRC-FILE VBR2 write must succeed               | VBRCFILE-STATUS not '00' AND not '10' after WRITE VBR-REC                   | Display 'ACCOUNT FILE WRITE STATUS IS:' + VBRCFILE-STATUS; display I/O status; call CEE3ABD abend (code 999)    | 1575-WRITE-VB2-RECORD |

### File Close

| #  | Rule                                     | Condition                                                          | Action                                                                                              | Source Location    |
| -- | ---------------------------------------- | ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- | ------------------ |
| 41 | ACCTFILE must close successfully          | ACCTFILE-STATUS not '00' after CLOSE ACCTFILE-FILE                | Display 'ERROR CLOSING ACCOUNT FILE'; display I/O status; call CEE3ABD abend (code 999)            | 9000-ACCTFILE-CLOSE |
| 42 | APPL-RESULT initialised via arithmetic before CLOSE | Unconditional                                             | ADD 8 TO ZERO GIVING APPL-RESULT; on success SUBTRACT APPL-RESULT FROM APPL-RESULT (sets to 0); on fail ADD 12 TO ZERO GIVING APPL-RESULT | 9000-ACCTFILE-CLOSE |
| 43 | OUT-FILE, ARRY-FILE, and VBRC-FILE are never explicitly closed | Unconditional (no CLOSE statements exist for these files) | No CLOSE is issued for the three output files; they are implicitly closed by the OS/JCL when the program issues GOBACK. This means file buffers are not explicitly flushed by the program. | Program-wide (absence) |

## Calculations

| Calculation                       | Formula / Logic                                                                                                             | Input Fields                              | Output Field                  | Source Location        |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- | ----------------------------- | ---------------------- |
| Default cycle debit substitution  | If ACCT-CURR-CYC-DEBIT = 0 then output value = 2525.00 (literal); otherwise OUT-ACCT-CURR-CYC-DEBIT is not updated (retains prior buffer contents -- no ELSE branch) | ACCT-CURR-CYC-DEBIT                       | OUT-ACCT-CURR-CYC-DEBIT       | 1300-POPUL-ACCT-RECORD |
| Reissue date conversion           | External assembler routine COBDATFT converts YYYY-MM-DD input (CODATECN-TYPE='2', 88 YYYY-MM-DD-IN) to YYYYMMDD output (CODATECN-OUTTYPE='2', 88 YYYYMMDD-OP) per CODATECN contract | ACCT-REISSUE-DATE -> CODATECN-INP-DATE, CODATECN-TYPE='2', CODATECN-OUTTYPE='2' | OUT-ACCT-REISSUE-DATE (via CODATECN-0UT-DATE) | 1300-POPUL-ACCT-RECORD |
| Reissue year extraction for VBR2  | Direct character extraction -- first 4 bytes of ACCT-REISSUE-DATE via REDEFINES overlay (WS-REISSUE-DATE over WS-ACCT-REISSUE-DATE); NOT derived from COBDATFT output | ACCT-REISSUE-DATE (characters 1-4 = YYYY) | VB2-ACCT-REISSUE-YYYY         | 1300-POPUL-ACCT-RECORD (MOVE), 1500-POPUL-VBRC-RECORD (use) |
| APPL-RESULT reset to 0 (success)  | SUBTRACT APPL-RESULT FROM APPL-RESULT (idiomatic zero-set)                                                                  | APPL-RESULT                               | APPL-RESULT = 0               | 9000-ACCTFILE-CLOSE    |
| APPL-RESULT set to 8 (pending)    | ADD 8 TO ZERO GIVING APPL-RESULT                                                                                            | Literal 8                                 | APPL-RESULT = 8               | 9000-ACCTFILE-CLOSE    |

## Error Handling

| Condition                                       | Action                                                                                                         | Return Code            | Source Location          |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ---------------------- | ------------------------ |
| ACCTFILE-STATUS not '00' on OPEN               | Display 'ERROR OPENING ACCTFILE'; display 4-digit decoded I/O status; CALL 'CEE3ABD' USING 999, 0             | Abend 999              | 0000-ACCTFILE-OPEN       |
| OUTFILE-STATUS not '00' on OPEN                | Display 'ERROR OPENING OUTFILE' + raw status; display decoded status; CALL 'CEE3ABD' USING 999, 0             | Abend 999              | 2000-OUTFILE-OPEN        |
| ARRYFILE-STATUS not '00' on OPEN               | Display 'ERROR OPENING ARRAYFILE' + raw status; display decoded status; CALL 'CEE3ABD' USING 999, 0           | Abend 999              | 3000-ARRFILE-OPEN        |
| VBRCFILE-STATUS not '00' on OPEN               | Display 'ERROR OPENING VBRC FILE' + raw status; display decoded status; CALL 'CEE3ABD' USING 999, 0           | Abend 999              | 4000-VBRFILE-OPEN        |
| ACCTFILE-STATUS = '10' on READ                 | MOVE 16 TO APPL-RESULT; 88 APPL-EOF fires; END-OF-FILE set to 'Y'; loop terminates normally                   | None (normal EOF)      | 1000-ACCTFILE-GET-NEXT   |
| ACCTFILE-STATUS not '00' and not '10' on READ  | Display 'ERROR READING ACCOUNT FILE'; display decoded I/O status; CALL 'CEE3ABD' USING 999, 0                 | Abend 999              | 1000-ACCTFILE-GET-NEXT   |
| OUTFILE-STATUS not '00' and not '10' on WRITE  | Display 'ACCOUNT FILE WRITE STATUS IS:' + OUTFILE-STATUS; display decoded status; CALL 'CEE3ABD' USING 999, 0 | Abend 999              | 1350-WRITE-ACCT-RECORD   |
| ARRYFILE-STATUS not '00' and not '10' on WRITE | Display 'ACCOUNT FILE WRITE STATUS IS:' + ARRYFILE-STATUS; display decoded status; CALL 'CEE3ABD' USING 999, 0 | Abend 999             | 1450-WRITE-ARRY-RECORD   |
| VBRCFILE-STATUS not '00' and not '10' on WRITE (VBR1) | Display 'ACCOUNT FILE WRITE STATUS IS:' + VBRCFILE-STATUS; display decoded status; CALL 'CEE3ABD' USING 999, 0 | Abend 999        | 1550-WRITE-VB1-RECORD    |
| VBRCFILE-STATUS not '00' and not '10' on WRITE (VBR2) | Display 'ACCOUNT FILE WRITE STATUS IS:' + VBRCFILE-STATUS; display decoded status; CALL 'CEE3ABD' USING 999, 0 | Abend 999        | 1575-WRITE-VB2-RECORD    |
| ACCTFILE-STATUS not '00' on CLOSE              | Display 'ERROR CLOSING ACCOUNT FILE'; display decoded status; CALL 'CEE3ABD' USING 999, 0                     | Abend 999              | 9000-ACCTFILE-CLOSE      |
| Any I/O error (non-numeric status or stat1='9')| 9910-DISPLAY-IO-STATUS: decode status using BINARY overlay for vendor-specific codes; display 'FILE STATUS IS: NNNN' + decoded 4-digit value | N/A (diagnostic only) | 9910-DISPLAY-IO-STATUS |
| Abend entry point                              | 9999-ABEND-PROGRAM: DISPLAY 'ABENDING PROGRAM'; MOVE 0 TO TIMING; MOVE 999 TO ABCODE; CALL 'CEE3ABD' USING ABCODE, TIMING | ABCODE=999, TIMING=0 | 9999-ABEND-PROGRAM     |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. DISPLAY 'START OF EXECUTION OF PROGRAM CBACT01C' -- announce start
2. 0000-ACCTFILE-OPEN -- open ACCTFILE for INPUT; abend on failure
3. 2000-OUTFILE-OPEN -- open OUT-FILE for OUTPUT; abend on failure
4. 3000-ARRFILE-OPEN -- open ARRY-FILE for OUTPUT; abend on failure
5. 4000-VBRFILE-OPEN -- open VBRC-FILE for OUTPUT; abend on failure
6. PERFORM UNTIL END-OF-FILE = 'Y' -- main processing loop:
   - IF END-OF-FILE = 'N': PERFORM 1000-ACCTFILE-GET-NEXT
     - Inside 1000, on status '00': INITIALIZE ARR-ARRAY-REC; then PERFORM in sequence:
       - 1100-DISPLAY-ACCT-RECORD -- DISPLAY 11 labeled account fields to SYSOUT + separator line
       - 1300-POPUL-ACCT-RECORD -- map fields to OUT-ACCT-REC; MOVE ACCT-REISSUE-DATE to both CODATECN-INP-DATE and WS-REISSUE-DATE; CALL 'COBDATFT' for date conversion; MOVE converted date to OUT-ACCT-REISSUE-DATE; apply default debit (2525.00) if cycle debit is zero; note ACCT-ADDR-ZIP is not mapped
       - 1350-WRITE-ACCT-RECORD -- WRITE OUT-ACCT-REC; abend on write error
       - 1400-POPUL-ARRAY-RECORD -- populate ARR-ARRAY-REC (slots 1-3 with mix of live and hardcoded values; slots 4-5 zeroed by INITIALIZE)
       - 1450-WRITE-ARRY-RECORD -- WRITE ARR-ARRAY-REC; abend on write error
       - INITIALIZE VBRC-REC1
       - 1500-POPUL-VBRC-RECORD -- populate VBR1 and VBR2 working storage records; VBR2 year taken from WS-ACCT-REISSUE-YYYY (source date, not COBDATFT output); DISPLAY both to SYSOUT
       - 1550-WRITE-VB1-RECORD -- MOVE 12 TO WS-RECD-LEN; WRITE VBR-REC (VBR1 content); abend on write error
       - 1575-WRITE-VB2-RECORD -- MOVE 39 TO WS-RECD-LEN; WRITE VBR-REC (VBR2 content); abend on write error
     - Inside 1000, on status '10' (EOF): MOVE 16 TO APPL-RESULT; APPL-EOF fires; END-OF-FILE set to 'Y'
     - Inside 1000, on other status: MOVE 12 TO APPL-RESULT; abend
   - After 1000 returns: IF END-OF-FILE = 'N': DISPLAY ACCOUNT-RECORD (raw 300-byte record dump to SYSOUT)
7. 9000-ACCTFILE-CLOSE -- CLOSE ACCTFILE-FILE; abend on failure (OUT-FILE, ARRY-FILE, VBRC-FILE are NOT explicitly closed)
8. DISPLAY 'END OF EXECUTION OF PROGRAM CBACT01C' -- announce completion
9. GOBACK -- return to caller / JCL; OS implicitly closes remaining open files
