---
type: integration
subtype: io-map
status: draft
confidence: medium
last_pass: 1
---

# I/O Map

Complete mapping of every program to every external resource it accesses, with direction and access pattern.

## Program I/O Summary

| Program        | Files Read | Files Written | DB Tables | MQ Queues | Screens  |
| -------------- | ---------- | ------------- | --------- | --------- | -------- |
| [PROGRAM-NAME] | [n]        | [n]           | [n]       | [n]       | [n]      |

## Detailed I/O Map

| Program        | Resource       | Type                   | Direction     | Access Pattern     |
| -------------- | -------------- | ---------------------- | ------------- | ------------------ |
| [PROGRAM-NAME] | [RESOURCE]     | [File/DB2/MQ/CICS/IMS] | [IN/OUT/BOTH] | [Seq/Keyed/Cursor] |

## Shared Resources

Resources accessed by multiple programs:

| Resource       | Type        | Read By            | Written By         |
| -------------- | ----------- | ------------------ | ------------------ |
| [RESOURCE]     | [File/DB/Q] | [PROG-A, PROG-B]  | [PROG-C]           |
