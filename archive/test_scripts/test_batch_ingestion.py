#!/usr/bin/env python3
"""Test batch ingestion of all NC Music Standards documents"""

import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from backend.ingestion.standards_parser import NCStandardsParser
from backend.repositories.database import DatabaseManager

def test_batch_ingestion():
    """Test ingesting all standards documents"""
    
    docs_dir = Path("NC Music Standards and Resources")
    pdf_files = sorted(docs_dir.glob("*.pdf"))
    
    # Filter to just the unpacking documents (the ones with actual standards)
    unpacking_docs = [
        f for f in pdf_files 
        if "Unpacking" in f.name and "Google Docs" in f.name
    ]
    
    logger.info(f"Found {len(unpacking_docs)} unpacking documents to process")
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize_database()
    
    # Clear existing data
    logger.info("Clearing existing standards...")
    with db_manager.get_connection() as conn:
        conn.execute("DELETE FROM objectives")
        conn.execute("DELETE FROM standards")
        conn.commit()
    
    # Initialize parser (hybrid mode by default)
    parser = NCStandardsParser(use_vision=False)
    
    total_standards = 0
    total_objectives = 0
    failed_docs = []
    
    start_time = time.time()
    
    for i, pdf_file in enumerate(unpacking_docs, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {i}/{len(unpacking_docs)}: {pdf_file.name}")
        logger.info(f"{'='*60}")
        
        try:
            doc_start = time.time()
            
            # Parse document
            parsed_standards = parser.parse_standards_document(str(pdf_file))
            
            # Convert to models
            standards, objectives = parser.normalize_to_models(pdf_file.name)
            
            # Save to database
            with db_manager.get_connection() as conn:
                for standard in standards:
                    conn.execute(
                        """INSERT OR REPLACE INTO standards 
                           (standard_id, grade_level, strand_code, strand_name, 
                            strand_description, standard_text, source_document, 
                            ingestion_date, version)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            standard.standard_id,
                            standard.grade_level,
                            standard.strand_code,
                            standard.strand_name,
                            standard.strand_description,
                            standard.standard_text,
                            standard.source_document,
                            standard.ingestion_date,
                            standard.version
                        )
                    )
                
                for objective in objectives:
                    conn.execute(
                        """INSERT OR REPLACE INTO objectives 
                           (objective_id, standard_id, objective_text)
                           VALUES (?, ?, ?)""",
                        (objective.objective_id, objective.standard_id, objective.objective_text)
                    )
                
                conn.commit()
            
            doc_elapsed = time.time() - doc_start
            
            logger.info(f"✓ Processed in {doc_elapsed:.2f}s")
            logger.info(f"  Standards: {len(standards)}")
            logger.info(f"  Objectives: {len(objectives)}")
            
            total_standards += len(standards)
            total_objectives += len(objectives)
            
        except Exception as e:
            logger.error(f"✗ Failed to process {pdf_file.name}: {e}")
            import traceback
            traceback.print_exc()
            failed_docs.append(pdf_file.name)
            continue
    
    total_elapsed = time.time() - start_time
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("BATCH INGESTION SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total documents processed: {len(unpacking_docs) - len(failed_docs)}/{len(unpacking_docs)}")
    logger.info(f"Total standards ingested: {total_standards}")
    logger.info(f"Total objectives ingested: {total_objectives}")
    logger.info(f"Total time: {total_elapsed:.2f}s ({total_elapsed/60:.1f} minutes)")
    logger.info(f"Average per document: {total_elapsed/len(unpacking_docs):.2f}s")
    
    if failed_docs:
        logger.info(f"\nFailed documents ({len(failed_docs)}):")
        for doc in failed_docs:
            logger.info(f"  - {doc}")
    else:
        logger.info("\n✓ All documents processed successfully!")
    
    # Verify database
    with db_manager.get_connection() as conn:
        standards_count = conn.execute("SELECT COUNT(*) FROM standards").fetchone()[0]
        objectives_count = conn.execute("SELECT COUNT(*) FROM objectives").fetchone()[0]
        
        logger.info(f"\nDatabase verification:")
        logger.info(f"  Standards in DB: {standards_count}")
        logger.info(f"  Objectives in DB: {objectives_count}")

if __name__ == "__main__":
    test_batch_ingestion()
