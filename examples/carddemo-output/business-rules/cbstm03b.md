---
type: business-rules
program: CBSTM03B
program_type: subprogram
status: draft
confidence: high
last_pass: 3
calls: []
called_by:
- CBSTM03A
uses_copybooks: []
reads:
- ACCT-FILE
- CUST-FILE
- TRNX-FILE
- XREF-FILE
writes: []
db_tables: []
transactions: []
mq_queues: []
---

# CBSTM03B -- Business Rules

## Program Purpose

CBSTM03B is a batch COBOL subroutine called by CBSTM03A to perform all file I/O
for the Transaction Report. It is a generic file-handler: the caller passes an
operation code and a DD name through the LINKAGE SECTION, and CBSTM03B opens,
reads, or closes whichever file is named. The result of every operation (the
two-byte file status) is always returned to the caller in the shared linkage
area. No business calculations are performed here; the program exists solely to
isolate file access from report-building logic.

## Input / Output

| Direction | Resource  | Type | Description                                                   |
| --------- | --------- | ---- | ------------------------------------------------------------- |
| IN/OUT    | TRNX-FILE | File | Indexed VSAM, sequential access. Key FD-TRNXS-ID (card 16 bytes + transaction ID 16 bytes = 32 bytes). Data PIC X(318). Full record 350 bytes. DD name 'TRNXFILE'. |
| IN/OUT    | XREF-FILE | File | Indexed VSAM, sequential access. Key FD-XREF-CARD-NUM PIC X(16). Data PIC X(34). Full record 50 bytes. DD name 'XREFFILE'. |
| IN/OUT    | CUST-FILE | File | Indexed VSAM, random access. Key FD-CUST-ID PIC X(9). Data PIC X(491). Full record 500 bytes. DD name 'CUSTFILE'. |
| IN/OUT    | ACCT-FILE | File | Indexed VSAM, random access. Key FD-ACCT-ID PIC 9(11). Data PIC X(289). Full record 300 bytes. DD name 'ACCTFILE'. |
| IN        | LK-M03B-DD   | Linkage | 8-byte DD name identifying which file to operate on ('TRNXFILE', 'XREFFILE', 'CUSTFILE', 'ACCTFILE'). |
| IN        | LK-M03B-OPER | Linkage | 1-byte operation code: O=Open, C=Close, R=Sequential Read, K=Keyed Read, W=Write (not implemented), Z=Rewrite (not implemented). |
| IN        | LK-M03B-KEY  | Linkage | 25-byte key value used for keyed reads (CUST-FILE and ACCT-FILE only). |
| IN        | LK-M03B-KEY-LN | Linkage | Signed 4-digit integer (PIC S9(4)): number of bytes from LK-M03B-KEY to move into the file record key before a keyed read. |
| OUT       | LK-M03B-FLDT | Linkage | 1000-byte field that receives the record data returned by a READ operation. |
| OUT       | LK-M03B-RC   | Linkage | 2-byte file status returned to the caller after every file operation. |

## Business Rules

### File Dispatch

| #  | Rule                              | Condition                            | Action                                                     | Source Location      |
| -- | --------------------------------- | ------------------------------------ | ---------------------------------------------------------- | -------------------- |
| 1  | Route to TRNXFILE handler         | LK-M03B-DD = 'TRNXFILE'             | PERFORM 1000-TRNXFILE-PROC THRU 1999-EXIT                  | 0000-START line 119  |
| 2  | Route to XREFFILE handler         | LK-M03B-DD = 'XREFFILE'             | PERFORM 2000-XREFFILE-PROC THRU 2999-EXIT                  | 0000-START line 121  |
| 3  | Route to CUSTFILE handler         | LK-M03B-DD = 'CUSTFILE'             | PERFORM 3000-CUSTFILE-PROC THRU 3999-EXIT                  | 0000-START line 123  |
| 4  | Route to ACCTFILE handler         | LK-M03B-DD = 'ACCTFILE'             | PERFORM 4000-ACCTFILE-PROC THRU 4999-EXIT                  | 0000-START line 125  |
| 5  | Unknown DD name -- immediate exit | LK-M03B-DD not one of the four above | GO TO 9999-GOBACK; LK-M03B-RC is NOT updated (caller's prior value retained) | 0000-START line 127 |

The dispatch is implemented as an EVALUATE on LK-M03B-DD with WHEN OTHER for the unknown case.

### TRNX-FILE Operations (1000-TRNXFILE-PROC)

| #  | Rule                              | Condition                    | Action                                                     | Source Location           |
| -- | --------------------------------- | ---------------------------- | ---------------------------------------------------------- | ------------------------- |
| 6  | Open TRNX-FILE for input          | LK-M03B-OPER = 'O' (M03B-OPEN)  | OPEN INPUT TRNX-FILE; GO TO 1900-EXIT to capture status   | 1000-TRNXFILE-PROC line 135 |
| 7  | Sequential read from TRNX-FILE    | LK-M03B-OPER = 'R' (M03B-READ)  | READ TRNX-FILE INTO LK-M03B-FLDT; GO TO 1900-EXIT        | 1000-TRNXFILE-PROC line 140 |
| 8  | Close TRNX-FILE                   | LK-M03B-OPER = 'C' (M03B-CLOSE) | CLOSE TRNX-FILE; GO TO 1900-EXIT to capture status        | 1000-TRNXFILE-PROC line 146 |
| 9  | Return TRNX-FILE status to caller | Always, after any TRNX-FILE op   | MOVE TRNXFILE-STATUS TO LK-M03B-RC                        | 1900-EXIT line 152        |

### XREF-FILE Operations (2000-XREFFILE-PROC)

| #  | Rule                              | Condition                    | Action                                                     | Source Location           |
| -- | --------------------------------- | ---------------------------- | ---------------------------------------------------------- | ------------------------- |
| 10 | Open XREF-FILE for input          | LK-M03B-OPER = 'O' (M03B-OPEN)  | OPEN INPUT XREF-FILE; GO TO 2900-EXIT to capture status   | 2000-XREFFILE-PROC line 159 |
| 11 | Sequential read from XREF-FILE    | LK-M03B-OPER = 'R' (M03B-READ)  | READ XREF-FILE INTO LK-M03B-FLDT; GO TO 2900-EXIT        | 2000-XREFFILE-PROC line 164 |
| 12 | Close XREF-FILE                   | LK-M03B-OPER = 'C' (M03B-CLOSE) | CLOSE XREF-FILE; GO TO 2900-EXIT to capture status        | 2000-XREFFILE-PROC line 170 |
| 13 | Return XREF-FILE status to caller | Always, after any XREF-FILE op   | MOVE XREFFILE-STATUS TO LK-M03B-RC                        | 2900-EXIT line 176        |

### CUST-FILE Operations (3000-CUSTFILE-PROC)

| #  | Rule                              | Condition                       | Action                                                                                     | Source Location           |
| -- | --------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------ | ------------------------- |
| 14 | Open CUST-FILE for input          | LK-M03B-OPER = 'O' (M03B-OPEN)    | OPEN INPUT CUST-FILE; GO TO 3900-EXIT to capture status                                   | 3000-CUSTFILE-PROC line 183 |
| 15 | Keyed read from CUST-FILE         | LK-M03B-OPER = 'K' (M03B-READ-K)  | Move LK-M03B-KEY(1:LK-M03B-KEY-LN) to FD-CUST-ID, then READ CUST-FILE INTO LK-M03B-FLDT | 3000-CUSTFILE-PROC line 188 |
| 16 | Key length controls read key      | Always on keyed read             | Only the first LK-M03B-KEY-LN bytes of LK-M03B-KEY are placed into FD-CUST-ID (9 bytes). Caller must supply correct length. | 3000-CUSTFILE-PROC line 189 |
| 17 | Close CUST-FILE                   | LK-M03B-OPER = 'C' (M03B-CLOSE)   | CLOSE CUST-FILE; GO TO 3900-EXIT to capture status                                        | 3000-CUSTFILE-PROC line 195 |
| 18 | Return CUST-FILE status to caller | Always, after any CUST-FILE op     | MOVE CUSTFILE-STATUS TO LK-M03B-RC                                                        | 3900-EXIT line 201        |

### ACCT-FILE Operations (4000-ACCTFILE-PROC)

| #  | Rule                              | Condition                       | Action                                                                                     | Source Location           |
| -- | --------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------ | ------------------------- |
| 19 | Open ACCT-FILE for input          | LK-M03B-OPER = 'O' (M03B-OPEN)    | OPEN INPUT ACCT-FILE; GO TO 4900-EXIT to capture status                                   | 4000-ACCTFILE-PROC line 208 |
| 20 | Keyed read from ACCT-FILE         | LK-M03B-OPER = 'K' (M03B-READ-K)  | Move LK-M03B-KEY(1:LK-M03B-KEY-LN) to FD-ACCT-ID, then READ ACCT-FILE INTO LK-M03B-FLDT | 4000-ACCTFILE-PROC line 213 |
| 21 | Key length controls read key      | Always on keyed read             | Only the first LK-M03B-KEY-LN bytes of LK-M03B-KEY are placed into FD-ACCT-ID (11 bytes numeric). Caller must supply correct length. | 4000-ACCTFILE-PROC line 214 |
| 22 | Close ACCT-FILE                   | LK-M03B-OPER = 'C' (M03B-CLOSE)   | CLOSE ACCT-FILE; GO TO 4900-EXIT to capture status                                        | 4000-ACCTFILE-PROC line 220 |
| 23 | Return ACCT-FILE status to caller | Always, after any ACCT-FILE op     | MOVE ACCTFILE-STATUS TO LK-M03B-RC                                                        | 4900-EXIT line 226        |

### Unimplemented Operations

| #  | Rule                                    | Condition                                                   | Action                                          | Source Location |
| -- | --------------------------------------- | ----------------------------------------------------------- | ----------------------------------------------- | --------------- |
| 24 | Write operation code defined but unused | LK-M03B-OPER = 'W' (M03B-WRITE 88-level)                   | No matching IF branch; falls through all three IF tests to the EXIT paragraph; no file I/O performed; prior file status IS returned to caller via LK-M03B-RC | All proc sections |
| 25 | Rewrite operation code defined but unused | LK-M03B-OPER = 'Z' (M03B-REWRITE 88-level)               | No matching IF branch; falls through all three IF tests to the EXIT paragraph; no file I/O performed; prior file status IS returned to caller via LK-M03B-RC | All proc sections |

## Calculations

| Calculation       | Formula / Logic                                             | Input Fields                          | Output Field  | Source Location           |
| ----------------- | ----------------------------------------------------------- | ------------------------------------- | ------------- | ------------------------- |
| Partial key move for CUST-FILE  | Reference modification: LK-M03B-KEY(1:LK-M03B-KEY-LN)     | LK-M03B-KEY (PIC X(25)), LK-M03B-KEY-LN (PIC S9(4)) | FD-CUST-ID (PIC X(9))    | 3000-CUSTFILE-PROC line 189 |
| Partial key move for ACCT-FILE  | Reference modification: LK-M03B-KEY(1:LK-M03B-KEY-LN)     | LK-M03B-KEY (PIC X(25)), LK-M03B-KEY-LN (PIC S9(4)) | FD-ACCT-ID (PIC 9(11))   | 4000-ACCTFILE-PROC line 214 |

## Error Handling

| Condition                                        | Action                                              | Return Code             | Source Location           |
| ------------------------------------------------ | --------------------------------------------------- | ----------------------- | ------------------------- |
| Any file operation on TRNX-FILE completes        | MOVE TRNXFILE-STATUS TO LK-M03B-RC                  | Two-byte VSAM status    | 1900-EXIT line 152        |
| Any file operation on XREF-FILE completes        | MOVE XREFFILE-STATUS TO LK-M03B-RC                  | Two-byte VSAM status    | 2900-EXIT line 176        |
| Any file operation on CUST-FILE completes        | MOVE CUSTFILE-STATUS TO LK-M03B-RC                  | Two-byte VSAM status    | 3900-EXIT line 201        |
| Any file operation on ACCT-FILE completes        | MOVE ACCTFILE-STATUS TO LK-M03B-RC                  | Two-byte VSAM status    | 4900-EXIT line 226        |
| LK-M03B-DD is not one of the four known DD names | GO TO 9999-GOBACK immediately; LK-M03B-RC is NOT updated | Unchanged (caller's prior value) | 0000-START line 127 |
| Operation code is W or Z (write/rewrite)         | Falls through all IF tests to the EXIT paragraph without performing any file I/O; file status IS returned reflecting the unchanged WORKING-STORAGE status from the last real operation on that file | Prior status value | All proc paragraphs |

Note: CBSTM03B does not issue its own error messages or ABEND calls. All error
detection is the responsibility of the caller (CBSTM03A), which inspects
LK-M03B-RC after each call.

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. 0000-START -- entry point; EVALUATE on LK-M03B-DD dispatches to one of four file-handling sections or GO TO 9999-GOBACK for unknown DD names
2. 1000-TRNXFILE-PROC THRU 1999-EXIT -- handles TRNX-FILE; operation determined by sequential IF chain on M03B-OPEN / M03B-READ (sequential) / M03B-CLOSE; status always captured at 1900-EXIT
3. 2000-XREFFILE-PROC THRU 2999-EXIT -- identical structure to 1000 block but for XREF-FILE (sequential read); status captured at 2900-EXIT
4. 3000-CUSTFILE-PROC THRU 3999-EXIT -- handles CUST-FILE; uses M03B-READ-K (keyed random read) instead of sequential; key built from LK-M03B-KEY/LK-M03B-KEY-LN via reference modification before READ; status captured at 3900-EXIT
5. 4000-ACCTFILE-PROC THRU 4999-EXIT -- identical structure to 3000 block but for ACCT-FILE (keyed read); status captured at 4900-EXIT
6. 9999-GOBACK -- single GOBACK statement; positioned immediately after 0000-START in source (line 130), before all file-handler paragraphs; reached by fall-through after any PERFORM block completes, or directly via GO TO for unknown DD name
