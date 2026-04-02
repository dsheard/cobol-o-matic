---
type: business-rules
program: CRDTAGY2
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

# CRDTAGY2 -- Business Rules

## Program Purpose

CRDTAGY2 is a simulated credit agency program used for credit scoring within the CICS Banking Sample Application (CBSA). It is driven asynchronously via the CICS Async API (EXEC CICS LINK or RUN TRANSID). Its sole business function is to:

1. Introduce a random delay of 1 to just-under-3 seconds (simulating a real external credit agency response time).
2. Generate a random credit score between 1 and 999.
3. Return the credit score to the calling program via a CICS channel/container.

The parent program enforces a 3-second overall timeout. The program header comment states "there is a 1 in 4 chance that data will be returned within the overall 3 second delay" -- deliberately simulating the unreliability of external credit agencies.

Input data (customer key, name, address, date of birth) is received in container `CIPB` on channel `CIPCREDCHANN`. The computed credit score is written back into the same container before returning.

## Input / Output

| Direction | Resource        | Type | Description                                                                 |
| --------- | --------------- | ---- | --------------------------------------------------------------------------- |
| IN        | CIPB            | CICS | Container on channel CIPCREDCHANN -- customer data including sort code, account number, name, address, date of birth |
| OUT       | CIPB            | CICS | Same container, updated with the generated credit score (WS-CONT-IN-CREDIT-SCORE) |
| OUT       | ABNDPROC (LINK) | CICS | Abend handler program -- called via WS-ABEND-PGM on DELAY failure before issuing ABEND |

## Business Rules

### Credit Score Generation

| #  | Rule                          | Condition                                                                 | Action                                                                                                                     | Source Location |
| -- | ----------------------------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 1  | Seed random number generator  | Always, at program entry                                                  | Move EIBTASKN (current task number) to WS-SEED; use as seed for FUNCTION RANDOM to ensure different sequences per task    | A010 (line 121) |
| 2  | Generate random delay amount  | Always, using seeded RANDOM                                               | COMPUTE WS-DELAY-AMT = ((3 - 1) * FUNCTION RANDOM(WS-SEED)) + 1; result truncated to integer, effective range is 1 to just under 3 seconds | A010 (lines 123-124) |
| 3  | Apply simulated agency delay  | Always                                                                    | EXEC CICS DELAY FOR SECONDS(WS-DELAY-AMT); emulates external credit agency latency; program comment says ~1-in-4 chance of completing within the parent's 3-second window | A010 (lines 126-130) |
| 4  | Generate random credit score  | After successful container GET; uses same RANDOM sequence (no new seed)   | COMPUTE WS-NEW-CREDSCORE = ((999 - 1) * FUNCTION RANDOM) + 1; result is in range 1-999                                  | A010 (lines 215-216) |
| 5  | Write credit score to container | Always after score generation                                            | MOVE WS-NEW-CREDSCORE TO WS-CONT-IN-CREDIT-SCORE; then PUT the updated WS-CONT-IN back to container CIPB                | A010 (lines 218, 225-231) |

### Container I/O

| #  | Rule                          | Condition                                                   | Action                                                                                                                   | Source Location      |
| -- | ----------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | -------------------- |
| 6  | Read input container          | Always                                                      | EXEC CICS GET CONTAINER(WS-CONTAINER-NAME) CHANNEL(WS-CHANNEL-NAME) INTO(WS-CONT-IN) FLENGTH(WS-CONTAINER-LEN); WS-CONTAINER-NAME='CIPB', WS-CHANNEL-NAME='CIPCREDCHANN' | A010 (lines 193-199) |
| 7  | Container GET failure         | WS-CICS-RESP NOT = DFHRESP(NORMAL) after GET CONTAINER      | DISPLAY error message with RESP/RESP2/container/channel/length; PERFORM GET-ME-OUT-OF-HERE (EXEC CICS RETURN)           | A010 (lines 201-208) |
| 8  | Write output container        | After credit score is generated                             | EXEC CICS PUT CONTAINER(WS-CONTAINER-NAME) FROM(WS-CONT-IN) FLENGTH(WS-CONTAINER-LEN) CHANNEL(WS-CHANNEL-NAME)         | A010 (lines 225-231) |
| 9  | Container PUT failure         | WS-CICS-RESP NOT = DFHRESP(NORMAL) after PUT CONTAINER      | DISPLAY error message with RESP/RESP2/container/channel/length; PERFORM GET-ME-OUT-OF-HERE (EXEC CICS RETURN)           | A010 (lines 233-240) |

## Calculations

| Calculation         | Formula / Logic                                              | Input Fields                   | Output Field       | Source Location      |
| ------------------- | ------------------------------------------------------------ | ------------------------------ | ------------------ | -------------------- |
| Random delay amount | WS-DELAY-AMT = ((3 - 1) * FUNCTION RANDOM(WS-SEED)) + 1    | WS-SEED (from EIBTASKN)        | WS-DELAY-AMT       | A010 (lines 123-124) |
| Credit score        | WS-NEW-CREDSCORE = ((999 - 1) * FUNCTION RANDOM) + 1       | RANDOM (continued sequence)    | WS-NEW-CREDSCORE   | A010 (lines 215-216) |
| Container length    | WS-CONTAINER-LEN = LENGTH OF WS-CONT-IN                     | WS-CONT-IN (layout)            | WS-CONTAINER-LEN   | A010 (lines 191, 223) |

Notes on calculations:
- Both RANDOM calls share the same sequence: the first call uses FUNCTION RANDOM(WS-SEED) which seeds the generator; the second call uses FUNCTION RANDOM (no seed) to continue the same sequence. This ensures the delay and score are correlated per task.
- Delay range: WS-DELAY-AMT is PIC S9(8) COMP so the fractional result is truncated. The minimum value is 1 second. The source header comment says "0 to 3 seconds" but the formula ((3-1)*R)+1 produces a minimum of 1.
- Credit score range: 1 to 999 (3-digit PIC 999 field, stored in WS-CONT-IN-CREDIT-SCORE).

## Error Handling

| Condition                                  | Action                                                                                                                                                                                                                           | Return Code      | Source Location      |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- | -------------------- |
| EXEC CICS DELAY not DFHRESP(NORMAL)        | INITIALIZE ABNDINFO-REC; populate ABND-RESPCODE, ABND-RESP2CODE, ABND-APPLID (via ASSIGN), ABND-TASKNO-KEY, ABND-TRANID, ABND-DATE, ABND-TIME, ABND-UTIME-KEY; set ABND-CODE = 'PLOP'; set ABND-SQLCODE = ZEROS; STRING freeform message 'A010  - *** The delay messed up! ***' with RESP/RESP2 into ABND-FREEFORM; EXEC CICS LINK PROGRAM(WS-ABEND-PGM) COMMAREA(ABNDINFO-REC); DISPLAY '*** The delay messed up ! ***'; EXEC CICS ABEND ABCODE('PLOP') | ABCODE='PLOP'    | A010 (lines 132-188) |
| EXEC CICS GET CONTAINER not DFHRESP(NORMAL) | DISPLAY 'CRDTAGY2 - UNABLE TO GET CONTAINER. RESP=' with RESP/RESP2/container/channel/length details; PERFORM GET-ME-OUT-OF-HERE                                                                                                | None (RETURN)    | A010 (lines 201-208) |
| EXEC CICS PUT CONTAINER not DFHRESP(NORMAL) | DISPLAY 'CRDTAGY2 - UNABLE TO PUT CONTAINER. RESP=' with RESP/RESP2/container/channel/length details; PERFORM GET-ME-OUT-OF-HERE                                                                                                | None (RETURN)    | A010 (lines 233-240) |

Notes on error handling:
- The DELAY failure path is the only one that invokes the formal ABEND handler (ABNDPROC via LINK using WS-ABEND-PGM variable, VALUE 'ABNDPROC') and issues a hard ABEND with code 'PLOP'. This is more severe than container failures.
- Container GET/PUT failures perform a soft return (EXEC CICS RETURN) without an ABEND. The parent program relying on the async response will not receive the credit score container and must handle the timeout itself.
- ABND-SQLCODE is set to ZEROS (no SQL in this program; the field is part of the generic ABNDINFO copybook).
- There is a bug in the abend time string (lines 154-159): WS-TIME-NOW-GRP-MM is used at both the minutes position (line 156) and the seconds position (line 158), instead of WS-TIME-NOW-GRP-SS for seconds. The ABND-TIME field will record HH:MM:MM rather than HH:MM:SS.

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. A010 -- Program entry point (PREMIERE SECTION); all main logic executes here sequentially
2. MOVE 'CIPB' TO WS-CONTAINER-NAME; MOVE 'CIPCREDCHANN' TO WS-CHANNEL-NAME -- set channel/container literals into working storage variables
3. MOVE EIBTASKN TO WS-SEED -- seed random number generator with CICS task number
4. COMPUTE WS-DELAY-AMT -- calculate random delay of 1 to just-under-3 seconds
5. EXEC CICS DELAY FOR SECONDS(WS-DELAY-AMT) -- introduce simulated agency latency
6. IF DELAY fails -- PERFORM POPULATE-TIME-DATE, populate ABNDINFO-REC, EXEC CICS ASSIGN PROGRAM(ABND-PROGRAM), EXEC CICS LINK PROGRAM(WS-ABEND-PGM), then ABEND 'PLOP'
7. COMPUTE WS-CONTAINER-LEN = LENGTH OF WS-CONT-IN -- calculate container size
8. EXEC CICS GET CONTAINER(WS-CONTAINER-NAME) -- retrieve customer data input
9. IF GET fails -- PERFORM GET-ME-OUT-OF-HERE (RETURN)
10. COMPUTE WS-NEW-CREDSCORE -- generate random credit score 1-999
11. MOVE WS-NEW-CREDSCORE TO WS-CONT-IN-CREDIT-SCORE -- update container data
12. COMPUTE WS-CONTAINER-LEN = LENGTH OF WS-CONT-IN -- recalculate container size before PUT
13. EXEC CICS PUT CONTAINER(WS-CONTAINER-NAME) -- write updated container with credit score
14. IF PUT fails -- PERFORM GET-ME-OUT-OF-HERE (RETURN)
15. PERFORM GET-ME-OUT-OF-HERE -- normal return path
16. GET-ME-OUT-OF-HERE SECTION -- EXEC CICS RETURN
17. POPULATE-TIME-DATE SECTION -- EXEC CICS ASKTIME / FORMATTIME (called only from DELAY error path)
