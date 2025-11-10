"""Embeddings generation and management for standards documents"""

import sqlite3
import json
import numpy as np
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
        self._init_embeddings_table()
    
    def _init_embeddings_table(self):
        """Initialize embeddings table in database"""
        conn = self.db_manager.get_connection()
        try:
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS objective_embeddings (
                    objective_id TEXT PRIMARY KEY,
                    standard_id TEXT,
                    objective_text TEXT,
                    embedding_vector BLOB,
                    embedding_dimension INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            
            conn.commit()
        finally:
            conn.close()
    
    def _serialize_embedding(self, embedding: List[float]) -> bytes:
        """Serialize embedding vector to bytes for storage"""
        return np.array(embedding, dtype=np.float32).tobytes()
    
    def _deserialize_embedding(self, embedding_bytes: bytes) -> List[float]:
        """Deserialize embedding vector from bytes"""
        return np.frombuffer(embedding_bytes, dtype=np.float32).tolist()
    
    def _prepare_standard_text(self, standard: Standard, objectives: List[Objective]) -> str:
        """Prepare text for embedding by combining standard and objectives"""
        objectives_text = " ".join([obj.objective_text for obj in objectives])
        
        return f"""
        Grade Level: {standard.grade_level}
        Strand: {standard.strand_name} ({standard.strand_code})
        Standard: {standard.standard_text}
        Objectives: {objectives_text}
        """.strip()
    
    def generate_standard_embedding(self, standard: Standard, objectives: List[Objective]) -> List[float]:
        """Generate embedding for a standard with its objectives"""
        text_to_embed = self._prepare_standard_text(standard, objectives)
        
        try:
            embedding = self.client.create_embedding(text_to_embed)
            logger.info(f"Generated embedding for standard {standard.standard_id}")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding for standard {standard.standard_id}: {str(e)}")
            raise
    
    def generate_objective_embedding(self, objective: Objective) -> List[float]:
        """Generate embedding for an objective"""
        try:
            embedding = self.client.create_embedding(objective.objective_text)
            logger.info(f"Generated embedding for objective {objective.objective_id}")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding for objective {objective.objective_id}: {str(e)}")
            raise
    
    def store_standard_embedding(self, standard: Standard, objectives: List[Objective], embedding: List[float]):
        """Store embedding for a standard"""
        objectives_text = " ".join([obj.objective_text for obj in objectives])
        embedding_bytes = self._serialize_embedding(embedding)
        
        conn = self.db_manager.get_connection()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO standard_embeddings
                (standard_id, grade_level, strand_code, strand_name, standard_text,
                 objectives_text, embedding_vector, embedding_dimension)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                standard.standard_id,
                standard.grade_level,
                standard.strand_code,
                standard.strand_name,
                standard.standard_text,
                objectives_text,
                embedding_bytes,
                len(embedding)
            ))
            conn.commit()
        finally:
            conn.close()
    
    def store_objective_embedding(self, objective: Objective, embedding: List[float]):
        """Store embedding for an objective"""
        embedding_bytes = self._serialize_embedding(embedding)
        
        conn = self.db_manager.get_connection()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO objective_embeddings
                (objective_id, standard_id, objective_text, embedding_vector, embedding_dimension)
                VALUES (?, ?, ?, ?, ?)
            """, (
                objective.objective_id,
                objective.standard_id,
                objective.objective_text,
                embedding_bytes,
                len(embedding)
            ))
            conn.commit()
        finally:
            conn.close()
    
    def get_standard_embedding(self, standard_id: str) -> Optional[EmbeddedStandard]:
        """Retrieve embedding for a standard"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                SELECT standard_id, grade_level, strand_code, strand_name, 
                       standard_text, objectives_text, embedding_vector
                FROM standard_embeddings 
                WHERE standard_id = ?
            """, (standard_id,))
            
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
                    objectives_text=row[5]
                )
        finally:
            conn.close()
        return None
    
    def get_objective_embedding(self, objective_id: str) -> Optional[EmbeddedObjective]:
        """Retrieve embedding for an objective"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                SELECT objective_id, standard_id, objective_text, embedding_vector
                FROM objective_embeddings 
                WHERE objective_id = ?
            """, (objective_id,))
            
            row = cursor.fetchone()
            if row:
                embedding = self._deserialize_embedding(row[3])
                return EmbeddedObjective(
                    objective_id=row[0],
                    standard_id=row[1],
                    objective_text=row[2],
                    embedding=embedding
                )
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
        similarity_threshold: float = 0.5
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
                        objectives_text=row[5]
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
        similarity_threshold: float = 0.5
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
                        embedding=stored_embedding
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
                "embedding_dimension": dimension[0] if dimension else 0
            }
        finally:
            conn.close()
    
    def delete_all_embeddings(self):
        """Delete all embeddings from the database"""
        conn = self.db_manager.get_connection()
        try:
            conn.execute("DELETE FROM standard_embeddings")
            conn.execute("DELETE FROM objective_embeddings")
            conn.commit()
            logger.info("All embeddings deleted from database")
        finally:
            conn.close()


class StandardsEmbedder:
    """Utility class to batch generate embeddings for all standards"""
    
    def __init__(self):
        self.embeddings_manager = StandardsEmbeddings()
        self.client = ChutesClient()
    
    def embed_all_standards(self, batch_size: int = 10) -> Dict[str, int]:
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
                existing = self.embeddings_manager.get_standard_embedding(standard.standard_id)
                if existing:
                    stats["skipped"] += 1
                    logger.debug(f"Skipping standard {standard.standard_id} - already embedded")
                    continue
                
                # Get objectives for this standard
                objectives = repository.get_objectives_for_standard(standard.standard_id)
                
                # Generate embedding
                embedding = self.embeddings_manager.generate_standard_embedding(
                    standard, objectives
                )
                
                # Store embedding
                self.embeddings_manager.store_standard_embedding(
                    standard, objectives, embedding
                )
                
                stats["success"] += 1
                logger.info(f"Embedded standard {standard.standard_id} ({i+1}/{len(standards)})")
                
                # Embed objectives as well
                for objective in objectives:
                    try:
                        obj_embedding = self.embeddings_manager.generate_objective_embedding(objective)
                        self.embeddings_manager.store_objective_embedding(objective, obj_embedding)
                    except Exception as e:
                        logger.warning(f"Failed to embed objective {objective.objective_id}: {str(e)}")
                        stats["failed"] += 1
                
            except Exception as e:
                logger.error(f"Failed to embed standard {standard.standard_id}: {str(e)}")
                stats["failed"] += 1
        
        logger.info(f"Embedding generation complete: {stats}")
        return stats