# Policy-growth demonstration protocol

Use this only when the user asks for a growth/scalability demo. Keep fictional policies visibly separate from real company rules.

## Assemble the comparison

- Preserve an original snapshot; create an expanded snapshot from original records plus additions. Check collisions before combining. Store snapshots in a temporary or explicit experiment directory, not by silently rewriting the active catalogue.
- Use a small understandable addition pack first. For example, given a user-approved fictional rule “test ink over 30 ml is prohibited,” use equality, above-boundary and missing-volume cases plus a held-out paraphrase and a similar unrelated item.
- Reuse rule types the runtime supports. A new topic or operator is an implementation change, not evidence of adding data without code.
- Keep old unaffected cases frozen. Add newly covered cases, cross-policy interactions and near-neighbour/no-match cases. New-item answers before additions should acknowledge insufficient policy evidence, not claim definitive acceptance.
- For different quantities on multiple items, do not assign one global quantity to every item. The current extractor cannot bind them reliably; expect clarification or identify the needed implementation work.

## Snapshot assembly example

Use actual requested pack/output paths. This example uses the existing fixture; select a fresh output directory rather than deleting or overwriting a previous experiment. Run from the repo environment with `uv run python` through the available shell/tool.

```python
import json
from pathlib import Path
from agent.policies import load_policies

base = load_policies("agent/data/policies.json")
added = load_policies("evals/fixtures/policy_additions.json")
assert not ({p["id"] for p in base} & {p["id"] for p in added})
out = Path(".cache/policy-growth/trial-001")
out.mkdir(parents=True, exist_ok=False)
for name, records in [("original", base), ("expanded", base + added)]:
    (out / (name + ".json")).write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
```

The standard search demo reads fixed catalogue/fixture paths. For a different assembled snapshot, use the existing store API rather than pretending the demo has an arbitrary-pack CLI option:

```python
from agent.policies import PolicyStore, load_policies
records = load_policies(out / "expanded.json")
store = PolicyStore(records)  # Offline keyword/alias retrieval.
```

Only for an authorised live semantic run, replace that last line with:

```python
from agent.policies import configured_store
store = configured_store(
    index_path=out / "semantic.json", records=records, require_semantic=True
)
```

Call `store.search_with_scores(query, topic)` with the held-out queries to collect candidates. Inspect selected-policy correctness separately from oracle rule tests. Do not pass snapshot records with embedded tests directly to an answering model; use `runtime_policy` projections.

## Measure the intended capability

Run the entire cheap rule/retrieval suite to find interference with old policies. Select live tests by relevant policy IDs plus a fixed critical regression set. Run live models only when requested/configured; otherwise provide exact commands for the teammate machine.

Report separately:

- Original/expanded record counts and number of added test cases.
- Old-case regressions and newly covered correctness.
- Recall@5 / complete expected-policy coverage, false prohibitions and unknown-case handling.
- Index update time, records re-embedded, query latency and context size where measured.
- Model input/output tokens and costs only if instrumentation captures them. Mark missing data unknown.

A 10/100/1,000-record test needs realistic confusing neighbours, not just irrelevant random filler. Synthetic data validates a synthetic workload. Do not say “semantic” when only aliases or fake vectors ran. Do not say “pipeline accuracy” for oracle rule checks against the known correct policy.

## Full-context comparison

If the user asks for all-context versus workflow, inspect whether the experiment driver exists. Do not invent a command or fabricate measurements. Share answering model, question IDs, policy snapshot, permissions, output budgets and blinded scoring. Include classifier/embedding overhead for the workflow. Keep full-context capacity errors visible instead of truncating silently. The proposed experiment and pending instrumentation are documented in `docs/evaluation-benchmark.md`.

## Demo handoff

Provide the source policy pack, reviewed or review-pending expectations, snapshot assembly instructions, commands and a short sequence the presenter can rehearse. Expected outcomes are not measured results. Leave unrelated user changes untouched. Publication to the team repo follows session authorisation, not this skill alone.
