#!/usr/bin/env python3
"""
Simple script to generate objective embeddings
"""

import sys
import os
import time
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.llm.embeddings import StandardsEmbeddings
from backend.repositories.standards_repository import StandardsRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def generate_all_objective_embeddings():
    """Generate embeddings for all objectives"""
    print("🎯 Generating All Objective Embeddings")
    print("=" * 45)

    repo = StandardsRepository()
    embeddings_manager = StandardsEmbeddings()

    # Get all standards first, then get objectives from each standard
    standards = repo.get_all_standards()
    print(f"Processing {len(standards)} standards to find objectives...")

    all_objectives = []
    for standard in standards:
        objectives = repo.get_objectives_for_standard(standard.standard_id)
        all_objectives.extend(objectives)

    print(f"Found {len(all_objectives)} total objectives")

    # Get already embedded objectives
    conn = embeddings_manager.db_manager.get_connection()
    try:
        cursor = conn.execute("SELECT objective_id FROM objective_embeddings")
        embedded_ids = {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()

    # Filter out already embedded objectives
    remaining_objectives = [
        obj for obj in all_objectives if obj.objective_id not in embedded_ids
    ]
    print(f"Remaining objectives to embed: {len(remaining_objectives)}")

    if not remaining_objectives:
        print("✅ All objectives already have embeddings!")
        return

    # Process objectives
    success_count = 0
    error_count = 0

    for i, objective in enumerate(remaining_objectives, 1):
        try:
            print(
                f"[{i}/{len(remaining_objectives)}] Generating embedding for {objective.objective_id}..."
            )
            embedding = embeddings_manager.generate_objective_embedding(objective)
            embeddings_manager.store_objective_embedding(objective, embedding)
            success_count += 1
            print(f"  ✅ Success")

            # Delay to avoid overwhelming the API
            time.sleep(1.5)

        except Exception as e:
            error_count += 1
            print(f"  ❌ Error: {e}")
            logger.error(
                f"Failed to generate embedding for {objective.objective_id}: {e}"
            )

            # If we get errors, maybe wait a bit longer
            time.sleep(3)

    print(f"\n🎉 Generation Complete!")
    print(f"✅ Successfully generated: {success_count}")
    print(f"❌ Errors: {error_count}")

    # Verify final count
    final_stats = embeddings_manager.get_embedding_stats()
    print(
        f"📊 Final objective embeddings: {final_stats.get('objective_embeddings', 0)}"
    )


if __name__ == "__main__":
    generate_all_objective_embeddings()
