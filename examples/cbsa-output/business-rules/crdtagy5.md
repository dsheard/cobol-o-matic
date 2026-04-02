---
type: business-rules
program: CRDTAGY5
program_type: online
status: draft
confidence: high
last_pass: 2
calls:
- ABNDPROC
called_by: []
uses_copybooks:
- ABNDINFO
- SORTCODE
reads: []
writes: []
db_tables: []
transactions: []
mq_queues: []
---

# CRDTAGY5 -- Business Rules

## Program Purpose

CRDTAGY5 is a dummy credit agency stub used in the CBSA credit scoring workflow. It operates as an asynchronous child program driven via the CICS Async API. Its two responsibilities are:

1. Introduce a random processing delay of 1 to 2 seconds to simulate a real external credit agency responding at variable speed.
2. Generate a random credit score in the range 1 to 998 and write it back to the caller via a CICS channel/container.

The program header comment states the delay is "between 0 and 3 seconds" and that there is "1 in 4 chance" data will be returned within the parent's 3-second deadline. However, the actual delay formula `((3-1) * FUNCTION RANDOM(WS-SEED)) + 1` produces values in the range [1, 3), which truncates to 1 or 2 seconds for PIC S9(8) COMP, so the delay is always 1 or 2 seconds -- less than the parent's 3-second timeout in practice. This is a discrepancy between the stated intent in the source comment and the actual implementation.

Data is exchanged exclusively through a named CICS channel (`CIPCREDCHANN`) and container (`CIPE`). There is no direct COMMAREA, no file I/O, and no database access.

## Input / Output

| Direction | Resource       | Type | Description                                                                 |
| --------- | -------------- | ---- | --------------------------------------------------------------------------- |
| IN        | CIPE           | CICS | Container on channel CIPCREDCHANN. Contains customer key, name, address, DOB, existing credit score, review date, and success/fail flags. |
| OUT       | CIPE           | CICS | Same container returned with WS-CONT-IN-CREDIT-SCORE overwritten with newly generated random credit score (1--998 in practice). |
| OUT       | ABNDPROC       | CICS | LINK to abend handler program if a CICS DELAY command fails (error path only). |

## Business Rules

### Credit Score Generation

| #  | Rule                              | Condition                                  | Action                                                                                                     | Source Location   |
| -- | --------------------------------- | ------------------------------------------ | ---------------------------------------------------------------------------------------------------------- | ----------------- |
| 1  | Random delay seeded by task number | Always (unconditional on entry)            | COMPUTE WS-DELAY-AMT = ((3 - 1) * FUNCTION RANDOM(WS-SEED)) + 1, where WS-SEED = EIBTASKN. Truncated to PIC S9(8) COMP, delay is 1 or 2 seconds. | A010, lines 121--124 |
| 2  | CICS DELAY executed for computed seconds | WS-DELAY-AMT is 1 or 2 seconds        | EXEC CICS DELAY FOR SECONDS(WS-DELAY-AMT). Emulates external agency latency.                              | A010, lines 126--130 |
| 3  | Credit score is a random integer 1--998 | Delay completed successfully          | COMPUTE WS-NEW-CREDSCORE = ((999 - 1) * FUNCTION RANDOM) + 1. The seed was already set by the RANDOM call at step 1; no seed is re-used here. Due to RANDOM < 1 and PIC 999 truncation, actual range is 1--998. | A010, lines 216--217 |
| 4  | Credit score is placed into the inbound container record | Always after generation  | MOVE WS-NEW-CREDSCORE TO WS-CONT-IN-CREDIT-SCORE                                                          | A010, line 219    |
| 5  | Updated container record is returned to caller | Always after score generation   | EXEC CICS PUT CONTAINER('CIPE') CHANNEL('CIPCREDCHANN') FROM(WS-CONT-IN). Overwrites the container with the modified record including the new credit score. | A010, lines 227--233 |

### Channel and Container Addressing

| #  | Rule                              | Condition    | Action                                                                 | Source Location |
| -- | --------------------------------- | ------------ | ---------------------------------------------------------------------- | --------------- |
| 6  | Container name is fixed literal   | Always       | WS-CONTAINER-NAME = 'CIPE            ' (16-byte field, space-padded). | A010, line 119  |
| 7  | Channel name is fixed literal     | Always       | WS-CHANNEL-NAME = 'CIPCREDCHANN    ' (16-byte field, space-padded).  | A010, line 120  |
| 8  | Container length is computed at runtime | Before GET and before PUT | COMPUTE WS-CONTAINER-LEN = LENGTH OF WS-CONT-IN. Applied twice: once before the GET and once before the PUT. | A010, lines 190, 225 |

## Calculations

| Calculation         | Formula / Logic                                              | Input Fields          | Output Field       | Source Location       |
| ------------------- | ------------------------------------------------------------ | --------------------- | ------------------ | --------------------- |
| Random delay amount | `((3 - 1) * FUNCTION RANDOM(WS-SEED)) + 1`                  | WS-SEED (= EIBTASKN)  | WS-DELAY-AMT       | A010, lines 123--124  |
| Random credit score | `((999 - 1) * FUNCTION RANDOM) + 1`                          | Implicit RANDOM state (seeded above) | WS-NEW-CREDSCORE   | A010, lines 216--217  |
| Container length    | `LENGTH OF WS-CONT-IN`                                       | WS-CONT-IN (structure) | WS-CONTAINER-LEN   | A010, lines 190, 225  |

Notes on calculations:
- The delay formula `((3-1) * FUNCTION RANDOM(WS-SEED)) + 1` produces values in the range [1, 3). With PIC S9(8) COMP integer truncation the actual values are **1 or 2 seconds**. The source header comment states "between 0 and 3 seconds" and "1 in 4 chance" of returning within the parent's 3-second timeout; however, since the delay is always 1 or 2 seconds, the program will almost always return before the timeout. The source comment does not accurately reflect the implementation.
- The credit score formula produces values in the range [1, 999). FUNCTION RANDOM returns a value >= 0 and < 1, so `((999-1) * RANDOM) + 1` has a mathematical upper bound of 998.999..., which truncates to **998** for PIC 999. The intended range is stated as 1--999 in code comments but the actual maximum achievable value is 998.
- Because WS-SEED is set from EIBTASKN before the first RANDOM call, the random sequence is deterministic per CICS task number, making test results reproducible if the task number is controlled.

## Error Handling

| Condition                                      | Action                                                                                              | Return Code       | Source Location         |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------- | ----------------- | ----------------------- |
| EXEC CICS DELAY returns non-NORMAL response    | 1. INITIALIZE ABNDINFO-REC. 2. Populate ABND-RESPCODE, ABND-RESP2CODE from EIB fields. 3. EXEC CICS ASSIGN APPLID(ABND-APPLID). 4. Populate ABND-TASKNO-KEY from EIBTASKN, ABND-TRANID from EIBTRNID. 5. PERFORM POPULATE-TIME-DATE. 6. Move WS-ORIG-DATE to ABND-DATE. 7. STRING HH:MM:MM (bug: seconds position uses MM twice -- see note) into ABND-TIME. 8. Move WS-U-TIME to ABND-UTIME-KEY. 9. Set ABND-CODE = 'PLOP'. 10. EXEC CICS ASSIGN PROGRAM(ABND-PROGRAM). 11. Set ABND-SQLCODE = 0. 12. STRING 'A010  - *** The delay messed up! ***' + EIBRESP + RESP2 into ABND-FREEFORM. 13. EXEC CICS LINK PROGRAM('ABNDPROC') COMMAREA(ABNDINFO-REC). 14. DISPLAY '*** The delay messed up ! ***'. 15. EXEC CICS ABEND ABCODE('PLOP'). | ABEND code 'PLOP' | A010, lines 132--188    |
| EXEC CICS GET CONTAINER returns non-NORMAL response | DISPLAY 'CRDTAGY5 - UNABLE TO GET CONTAINER. RESP=' + WS-CICS-RESP + ', RESP2=' + WS-CICS-RESP2, plus container/channel/length details. PERFORM GET-ME-OUT-OF-HERE (EXEC CICS RETURN). | None (soft exit)  | A010, lines 200--207    |
| EXEC CICS PUT CONTAINER returns non-NORMAL response | DISPLAY 'CRDTAGY5- UNABLE TO PUT CONTAINER. RESP=' + WS-CICS-RESP + ', RESP2=' + WS-CICS-RESP2, plus container/channel/length details. PERFORM GET-ME-OUT-OF-HERE (EXEC CICS RETURN). | None (soft exit)  | A010, lines 235--242    |

Notes on error handling:
- The DELAY failure path is the only one that invokes ABNDPROC and issues a hard ABEND. Container GET and PUT failures produce only a DISPLAY diagnostic and exit cleanly via CICS RETURN. This asymmetry means a container failure leaves the parent with no updated credit score, which the parent must detect via its own timeout mechanism.
- **Bug at line 158**: The STRING that builds ABND-TIME uses `WS-TIME-NOW-GRP-MM` twice -- once for the minutes position and again where `WS-TIME-NOW-GRP-SS` should appear for seconds. The resulting ABND-TIME field records `HH:MM:MM` rather than `HH:MM:SS`. This means the seconds component of the abend timestamp is always recorded as the minutes value repeated, making the abend log timestamp unreliable for sub-minute analysis.
- The ABND-CODE value `'PLOP'` is hardcoded and has no application-specific meaning; it is a placeholder abend code used solely for the delay failure scenario.

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. **A010** -- Entry point. Sets container/channel names (CIPE, CIPCREDCHANN) and seeds RANDOM from EIBTASKN. Executes random delay calculation and CICS DELAY command.
2. *(Error branch)* If DELAY fails: populate ABNDINFO-REC, EXEC CICS ASSIGN APPLID and PROGRAM, PERFORM POPULATE-TIME-DATE, LINK to ABNDPROC via WS-ABEND-PGM ('ABNDPROC'), then ABEND with code 'PLOP'.
3. **A010 (continued)** -- Computes container length, issues EXEC CICS GET CONTAINER(CIPE) CHANNEL(CIPCREDCHANN) to retrieve customer data into WS-CONT-IN.
4. *(Error branch)* If GET fails: DISPLAY diagnostics, PERFORM GET-ME-OUT-OF-HERE (CICS RETURN, program ends).
5. **A010 (continued)** -- Computes new random credit score (1--998), MOVEs it into WS-CONT-IN-CREDIT-SCORE.
6. **A010 (continued)** -- Recomputes container length, issues EXEC CICS PUT CONTAINER(CIPE) CHANNEL(CIPCREDCHANN) to write updated WS-CONT-IN back.
7. *(Error branch)* If PUT fails: DISPLAY diagnostics, PERFORM GET-ME-OUT-OF-HERE (CICS RETURN, program ends).
8. **A010 (continued)** -- Normal path: PERFORM GET-ME-OUT-OF-HERE (line 244).
9. **GET-ME-OUT-OF-HERE (GMOFH010)** -- Normal and error-soft exit. EXEC CICS RETURN (returns to CICS, control back to async parent).
10. **POPULATE-TIME-DATE (PTD010)** -- Called only on DELAY failure. EXEC CICS ASKTIME ABSTIME(WS-U-TIME), then EXEC CICS FORMATTIME to produce DDMMYYYY date (with DATESEP) and HHMMSS time for ABEND record.
