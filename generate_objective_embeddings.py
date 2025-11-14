#!/usr/bin/env python3
"""
Generate objective embeddings in smaller batches
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


def generate_objective_embeddings_batch(batch_size=10, delay=2.0):
    """Generate objective embeddings in small batches"""
    print("🎯 Generating Objective Embeddings")
    print("=" * 40)

    repo = StandardsRepository()
    embeddings_manager = StandardsEmbeddings()

    # Get all objectives
    objectives = repo.get_all_objectives()
    print(f"Total objectives to process: {len(objectives)}")

    # Get already embedded objectives
    conn = embeddings_manager.db_manager.get_connection()
    try:
        cursor = conn.execute("SELECT objective_id FROM objective_embeddings")
        embedded_ids = {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()

    # Filter out already embedded objectives
    remaining_objectives = [
        obj for obj in objectives if obj.objective_id not in embedded_ids
    ]
    print(f"Remaining objectives to embed: {len(remaining_objectives)}")

    if not remaining_objectives:
        print("✅ All objectives already have embeddings!")
        return

    # Process in batches
    success_count = 0
    error_count = 0

    for i in range(0, len(remaining_objectives), batch_size):
        batch = remaining_objectives[i : i + batch_size]
        print(
            f"\nProcessing batch {i // batch_size + 1}/{(len(remaining_objectives) + batch_size - 1) // batch_size}"
        )

        for objective in batch:
            try:
                print(f"  Generating embedding for {objective.objective_id}...")
                embedding = embeddings_manager.generate_objective_embedding(objective)
                embeddings_manager.store_objective_embedding(objective, embedding)
                success_count += 1
                print(f"    ✅ Success")

                # Small delay to avoid overwhelming the API
                time.sleep(delay)

            except Exception as e:
                error_count += 1
                print(f"    ❌ Error: {e}")
                logger.error(
                    f"Failed to generate embedding for {objective.objective_id}: {e}"
                )

        # Longer delay between batches
        if i + batch_size < len(remaining_objectives):
            print(f"  Batch completed. Waiting {delay * 2}s before next batch...")
            time.sleep(delay * 2)

    print(f"\n🎉 Generation Complete!")
    print(f"✅ Successfully generated: {success_count}")
    print(f"❌ Errors: {error_count}")

    # Verify final count
    final_stats = embeddings_manager.get_embedding_stats()
    print(
        f"📊 Final objective embeddings: {final_stats.get('objective_embeddings', 0)}"
    )


if __name__ == "__main__":
    generate_objective_embeddings_batch(batch_size=5, delay=1.5)
