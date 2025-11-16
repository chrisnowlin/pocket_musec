#!/usr/bin/env python3
"""
Populate RAG embedding data from existing standards - batch version with progress tracking
"""

import sys
import os
import time
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.llm.embeddings import StandardsEmbedder, StandardsEmbeddings
from backend.repositories.standards_repository import StandardsRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def populate_rag_data_batch(max_standards=20, batch_size=3):
    """Populate RAG data with embeddings for a limited number of standards"""
    print(f"🎵 Populating RAG Embedding Data (max {max_standards} standards)")
    print("=" * 50)

    # Check current state
    repo = StandardsRepository()
    standards = repo.get_all_standards()
    print(f"📊 Found {len(standards)} standards in database")

    # Limit to max_standards for testing
    standards = standards[:max_standards]
    print(f"📊 Processing first {len(standards)} standards")

    embeddings_manager = StandardsEmbeddings()
    stats = embeddings_manager.get_embedding_stats()
    print(f"📈 Current embedding stats: {stats}")

    if stats["standard_embeddings"] > 0:
        print(f"⚠️  Embeddings already exist. Clearing existing data...")
        embeddings_manager.delete_all_embeddings()
        embeddings_manager.delete_all_prepared_texts()
        print("✅ Existing embeddings cleared")

    # Generate embeddings in batches
    print(f"🚀 Starting embedding generation (batch size: {batch_size})...")
    start_time = time.time()

    success_count = 0
    failed_count = 0

    for i in range(0, len(standards), batch_size):
        batch = standards[i : i + batch_size]
        print(
            f"📦 Processing batch {i // batch_size + 1}/{(len(standards) - 1) // batch_size + 1} ({len(batch)} standards)"
        )

        for standard in batch:
            try:
                # Get objectives for this standard
                objectives = repo.get_objectives_for_standard(standard.standard_id)

                # Generate embedding
                embedding = embeddings_manager.generate_standard_embedding(
                    standard, objectives
                )

                # Store embedding
                embeddings_manager.store_standard_embedding(
                    standard, objectives, embedding
                )

                success_count += 1
                print(
                    f"  ✅ Embedded standard {standard.standard_id} ({success_count}/{len(standards)})"
                )

                # Brief pause to avoid rate limiting
                time.sleep(0.5)

            except Exception as e:
                logger.error(
                    f"  ❌ Failed to embed standard {standard.standard_id}: {e}"
                )
                failed_count += 1

        # Longer pause between batches
        if i + batch_size < len(standards):
            print(f"  ⏸️  Pausing between batches...")
            time.sleep(2)

    elapsed_time = time.time() - start_time

    print(f"✅ Embedding generation completed in {elapsed_time:.2f} seconds")
    print(f"📊 Results: {success_count} success, {failed_count} failed")

    # Verify results
    final_stats = embeddings_manager.get_embedding_stats()
    print(f"📈 Final embedding stats: {final_stats}")

    # Test semantic search
    print(f"🔍 Testing semantic search...")
    try:
        test_results = repo.search_standards_semantic(
            query="rhythm patterns", grade_level="1", limit=3, similarity_threshold=0.3
        )
        print(f"✅ Semantic search found {len(test_results)} results")
        for j, (standard, similarity) in enumerate(test_results, 1):
            print(f"   {j}. {standard.standard_id} - similarity: {similarity:.3f}")
            print(f"      {standard.standard_text[:80]}...")
    except Exception as e:
        print(f"❌ Semantic search test failed: {e}")

    return success_count > 0


if __name__ == "__main__":
    success = populate_rag_data_batch(max_standards=20, batch_size=3)
    sys.exit(0 if success else 1)
