# Parcel Pigeon: policy controller and evaluation demo

A workshop prototype for testing a customer-support agent against a growing policy catalogue. It combines input classification, protected order tools, policy retrieval, deterministic decisions, bounded answer repair and offline evaluations.

**Start here:** [Teammate setup](README-TEAMMATE.md) · [Semantic demo walkthrough](docs/semantic-demo.md) · [Metrics and comparison design](docs/evaluation-benchmark.md).

## Current implementation and evidence

The implementation is on **[PR #1](https://github.com/tishayaem/friendly-meetup-hackathon/pull/1)**, branch `N-Bhar:codex/policy-evaluation-team-pr`. At the latest source review, the team repository's default branch still had the original keyword-only agent. Until the PR merges, check out its branch rather than assuming a clone of the default branch includes these features.

From a clone with GitHub CLI available:

```sh
gh pr checkout 1 --repo tishayaem/friendly-meetup-hackathon
```

| Component | Status |
|---|---|
| Input classifier | Implemented: harmful/injection signals, relevance, intent and topics |
| Policy search | Implemented: keyword/aliases plus optional embedding similarity and score traces |
| Rule decisions | Implemented for supported prohibited-item conditions and refund decisions |
| Order tools | Implemented: session/order authorisation and private-field filtering |
| Verification | Implemented as a local simulated-code demo; not real identity proof |
| Answer generation | Implemented: controlled tools, bounded output checks, one repair attempt |
| AI judge | Implemented: validated 1–5 score and reason; human calibration still needed |
| Search showcase | Implemented: lexical/semantic rankings, original/expanded policy snapshots, saved traces |
| Full-context A/B comparison | Specified, **not implemented** |
| Detailed latency/token/cost accounting | Partial; see implementation backlog below |

Latest verified evidence:

- **81 offline tests passed.** Mock embeddings test integration only, not semantic quality.
- **30 live agent-evaluation cases** are present; this is a case count, not a passing live score.
- **15 active policies**, with three fictional additions isolated in the search demo's expanded snapshot.
- The offline lexical search showcase retrieved all expected policies in **12/16 positive checks**, across 24 original/expanded query records. No-applicable-rule cases require manual review and are not counted as automatic passes.
- A complete live agent/judge evaluation and real embedding-quality evaluation have **not** been established on the development machine. Run those on the teammate machine and retain the results.

## What remains to implement

### Before relying on the demo or benchmark results

| Priority | Work | Completion evidence |
|---|---|---|
| P0 | Fix `evals/stages.py`: the report emits `oracle_rule_accuracy`, but the final check reads `rule_accuracy` | Both lexical and semantic benchmark CLI paths complete without `KeyError`; add a regression test |
| P0 | Configure and verify the teammate's actual embedding, classifier, agent and judge models | Embedding preflight plus one inspected classified/answered/judged case succeed |
| P0 | Run and review the live retrieval showcase and full agent suite | Saved results, failures explained, several judge verdicts manually checked |
| P1 | Improve ambiguous/multiple-item fact extraction | Separate quantities bind to the correct items; unknown facts trigger clarification |
| P1 | Validate semantic applicability and relevance behaviour | Held-out synonyms and confusing neighbours tested; similarity alone cannot establish prohibition |
| P1 | Review unresolved business-policy boundaries | Agreed fractional-weight pricing, applicable holiday calendar/counting and any missing claim rules, with boundary tests |

**Known command blocker:** `uv run python -m evals.stages` and `--semantic` can currently fail after printing the first row because of the metric-key mismatch above. This README update does not change that code. Use the separate `agent.search_demo --showcase` command for the current retrieval demonstration. Its retrieval score is not a substitute for agent-answer accuracy.

### To deliver the full-context-versus-workflow experiment

- [ ] Implement the all-policies-in-context baseline using the same answering model, authorisation boundaries and generation limits.
- [ ] Add a paired experiment driver with immutable original/expanded policy snapshots, held-out queries, repeats and recorded run order.
- [ ] Track input/output tokens, model IDs, durations, errors and attempts for **every** classifier, answering and embedding call. Track judge calls separately.
- [ ] Aggregate **all conversation turns**. The current evaluation runner retains final-turn usage, so it cannot yet report complete conversation costs or latency.
- [ ] Add dated model-pricing configuration. Unknown costs remain unknown; local API spend does not measure hardware cost.
- [ ] Add independent structured assessments for decision correctness, unsupported claims, useful answers and critical violations. The current overall judge score does not measure claim-level hallucination rate.
- [ ] Produce the four-cell report: full context/workflow, before/after additions. Keep old-case regressions separate from newly answerable cases.
- [ ] Human-review judge disagreements and all alleged critical violations. No weighted average should hide a privacy failure.

The complete definitions, controls, proposed thresholds and demonstration budget are in [the evaluation specification](docs/evaluation-benchmark.md). A smaller input context is not by itself proof of higher accuracy, lower latency or lower total cost.

### Beyond this workshop prototype

Real purchaser authentication, a secure verification interface, production storage, arbitrary prose-to-rule compilation and production-scale retrieval infrastructure remain outside the current demo. The classifier has a fixed topic vocabulary; new topics require routing changes. Current rule operators support `eq`/`gt` conjunctions, and only the initial supported fact types have extractors. Output checks cannot guarantee detection of every hallucination or partial disclosure.

## Run it on the teammate machine

Run commands from the repository root. Install Git, [uv](https://docs.astral.sh/uv/) and Python 3.11+. uv can install Python. Live models can use native Ollama, the supplied Docker Compose service, or compatible hosted endpoints. **Docker and a GPU are not required for offline tests.**

### 1. Dependencies and offline checks

```sh
uv python install 3.13
uv sync --python 3.13 --locked
uv run pytest -q
uv run python -m agent.policies
uv run python -m agent.search_demo --mode lexical --check
```

These commands do not call live models. The catalogue preparation above builds a lexical index. The full offline showcase can expose legitimate retrieval failures:

```sh
uv run python -m agent.search_demo --mode lexical --showcase --report results/lexical-showcase.jsonl
```

Choose a fresh report filename on subsequent runs. Exit 1 means at least one positive retrieval check failed; it does not necessarily mean setup failed.

### 2. Environment configuration

Create `.env` only if it does not exist. Do not overwrite working credentials.

PowerShell:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

macOS/Linux:

```sh
test -f .env || cp .env.example .env
```

| Role | Configure | Needed for |
|---|---|---|
| EMBEDDING | `EMBEDDING_BASE_URL`, `EMBEDDING_MODEL`, optional API key | Semantic search-only demo and semantic agent retrieval |
| CLASSIFIER | `CLASSIFIER_BASE_URL`, `CLASSIFIER_MODEL`, optional API key | Full agent and live classification evaluation |
| AGENT | `AGENT_BASE_URL`, `AGENT_MODEL`, optional API key | Generated full-agent responses and tool calling |
| JUDGE | `JUDGE_BASE_URL`, `JUDGE_MODEL`, optional API key | Offline answer evaluation; the general readiness checker also checks it |

For hosted services, use supported model IDs and your own keys. For local Ollama, leave keys blank. Never commit `.env`. Detailed provider setup is in [the teammate guide](README-TEAMMATE.md) and [provider notes](docs/providers.md).

### 3. Semantic search-only demo

Start native Ollama and install the embedding model:

```sh
ollama pull embeddinggemma
```

Set in `.env`:

```dotenv
EMBEDDING_BASE_URL=http://localhost:11434/v1
EMBEDDING_API_KEY=
EMBEDDING_MODEL=embeddinggemma
```

Then run:

```sh
uv run python -m agent.search_demo --check
uv run python -m agent.search_demo
```

This path needs only embeddings, not the three chat-model roles. It is a **terminal interface**: `http://localhost:11434/v1` is the model API address, not a website or chat UI. Missing embeddings fail explicitly; the semantic demo never silently switches to lexical mode.

Try `Can I ship paper money from my wallet?`, inspect candidates and score components, and select a rank to inspect a rule. Confirm applicability before evaluating supplied facts. Use `/expand` for the fictional 18-policy snapshot, `/reset` to return to 15 policies, and `/quit` to exit.

Record the fixed before/after queries:

```sh
uv run python -m agent.search_demo --showcase --report results/semantic-showcase.jsonl
```

Semantic and lexical indexes have separate cache files. First-time embedding preparation may take longer. Positive retrieval checks and unknown/no-match review cases are reported separately.

### 4. Full support-agent demo

Keep the embedding settings and configure CLASSIFIER/AGENT/JUDGE from `.env.example`. For its local defaults, install the two chat models:

```sh
ollama pull llama3.2:3b
ollama pull qwen2.5:7b
uv run python -m agent.demo --semantic --check
uv run python -m agent.demo --semantic
```

The classifier and agent share the first model; the judge uses the second. Compatibility and latency must be checked on the actual machine. To use Docker instead of native Ollama, follow [the teammate setup](README-TEAMMATE.md#option-b-docker-ollama), and also pull the embedding model inside that service.

Rehearse a prohibited-item query, an underspecified quantity, an order-status query with simulated verification, and a prohibited address-disclosure request. The code appears only in the tester-facing terminal and is entered at the dedicated prompt. Verification does not permit name/address/phone disclosure. Use complete questions: the demo retains the pending verification request, not general chat memory.

### 5. Live evaluations and reports

Start with a single case, then the suite:

```sh
uv run python -m evals.run --only price-next-day --label smoke
uv run python -m evals.stages --classifier
uv run python -m evals.run --label teammate-baseline
uv run python -m evals.run --only privacy-address --repeat 3 --label privacy-repeat
```

`evals.stages --classifier` uses a separate branch from the known broken retrieval-benchmark path. `--no-judge` on `evals.run` skips the judge but still calls the classifier and sometimes the answering model; it is **not offline mode**.

Use the actual filenames printed by completed runs:

```sh
uv run python -m evals.metrics results/RUN.jsonl
uv run python -m evals.compare results/BEFORE.jsonl results/AFTER.jsonl
```

Replace placeholders and retain the saved JSONL files. Results are ignored by Git, so share them explicitly. Missing measurement fields remain unknown in the summary. Preserve case expectations and judge configuration when claiming a fix. The paired full-context experiment is not available through these commands yet.

## Adding policies and relevant tests

1. Edit **`agent/data/policies.json`**, the executable source. Keep a stable ID, increment its version for changes, and provide topic, text, reviewed aliases and applicability as appropriate.
2. For a supported executable rule, add required facts/conditions and reviewed examples. Include boundaries, missing information, synonyms and confusing non-matches where relevant.
3. Add a held-out live case to `evals/cases.jsonl` when conversational behaviour changes. Do not derive expected answers solely from the same model/rule function being tested.
4. Run offline tests and prepare the index. Record-level tests are discovered automatically. For embeddings use `uv run python -m agent.policies --semantic`.
5. Run the retrieval showcase and relevant live cases. Review old-policy regressions as well as new coverage.

The search demo's `/expand` uses fixtures in memory and does not edit the active catalogue. The JSON/Markdown policy copies must be kept consistent for human readers; runtime retrieval reads JSON and excludes embedded test answers. See [the full extension example](docs/testing-demo.md#adding-a-policy-and-its-tests).

## Reusable policy/test authoring skill

The team-shareable skill is [`.agents/skills/policy-eval-author/SKILL.md`](.agents/skills/policy-eval-author/SKILL.md). It covers existing-policy test expansion, source-backed policy additions and isolated synthetic growth demos. A personal copy is installed on the development machine; teammates can use the repo copy or copy its folder to `~/.codex/skills/policy-eval-author`.

Example requests in a Codex chat:

```text
Use $policy-eval-author to add boundary and missing-information tests for the existing perfume rule without changing its meaning.

Use $policy-eval-author to prepare a fictional demo policy: screen-cleaning fluid over 45 ml is prohibited. Add source-derived tests and a held-out query, keeping the active catalogue unchanged.

Use $policy-eval-author to prepare original and expanded policy snapshots, new-case coverage and old-policy regression checks. Run offline checks only and leave live model commands for the teammate machine.
```

If the skill is not available by name in the current chat, ask the agent to read the repository's SKILL.md directly. The skill drafts cases from explicit policy text; independent review of the expectations is still necessary. It does not automatically invent or activate company rules, run live models, or publish changes.

A read-only helper validates a policy pack and its agreement with the current implementation:

```sh
uv run python .agents/skills/policy-eval-author/scripts/audit_policy_pack.py --repo . --pack evals/fixtures/policy_additions.json --baseline agent/data/policies.json
```

Add `--cases path/to/new-cases.jsonl` to check live-case structure and IDs against the existing suite. A successful audit does not make an isolated fixture part of the active catalogue, prove semantic accuracy or replace human review. Unsupported operators, new topics and missing extractors are reported as implementation gaps.

## Demo readiness checklist

- [ ] Teammate has the implementation branch and locked dependencies.
- [ ] Offline tests pass; actual embedding-query preflight succeeds.
- [ ] Classifier, answering model and judge have been smoke-tested where used.
- [ ] Original/expanded retrieval results are saved and manually inspected, including non-matches.
- [ ] Verification, refusal, clarification and fallback have been rehearsed.
- [ ] Live case results and judge disagreements are available; errors are not presented as passing answers.
- [ ] Any slide comparing full context with the workflow is labelled **planned** until the missing experiment driver and measurements exist.

## Further documentation

- [Teammate setup, providers and troubleshooting](README-TEAMMATE.md)
- [Semantic search demo and showcase](docs/semantic-demo.md)
- [Decision flow and policy boundaries](docs/decision-flow.md)
- [Policy extension and implementation limits](docs/testing-demo.md)
- [Metrics, acceptance criteria and A/B design](docs/evaluation-benchmark.md)

<details>
<summary>Original workshop brief (historical starter instructions)</summary>

The following describes the original exercise. TODOs such as implementing the tool-use check and judge have already been completed in this PR. Use the current instructions above to run the implemented version.

## 🎯 What you'll build

- A **test set** of customer questions
- **Automatic checks** and an **AI judge** that grade every answer
- A **before/after scorecard** showing that your fix worked

## ⚙️ Setup (10 min)

You need: [Docker](https://docs.docker.com/get-docker/) and [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
cp .env.example .env
docker compose up -d                                   # starts local LLMs
docker compose exec ollama ollama pull llama3.2:3b     # the agent (2 GB)
docker compose exec ollama ollama pull qwen2.5:7b      # the judge (5 GB)
uv run python -m agent.agent "How much is Next Day delivery?"
```

✅ You should see an answer mentioning **£6.50**.

💡 Using a hosted model (OpenAI, Gemini, Mistral…) instead? See [docs/providers.md](docs/providers.md).

## 🪜 The challenge

| Level | Goal | Time |
|---|---|---|
| 1 | Meet the agent | 15 min |
| 2 | Write the tests | 45 min |
| 3 | Build the judge | 30 min |
| 4 | Fix it and prove it | 30 min |
| ⭐ | Bonus | Any time left |

### Level 1: Meet the agent

1. Skim [agent/data/policies.md](agent/data/policies.md). This is what the bot should know.
2. Ask it a few questions with `uv run python -m agent.agent "..."`
3. Run the starter tests:
   ```bash
   uv run python -m evals.run --label baseline
   ```

✅ **Done when:** you see a scorecard. (➖ means "not scored yet". You'll fix that next.)

### Level 2: Write the tests

1. In [evals/checks.py](evals/checks.py), implement `tool_called`.
2. Add **at least one check of your own** (ideas in the file).
3. Add **15+ cases** to [evals/cases.jsonl](evals/cases.jsonl) → [how to write good cases](docs/writing-cases.md)

✅ **Done when:** 20+ cases, and no ➖ in the Checks column.

### Level 3: Build the judge

1. Complete the TODO in [evals/judge.py](evals/judge.py). The rubric is in [evals/rubric.md](evals/rubric.md).
2. Run the full suite again.
3. Read 3–4 of the judge's reasons in `results/`. Do you agree?
4. Is one score enough? A customer, a support manager and a lawyer would each judge the same answer differently. Pick the perspectives that matter to you (readability is one) and decide how to measure each: a check, the judge, or a number. There's no single right set, so be creative.

✅ **Done when:** every case with an `expected` field gets a score.

### Level 4: Fix it and prove it

1. Pick a failure. Change **one thing**: the [system prompt](agent/system_prompt.md), a [tool](agent/tools.py), or the model.
2. Re-run and compare:
   ```bash
   uv run python -m evals.run --label fix-1
   uv run python -m evals.compare results/<baseline>.jsonl results/<fix-1>.jsonl
   ```

💡 Watch for fixes that break something else. And not every fix belongs in the prompt.

✅ **Done when:** the comparison shows at least one 🟢 fixed and no 🔴 broke.

### ⭐ Bonus

Tracing, judge accuracy, model shoot-outs, red-teaming → [docs/stretch.md](docs/stretch.md)

## 🎤 Demo (3 min)

- Your scorecard **before and after**
- One **interesting failure**, and why it happened
- **Do you trust your judge?** Why or why not?
- **Which metrics did you choose**, and what did each one reveal?

## 🗂️ Project map

```
agent/                  the bot you're testing
├── agent.py            agent loop (no need to edit)
├── system_prompt.md    its instructions ← edit in Level 4
├── tools.py            get_order, search_policies
└── data/               policies + orders (the "truth")
evals/                  your work happens here
├── cases.jsonl         test cases ← Level 2
├── checks.py           deterministic checks ← Level 2
├── judge.py            LLM judge ← Level 3
├── rubric.md           judge's marking scheme
├── run.py              runs everything → results/
└── compare.py          before vs after
docs/                   short guides
results/                saved runs (one file per run)
```

## 🆘 Stuck?

| Problem | Try |
|---|---|
| Connection error | `docker compose ps` (is Ollama running?) and check `.env` |
| Too slow | `--only <case-id>`, `--no-judge`, or a hosted model |
| Model ignores tools | Normal for small models! That's a finding: put it in a test. |
| Anything else | Grab an organiser 🙋 |

</details>
