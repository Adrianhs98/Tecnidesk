# Specification: Assisted Diagnosis with Explainability

**Capability**: `assisted-diagnosis`  
**Status**: draft  
**Version**: 1.0  

## Overview
This capability introduces an AI-assisted diagnostic tool for technicians. It uses a Retrieve-then-Explain RAG pattern over structured data to find similar historical or synthetic repair cases, and strictly grounds its explanations in the retrieved cases to prevent hallucination. It also includes a feedback loop for technicians to correct diagnoses, continuously shifting the system's maturity from synthetic rules to real workshop data.

## Scenarios

### Scenario 1: Database Infrastructure and Local Embedding Configuration
**Given** a clean PostgreSQL database in Supabase
**When** the backend initializes or migrations run
**Then** the `vector` extension is enabled in the `extensions` schema
**And** the `diagnostic_cases` table is created with an `embedding` column of type `Vector(768)`
**And** an HNSW index is created on the `embedding` column using `vector_cosine_ops`
**And** the backend utilizes a local Ollama service (`nomic-embed-text-v2-moe:latest`, 768 dims, optimized for multilingual) hosted on a Mac mini via Tailscale Funnel (`LOCAL_EMBEDDING_SERVICE_URL`)
**And** any new cases saved to the database are explicitly embedded by first safely truncating the concatenated text to fit the 512-token limit, and then prepending the `search_document: ` prefix.

### Scenario 2: Hybrid Retrieval and Scoring
**Given** a mix of `synthetic` and `real_validated` diagnostic cases in the database
**When** a technician requests a diagnosis for a specific device brand, model, and symptom
**Then** the system generates a new 768-dim embedding for the described symptom in real-time by calling the local Ollama service, **strictly prepending the `search_query: ` prefix**
**And** the system filters candidates by `shop_id` (allowing global `synthetic` cases) and device brand/model
**And** the system performs a cosine similarity search against the real-time symptom embedding
**And** the final ranking prioritizes `real_validated` cases over `synthetic` cases if both have similar distance scores.

### Scenario 3: Strict Grounded Synthesis (Zero Hallucination)
**Given** the retrieval step returned highly relevant cases
**When** the reasoning engine (LLM) generates the explanation
**Then** the output is a structured JSON payload
**And** every factual claim in the explanation cites a valid `case_id` that exists within the retrieved set
**And** the cited `diagnosed_cause` and `solution_applied` fields perfectly match the original structured database columns for that `case_id`
**And** the system successfully validates this exact field match via a deterministic post-check before returning the response.

### Scenario 4: Graceful Fallback on Insufficient Evidence
**Given** the retrieval step found no cases with a cosine distance $\le 0.40$
**When** the reasoning engine attempts to generate an explanation
**Then** the system explicitly sets `had_sufficient_evidence = false`
**And** the system returns a safe fallback message indicating lack of historical data, rather than hallucinating an ungrounded solution.

### Scenario 5: Human-in-the-Loop Correction (Feedback Loop)
**Given** a completed diagnostic recommendation presented to a technician
**When** the technician engages the correction chat to modify the diagnosis and confirms the new solution
**Then** a new record is inserted into `diagnostic_cases`
**And** the new record has `source_type = 'real_validated'`
**And** it contains the technician's actual `diagnosed_cause` and `solution_applied`
**And** it populates `derived_from_case_id` with the original case's ID
**And** the original synthetic case is left unmodified.

### Scenario 6: Maturity Metric Tracking
**Given** the diagnostic system is actively used
**When** a diagnosis is served to the frontend
**Then** the query and the `source_type` of the top retrieved case are logged in `diagnostic_query_log`
**And** the frontend can calculate and display a maturity metric representing the percentage of diagnoses driven by `real_validated` data versus `synthetic` data.
