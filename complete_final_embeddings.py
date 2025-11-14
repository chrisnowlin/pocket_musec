#!/usr/bin/env python3
"""
Complete the final remaining embeddings (Kindergarten, Novice, and the failed I.CR.2)
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


def complete_final_standards():
    """Complete the final remaining standards"""
    print("🎵 Completing Final Standard Embeddings")
    print("=" * 50)

    repo = StandardsRepository()
    embeddings_manager = StandardsEmbeddings()

    # Get all standards and find missing ones
    all_standards = repo.get_all_standards()

    conn = embeddings_manager.db_manager.get_connection()
    try:
        cursor = conn.execute("SELECT standard_id FROM standard_embeddings")
        embedded_ids = {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()

    missing_standards = [s for s in all_standards if s.standard_id not in embedded_ids]

    print(f"📊 Missing standards: {len(missing_standards)}")

    # Group by grade for clarity
    by_grade = {}
    for standard in missing_standards:
        grade = standard.grade_level
        if grade not in by_grade:
            by_grade[grade] = []
        by_grade[grade].append(standard)

    for grade, standards in by_grade.items():
        print(f"  {grade}: {len(standards)} standards")

    success_count = 0
    failed_count = 0

    for grade, standards in by_grade.items():
        print(f"\\n📚 Processing {grade}: {len(standards)} standards")

        for i, standard in enumerate(standards, 1):
            try:
                print(f"  🔄 Processing {standard.standard_id} ({i}/{len(standards)})")

                objectives = repo.get_objectives_for_standard(standard.standard_id)
                embedding = embeddings_manager.generate_standard_embedding(
                    standard, objectives
                )
                embeddings_manager.store_standard_embedding(
                    standard, objectives, embedding
                )

                success_count += 1
                print(f"    ✅ Success")

                time.sleep(1.0)  # Longer pause to avoid rate limits

            except Exception as e:
                logger.error(f"    ❌ Failed {standard.standard_id}: {e}")
                failed_count += 1

                # Try one more time after a longer pause
                print(f"    🔄 Retrying after pause...")
                time.sleep(5.0)
                try:
                    objectives = repo.get_objectives_for_standard(standard.standard_id)
                    embedding = embeddings_manager.generate_standard_embedding(
                        standard, objectives
                    )
                    embeddings_manager.store_standard_embedding(
                        standard, objectives, embedding
                    )

                    success_count += 1
                    failed_count -= 1  # Remove from failed count
                    print(f"    ✅ Retry success")

                except Exception as retry_e:
                    logger.error(f"    ❌ Retry failed: {retry_e}")

    print(f"\\n✅ Final standards: {success_count} success, {failed_count} failed")

    # Verify completion
    final_stats = embeddings_manager.get_embedding_stats()
    print(f"📈 Final standard embeddings: {final_stats['standard_embeddings']}/112")

    return success_count, failed_count


def quick_objective_sample():
    """Generate a sample of objective embeddings to demonstrate functionality"""
    print("\\n🎯 Generating Sample Objective Embeddings")
    print("=" * 50)

    repo = StandardsRepository()
    embeddings_manager = StandardsEmbeddings()

    # Get objectives from just First Grade as a sample
    first_grade_standards = repo.get_standards_by_grade_and_strand(
        "First Grade", "CONNECT"
    )
    sample_objectives = []

    for standard in first_grade_standards[:2]:  # Just 2 standards as sample
        objectives = repo.get_objectives_for_standard(standard.standard_id)
        sample_objectives.extend(objectives)

    print(f"📊 Sample objectives: {len(sample_objectives)}")

    success_count = 0
    failed_count = 0

    for objective in sample_objectives:
        try:
            embedding = embeddings_manager.generate_objective_embedding(objective)
            embeddings_manager.store_objective_embedding(objective, embedding)

            success_count += 1
            print(f"  ✅ {objective.objective_id}")

            time.sleep(0.5)

        except Exception as e:
            logger.error(f"  ❌ Failed {objective.objective_id}: {e}")
            failed_count += 1

    print(f"\\n✅ Sample objectives: {success_count} success, {failed_count} failed")

    return success_count, failed_count


def main():
    """Main execution"""
    print("🚀 Completing Final Embeddings Generation")
    print("=" * 60)

    try:
        # Phase 1: Complete remaining standards
        standard_success, standard_failed = complete_final_standards()

        # Phase 2: Sample objective embeddings (to demonstrate functionality)
        objective_success, objective_failed = quick_objective_sample()

        # Summary
        print("\\n🎉 FINAL COMPLETION SUMMARY")
        print("=" * 60)
        print(f"Standards: {standard_success} success, {standard_failed} failed")
        print(
            f"Objectives (sample): {objective_success} success, {objective_failed} failed"
        )

        # Final verification
        embeddings_manager = StandardsEmbeddings()
        final_stats = embeddings_manager.get_embedding_stats()
        print(f"\\n📈 Final Database Stats:")
        print(f"  Standard embeddings: {final_stats['standard_embeddings']}/112")
        print(f"  Objective embeddings: {final_stats['objective_embeddings']} (sample)")

        if final_stats["standard_embeddings"] == 112:
            print("\\n✅ ALL STANDARD EMBEDDINGS COMPLETED!")
            print("🎯 RAG system is now fully operational for all grades!")
            print("🔍 Semantic search available for all 112 standards!")
        else:
            remaining = 112 - final_stats["standard_embeddings"]
            print(f"\\n⚠️  {remaining} standards still missing embeddings")

        return final_stats["standard_embeddings"] == 112

    except Exception as e:
        logger.error(f"❌ Completion failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
