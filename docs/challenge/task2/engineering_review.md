# Task 2 — Engineering Review

What judges look for in your extraction code. Tier 2 doesn't affect the leaderboard, but it's how finalists get picked.

## Code Quality (35% of Tier 2)

| Dimension | What judges look for |
|---|---|
| Structure (25%) | Document parsing separated from LLM interaction. Schema mapping in its own module. Normalization rules factored out, not inline. |
| Type safety (20%) | Output schema fully typed with nested Pydantic models (`Indication`, `DosageForm`, `Warning`, `AdverseReaction`). Optional fields typed as `T | None`. |
| Error handling (15%) | Malformed LLM output handled. Fallback logic for missing sections. Per-field failure instead of whole-extraction failure. |
| Testing (25%) | Tests with sample documents. Normalization rules unit-tested (unit conversion, drug name canonicalization). Edge cases tested (empty document, missing sections). |
| Readability (15%) | Extraction prompt clearly structured with target schema. Normalization rules documented. |

## Architecture Design (40% of Tier 2)

| Dimension | What judges look for |
|---|---|
| AI pipeline (30%) | Chunking or section-splitting strategy for long documents. Clear decision on single-pass vs. section-by-section extraction. Post-processing pipeline (LLM output → normalization → validation → response). |
| Decomposition (25%) | Parser → Extractor → Normalizer → Validator layering. Each stage has a clear responsibility and interface. |
| API design (20%) | `POST /extract` handles the full document contract. Proper error responses for invalid documents. Consistent output schema whether all fields are present or some are null. |
| Trade-off reasoning (15%) | Awareness of accuracy-vs-cost trade-off in single-pass vs. multi-pass extraction. Model selection justified for document size. |
| Scalability (10%) | Can process documents concurrently. Token budget management for very long documents. |

## Engineering Maturity (25% of Tier 2)

| Dimension | What judges look for |
|---|---|
| Deployment (30%) | Same as all tasks — Dockerfile, env config, README. |
| Config and secrets (25%) | Model endpoint and API keys in env vars. Token limits configurable. |
| Observability (20%) | Structured logging with `document_id`. Extraction success/failure rates logged. |
| Security (25%) | Document content treated as untrusted input. Input size limits enforced. |

## Tips

- Documents are long (5,000–10,000+ words). Input tokens dominate cost.
- Some fields (drug name, manufacturer) can be grabbed with regex — save LLM calls for the hard stuff.
- Prompt caching is less useful here since the document changes every request.
- Extraction is a pipeline problem. The differentiator is parsing + normalization, not just prompt quality.
