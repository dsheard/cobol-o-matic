---
type: inventory
subtype: copybooks
status: draft
confidence: medium
last_pass: 1
---

# Copybook Inventory

Catalog of all copybooks (COPY members) found in the source directory.

## Copybooks

| Copybook    | Source File    | Used By        | Fields | Purpose         |
| ----------- | -------------- | -------------- | ------ | --------------- |
| [COPY-NAME] | [filename.cpy] | [PROG1, PROG2] | [n]    | [Brief purpose] |

## Orphan Copybooks

Copybooks in the source directory not referenced by any analysed program:

- [COPY-NAME]

## Missing Copybooks

Copybooks referenced by COPY statements but not found in the source directory:

| Copybook    | Referenced By  |
| ----------- | -------------- |
| [COPY-NAME] | [PROGRAM-NAME] |
