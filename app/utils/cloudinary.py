import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import Dict
from app.core.config import (
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET
)
from app.core.logger import get_logger

logger = get_logger(__name__)

# -------------------------------------------------
# Cloudinary Configuration
# -------------------------------------------------
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)

# -------------------------------------------------
# Upload File (PDF / Image)
# -------------------------------------------------
def upload_file(
    file,
    folder: str = "ordereasy"
) -> Dict[str, str]:
    """
    Uploads a file to Cloudinary.

    Returns:
    {
        public_id,
        url,
        file_name,
        upload_date,
        resource_type
    }
    """

    try:
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type="auto"
        )
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {e}")
        raise RuntimeError("File upload failed")

    logger.info(f"Cloudinary upload success: {result.get('public_id')}")

    return {
        "public_id": result.get("public_id"),
        "url": result.get("secure_url"),
        "file_name": result.get("original_filename"),
        "upload_date": result.get("created_at"),
        "resource_type": result.get("resource_type")
    }

# -------------------------------------------------
# Delete File
# -------------------------------------------------
def delete_file(public_id: str, resource_type: str = "auto") -> None:
    """
    Deletes a file from Cloudinary using public_id.
    """

    if not public_id:
        return

    try:
        cloudinary.uploader.destroy(
            public_id,
            resource_type=resource_type
        )
        logger.info(f"Cloudinary file deleted: {public_id}")
    except Exception as e:
        logger.error(f"Cloudinary delete failed ({public_id}): {e}")
