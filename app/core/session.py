from fastapi import Request, HTTPException


# -------------------------------------------------
# Require Organization Login
# -------------------------------------------------
def require_login(request: Request) -> str:
    """
    Ensures the user is logged in.
    Returns organization name.
    """
    if "org" not in request.session:
        raise HTTPException(status_code=401, detail="Authentication required")

    return request.session["org"]


# -------------------------------------------------
# Require Admin Access
# -------------------------------------------------
def require_admin(request: Request) -> None:
    """
    Ensures the user is admin.
    """
    if not request.session.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")


# -------------------------------------------------
# Organization Scope Validation
# -------------------------------------------------
def validate_org_access(record_org: str, request: Request) -> None:
    """
    Ensures organization can access only its own data.
    Admin bypasses this check.
    """
    if request.session.get("is_admin"):
        return

    session_org = request.session.get("org")

    if record_org != session_org:
        raise HTTPException(
            status_code=403, detail="Access denied for this organization"
        )
