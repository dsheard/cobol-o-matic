---
type: test-specifications
subtype: equivalence-matrix
status: draft
confidence: medium
last_pass: 1
---

# Equivalence Matrix

Traceability from test scenarios back to business rules and source programs. This matrix is a reference for auditors and SMEs -- it does not dictate test organization (tests are organized by capability, not by program).

## Traceability

| Test ID | Capability   | Scenario     | Business Rules | Source Programs | Source Paragraphs |
| ------- | ------------ | ------------ | -------------- | --------------- | ----------------- |
| T-001   | [Cap name]   | [Scenario]   | [BR-nnn]       | [PROGRAM]       | [Paragraph]       |

## Coverage Summary

| Capability   | Total Tests | Happy Path | Error | Boundary | Confidence   |
| ------------ | ----------- | ---------- | ----- | -------- | ------------ |
| [Cap name]   | 0           | 0          | 0     | 0        | [high/med/low] |

## Untested Rules

Business rules from the analysis artifacts that are not covered by any test scenario. These represent gaps requiring SME review or additional test design:

| Rule ID | Program   | Rule Description       | Reason Untested           | Priority          |
| ------- | --------- | ---------------------- | ------------------------- | ----------------- |
| [BR-nnn] | [PROGRAM] | [What the rule does]  | [Why no test was derived] | [High/Medium/Low] |
