"""Standards repository for querying music education standards"""

import sqlite3
from typing import List, Optional, Dict, Any, Tuple
from .database import DatabaseManager
from .models import Standard, Objective, StandardWithObjectives
from backend.llm.embeddings import StandardsEmbeddings


class StandardsRepository:
    """Repository for querying standards and objectives from database"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager()
        self.embeddings = StandardsEmbeddings()
        # Simple in-memory cache for frequently accessed data
        self._grade_levels_cache: Optional[List[str]] = None
        self._strand_codes_cache: Optional[List[str]] = None
        self._strand_info_cache: Optional[Dict[str, Dict[str, str]]] = None
    
    def get_all_standards(self) -> List[Standard]:
        """Get all standards from database"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                SELECT standard_id, grade_level, strand_code, strand_name,
                       strand_description, standard_text, source_document,
                       ingestion_date, version
                FROM standards
                ORDER BY grade_level, strand_code, standard_id
            """)
            
            standards = []
            for row in cursor.fetchall():
                standards.append(Standard(
                    standard_id=row[0],
                    grade_level=row[1],
                    strand_code=row[2],
                    strand_name=row[3],
                    strand_description=row[4],
                    standard_text=row[5],
                    source_document=row[6],
                    ingestion_date=row[7],
                    version=row[8]
                ))
            
            return standards
        finally:
            conn.close()
    
    def get_standards_by_grade(self, grade_level: str) -> List[Standard]:
        """Get standards for a specific grade level"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                SELECT standard_id, grade_level, strand_code, strand_name,
                       strand_description, standard_text, source_document,
                       ingestion_date, version
                FROM standards
                WHERE grade_level = ?
                ORDER BY strand_code, standard_id
            """, (grade_level,))
            
            standards = []
            for row in cursor.fetchall():
                standards.append(Standard(
                    standard_id=row[0],
                    grade_level=row[1],
                    strand_code=row[2],
                    strand_name=row[3],
                    strand_description=row[4],
                    standard_text=row[5],
                    source_document=row[6],
                    ingestion_date=row[7],
                    version=row[8]
                ))
            
            return standards
        finally:
            conn.close()
    
    def get_standards_by_strand(self, strand_code: str) -> List[Standard]:
        """Get standards for a specific strand code"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                SELECT standard_id, grade_level, strand_code, strand_name,
                       strand_description, standard_text, source_document,
                       ingestion_date, version
                FROM standards
                WHERE strand_code = ?
                ORDER BY grade_level, standard_id
            """, (strand_code,))
            
            standards = []
            for row in cursor.fetchall():
                standards.append(Standard(
                    standard_id=row[0],
                    grade_level=row[1],
                    strand_code=row[2],
                    strand_name=row[3],
                    strand_description=row[4],
                    standard_text=row[5],
                    source_document=row[6],
                    ingestion_date=row[7],
                    version=row[8]
                ))
            
            return standards
        finally:
            conn.close()
    
    def get_standards_by_grade_and_strand(self, grade_level: str, strand_code: str) -> List[Standard]:
        """Get standards for a specific grade level and strand"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                SELECT standard_id, grade_level, strand_code, strand_name,
                       strand_description, standard_text, source_document,
                       ingestion_date, version
                FROM standards
                WHERE grade_level = ? AND strand_code = ?
                ORDER BY standard_id
            """, (grade_level, strand_code))
            
            standards = []
            for row in cursor.fetchall():
                standards.append(Standard(
                    standard_id=row[0],
                    grade_level=row[1],
                    strand_code=row[2],
                    strand_name=row[3],
                    strand_description=row[4],
                    standard_text=row[5],
                    source_document=row[6],
                    ingestion_date=row[7],
                    version=row[8]
                ))
            
            return standards
        finally:
            conn.close()
    
    def get_standard_by_id(self, standard_id: str) -> Optional[Standard]:
        """Get a specific standard by its ID"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                SELECT standard_id, grade_level, strand_code, strand_name,
                       strand_description, standard_text, source_document,
                       ingestion_date, version
                FROM standards
                WHERE standard_id = ?
            """, (standard_id,))
            
            row = cursor.fetchone()
            if row:
                return Standard(
                    standard_id=row[0],
                    grade_level=row[1],
                    strand_code=row[2],
                    strand_name=row[3],
                    strand_description=row[4],
                    standard_text=row[5],
                    source_document=row[6],
                    ingestion_date=row[7],
                    version=row[8]
                )
            return None
        finally:
            conn.close()
    
    def get_objectives_for_standard(self, standard_id: str) -> List[Objective]:
        """Get all objectives for a specific standard"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                SELECT objective_id, standard_id, objective_text
                FROM objectives
                WHERE standard_id = ?
                ORDER BY objective_id
            """, (standard_id,))
            
            objectives = []
            for row in cursor.fetchall():
                objectives.append(Objective(
                    objective_id=row[0],
                    standard_id=row[1],
                    objective_text=row[2]
                ))
            
            return objectives
        finally:
            conn.close()
    
    def get_standard_with_objectives(self, standard_id: str) -> Optional[StandardWithObjectives]:
        """Get a standard with all its objectives"""
        standard = self.get_standard_by_id(standard_id)
        if not standard:
            return None
        
        objectives = self.get_objectives_for_standard(standard_id)
        return StandardWithObjectives(
            standard=standard,
            objectives=objectives
        )
    
    def search_standards(self, query: str) -> List[Standard]:
        """Full-text search of standard descriptions"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                SELECT standard_id, grade_level, strand_code, strand_name,
                       strand_description, standard_text, source_document,
                       ingestion_date, version
                FROM standards
                WHERE standard_text LIKE ? 
                   OR strand_description LIKE ?
                   OR strand_name LIKE ?
                ORDER BY grade_level, strand_code, standard_id
            """, (f"%{query}%", f"%{query}%", f"%{query}%"))
            
            standards = []
            for row in cursor.fetchall():
                standards.append(Standard(
                    standard_id=row[0],
                    grade_level=row[1],
                    strand_code=row[2],
                    strand_name=row[3],
                    strand_description=row[4],
                    standard_text=row[5],
                    source_document=row[6],
                    ingestion_date=row[7],
                    version=row[8]
                ))
            
            return standards
        finally:
            conn.close()
    
    def get_grade_levels(self) -> List[str]:
        """Get all available grade levels (cached)"""
        if self._grade_levels_cache is None:
            conn = self.db_manager.get_connection()
            try:
                cursor = conn.execute("""
                    SELECT DISTINCT grade_level 
                    FROM standards 
                    ORDER BY grade_level
                """)
                
                self._grade_levels_cache = [row[0] for row in cursor.fetchall()]
            finally:
                conn.close()
        
        return self._grade_levels_cache
    
    def get_strand_codes(self) -> List[str]:
        """Get all available strand codes (cached)"""
        if self._strand_codes_cache is None:
            conn = self.db_manager.get_connection()
            try:
                cursor = conn.execute("""
                    SELECT DISTINCT strand_code 
                    FROM standards 
                    ORDER BY strand_code
                """)
                
                self._strand_codes_cache = [row[0] for row in cursor.fetchall()]
            finally:
                conn.close()
        
        return self._strand_codes_cache
    
    def get_strand_info(self) -> Dict[str, Dict[str, str]]:
        """Get strand information (code, name, description) for all strands (cached)"""
        if self._strand_info_cache is None:
            conn = self.db_manager.get_connection()
            try:
                cursor = conn.execute("""
                    SELECT DISTINCT strand_code, strand_name, strand_description
                    FROM standards 
                    ORDER BY strand_code
                """)
                
                strand_info = {}
                for row in cursor.fetchall():
                    strand_info[row[0]] = {
                        'name': row[1],
                        'description': row[2]
                    }
                
                self._strand_info_cache = strand_info
            finally:
                conn.close()
        
        return self._strand_info_cache
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        self._grade_levels_cache = None
        self._strand_codes_cache = None
        self._strand_info_cache = None
    
    def get_standards_count(self) -> int:
        """Get total count of standards"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM standards")
            return cursor.fetchone()[0]
        finally:
            conn.close()
    
    def get_objectives_count(self) -> int:
        """Get total count of objectives"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM objectives")
            return cursor.fetchone()[0]
        finally:
            conn.close()
    
    def search_standards_semantic(
        self, 
        query: str, 
        grade_level: Optional[str] = None,
        strand_code: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.5
    ) -> List[Tuple[Standard, float]]:
        """
        Search for standards using semantic similarity
        
        Args:
            query: Search query text
            grade_level: Optional grade level filter
            strand_code: Optional strand code filter
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of (Standard, similarity_score) tuples
        """
        # Generate embedding for query
        query_embedding = self.embeddings.embed_query(query)
        
        # Search for similar standards
        similar_standards = self.embeddings.search_similar_standards(
            query_embedding=query_embedding,
            grade_level=grade_level,
            strand_code=strand_code,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
        
        # Convert EmbeddedStandard objects back to Standard objects
        results = []
        for embedded_standard, similarity in similar_standards:
            standard = Standard(
                standard_id=embedded_standard.standard_id,
                grade_level=embedded_standard.grade_level,
                strand_code=embedded_standard.strand_code,
                strand_name=embedded_standard.strand_name,
                strand_description="",  # Not stored in embeddings
                standard_text=embedded_standard.standard_text,
                source_document="",  # Not stored in embeddings
                ingestion_date="",  # Not stored in embeddings
                version=""  # Not stored in embeddings
            )
            results.append((standard, similarity))
        
        return results
    
    def search_objectives_semantic(
        self, 
        query: str, 
        standard_id: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.5
    ) -> List[Tuple[Objective, float]]:
        """
        Search for objectives using semantic similarity
        
        Args:
            query: Search query text
            standard_id: Optional standard ID filter
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of (Objective, similarity_score) tuples
        """
        # Generate embedding for query
        query_embedding = self.embeddings.embed_query(query)
        
        # Search for similar objectives
        similar_objectives = self.embeddings.search_similar_objectives(
            query_embedding=query_embedding,
            standard_id=standard_id,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
        
        # Convert EmbeddedObjective objects back to Objective objects
        results = []
        for embedded_objective, similarity in similar_objectives:
            objective = Objective(
                objective_id=embedded_objective.objective_id,
                standard_id=embedded_objective.standard_id,
                objective_text=embedded_objective.objective_text
            )
            results.append((objective, similarity))
        
        return results
    
    def recommend_standards_for_topic(
        self, 
        topic: str, 
        grade_level: Optional[str] = None,
        limit: int = 5
    ) -> List[Tuple[Standard, float]]:
        """
        Recommend standards for a given topic using semantic search
        
        Args:
            topic: Topic or lesson idea
            grade_level: Optional grade level filter
            limit: Maximum number of recommendations
            
        Returns:
            List of (Standard, relevance_score) tuples
        """
        # Use a higher similarity threshold for recommendations
        return self.search_standards_semantic(
            query=topic,
            grade_level=grade_level,
            limit=limit,
            similarity_threshold=0.3  # Lower threshold to get more recommendations
        )
    
    def get_embedding_stats(self) -> Dict[str, int]:
        """Get statistics about embeddings in the database"""
        return self.embeddings.get_embedding_stats()
