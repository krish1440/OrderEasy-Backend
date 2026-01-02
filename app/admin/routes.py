from fastapi import APIRouter, Request, HTTPException
from app.core.supabase import supabase
from app.core.session import require_admin
from app.core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# -------------------------------------------------
# 1️⃣ LIST ALL ORGANIZATIONS
# -------------------------------------------------
@router.get("/organizations")
def list_organizations(request: Request):
    """
    Admin: View all registered organizations.
    """
    require_admin(request)

    res = supabase.table("users") \
        .select("username, organization, is_admin") \
        .execute()

    return res.data


# -------------------------------------------------
# 2️⃣ GET ORGANIZATION DETAILS
# -------------------------------------------------
@router.get("/organizations/{organization}")
def get_organization_details(organization: str, request: Request):
    """
    Admin: Get organization summary.
    """
    require_admin(request)

    orders_count = supabase.table("orders") \
        .select("order_id", count="exact") \
        .eq("org", organization) \
        .execute().count

    deliveries_count = supabase.table("deliveries") \
        .select("delivery_id", count="exact") \
        .eq("org", organization) \
        .execute().count

    return {
        "organization": organization,
        "orders_count": orders_count,
        "deliveries_count": deliveries_count
    }


# -------------------------------------------------
# 3️⃣ DELETE ORGANIZATION (FULL CLEANUP)
# -------------------------------------------------
@router.delete("/organizations/{organization}")
def delete_organization(organization: str, request: Request):
    """
    Admin: Permanently delete an organization.
    """

    require_admin(request)

    # ❌ Prevent admin self-delete
    if organization.upper() == "ADMIN":
        raise HTTPException(400, "Admin account cannot be deleted")

    # Check organization exists
    user = supabase.table("users") \
        .select("organization") \
        .eq("organization", organization) \
        .execute()

    if not user.data:
        raise HTTPException(404, "Organization not found")

    # Delete organization user
    # Orders & deliveries auto-delete via FK cascade
    supabase.table("users") \
        .delete() \
        .eq("organization", organization) \
        .execute()

    logger.warning(f"Admin deleted organization: {organization}")

    return {
        "message": f"Organization '{organization}' deleted permanently"
    }
