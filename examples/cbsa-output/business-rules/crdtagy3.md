---
type: business-rules
program: CRDTAGY3
program_type: online
status: draft
confidence: high
last_pass: 4
calls: []
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

# CRDTAGY3 -- Business Rules

## Program Purpose

CRDTAGY3 is a simulated (dummy) credit-scoring agency program invoked asynchronously
via the CICS Async API. It receives customer data from its parent program through a
CICS channel/container pair (channel `CIPCREDCHANN`, container `CIPC`), introduces a
random delay of 1-3 seconds to emulate a real external agency response, then generates
a random credit score in the range 1-999 and writes the result back into the same
container before returning.

The program is one of five identical credit-agency stubs (CRDTAGY1-5). CRECUST launches
all five in parallel via `EXEC CICS RUN TRANSID` using transaction IDs OCR1-OCR5. Each
stub uses a different container within the same channel (CIPA-CIPE respectively);
CRDTAGY3 is iteration 3 and uses container CIPC. CRECUST then delays 3 seconds and
FETCHes whichever children have completed within that window.

The program comment block states "between 0 and 3 seconds" and "1 in 4 chance" of
returning within the parent's 3-second timeout. However, the actual COMPUTE formula
`((3-1) * FUNCTION RANDOM(WS-SEED)) + 1` adds 1 to the result, so the practical range
is 1-3 seconds (RANDOM returns 0.0 to <1.0). The "1 in 4" comment appears to be an
authoring error relative to the code; the formula produces 1 in 3 odds that the delay
will be exactly 1 second. Neither the comment nor the formula produce a 0-second delay.

## Input / Output

| Direction | Resource        | Type | Description                                                           |
| --------- | --------------- | ---- | --------------------------------------------------------------------- |
| IN        | CIPCREDCHANN    | CICS | Channel carrying the inbound customer data container                  |
| IN        | CIPC            | CICS | Container within CIPCREDCHANN; holds WS-CONT-IN customer record       |
| OUT       | CIPC            | CICS | Same container, updated with the generated credit score               |
| OUT       | ABNDPROC        | CICS | Abend-handler program linked to on DELAY failure (error path only)    |

## Business Rules

### Delay / Timing

| #  | Rule                              | Condition                                     | Action                                                                                       | Source Location |
| -- | --------------------------------- | --------------------------------------------- | -------------------------------------------------------------------------------------------- | --------------- |
| 1  | Random delay seed from task number | Always                                        | EIBTASKN is moved to WS-SEED before the first RANDOM call, ensuring task-unique randomness  | A010 line 121   |
| 2  | Delay duration is 1-3 seconds     | Always on entry                               | `WS-DELAY-AMT = ((3 - 1) * RANDOM(WS-SEED)) + 1` yields values in the inclusive range 1-3  | A010 lines 123-124 |
| 3  | CICS DELAY issued before any work | Always                                        | `EXEC CICS DELAY FOR SECONDS(WS-DELAY-AMT)` is the first external call                      | A010 lines 126-130 |

### Credit Score Generation

| #  | Rule                              | Condition                                     | Action                                                                                       | Source Location |
| -- | --------------------------------- | --------------------------------------------- | -------------------------------------------------------------------------------------------- | --------------- |
| 4  | Credit score range is 1-999       | Always, after successful DELAY and GET        | `WS-NEW-CREDSCORE = ((999 - 1) * FUNCTION RANDOM) + 1` -- no seed reused (seed applied on first call) | A010 lines 213-214 |
| 5  | Score written into container data | Always, after score generation                | `MOVE WS-NEW-CREDSCORE TO WS-CONT-IN-CREDIT-SCORE` overwrites whatever score was in the inbound container | A010 line 217 |
| 6  | WS-CONT-IN-SUCCESS and WS-CONT-IN-FAIL-CODE not set | Always | These fields exist in the inbound container record layout but CRDTAGY3 never sets them; they are returned to the parent with whatever values they had when PUT from the parent | A010 (no assignment statement) |

### Container Protocol

| #  | Rule                                         | Condition   | Action                                                                                          | Source Location    |
| -- | -------------------------------------------- | ----------- | ----------------------------------------------------------------------------------------------- | ------------------ |
| 7  | Container name is fixed value `CIPC`         | Always      | Literal `'CIPC            '` moved to WS-CONTAINER-NAME at program entry                       | A010 line 119      |
| 8  | Channel name is fixed value `CIPCREDCHANN`   | Always      | Literal `'CIPCREDCHANN    '` moved to WS-CHANNEL-NAME at program entry                         | A010 line 120      |
| 9  | Container length computed from record length | Before GET and before PUT | `COMPUTE WS-CONTAINER-LEN = LENGTH OF WS-CONT-IN` -- computed twice (before GET and before PUT) | A010 lines 189, 222 |
| 10 | GET must succeed before score is generated   | Sequentially enforced | If CICS GET fails, PERFORM GET-ME-OUT-OF-HERE terminates the program; no score is generated    | A010 lines 199-206  |
| 11 | PUT must succeed before normal return        | Sequentially enforced | If CICS PUT fails, PERFORM GET-ME-OUT-OF-HERE terminates; score is not considered delivered    | A010 lines 232-239  |

### Parent / Child Async Protocol

| #  | Rule                                              | Condition | Action                                                                                                  | Source Location (CRECUST) |
| -- | ------------------------------------------------- | --------- | ------------------------------------------------------------------------------------------------------- | ------------------------- |
| 12 | CRDTAGY3 is agency stub 3 of 5                    | Always    | CRECUST iterates WS-CC-CNT 1-5, builds TRANSID as `'OCR' + WS-CC-CNT`; when WS-CC-CNT=3, TRANSID=OCR3 | CRECUST CREDIT-CHECK CC010 line 585-587 |
| 13 | Container CIPC assigned to iteration 3            | Always    | CRECUST EVALUATE WS-CC-CNT WHEN 3 assigns WS-PUT-CONT-NAME = `'CIPC            '`                       | CRECUST CREDIT-CHECK CC010 line 596 |
| 14 | Parent waits 3 seconds then FETCHes               | Always    | CRECUST issues `EXEC CICS DELAY FOR SECONDS(3)` after launching all 5 children; only completed children contribute credit scores | CRECUST CREDIT-CHECK line 681-683 |

## Calculations

| Calculation             | Formula / Logic                                     | Input Fields       | Output Field        | Source Location     |
| ----------------------- | --------------------------------------------------- | ------------------ | ------------------- | ------------------- |
| Random delay (seconds)  | `((3 - 1) * FUNCTION RANDOM(WS-SEED)) + 1`         | WS-SEED (EIBTASKN) | WS-DELAY-AMT        | A010 lines 123-124  |
| Random credit score     | `((999 - 1) * FUNCTION RANDOM) + 1`                | None (seeded by earlier call) | WS-NEW-CREDSCORE | A010 lines 213-214 |
| Container length        | `LENGTH OF WS-CONT-IN` (intrinsic function)         | WS-CONT-IN record  | WS-CONTAINER-LEN    | A010 lines 189, 222 |

Notes:
- WS-DELAY-AMT is PIC S9(8) COMP; the RANDOM formula yields 1.0-3.0 which truncates to integer 1, 2, or 3.
- WS-NEW-CREDSCORE is PIC 999 (3-digit unsigned display); the formula yields 1-999.
- Because RANDOM was already seeded with WS-SEED on the first call, the second call to FUNCTION RANDOM (without seed) continues the same pseudo-random sequence -- guaranteeing the credit score is correlated with the delay, not independently seeded.
- The program header comment states the delay range is "0 to 3 seconds" with "1 in 4" odds of returning in time. The actual formula always adds 1, producing a minimum of 1 second and "1 in 3" odds. The comment is inconsistent with the code.

## Error Handling

| Condition                         | Action                                                                                                                                     | Return Code / ABEND | Source Location     |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------- | ------------------- |
| CICS DELAY returns non-NORMAL     | Populate ABNDINFO-REC with EIBRESP, EIBRESP2, APPLID, task number, transaction ID, date/time, ABND-CODE='PLOP'; LINK to ABNDPROC; ABEND with code 'PLOP' | ABCODE('PLOP')  | A010 lines 132-187  |
| CICS GET CONTAINER returns non-NORMAL | DISPLAY error message showing container name, channel name, RESP, RESP2; PERFORM GET-ME-OUT-OF-HERE (CICS RETURN)                      | None (soft return)  | A010 lines 199-206  |
| CICS PUT CONTAINER returns non-NORMAL | DISPLAY error message showing container name, channel name, RESP, RESP2; PERFORM GET-ME-OUT-OF-HERE (CICS RETURN)                      | None (soft return)  | A010 lines 232-239  |

### DELAY failure error message (exact text)
`'A010  - *** The delay messed up! ***'` concatenated with `' EIBRESP='`, `ABND-RESPCODE`, `' RESP2='`, `ABND-RESP2CODE` -- written to ABND-FREEFORM.

Also: `DISPLAY '*** The delay messed up ! ***'` to console before ABEND.

**Bug in ABEND time string (line 158):** The STRING statement that builds ABND-TIME uses
`WS-TIME-NOW-GRP-MM` for both the minutes and the seconds slot. The seconds component
`WS-TIME-NOW-GRP-SS` is never referenced. As a result the time recorded in the abend
record is formatted HH:MM:MM rather than HH:MM:SS.

### GET failure display message (exact text)
`'CRDTAGY3- UNABLE TO GET CONTAINER. RESP='` followed by WS-CICS-RESP, `', RESP2='`, WS-CICS-RESP2, then second line: `'CONTAINER='`, WS-CONTAINER-NAME, `' CHANNEL='`, WS-CHANNEL-NAME, `' FLENGTH='`, WS-CONTAINER-LEN.

### PUT failure display message (exact text)
`'CRDTAGY3- UNABLE TO PUT CONTAINER. RESP='` followed by WS-CICS-RESP, `', RESP2='`, WS-CICS-RESP2, then second line: `'CONTAINER='`, WS-CONTAINER-NAME, `' CHANNEL='`, WS-CHANNEL-NAME, `' FLENGTH='`, WS-CONTAINER-LEN.

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. A010 (PREMIERE SECTION) -- entry point; sets container/channel names, seeds random, computes delay
2. EXEC CICS DELAY -- pauses 1-3 seconds to simulate external agency latency
3. IF DELAY fails: PERFORM POPULATE-TIME-DATE -- retrieves current date/time for abend record
4. IF DELAY fails: EXEC CICS LINK PROGRAM('ABNDPROC') -- delegates abend handling, then EXEC CICS ABEND ABCODE('PLOP')
5. EXEC CICS GET CONTAINER(CIPC) CHANNEL(CIPCREDCHANN) -- retrieves inbound customer record into WS-CONT-IN
6. IF GET fails: PERFORM GET-ME-OUT-OF-HERE -- EXEC CICS RETURN (soft exit)
7. COMPUTE WS-NEW-CREDSCORE -- generates random credit score 1-999
8. MOVE WS-NEW-CREDSCORE TO WS-CONT-IN-CREDIT-SCORE -- updates the record
9. EXEC CICS PUT CONTAINER(CIPC) CHANNEL(CIPCREDCHANN) -- writes updated record back
10. IF PUT fails: PERFORM GET-ME-OUT-OF-HERE -- EXEC CICS RETURN (soft exit)
11. PERFORM GET-ME-OUT-OF-HERE -- normal EXEC CICS RETURN

## Frontmatter Discrepancies (Iteration 4 Findings)

The following frontmatter values appear incorrect based on source analysis. They were not modified per instructions but are flagged here for resolution:

- **transactions**: should be `[OCR3]`. The CSD file (`BANK.csd` line 285-293) defines `DEFINE TRANSACTION(OCR3) GROUP(BANK) PROGRAM(CRDTAGY3)`. The field is currently empty.
- **called_by**: should include `CRECUST`. CRECUST's CREDIT-CHECK section (lines 579-674) iterates OCR1-OCR5 via `EXEC CICS RUN TRANSID`, building the TRANSID dynamically as `'OCR' + WS-CC-CNT`. When WS-CC-CNT=3, TRANSID='OCR3' which starts CRDTAGY3. The field is currently empty.
