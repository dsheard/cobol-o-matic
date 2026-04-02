---
type: business-rules
program: CSUTLDTC
program_type: subprogram
status: draft
confidence: high
last_pass: 4
calls:
- CEEDAYS
called_by:
- CORPT00C
- COTRN02C
uses_copybooks: []
reads: []
writes: []
db_tables: []
transactions: []
mq_queues: []
---

# CSUTLDTC -- Business Rules

## Program Purpose

CSUTLDTC is a date-validation utility subprogram. It accepts a date string and a
picture-format mask, delegates conversion to the IBM Language Environment
`CEEDAYS` API (which converts a character date to a Lilian day number), inspects
the CEEDAYS feedback code, and returns a human-readable validation result and a
numeric severity back to the caller. Every caller that needs to check whether a
date value is well-formed calls this program rather than invoking `CEEDAYS`
directly.

## Input / Output

| Direction | Resource       | Type        | Description                                                               |
| --------- | -------------- | ----------- | ------------------------------------------------------------------------- |
| IN        | LS-DATE        | Linkage     | 10-character date string to validate (e.g., `2022-07-19`)                |
| IN        | LS-DATE-FORMAT | Linkage     | 10-character picture mask describing the date format (e.g., `YYYY-MM-DD`) |
| OUT       | LS-RESULT      | Linkage     | 80-character message block: severity (4), literal `Mesg Code:` (11), message number (4), space (1), result text (15), space (1), literal `TstDate:` (9), date echo (10), space (1), literal `Mask used:` (10), format echo (10), space (1), filler spaces (3) |
| OUT       | RETURN-CODE    | System      | Numeric severity from CEEDAYS feedback code; 0 = date is valid           |
| CALL      | CEEDAYS        | LE API      | IBM Language Environment date-conversion service; converts character date to Lilian integer |

## Business Rules

### Date Validation -- CEEDAYS Feedback Interpretation

| #  | Rule                         | Condition                                           | Action                                        | Source Location        |
| -- | ---------------------------- | --------------------------------------------------- | --------------------------------------------- | ---------------------- |
| 1  | Date is valid                | `FC-INVALID-DATE` is TRUE (feedback = X'0000000000000000') | Move `'Date is valid'` to WS-RESULT    | A000-MAIN line 129-130 |
| 2  | Insufficient data            | `FC-INSUFFICIENT-DATA` is TRUE (feedback = X'000309CB59C3C5C5') | Move `'Insufficient'` to WS-RESULT | A000-MAIN line 131-132 |
| 3  | Bad date value               | `FC-BAD-DATE-VALUE` is TRUE (feedback = X'000309CC59C3C5C5') | Move `'Datevalue error'` to WS-RESULT | A000-MAIN line 133-134 |
| 4  | Invalid era                  | `FC-INVALID-ERA` is TRUE (feedback = X'000309CD59C3C5C5') | Move `'Invalid Era    '` to WS-RESULT | A000-MAIN line 135-136 |
| 5  | Unsupported range            | `FC-UNSUPP-RANGE` is TRUE (feedback = X'000309D159C3C5C5') | Move `'Unsupp. Range  '` to WS-RESULT | A000-MAIN line 137-138 |
| 6  | Invalid month                | `FC-INVALID-MONTH` is TRUE (feedback = X'000309D559C3C5C5') | Move `'Invalid month  '` to WS-RESULT | A000-MAIN line 139-140 |
| 7  | Bad picture string           | `FC-BAD-PIC-STRING` is TRUE (feedback = X'000309D659C3C5C5') | Move `'Bad Pic String '` to WS-RESULT | A000-MAIN line 141-142 |
| 8  | Non-numeric data in date     | `FC-NON-NUMERIC-DATA` is TRUE (feedback = X'000309D859C3C5C5') | Move `'Nonnumeric data'` to WS-RESULT | A000-MAIN line 143-144 |
| 9  | Year in era is zero          | `FC-YEAR-IN-ERA-ZERO` is TRUE (feedback = X'000309D959C3C5C5') | Move `'YearInEra is 0 '` to WS-RESULT | A000-MAIN line 145-146 |
| 10 | All other CEEDAYS errors     | WHEN OTHER (any unrecognised feedback value)        | Move `'Date is invalid'` to WS-RESULT         | A000-MAIN line 147-148 |

### Note on Rule 1 Naming

The 88-level condition `FC-INVALID-DATE` has a VALUE of X'0000000000000000' (all
zeroes), which is the CEEDAYS feedback token returned when the call **succeeds**
and the date **is** valid. The name is misleading -- all-zero feedback means no
error. The result text `'Date is valid'` confirms this interpretation.

### Result Text Literal Lengths

The source includes an explicit maintenance comment at line 126-127:

```
*    WS-RESULT IS 15 CHARACTERS
*                123456789012345'
```

WS-RESULT is a 15-character field. Not all result literals are exactly 15
characters -- shorter literals are right-padded by COBOL's alphanumeric MOVE to
fill the field. Actual literal lengths from source:

| Result Text         | Actual Length | Rule # |
| ------------------- | ------------- | ------ |
| `'Date is valid'`   | 13 characters | 1      |
| `'Insufficient'`    | 12 characters | 2      |
| `'Datevalue error'` | 15 characters | 3      |
| `'Invalid Era    '` | 15 characters | 4      |
| `'Unsupp. Range  '` | 15 characters | 5      |
| `'Invalid month  '` | 15 characters | 6      |
| `'Bad Pic String '` | 15 characters | 7      |
| `'Nonnumeric data'` | 15 characters | 8      |
| `'YearInEra is 0 '` | 15 characters | 9      |
| `'Date is invalid'` | 15 characters | 10     |

Rules 1 and 2 rely on COBOL implicit right-padding with spaces. Callers that
parse WS-RESULT by exact string match rather than by leading characters must
account for this trailing-space padding.

### Severity Return

| #  | Rule                    | Condition                  | Action                                                | Source Location       |
| -- | ----------------------- | -------------------------- | ----------------------------------------------------- | --------------------- |
| 11 | Return numeric severity | Always, after CEEDAYS call | SEVERITY sub-field of FEEDBACK-CODE moved to RETURN-CODE via WS-SEVERITY-N | PROCEDURE DIVISION line 98, A000-MAIN line 123 |
| 12 | Return message number   | Always, after CEEDAYS call | MSG-NO sub-field of FEEDBACK-CODE moved to WS-MSG-NO-N for inclusion in LS-RESULT | A000-MAIN line 124   |

## Calculations

| Calculation           | Formula / Logic                                                                 | Input Fields                        | Output Field     | Source Location       |
| --------------------- | ------------------------------------------------------------------------------- | ----------------------------------- | ---------------- | --------------------- |
| Lilian date conversion | CEEDAYS converts a character date string under a given picture mask to a Lilian day number (days since 14 October 1582) | WS-DATE-TO-TEST (from LS-DATE), WS-DATE-FORMAT (from LS-DATE-FORMAT) | OUTPUT-LILLIAN (S9(9) BINARY) | A000-MAIN line 116-120 |
| Input string binding -- date | LENGTH OF LS-DATE (10) moved to VSTRING-LENGTH of WS-DATE-TO-TEST; LS-DATE moved to VSTRING-TEXT of WS-DATE-TO-TEST and to WS-DATE (echo field) | LS-DATE | WS-DATE-TO-TEST (VSTRING-LENGTH + VSTRING-TEXT), WS-DATE | A000-MAIN line 105-108 |
| Input string binding -- format | LENGTH OF LS-DATE-FORMAT (10) moved to VSTRING-LENGTH of WS-DATE-FORMAT; LS-DATE-FORMAT moved to VSTRING-TEXT of WS-DATE-FORMAT and to WS-DATE-FMT (echo field) | LS-DATE-FORMAT | WS-DATE-FORMAT (VSTRING-LENGTH + VSTRING-TEXT), WS-DATE-FMT | A000-MAIN line 109-113 |

## Error Handling

| Condition                         | Action                                                    | Return Code                      | Source Location        |
| --------------------------------- | --------------------------------------------------------- | -------------------------------- | ---------------------- |
| FC-INSUFFICIENT-DATA from CEEDAYS | WS-RESULT = `'Insufficient'`; WS-SEVERITY-N set from feedback; returned in RETURN-CODE | Non-zero SEVERITY from CEEDAYS   | A000-MAIN line 131-132 |
| FC-BAD-DATE-VALUE from CEEDAYS    | WS-RESULT = `'Datevalue error'`                           | Non-zero SEVERITY from CEEDAYS   | A000-MAIN line 133-134 |
| FC-INVALID-ERA from CEEDAYS       | WS-RESULT = `'Invalid Era    '`                           | Non-zero SEVERITY from CEEDAYS   | A000-MAIN line 135-136 |
| FC-UNSUPP-RANGE from CEEDAYS      | WS-RESULT = `'Unsupp. Range  '`                           | Non-zero SEVERITY from CEEDAYS   | A000-MAIN line 137-138 |
| FC-INVALID-MONTH from CEEDAYS     | WS-RESULT = `'Invalid month  '`                           | Non-zero SEVERITY from CEEDAYS   | A000-MAIN line 139-140 |
| FC-BAD-PIC-STRING from CEEDAYS    | WS-RESULT = `'Bad Pic String '`                           | Non-zero SEVERITY from CEEDAYS   | A000-MAIN line 141-142 |
| FC-NON-NUMERIC-DATA from CEEDAYS  | WS-RESULT = `'Nonnumeric data'`                           | Non-zero SEVERITY from CEEDAYS   | A000-MAIN line 143-144 |
| FC-YEAR-IN-ERA-ZERO from CEEDAYS  | WS-RESULT = `'YearInEra is 0 '`                           | Non-zero SEVERITY from CEEDAYS   | A000-MAIN line 145-146 |
| Any other CEEDAYS error           | WS-RESULT = `'Date is invalid'`                           | Non-zero SEVERITY from CEEDAYS   | A000-MAIN line 147-148 |
| CEEDAYS success (all-zero token)  | WS-RESULT = `'Date is valid'`; RETURN-CODE = 0            | 0 (zero severity)                | A000-MAIN line 129-130 |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. PROCEDURE DIVISION entry -- INITIALIZE WS-MESSAGE; MOVE SPACES TO WS-DATE (line 90-91)
2. PERFORM A000-MAIN THRU A000-MAIN-EXIT -- single main paragraph that does all work (line 93-94)
3. A000-MAIN -- copies LS-DATE into CEEDAYS VString structure (WS-DATE-TO-TEST) and into WS-DATE echo field; copies LS-DATE-FORMAT into WS-DATE-FORMAT VString and WS-DATE-FMT echo field; initialises OUTPUT-LILLIAN to 0 (line 105-114)
4. CALL 'CEEDAYS' USING WS-DATE-TO-TEST, WS-DATE-FORMAT, OUTPUT-LILLIAN, FEEDBACK-CODE -- IBM LE date conversion API (line 116-120)
5. A000-MAIN (post-call) -- MOVE WS-DATE-TO-TEST TO WS-DATE: this moves the entire VString group (2-byte binary length prefix + text) into the 10-char WS-DATE field. The first 2 bytes of WS-DATE will be binary (the VString length value), not the ASCII/EBCDIC date characters. This corrupts the date echo field in the LS-RESULT output block. The pre-call copy at line 107-108 correctly placed LS-DATE text into WS-DATE; this post-call overwrite replaces it with a garbled value. (line 122)
6. A000-MAIN (post-call) -- extracts SEVERITY from FEEDBACK-CODE into WS-SEVERITY-N; extracts MSG-NO from FEEDBACK-CODE into WS-MSG-NO-N (line 123-124)
7. A000-MAIN (post-call) -- EVALUATE TRUE on FEEDBACK-TOKEN-VALUE 88-levels to set WS-RESULT text (15-char message) (line 128-149)
8. PROCEDURE DIVISION (return) -- MOVE WS-MESSAGE TO LS-RESULT; MOVE WS-SEVERITY-N TO RETURN-CODE; EXIT PROGRAM (line 97-100)

## Data Quality Note -- Corrupted Date Echo in LS-RESULT

At line 122, `MOVE WS-DATE-TO-TEST TO WS-DATE` moves the group-level VString
structure (which begins with a 2-byte binary `Vstring-length` field, value 10,
followed by the date text characters) into the 10-character `WS-DATE` PIC X(10)
field. This means:

- Bytes 1-2 of WS-DATE will be binary X'000A' (the value 10 stored as BINARY
  S9(4)) rather than the first two characters of the date.
- Bytes 3-10 of WS-DATE will contain the first 8 characters of the date text.
- The 9th and 10th date characters are lost.

The net effect is that the `TstDate:` portion of the 80-character LS-RESULT
block returned to callers will contain garbled binary data in positions 1-2
rather than the original date string. Callers (CORPT00C, COTRN02C) do not
appear to parse the TstDate field from LS-RESULT -- they test only
`CSUTLDTC-RESULT-SEV-CD` (positions 1-4) and `CSUTLDTC-RESULT-MSG-NUM`
(positions 16-19 of the result block) -- so this corruption has no functional
impact on current callers, but any future caller that reads the date echo field
will receive incorrect data.
