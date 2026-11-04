# Repository contracts

Treat these as the current integration points, not a substitute for inspecting source.

## Policy record

The runtime catalogue is `agent/data/policies.json`, a JSON array. A record needs `id`, positive integer `version`, `topic`, `text`, `aliases` (strings), `active` (boolean), and `tests` (array). The current catalogue has one record per policy ID; duplicate IDs are rejected even for inactive versions. Increment a version when changing the current record's meaning. Keep human-readable policy documents consistent when updating the actual business rules.

Executable prohibited-item rules have `outcome: "prohibited"`, optional `required` fact names, and `conditions` with `field`, `op`, `value`. Conditions are ANDed. Current operators: `gt` for numeric thresholds and `eq` for exact typed values. Conditional fields must be required. The current request extractor knows `volume_ml` and `standalone`. A new numeric fact name can pass the generic evaluator but is not automatically extractable from customer questions.

Existing topics are the classifier's fixed TOPICS set. A new topic requires routing work; creating JSON alone does not do it. General text records can have no `rule`; do not invent executable conditions for them.

## Embedded examples

Each entry: `{"query":"...", "facts":{...}, "expected":"..."}`.

For a supplied rule “fictional test ink over 30 ml is prohibited”:

- Facts `{"volume_ml":30}`: `not_prohibited_by_rule` because “over” excludes equality.
- Facts `{"volume_ml":31}`: `prohibited`.
- Facts `{}`: `needs_information`.

The query must state facts consistently with the fact object. These outcomes are derived from the supplied sentence before invoking code. Add below-boundary cases where they detect a distinct issue.

`tests/test_pipeline.py` currently discovers examples from the active catalogue, requires the owning policy in the lexical top five, then checks the rule outcome. This does not automatically evaluate every isolated fixture file or semantic model. If adding a pure semantic held-out query that lexical search misses, place it in a semantic retrieval dataset rather than silently forcing a lexical test to pass.

## Live cases

`evals/cases.jsonl` has one case per line: `id`, `input`, `expected` (plain language), `checks` (array of type/value), `tags`. Supported check names come from `evals/checks.py`. Optional `classification` has expected route/intent/harmful/injection labels. `context.verified_order` is a trusted evaluation fixture, not user-supplied verification. Optional `steps` supports self-contained customer inputs and test-driver verification events.

Only use `outcome` checks for exact controller values verified in code. A rule's `prohibited` outcome can appear inside `result.decisions` while the outer controller outcome is `policy_decision`; do not conflate them. For prose refusals/clarifications, avoid brittle exact-word matching.

Use existing judge-independent checks for policy IDs, calls and permissions, and a plain expected behaviour for the judge. A passing judge never overrides a hard failure. Unknown checks fail validation. New case IDs must be unique relative to existing cases, not just within the new pack. The current suite has an exact 30-case count assertion: a legitimate expansion must update that count or replace it with a justified coverage minimum while preserving existing cases and behaviour checks.

## Retrieval and growth datasets

`evals/fixtures/retrieval_demo.json` is an array of `id`, `query`, `topic`, `expected_original` and `expected_expanded` policy-ID lists. An empty list means manual review/no applicable explicit rule, not automatic allowance or a scored success. Original and expanded expectations may differ when a rule is newly added.

`evals/fixtures/policy_additions.json` contains the existing fictional additions. The `/expand` demo loads this predefined fixture; arbitrary new packs do not become active merely because a skill generated them. Use an explicit snapshot assembly or update the intended demo fixture in scope.

Runtime policy projection excludes `tests`. Do not move gold labels into policy `text`, aliases, prompts or tool descriptions. Semantic retrieval is candidate ranking; item applicability and condition checks are separate.
