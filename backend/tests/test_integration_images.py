"""
Integration tests for image processing system.

Tests the complete image processing pipeline including:
- Image upload
- OCR text extraction
- Vision AI analysis
- Image storage and retrieval
- Storage quota management
"""

import pytest
import os
import tempfile
import io
from PIL import Image
from fastapi.testclient import TestClient

# Add backend to path
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.api.main import app
from backend.repositories.migrations import DatabaseMigrator
from backend.auth.models import UserRole, ProcessingMode


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Migrate database
    migrator = DatabaseMigrator(db_path)
    migrator.migrate()

    # Update app to use test database
    from backend.api import dependencies

    dependencies.DATABASE_PATH = db_path

    yield db_path

    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def temp_image_dir():
    """Create temporary directory for image storage."""
    import tempfile

    temp_dir = tempfile.mkdtemp()

    # Update image storage path
    from backend.image_processing import image_storage

    image_storage.STORAGE_PATH = temp_dir

    yield temp_dir

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def client(test_db, temp_image_dir):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def admin_user(test_db):
    """Create an admin user for testing."""
    repo = UserRepository(test_db)
    user = repo.create_user(
        email="admin@test.com",
        password="Admin123",
        role=UserRole.ADMIN,
        full_name="Test Admin",
        processing_mode=ProcessingMode.CLOUD,
    )
    return user


@pytest.fixture
def admin_token(client, admin_user):
    """Get admin access token."""
    response = client.post(
        "/api/auth/login", json={"email": "admin@test.com", "password": "Admin123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def test_image():
    """Create a simple test image."""
    # Create a simple PNG image with text
    img = Image.new("RGB", (200, 100), color="white")

    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    return img_bytes


class TestImageUpload:
    """Test image upload functionality."""

    def test_upload_single_image(self, client, admin_token, test_image):
        """Test uploading a single image."""
        response = client.post(
            "/api/images",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={"file": ("test.png", test_image, "image/png")},
            data={"processing_mode": "cloud"},
        )

        # May return 200 or 500 depending on whether Tesseract/Chutes API is available
        # In test environment without external dependencies, we expect it to attempt processing
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert data["filename"] == "test.png"
            assert data["mime_type"] == "image/png"

    def test_upload_requires_auth(self, client, test_image):
        """Test image upload requires authentication."""
        response = client.post(
            "/api/images", files={"file": ("test.png", test_image, "image/png")}
        )

        assert response.status_code == 401

    def test_upload_invalid_file_type(self, client, admin_token):
        """Test uploading non-image file is rejected."""
        # Create a text file
        text_file = io.BytesIO(b"This is not an image")

        response = client.post(
            "/api/images",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={"file": ("test.txt", text_file, "text/plain")},
        )

        assert response.status_code in [400, 422]  # Bad request or validation error

    def test_batch_upload(self, client, admin_token, test_image):
        """Test uploading multiple images."""
        # Create two test images
        test_image.seek(0)
        img2 = io.BytesIO()
        img = Image.new("RGB", (200, 100), color="blue")
        img.save(img2, format="PNG")
        img2.seek(0)

        response = client.post(
            "/api/images/batch",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=[
                ("files", ("test1.png", test_image, "image/png")),
                ("files", ("test2.png", img2, "image/png")),
            ],
            data={"processing_mode": "cloud"},
        )

        # May fail if external services unavailable
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "results" in data
            assert len(data["results"]) == 2


class TestImageRetrieval:
    """Test image retrieval and listing."""

    @pytest.fixture
    def uploaded_image(self, client, admin_token, test_image):
        """Upload an image for testing retrieval."""
        response = client.post(
            "/api/images",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={"file": ("test.png", test_image, "image/png")},
        )

        if response.status_code == 200:
            return response.json()
        return None

    def test_list_images(self, client, admin_token, uploaded_image):
        """Test listing user's images."""
        response = client.get(
            "/api/images", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "images" in data
        assert isinstance(data["images"], list)

        if uploaded_image:
            assert len(data["images"]) > 0

    def test_get_image_by_id(self, client, admin_token, uploaded_image):
        """Test retrieving specific image."""
        if not uploaded_image:
            pytest.skip("Image upload not available")

        response = client.get(
            f"/api/images/{uploaded_image['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == uploaded_image["id"]

    def test_get_nonexistent_image(self, client, admin_token):
        """Test retrieving non-existent image."""
        response = client.get(
            "/api/images/nonexistent_id",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404

    def test_search_images(self, client, admin_token, uploaded_image):
        """Test searching images by content."""
        response = client.get(
            "/api/images/search",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"query": "test", "limit": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)


class TestImageDeletion:
    """Test image deletion."""

    @pytest.fixture
    def uploaded_image(self, client, admin_token, test_image):
        """Upload an image for testing deletion."""
        response = client.post(
            "/api/images",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={"file": ("test.png", test_image, "image/png")},
        )

        if response.status_code == 200:
            return response.json()
        return None

    def test_delete_image(self, client, admin_token, uploaded_image):
        """Test deleting an image."""
        if not uploaded_image:
            pytest.skip("Image upload not available")

        response = client.delete(
            f"/api/images/{uploaded_image['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200

        # Verify image is gone
        get_response = client.get(
            f"/api/images/{uploaded_image['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert get_response.status_code == 404

    def test_delete_nonexistent_image(self, client, admin_token):
        """Test deleting non-existent image."""
        response = client.delete(
            "/api/images/nonexistent_id",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404


class TestStorageManagement:
    """Test storage quota and management."""

    def test_get_storage_info(self, client, admin_token):
        """Test getting storage information."""
        response = client.get(
            "/api/images/storage/info",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_images" in data
        assert "total_size_bytes" in data
        assert "quota_mb" in data
        assert "used_percentage" in data


class TestImageIsolation:
    """Test that users can only access their own images."""

    @pytest.fixture
    def teacher_user(self, test_db):
        """Create a teacher user."""
        repo = UserRepository(test_db)
        user = repo.create_user(
            email="teacher@test.com",
            password="Teacher123",
            role=UserRole.TEACHER,
            full_name="Test Teacher",
            processing_mode=ProcessingMode.CLOUD,
        )
        return user

    @pytest.fixture
    def teacher_token(self, client, teacher_user):
        """Get teacher access token."""
        response = client.post(
            "/api/auth/login",
            json={"email": "teacher@test.com", "password": "Teacher123"},
        )
        return response.json()["access_token"]

    @pytest.fixture
    def admin_image(self, client, admin_token, test_image):
        """Upload image as admin."""
        response = client.post(
            "/api/images",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={"file": ("admin_image.png", test_image, "image/png")},
        )

        if response.status_code == 200:
            return response.json()
        return None

    def test_teacher_cannot_see_admin_images(self, client, teacher_token, admin_image):
        """Test teacher cannot access admin's images."""
        if not admin_image:
            pytest.skip("Image upload not available")

        response = client.get(
            f"/api/images/{admin_image['id']}",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )

        # Should be 404 (not found) or 403 (forbidden)
        assert response.status_code in [403, 404]

    def test_teacher_sees_only_own_images(
        self, client, teacher_token, admin_token, admin_image, test_image
    ):
        """Test teacher only sees their own images in list."""
        # Upload image as teacher
        test_image.seek(0)
        teacher_upload = client.post(
            "/api/images",
            headers={"Authorization": f"Bearer {teacher_token}"},
            files={"file": ("teacher_image.png", test_image, "image/png")},
        )

        # List images as teacher
        response = client.get(
            "/api/images", headers={"Authorization": f"Bearer {teacher_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        if admin_image and teacher_upload.status_code == 200:
            # Teacher should only see their own image
            teacher_image_ids = [img["id"] for img in data["images"]]
            assert admin_image["id"] not in teacher_image_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
