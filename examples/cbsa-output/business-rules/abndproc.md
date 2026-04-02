---
type: business-rules
program: ABNDPROC
program_type: online
status: draft
confidence: high
last_pass: 3
calls: []
called_by:
- BNK1CAC
- BNK1CCA
- BNK1CCS
- BNK1CRA
- BNK1DAC
- BNK1DCS
- BNK1TFN
- BNK1UAC
- BNKMENU
- CRDTAGY1
- CRDTAGY2
- CRDTAGY3
- CRDTAGY4
- CRDTAGY5
- CREACC
- CRECUST
- DBCRFUN
- DELACC
- DELCUS
- INQACC
- INQACCCU
- INQCUST
- XFRFUN
uses_copybooks:
- ABNDINFO
reads:
- ABNDFILE
writes:
- ABNDFILE
db_tables: []
transactions: []
mq_queues: []
---

# ABNDPROC -- Business Rules

## Program Purpose

ABNDPROC is a centralised abend-logging service for the CICS Banking Sample Application (CBSA). Any online program that detects an unrecoverable error (abend condition) passes abend details to this program via DFHCOMMAREA. ABNDPROC writes a single record to the VSAM KSDS file ABNDFILE keyed by a composite of UNIX time and CICS task number. This provides a single collection point for all application abends, allowing operators to view error history without hunting through individual transaction logs.

The program is invoked via `EXEC CICS LINK PROGRAM('ABNDPROC')` from caller programs. It performs no computation, no validation of the incoming data, and no looping -- it is a pure write-through persistence layer.

Note: UPDACC and UPDCUST also use the ABNDINFO copybook and contain references to ABNDPROC in their source, but they are not reflected in the frontmatter `called_by` list (which has been preserved as verified).

## Input / Output

| Direction | Resource    | Type                   | Description                                                                                                                                                                                        |
| --------- | ----------- | ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| IN        | DFHCOMMAREA | CICS                   | Abend record passed by the calling program. Layout defined directly in LINKAGE SECTION (COMM-VSAM-KEY, COMM-APPLID, COMM-TRANID, COMM-DATE, COMM-TIME, COMM-CODE, COMM-PROGRAM, COMM-RESPCODE, COMM-RESP2CODE, COMM-SQLCODE, COMM-FREEFORM). |
| OUT       | ABNDFILE    | VSAM KSDS (CICS FILE)  | Abend record written to the centralised KSDS datastore. Key is ABND-VSAM-KEY (12-byte composite: ABND-UTIME-KEY PIC S9(15) COMP-3 = 8 bytes packed + ABND-TASKNO-KEY PIC 9(4) = 4 bytes display). |

## Business Rules

### Abend Record Persistence

| #  | Rule                                            | Condition                                                                | Action                                                                                                                                                                                                      | Source Location         |
| -- | ----------------------------------------------- | ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- |
| 1  | Accept and persist abend record                 | Program entered with DFHCOMMAREA populated by calling program            | MOVE DFHCOMMAREA TO WS-ABND-AREA (group move between structurally identical layouts -- DFHCOMMAREA defined in LINKAGE SECTION, WS-ABND-AREA defined using the ABNDINFO copybook), then EXEC CICS WRITE to ABNDFILE using ABND-VSAM-KEY as the record identifier. | PREMIERE / A010 line 139-147 |
| 2  | VSAM write success -- normal exit               | WS-CICS-RESP = DFHRESP(NORMAL) after CICS WRITE                          | PERFORM GET-ME-OUT-OF-HERE, which issues EXEC CICS RETURN and GOBACK to return control to the calling program.                                                                                              | PREMIERE / A010 line 163 |
| 3  | VSAM write failure -- suppress abend and return | WS-CICS-RESP NOT= DFHRESP(NORMAL) after EXEC CICS WRITE to ABNDFILE     | DISPLAY four diagnostic lines (message text, RESP, RESP2 values) to the CICS log, then EXEC CICS RETURN immediately -- the program does NOT re-abend or call ABNDPROC recursively. The failed record is silently abandoned. | PREMIERE / A010 lines 149-158 |

### Record Key Composition

| #  | Rule                                                    | Condition | Action                                                                                                                                                                                                                                                                                 | Source Location                     |
| -- | ------------------------------------------------------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| 4  | VSAM key is a 12-byte composite of utime and task number | Always    | ABND-VSAM-KEY is a 12-byte composite: ABND-UTIME-KEY (PIC S9(15) COMP-3, 8 bytes packed -- microsecond UNIX timestamp supplied by caller) concatenated with ABND-TASKNO-KEY (PIC 9(4), 4 bytes display -- CICS task number supplied by caller). WS-ABND-KEY-LEN VALUE +12 in WORKING-STORAGE confirms this size, though that constant is never referenced in the EXEC CICS WRITE (no KEYLENGTH clause -- CICS derives key length from the file definition). Uniqueness relies on the caller populating both fields correctly before linking. | ABNDINFO copybook / LINKAGE SECTION |
| 5  | Key length constant is defined but never used           | Always    | WS-ABND-KEY-LEN PIC S9(8) COMP VALUE +12 is defined in WORKING-STORAGE at line 40. It is not referenced anywhere in the PROCEDURE DIVISION (the EXEC CICS WRITE has no KEYLENGTH clause). It is dead code within this program -- likely a scaffold artifact or note left for documentation purposes. | WORKING-STORAGE line 40             |

### Abend Record Content (fields written to ABNDFILE)

| #  | Rule                                  | Condition | Action                                                                                                                                                                          | Source Location          |
| -- | ------------------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| 6  | APPLID is recorded                    | Always    | ABND-APPLID (PIC X(8)) is written to ABNDFILE as received from COMM-APPLID in DFHCOMMAREA.                                                                                      | ABNDINFO copybook / A010 |
| 7  | TRANID is recorded                    | Always    | ABND-TRANID (PIC X(4)) is written to ABNDFILE as received from COMM-TRANID in DFHCOMMAREA.                                                                                      | ABNDINFO copybook / A010 |
| 8  | Date is recorded verbatim             | Always    | ABND-DATE (PIC X(10)) is written as received from COMM-DATE -- format is determined entirely by the calling program; ABNDPROC performs no date reformatting.                    | ABNDINFO copybook / A010 |
| 9  | Time is recorded verbatim             | Always    | ABND-TIME (PIC X(8)) is written as received from COMM-TIME -- format is determined entirely by the calling program.                                                             | ABNDINFO copybook / A010 |
| 10 | Abend code is recorded                | Always    | ABND-CODE (PIC X(4)) is written as received from COMM-CODE -- this is the 4-character CICS abend code.                                                                          | ABNDINFO copybook / A010 |
| 11 | Originating program is recorded       | Always    | ABND-PROGRAM (PIC X(8)) is written as received from COMM-PROGRAM.                                                                                                               | ABNDINFO copybook / A010 |
| 12 | CICS RESP code is recorded            | Always    | ABND-RESPCODE (PIC S9(8) DISPLAY SIGN LEADING SEPARATE) is written as received from COMM-RESPCODE.                                                                              | ABNDINFO copybook / A010 |
| 13 | CICS RESP2 code is recorded           | Always    | ABND-RESP2CODE (PIC S9(8) DISPLAY SIGN LEADING SEPARATE) is written as received from COMM-RESP2CODE.                                                                            | ABNDINFO copybook / A010 |
| 14 | SQL return code is recorded           | Always    | ABND-SQLCODE (PIC S9(8) DISPLAY SIGN LEADING SEPARATE) is written as received from COMM-SQLCODE. This allows DB2 errors to be captured alongside CICS errors in the same record. | ABNDINFO copybook / A010 |
| 15 | Freeform diagnostic text is recorded  | Always    | ABND-FREEFORM (PIC X(600)) is written as received from COMM-FREEFORM -- the caller is solely responsible for populating this field with human-readable context.                 | ABNDINFO copybook / A010 |

### Dead Code in LOCAL-STORAGE

| #  | Rule                                          | Condition | Action                                                                                                                                                                                                                                                                                                                                                                                                                  | Source Location            |
| -- | --------------------------------------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| 16 | LOCAL-STORAGE scaffolding items are all unused | Always    | The LOCAL-STORAGE SECTION defines the following items that are never referenced in the PROCEDURE DIVISION: DB2-DATE-REFORMAT (date reformatting work area, lines 45-51), DATA-STORE-TYPE with 88-level conditions DATASTORE-TYPE-DLI VALUE '1' / DATASTORE-TYPE-DB2 VALUE '2' / DATASTORE-TYPE-VSAM VALUE 'V' (lines 52-55), WS-EIBTASKN12 PIC 9(12) (line 57), WS-SQLCODE-DISP PIC 9(9) (line 58), WS-U-TIME PIC S9(15) COMP-3 (line 65), WS-ORIG-DATE / WS-ORIG-DATE-GRP / WS-ORIG-DATE-GRP-X (lines 66-79), WS-PASSED-DATA with WS-TEST-KEY / WS-SORT-CODE / WS-CUSTOMER-RANGE (lines 82-88), WS-SORT-DIV (lines 90-93), CUSTOMER-KY with REQUIRED-SORT-CODE / REQUIRED-ACC-NUM (lines 95-97), PROCTRAN-RIDFLD PIC S9(8) COMP (line 99), SQLCODE-DISPLAY PIC S9(8) (lines 101-102), MY-ABEND-CODE PIC XXXX (line 104). These appear to be boilerplate carried over from another program template. None affect runtime behaviour. | LOCAL-STORAGE lines 45-104 |

## Calculations

| Calculation | Formula / Logic                                                               | Input Fields          | Output Field             | Source Location |
| ----------- | ----------------------------------------------------------------------------- | --------------------- | ------------------------ | --------------- |
| None        | ABNDPROC performs no arithmetic. All fields are passed in by the caller and written verbatim via a single group MOVE and EXEC CICS WRITE. | DFHCOMMAREA (all fields) | WS-ABND-AREA -> ABNDFILE | N/A             |

## Error Handling

| Condition                                                                             | Action                                                                                                                                                                                                                     | Return Code                              | Source Location               |
| ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | ----------------------------- |
| EXEC CICS WRITE to ABNDFILE returns WS-CICS-RESP NOT= DFHRESP(NORMAL)                | DISPLAY '*********************************************' to CICS log; DISPLAY '**** Unable to write to the file ABNDFILE !!!' to CICS log; DISPLAY 'RESP=' WS-CICS-RESP ' RESP2=' WS-CICS-RESP2 to CICS log; DISPLAY '*********************************************'; then EXEC CICS RETURN without re-raising any abend. The failed record is silently abandoned. | None issued to caller; program returns normally | PREMIERE / A010 lines 149-158 |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. PREMIERE / A010 (line 132) -- Entry point. MOVE DFHCOMMAREA TO WS-ABND-AREA copies all fields from the LINKAGE SECTION layout into the WORKING-STORAGE layout defined by the ABNDINFO copybook.
2. PREMIERE / A010 (lines 141-147) -- EXEC CICS WRITE FILE('ABNDFILE') FROM(WS-ABND-AREA) RIDFLD(ABND-VSAM-KEY) RESP(WS-CICS-RESP) RESP2(WS-CICS-RESP2). Writes the abend record to the VSAM KSDS. No KEYLENGTH clause -- CICS uses the file definition.
3. PREMIERE / A010 (lines 149-158) -- IF WS-CICS-RESP NOT= DFHRESP(NORMAL): log four DISPLAY lines to CICS log and EXEC CICS RETURN (early exit; write has failed and record is not persisted).
4. PREMIERE / A010 (line 163) -- Normal path (write succeeded): PERFORM GET-ME-OUT-OF-HERE.
5. GET-ME-OUT-OF-HERE / GMOOH010 (lines 171-173) -- EXEC CICS RETURN then GOBACK. Program ends and control returns to caller.
