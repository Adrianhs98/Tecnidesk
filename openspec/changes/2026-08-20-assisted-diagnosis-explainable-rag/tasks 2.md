# Tasks: AI-Assisted Diagnostic System with Explainable Reasoning

- [ ] 1. Phase 1: Infrastructure Foundation & Local Embeddings
  - [ ] 1.1 Document Mac mini M1 prerequisites: `pmset` sleep rules, `tailscale funnel 11434 on`, and `ollama pull nomic-embed-text-v2-moe:latest`
  - [ ] 1.2 Add `google-genai>=0.1.0` and `pgvector>=0.3.0` to `backend/requirements.txt`
  - [ ] 1.3 Add `LOCAL_EMBEDDING_SERVICE_URL` and `GEMINI_API_KEY` to `backend/app/config.py` (`Settings`)
  - [ ] 1.4 Create Alembic migration enabling `vector` extension and creating `diagnostic_cases`, `diagnostic_conversations`, `diagnostic_messages`, and `diagnostic_query_log` tables
  - [ ] 1.5 Create SQLAlchemy 2.0 ORM models in `backend/app/models/diagnostic.py` with `Vector(768)` and HNSW index
  - [ ] 1.6 Implement `backend/app/services/embedding_service.py` with 512-token safe truncation, `search_document: ` and `search_query: ` prefixes, and 10s HTTP timeout fallback
  - [ ] 1.7 Create automated `pg_dump` backup script in `backend/scripts/backup_supabase.sh` (or `.ps1`) for local database snapshots

- [ ] 2. Phase 2: Synthetic Data Generation & Hybrid Retrieval
  - [ ] 2.1 Create domain rule knowledge base matrix for common smartphone brands/models in `backend/app/data/synthetic_repair_matrix.json`
  - [ ] 2.2 Create ingestion script `backend/scripts/seed_synthetic_cases.py` to embed and seed ~200-300 synthetic diagnostic cases with `source_type = 'synthetic'`
  - [ ] 2.3 Implement `backend/app/services/diagnostic_service.py` with pgvector similarity search, multi-tenant `shop_id` filter (allowing global synthetics), and composite scoring (`real_validated` prioritized over `synthetic`)
  - [ ] 2.4 Add unit tests for retrieval scoring and tenant isolation in `backend/tests/unit/test_diagnostic_retrieval.py`

- [ ] 3. Phase 3: Grounded Reasoning Layer & Explainability
  - [ ] 3.1 Create Pydantic diagnostic schemas in `backend/app/schemas/diagnostic.py` (`GroundedCitation`, `DiagnosticResponse`)
  - [ ] 3.2 Implement `backend/app/services/explanation_service.py` using `gemini-3.5-flash` with zero temperature, structured JSON schema output, and closed-world prompt
  - [ ] 3.3 Implement deterministic post-check verification function in `explanation_service.py` validating that cited `case_id`s exist and `diagnosed_cause`/`solution_applied` match the database records exactly
  - [ ] 3.4 Create endpoint `POST /tickets/{id}/diagnose` in `backend/app/routers/tickets.py` guarded by `subscription_guard` with query logging to `diagnostic_query_log` and `had_sufficient_evidence = false` fallback
  - [ ] 3.5 Add unit and integration tests for grounded reasoning, hallucination rejection, and distance threshold cutoff in `backend/tests/integration/test_explainable_diagnosis.py`

- [ ] 4. Phase 4: Human-in-the-Loop Correction Chat
  - [ ] 4.1 Implement `backend/app/services/correction_service.py` to handle conversation turns and message history
  - [ ] 4.2 Create endpoints `POST /tickets/{id}/diagnostic-chat` and `POST /tickets/{id}/diagnostic-chat/confirm`
  - [ ] 4.3 Implement correction confirmation logic: embeds the technician's validated solution, creates a new `diagnostic_case` with `source_type = 'real_validated'`, populates `shop_id` and `derived_from_case_id` pointing to the original synthetic case, and closes conversation
  - [ ] 4.4 Add integration tests covering the correction loop and coexistence of synthetic and real cases in `backend/tests/integration/test_diagnostic_correction.py`

- [ ] 5. Phase 5: Frontend Integration & Maturity Metric
  - [ ] 5.1 Implement `GET /diagnostic/maturity-metric` endpoint returning the percentage of diagnoses served by `real_validated` data
  - [ ] 5.2 Create frontend API client functions in `frontend/src/api/diagnostic.js`
  - [ ] 5.3 Integrate diagnostic assist panel with collapsible citation badges, confidence scores, and explanation inside `frontend/src/features/admin/components/DiagnosticModal.jsx`
  - [ ] 5.4 Integrate inline correction chat drawer inside `DiagnosticModal.jsx`
  - [ ] 5.5 Integrate lightweight onBlur initial suggestion preview in `frontend/src/features/admin/components/NewTicketModal.jsx`
  - [ ] 5.6 Add component and workflow tests in `frontend/src/tests/components/DiagnosticAssist.test.jsx`
  - [ ] 5.7 Run full test suite (`pytest` and `npm test`) and build verification (`npm run build`)
