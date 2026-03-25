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
    Computes a cryptographically secure hash for a plain-text password.
    
    Utilizes `bcrypt` with a generated salt for defensive salt-hashing, 
    making it computationally expensive for brute-force or dictionary 
    attacks.
    
    Args:
        password (str): The plain-text password to hash.
        
    Returns:
        str: The resulting salt-hashed password string.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# -------------------------------------------------
# Password Verification (SAFE & HARDENED)
# -------------------------------------------------
def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a stored bcrypt hash.
    
    Includes security guards to handle legacy or corrupted hashes gracefully 
    without causing application downtime. Returns a boolean indicating 
    verification success.
    
    Args:
        password (str): The plain-text password to verify.
        hashed_password (str): The stored bcrypt hash string.
        
    Returns:
        bool: True if the password matches the hash, False otherwise.
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
