---
type: integration
subtype: interfaces
status: draft
confidence: medium
last_pass: 1
---

# External Interfaces

All external system touchpoints identified in the COBOL source.

## Interface Summary

| Interface | Type                   | Direction     | Used By Programs | Description   |
| --------- | ---------------------- | ------------- | ---------------- | ------------- |
| [Name]    | [File/DB2/MQ/CICS/TCP] | [IN/OUT/BOTH] | [PROG1, PROG2]   | [Description] |

## File Interfaces

| DD Name / Path | Organisation | Record Layout  | Read By    | Written By | Description |
| -------------- | ------------ | -------------- | ---------- | ---------- | ----------- |
| [DDNAME]       | [Seq/VSAM]   | [copybook ref] | [programs] | [programs] | [Purpose]   |

## Database Interfaces

| Table / Segment | Operations                       | Programs   | Key Columns | Description |
| --------------- | -------------------------------- | ---------- | ----------- | ----------- |
| [TABLE-NAME]    | [SELECT, INSERT, UPDATE, DELETE] | [programs] | [columns]   | [Purpose]   |

## Messaging Interfaces

| Queue / Topic | Direction | Programs   | Message Format | Description |
| ------------- | --------- | ---------- | -------------- | ----------- |
| [QUEUE-NAME]  | [PUT/GET] | [programs] | [copybook ref] | [Purpose]   |

## CICS Interfaces

| Transaction | Program   | Map/Mapset | Comm Area  | Description |
| ----------- | --------- | ---------- | ---------- | ----------- |
| [TRAN-ID]   | [PROGRAM] | [MAP]      | [COPYBOOK] | [Purpose]   |

## External System Boundary

Systems or applications referenced but outside the analysed codebase:

| System        | Interface Type   | Direction | Evidence         |
| ------------- | ---------------- | --------- | ---------------- |
| [System name] | [File/MQ/DB/API] | [IN/OUT]  | [How identified] |
