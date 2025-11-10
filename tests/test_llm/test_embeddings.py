"""Tests for standards embeddings functionality"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from backend.llm.embeddings import StandardsEmbeddings, StandardsEmbedder, EmbeddedStandard, EmbeddedObjective
from backend.repositories.models import Standard, Objective


class TestStandardsEmbeddings:
    """Test cases for StandardsEmbeddings class"""

    @pytest.fixture
    def mock_client(self):
        """Create a mock ChutesClient"""
        client = Mock()
        client.create_embedding.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        return client

    @pytest.fixture
    def embeddings_manager(self, mock_client):
        """Create a StandardsEmbeddings instance with mock client"""
        with patch('backend.llm.embeddings.ChutesClient', return_value=mock_client):
            return StandardsEmbeddings(mock_client)

    @pytest.fixture
    def sample_standard(self):
        """Create a sample standard for testing"""
        return Standard(
            standard_id="3.M.CR.1",
            grade_level="3rd Grade",
            strand_code="M.CR",
            strand_name="Musical Creation",
            strand_description="Creating, composing, and improvising music",
            standard_text="Create rhythmic patterns using quarter notes and eighth notes",
            source_document="test.pdf",
            ingestion_date="2024-01-01",
            version="1.0"
        )

    @pytest.fixture
    def sample_objectives(self):
        """Create sample objectives for testing"""
        return [
            Objective(
                objective_id="3.M.CR.1.1",
                standard_id="3.M.CR.1",
                objective_text="Perform quarter note patterns"
            ),
            Objective(
                objective_id="3.M.CR.1.2",
                standard_id="3.M.CR.1",
                objective_text="Create eighth note combinations"
            )
        ]

    def test_init_embeddings_table(self, embeddings_manager):
        """Test that embeddings tables are created properly"""
        # This is tested implicitly through the fixture creation
        # If no exception is raised, the tables were created successfully
        assert embeddings_manager.client is not None

    def test_serialize_deserialize_embedding(self, embeddings_manager):
        """Test embedding serialization and deserialization"""
        original_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Serialize
        serialized = embeddings_manager._serialize_embedding(original_embedding)
        assert isinstance(serialized, bytes)
        
        # Deserialize
        deserialized = embeddings_manager._deserialize_embedding(serialized)
        # Use approximate equality for float comparison due to numpy precision
        assert len(deserialized) == len(original_embedding)
        for i, (actual, exp) in enumerate(zip(deserialized, original_embedding)):
            assert abs(actual - exp) < 1e-6

    def test_prepare_standard_text(self, embeddings_manager, sample_standard, sample_objectives):
        """Test text preparation for embedding generation"""
        text = embeddings_manager._prepare_standard_text(sample_standard, sample_objectives)
        
        assert "3rd Grade" in text
        assert "M.CR" in text
        assert "Musical Creation" in text
        assert "Create rhythmic patterns" in text
        assert "Perform quarter note patterns" in text
        assert "Create eighth note combinations" in text

    def test_generate_standard_embedding(self, embeddings_manager, sample_standard, sample_objectives):
        """Test standard embedding generation"""
        embedding = embeddings_manager.generate_standard_embedding(sample_standard, sample_objectives)
        
        # Use approximate equality for float comparison due to numpy precision
        expected = [0.1, 0.2, 0.3, 0.4, 0.5]
        assert len(embedding) == len(expected)
        for i, (actual, exp) in enumerate(zip(embedding, expected)):
            assert abs(actual - exp) < 1e-6
        embeddings_manager.client.create_embedding.assert_called_once()

    def test_generate_objective_embedding(self, embeddings_manager):
        """Test objective embedding generation"""
        objective = Objective(
            objective_id="test.obj.1",
            standard_id="test.std.1",
            objective_text="Test objective text"
        )
        
        embedding = embeddings_manager.generate_objective_embedding(objective)
        
        # Use approximate equality for float comparison due to numpy precision
        expected = [0.1, 0.2, 0.3, 0.4, 0.5]
        assert len(embedding) == len(expected)
        for i, (actual, exp) in enumerate(zip(embedding, expected)):
            assert abs(actual - exp) < 1e-6
        embeddings_manager.client.create_embedding.assert_called_with("Test objective text")

    def test_store_and_retrieve_standard_embedding(self, embeddings_manager, sample_standard, sample_objectives):
        """Test storing and retrieving standard embeddings"""
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Store embedding
        embeddings_manager.store_standard_embedding(sample_standard, sample_objectives, embedding)
        
        # Retrieve embedding
        retrieved = embeddings_manager.get_standard_embedding(sample_standard.standard_id)
        
        assert retrieved is not None
        assert retrieved.standard_id == sample_standard.standard_id
        assert retrieved.grade_level == sample_standard.grade_level
        assert retrieved.strand_code == sample_standard.strand_code
        assert retrieved.standard_text == sample_standard.standard_text
        # Use approximate equality for float comparison due to numpy precision
        assert len(retrieved.embedding) == len(embedding)
        for i, (actual, exp) in enumerate(zip(retrieved.embedding, embedding)):
            assert abs(actual - exp) < 1e-6

    def test_store_and_retrieve_objective_embedding(self, embeddings_manager):
        """Test storing and retrieving objective embeddings"""
        objective = Objective(
            objective_id="test.obj.1",
            standard_id="test.std.1",
            objective_text="Test objective text"
        )
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Store embedding
        embeddings_manager.store_objective_embedding(objective, embedding)
        
        # Retrieve embedding
        retrieved = embeddings_manager.get_objective_embedding(objective.objective_id)
        
        assert retrieved is not None
        assert retrieved.objective_id == objective.objective_id
        assert retrieved.standard_id == objective.standard_id
        assert retrieved.objective_text == objective.objective_text
        # Use approximate equality for float comparison due to numpy precision
        assert len(retrieved.embedding) == len(embedding)
        for i, (actual, exp) in enumerate(zip(retrieved.embedding, embedding)):
            assert abs(actual - exp) < 1e-6

    def test_cosine_similarity(self, embeddings_manager):
        """Test cosine similarity calculation"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]  # Identical
        vec3 = [0.0, 1.0, 0.0]  # Orthogonal
        vec4 = [0.5, 0.5, 0.0]  # 45 degrees
        
        # Identical vectors should have similarity 1.0
        assert embeddings_manager.cosine_similarity(vec1, vec2) == pytest.approx(1.0)
        
        # Orthogonal vectors should have similarity 0.0
        assert embeddings_manager.cosine_similarity(vec1, vec3) == pytest.approx(0.0)
        
        # 45-degree vectors should have similarity ~0.707
        assert embeddings_manager.cosine_similarity(vec1, vec4) == pytest.approx(0.707, rel=1e-2)

    def test_search_similar_standards(self, embeddings_manager, sample_standard, sample_objectives):
        """Test semantic search for similar standards"""
        # Clear any existing embeddings from previous tests
        embeddings_manager.delete_all_embeddings()
        
        # Store some test embeddings
        embedding1 = [1.0, 0.0, 0.0]
        embedding2 = [0.9, 0.1, 0.0]  # Similar to embedding1
        embedding3 = [0.0, 1.0, 0.0]  # Different from embedding1
        
        # Create test standards
        std1 = Standard("std1", "3rd", "M.CR", "Creation", "", "Standard 1", "", "", "")
        std2 = Standard("std2", "3rd", "M.CR", "Creation", "", "Standard 2", "", "", "")
        std3 = Standard("std3", "4th", "M.PR", "Performance", "", "Standard 3", "", "", "")
        
        # Store embeddings
        embeddings_manager.store_standard_embedding(std1, [], embedding1)
        embeddings_manager.store_standard_embedding(std2, [], embedding2)
        embeddings_manager.store_standard_embedding(std3, [], embedding3)
        
        # Search for similar standards
        query_embedding = [1.0, 0.0, 0.0]
        results = embeddings_manager.search_similar_standards(
            query_embedding=query_embedding,
            limit=5,
            similarity_threshold=0.5
        )
        
        # Should return std1 and std2 (similar), but not std3 (different)
        assert len(results) == 2
        assert results[0][0].standard_id in ["std1", "std2"]
        assert results[1][0].standard_id in ["std1", "std2"]
        assert results[0][1] > results[1][1]  # First result should be more similar

    def test_search_similar_standards_with_filters(self, embeddings_manager):
        """Test semantic search with grade and strand filters"""
        # Store test embeddings for different grades/strands
        std1 = Standard(standard_id="std1", grade_level="3rd", strand_code="M.CR", strand_name="Creation", strand_description="", standard_text="Standard 1", source_document="", ingestion_date="", version="")
        std2 = Standard(standard_id="std2", grade_level="4th", strand_code="M.CR", strand_name="Creation", strand_description="", standard_text="Standard 2", source_document="", ingestion_date="", version="")
        std3 = Standard(standard_id="std3", grade_level="3rd", strand_code="M.PR", strand_name="Performance", strand_description="", standard_text="Standard 3", source_document="", ingestion_date="", version="")
        
        embedding = [1.0, 0.0, 0.0]
        
        embeddings_manager.store_standard_embedding(std1, [], embedding)
        embeddings_manager.store_standard_embedding(std2, [], embedding)
        embeddings_manager.store_standard_embedding(std3, [], embedding)
        
        # Search with grade filter
        query_embedding = [1.0, 0.0, 0.0]
        results = embeddings_manager.search_similar_standards(
            query_embedding=query_embedding,
            grade_level="3rd",
            limit=10
        )
        
        # Should only return 3rd grade standards
        assert len(results) == 2
        for result, _ in results:
            assert result.grade_level == "3rd"

    def test_search_similar_objectives(self, embeddings_manager):
        """Test semantic search for similar objectives"""
        # Store test objective embeddings
        obj1 = Objective(objective_id="obj1", standard_id="std1", objective_text="Create rhythmic patterns")
        obj2 = Objective(objective_id="obj2", standard_id="std1", objective_text="Compose simple melodies")
        obj3 = Objective(objective_id="obj3", standard_id="std2", objective_text="Perform with expression")
        
        embedding1 = [1.0, 0.0, 0.0, 0.0, 0.0]
        embedding2 = [0.9, 0.1, 0.0, 0.0, 0.0]  # Similar to embedding1
        embedding3 = [0.0, 1.0, 0.0, 0.0, 0.0]  # Different from embedding1
        
        embeddings_manager.store_objective_embedding(obj1, embedding1)
        embeddings_manager.store_objective_embedding(obj2, embedding2)
        embeddings_manager.store_objective_embedding(obj3, embedding3)
        
        # Search for similar objectives
        query_embedding = [1.0, 0.0, 0.0, 0.0, 0.0]
        results = embeddings_manager.search_similar_objectives(
            query_embedding=query_embedding,
            limit=5,
            similarity_threshold=0.5
        )
        
        # Should return obj1 and obj2 (similar), but not obj3 (different)
        assert len(results) == 2
        assert results[0][0].objective_id in ["obj1", "obj2"]
        assert results[1][0].objective_id in ["obj1", "obj2"]

    def test_embed_query(self, embeddings_manager):
        """Test query embedding generation"""
        query = "rhythmic patterns and composition"
        
        embedding = embeddings_manager.embed_query(query)
        
        assert embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
        embeddings_manager.client.create_embedding.assert_called_with(query)

    def test_get_embedding_stats(self, embeddings_manager):
        """Test getting embedding statistics"""
        # Clear existing embeddings first
        embeddings_manager.delete_all_embeddings()
        
        # Store some test data
        std1 = Standard(standard_id="std1", grade_level="3rd", strand_code="M.CR", strand_name="Creation", strand_description="", standard_text="Standard 1", source_document="", ingestion_date="", version="")
        obj1 = Objective(objective_id="obj1", standard_id="std1", objective_text="Test objective")
        
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        embeddings_manager.store_standard_embedding(std1, [], embedding)
        embeddings_manager.store_objective_embedding(obj1, embedding)
        
        # Get stats
        stats = embeddings_manager.get_embedding_stats()
        
        assert stats["standard_embeddings"] == 1
        assert stats["objective_embeddings"] == 1
        assert stats["embedding_dimension"] == 5

    def test_delete_all_embeddings(self, embeddings_manager):
        """Test deleting all embeddings"""
        # Clear existing embeddings first
        embeddings_manager.delete_all_embeddings()
        
        # Store some test data
        std1 = Standard(standard_id="std1", grade_level="3rd", strand_code="M.CR", strand_name="Creation", strand_description="", standard_text="Standard 1", source_document="", ingestion_date="", version="")
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        embeddings_manager.store_standard_embedding(std1, [], embedding)
        
        # Verify embeddings exist
        stats_before = embeddings_manager.get_embedding_stats()
        assert stats_before["standard_embeddings"] == 1
        
        # Delete all embeddings
        embeddings_manager.delete_all_embeddings()
        
        # Verify embeddings are gone
        stats_after = embeddings_manager.get_embedding_stats()
        assert stats_after["standard_embeddings"] == 0
        assert stats_after["objective_embeddings"] == 0

    def test_get_nonexistent_standard_embedding(self, embeddings_manager):
        """Test retrieving a standard embedding that doesn't exist"""
        result = embeddings_manager.get_standard_embedding("nonexistent.id")
        assert result is None

    def test_get_nonexistent_objective_embedding(self, embeddings_manager):
        """Test retrieving an objective embedding that doesn't exist"""
        result = embeddings_manager.get_objective_embedding("nonexistent.id")
        assert result is None


class TestStandardsEmbedder:
    """Test cases for StandardsEmbedder class"""

    @pytest.fixture
    def mock_embeddings_manager(self):
        """Create a mock StandardsEmbeddings"""
        manager = Mock()
        manager.get_standard_embedding.return_value = None  # No existing embedding
        manager.generate_standard_embedding.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        manager.store_standard_embedding.return_value = None
        manager.generate_objective_embedding.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        manager.store_objective_embedding.return_value = None
        return manager

    @pytest.fixture
    def embedder(self, mock_embeddings_manager):
        """Create a StandardsEmbedder with mocked dependencies"""
        with patch('backend.llm.embeddings.StandardsEmbeddings', return_value=mock_embeddings_manager):
            return StandardsEmbedder()

    @pytest.fixture
    def mock_repository(self):
        """Create a mock StandardsRepository"""
        repository = Mock()
        
        # Create sample standards and objectives
        std1 = Standard(standard_id="std1", grade_level="3rd", strand_code="M.CR", strand_name="Creation", strand_description="", standard_text="Standard 1", source_document="", ingestion_date="", version="")
        std2 = Standard(standard_id="std2", grade_level="4th", strand_code="M.PR", strand_name="Performance", strand_description="", standard_text="Standard 2", source_document="", ingestion_date="", version="")
        
        obj1 = Objective(objective_id="obj1", standard_id="std1", objective_text="Objective 1")
        obj2 = Objective(objective_id="obj2", standard_id="std1", objective_text="Objective 2")
        obj3 = Objective(objective_id="obj3", standard_id="std2", objective_text="Objective 3")
        
        repository.get_all_standards.return_value = [std1, std2]
        repository.get_objectives_for_standard.side_effect = {
            "std1": [obj1, obj2],
            "std2": [obj3]
        }.get
        
        return repository

    def test_embed_all_standards_success(self, embedder, mock_embeddings_manager, mock_repository):
        """Test successful embedding of all standards"""
        with patch('backend.repositories.standards_repository.StandardsRepository', return_value=mock_repository):
            stats = embedder.embed_all_standards()
            
            assert stats["success"] == 2
            assert stats["failed"] == 0
            assert stats["skipped"] == 0
            
            # Verify methods were called
            assert mock_embeddings_manager.generate_standard_embedding.call_count == 2
            assert mock_embeddings_manager.store_standard_embedding.call_count == 2
            assert mock_embeddings_manager.generate_objective_embedding.call_count == 3  # 2 for std1, 1 for std2
            assert mock_embeddings_manager.store_objective_embedding.call_count == 3

    def test_embed_all_standards_with_existing_embeddings(self, embedder, mock_embeddings_manager, mock_repository):
        """Test embedding when some embeddings already exist"""
        # Simulate existing embedding for first standard
        def get_standard_embedding_side_effect(standard_id):
            if standard_id == "std1":
                return Mock()  # Existing embedding
            return None
        
        mock_embeddings_manager.get_standard_embedding.side_effect = get_standard_embedding_side_effect
        
        with patch('backend.repositories.standards_repository.StandardsRepository', return_value=mock_repository):
            stats = embedder.embed_all_standards()
            
            assert stats["success"] == 1  # Only std2 embedded
            assert stats["skipped"] == 1  # std1 skipped
            assert stats["failed"] == 0

    def test_embed_all_standards_with_failures(self, embedder, mock_embeddings_manager, mock_repository):
        """Test embedding when some embeddings fail"""
        # Simulate failure for first standard
        def generate_standard_embedding_side_effect(standard, objectives):
            if standard.standard_id == "std1":
                raise Exception("API error")
            return [0.1, 0.2, 0.3, 0.4, 0.5]
        
        mock_embeddings_manager.generate_standard_embedding.side_effect = generate_standard_embedding_side_effect
        
        with patch('backend.repositories.standards_repository.StandardsRepository', return_value=mock_repository):
            stats = embedder.embed_all_standards()
            
            assert stats["success"] == 1  # std2 succeeded
            assert stats["failed"] == 1  # std1 failed
            assert stats["skipped"] == 0

    def test_embed_all_standards_batch_size(self, embedder, mock_embeddings_manager, mock_repository):
        """Test embedding with custom batch size"""
        with patch('backend.repositories.standards_repository.StandardsRepository', return_value=mock_repository):
            embedder.embed_all_standards(batch_size=1)
            
            # Should still process all standards, batch size affects logging/progress
            assert mock_embeddings_manager.generate_standard_embedding.call_count == 2


class TestEmbeddedStandard:
    """Test cases for EmbeddedStandard dataclass"""

    def test_embedded_standard_creation(self):
        """Test creating an EmbeddedStandard"""
        embedded = EmbeddedStandard(
            standard_id="3.M.CR.1",
            grade_level="3rd Grade",
            strand_code="M.CR",
            strand_name="Musical Creation",
            standard_text="Create rhythmic patterns",
            embedding=[0.1, 0.2, 0.3],
            objectives_text="Create patterns, Perform rhythms"
        )
        
        assert embedded.standard_id == "3.M.CR.1"
        assert embedded.grade_level == "3rd Grade"
        assert embedded.strand_code == "M.CR"
        assert embedded.strand_name == "Musical Creation"
        assert embedded.standard_text == "Create rhythmic patterns"
        assert embedded.embedding == [0.1, 0.2, 0.3]
        assert embedded.objectives_text == "Create patterns, Perform rhythms"


class TestEmbeddedObjective:
    """Test cases for EmbeddedObjective dataclass"""

    def test_embedded_objective_creation(self):
        """Test creating an EmbeddedObjective"""
        embedded = EmbeddedObjective(
            objective_id="3.M.CR.1.1",
            standard_id="3.M.CR.1",
            objective_text="Create simple rhythmic patterns",
            embedding=[0.1, 0.2, 0.3]
        )
        
        assert embedded.objective_id == "3.M.CR.1.1"
        assert embedded.standard_id == "3.M.CR.1"
        assert embedded.objective_text == "Create simple rhythmic patterns"
        assert embedded.embedding == [0.1, 0.2, 0.3]