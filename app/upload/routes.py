from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from app.utils.cloudinary import upload_file
from app.core.session import require_login
from app.core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/")
async def upload(request: Request, file: UploadFile = File(...)):
    """
    Generic file upload endpoint.
    Returns Cloudinary metadata (url, public_id, etc.)
    """
    org = require_login(request)
    
    if not file:
        raise HTTPException(400, "No file provided")

    try:
        # file.file is the actual SpooledTemporaryFile
        result = upload_file(file.file, folder="ordereasy")
        return result
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(500, f"Upload failed: {str(e)}")
