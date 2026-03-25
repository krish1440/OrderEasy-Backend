import bcrypt
import re


# -------------------------------------------------
# Password Validation Rules
# -------------------------------------------------
def validate_password(password: str) -> None:
    """
    Enforces organizational security policies for password complexity.
    
    Validation criteria:
    - Length: Minimum 6 characters.
    - Complexity: Must contain at least one letter, one digit, and one 
      special character (e.g., !, @, #).
    
    Args:
        password (str): The plain-text password to validate.
        
    Raises:
        ValueError: If the password fails any complexity or length check.
    """

    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters long")

    if not re.search(r"[A-Za-z]", password):
        raise ValueError("Password must contain at least one letter")

    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Password must contain at least one special character")


# -------------------------------------------------
# Password Hashing
# -------------------------------------------------
def hash_password(password: str) -> str:
    """
    Hashes password using bcrypt.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# -------------------------------------------------
# Password Verification (SAFE & HARDENED)
# -------------------------------------------------
def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifies plain password against stored hash.
    Never crashes the application.
    Returns False for any invalid / corrupted password.
    """

    # Guard against empty / invalid stored values
    if not hashed_password or not isinstance(hashed_password, str):
        return False

    # bcrypt hashes always start with $2
    if not hashed_password.startswith("$2"):
        return False

    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        # Invalid salt or corrupted hash
        return False
