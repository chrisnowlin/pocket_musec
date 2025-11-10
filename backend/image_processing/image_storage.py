"""Image storage with compression and quota management"""

from PIL import Image
from pathlib import Path
import shutil
import uuid
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ImageStorage:
    """
    Manages image file storage with compression and quota enforcement
    """

    def __init__(
        self,
        storage_path: str = "data/images",
        max_size_mb: int = 5120,  # 5GB default
        jpeg_quality: int = 85
    ):
        """
        Initialize image storage

        Args:
            storage_path: Directory for image storage
            max_size_mb: Maximum storage size in MB (default 5GB)
            jpeg_quality: JPEG compression quality (1-100, default 85)
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.jpeg_quality = jpeg_quality

    def store_image(
        self,
        image_path: str,
        user_id: str,
        original_filename: str
    ) -> Tuple[str, str, int]:
        """
        Store image with compression

        Args:
            image_path: Path to source image
            user_id: User ID for organization
            original_filename: Original filename

        Returns:
            Tuple of (stored_path, compressed_path, file_size)
        """
        # Generate unique ID
        image_id = str(uuid.uuid4())
        file_ext = Path(original_filename).suffix.lower()

        # Create user directory
        user_dir = self.storage_path / user_id
        user_dir.mkdir(exist_ok=True)

        # Store original
        original_dest = user_dir / f"{image_id}_original{file_ext}"
        shutil.copy2(image_path, original_dest)

        # Create compressed version
        compressed_dest = user_dir / f"{image_id}_compressed.jpg"
        compressed_size = self._compress_image(str(original_dest), str(compressed_dest))

        logger.info(
            f"Stored image {image_id}: "
            f"original={original_dest.stat().st_size} bytes, "
            f"compressed={compressed_size} bytes"
        )

        return str(original_dest), str(compressed_dest), compressed_size

    def _compress_image(self, source_path: str, dest_path: str) -> int:
        """
        Compress image to JPEG

        Args:
            source_path: Source image path
            dest_path: Destination path for compressed image

        Returns:
            Size of compressed file in bytes
        """
        try:
            with Image.open(source_path) as img:
                # Convert RGBA to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # Save with compression
                img.save(
                    dest_path,
                    'JPEG',
                    quality=self.jpeg_quality,
                    optimize=True
                )

            return Path(dest_path).stat().st_size

        except Exception as e:
            logger.error(f"Image compression failed: {e}")
            # Fallback: copy original
            shutil.copy2(source_path, dest_path)
            return Path(dest_path).stat().st_size

    def get_storage_usage(self, user_id: Optional[str] = None) -> int:
        """
        Get current storage usage in bytes

        Args:
            user_id: Optional user ID to check specific user's usage

        Returns:
            Total bytes used
        """
        total = 0

        if user_id:
            user_dir = self.storage_path / user_id
            if user_dir.exists():
                for file_path in user_dir.rglob('*'):
                    if file_path.is_file():
                        total += file_path.stat().st_size
        else:
            # Total for all users
            for file_path in self.storage_path.rglob('*'):
                if file_path.is_file():
                    total += file_path.stat().st_size

        return total

    def check_quota(self, additional_bytes: int = 0) -> bool:
        """
        Check if adding more data would exceed quota

        Args:
            additional_bytes: Bytes to be added

        Returns:
            True if within quota, False if would exceed
        """
        current_usage = self.get_storage_usage()
        return (current_usage + additional_bytes) <= self.max_size_bytes

    def get_quota_info(self) -> dict:
        """
        Get quota information

        Returns:
            Dictionary with usage, limit, available, percentage
        """
        usage = self.get_storage_usage()
        available = max(0, self.max_size_bytes - usage)
        percentage = (usage / self.max_size_bytes) * 100 if self.max_size_bytes > 0 else 0

        return {
            "usage_bytes": usage,
            "usage_mb": usage / (1024 * 1024),
            "limit_bytes": self.max_size_bytes,
            "limit_mb": self.max_size_bytes / (1024 * 1024),
            "available_bytes": available,
            "available_mb": available / (1024 * 1024),
            "percentage": percentage
        }

    def delete_image(self, image_path: str) -> bool:
        """
        Delete an image and its compressed version

        Args:
            image_path: Path to image (original or compressed)

        Returns:
            True if deleted, False otherwise
        """
        try:
            path = Path(image_path)

            # Delete both original and compressed versions
            if path.exists():
                path.unlink()

            # Find and delete the paired file
            if '_original' in path.name:
                compressed = path.parent / path.name.replace('_original', '_compressed').replace(path.suffix, '.jpg')
                if compressed.exists():
                    compressed.unlink()
            elif '_compressed' in path.name:
                # Extract image ID and find original
                image_id = path.stem.replace('_compressed', '')
                for original in path.parent.glob(f"{image_id}_original.*"):
                    if original.exists():
                        original.unlink()

            logger.info(f"Deleted image: {image_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete image {image_path}: {e}")
            return False

    def evict_oldest(self, count: int = 1) -> int:
        """
        Evict oldest images (LRU eviction)

        Args:
            count: Number of images to evict

        Returns:
            Number of images actually evicted
        """
        # Find all original images with their access times
        images = []
        for user_dir in self.storage_path.iterdir():
            if user_dir.is_dir():
                for img_path in user_dir.glob('*_original.*'):
                    images.append((img_path, img_path.stat().st_atime))

        # Sort by access time (oldest first)
        images.sort(key=lambda x: x[1])

        # Evict oldest
        evicted = 0
        for img_path, _ in images[:count]:
            if self.delete_image(str(img_path)):
                evicted += 1

        logger.info(f"Evicted {evicted} oldest images")
        return evicted

    def cleanup_user_images(self, user_id: str) -> int:
        """
        Delete all images for a user

        Args:
            user_id: User ID

        Returns:
            Number of images deleted
        """
        user_dir = self.storage_path / user_id
        if not user_dir.exists():
            return 0

        count = 0
        for img_path in user_dir.iterdir():
            if img_path.is_file() and self.delete_image(str(img_path)):
                count += 1

        # Remove empty directory
        try:
            user_dir.rmdir()
        except:
            pass

        return count
