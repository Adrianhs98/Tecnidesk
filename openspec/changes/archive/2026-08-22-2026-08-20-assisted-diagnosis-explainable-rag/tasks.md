# Tasks: AI-Assisted Diagnostic System with Explainable Reasoning

- [x] 1. Phase 1: Infrastructure Foundation & Local Embeddings
  - [x] 1.1 Document Mac mini M1 prerequisites: `pmset` sleep rules, `tailscale funnel 11434 on`, and `ollama pull nomic-embed-text-v2-moe:latest`
  - [x] 1.2 Add `google-genai>=0.1.0` and `pgvector>=0.3.0` to `backend/requirements.txt`
  - [x] 1.3 Add `LOCAL_EMBEDDING_SERVICE_URL` and `GEMINI_API_KEY` to `backend/app/config.py` (`Settings`)
  - [x] 1.4 Create Alembic migration enabling `vector` extension and creating `diagnostic_cases`, `diagnostic_conversations`, `diagnostic_messages`, and `diagnostic_query_log` tables
  - [x] 1.5 Create SQLAlchemy 2.0 ORM models in `backend/app/models/diagnostic.py` with `Vector(768)` and HNSW index
  - [x] 1.6 Implement `backend/app/services/embedding_service.py` with 512-token safe truncation, `search_document: ` and `search_query: ` prefixes, 10s HTTP timeout fallback, and `EmbeddingServiceUnavailableError` exception handling
  - [x] 1.7 Create automated `pg_dump` backup script in `backend/scripts/backup_supabase.sh` (or `.ps1`) for local database snapshots

- [x] 2. Phase 2: Synthetic Data Generation & Hybrid Retrieval
  - [x] 2.1 Create domain rule knowledge base matrix for common smartphone brands/models in `backend/app/data/synthetic_repair_matrix.json`
  - [x] 2.2 Create ingestion script `backend/scripts/seed_synthetic_cases.py` to embed and seed ~200-300 synthetic diagnostic cases with `source_type = 'synthetic'`
  - [x] 2.3 Implement `backend/app/services/diagnostic_service.py` with pgvector similarity search, multi-tenant `shop_id` filter (allowing global synthetics), and composite scoring (`real_validated` prioritized over `synthetic`)
  - [x] 2.4 Add unit tests for retrieval scoring and tenant isolation in `backend/tests/unit/test_diagnostic_retrieval.py`

- [x] 3. Phase 3: Grounded Reasoning Layer & Explainability
  - [x] 3.1 Create Pydantic diagnostic schemas in `backend/app/schemas/diagnostic.py` (`GroundedCitation`, `DiagnosticResponse`)
  - [x] 3.2 Implement `backend/app/services/explanation_service.py` using `gemini-3.7-flash` (high thinking effort, zero temperature, structured JSON schema output, and closed-world prompt)
  - [x] 3.3 Implement deterministic post-check verification function in `explanation_service.py` validating that cited `case_id`s exist and `diagnosed_cause`/`solution_applied` match the database records exactly
  - [x] 3.4 Create endpoint `POST /tickets/{id}/diagnose` in `backend/app/routers/tickets.py` guarded by `subscription_guard` with query logging to `diagnostic_query_log` and `had_sufficient_evidence = false` fallback
  - [x] 3.5 Add unit and integration tests for grounded reasoning, hallucination rejection, and distance threshold cutoff in `backend/tests/integration/test_explainable_diagnosis.py`

- [x] 4. Phase 4: Human-in-the-Loop Correction Chat
  - [x] 4.1 Implement `backend/app/services/correction_service.py` to handle conversation turns and message history
  - [x] 4.2 Create endpoints `POST /tickets/{id}/diagnostic-chat` and `POST /tickets/{id}/diagnostic-chat/confirm`
  - [x] 4.3 Implement correction confirmation logic: embeds the technician's validated solution, creates a new `diagnostic_case` with `source_type = 'real_validated'`, populates `shop_id` and `derived_from_case_id` pointing to the original synthetic case, and closes conversation
  - [x] 4.4 Add integration tests covering the correction loop and coexistence of synthetic and real cases in `backend/tests/integration/test_diagnostic_correction.py`

- [x] 5. Phase 5: Frontend Integration & Maturity Metric
  - [x] 5.1 Implement `GET /diagnostic/maturity-metric` endpoint returning the percentage of diagnoses served by `real_validated` data
  - [x] 5.2 Create frontend API client functions in `frontend/src/api/diagnostic.js`
  - [x] 5.3 Integrate diagnostic assist panel with collapsible citation badges, confidence scores, and explanation inside `frontend/src/features/admin/components/DiagnosticModal.jsx`
  - [x] 5.4 Integrate inline correction chat drawer inside `DiagnosticModal.jsx`
  - [x] 5.5 Integrate lightweight onBlur initial suggestion preview in `frontend/src/features/admin/components/NewTicketModal.jsx`
  - [x] 5.6 Add component and workflow tests in `frontend/src/tests/components/DiagnosticAssist.test.jsx`
  - [x] 5.7 Run full test suite (`pytest` and `npm test`) and build verification (`npm run build`)
