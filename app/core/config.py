import os
from dotenv import load_dotenv

# -------------------------------------------------
# Load environment variables
# -------------------------------------------------
load_dotenv()

# -------------------------------------------------
# Cloudinary Config
# -------------------------------------------------
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# -------------------------------------------------
# Supabase Config
# -------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# -------------------------------------------------
# Admin Credentials (System Level)
# -------------------------------------------------
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# -------------------------------------------------
# Session / Security
# -------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY")

# -------------------------------------------------
# Validation (Fail Fast)
# -------------------------------------------------
REQUIRED_VARS = {
    "CLOUDINARY_CLOUD_NAME": CLOUDINARY_CLOUD_NAME,
    "CLOUDINARY_API_KEY": CLOUDINARY_API_KEY,
    "CLOUDINARY_API_SECRET": CLOUDINARY_API_SECRET,
    "SUPABASE_URL": SUPABASE_URL,
    "SUPABASE_KEY": SUPABASE_KEY,
    "ADMIN_USERNAME": ADMIN_USERNAME,
    "ADMIN_PASSWORD": ADMIN_PASSWORD,
    "SECRET_KEY": SECRET_KEY,
}

missing = [k for k, v in REQUIRED_VARS.items() if not v]

if missing:
    raise RuntimeError(
        f"Missing required environment variables: {', '.join(missing)}"
    )
