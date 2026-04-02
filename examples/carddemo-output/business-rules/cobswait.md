---
type: business-rules
program: COBSWAIT
program_type: batch
status: draft
confidence: high
last_pass: 4
calls:
- MVSWAIT
called_by: []
uses_copybooks: []
reads: []
writes: []
db_tables: []
transactions: []
mq_queues: []
---

# COBSWAIT -- Business Rules

## Program Purpose

COBSWAIT is a batch utility program that introduces a controlled delay (wait/sleep) into a job stream. It accepts a single numeric parameter from SYSIN representing a wait duration in centiseconds, converts it to a binary (COMP) field, and passes it to the assembler/system routine MVSWAIT. The program has no file I/O, no database access, and no screen interaction. Its sole purpose is to pause batch execution for a configurable interval.

## Input / Output

| Direction | Resource   | Type    | Description                                                                                    |
| --------- | ---------- | ------- | ---------------------------------------------------------------------------------------------- |
| IN        | SYSIN      | DD/PARM | 8-byte alphanumeric parameter containing the wait duration in centiseconds (e.g., "00000100") |
| OUT       | MVSWAIT    | CALL    | Called routine that performs the actual OS-level wait using the converted numeric value        |

## Business Rules

### Wait Duration Processing

| #   | Rule                        | Condition                                     | Action                                                                                                                             | Source Location      |
| --- | --------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | -------------------- |
| 1   | Accept wait duration        | Unconditional -- program entry                | ACCEPT PARM-VALUE FROM SYSIN reads an 8-byte alphanumeric value from the SYSIN stream into PARM-VALUE (PIC X(8))                  | PROCEDURE DIVISION   |
| 2   | Convert parameter to binary | Unconditional -- after ACCEPT                 | MOVE PARM-VALUE TO MVSWAIT-TIME converts the alphanumeric SYSIN value to PIC 9(8) COMP (binary) field MVSWAIT-TIME for the CALL   | PROCEDURE DIVISION   |
| 3   | Invoke wait routine         | Unconditional -- after MOVE                   | CALL 'MVSWAIT' USING MVSWAIT-TIME passes the centisecond count to the MVSWAIT subroutine, which performs the platform-level sleep  | PROCEDURE DIVISION   |
| 4   | Terminate normally          | Unconditional -- after CALL returns           | STOP RUN terminates the batch program with normal completion; no return code is set explicitly                                     | PROCEDURE DIVISION   |

## Calculations

| Calculation        | Formula / Logic                                                                                    | Input Fields  | Output Field  | Source Location    |
| ------------------ | -------------------------------------------------------------------------------------------------- | ------------- | ------------- | ------------------ |
| Parameter coercion | MOVE PARM-VALUE TO MVSWAIT-TIME -- alphanumeric-to-numeric MOVE; implicit numeric conversion by COBOL runtime from PIC X(8) to PIC 9(8) COMP | PARM-VALUE (PIC X(8)) | MVSWAIT-TIME (PIC 9(8) COMP) | PROCEDURE DIVISION |

## Error Handling

| Condition                      | Action                                                                                                                         | Return Code | Source Location    |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ | ----------- | ------------------ |
| Non-numeric SYSIN value        | No explicit check coded; MOVE of non-numeric X(8) to 9(8) COMP will produce undefined/zero result or runtime error depending on the platform | Undefined   | PROCEDURE DIVISION |
| MVSWAIT CALL failure           | No ON EXCEPTION or ON OVERFLOW clause coded on the CALL statement; any failure in MVSWAIT is not trapped by COBSWAIT           | Undefined   | PROCEDURE DIVISION |
| Missing/empty SYSIN            | No explicit check; PARM-VALUE would be spaces; MOVE to COMP field would result in zero or runtime error                       | Undefined   | PROCEDURE DIVISION |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. ACCEPT PARM-VALUE FROM SYSIN -- reads the 8-byte centisecond wait value from the SYSIN DD
2. MOVE PARM-VALUE TO MVSWAIT-TIME -- converts alphanumeric input to binary numeric (PIC 9(8) COMP)
3. CALL 'MVSWAIT' USING MVSWAIT-TIME -- delegates the actual wait to the MVSWAIT subroutine, passing the centisecond count by reference
4. STOP RUN -- unconditional normal termination after the wait completes
