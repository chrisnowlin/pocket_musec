#!/usr/bin/env python3
"""
Complete embeddings generation for all remaining standards and objectives
Optimized for production use with progress tracking and error recovery
"""

import sys
import os
import time
import logging
from typing import List, Dict, Tuple

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.llm.embeddings import StandardsEmbedder, StandardsEmbeddings
from backend.repositories.standards_repository import StandardsRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_remaining_standards(
    repo: StandardsRepository, embeddings_manager: StandardsEmbeddings
) -> List:
    """Get standards that haven't been embedded yet"""
    all_standards = repo.get_all_standards()
    embedded_standard_ids = set()

    # Get IDs of already embedded standards
    conn = embeddings_manager.db_manager.get_connection()
    try:
        cursor = conn.execute("SELECT standard_id FROM standard_embeddings")
        embedded_standard_ids = {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()

    # Filter out already embedded standards
    remaining_standards = [
        s for s in all_standards if s.standard_id not in embedded_standard_ids
    ]
    return remaining_standards


def embed_standards_by_grade(
    target_grades: List[str],
    batch_size: int = 3,
    delay_between_batches: float = 2.0,
    delay_between_standards: float = 0.5,
) -> Dict[str, int]:
    """Embed standards for specific grades with optimized processing"""

    repo = StandardsRepository()
    embeddings_manager = StandardsEmbeddings()
    embedder = StandardsEmbedder()

    print(f"🎵 Complete Embeddings Generation")
    print("=" * 50)
    print(f"Target grades: {target_grades}")
    print(f"Batch size: {batch_size}")
    print(f"Delay between batches: {delay_between_batches}s")
    print(f"Delay between standards: {delay_between_standards}s")

    # Get remaining standards
    remaining_standards = get_remaining_standards(repo, embeddings_manager)
    print(f"📊 Remaining standards to embed: {len(remaining_standards)}")

    # Filter by target grades
    target_standards = [
        s for s in remaining_standards if s.grade_level in target_grades
    ]
    print(f"📊 Target standards for this run: {len(target_standards)}")

    if not target_standards:
        print("✅ No standards to embed for target grades")
        return {"success": 0, "failed": 0, "skipped": 0}

    # Group by grade for progress tracking
    standards_by_grade = {}
    for standard in target_standards:
        grade = standard.grade_level
        if grade not in standards_by_grade:
            standards_by_grade[grade] = []
        standards_by_grade[grade].append(standard)

    stats = {"success": 0, "failed": 0, "skipped": 0}
    start_time = time.time()

    for grade, standards in standards_by_grade.items():
        print(f"\\n📚 Processing {grade}: {len(standards)} standards")
        print("-" * 40)

        grade_start_time = time.time()

        for i in range(0, len(standards), batch_size):
            batch = standards[i : i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(standards) - 1) // batch_size + 1

            print(f"  📦 Batch {batch_num}/{total_batches} ({len(batch)} standards)")

            for standard in batch:
                try:
                    # Check if already exists (race condition protection)
                    existing = embeddings_manager.get_standard_embedding(
                        standard.standard_id
                    )
                    if existing:
                        stats["skipped"] += 1
                        print(
                            f"    ⏭️  Skipping {standard.standard_id} (already exists)"
                        )
                        continue

                    # Get objectives for this standard
                    objectives = repo.get_objectives_for_standard(standard.standard_id)

                    # Generate embedding
                    print(f"    🔄 Generating embedding for {standard.standard_id}...")
                    embedding = embeddings_manager.generate_standard_embedding(
                        standard, objectives
                    )

                    # Store embedding
                    embeddings_manager.store_standard_embedding(
                        standard, objectives, embedding
                    )

                    stats["success"] += 1
                    print(
                        f"    ✅ Embedded {standard.standard_id} ({stats['success']}/{len(target_standards)})"
                    )

                    # Brief pause to avoid rate limiting
                    if delay_between_standards > 0:
                        time.sleep(delay_between_standards)

                except Exception as e:
                    logger.error(f"    ❌ Failed to embed {standard.standard_id}: {e}")
                    stats["failed"] += 1

            # Longer pause between batches
            if i + batch_size < len(standards) and delay_between_batches > 0:
                print(f"    ⏸️  Pausing between batches...")
                time.sleep(delay_between_batches)

        grade_elapsed = time.time() - grade_start_time
        print(f"  ✅ {grade} completed in {grade_elapsed:.1f}s")

    total_elapsed = time.time() - start_time

    print(f"\\n🎉 Embedding Generation Complete!")
    print(f"⏱️  Total time: {total_elapsed:.1f}s")
    print(f"📊 Final stats: {stats}")

    # Verify results
    final_stats = embeddings_manager.get_embedding_stats()
    print(f"📈 Database stats: {final_stats}")

    return stats


def embed_all_objectives(
    batch_size: int = 5, delay_between_batches: float = 1.0
) -> Dict[str, int]:
    """Generate embeddings for all objectives"""

    repo = StandardsRepository()
    embeddings_manager = StandardsEmbeddings()
    embedder = StandardsEmbedder()

    print(f"\\n🎯 Generating Objective Embeddings")
    print("=" * 50)

    # Get all objectives from all standards
    all_standards = repo.get_all_standards()
    all_objectives = []

    for standard in all_standards:
        objectives = repo.get_objectives_for_standard(standard.standard_id)
        all_objectives.extend(objectives)

    print(f"📊 Total objectives to process: {len(all_objectives)}")

    # Filter out already embedded objectives
    conn = embeddings_manager.db_manager.get_connection()
    try:
        cursor = conn.execute("SELECT objective_id FROM objective_embeddings")
        embedded_objective_ids = {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()

    remaining_objectives = [
        obj for obj in all_objectives if obj.objective_id not in embedded_objective_ids
    ]
    print(f"📊 Remaining objectives to embed: {len(remaining_objectives)}")

    if not remaining_objectives:
        print("✅ All objectives already embedded")
        return {"success": 0, "failed": 0, "skipped": 0}

    stats = {"success": 0, "failed": 0, "skipped": 0}
    start_time = time.time()

    for i in range(0, len(remaining_objectives), batch_size):
        batch = remaining_objectives[i : i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(remaining_objectives) - 1) // batch_size + 1

        print(
            f"  📦 Objective batch {batch_num}/{total_batches} ({len(batch)} objectives)"
        )

        for objective in batch:
            try:
                # Generate embedding
                embedding = embeddings_manager.generate_objective_embedding(objective)

                # Store embedding
                embeddings_manager.store_objective_embedding(objective, embedding)

                stats["success"] += 1
                print(f"    ✅ Embedded {objective.objective_id}")

                # Brief pause
                time.sleep(0.3)

            except Exception as e:
                logger.error(f"    ❌ Failed to embed {objective.objective_id}: {e}")
                stats["failed"] += 1

        # Pause between batches
        if i + batch_size < len(remaining_objectives):
            time.sleep(delay_between_batches)

    elapsed = time.time() - start_time
    print(f"\\n✅ Objective embeddings completed in {elapsed:.1f}s")
    print(f"📊 Objective stats: {stats}")

    # Final verification
    final_stats = embeddings_manager.get_embedding_stats()
    print(f"📈 Final database stats: {final_stats}")

    return stats


def main():
    """Main execution function"""
    print("🚀 Starting Complete Embeddings Generation")
    print("=" * 60)

    # Define remaining grades to process
    remaining_grades = [
        "Third Grade",
        "Fourth Grade",
        "Fifth Grade",
        "Sixth Grade",
        "Seventh Grade",
        "Eighth Grade",
        "Kindergarten",
        "Novice",
        "Developing",
        "Intermediate",
        "Accomplished",
        "Advanced",
    ]

    try:
        # Phase 1: Embed all remaining standards
        print("\\n📚 PHASE 1: Standard Embeddings")
        print("=" * 40)
        standard_stats = embed_standards_by_grade(
            target_grades=remaining_grades,
            batch_size=3,
            delay_between_batches=2.0,
            delay_between_standards=0.5,
        )

        # Phase 2: Embed all objectives
        print("\\n🎯 PHASE 2: Objective Embeddings")
        print("=" * 40)
        objective_stats = embed_all_objectives(batch_size=5, delay_between_batches=1.0)

        # Final summary
        print("\\n🎉 COMPLETE EMBEDDINGS GENERATION SUMMARY")
        print("=" * 60)
        print(
            f"Standards: {standard_stats['success']} success, {standard_stats['failed']} failed, {standard_stats['skipped']} skipped"
        )
        print(
            f"Objectives: {objective_stats['success']} success, {objective_stats['failed']} failed, {objective_stats['skipped']} skipped"
        )

        total_success = standard_stats["success"] + objective_stats["success"]
        total_failed = standard_stats["failed"] + objective_stats["failed"]

        print(f"\\nOverall: {total_success} success, {total_failed} failed")

        if total_failed == 0:
            print("✅ ALL EMBEDDINGS GENERATED SUCCESSFULLY!")
        else:
            print(f"⚠️  Completed with {total_failed} failures")

        return total_failed == 0

    except KeyboardInterrupt:
        print("\\n⏹️  Embedding generation interrupted by user")
        return False
    except Exception as e:
        logger.error(f"❌ Embedding generation failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
