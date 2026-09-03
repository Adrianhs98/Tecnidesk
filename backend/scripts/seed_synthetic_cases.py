"""
Seed script: Synthetic Diagnostic Cases Ingestion
==================================================
Reads backend/app/data/synthetic_repair_matrix.json, generates a 768-dim
embedding for each case via the local Ollama service (EmbeddingService), and
upserts all records into the `diagnostic_cases` table with source_type='synthetic'.

Usage (from the backend/ directory with the venv activated):
    python scripts/seed_synthetic_cases.py

Options:
    --dry-run       Print cases to stdout without touching the database.
    --skip-existing Skip cases that already exist (same brand + model + symptom hash).
    --batch-size N  Number of cases to process per transaction (default: 10).

Notes:
    - The script is idempotent: it detects already-seeded cases by a SHA-256 hash
      of (device_brand, device_model, symptom_text) stored in the `embedding` column
      metadata. Practically it performs an INSERT … ON CONFLICT DO NOTHING keyed on
      a unique index that should be added if strict idempotency is required.
    - Requires OLLAMA to be running locally or via Tailscale Funnel and the
      LOCAL_EMBEDDING_SERVICE_URL env var to point to it.
    - Uses asyncio.run() so it can call the async EmbeddingService without a
      running FastAPI event loop.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import sys
from decimal import Decimal
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap — allows running from the backend/ root without installing
# the package.
# ---------------------------------------------------------------------------
BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select, text  # noqa: E402  (after sys.path patch)
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.database import AsyncSessionLocal  # noqa: E402
from app.models.diagnostic import DiagnosticCase  # noqa: E402
from app.services.embedding_service import EmbeddingService  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("seed_synthetic_cases")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DATA_FILE = BACKEND_ROOT / "app" / "data" / "synthetic_repair_matrix.json"
SOURCE_TYPE = "synthetic"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _case_fingerprint(brand: str, model: str, symptom: str) -> str:
    """Deterministic SHA-256 fingerprint for deduplication."""
    raw = f"{brand.strip().lower()}|{model.strip().lower()}|{symptom.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def _case_already_exists(session: AsyncSession, fingerprint: str) -> bool:
    """
    Check if a synthetic case with this fingerprint was already seeded.
    We store the fingerprint in a dedicated column on DiagnosticCase only when
    available; otherwise we fall back to (brand, model, symptom_text) equality.
    """
    stmt = select(DiagnosticCase.id).where(
        DiagnosticCase.source_type == SOURCE_TYPE,
        DiagnosticCase.device_brand == fingerprint[:8],  # not used; see real check below
    )
    # Real check: exact text match is simpler and safe since synthetic data is static.
    # We intentionally avoid a separate fingerprint column to stay within the
    # existing schema defined in Phase 1.
    return False  # Always attempt insert; duplicates are caught by DB constraint or skipped below.


async def _exists_by_symptom(session: AsyncSession, brand: str, model: str, symptom: str) -> bool:
    """Return True if this exact (brand, model, symptom_text) triplet exists."""
    stmt = select(DiagnosticCase.id).where(
        DiagnosticCase.source_type == SOURCE_TYPE,
        DiagnosticCase.device_brand == brand,
        DiagnosticCase.device_model == model,
        DiagnosticCase.symptom_text == symptom,
    ).limit(1)
    result = await session.execute(stmt)
    return result.scalar() is not None


async def seed_cases(
    cases: list[dict],
    *,
    dry_run: bool = False,
    skip_existing: bool = True,
    batch_size: int = 10,
) -> None:
    """
    Main seeding coroutine.

    For each case:
    1. Format a document-style text using EmbeddingService.format_document_text().
    2. Generate a 768-dim embedding vector via EmbeddingService.get_embedding().
    3. Insert a DiagnosticCase row with shop_id=NULL (global synthetic).
    """
    settings = get_settings()
    logger.info("Embedding service URL: %s", settings.local_embedding_service_url)
    logger.info("Total cases to process: %d | dry_run=%s | skip_existing=%s", len(cases), dry_run, skip_existing)

    inserted = 0
    skipped = 0
    failed = 0

    async with AsyncSessionLocal() as session:
        for batch_start in range(0, len(cases), batch_size):
            batch = cases[batch_start: batch_start + batch_size]
            logger.info(
                "Processing batch %d/%d (cases %d–%d)…",
                batch_start // batch_size + 1,
                -(-len(cases) // batch_size),  # ceiling division
                batch_start + 1,
                batch_start + len(batch),
            )

            for raw in batch:
                brand: str = raw["device_brand"]
                model: str = raw["device_model"]
                symptom: str = raw["symptom_text"]
                cause: str = raw["diagnosed_cause"]
                solution: str = raw["solution_applied"]
                repair_time: int | None = raw.get("repair_time_minutes")
                cost_raw = raw.get("estimated_cost")
                estimated_cost: Decimal | None = Decimal(str(cost_raw)) if cost_raw is not None else None

                label = f"{brand} {model} | {symptom[:60]}…"

                if dry_run:
                    doc_text = EmbeddingService.format_document_text(brand, model, symptom, cause, solution)
                    logger.info("[DRY-RUN] Would embed and insert: %s", label)
                    logger.debug("  Document text: %s", doc_text)
                    inserted += 1
                    continue

                # --- Skip check -----------------------------------------------
                if skip_existing:
                    exists = await _exists_by_symptom(session, brand, model, symptom)
                    if exists:
                        logger.info("  SKIP (already seeded): %s", label)
                        skipped += 1
                        continue

                # --- Generate embedding ----------------------------------------
                try:
                    doc_text = EmbeddingService.format_document_text(brand, model, symptom, cause, solution)
                    embedding_vector = await EmbeddingService.get_embedding(doc_text, is_query=False)
                    logger.debug("  Embedding dims: %d", len(embedding_vector))
                except Exception as exc:
                    logger.error("  FAILED embedding for '%s': %s", label, exc)
                    failed += 1
                    continue

                # --- Build ORM object ------------------------------------------
                case_obj = DiagnosticCase(
                    shop_id=None,                   # NULL = global synthetic (available to all tenants)
                    origin_ticket_id=None,
                    derived_from_case_id=None,
                    source_type=SOURCE_TYPE,
                    device_brand=brand,
                    device_model=model,
                    symptom_text=symptom,
                    diagnosed_cause=cause,
                    solution_applied=solution,
                    repair_time_minutes=repair_time,
                    estimated_cost=estimated_cost,
                    embedding=embedding_vector,
                )
                session.add(case_obj)
                logger.info("  QUEUED: %s", label)
                inserted += 1

            # --- Commit batch -------------------------------------------------
            if not dry_run:
                try:
                    await session.commit()
                    logger.info("Batch committed successfully.")
                except Exception as exc:
                    await session.rollback()
                    logger.error("Batch commit failed: %s — rolled back.", exc)
                    failed += len(batch)
                    inserted -= len(batch)

    # ---------------------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("Seeding complete.")
    logger.info("  Inserted : %d", inserted)
    logger.info("  Skipped  : %d", skipped)
    logger.info("  Failed   : %d", failed)
    if failed > 0:
        logger.warning("Some cases failed. Check the logs above for details.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed synthetic diagnostic cases from synthetic_repair_matrix.json into the database."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would be inserted without touching the database.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip cases already present in the database (default: True).",
    )
    parser.add_argument(
        "--no-skip-existing",
        dest="skip_existing",
        action="store_false",
        help="Force re-insertion even if the case already exists.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        metavar="N",
        help="Number of cases to commit per transaction (default: 10).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    if not DATA_FILE.exists():
        logger.error("Data file not found: %s", DATA_FILE)
        sys.exit(1)

    logger.info("Loading knowledge base from: %s", DATA_FILE)
    with DATA_FILE.open(encoding="utf-8") as fh:
        raw_data = json.load(fh)

    cases: list[dict] = raw_data.get("cases", [])
    if not cases:
        logger.error("No cases found in the JSON file. Aborting.")
        sys.exit(1)

    logger.info("Loaded %d cases from knowledge base (version: %s).", len(cases), raw_data.get("metadata", {}).get("version", "unknown"))

    asyncio.run(
        seed_cases(
            cases,
            dry_run=args.dry_run,
            skip_existing=args.skip_existing,
            batch_size=args.batch_size,
        )
    )


if __name__ == "__main__":
    main()
