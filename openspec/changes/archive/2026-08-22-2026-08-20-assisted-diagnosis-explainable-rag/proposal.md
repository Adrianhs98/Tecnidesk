# Proposal: AI-Assisted Diagnostic System with Explainable Reasoning and Hybrid Trust Architecture

**Status**: proposed  
**Date**: 2026-08-20  
**Author**: SDD Orchestrator  

---

## 1. Problem & Context

TecniDesk currently has **no AI-assisted diagnosis or RAG module**. The database lacks vector extensions, embeddings tables, and AI dependencies. Furthermore, with TecniDesk currently in a cold-start state (<100 total tickets in production and ~10 real historical pilot cases), any traditional search or simple retrieval approach would fail due to data sparsity.

A simple "find similar tickets" search lacks the technical depth and transparency required for real workshop adoption. Technicians need:
1. A system that works reliably from day one using validated domain knowledge rules (synthetic data) without hallucinating.
2. A strict **hierarchy of trust** where real shop-validated repair outcomes always supersede synthetic benchmarks.
3. An **explainable reasoning layer** ("Retrieve-then-Explain") where every diagnostic recommendation is explicitly backed by cited evidence (exact case IDs, source classification, confidence scores, and natural language rationale).
4. A **human-in-the-loop conversation channel** allowing technicians to confirm, correct, or refine diagnoses, which persists new `real_validated` knowledge linked by device brand/model without overwriting the original synthetic guideline.

---

## 2. Proposed Architecture & Solution

### 2.1 Core AI & Database Stack
- **Vector Extension**: Enable PostgreSQL `vector` extension (`pgvector`) in Supabase.
- **Embedding Model**: Local Ollama service running `nomic-embed-text-v2-moe:latest` (768 dims) hosted on a Mac mini M1, exposed via Tailscale Funnel. This MoE architecture is specifically trained for multilingual support (~100 languages, including strong Spanish performance). Keeps recurring vector costs at $0 while matching the 768-dim HNSW architecture. **Constraints**: It has a strict 512-token context limit (unlike v1.5), so the backend must safely truncate concatenated case text before embedding. **Critical Requirement**: The model requires explicit task prefixes: `search_document: ` for cases stored in the database, and `search_query: ` for the symptom searched by the technician.
- **LLM Reasoning Engine**: `gemini-3.7-flash` (high thinking effort, temperature 0.0, structured JSON output) via the official `google-genai` SDK. Provides strong multi-step technical grounding and explanation quality.
- **ORM & Driver**: `SQLAlchemy 2.0` (async) + `asyncpg` + `pgvector.sqlalchemy` with HNSW cosine distance indexing (`vector_cosine_ops`).

### 2.2 Data Model (New Isolated Tables)
1. `diagnostic_cases`: Stores both `synthetic` rules and `real_validated` workshop outcomes with `embedding Vector(768)`, `source_type`, `shop_id` (NULL for global synthetic cases), `device_brand`, `device_model`, `symptom_text`, `diagnosed_cause`, `solution_applied`, and optional `derived_from_case_id`.
2. `diagnostic_conversations`: Manages human-in-the-loop chat threads per diagnostic recommendation.
3. `diagnostic_messages`: Audit trail of messages exchanged between technician and assistant.
4. `diagnostic_query_log`: Tracks queries, top similarity score, source type used, and evidence sufficiency for the maturity metric (`% real_validated vs synthetic`).

### 2.3 Two-Step Grounded Reasoning Pipeline
1. **Deterministic Retrieval & Scoring**: Query embedding generated on-the-fly for new symptoms via the local Ollama service. The backend **must** prepend the `search_query: ` prefix to the symptom text before generating the embedding, ensuring proper vector alignment with the stored cases (which are embedded using the `search_document: ` prefix) &rarr; pgvector similarity search &rarr; composite score (`similarity * source_weight`) &rarr; confidence threshold cutoff (distance $\le 0.40$). If the local embedding service fails (e.g. timeout > 10s), the system gracefully fails with an `EMBEDDING_SERVICE_UNAVAILABLE` error, distinct from the `INSUFFICIENT_EVIDENCE` fallback.
2. **Grounded Synthesis & Quote Verification**: LLM receives bounded evidence context &rarr; produces structured claims citing exact `case_id` and reproducing the structured fields exactly &rarr; deterministic post-check verifies that the cited `case_id` exists in the retrieved set AND that the generated `diagnosed_cause` / `solution_applied` text perfectly matches the actual database fields for that case &rarr; fallback to `INSUFFICIENT_EVIDENCE` if ungrounded.

### 2.4 Phased Implementation Roadmap
- **Phase 1 (Infrastructure Foundation)**: Dependencies (`google-genai`, `pgvector`), `GEMINI_API_KEY` configuration, Mac mini local setup (`pmset` sleep rules, Tailscale Funnel for Ollama on port 11434, pull `nomic-embed-text-v2-moe` via custom GGUF if not in main registry), `LOCAL_EMBEDDING_SERVICE_URL` env var, Alembic migration for `vector` extension, and `embedding_service.py` (implementing the strict task prefixing logic). Also includes scheduled `pg_dump` backup strategy.
- **Phase 2 (Synthetic Data & Scoring Retrieval)**: Domain rule generator script (~200-500 cases across popular brands/models), `diagnostic_service.py` with multi-tenant filtering and hybrid scoring, initial `POST /tickets/{id}/diagnose` endpoint.
- **Phase 3 (Explainable Reasoning Layer)**: Structured Pydantic schema, `explanation_service.py` with 2-step pipeline and deterministic citation verifier, confidence and fallback handling.
- **Phase 4 (Human-in-the-Loop Correction Chat)**: Chat ORM models, migration, `correction_service.py`, endpoints to convert accepted corrections into new `real_validated` cases linked via `derived_from_case_id`.
- **Phase 5 (Frontend Integration & Maturity Metric)**: UI panels in `DiagnosticModal.jsx` and `NewTicketModal.jsx`, collapsible evidence display, inline correction chat, and real-time maturity metric dashboard.

---

## 3. Capabilities

| Capability | Description |
|---|---|
| `assisted-diagnosis-infrastructure` | Supabase pgvector extension, `gemini-embedding-001` integration, and async vector ORM model |
| `assisted-diagnosis-retrieval` | Synthetic domain bootstrapping and hybrid scoring retrieval (real > synthetic) |
| `assisted-diagnosis-explainability` | Two-step grounded explanation pipeline with deterministic quote verification and fallback |
| `assisted-diagnosis-correction-chat` | Human-in-the-loop feedback loop generating persistent `real_validated` cases |
| `assisted-diagnosis-ui-metrics` | Frontend inspection components and honest system maturity tracker |

---

## 4. Explicit Boundaries & Out of Scope

- **No generic conversational bot**: Chat is strictly bounded to validating, correcting, or refining a specific ticket diagnostic.
- **No data overwrites**: Real corrections never overwrite synthetic cases; both coexist with explicit source tags and lineage pointers (`derived_from_case_id`).
- **No ungrounded explanations**: The LLM is forbidden from introducing causes or steps not present in the retrieved evidence chunks.
- **No fake accuracy metrics**: The system reports its maturity honestly as `% of diagnoses served by real data`, starting at 0%.

---

## 5. Acceptance Criteria

1. `POST /tickets/{id}/diagnose` returns a structured diagnosis containing probable cause, recommended repair steps, cited evidence cases, source types (`synthetic` or `real_validated`), similarity scores, and natural language explanation.
2. If cosine distance of all candidates exceeds threshold (> 0.40), the system explicitly returns `had_sufficient_evidence = false` with a safe fallback instead of hallucinating.
3. All claims in the explanation are anchored to a valid `case_id` from the retrieved set, and the cited `diagnosed_cause` / `solution_applied` match the original database fields exactly.
4. When a technician submits a correction via the chat, a new `diagnostic_case` is created with `source_type = 'real_validated'`, its embedding is indexed, and `derived_from_case_id` points to the original case.
5. In subsequent queries for the same device brand/model/symptom, the `real_validated` case is prioritized over the synthetic case.
6. The system calculates and exposes the `% real vs synthetic` maturity metric accurately from `diagnostic_query_log`.
