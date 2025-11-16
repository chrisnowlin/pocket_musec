#!/usr/bin/env python3
"""
Quick script to check embeddings generation progress
"""

import sqlite3
import sys


def check_progress():
    """Check current embeddings progress"""
    conn = sqlite3.connect("pocketmusec.db")

    # Get counts
    cursor = conn.execute("SELECT COUNT(*) FROM objective_embeddings")
    objective_count = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(*) FROM standard_embeddings")
    standard_count = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(*) FROM objectives")
    total_objectives = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(*) FROM standards")
    total_standards = cursor.fetchone()[0]

    # Get latest objective embeddings
    cursor = conn.execute(
        "SELECT objective_id FROM objective_embeddings ORDER BY rowid DESC LIMIT 5"
    )
    latest_objectives = [row[0] for row in cursor.fetchall()]

    conn.close()

    print("📊 Embeddings Progress Report")
    print("=" * 35)
    print(
        f"Standard Embeddings: {standard_count}/{total_standards} ({standard_count / total_standards * 100:.1f}%)"
    )
    print(
        f"Objective Embeddings: {objective_count}/{total_objectives} ({objective_count / total_objectives * 100:.1f}%)"
    )

    if latest_objectives:
        print(f"\nLatest objective embeddings:")
        for obj_id in latest_objectives:
            print(f"  ✅ {obj_id}")

    if objective_count < total_objectives:
        remaining = total_objectives - objective_count
        print(f"\n🔄 Remaining objectives: {remaining}")
        print("💡 Background generation should be running...")
    else:
        print("\n🎉 All embeddings complete!")


if __name__ == "__main__":
    check_progress()
