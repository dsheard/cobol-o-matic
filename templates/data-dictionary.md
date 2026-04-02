---
type: data
subtype: data-dictionary
status: draft
confidence: medium
last_pass: 1
---

# Data Dictionary

All data items extracted from WORKING-STORAGE, LOCAL-STORAGE, LINKAGE SECTION, and copybooks.

## Key Data Structures

### [Structure Name]

Defined in: [PROGRAM or COPYBOOK]

| Level | Name         | PIC     | Usage     | Description   |
| ----- | ------------ | ------- | --------- | ------------- |
| 01    | [GROUP-NAME] |         |           | [Purpose]     |
| 05    | [FIELD-NAME] | [X(10)] | [DISPLAY] | [Description] |

## Shared Data Items

Data items defined in copybooks and used across multiple programs:

| Data Item    | Defined In | Used By Programs | PIC    | Description   |
| ------------ | ---------- | ---------------- | ------ | ------------- |
| [FIELD-NAME] | [COPYBOOK] | [PROG1, PROG2]   | [9(5)] | [Description] |

## Constants and Literals

Named constants (88-level items) and significant literals found in the codebase:

| Constant | Value   | Defined In         | Usage Context |
| -------- | ------- | ------------------ | ------------- |
| [NAME]   | [VALUE] | [PROGRAM/COPYBOOK] | [Context]     |
