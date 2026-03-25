from fastapi import APIRouter, Request, HTTPException
from datetime import date
from app.core.supabase import supabase
from app.core.session import require_login
from app.core.logger import get_logger
from app.utils.cloudinary import delete_file

router = APIRouter()
logger = get_logger(__name__)


# -------------------------------------------------
# Helper: Get next delivery_id per order
# -------------------------------------------------
def get_next_delivery_id(order_id: int, org: str) -> int:
    res = (
        supabase.table("deliveries")
        .select("delivery_id")
        .eq("order_id", order_id)
        .eq("org", org)
        .order("delivery_id", desc=True)
        .limit(1)
        .execute()
    )

    return res.data[0]["delivery_id"] + 1 if res.data else 1


# -------------------------------------------------
# 1️⃣ ADD DELIVERY (PARTIAL DELIVERY)
# -------------------------------------------------
@router.post("/")
def add_delivery(payload: dict, request: Request):
    """
    Add a partial delivery for an order.
    """

    org = require_login(request)

    required_fields = ["order_id", "delivery_quantity", "total_amount_received"]

    for field in required_fields:
        if field not in payload:
            raise HTTPException(400, f"Missing field: {field}")

    order_id = payload["order_id"]
    delivery_qty = payload["delivery_quantity"]
    amount_received = payload["total_amount_received"]

    delivery_date = payload.get("delivery_date", date.today().strftime("%Y-%m-%d"))

    if delivery_qty <= 0:
        raise HTTPException(400, "Delivery quantity must be positive")

    if amount_received < 0:
        raise HTTPException(400, "Amount received cannot be negative")

    # Fetch order
    order_res = (
        supabase.table("orders")
        .select("*")
        .eq("order_id", order_id)
        .eq("org", org)
        .execute()
    )

    if not order_res.data:
        raise HTTPException(404, "Order not found")

    order = order_res.data[0]

    remaining_qty = order["quantity"] - order["delivered_quantity"]

    if delivery_qty > remaining_qty:
        raise HTTPException(400, "Delivery quantity exceeds remaining quantity")

    if amount_received > order["pending_amount"]:
        raise HTTPException(400, "Amount received exceeds pending amount")

    delivery_id = get_next_delivery_id(order_id, org)

    delivery_data = {
        "order_id": order_id,
        "delivery_id": delivery_id,
        "org": org,
        "delivery_quantity": delivery_qty,
        "delivery_date": delivery_date,
        "total_amount_received": amount_received,
        "public_id": payload.get("public_id"),
        "url": payload.get("url"),
        "file_name": payload.get("file_name"),
        "upload_date": payload.get("upload_date"),
        "resource_type": payload.get("resource_type"),
        "custom_data": payload.get("custom_data", {}),
    }

    # Insert delivery
    supabase.table("deliveries").insert(delivery_data).execute()

    # Update order
    new_delivered_qty = order["delivered_quantity"] + delivery_qty
    new_pending_amount = order["pending_amount"] - amount_received

    new_status = (
        "Completed"
        if new_pending_amount == 0 and new_delivered_qty == order["quantity"]
        else "Pending"
    )

    supabase.table("orders").update(
        {
            "delivered_quantity": new_delivered_qty,
            "pending_amount": new_pending_amount,
            "status": new_status,
        }
    ).eq("order_id", order_id).eq("org", org).execute()

    logger.info(
        f"Delivery added | Order: {order_id} | Delivery ID: {delivery_id} | Org: {org}"
    )

    return {"message": "Delivery added successfully", "delivery_id": delivery_id}


# -------------------------------------------------
# 2️⃣ LIST DELIVERIES FOR AN ORDER
# -------------------------------------------------
@router.get("/{order_id}")
def list_deliveries(order_id: int, request: Request):
    """
    List all deliveries for a given order.
    """

    org = require_login(request)

    res = (
        supabase.table("deliveries")
        .select("*")
        .eq("order_id", order_id)
        .eq("org", org)
        .order("delivery_id")
        .execute()
    )

    return res.data


# -------------------------------------------------
# 3️⃣ DELETE DELIVERY (ROLLBACK + CLOUDINARY DELETE)
# -------------------------------------------------
@router.delete("/{order_id}/{delivery_id}")
def delete_delivery(order_id: int, delivery_id: int, request: Request):
    """
    Delete a delivery, rollback order values,
    and delete Cloudinary file if exists.
    """

    org = require_login(request)

    delivery_res = (
        supabase.table("deliveries")
        .select("*")
        .eq("order_id", order_id)
        .eq("delivery_id", delivery_id)
        .eq("org", org)
        .execute()
    )

    if not delivery_res.data:
        raise HTTPException(404, "Delivery not found")

    delivery = delivery_res.data[0]

    # Fetch order
    order_res = (
        supabase.table("orders")
        .select("*")
        .eq("order_id", order_id)
        .eq("org", org)
        .execute()
    )

    order = order_res.data[0]

    # 🔥 DELETE CLOUDINARY FILE FIRST
    if delivery.get("public_id"):
        delete_file(
            public_id=delivery["public_id"],
            resource_type=delivery.get("resource_type", "auto"),
        )

    # Rollback calculations
    new_delivered_qty = order["delivered_quantity"] - delivery["delivery_quantity"]
    new_pending_amount = order["pending_amount"] + delivery["total_amount_received"]

    new_status = (
        "Completed"
        if new_pending_amount == 0 and new_delivered_qty == order["quantity"]
        else "Pending"
    )

    # Delete delivery record
    supabase.table("deliveries").delete().eq("order_id", order_id).eq(
        "delivery_id", delivery_id
    ).eq("org", org).execute()

    # Update order
    supabase.table("orders").update(
        {
            "delivered_quantity": new_delivered_qty,
            "pending_amount": new_pending_amount,
            "status": new_status,
        }
    ).eq("order_id", order_id).eq("org", org).execute()

    logger.warning(
        f"Delivery deleted | Order: {order_id} | Delivery ID: {delivery_id} | Org: {org}"
    )

    return {"message": "Delivery deleted and order rolled back"}
