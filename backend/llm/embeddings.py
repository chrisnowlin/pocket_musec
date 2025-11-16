"""Embeddings generation and management for standards documents"""

import sqlite3
import json
import numpy as np
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass

from backend.llm.chutes_client import ChutesClient
from backend.repositories.database import DatabaseManager
from backend.repositories.models import Standard, Objective

logger = logging.getLogger(__name__)


@dataclass
class EmbeddedStandard:
    """Standard with its embedding vector"""

    standard_id: str
    grade_level: str
    strand_code: str
    strand_name: str
    standard_text: str
    embedding: List[float]
    objectives_text: str


@dataclass
class EmbeddedObjective:
    """Objective with its embedding vector"""

    objective_id: str
    standard_id: str
    objective_text: str
    embedding: List[float]


class StandardsEmbeddings:
    """Manage embeddings for standards and objectives"""

    def __init__(self, client: Optional[ChutesClient] = None):
        self.client = client or ChutesClient()
        self.db_manager = DatabaseManager()
        from config import config

        self.prepared_texts_dir = Path(config.paths.prepared_texts_dir)
        self.prepared_texts_dir.mkdir(parents=True, exist_ok=True)
        (self.prepared_texts_dir / "standards").mkdir(exist_ok=True)
        (self.prepared_texts_dir / "objectives").mkdir(exist_ok=True)
        self._init_embeddings_table()

    def _init_embeddings_table(self):
        """Initialize embeddings table in database with proper transaction management"""
        conn = self.db_manager.get_connection()
        try:
            # Start explicit transaction with immediate locking
            conn.execute("BEGIN IMMEDIATE")

            logger.info(
                "Initializing embeddings tables with proper transaction management"
            )

            conn.execute("""
                CREATE TABLE IF NOT EXISTS standard_embeddings (
                    standard_id TEXT PRIMARY KEY,
                    grade_level TEXT,
                    strand_code TEXT,
                    strand_name TEXT,
                    standard_text TEXT,
                    objectives_text TEXT,
                    embedding_vector BLOB,
                    embedding_dimension INTEGER,
                    file_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES uploaded_files(file_id) ON DELETE SET NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS objective_embeddings (
                    objective_id TEXT PRIMARY KEY,
                    standard_id TEXT,
                    objective_text TEXT,
                    embedding_vector BLOB,
                    embedding_dimension INTEGER,
                    file_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES uploaded_files(file_id) ON DELETE SET NULL
                )
            """)

            # Create indexes for efficient search
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_standard_embeddings_grade
                ON standard_embeddings(grade_level)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_standard_embeddings_strand
                ON standard_embeddings(strand_code)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_objective_embeddings_standard
                ON objective_embeddings(standard_id)
            """)

            # Create file_id indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_standard_embeddings_file_id
                ON standard_embeddings(file_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_objective_embeddings_file_id
                ON objective_embeddings(file_id)
            """)

            # Commit the transaction
            conn.commit()
            logger.info("Successfully initialized embeddings tables")

        except (sqlite3.Error, sqlite3.DatabaseError, Exception) as e:
            # Rollback on any error
            conn.rollback()
            logger.error(f"Failed to initialize embeddings tables, rolled back: {e}")
            raise Exception(f"Failed to initialize embeddings tables: {str(e)}")
        finally:
            conn.close()

    def _serialize_embedding(self, embedding: List[float]) -> bytes:
        """Serialize embedding vector to bytes for storage"""
        return np.array(embedding, dtype=np.float32).tobytes()

    def _deserialize_embedding(self, embedding_bytes: bytes) -> List[float]:
        """Deserialize embedding vector from bytes"""
        return np.frombuffer(embedding_bytes, dtype=np.float32).tolist()

    def _prepare_standard_text(
        self, standard: Standard, objectives: List[Objective]
    ) -> str:
        """Prepare text for embedding by combining standard and objectives"""
        objectives_text = " ".join([obj.objective_text for obj in objectives])

        prepared_text = f"""
        Grade Level: {standard.grade_level}
        Strand: {standard.strand_name} ({standard.strand_code})
        Standard: {standard.standard_text}
        Objectives: {objectives_text}
        """.strip()

        # Save prepared text to file
        self._save_prepared_standard_text(standard.standard_id, prepared_text)

        return prepared_text

    def generate_standard_embedding(
        self, standard: Standard, objectives: List[Objective]
    ) -> List[float]:
        """Generate embedding for a standard with its objectives"""
        text_to_embed = self._prepare_standard_text(standard, objectives)

        try:
            embedding = self.client.create_embedding(text_to_embed)
            logger.info(f"Generated embedding for standard {standard.standard_id}")
            return embedding
        except Exception as e:
            logger.error(
                f"Failed to generate embedding for standard {standard.standard_id}: {str(e)}"
            )
            raise

    def generate_objective_embedding(self, objective: Objective) -> List[float]:
        """Generate embedding for an objective"""
        try:
            # Save prepared text to file
            self._save_prepared_objective_text(
                objective.objective_id, objective.objective_text
            )

            embedding = self.client.create_embedding(objective.objective_text)
            logger.info(f"Generated embedding for objective {objective.objective_id}")
            return embedding
        except Exception as e:
            logger.error(
                f"Failed to generate embedding for objective {objective.objective_id}: {str(e)}"
            )
            raise

    def store_standard_embedding(
        self,
        standard: Standard,
        objectives: List[Objective],
        embedding: List[float],
        file_id: Optional[str] = None,
    ):
        """Store embedding for a standard with proper transaction management"""
        objectives_text = " ".join([obj.objective_text for obj in objectives])
        embedding_bytes = self._serialize_embedding(embedding)

        conn = self.db_manager.get_connection()
        try:
            # Start explicit transaction with immediate locking
            conn.execute("BEGIN IMMEDIATE")

            logger.debug(f"Storing embedding for standard {standard.standard_id}")

            conn.execute(
                """
                INSERT OR REPLACE INTO standard_embeddings
                (standard_id, grade_level, strand_code, strand_name, standard_text,
                 objectives_text, embedding_vector, embedding_dimension, file_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    standard.standard_id,
                    standard.grade_level,
                    standard.strand_code,
                    standard.strand_name,
                    standard.standard_text,
                    objectives_text,
                    embedding_bytes,
                    len(embedding),
                    file_id,
                ),
            )

            # Commit the transaction
            conn.commit()
            logger.debug(
                f"Successfully stored embedding for standard {standard.standard_id}"
            )

        except (sqlite3.Error, sqlite3.DatabaseError, Exception) as e:
            # Rollback on any error
            conn.rollback()
            logger.error(
                f"Failed to store embedding for standard {standard.standard_id}, rolled back: {e}"
            )
            raise Exception(f"Failed to store standard embedding: {str(e)}")
        finally:
            conn.close()

    def store_objective_embedding(
        self,
        objective: Objective,
        embedding: List[float],
        file_id: Optional[str] = None,
    ):
        """Store embedding for an objective with proper transaction management"""
        embedding_bytes = self._serialize_embedding(embedding)

        conn = self.db_manager.get_connection()
        try:
            # Start explicit transaction with immediate locking
            conn.execute("BEGIN IMMEDIATE")

            logger.debug(f"Storing embedding for objective {objective.objective_id}")

            conn.execute(
                """
                INSERT OR REPLACE INTO objective_embeddings
                (objective_id, standard_id, objective_text, embedding_vector, embedding_dimension, file_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    objective.objective_id,
                    objective.standard_id,
                    objective.objective_text,
                    embedding_bytes,
                    len(embedding),
                    file_id,
                ),
            )

            # Commit the transaction
            conn.commit()
            logger.debug(
                f"Successfully stored embedding for objective {objective.objective_id}"
            )

        except (sqlite3.Error, sqlite3.DatabaseError, Exception) as e:
            # Rollback on any error
            conn.rollback()
            logger.error(
                f"Failed to store embedding for objective {objective.objective_id}, rolled back: {e}"
            )
            raise Exception(f"Failed to store objective embedding: {str(e)}")
        finally:
            conn.close()

    def get_standard_embedding(self, standard_id: str) -> Optional[EmbeddedStandard]:
        """Retrieve embedding for a standard"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT standard_id, grade_level, strand_code, strand_name,
                       standard_text, objectives_text, embedding_vector, file_id
                FROM standard_embeddings
                WHERE standard_id = ?
            """,
                (standard_id,),
            )

            row = cursor.fetchone()
            if row:
                embedding = self._deserialize_embedding(row[6])
                return EmbeddedStandard(
                    standard_id=row[0],
                    grade_level=row[1],
                    strand_code=row[2],
                    strand_name=row[3],
                    standard_text=row[4],
                    embedding=embedding,
                    objectives_text=row[5],
                )
        finally:
            conn.close()
        return None

    def get_standard_embedding_with_file(
        self, standard_id: str
    ) -> Optional[Tuple[EmbeddedStandard, Optional[str]]]:
        """Retrieve embedding for a standard with file_id"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT standard_id, grade_level, strand_code, strand_name,
                       standard_text, objectives_text, embedding_vector, file_id
                FROM standard_embeddings
                WHERE standard_id = ?
            """,
                (standard_id,),
            )

            row = cursor.fetchone()
            if row:
                embedding = self._deserialize_embedding(row[6])
                embedded_standard = EmbeddedStandard(
                    standard_id=row[0],
                    grade_level=row[1],
                    strand_code=row[2],
                    strand_name=row[3],
                    standard_text=row[4],
                    embedding=embedding,
                    objectives_text=row[5],
                )
                return embedded_standard, row[7]  # file_id
        finally:
            conn.close()
        return None

    def get_objective_embedding(self, objective_id: str) -> Optional[EmbeddedObjective]:
        """Retrieve embedding for an objective"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT objective_id, standard_id, objective_text, embedding_vector
                FROM objective_embeddings
                WHERE objective_id = ?
            """,
                (objective_id,),
            )

            row = cursor.fetchone()
            if row:
                embedding = self._deserialize_embedding(row[3])
                return EmbeddedObjective(
                    objective_id=row[0],
                    standard_id=row[1],
                    objective_text=row[2],
                    embedding=embedding,
                )
        finally:
            conn.close()
        return None

    def get_objective_embedding_with_file(
        self, objective_id: str
    ) -> Optional[Tuple[EmbeddedObjective, Optional[str]]]:
        """Retrieve embedding for an objective with file_id"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT objective_id, standard_id, objective_text, embedding_vector, file_id
                FROM objective_embeddings
                WHERE objective_id = ?
            """,
                (objective_id,),
            )

            row = cursor.fetchone()
            if row:
                embedding = self._deserialize_embedding(row[3])
                embedded_objective = EmbeddedObjective(
                    objective_id=row[0],
                    standard_id=row[1],
                    objective_text=row[2],
                    embedding=embedding,
                )
                return embedded_objective, row[4]  # file_id
        finally:
            conn.close()
        return None

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def search_similar_standards(
        self,
        query_embedding: List[float],
        grade_level: Optional[str] = None,
        strand_code: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.5,
    ) -> List[Tuple[EmbeddedStandard, float]]:
        """Search for similar standards using embedding similarity"""
        conn = self.db_manager.get_connection()
        try:
            # Build query with optional filters
            query = """
                SELECT standard_id, grade_level, strand_code, strand_name, 
                       standard_text, objectives_text, embedding_vector
                FROM standard_embeddings
                WHERE 1=1
            """
            params = []

            if grade_level:
                query += " AND grade_level = ?"
                params.append(grade_level)

            if strand_code:
                query += " AND strand_code = ?"
                params.append(strand_code)

            cursor = conn.execute(query, params)
            results = []

            for row in cursor.fetchall():
                stored_embedding = self._deserialize_embedding(row[6])
                similarity = self.cosine_similarity(query_embedding, stored_embedding)

                if similarity >= similarity_threshold:
                    embedded_standard = EmbeddedStandard(
                        standard_id=row[0],
                        grade_level=row[1],
                        strand_code=row[2],
                        strand_name=row[3],
                        standard_text=row[4],
                        embedding=stored_embedding,
                        objectives_text=row[5],
                    )
                    results.append((embedded_standard, similarity))

            # Sort by similarity (descending) and limit results
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]
        finally:
            conn.close()

    def search_similar_objectives(
        self,
        query_embedding: List[float],
        standard_id: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.5,
    ) -> List[Tuple[EmbeddedObjective, float]]:
        """Search for similar objectives using embedding similarity"""
        conn = self.db_manager.get_connection()
        try:
            query = """
                SELECT objective_id, standard_id, objective_text, embedding_vector
                FROM objective_embeddings
                WHERE 1=1
            """
            params = []

            if standard_id:
                query += " AND standard_id = ?"
                params.append(standard_id)

            cursor = conn.execute(query, params)
            results = []

            for row in cursor.fetchall():
                stored_embedding = self._deserialize_embedding(row[3])
                similarity = self.cosine_similarity(query_embedding, stored_embedding)

                if similarity >= similarity_threshold:
                    embedded_objective = EmbeddedObjective(
                        objective_id=row[0],
                        standard_id=row[1],
                        objective_text=row[2],
                        embedding=stored_embedding,
                    )
                    results.append((embedded_objective, similarity))

            # Sort by similarity (descending) and limit results
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]
        finally:
            conn.close()

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a search query"""
        try:
            embedding = self.client.create_embedding(query)
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding for query: {str(e)}")
            raise

    def get_embedding_stats(self) -> Dict[str, int]:
        """Get statistics about embeddings in the database"""
        conn = self.db_manager.get_connection()
        try:
            standard_count = conn.execute(
                "SELECT COUNT(*) FROM standard_embeddings"
            ).fetchone()[0]

            objective_count = conn.execute(
                "SELECT COUNT(*) FROM objective_embeddings"
            ).fetchone()[0]

            # Get embedding dimension (should be consistent)
            dimension = conn.execute(
                "SELECT embedding_dimension FROM standard_embeddings LIMIT 1"
            ).fetchone()

            return {
                "standard_embeddings": standard_count,
                "objective_embeddings": objective_count,
                "embedding_dimension": dimension[0] if dimension else 0,
            }
        finally:
            conn.close()

    def _save_prepared_standard_text(self, standard_id: str, prepared_text: str):
        """Save prepared standard text to file"""
        try:
            file_path = self.prepared_texts_dir / "standards" / f"{standard_id}.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(prepared_text)
            logger.debug(
                f"Saved prepared text for standard {standard_id} to {file_path}"
            )
        except Exception as e:
            logger.warning(
                f"Failed to save prepared text for standard {standard_id}: {str(e)}"
            )

    def _save_prepared_objective_text(self, objective_id: str, prepared_text: str):
        """Save prepared objective text to file"""
        try:
            file_path = self.prepared_texts_dir / "objectives" / f"{objective_id}.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(prepared_text)
            logger.debug(
                f"Saved prepared text for objective {objective_id} to {file_path}"
            )
        except Exception as e:
            logger.warning(
                f"Failed to save prepared text for objective {objective_id}: {str(e)}"
            )

    def get_prepared_standard_text(self, standard_id: str) -> Optional[str]:
        """Read prepared standard text from file"""
        try:
            file_path = self.prepared_texts_dir / "standards" / f"{standard_id}.txt"
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            return None
        except Exception as e:
            logger.error(
                f"Failed to read prepared text for standard {standard_id}: {str(e)}"
            )
            return None

    def get_prepared_objective_text(self, objective_id: str) -> Optional[str]:
        """Read prepared objective text from file"""
        try:
            file_path = self.prepared_texts_dir / "objectives" / f"{objective_id}.txt"
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            return None
        except Exception as e:
            logger.error(
                f"Failed to read prepared text for objective {objective_id}: {str(e)}"
            )
            return None

    def list_prepared_texts(self) -> Dict[str, List[str]]:
        """List all prepared text files"""
        result = {"standards": [], "objectives": []}

        try:
            standards_dir = self.prepared_texts_dir / "standards"
            if standards_dir.exists():
                result["standards"] = [f.stem for f in standards_dir.glob("*.txt")]

            objectives_dir = self.prepared_texts_dir / "objectives"
            if objectives_dir.exists():
                result["objectives"] = [f.stem for f in objectives_dir.glob("*.txt")]
        except Exception as e:
            logger.error(f"Failed to list prepared texts: {str(e)}")

        return result

    def delete_all_embeddings(self):
        """Delete all embeddings from the database with proper transaction management and audit logging"""
        conn = self.db_manager.get_connection()
        try:
            # Start explicit transaction with immediate locking
            conn.execute("BEGIN IMMEDIATE")

            logger.info("AUDIT: Starting deletion of all embeddings from database")

            # Count records before deletion for audit trail
            standard_count = conn.execute(
                "SELECT COUNT(*) FROM standard_embeddings"
            ).fetchone()[0]
            objective_count = conn.execute(
                "SELECT COUNT(*) FROM objective_embeddings"
            ).fetchone()[0]

            logger.info(
                f"AUDIT: About to delete {standard_count} standard embeddings and {objective_count} objective embeddings"
            )

            conn.execute("DELETE FROM standard_embeddings")
            conn.execute("DELETE FROM objective_embeddings")

            # Commit the transaction
            conn.commit()
            logger.info(
                f"AUDIT: Successfully deleted all embeddings - {standard_count} standard, {objective_count} objective"
            )

        except (sqlite3.Error, sqlite3.DatabaseError, Exception) as e:
            # Rollback on any error
            conn.rollback()
            logger.error(f"AUDIT: Failed to delete all embeddings, rolled back: {e}")
            raise Exception(f"Failed to delete all embeddings: {str(e)}")
        finally:
            conn.close()

    def delete_all_prepared_texts(self):
        """Delete all prepared text files"""
        try:
            standards_dir = self.prepared_texts_dir / "standards"
            objectives_dir = self.prepared_texts_dir / "objectives"

            for file_path in standards_dir.glob("*.txt"):
                file_path.unlink()

            for file_path in objectives_dir.glob("*.txt"):
                file_path.unlink()

            logger.info("All prepared text files deleted")
        except Exception as e:
            logger.error(f"Failed to delete prepared text files: {str(e)}")
            raise


class StandardsEmbedder:
    """Utility class to batch generate embeddings for all standards"""

    def __init__(self):
        self.embeddings_manager = StandardsEmbeddings()
        self.client = ChutesClient()

    def embed_all_standards(
        self, batch_size: int = 10, file_id: Optional[str] = None
    ) -> Dict[str, int]:
        """Generate embeddings for all standards in the database"""
        from backend.repositories.standards_repository import StandardsRepository

        repository = StandardsRepository()
        stats = {"success": 0, "failed": 0, "skipped": 0}

        # Get all standards
        standards = repository.get_all_standards()

        logger.info(f"Starting embedding generation for {len(standards)} standards")

        for i, standard in enumerate(standards):
            try:
                # Check if embedding already exists
                existing = self.embeddings_manager.get_standard_embedding(
                    standard.standard_id
                )
                if existing:
                    stats["skipped"] += 1
                    logger.debug(
                        f"Skipping standard {standard.standard_id} - already embedded"
                    )
                    continue

                # Get objectives for this standard
                objectives = repository.get_objectives_for_standard(
                    standard.standard_id
                )

                # Generate embedding
                embedding = self.embeddings_manager.generate_standard_embedding(
                    standard, objectives
                )

                # Store embedding with file_id
                self.embeddings_manager.store_standard_embedding(
                    standard, objectives, embedding, file_id
                )

                stats["success"] += 1
                logger.info(
                    f"Embedded standard {standard.standard_id} ({i + 1}/{len(standards)})"
                )

                # Embed objectives as well
                for objective in objectives:
                    try:
                        obj_embedding = (
                            self.embeddings_manager.generate_objective_embedding(
                                objective
                            )
                        )
                        self.embeddings_manager.store_objective_embedding(
                            objective, obj_embedding, file_id
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to embed objective {objective.objective_id}: {str(e)}"
                        )
                        stats["failed"] += 1

            except Exception as e:
                logger.error(
                    f"Failed to embed standard {standard.standard_id}: {str(e)}"
                )
                stats["failed"] += 1

        logger.info(f"Embedding generation complete: {stats}")
        return stats

    def embed_standards_from_file(self, file_id: str) -> Dict[str, int]:
        """Generate embeddings for standards from a specific file"""
        from backend.repositories.standards_repository import StandardsRepository

        repository = StandardsRepository()
        stats = {"success": 0, "failed": 0, "skipped": 0}

        # Get standards associated with this file
        standards = (
            repository.get_standards_by_file_id(file_id)
            if hasattr(repository, "get_standards_by_file_id")
            else []
        )

        if not standards:
            logger.warning(f"No standards found for file_id: {file_id}")
            return stats

        logger.info(
            f"Starting embedding generation for {len(standards)} standards from file {file_id}"
        )

        for i, standard in enumerate(standards):
            try:
                # Check if embedding already exists
                existing = self.embeddings_manager.get_standard_embedding(
                    standard.standard_id
                )
                if existing:
                    stats["skipped"] += 1
                    logger.debug(
                        f"Skipping standard {standard.standard_id} - already embedded"
                    )
                    continue

                # Get objectives for this standard
                objectives = repository.get_objectives_for_standard(
                    standard.standard_id
                )

                # Generate embedding
                embedding = self.embeddings_manager.generate_standard_embedding(
                    standard, objectives
                )

                # Store embedding with file_id
                self.embeddings_manager.store_standard_embedding(
                    standard, objectives, embedding, file_id
                )

                stats["success"] += 1
                logger.info(
                    f"Embedded standard {standard.standard_id} ({i + 1}/{len(standards)}) from file {file_id}"
                )

                # Embed objectives as well
                for objective in objectives:
                    try:
                        obj_embedding = (
                            self.embeddings_manager.generate_objective_embedding(
                                objective
                            )
                        )
                        self.embeddings_manager.store_objective_embedding(
                            objective, obj_embedding, file_id
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to embed objective {objective.objective_id}: {str(e)}"
                        )
                        stats["failed"] += 1

            except Exception as e:
                logger.error(
                    f"Failed to embed standard {standard.standard_id}: {str(e)}"
                )
                stats["failed"] += 1

        logger.info(f"Embedding generation complete for file {file_id}: {stats}")
        return stats
