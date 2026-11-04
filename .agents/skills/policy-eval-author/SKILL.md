---
name: policy-eval-author
description: Add or revise Parcel Pigeon policies and source-grounded test cases, or prepare isolated policy-growth demonstrations in this evaluation repository. Use for policy authoring, boundary coverage and scalability fixtures; not for answering customer support questions.
---

# Policy evaluation author

Produce policy data and independently checkable expectations that work with the repository's actual evaluators. Default to offline work. A policy addition is not permission to change business rules, run costly live models, or publish a PR.

## Ground in the checked-out implementation

Find the repository root and read local AGENTS.md instructions. Inspect `agent/policies.py`, the target policy records, the relevant tests and eval schemas, and `README.md` known blockers. Do not assume the GitHub default branch contains the implementation: work on the user's current branch without switching it automatically.

Read [repository contracts](references/repository-contracts.md) before authoring data. Recheck those contracts against code; report unsupported operators, facts or topics rather than silently expanding the product. Ask for a missing business decision only when it materially changes the expected outcome; continue independent test design meanwhile.

## Choose the requested task

- **Tests for existing policies:** derive outcomes from the current authoritative policy, add missing boundaries and held-out conversational cases, and preserve policy meaning.
- **Add/update a real policy:** use the user's supplied rule or approved source. Add a unique ID/versioned record or increment a changed record's version. Include reviewed aliases, conditions supported by the engine and relevant examples. Preserve unrelated policies. Do not activate an invented policy.
- **Scalability demonstration:** read [growth protocol](references/growth-protocol.md). Put explicitly fictional additions in a separate fixture pack or assembled snapshot. Keep the live catalogue unchanged unless the user requests activation. Prefer rules using existing operators/fact extractors so the demo demonstrates data-driven extension.

## Author meaningful expectations

For each rule, cover applicable behaviour and any relevant threshold/equality, missing information, synonym, non-match and interaction cases. Choose coverage from the rule's actual risks rather than forcing a fixed test count.

- Record the supporting policy ID/version and a brief derivation for new expectations in the task report or case metadata outside runtime evidence.
- Derive expected outcomes from policy language and explicit facts, not from the answering model or the evaluator's returned output. Running the evaluator afterwards checks agreement with the written expectation; it does not establish the expectation's truth.
- Distinguish `not_prohibited_by_rule` from general acceptance. No matching policy means insufficient evidence, not permission.
- Embedded rule examples currently require retrieving their owner policy. Put unrelated-item and no-match expectations in separate retrieval/conversation cases or targeted Python tests, not in that embedded positive-retrieval format.
- Keep missing facts genuinely absent. Do not supply invented quantities, identity, holidays or claim evidence to make a test pass.
- Keep development examples and evaluation gold out of model context. Add at least one held-out phrasing when testing model generalisation; do not copy that phrasing into aliases just to improve retrieval scores.
- Say which expectations are policy-derived and which still need independent human review. Never label generated cases as human-reviewed unless that review occurred. Do not weaken an expectation merely because the current implementation fails it.

For general prose policies without an executable rule, use a natural-language expected behaviour and appropriate checks/judge reference. Do not pretend the initial prohibited-item rule vocabulary can execute refunds, calendars or arbitrary prose.

## Validate and deliver

1. Validate the pack with this skill's read-only audit helper, executed from the repo environment:
   `uv run python <absolute-skill-path>/scripts/audit_policy_pack.py --repo <repo-root> --pack <pack.json>`
   For isolated additions, use `--baseline agent/data/policies.json`; append `--cases <new-cases.jsonl>` when validating live cases. Relative paths resolve against `--repo`.
2. Run relevant offline tests. The helper validates an isolated pack but does not make the existing pytest parametrisation discover it; add a targeted test or assemble it in a temporary workspace. Run the cheap regression suite where appropriate.
3. Do not run the known broken retrieval branch of `evals.stages` without checking/fixing its metric-key mismatch. Use supported demo commands when relevant. Live semantic runs require configured actual embeddings; mocked vectors only verify plumbing.
4. If a supplied rule needs a new operator, topic or extractor, make that limitation explicit. Add implementation only when within the user's requested scope, with targeted tests.
5. Report changed files, policy/test counts, expected-outcome provenance, tests executed, unresolved ambiguities and an exact command/example invocation. Distinguish implemented behaviour, expected behaviour and measured performance. Do not claim a scalability gain from larger record counts alone.

Do not commit or push solely because this skill was invoked. Follow the user's existing authorisation for those actions. Do not overwrite an existing report or an unrelated policy pack. Do not require approval for routine reversible edits that the user has already requested.
