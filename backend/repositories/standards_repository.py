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
                SELECT
                    standard_code as standard_id,
                    level_name as grade_level,
                    strand_code,
                    strand_name,
                    strand_description,
                    standard_text,
                    document_title as source_document,
                    NULL as file_id,
                    NULL as ingestion_date,
                    NULL as version
                FROM standards_full
                ORDER BY level_code, strand_code, standard_code
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
                    file_id=row[7],
                    ingestion_date=row[8],
                    version=row[9]
                ))

            return standards
        finally:
            conn.close()

    def list_standards(
        self,
        grade_level: Optional[str] = None,
        strand_code: Optional[str] = None,
        limit: int = 50
    ) -> List[Standard]:
        """List standards filtered by grade and strand (optional)"""
        base_query = """
            SELECT
                standard_code as standard_id,
                level_name as grade_level,
                strand_code,
                strand_name,
                strand_description,
                standard_text,
                document_title as source_document,
                NULL as file_id,
                NULL as ingestion_date,
                NULL as version
            FROM standards_full
        """

        filters = []
        params = []

        if grade_level:
            # Convert grade_level to level_code format (handles both "Kindergarten" and "0")
            # The database stores level_code (e.g., "0", "1", "2") and level_name (e.g., "Kindergarten", "Grade 1")
            level_code = self._grade_to_level_code(grade_level)
            filters.append("level_code = ?")
            params.append(level_code)

        if strand_code:
            filters.append("strand_code = ?")
            params.append(strand_code)

        if filters:
            base_query += " WHERE " + " AND ".join(filters)

        base_query += " ORDER BY level_code, strand_code, standard_code LIMIT ?"
        params.append(limit)

        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(base_query, tuple(params))
            return [self._row_to_standard(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_standard_by_id(self, standard_id: str) -> Optional[Standard]:
        """Get a single standard by its ID"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                SELECT
                    standard_code as standard_id,
                    level_name as grade_level,
                    strand_code,
                    strand_name,
                    strand_description,
                    standard_text,
                    document_title as source_document,
                    NULL as file_id,
                    NULL as ingestion_date,
                    NULL as version
                FROM standards_full
                WHERE standard_code = ?
            """, (standard_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_standard(row)
        finally:
            conn.close()
    
    def _grade_to_level_code(self, grade_level: str) -> str:
        """Convert grade level to level_code format for database queries"""
        if not grade_level:
            return grade_level
        
        normalized = grade_level.strip()
        
        # If already a code (numeric or proficiency code), return as-is
        # Note: Database uses "K" for Kindergarten, not "0"
        if normalized.isdigit() or normalized in ["0", "K", "AC", "AD", "N", "D", "I"]:
            # Convert "0" to "K" since database uses "K" for Kindergarten
            return "K" if normalized == "0" else normalized
        
        # Convert frontend format to level_code
        # Note: Database stores Kindergarten as "K", not "0"
        grade_mapping = {
            "Kindergarten": "K",
            "Grade 1": "1",
            "Grade 2": "2",
            "Grade 3": "3",
            "Grade 4": "4",
            "Grade 5": "5",
            "Grade 6": "6",
            "Grade 7": "7",
            "Grade 8": "8",
            "Novice": "N",
            "Developing": "D",
            "Intermediate": "I",
            "Accomplished": "AC",
            "Advanced": "AD",
        }
        
        return grade_mapping.get(normalized, normalized)
    
    def get_standards_by_grade(self, grade_level: str) -> List[Standard]:
        """Get standards for a specific grade level"""
        # Convert grade level to level_code format for the new schema
        level_code = self._grade_to_level_code(grade_level)
        
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                SELECT
                    standard_code as standard_id,
                    level_name as grade_level,
                    strand_code,
                    strand_name,
                    strand_description,
                    standard_text,
                    document_title as source_document,
                    NULL as file_id,
                    NULL as ingestion_date,
                    NULL as version
                FROM standards_full
                WHERE level_code = ?
                ORDER BY strand_code, standard_code
            """, (level_code,))
            
            return [self._row_to_standard(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_standards_by_strand(self, strand_code: str) -> List[Standard]:
        """Get standards for a specific strand code"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                SELECT
                    standard_code as standard_id,
                    level_name as grade_level,
                    strand_code,
                    strand_name,
                    strand_description,
                    standard_text,
                    document_title as source_document,
                    NULL as file_id,
                    NULL as ingestion_date,
                    NULL as version
                FROM standards_full
                WHERE strand_code = ?
                ORDER BY level_code, standard_code
            """, (strand_code,))
            
            return [self._row_to_standard(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_standards_by_grade_and_strand(self, grade_level: str, strand_code: str) -> List[Standard]:
        """Get standards for a specific grade level and strand"""
        # Convert grade level to level_code format for the new schema
        level_code = self._grade_to_level_code(grade_level)
        
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                SELECT
                    standard_code as standard_id,
                    level_name as grade_level,
                    strand_code,
                    strand_name,
                    strand_description,
                    standard_text,
                    document_title as source_document,
                    NULL as file_id,
                    NULL as ingestion_date,
                    NULL as version
                FROM standards_full
                WHERE level_code = ? AND strand_code = ?
                ORDER BY standard_code
            """, (level_code, strand_code))
            
            return [self._row_to_standard(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_standard_by_id(self, standard_id: str) -> Optional[Standard]:
        """Get a specific standard by its ID"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                SELECT standard_id, grade_level, strand_code, strand_name,
                       strand_description, standard_text, source_document, file_id,
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
                    file_id=row[7],
                    ingestion_date=row[8],
                    version=row[9]
                )
            return None
        finally:
            conn.close()
    
    def get_objectives_for_standard(self, standard_id: str) -> List[Objective]:
        """Get all objectives for a specific standard"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                SELECT
                    objective_code as objective_id,
                    standard_code as standard_id,
                    objective_text,
                    NULL as file_id
                FROM objectives_full
                WHERE standard_code = ?
                ORDER BY objective_code
            """, (standard_id,))

            objectives = []
            for row in cursor.fetchall():
                objectives.append(Objective(
                    objective_id=row[0],
                    standard_id=row[1],
                    objective_text=row[2],
                    file_id=row[3]
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
                SELECT
                    standard_code as standard_id,
                    level_name as grade_level,
                    strand_code,
                    strand_name,
                    strand_description,
                    standard_text,
                    document_title as source_document,
                    NULL as file_id,
                    NULL as ingestion_date,
                    NULL as version
                FROM standards_full
                WHERE standard_text LIKE ?
                   OR strand_description LIKE ?
                   OR strand_name LIKE ?
                   OR standard_code LIKE ?
                ORDER BY level_code, strand_code, standard_code
            """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))

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
                    file_id=row[7],
                    ingestion_date=row[8],
                    version=row[9]
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
                    SELECT DISTINCT level_name
                    FROM standards_full
                    ORDER BY level_code
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
                    SELECT code
                    FROM strands
                    ORDER BY display_order
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
                    SELECT code, name, description
                    FROM strands
                    ORDER BY display_order
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
            cursor = conn.execute("SELECT COUNT(*) FROM standards WHERE is_variant = 0")
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

    def get_standards_by_file_id(self, file_id: str) -> List[Standard]:
        """Get standards for a specific file ID"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                SELECT standard_id, grade_level, strand_code, strand_name,
                       strand_description, standard_text, source_document, file_id,
                       ingestion_date, version
                FROM standards
                WHERE file_id = ?
                ORDER BY strand_code, standard_id
            """, (file_id,))
            
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
                    file_id=row[7],
                    ingestion_date=row[8],
                    version=row[9]
                ))
            
            return standards
        finally:
            conn.close()

    def _row_to_standard(self, row: sqlite3.Row) -> Standard:
        return Standard(
            standard_id=row[0],
            grade_level=row[1],
            strand_code=row[2],
            strand_name=row[3],
            strand_description=row[4],
            standard_text=row[5],
            source_document=row[6],
            file_id=row[7],
            ingestion_date=row[8],
            version=row[9]
        )
