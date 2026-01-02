from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from app.core.supabase import supabase
from app.core.security import (
    validate_password,
    hash_password,
    verify_password
)
from app.core.session import require_login
from app.core.config import ADMIN_USERNAME, ADMIN_PASSWORD
from app.core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

class LoginSchema(BaseModel):
    username: str
    password: str

class SendOtpSchema(BaseModel):
    email: str

class SignupSchema(BaseModel):
    username: str
    password: str
    organization: str
    email: str
    otp: str

# -------------------------------------------------
# 1️⃣ SEND OTP
# -------------------------------------------------
@router.post("/send-otp")
def send_otp(body: SendOtpSchema):
    """
    Triggers Supabase to send an OTP to the provided email.
    """
    try:
        # Supabase signInWithOtp sends an email with the OTP code
        res = supabase.auth.sign_in_with_otp({
            "email": body.email
        })
        
        # Note: res.error might be raised as an exception depending on the client version, 
        # or returned in res. If this client raises, the try/except catches it.
        # If it returns an object with error property:
        if hasattr(res, 'error') and res.error:
             raise HTTPException(400, str(res.error))

        logger.info(f"OTP sent to {body.email}")
        return {"message": "OTP sent successfully"}
    except Exception as e:
        logger.error(f"Error sending OTP: {str(e)}")
        raise HTTPException(400, f"Failed to send OTP: {str(e)}")

# -------------------------------------------------
# 2️⃣ ORGANIZATION SIGNUP (WITH OTP VERIFICATION)
# -------------------------------------------------
@router.post("/signup")
def signup(body: SignupSchema):
    """
    Registers a new organization after verifying OTP.
    Step 1: Verify OTP with Supabase.
    Step 2: Create user in local DB.
    """
    username = body.username
    password = body.password
    organization = body.organization
    email = body.email
    otp = body.otp

    # --- Step 1: Verify OTP ---
    try:
        res = supabase.auth.verify_otp({
            "email": email,
            "token": otp,
            "type": "email"
        })
        
        if not res.user:
            raise HTTPException(400, "Invalid OTP or Email")
            
    except Exception as e:
        logger.error(f"OTP Verifcation Failed: {str(e)}")
        raise HTTPException(400, "Invalid OTP. Please check and try again.")

    # --- Step 2: Check Local Persistence ---
    existing = supabase.table("users") \
        .select("username") \
        .eq("username", username) \
        .execute()

    if existing.data:
        raise HTTPException(400, "Username already exists")

    try:
        validate_password(password)
    except ValueError as e:
        raise HTTPException(400, str(e))

    supabase.table("users").insert({
        "username": username,
        "password": hash_password(password),
        "organization": organization,
        "is_admin": 0,
        "email": email
    }).execute()

    logger.info(f"Organization registered: {organization}")
    return {"message": "Organization registered successfully"}


# -------------------------------------------------
# 2️⃣ LOGIN (ORG + ADMIN) — SAFE VERSION
# -------------------------------------------------
@router.post("/login")
def login(request: Request, body: LoginSchema):
    """
    Login for organization or admin.
    Never throws 500.
    """
    username = body.username
    password = body.password

    # -------- ADMIN LOGIN (ONLY IF CONFIGURED) --------
    if ADMIN_USERNAME and ADMIN_PASSWORD:
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            request.session.clear()
            request.session["org"] = "ADMIN"
            request.session["is_admin"] = True
            request.session["username"] = ADMIN_USERNAME

            logger.info("Admin logged in")
            return {"message": "Admin logged in successfully"}

    # -------- ORG LOGIN --------
    res = supabase.table("users") \
        .select("*") \
        .eq("username", username) \
        .execute()

    if not res.data:
        raise HTTPException(401, "Invalid username or password")

    user = res.data[0]

    if not verify_password(password, user["password"]):
        raise HTTPException(401, "Invalid username or password")

    request.session.clear()
    request.session["org"] = user["organization"]
    request.session["username"] = user["username"]
    request.session["is_admin"] = False

    logger.info(f"Organization logged in: {user['organization']}")
    return {"message": "Login successful"}


# -------------------------------------------------
# 3️⃣ LOGOUT
# -------------------------------------------------
@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out successfully"}


# -------------------------------------------------
# 4️⃣ GET ACCOUNT INFO
# -------------------------------------------------
@router.get("/me")
def get_account_info(request: Request):
    """
    Returns logged-in account details.
    """

    org = require_login(request)

    # Admin info
    if request.session.get("is_admin"):
        return {
            "username": request.session.get("username"),
            "organization": "ADMIN",
            "is_admin": True
        }

    username = request.session.get("username")

    user = supabase.table("users") \
        .select("username, organization, is_admin, email") \
        .eq("username", username) \
        .execute().data

    if not user:
        raise HTTPException(404, "User not found")

    return user[0]


# -------------------------------------------------
# 5️⃣ CHANGE PASSWORD
# -------------------------------------------------
@router.post("/change-password")
def change_password(
    request: Request,
    current_password: str,
    new_password: str,
    confirm_new_password: str
):
    """
    Change password with full validation.
    """

    org = require_login(request)

    if request.session.get("is_admin"):
        raise HTTPException(400, "Admin password cannot be changed here")

    if new_password != confirm_new_password:
        raise HTTPException(400, "New password and confirmation do not match")

    if current_password == new_password:
        raise HTTPException(400, "New password must be different from old password")

    username = request.session.get("username")

    user = supabase.table("users") \
        .select("*") \
        .eq("username", username) \
        .execute().data[0]

    if not verify_password(current_password, user["password"]):
        raise HTTPException(400, "Current password is incorrect")

    try:
        validate_password(new_password)
    except ValueError as e:
        raise HTTPException(400, str(e))

    supabase.table("users").update({
        "password": hash_password(new_password)
    }).eq("username", username).execute()

    logger.info(f"Password changed for org: {org}")
    return {"message": "Password changed successfully"}


# -------------------------------------------------
# 6️⃣ DELETE ACCOUNT
# -------------------------------------------------
@router.delete("/delete-account")
def delete_account(request: Request):
    """
    Permanently deletes organization account.
    """

    org = require_login(request)

    if request.session.get("is_admin"):
        raise HTTPException(400, "Admin account cannot be deleted")

    supabase.table("users") \
        .delete() \
        .eq("organization", org) \
        .execute()

    request.session.clear()

    logger.warning(f"Organization deleted: {org}")
    return {"message": "Account deleted permanently"}
