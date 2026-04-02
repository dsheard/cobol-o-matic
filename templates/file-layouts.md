---
type: data
subtype: file-layouts
status: draft
confidence: medium
last_pass: 1
---

# File Layouts

File descriptions (FD/SD) and their record layouts extracted from FILE SECTION.

## Files

### [Logical File Name]

| Property       | Value                         |
| -------------- | ----------------------------- |
| FD Name        | [FD-NAME]                     |
| DD Name / Path | [DDNAME or file path]         |
| Organisation   | [Sequential/Indexed/Relative] |
| Access Mode    | [Sequential/Random/Dynamic]   |
| Record Length  | [n bytes]                     |
| Read By        | [PROG1, PROG2]                |
| Written By     | [PROG3]                       |

**Record Layout:**

| Level | Name          | PIC     | Offset | Length | Description   |
| ----- | ------------- | ------- | ------ | ------ | ------------- |
| 01    | [RECORD-NAME] |         | 0      | [n]    | [Purpose]     |
| 05    | [FIELD-NAME]  | [X(10)] | [0]    | [10]   | [Description] |

## File Summary

| File      | Organisation | Record Len | Read By    | Written By |
| --------- | ------------ | ---------- | ---------- | ---------- |
| [FD-NAME] | [Seq]        | [n]        | [programs] | [programs] |
