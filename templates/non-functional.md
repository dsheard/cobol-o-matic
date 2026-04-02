---
type: requirements
subtype: non-functional
status: draft
confidence: medium
last_pass: 1
---

# Non-Functional Requirements

Derived non-functional requirements observed in the COBOL source code.

## Error Handling

| Program        | Pattern                          | Approach              | Evidence              |
| -------------- | -------------------------------- | --------------------- | --------------------- |
| [PROGRAM-NAME] | [SQLCODE/FILE STATUS/DFHRESP]    | [ABEND/graceful/retry] | [Source location]    |

## Data Integrity

| Program        | Pattern                          | Mechanism             | Evidence              |
| -------------- | -------------------------------- | --------------------- | --------------------- |
| [PROGRAM-NAME] | [Commit/Syncpoint/Locking]       | [Description]         | [Source location]     |

## Performance

| Program        | Pattern                          | Indicator             | Evidence              |
| -------------- | -------------------------------- | --------------------- | --------------------- |
| [PROGRAM-NAME] | [SORT/Buffer/Checkpoint]         | [Description]         | [Source location]     |

## Security

| Program        | Pattern                          | Mechanism             | Evidence              |
| -------------- | -------------------------------- | --------------------- | --------------------- |
| [PROGRAM-NAME] | [Auth check/User ID validation]  | [Description]         | [Source location]     |

## Audit and Logging

| Program        | Pattern                          | Mechanism             | Evidence              |
| -------------- | -------------------------------- | --------------------- | --------------------- |
| [PROGRAM-NAME] | [DISPLAY/Audit WRITE/Timestamp]  | [Description]         | [Source location]     |

## Recovery

| Program        | Pattern                          | Mechanism             | Evidence              |
| -------------- | -------------------------------- | --------------------- | --------------------- |
| [PROGRAM-NAME] | [Restart/Checkpoint/Backout]     | [Description]         | [Source location]     |
