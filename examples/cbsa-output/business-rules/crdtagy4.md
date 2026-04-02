---
type: business-rules
program: CRDTAGY4
program_type: online
status: draft
confidence: high
last_pass: 3
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

# CRDTAGY4 -- Business Rules

## Program Purpose

CRDTAGY4 is a simulated credit agency program used for credit scoring within the CBSA CICS banking application. It is driven asynchronously by a parent program via the CICS Async API. The program's two responsibilities are:

1. Introduce a random delay to emulate the latency of a real credit bureau response. The program header comment states a 3-second parent timeout and describes a "1 in 4 chance" of the response arriving within that window. See the Delay Duration Accuracy note in Calculations for analysis of the actual formula behaviour.
2. Generate a random credit score in the range 1-999 and return it to the parent program via a CICS channel/container.

Data is exchanged exclusively through the CICS channel `CIPCREDCHANN` and container `CIPD`. No files, DB2 tables, or queues are accessed.

**Note -- source comment inconsistency:** The program header comment (lines 9-20) states the delay is "between 0 and 3 seconds" and gives a "1 in 4 chance" of returning within the 3-second window. The formula `((3-1) * FUNCTION RANDOM(WS-SEED)) + 1` actually produces values in the range [1, 3), which when truncated to PIC S9(8) COMP yields only 1 or 2 seconds -- never 0 or 3. The probability of returning within 3 seconds is therefore 100% based on the formula alone (both 1 and 2 are less than 3), contradicting the stated design intent. This appears to be either a formula defect (intended range was 0-3) or a stale comment.

## Input / Output

| Direction | Resource       | Type | Description                                                                                    |
| --------- | -------------- | ---- | ---------------------------------------------------------------------------------------------- |
| IN        | CIPD           | CICS | Container on channel CIPCREDCHANN. Carries customer identity fields (sort code, account number, name, address, date of birth) plus placeholder credit score (WS-CONT-IN-CREDIT-SCORE PIC 999) and review date fields. Also contains WS-CONT-IN-SUCCESS (PIC X) and WS-CONT-IN-FAIL-CODE (PIC X) which are present in the layout but are neither read nor set by this program -- they pass through unmodified. |
| OUT       | CIPD           | CICS | Same container, returned on channel CIPCREDCHANN with WS-CONT-IN-CREDIT-SCORE populated with the newly generated random credit score (1-999). All other fields including WS-CONT-IN-SUCCESS and WS-CONT-IN-FAIL-CODE are returned as received. |
| OUT       | ABNDPROC       | CICS | LINK to abend handler program if the CICS DELAY command fails; passes ABNDINFO-REC commarea. |

## Business Rules

### Random Delay Generation

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 1 | Seed PRNG from task number | Always on entry | Move EIBTASKN to WS-SEED so each CICS task produces a different random sequence | A010 (line 122) |
| 2 | Calculate delay duration | Always | `WS-DELAY-AMT = ((3 - 1) * FUNCTION RANDOM(WS-SEED)) + 1` -- FUNCTION RANDOM returns a value in [0,1); multiplied by 2 and offset by 1 gives [1, 3). Integer truncation to PIC S9(8) COMP yields 1 or 2 seconds only (3 is never produced because RANDOM never returns exactly 1.0) | A010 (lines 124-125) |
| 3 | Apply delay | Always | Issue `EXEC CICS DELAY FOR SECONDS(WS-DELAY-AMT)` to pause execution by the computed number of seconds | A010 (lines 127-131) |
| 4 | Parent timeout window | Design constraint per source comment | The program header comment states the parent program allows 3 seconds and that there is "a 1 in 4 chance" of data being returned within the window. Based on the actual formula (delay is always 1 or 2 seconds, both less than 3), the response will always arrive within the 3-second window -- contradicting the stated design intent. See Program Purpose note. | Program header comment (lines 18-19) and A010 (lines 124-125) |

### Credit Score Generation

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 5 | Generate credit score | After successful delay and GET container | `WS-NEW-CREDSCORE = ((999 - 1) * FUNCTION RANDOM) + 1` -- FUNCTION RANDOM returns [0,1); result range is [1, 999). Integer truncation to PIC 999 gives values 1-998 for most inputs; 999 is reachable only if RANDOM returns a value that rounds up to 999 before truncation (e.g. 0.998... gives 998.x+1=999.x, truncated to 999). Practical range is 1-999. No seed needed because the PRNG state was seeded earlier in A010. | A010 (lines 217-218) |
| 6 | Write score to container input record | Always | Move WS-NEW-CREDSCORE to WS-CONT-IN-CREDIT-SCORE, overwriting the placeholder value received from the parent | A010 (line 220) |
| 7 | Credit score range | Design constraint | Valid generated scores are 1 to 999 inclusive; the formula ensures a score of 0 is never produced | A010 calculation |

### Container I/O

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 8 | Read input container | After delay succeeds | `EXEC CICS GET CONTAINER('CIPD') CHANNEL('CIPCREDCHANN') INTO(WS-CONT-IN)` to receive customer data from the parent program | A010 (lines 194-200) |
| 9 | Container name literal | Always | WS-CONTAINER-NAME is set to `'CIPD            '` (16 chars, space-padded) and WS-CHANNEL-NAME to `'CIPCREDCHANN    '` (16 chars, space-padded) at the start of A010 | A010 (lines 120-121) |
| 10 | Compute container length before GET | Always | `WS-CONTAINER-LEN = LENGTH OF WS-CONT-IN` -- calculated dynamically to ensure correct buffer sizing | A010 (line 192) |
| 11 | Write output container | After score is populated | `EXEC CICS PUT CONTAINER('CIPD') FROM(WS-CONT-IN) CHANNEL('CIPCREDCHANN')` to return the enriched record (with credit score) to the parent | A010 (lines 227-233) |
| 12 | Compute container length before PUT | Always | `WS-CONTAINER-LEN = LENGTH OF WS-CONT-IN` -- recalculated before the PUT | A010 (line 225) |
| 13 | Success/fail-code fields pass-through | Always | WS-CONT-IN-SUCCESS (PIC X) and WS-CONT-IN-FAIL-CODE (PIC X) are present in the container record layout but CRDTAGY4 neither reads nor sets them; they are returned to the parent unchanged from whatever value the parent placed in the container | WS-CONT-IN layout (lines 59-60); no PROCEDURE DIVISION reference |

## Calculations

| Calculation | Formula / Logic | Input Fields | Output Field | Source Location |
| --- | --- | --- | --- | --- |
| Delay amount | `((3 - 1) * FUNCTION RANDOM(WS-SEED)) + 1` -- FUNCTION RANDOM returns a pseudo-random value in [0,1); `2 * RANDOM + 1` therefore yields [1, 3). Assignment to PIC S9(8) COMP truncates the fractional part, producing only the values 1 or 2. A delay of 3 seconds is never produced. The source header comment's claim of "0 to 3 seconds" and "1 in 4 chance" conflicts with this formula. | WS-SEED (= EIBTASKN) | WS-DELAY-AMT | A010 (lines 124-125) |
| Credit score | `((999 - 1) * FUNCTION RANDOM) + 1` -- uses PRNG state seeded earlier; `998 * RANDOM + 1` yields [1, 999). Assignment to PIC 999 (3-digit unsigned display) truncates the fractional part, producing values 1 to 998 for the bulk of the RANDOM range, and 999 when RANDOM is high enough that the result exceeds 999.0 before truncation (e.g., RANDOM >= 0.999 gives 998*0.999+1 = 998.002 -> 998; RANDOM = 0.9999 gives 998*0.9999+1=998.9002 -> 998; RANDOM ~= 1.0 is never produced). Practical upper bound is 998 unless compiler rounds before truncation. Stated design intent is 1-999. | PRNG state (seeded from EIBTASKN via earlier RANDOM call) | WS-NEW-CREDSCORE | A010 (lines 217-218) |
| Container length (GET) | `LENGTH OF WS-CONT-IN` -- intrinsic function returns the byte length of the WS-CONT-IN record | WS-CONT-IN (record layout) | WS-CONTAINER-LEN | A010 (line 192) |
| Container length (PUT) | `LENGTH OF WS-CONT-IN` -- same calculation repeated before PUT | WS-CONT-IN (record layout) | WS-CONTAINER-LEN | A010 (line 225) |

## Error Handling

| Condition | Action | Return Code | Source Location |
| --- | --- | --- | --- |
| CICS DELAY fails (`WS-CICS-RESP NOT = DFHRESP(NORMAL)`) | Initialize ABNDINFO-REC; populate EIBRESP, EIBRESP2, APPLID, task number, transaction ID, date/time, abend code `'PLOP'`, program name, SQLCODE=0; build freeform message `'A010  - *** The delay messed up! ***'` with RESP/RESP2 values; LINK to ABNDPROC passing ABNDINFO-REC commarea; DISPLAY `'*** The delay messed up ! ***'`; issue `EXEC CICS ABEND ABCODE('PLOP')` | Abend code `PLOP` | A010 (lines 133-189) |
| CICS GET CONTAINER fails (`WS-CICS-RESP NOT = DFHRESP(NORMAL)`) | DISPLAY `'CRDTAGY4 - UNABLE TO GET CONTAINER. RESP='` with RESP/RESP2, container name, channel name, and FLENGTH; PERFORM GET-ME-OUT-OF-HERE (issues EXEC CICS RETURN) | No explicit return code; program returns normally | A010 (lines 202-209) |
| CICS PUT CONTAINER fails (`WS-CICS-RESP NOT = DFHRESP(NORMAL)`) | DISPLAY `'CRDTAGY4- UNABLE TO PUT CONTAINER. RESP='` with RESP/RESP2, container name, channel name, and FLENGTH; PERFORM GET-ME-OUT-OF-HERE (issues EXEC CICS RETURN) | No explicit return code; program returns normally | A010 (lines 235-242) |

### Abend Handler Detail (DELAY failure path)

The abend information record (ABNDINFO-REC, from copybook ABNDINFO) is populated as follows before linking to ABNDPROC:

| Field | Source |
| --- | --- |
| ABND-RESPCODE | EIBRESP |
| ABND-RESP2CODE | EIBRESP2 |
| ABND-APPLID | EXEC CICS ASSIGN APPLID |
| ABND-TASKNO-KEY | EIBTASKN |
| ABND-TRANID | EIBTRNID |
| ABND-DATE | WS-ORIG-DATE (DD/MM/YYYY from FORMATTIME) |
| ABND-TIME | Formatted HH:MM:MM string -- **defect**: the STRING statement at line 159 uses WS-TIME-NOW-GRP-MM for the seconds component instead of WS-TIME-NOW-GRP-SS, so the time string is formatted as HH:MM:MM (minutes repeated) rather than HH:MM:SS |
| ABND-UTIME-KEY | WS-U-TIME (ASKTIME absolute time) |
| ABND-CODE | Literal `'PLOP'` |
| ABND-PROGRAM | EXEC CICS ASSIGN PROGRAM |
| ABND-SQLCODE | 0 (zeros) |
| ABND-FREEFORM | `'A010  - *** The delay messed up! *** EIBRESP=<resp> RESP2=<resp2>'` |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. A010 -- entry point; sets container/channel names and PRNG seed from EIBTASKN
2. COMPUTE WS-DELAY-AMT -- calculates random delay (1 or 2 seconds based on formula)
3. EXEC CICS DELAY -- suspends the task for WS-DELAY-AMT seconds
4. IF CICS DELAY fails -- PERFORM POPULATE-TIME-DATE, then LINK ABNDPROC, then EXEC CICS ABEND ABCODE('PLOP')
5. EXEC CICS GET CONTAINER -- reads customer data from CIPD/CIPCREDCHANN into WS-CONT-IN
6. IF GET CONTAINER fails -- PERFORM GET-ME-OUT-OF-HERE (EXEC CICS RETURN)
7. COMPUTE WS-NEW-CREDSCORE -- generates random credit score (1-999)
8. MOVE WS-NEW-CREDSCORE TO WS-CONT-IN-CREDIT-SCORE -- writes score into container record
9. EXEC CICS PUT CONTAINER -- returns enriched WS-CONT-IN to CIPD/CIPCREDCHANN
10. IF PUT CONTAINER fails -- PERFORM GET-ME-OUT-OF-HERE (EXEC CICS RETURN)
11. PERFORM GET-ME-OUT-OF-HERE -- normal exit via EXEC CICS RETURN

### Paragraphs

| Paragraph | Section | Purpose |
| --- | --- | --- |
| A010 | PREMIERE | Main logic: delay, GET container, generate score, PUT container |
| A999 | PREMIERE | Exit stub |
| GMOFH010 | GET-ME-OUT-OF-HERE | Issues EXEC CICS RETURN |
| GMOFH999 | GET-ME-OUT-OF-HERE | Exit stub |
| PTD010 | POPULATE-TIME-DATE | EXEC CICS ASKTIME + FORMATTIME to populate WS-U-TIME, WS-ORIG-DATE, WS-TIME-NOW |
| PTD999 | POPULATE-TIME-DATE | Exit stub |
