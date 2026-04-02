---
type: business-rules
program: CRDTAGY1
program_type: online
status: draft
confidence: high
last_pass: 4
calls:
- ABNDPROC
called_by:
- CRECUST
uses_copybooks:
- ABNDINFO
- SORTCODE
reads: []
writes: []
db_tables: []
transactions: []
mq_queues: []
---

# CRDTAGY1 -- Business Rules

## Program Purpose

CRDTAGY1 is a dummy credit-agency stub invoked asynchronously by CRECUST via the CICS Async API. It simulates a remote credit-agency call by:

1. Delaying for a random number of seconds (1--3) to emulate network/processing latency.
2. Reading the input customer data from a CICS channel/container (`CIPCREDCHANN` / `CIPA`).
3. Generating a random credit score between 1 and 999.
4. Writing the credit score back into the same container so the parent program (CRECUST) can retrieve it.

There is intentionally a 1-in-4 chance the delay reaches 3 seconds, which may exceed the parent's 3-second timeout, causing the parent to proceed without this agency's score -- emulating unreliable third-party credit-agency responses. CRDTAGY1 does not perform any database or file I/O of its own.

Note: The program header comment states "between 0 and 3 seconds" but the actual COMPUTE formula `((3 - 1) * FUNCTION RANDOM(WS-SEED)) + 1` produces values in the range 1--3, not 0--3. The code governs.

## Input / Output

| Direction | Resource       | Type             | Description                                                                                                   |
| --------- | -------------- | ---------------- | ------------------------------------------------------------------------------------------------------------- |
| IN        | CIPCREDCHANN   | CICS Channel     | Channel name carrying the `CIPA` container with customer data                                                 |
| IN        | CIPA           | CICS Container   | Input container: customer sort code, account number, name, address, DOB, existing credit score, review date, success flag (WS-CONT-IN-SUCCESS PIC X), fail code (WS-CONT-IN-FAIL-CODE PIC X) |
| OUT       | CIPA           | CICS Container   | Same container returned with `WS-CONT-IN-CREDIT-SCORE` overwritten with the newly generated random credit score; all other fields (including SUCCESS and FAIL-CODE) are passed through unmodified |
| OUT       | ABNDPROC       | CICS LINK        | Abend handler program called if CICS DELAY fails; receives ABNDINFO-REC commarea                              |

## Business Rules

### Credit Score Generation

| #   | Rule                                                        | Condition                                         | Action                                                                                                                                                      | Source Location          |
| --- | ----------------------------------------------------------- | ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| 1   | Random delay 1--3 seconds                                   | Always on entry                                   | COMPUTE WS-DELAY-AMT = ((3 - 1) * FUNCTION RANDOM(WS-SEED)) + 1; then EXEC CICS DELAY FOR SECONDS(WS-DELAY-AMT)                                            | A010 lines 124--131      |
| 2   | Delay seed derived from task number                         | Always on entry                                   | MOVE EIBTASKN TO WS-SEED; used as seed for FUNCTION RANDOM to ensure each task gets a different delay                                                       | A010 line 122            |
| 3   | Credit score range 1--999                                   | After container GET succeeds                      | COMPUTE WS-NEW-CREDSCORE = ((999 - 1) * FUNCTION RANDOM) + 1; result is PIC 999 (maximum 999)                                                              | A010 lines 215--216      |
| 4   | Credit score written back to container                      | After score generation                            | MOVE WS-NEW-CREDSCORE TO WS-CONT-IN-CREDIT-SCORE; replaces any existing credit score value in the container                                                 | A010 line 218            |
| 5   | Container and channel names are fixed literals              | Always                                            | WS-CONTAINER-NAME set to 'CIPA            ' (16-char, space padded); WS-CHANNEL-NAME set to 'CIPCREDCHANN    '                                              | A010 lines 120--121      |
| 6   | Timeout emulation (up to 1-in-4 chance of exceeding parent wait) | WS-DELAY-AMT may reach 3 seconds           | Parent CRECUST waits up to 3 seconds; if this stub delays 3 seconds the parent may time out before receiving the score                                       | Program header comment   |
| 7   | SUCCESS and FAIL-CODE fields passed through unmodified      | Always                                            | WS-CONT-IN-SUCCESS (PIC X) and WS-CONT-IN-FAIL-CODE (PIC X) are received in the container but never written by CRDTAGY1; returned to parent with original values | A010 (no assignment)  |

### Asynchronous Execution Model

| #   | Rule                                        | Condition                     | Action                                                                                                      | Source Location        |
| --- | ------------------------------------------- | ----------------------------- | ----------------------------------------------------------------------------------------------------------- | ---------------------- |
| 8   | Program is driven by CICS Async API         | Invoked by parent CRECUST     | Data exchanged via CICS channels/containers only -- no DFHCOMMAREA linkage                                  | Program header         |
| 9   | No direct return value to parent            | On normal completion          | EXEC CICS RETURN (no TRANSID); parent retrieves score by fetching the container after timeout               | GET-ME-OUT-OF-HERE     |

## Calculations

| Calculation           | Formula / Logic                                                                  | Input Fields                    | Output Field                      | Source Location         |
| --------------------- | -------------------------------------------------------------------------------- | ------------------------------- | --------------------------------- | ----------------------- |
| Random delay amount   | WS-DELAY-AMT = ((3 - 1) * FUNCTION RANDOM(WS-SEED)) + 1                         | WS-SEED (= EIBTASKN)            | WS-DELAY-AMT (S9(8) COMP)         | A010 lines 124--125     |
| Container data length | WS-CONTAINER-LEN = LENGTH OF WS-CONT-IN                                          | WS-CONT-IN (247 bytes)          | WS-CONTAINER-LEN (S9(8) COMP)     | A010 lines 190, 223     |
| Random credit score   | WS-NEW-CREDSCORE = ((999 - 1) * FUNCTION RANDOM) + 1                             | Seeded from prior RANDOM call   | WS-NEW-CREDSCORE (PIC 999)        | A010 lines 215--216     |

Notes on calculations:
- The RANDOM function is called with a SEED on the first invocation (delay) and without a seed on the second invocation (credit score), as COBOL RANDOM maintains internal state after seeding.
- WS-DELAY-AMT is declared S9(8) COMP but holds a value of 1, 2, or 3 (integer truncation of the COMPUTE result). No ROUNDED clause; fractional part is truncated.
- WS-NEW-CREDSCORE is PIC 999 (maximum 999), which matches the formula's upper bound. No ON SIZE ERROR clause.

## Error Handling

| Condition                                | Action                                                                                                                                                                                                                                                                                                                           | Return Code / Abend Code | Source Location      |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ | -------------------- |
| CICS DELAY fails (WS-CICS-RESP not NORMAL) | INITIALIZE ABNDINFO-REC; populate ABND-RESPCODE, ABND-RESP2CODE, ABND-APPLID (via CICS ASSIGN), ABND-TASKNO-KEY, ABND-TRANID, ABND-DATE, ABND-TIME, ABND-CODE='PLOP', ABND-PROGRAM (via CICS ASSIGN), ABND-SQLCODE=0, ABND-FREEFORM='A010  - *** The delay messed up! ***'; EXEC CICS LINK PROGRAM(WS-ABEND-PGM) resolves to 'ABNDPROC'; DISPLAY '*** The delay messed up ! ***'; EXEC CICS ABEND ABCODE('PLOP') | ABCODE 'PLOP'            | A010 lines 133--188  |
| CICS GET CONTAINER fails (WS-CICS-RESP not NORMAL) | DISPLAY 'CRDTAGY1 - UNABLE TO GET CONTAINER. RESP=' WS-CICS-RESP ', RESP2=' WS-CICS-RESP2; DISPLAY container name, channel name, FLENGTH; PERFORM GET-ME-OUT-OF-HERE (EXEC CICS RETURN) | None -- silent exit      | A010 lines 200--207  |
| CICS PUT CONTAINER fails (WS-CICS-RESP not NORMAL) | DISPLAY 'CRDTAGY1 - UNABLE TO PUT CONTAINER. RESP=' WS-CICS-RESP ', RESP2=' WS-CICS-RESP2; DISPLAY container name, channel name, FLENGTH; PERFORM GET-ME-OUT-OF-HERE (EXEC CICS RETURN) | None -- silent exit      | A010 lines 233--240  |

Notes on error handling:
- The GET CONTAINER and PUT CONTAINER failure paths do NOT call ABNDPROC and do NOT ABEND; they silently return to CICS. The parent program (CRECUST) must handle missing container data by timeout.
- The DELAY failure path calls ABNDPROC (via data item WS-ABEND-PGM VALUE 'ABNDPROC', line 104) then issues a hard ABEND with code 'PLOP'. This is the only hard abend in the program.
- ABND-TIME is constructed by STRING HH:MM:MM -- the third segment at line 159 uses WS-TIME-NOW-GRP-MM again instead of WS-TIME-NOW-GRP-SS. This is a copy-paste defect in the source; the seconds field of the abend timestamp will always show the minutes value.

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. A010 -- Entry point of PREMIERE SECTION; sets container/channel names from fixed literals, seeds RANDOM from EIBTASKN
2. A010 -- COMPUTE delay amount (1--3 seconds) using FUNCTION RANDOM(WS-SEED)
3. A010 -- EXEC CICS DELAY FOR SECONDS(WS-DELAY-AMT); checks WS-CICS-RESP
4. A010 (error branch only) -- PERFORM POPULATE-TIME-DATE to obtain current date/time for abend record
5. A010 (error branch only) -- EXEC CICS LINK PROGRAM(WS-ABEND-PGM) [resolves to 'ABNDPROC']; then EXEC CICS ABEND ABCODE('PLOP')
6. A010 -- COMPUTE WS-CONTAINER-LEN = LENGTH OF WS-CONT-IN
7. A010 -- EXEC CICS GET CONTAINER('CIPA') CHANNEL('CIPCREDCHANN') INTO(WS-CONT-IN) FLENGTH(WS-CONTAINER-LEN); checks WS-CICS-RESP
8. A010 (error branch) -- PERFORM GET-ME-OUT-OF-HERE (RETURN)
9. A010 -- COMPUTE WS-NEW-CREDSCORE using FUNCTION RANDOM (no seed; uses internal state from step 2)
10. A010 -- MOVE WS-NEW-CREDSCORE TO WS-CONT-IN-CREDIT-SCORE
11. A010 -- COMPUTE WS-CONTAINER-LEN = LENGTH OF WS-CONT-IN
12. A010 -- EXEC CICS PUT CONTAINER('CIPA') FROM(WS-CONT-IN) FLENGTH(WS-CONTAINER-LEN); checks WS-CICS-RESP
13. A010 (error branch) -- PERFORM GET-ME-OUT-OF-HERE (RETURN)
14. A010 -- PERFORM GET-ME-OUT-OF-HERE (normal exit -- EXEC CICS RETURN)
15. POPULATE-TIME-DATE -- EXEC CICS ASKTIME / FORMATTIME (only reached on DELAY error)
16. GET-ME-OUT-OF-HERE -- EXEC CICS RETURN (unconditional; all exit paths lead here)
