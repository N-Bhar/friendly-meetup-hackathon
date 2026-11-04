# Working semantic policy-search demo

Run this on the teammate machine. No local live inference was used to validate these changes. The test suite uses explicit fake vectors to verify integration, not to claim model quality.

## What you can demonstrate

- A real embedding endpoint retrieves candidate policies from unfamiliar wording.
- Keyword/alias and semantic scores appear side by side, so an alias hit is not misrepresented as a semantic discovery.
- Selecting a candidate and explicitly confirming its applicability runs the deterministic rule with supplied facts.
- `/expand` adds three fictional benchmark policies in memory; `/reset` restores the original snapshot. Neither changes the company's policy file.
- A fixed 12-query showcase runs before and after the additions and saves 24 trace records.
- The full support-agent demo can require semantic retrieval too, with its classifier, permissions and verification flow.

This is a terminal demo, not a web server. `http://localhost:11434/v1` is a model API address, not the demo UI. Start the demo from a terminal at the repository root.

## 1. Install dependencies

```sh
uv sync --locked
```

Create `.env` from `.env.example` if it does not exist. Preserve existing keys and settings. For Windows PowerShell:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

## 2. Prepare a real embedding model

For native Ollama, start its server and download an embedding-capable model:

```sh
ollama pull embeddinggemma
```

For Docker Ollama, use this instead:

```sh
docker compose up -d ollama
docker compose exec ollama ollama pull embeddinggemma
```

Set these fields in `.env`:

```dotenv
EMBEDDING_BASE_URL=http://localhost:11434/v1
EMBEDDING_API_KEY=
EMBEDDING_MODEL=embeddinggemma
```

An alternative OpenAI-compatible embedding endpoint works too; supply its real model ID and key. A chat-only model is not an embedding model. Ollama documents [embedding generation](https://github.com/ollama/ollama/blob/main/docs/capabilities/embeddings.mdx) and its [OpenAI-compatible embeddings endpoint](https://ollama.com/blog/embedding-models).

The search-only demo needs **only the embedding role**. It does not call the classifier, answering model or judge. It may still send policy text and queries to the configured embedding provider.

## 3. Verify the endpoint and start the search demo

```sh
uv run python -m agent.search_demo --check
uv run python -m agent.search_demo
```

Semantic is the default mode. Startup embeds changed policy records and `--check` also embeds a real query. Missing configuration or failed embeddings cause a clear error and exit code 2; no silent lexical fallback occurs. First-time indexing can take longer than a warm query.

The real semantic cache is `.cache/policy-index.semantic.json`. The ordinary lexical preparation command uses `.cache/policy-index.json`, so it no longer overwrites the semantic cache. Cache identity includes endpoint and model.

Try these questions:

1. `Can I send banknotes?` — inspect the alias score for the cash rule.
2. `Can I ship paper money from my wallet?` — inspect whether semantics ranks the cash rule when literal overlap is absent or weak.
3. `Can I ship a bottle of scented eau de toilette?` — inspect perfume candidates. Select the applicable result, confirm it, then supply `volume_ml` as a number if needed.
4. `Can I send a ceramic mug?` — candidates may still appear. Do not interpret a ranked candidate as acceptance or prohibition.
5. `/expand`, then `Can I send 31 ml illustration ink?` — show the newly added fictional rule and its numerical boundary.
6. `/reset` — restore the original 15-policy snapshot. `/quit` ends the session.

The expanded snapshot has 18 records. These synthetic additions are demonstrations, not genuine company policy. Use the rank prompt only to inspect a candidate. Evaluation requires the operator to confirm applicability; similarity is not proof that a rule applies. Supported conditions are evaluated by the existing rule engine. Missing/invalid facts produce clarification instead of a guessed amount. Scores are ranking components, not calibrated confidence probabilities.

## 4. Record the before/after showcase

```sh
uv run python -m agent.search_demo --showcase --report results/semantic-showcase.jsonl
```

Choose a fresh report filename on reruns. The demo will not overwrite an existing report. Queries and expected policy IDs live in `evals/fixtures/retrieval_demo.json`, separate from runtime policy text.

Each row records mode, model, snapshot, record count, candidate policy IDs/text, keyword/alias/semantic scores, query latency and snapshot preparation time. Positive cases check whether **all expected policy IDs** appear among five candidates. Unknown/no-applicable-rule cases remain unassessed for automatic pass/fail; inspect them manually. Their empty expected list is never counted as an automatic success.

Exit code 0 means all positive retrieval checks passed, 1 means at least one failed, and 2 means setup/runtime failure. This is retrieval evidence, not a decision-accuracy, hallucination or production-safety score. Embedding quality has not been measured on the development machine; do not assume every positive case will pass your chosen model.

To show the keyword/alias baseline with the same questions:

```sh
uv run python -m agent.search_demo --mode lexical --showcase --report results/lexical-showcase.jsonl
```

This command is entirely offline and clearly labels itself lexical. Paraphrase retrieval failures are legitimate results, not setup errors. It is a **retrieval comparison**, distinct from the planned full-context-versus-workflow experiment.

## 5. Run the full agent with semantic retrieval

Also configure CLASSIFIER and AGENT in `.env` as described in [the teammate guide](../README-TEAMMATE.md). The general readiness checker checks JUDGE too; the interactive chat itself does not judge answers offline.

```sh
uv run python -m agent.demo --semantic --check
uv run python -m agent.demo --semantic
```

The prepared store is reused across requests, including verification resumption. Retrieval events now expose ranking components and the result labels its retrieval mode. Tool permissions still run independently of suggested tools. Rule/template responses may skip the answering model. Purely semantic matches go through the answering-model path rather than automatically triggering a prohibition.

The three additions in the search demo remain an isolated snapshot; they do not silently change the catalogue used by the full agent. Add reviewed records to `agent/data/policies.json` and rerun tests when making an actual policy change.

## Troubleshooting

| Symptom | Next step |
|---|---|
| Opening `/v1` shows an error or blank page | Expected: it is an API base URL. Run the terminal command above. |
| Missing EMBEDDING_MODEL | Set it in `.env`; chat-role model settings do not configure embeddings. |
| Endpoint/model error | Check server, exact model ID and embedding capability; try `--check` before the showcase. |
| Semantic check succeeds, full agent fails | Test CLASSIFIER/AGENT configuration separately. Embeddings do not provide chat/tool calling. |
| Different top result on a paraphrase | Record it as retrieval quality; inspect candidates and scores rather than forcing a favourable result. |
| Several items with different volumes | The initial extractor cannot bind each quantity to each item. Confirm the selected rule and supply the appropriate fact explicitly. |

Implementation checks: `uv run pytest -q`. All mock-vector tests are offline. Do not report them as a successful live embedding evaluation.
