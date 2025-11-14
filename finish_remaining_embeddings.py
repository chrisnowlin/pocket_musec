#!/usr/bin/env python3
"""
Finish remaining embeddings for the last few grades and objectives
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


def finish_remaining_standards():
    """Complete the remaining standard embeddings"""
    print("🎵 Finishing Remaining Standard Embeddings")
    print("=" * 50)

    repo = StandardsRepository()
    embeddings_manager = StandardsEmbeddings()

    # Get remaining standards
    conn = embeddings_manager.db_manager.get_connection()
    try:
        cursor = conn.execute("SELECT standard_id FROM standard_embeddings")
        embedded_ids = {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()

    all_standards = repo.get_all_standards()
    remaining_standards = [
        s for s in all_standards if s.standard_id not in embedded_ids
    ]

    print(f"📊 Remaining standards: {len(remaining_standards)}")

    # Group by grade
    by_grade = {}
    for standard in remaining_standards:
        grade = standard.grade_level
        if grade not in by_grade:
            by_grade[grade] = []
        by_grade[grade].append(standard)

    print(f"📚 Remaining by grade: {list(by_grade.keys())}")

    success_count = 0
    failed_count = 0

    for grade, standards in by_grade.items():
        print(f"\\n📚 Processing {grade}: {len(standards)} standards")

        for i, standard in enumerate(standards, 1):
            try:
                objectives = repo.get_objectives_for_standard(standard.standard_id)
                embedding = embeddings_manager.generate_standard_embedding(
                    standard, objectives
                )
                embeddings_manager.store_standard_embedding(
                    standard, objectives, embedding
                )

                success_count += 1
                print(f"  ✅ {standard.standard_id} ({i}/{len(standards)})")

                time.sleep(0.5)  # Brief pause

            except Exception as e:
                logger.error(f"  ❌ Failed {standard.standard_id}: {e}")
                failed_count += 1

    print(f"\\n✅ Standards completed: {success_count} success, {failed_count} failed")

    # Verify completion
    final_stats = embeddings_manager.get_embedding_stats()
    print(f"📈 Final standard embeddings: {final_stats['standard_embeddings']}/112")

    return success_count, failed_count


def generate_objective_embeddings():
    """Generate embeddings for all objectives"""
    print("\\n🎯 Generating Objective Embeddings")
    print("=" * 50)

    repo = StandardsRepository()
    embeddings_manager = StandardsEmbeddings()

    # Get all objectives
    all_standards = repo.get_all_standards()
    all_objectives = []

    for standard in all_standards:
        objectives = repo.get_objectives_for_standard(standard.standard_id)
        all_objectives.extend(objectives)

    print(f"📊 Total objectives: {len(all_objectives)}")

    # Filter already embedded
    conn = embeddings_manager.db_manager.get_connection()
    try:
        cursor = conn.execute("SELECT objective_id FROM objective_embeddings")
        embedded_ids = {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()

    remaining_objectives = [
        obj for obj in all_objectives if obj.objective_id not in embedded_ids
    ]
    print(f"📊 Remaining objectives: {len(remaining_objectives)}")

    if not remaining_objectives:
        print("✅ All objectives already embedded")
        return 0, 0

    success_count = 0
    failed_count = 0

    # Process in smaller batches to avoid rate limits
    batch_size = 10
    for i in range(0, len(remaining_objectives), batch_size):
        batch = remaining_objectives[i : i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(remaining_objectives) - 1) // batch_size + 1

        print(f"\\n📦 Batch {batch_num}/{total_batches}: {len(batch)} objectives")

        for j, objective in enumerate(batch, 1):
            try:
                embedding = embeddings_manager.generate_objective_embedding(objective)
                embeddings_manager.store_objective_embedding(objective, embedding)

                success_count += 1
                print(f"  ✅ {objective.objective_id} ({j}/{len(batch)})")

                time.sleep(0.3)  # Brief pause

            except Exception as e:
                logger.error(f"  ❌ Failed {objective.objective_id}: {e}")
                failed_count += 1

        # Pause between batches
        if i + batch_size < len(remaining_objectives):
            print(f"  ⏸️  Pausing between batches...")
            time.sleep(2.0)

    print(f"\\n✅ Objectives completed: {success_count} success, {failed_count} failed")

    # Final verification
    final_stats = embeddings_manager.get_embedding_stats()
    print(f"📈 Final database stats: {final_stats}")

    return success_count, failed_count


def main():
    """Main execution"""
    print("🚀 Finishing Complete Embeddings Generation")
    print("=" * 60)

    try:
        # Phase 1: Finish remaining standards
        standard_success, standard_failed = finish_remaining_standards()

        # Phase 2: Generate objective embeddings
        objective_success, objective_failed = generate_objective_embeddings()

        # Summary
        print("\\n🎉 FINAL COMPLETION SUMMARY")
        print("=" * 60)
        print(f"Standards: {standard_success} success, {standard_failed} failed")
        print(f"Objectives: {objective_success} success, {objective_failed} failed")

        total_success = standard_success + objective_success
        total_failed = standard_failed + objective_failed

        print(f"\\nTotal: {total_success} success, {total_failed} failed")

        if total_failed == 0:
            print("✅ ALL EMBEDDINGS COMPLETED SUCCESSFULLY!")
            print("🎯 RAG system is now fully operational for all grades!")
        else:
            print(f"⚠️  Completed with {total_failed} failures")

        return total_failed == 0

    except Exception as e:
        logger.error(f"❌ Completion failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
