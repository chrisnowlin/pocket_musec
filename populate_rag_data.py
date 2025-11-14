#!/usr/bin/env python3
"""
Populate RAG embedding data from existing standards
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


def populate_rag_data():
    """Populate RAG data with embeddings for all existing standards"""
    print("🎵 Populating RAG Embedding Data")
    print("=" * 50)

    # Check current state
    repo = StandardsRepository()
    standards = repo.get_all_standards()
    print(f"📊 Found {len(standards)} standards in database")

    embeddings_manager = StandardsEmbeddings()
    embedder = StandardsEmbedder()
    stats = embeddings_manager.get_embedding_stats()
    print(f"📈 Current embedding stats: {stats}")

    if stats["standard_embeddings"] > 0:
        print(f"⚠️  Embeddings already exist. Clearing existing data...")
        embeddings_manager.delete_all_embeddings()
        embeddings_manager.delete_all_prepared_texts()
        print("✅ Existing embeddings cleared")

    # Generate embeddings
    print(f"🚀 Starting embedding generation...")
    start_time = time.time()

    try:
        generation_stats = embedder.embed_all_standards(batch_size=5)
        elapsed_time = time.time() - start_time

        print(f"✅ Embedding generation completed in {elapsed_time:.2f} seconds")
        print(f"📊 Final stats: {generation_stats}")

        # Verify results
        final_stats = embeddings_manager.get_embedding_stats()
        print(f"📈 Final embedding stats: {final_stats}")

        # Test semantic search
        print(f"🔍 Testing semantic search...")
        test_results = repo.search_standards_semantic(
            query="rhythm patterns", grade_level="1", limit=3, similarity_threshold=0.3
        )
        print(f"✅ Semantic search found {len(test_results)} results")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to populate RAG data: {e}")
        return False


if __name__ == "__main__":
    success = populate_rag_data()
    sys.exit(0 if success else 1)
