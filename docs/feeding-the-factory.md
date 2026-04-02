# Reverse-engineering legacy COBOL into requirements and test specs

Legacy modernization projects usually start with workshops: analysts read COBOL, interview SMEs, and turn the findings into documents that are already stale by the time implementation begins. I wanted a better first draft, so I built a tool that reads COBOL source and emits structured requirements, business rules, and test specifications with source traceability.

The split is simple. Python does the deterministic work: parsing divisions and paragraphs, building call graphs, extracting copybooks and file I/O, and chunking large programs. Bounded agents do the interpretive work: turning that structure into usable artifacts rather than freeform summaries.

To keep this grounded, the repository includes full example outputs for two public COBOL applications: AWS CardDemo (31 programs, about 19,600 lines of COBOL) and IBM's CICS Banking Sample Application (29 programs). They produce 50 and 48 markdown artifacts respectively across inventory, data, flow, integration, per-program business rules, synthesized requirements, and test specifications.

That doesn't prove the approach is ready for every 800,000-line estate. It does show this is more than a toy prompt aimed at a toy program: the workflow can analyze non-trivial CICS/VSAM/DB2 applications and emit artifacts a team can review, validate, and use.

The reality for most legacy modernization programs is that the original requirements are buried inside 800,000 lines of COBOL written over four decades, spread across hundreds of programs, with no living documentation and the original developers long retired. Business logic isn't missing, but it might as well be. It's encoded in PROCEDURE DIVISION paragraphs, `EVALUATE` statements, `PERFORM THRU` sequences, and cryptic variable names like `WS-ACCT-STAT-CD`. The organization runs on this logic every day. They just can't read it anymore, at the scale needed to rewrite it.

Most modernization approaches treat discovery as a consulting exercise. Teams of analysts spend months reading COBOL, interviewing SMEs, and writing Word documents. The output is expensive, incomplete, and stale by the time implementation starts. Worse, it's disconnected from the source: if an analyst writes "the system validates account status before processing transactions," there's no traceability back to the specific paragraph, condition, and action in the code.

What has worked well for me is treating reverse engineering as a workflow that produces structured, traceable artifacts in a format downstream tooling can consume. The output isn't a report. It's a set of machine-readable specifications that can feed requirements, planning, and testing work downstream. Instead of agents writing code from specs, agents read code and produce specs.

## What it produces on real codebases

At a high level, the tool produces:

- inventories of programs, copybooks, and JCL
- data dictionaries, file and database operations, and interface maps
- per-program business rules with source traceability
- synthesized capabilities, test specifications, and modernization notes

All of those are markdown files with YAML frontmatter, so they can be reviewed by humans and consumed by downstream tooling.

## A tiny example

Starting from a simplified COBOL fragment:

```cobol
IF ACCT-STATUS = 'C'
    MOVE 'Y' TO ERROR-FLAG
    PERFORM 9000-ERROR-RTN
END-IF
```

A business-rules artifact should capture that behavior in business terms:

| Rule                 | Condition                | Action                                         |
| -------------------- | ------------------------ | ---------------------------------------------- |
| Account status check | Account status is Closed | Skip processing and return an error indication |

And the derived test spec becomes:

| Scenario                | Preconditions                | Input                | Expected Output              |
| ----------------------- | ---------------------------- | -------------------- | ---------------------------- |
| Closed account rejected | Account exists and is Closed | Valid account number | Error: account not available |

That is the goal: not to summarize code, but to turn implementation detail into artifacts a product, migration, and test team can all use.

## Layer 1: deterministic parsing

Before any agent touches the COBOL, Python handles the structural work. This is a critical design choice: agents shouldn't decide what comes next or where artifacts should live. Structure is deterministic; interpretation is not.

The parser handles:

**Division and paragraph extraction.** COBOL programs have a rigid structure - IDENTIFICATION, ENVIRONMENT, DATA, and PROCEDURE divisions. Within the PROCEDURE DIVISION, paragraphs are the fundamental unit of logic. The parser identifies every paragraph, its line range, its `PERFORM` targets, and any `PERFORM ... THRU` ranges (a COBOL pattern where a single statement executes a contiguous sequence of paragraphs).

**Classification.** Each paragraph is classified by its structural role - dispatch (main routing logic), validation, I/O, error handling, screen handling, computation, or utility - based on the COBOL verbs and patterns it contains. This classification drives how paragraphs are grouped for analysis.

**Fact extraction.** Regex-based extraction pulls out copybook references, SQL table names, CICS commands, `CALL` and `XCTL` targets, file I/O operations, transaction IDs, and program type (online, batch, or subprogram). These facts are cross-referenced across all programs to build a call graph, a reverse call graph, and a per-program file-usage map that later artifacts can turn into producer-consumer views.

**Chunking.** Large programs (2,000+ lines is the default threshold) are split into semantic chunks: groups of related paragraphs that can be analyzed independently. Dispatch targets stay together. `PERFORM THRU` ranges are kept intact. Error-handling EXIT paragraphs are attached to their parent chunks. Each chunk gets a context header with relevant DATA DIVISION literals so the agent has the definitions it needs without reading the entire program.

The output of this layer is a manifest for each program and a cross-program facts file. Analysis artifacts are organized into subdirectories by concern: `inventory/`, `data/`, `flows/`, `integration/`, `business-rules/`, `requirements/`, and `test-specs/`.

```yaml
# staging/program-facts.yaml (simplified)
program_types:
  CBACT01C: batch
  COSGN00C: online
  CBTRN02C: online
call_graph:
  CBACT01C: [CBACT02C, CBACT03C]
  COSGN00C: [CSUTLDTC]
called_by:
  CBACT02C: [CBACT01C]
  CSUTLDTC: [COSGN00C, COSGN01C]
files:
  CBACT01C: [ACCTFILE, XREFFILE]
  CBACT03C: [ACCTFILE, ACTRPT]
copybooks:
  CBACT01C: [CVACT01Y, CVACT02Y]
transids:
  COSGN00C: CA00
```

Deterministic pre-processing sets up context before the agent does interpretive work. The parser doesn't decide what the code means. It gives agents a structured map of where to look and what's there.

## Layer 2: specialized agents for semantic interpretation

With that structural map in hand, an orchestrator agent spawns specialized workers - each responsible for a different artifact type, each operating within a bounded scope with a strict output template.

### Five workers, then three synthesis passes

| Worker             | What it reads                                 | What it writes                                                      |
| ------------------ | --------------------------------------------- | ------------------------------------------------------------------- |
| **Inventory**      | All source files, copybooks, JCL              | Program catalog, copybook catalog, JCL job inventory                |
| **Data**           | DATA DIVISIONs, copybooks, SQL                | Data dictionary, file layouts, database operations                  |
| **Flow**           | PERFORM/CALL/XCTL patterns, JCL               | Program call graph (with Mermaid diagrams), batch flows, data flows |
| **Integration**    | CICS/MQ/file I/O, external calls              | Interface catalog, I/O map                                          |
| **Business Rules** | PROCEDURE DIVISION (per-program or per-chunk) | Business rules per program                                          |

Each worker gets a self-contained prompt that includes the full workflow, domain knowledge, and output template. Workers don't need to read external reference material or figure out what format to use. The template is embedded in the prompt. In practice, each worker behaves like a bounded skill: clear input contract, fixed template, explicit definition of done.

### Structured output, not freeform analysis

Every artifact follows a template with YAML frontmatter and predefined sections. Here's a simplified business rules artifact:

```yaml
---
type: business-rules
program: "CBACT01C"
program_type: batch
status: draft
confidence: medium
calls: [CBACT02C, CBACT03C]
called_by: []
uses_copybooks: [CVACT01Y, CVACT02Y]
reads: [ACCTFILE, XREFFILE]
writes: [ACTRPT]
db_tables: []
transactions: []
---

# CBACT01C - Business Rules

## Program Purpose
Batch account processing program that reads the account master file,
applies daily transaction updates, and produces an activity report.

## Business Rules

### Validation
| # | Rule | Condition | Action | Source Location |
|--|---|------|----|--------|
| 1 | Account status check | IF ACCT-STATUS = 'C' | Skip processing, write to reject report | 1000-VALIDATE-ACCT |
| 2 | Balance threshold | IF ACCT-BALANCE < ZERO | Set error flag, PERFORM 9000-ERROR-RTN | 1000-VALIDATE-ACCT |

### Calculations
| Calculation | Formula / Logic | Input Fields | Output Field | Source Location |
|-------|--------|-------|-------|---------|
| Daily interest | ACCT-BALANCE * DAILY-RATE / 365 | ACCT-BALANCE, DAILY-RATE | WS-INTEREST-AMT | 2000-CALC-INTEREST |
```

The frontmatter isn't decoration. It's machine-readable metadata that downstream tooling consumes. `calls` and `called_by` establish dependency graphs. `reads` and `writes` define data lineage. `confidence` signals where human review should focus. Like the requirement frontmatter used downstream (`id`, `title`, `status`), it gives later steps something structured to consume.

### Chunked analysis for large programs

Production COBOL programs routinely exceed 5,000 lines. Sending the entire program to an agent would either exceed context limits or dilute attention across too much code. The chunking strategy addresses this:

1. The deterministic parser splits the PROCEDURE DIVISION into semantic chunks
2. Each chunk gets its own agent session with the chunk source, the DATA DIVISION (shared context), and the program manifest
3. Each session writes to the same output file, building up the business rules incrementally
4. After all chunks complete, a coverage check verifies that every HIGH-priority paragraph from the manifest appears in the output

Large programs are broken into bounded pieces that agents can handle reliably, with deterministic checks to catch gaps before the merged output is treated as complete.

## Evaluation: deterministic checks, then a critic pass

Evaluation is also two-layered.

**Deterministic validation** is currently used as a structural audit after the cross-cutting and test-spec phases, and the same helpers are reused for business-rules reconciliation. In practice, it checks things like:

- Does the artifact file exist where the template expects it?
- Do template-derived artifacts have the expected `type` / `subtype` frontmatter?
- Are all required sections present with substantive content?
- Are there stray markdown files at the output root that don't belong there?
- For test specs, do the coverage-summary counts and capability sections line up?

For business rules, validation goes deeper: frontmatter fields are reconciled against the parser's `ProgramFacts`. If the parser found three copybook references but the agent only listed two, that gets repaired and reported. If the parser classified a program as `online` but the agent wrote `batch`, that gets repaired and reported.

**The critic agent** then runs a semantic cross-check on the high-value shared artifacts: today that means the cross-cutting outputs and the synthesized test specifications. It reads the artifacts, cross-references claims against the actual source code, and fixes issues in place:

- Does the program count in the inventory match the number of `.cbl` / `.cob` files on disk? (Agents occasionally miss programs or double-count.)
- Does the call graph include every `CALL`, `EXEC CICS LINK`, and `EXEC CICS XCTL` statement? (Verified by code search against all source files.)
- Are program type classifications plausible?
- Do batch flows match JCL `EXEC PGM=` steps?
- Do the interface and test-spec artifacts contradict the source or each other?

The critic has the same basic file and search tools as the workers, but no ability to spawn subagents. It starts from the artifacts, cross-checks them against source, and fixes issues in place. Its job is correction, not generation.

Deterministic checks catch structural issues fast; the critic handles judgment calls that require reading comprehension. In the current implementation this is closer to an automated review loop than a hard CI gate, but it surfaces obvious drift and often corrects it before a human reads the artifacts.

## Phased execution for scale

Small codebases (10 or fewer programs) run in a single orchestrator session. Larger codebases use a five-phase pipeline:

**Phase 1: Cross-cutting analysis.** Inventory, data, flow, and integration workers run in parallel against the entire codebase, iterating until convergence. Deterministic validation and a critic pass follow. This produces the structural artifacts that establish the landscape: what programs exist, how they connect, what data they share.

**Phase 2: Per-program business rules.** Programs are processed in parallel batches (default batch size of 3). Each program gets its own convergence loop running only the business-rules worker. Large programs use the chunked analysis path. State is tracked per-program, enabling resume if the run is interrupted.

**Phase 3: Requirements synthesis.** A requirements-deriver agent reads the generated artifacts, updates the application overview (`application.md`), and synthesizes:

- **Functional capabilities**: what the application actually does, traced back to specific programs and business rules
- **Non-functional requirements**: error handling patterns, data integrity mechanisms, performance characteristics, security controls - all observed in the source code, not assumed
- **Modernization notes**: complexity assessment, technical debt, decomposition candidates, data migration considerations

**Phase 4: Test specification synthesis.** A test-specs-deriver agent reads the capabilities, business rules, data dictionary, and flow artifacts to produce stack-agnostic behavioral test specifications. Tests are organized by business capability - not by COBOL program - so the modernized system is free to decompose differently while still proving behavioral equivalence. The output includes scenario tables, data contract tests for migration coexistence, and a traceability matrix linking every test back to its source rules.

**Phase 5: Implementation plan.** An implementation-plan-deriver agent reads the capabilities, dependency graph, integration analysis, and modernization notes to produce a phased migration plan. Rather than assuming a single migration approach, the agent evaluates the codebase against five strategies -- strangler fig, rewrite, branch-by-abstraction, parallel run, and pipeline replacement -- and selects the best fit (or a hybrid) based on scale, coupling, online/batch mix, regulatory profile, and natural boundary availability.

This phased approach enforces dependency ordering. Capabilities depend on business rules, test specifications depend on capabilities, and migration planning depends on all of the above. Deterministic orchestration handles that sequencing; agents never decide what phase comes next.

## Convergence loops: closing the gaps

Within each phase, the orchestrator doesn't just run workers once and move on. It runs them in a convergence loop. Each iteration records new findings and the artifacts written or updated. If an iteration produces new discoveries, the next run gets that updated context and focuses on filling gaps rather than regenerating from scratch. When consecutive iterations produce no new discoveries, the loop declares convergence and stops. A configurable ceiling (default: 5 iterations) prevents runaway loops.

Single-pass analysis sounds efficient, but it consistently leaves gaps. A first pass might document 47 of 50 copybooks or miss a batch-only edge case buried in one program's business rules. Convergence loops treat those omissions as fixable rather than acceptable.

Convergence loops are complementary to the critic pass, not a replacement. Convergence loops give the phase's own specialized workers a chance to self-correct before the critic runs. The critic catches errors of interpretation. Convergence loops catch errors of omission.

The cost of convergence is bounded by an early-exit parameter (`n_stable`, default: 2), so phases usually stop after one confirmation pass rather than running to the maximum iteration count.

## From legacy code to implementation inputs

This is where the output format matters. The reverse engineering tool produces structured markdown with machine-readable frontmatter. Downstream requirements, planning, or code-generation steps can consume that directly. The output is designed to bridge the gap between legacy code and implementation work.

Consider a functional capability extracted from a COBOL batch processing system:

```yaml
---
type: requirements
subtype: capabilities
status: draft
confidence: medium
---

# Functional Capabilities

## Capabilities

### Daily Account Processing

| Property | Value |
|-----|----|
| Description | End-of-day batch cycle that applies transactions, calculates interest, updates balances, and produces regulatory reports |
| Source Programs | CBACT01C, CBACT02C, CBACT03C |
| Input | ACCTFILE (account master), TRANFILE (daily transactions) |
| Output | ACTRPT (activity report), REGFILE (regulatory extract) |
| Business Rules | Account status validation, interest calculation, balance update sequencing |
| Data Entities | ACCT-RECORD, TRAN-RECORD, RPT-RECORD |
```

This artifact describes a capability in language a product team can understand, but with full traceability back to specific programs, files, and rules. A downstream requirements step can read it and produce a properly structured requirement:

```yaml
---
id: REQ-001
title: "Daily Account Processing"
status: draft
source: legacy/capabilities.md#daily-account-processing
---

## Description
System must execute an end-of-day batch cycle that applies daily transactions
to account balances, calculates accrued interest, and produces activity
and regulatory reports.

## Acceptance Criteria
- [ ] All pending transactions are applied in sequence
- [ ] Interest is calculated using the daily rate formula (balance * rate / 365)
- [ ] Accounts with status 'C' (closed) are excluded from processing
- [ ] Negative balance accounts are flagged for review
- [ ] Activity report includes all processed and rejected transactions
- [ ] Regulatory extract matches the format specified in REGFILE copybook
```

The `source` field traces back to the legacy capability. The acceptance criteria are derived from the business rules the reverse engineering tool extracted. The non-functional requirements artifact captures error handling patterns and data integrity mechanisms that a rewrite needs to preserve. The modernization notes identify which programs are decomposition candidates and what the data migration risks are.

Instead of starting from interviews and workshops, teams start from artifacts derived from what the system actually does, not what someone remembers it doing. SMEs and engineers still need to review them — agents miss nuance, and organizational context isn't in the source code — but the starting point is dramatically better than a blank page.

## From business rules to test specifications

Requirements tell you what to build. The question every stakeholder asks during legacy modernization is how you prove the new system does the same thing as the old one.

The extracted business rules are not just requirements input. They're a **test oracle**. Every rule in those tables has a condition and an action - and that's a test case waiting to be written.

Consider a business rule extracted from an account display program:

| #   | Rule                 | Condition                | Action                                   | Source Rules |
| --- | -------------------- | ------------------------ | ---------------------------------------- | ------------ |
| 1   | Account status check | Account status is Closed | Skip processing, return error indication | BR-002       |

That immediately yields at least two test scenarios:

| #   | Scenario                 | Category   | Preconditions                 | Input                | Expected Output              | Source Rules |
| --- | ------------------------ | ---------- | ----------------------------- | -------------------- | ---------------------------- | ------------ |
| 1   | Active account processed | happy-path | Account exists, status Active | Valid account number | Account details returned     | BR-001       |
| 2   | Closed account rejected  | error      | Account exists, status Closed | Valid account number | Error: account not available | BR-002       |

Notice what's absent: no COBOL paragraph names, no variable names, no `EVALUATE` statements. The test describes what the system does in business terms - account status, not `ACCT-STAT-CD`. Any implementation that passes this test preserves the legacy behavior, regardless of language, architecture, or internal decomposition.

This is the anti-JOBOL principle applied to testing. "JOBOL" - writing Java (or Python, or Go) that mirrors COBOL's structure line by line - is a common failure mode in legacy modernization. The same trap exists for tests: if you organize cases by COBOL program and paragraph, you encode the legacy decomposition into the suite and pressure the new system to mirror it. Tests organized by **business capability** avoid that. The modernized system can have a completely different internal structure and still pass every test.

### Three test artifacts, three audiences

The tool produces three test specification artifacts, each serving a different purpose:

**Behavioral test specifications** organize scenarios by business capability - the same capabilities identified in Phase 3. For each capability, the agent derives happy-path, error, and boundary scenarios from the business rules, using field definitions from the data dictionary to determine equivalence classes and boundary values. A `PIC S9(10)V99` field tells you the valid range; the agent generates tests at zero, the minimum, the maximum, and the boundaries between equivalence classes.

**Data contract tests** define invariants for each data store - files, database tables, message queues. These are essential during the coexistence period when old and new systems run in parallel. The legacy system writes VSAM records with specific layouts and key structures. The modernized system might use a relational database. Data contract tests verify that the semantics are preserved regardless of storage technology: keys are unique, status fields contain only valid values, referential integrity holds across stores.

**The equivalence matrix** provides traceability from each test scenario back to specific business rules, source programs, and COBOL paragraphs. This is the only place COBOL-specific references appear. The matrix serves auditors and SMEs who need to verify coverage: every business rule should trace to at least one test, and rules without tests should be explicitly flagged with a reason. The matrix is a reference document, not a test design document. It answers "where did this test come from?" without dictating how the test is structured.

### Stack-agnostic by design

None of these specifications reference a target language, framework, or testing tool. They describe behavior in business-domain terms with structured tables that any test generation tool can consume. A team modernizing to Java microservices can derive JUnit tests from the same specifications that a team modernizing to Python services uses to produce pytest tests. The specifications are the contract; implementation is a downstream concern.

These test specifications are another set of machine-readable artifacts that downstream tooling can consume without assumptions about the final target.

## State persistence and resumability

Legacy analysis runs can take hours for large codebases. The tool persists state after every iteration - discoveries, artifacts written, completion status - as JSON files. A `--resume` flag picks up where a killed or failed run left off:

- Completed phases are skipped entirely
- Completed programs within a phase are skipped
- Incomplete chunks within a program resume from the last unfinished chunk

This is operationally important. Large COBOL applications might have 200+ programs. Processing them all takes multiple hours of LLM compute. Network timeouts, rate limits, and model errors are inevitable at that scale. Without resumability, every failure means starting over. With it, failures cost minutes, not hours.

## What we've learned

The public examples in this repo are CardDemo and CBSA. We've also used similar reverse-engineering workflows across CICS, IMS, DB2, VSAM, and MQ environments, and this tool codifies the patterns that held up across them. There will still be COBOL conventions and organizational idioms it doesn't handle well yet, so take these as observations from the field rather than universal truths.

### Where it still breaks down

This is not zero-touch reverse engineering. Business intent that lives in people's heads, runbooks, ticket history, or regulator conversations will not appear in the output because it is not in the source. Open-source sample apps are also cleaner than many real-world estates: fewer local conventions, fewer environment-specific jobs, and less entropy from decades of patches.

Even in the happy path, first-pass artifacts are usually incomplete or partly wrong. That's why the workflow has convergence loops, a critic pass, and a human review step. The goal is a much better first draft, not blind trust.

### The 80/20 split between deterministic and interpretive work

The most useful design decision was drawing the line between what Python does and what agents do. Structural parsing — divisions, paragraphs, chunking, fact extraction, call graphs — is deterministic. It's fast, reliable, and reproducible. Agents would get this wrong often enough to be unusable.

Semantic interpretation — what does this paragraph do? What business rule does this `EVALUATE` encode? Why does this program call that one? — requires reading comprehension that regex can't provide. Agents are good at this when given bounded, well-structured inputs.

The temptation is to let agents do everything. Every task that can be deterministic probably should be. Agents should only handle work that genuinely requires judgment.

### Templates enforce consistency more than instructions do

Early versions used detailed prose instructions telling agents what sections to include and what format to use. Agents followed them most of the time. Occasionally they'd invent their own section headers, skip sections they deemed irrelevant, or restructure the output in creative but unhelpful ways.

Embedding the actual template - frontmatter schema, section headers, table structures - in the prompt eliminated this. Agents fill in a structure rather than invent one. They're dramatically more reliable when completing a template than when writing from scratch.

### The critic is the highest-leverage component

Of all the components, the critic pass produces the most improvement per token spent. First-pass artifacts from workers are typically 70-80% accurate. That still leaves 20-30% needing correction, which is too much if humans have to clean it up manually. The critic, with explicit instructions to cross-reference claims against source code using file reads and code search, catches most of the remaining issues: missed programs, incorrect classifications, incomplete call graphs, wrong file I/O directions. Human review is still needed, but the critic significantly reduces how much of it.

Generating content is relatively easy. Validating it against ground truth is where quality comes from.

### Platform-agnostic design pays for itself

COBOL ecosystems vary enormously: CICS, IMS, batch-only, DB2, VSAM, MQ, or any combination. Variable naming conventions differ across organizations. Transaction ID patterns differ. File I/O styles differ. Early versions of the tool were tuned for a specific application and broke immediately on others.

Making the tool platform-agnostic - broad regex patterns, generic field names, no hardcoded assumptions about specific middleware - required more upfront work but made it deployable across codebases without modification. The same principle applies to any reusable workflow: encode patterns, not instances.

## Practical takeaways

- **Invest in deterministic parsing before agent work.** The quality of agent output is directly proportional to the quality of structural context they receive. A well-parsed manifest with accurate paragraph classification and fact extraction makes agent prompts shorter, more focused, and more reliable.
- **Design output formats for machine consumption.** If the reverse engineering output will feed downstream tooling, its format matters more than its prose quality. YAML frontmatter with consistent field names is more valuable than beautifully written paragraphs that require natural language processing to extract structure from.
- **Build resume into everything.** Any workflow that takes more than ten minutes to run will eventually fail partway through. State persistence and idempotent resume aren't nice-to-haves. They're requirements.
- **Derive tests at the capability level, not the program level.** If your test suite mirrors COBOL's program-and-paragraph decomposition, you've encoded the legacy structure into your verification strategy. Organize tests by business capability so the target system can decompose differently while still proving equivalence.
- **Start with automated reverse engineering, then use workshops to validate it.** The tool produces artifacts that SMEs can review and correct, rather than asking them to recreate logic from memory over months.
- **Budget for the full pipeline.** Reverse engineering isn't a one-off consulting phase. It's the front end of a repeatable delivery pipeline. The same structured specifications that describe the legacy system can become the requirements that drive the new one.
- **Measure coverage, not just accuracy.** A reverse engineering pass that accurately documents 80% of programs is more valuable than one that perfectly documents 20%. Coverage gaps are visible and addressable. Unknown unknowns are not.
- **Use test specifications to build confidence in the rewrite.** The biggest risk in legacy modernization isn't the rewrite itself — it's proving the new system does the same thing. Machine-derived test specifications, traced back to extracted business rules, give stakeholders a concrete verification strategy rather than a leap of faith.

## Bottom line

If you want to modernize a legacy system, you need artifacts that describe what the existing system actually does, traced back to the source code that implements it.

This reverse-engineering workflow can provide that first draft. It doesn't remove the need for human review, but it changes the starting point: instead of workshops and blank documents, teams begin with machine-readable requirements, business rules, test specs, and a concrete basis for migration planning.

---

_By [Daniel Sheard](https://www.linkedin.com/in/danielsheard/) and [Dave Kerr](https://uk.linkedin.com/in/dwmkerr). Companion piece to [Agentic workflows for software development](https://medium.com/quantumblack/agentic-workflows-for-software-development-dc8e64f4a79d), which describes one downstream delivery pipeline that can consume the specifications this tool produces._
