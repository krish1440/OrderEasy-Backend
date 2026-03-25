from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from app.core.supabase import supabase
from app.core.security import validate_password, hash_password, verify_password
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
def send_otp(body: SendOtpSchema) -> dict:
    """
    Initiates the One-Time Password (OTP) flow via Supabase Auth.
    
    Sends a verification code to the user's email address which is 
    required for subsequent organization registration.
    
    Args:
        body (SendOtpSchema): The schema containing the destination email.
        
    Returns:
        dict: A success message.
        
    Raises:
        HTTPException: If the OTP service fails or email is invalid.
    """
    try:
        # Supabase signInWithOtp sends an email with the OTP code
        res = supabase.auth.sign_in_with_otp({"email": body.email})

        # Note: res.error might be raised as an exception depending on the client version,
        # or returned in res. If this client raises, the try/except catches it.
        # If it returns an object with error property:
        if hasattr(res, "error") and res.error:
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
def signup(body: SignupSchema) -> dict:
    """
    Registers a new organization following successful OTP verification.
    
    This is a two-step process:
    1. Validates the OTP token with Supabase Auth.
    2. Persists the organization and user credentials to the local database.
    
    Args:
        body (SignupSchema): The registration details including OTP and credentials.
        
    Returns:
        dict: A success message confirming registration.
        
    Raises:
        HTTPException: If OTP is invalid, username exists, or password is weak.
    """
    username = body.username
    password = body.password
    organization = body.organization
    email = body.email
    otp = body.otp

    # --- Step 1: Verify OTP ---
    try:
        res = supabase.auth.verify_otp({"email": email, "token": otp, "type": "email"})

        if not res.user:
            raise HTTPException(400, "Invalid OTP or Email")

    except Exception as e:
        logger.error(f"OTP Verifcation Failed: {str(e)}")
        raise HTTPException(400, "Invalid OTP. Please check and try again.")

    # --- Step 2: Check Local Persistence ---
    existing = (
        supabase.table("users").select("username").eq("username", username).execute()
    )

    if existing.data:
        raise HTTPException(400, "Username already exists")

    try:
        validate_password(password)
    except ValueError as e:
        raise HTTPException(400, str(e))

    supabase.table("users").insert(
        {
            "username": username,
            "password": hash_password(password),
            "organization": organization,
            "is_admin": 0,
            "email": email,
        }
    ).execute()

    logger.info(f"Organization registered: {organization}")
    return {"message": "Organization registered successfully"}


# -------------------------------------------------
# 2️⃣ LOGIN (ORG + ADMIN) — SAFE VERSION
# -------------------------------------------------
@router.post("/login")
def login(request: Request, body: LoginSchema) -> dict:
    """
    Authenticates an organization user or a system administrator.
    
    Checks credentials against both the hardcoded admin config and 
    the local users table. On success, initializes a secure session.
    
    Args:
        request (Request): The FastAPI request object for session management.
        body (LoginSchema): The login credentials.
        
    Returns:
        dict: A success message.
        
    Raises:
        HTTPException: If authentication fails for any reason.
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
    res = supabase.table("users").select("*").eq("username", username).execute()

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
def logout(request: Request) -> dict:
    """
    Terminates the current user session.
    
    Args:
        request (Request): The FastAPI request object to clear the session.
        
    Returns:
        dict: A success message.
    """
    request.session.clear()
    return {"message": "Logged out successfully"}


# -------------------------------------------------
# 4️⃣ GET ACCOUNT INFO
# -------------------------------------------------
@router.get("/me")
def get_account_info(request: Request) -> dict:
    """
    Retrieves the profile and organization details for the logged-in user.
    
    Fetches comprehensive information including organization name, email, 
    and custom logo URL from the local database.
    
    Args:
        request (Request): The FastAPI request object for authentication.
        
    Returns:
        dict: The account profile data.
        
    Raises:
        HTTPException: If the user is not found or not logged in.
    """

    org = require_login(request)

    # Admin info
    if request.session.get("is_admin"):
        return {
            "username": request.session.get("username"),
            "organization": "ADMIN",
            "is_admin": True,
        }

    username = request.session.get("username")

    user = (
        supabase.table("users")
        .select("username, organization, is_admin, email, logo_url")
        .eq("username", username)
        .execute()
        .data
    )

    if not user:
        raise HTTPException(404, "User not found")

    return user[0]


# -------------------------------------------------
# 5️⃣ UPDATE LOGO
# -------------------------------------------------
class UpdateLogoSchema(BaseModel):
    logo_url: str


@router.put("/update-logo")
def update_logo(request: Request, body: UpdateLogoSchema) -> dict:
    """
    Updates the custom logo URL for the organization.
    
    Allows organizations to personalize their dashboard by providing a 
    valid image URL (typically from Cloudinary).
    
    Args:
        request (Request): The FastAPI request object for authentication.
        body (UpdateLogoSchema): The new logo URL.
        
    Returns:
        dict: A success message and the updated logo URL.
        
    Raises:
        HTTPException: If the user is an admin or update fails.
    """
    org = require_login(request)

    if request.session.get("is_admin"):
        raise HTTPException(400, "Admin account cannot have a custom logo")

    username = request.session.get("username")

    try:
        supabase.table("users").update({"logo_url": body.logo_url}).eq(
            "username", username
        ).execute()

        logger.info(f"Logo updated for organization: {org}")
        return {"message": "Logo updated successfully", "logo_url": body.logo_url}
    except Exception as e:
        logger.error(f"Failed to update logo for {org}: {str(e)}")
        raise HTTPException(500, "Failed to update logo")


# -------------------------------------------------
# 6️⃣ CHANGE PASSWORD
# -------------------------------------------------
@router.post("/change-password")
def change_password(
    request: Request,
    current_password: str,
    new_password: str,
    confirm_new_password: str,
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

    user = (
        supabase.table("users").select("*").eq("username", username).execute().data[0]
    )

    if not verify_password(current_password, user["password"]):
        raise HTTPException(400, "Current password is incorrect")

    try:
        validate_password(new_password)
    except ValueError as e:
        raise HTTPException(400, str(e))

    supabase.table("users").update({"password": hash_password(new_password)}).eq(
        "username", username
    ).execute()

    return {"message": "Password updated successfully"}


# -------------------------------------------------
# 7️⃣ FORGOT PASSWORD
# -------------------------------------------------
class ForgotPasswordSchema(BaseModel):
    email: str
    redirect_to: str


@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordSchema):
    """
    Sends a password reset email using Supabase Auth.
    Expects redirect_to to point back to the frontend (e.g., http://localhost:3000/#/reset-password).
    """
    try:
        # 1. Trigger Supabase to send a password reset email.
        # Supabase will handle checking if the user exists in its Auth system.
        response = supabase.auth.reset_password_for_email(
            body.email, options={"redirect_to": body.redirect_to}
        )

        # 2. Check for errors in the Supabase response
        if hasattr(response, "error") and response.error:
            logger.error(f"Supabase reset error for {body.email}: {response.error}")
            # We still return success to prevent email enumeration,
            # but we log the error for debugging.

        logger.info(f"Password reset triggered for {body.email}")
        return {
            "message": "If an account with that email exists, we have sent a reset link to it."
        }
    except Exception as e:
        logger.error(f"Failed to process forgot password for {body.email}: {str(e)}")
        # Generic error message to prevent enumeration
        return {
            "message": "If an account with that email exists, we have sent a reset link to it."
        }


# -------------------------------------------------
# 8️⃣ RESET PASSWORD (FINALIZE)
# -------------------------------------------------
class ResetPasswordSchema(BaseModel):
    new_password: str
    access_token: str


@router.post("/reset-password")
def execute_reset_password(body: ResetPasswordSchema):
    """
    Executes the password reset using the token from the email.
    """
    try:
        # Ensure password is valid length
        try:
            validate_password(body.new_password)
        except ValueError as e:
            raise HTTPException(400, str(e))

        # 1. Update the user password in Supabase Auth using their session
        # We need to set the session using the access token first
        supabase.auth.set_session(
            body.access_token, body.access_token
        )  # Refresh token not strictly needed for this one-off

        auth_response = supabase.auth.update_user({"password": body.new_password})

        if not auth_response.user:
            raise Exception("Failed to update password in Auth provider")

        # 2. Update our custom `users` table password field
        # The auth update was successful, so we sync our local password standard
        user_email = auth_response.user.email
        supabase.table("users").update(
            {"password": hash_password(body.new_password)}
        ).eq("email", user_email).execute()

        logger.info(f"Password successfully reset for {user_email}")

        # 3. Log them out so they have to sign in with new credentials
        supabase.auth.sign_out()

        return {"message": "Password successfully reset"}
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        raise HTTPException(
            400, "Invalid or expired reset token, or password update failed."
        )


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

    supabase.table("users").delete().eq("organization", org).execute()

    request.session.clear()

    logger.warning(f"Organization deleted: {org}")
    return {"message": "Account deleted permanently"}
