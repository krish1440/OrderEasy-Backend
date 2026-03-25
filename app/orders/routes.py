from fastapi import APIRouter, Request, HTTPException
from app.core.supabase import supabase
from app.core.session import require_login
from app.core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


# -------------------------------------------------
# Helper: Calculate Order Amounts
# -------------------------------------------------
def calculate_amounts(
    quantity: int, price: float, gst: float, advance: float
) -> tuple[float, float, float]:
    """
    Calculates essential order amounts including basic price, total with GST, and pending balance.

    Args:
        quantity: The number of items in the order.
        price: The price per unit of the product.
        gst: The GST percentage to apply.
        advance: The advance payment received from the customer.

    Returns:
        A tuple containing (basic_price, total_with_gst, pending_amount).
    """
    basic_price = quantity * price
    total_with_gst = basic_price + (basic_price * gst / 100)
    pending_amount = total_with_gst - advance
    return basic_price, total_with_gst, pending_amount


# -------------------------------------------------
# Helper: Get next order_id per org
# -------------------------------------------------
def get_next_order_id(org: str) -> int:
    """
    Retrieves the next sequential order ID for a specific organization.

    Args:
        org: The organization's unique identifier.

    Returns:
        The next integer order ID (starting from 1).
    """
    res = (
        supabase.table("orders")
        .select("order_id")
        .eq("org", org)
        .order("order_id", desc=True)
        .limit(1)
        .execute()
    )

    return res.data[0]["order_id"] + 1 if res.data else 1


# -------------------------------------------------
# 1️⃣ CREATE ORDER
# -------------------------------------------------
@router.post("/")
def create_order(payload: dict, request: Request):
    print(f"DEBUG HEADERS: {request.headers}", flush=True)
    org = require_login(request)

    required_fields = [
        "receiver_name",
        "date",
        "expected_delivery_date",
        "product",
        "quantity",
        "price",
        "gst",
        "advance_payment",
    ]

    for field in required_fields:
        if field not in payload:
            raise HTTPException(400, f"Missing field: {field}")

    # Auto-generate Order ID
    order_id = get_next_order_id(org)

    quantity = payload["quantity"]
    price = payload["price"]
    gst = payload["gst"]
    advance = payload["advance_payment"]

    if quantity <= 0:
        raise HTTPException(400, "Quantity must be positive")

    if price < 0 or gst < 0 or advance < 0:
        raise HTTPException(400, "Price, GST, and advance payment must be non-negative")

    basic_price, total_with_gst, pending_amount = calculate_amounts(
        quantity, price, gst, advance
    )

    if advance > total_with_gst:
        raise HTTPException(400, "Advance payment cannot exceed total order amount")

    order_data = {
        "order_id": order_id,
        "org": org,
        "receiver_name": payload.get("receiver_name"),
        "date": payload.get("date"),
        "expected_delivery_date": payload.get("expected_delivery_date"),
        "product": payload.get("product"),
        "description": payload.get("description"),
        "quantity": quantity,
        "price": price,
        "basic_price": basic_price,
        "gst": gst,
        "advance_payment": advance,
        "total_amount_with_gst": total_with_gst,
        "pending_amount": pending_amount,
        "status": "Completed" if pending_amount == 0 else "Pending",
        "created_by": org,
        "delivered_quantity": 0,
        "url": payload.get("url"),
        "custom_data": payload.get("custom_data", {}),
    }

    try:
        supabase.table("orders").insert(order_data).execute()
    except Exception as e:
        logger.error(f"Order creation failed: {e}")
        raise HTTPException(500, "Failed to create order")

    logger.info(f"Order created: {payload['order_id']} | Org: {org}")
    return {"message": "Order created successfully"}


# -------------------------------------------------
# 2️⃣ GET ALL ORDERS
# -------------------------------------------------
@router.get("/")
def list_orders(request: Request):
    org = require_login(request)

    res = (
        supabase.table("orders")
        .select("*")
        .eq("org", org)
        .order("date", desc=True)
        .execute()
    )

    return res.data


# -------------------------------------------------
# 3️⃣ GET SINGLE ORDER
# -------------------------------------------------
@router.get("/{order_id}")
def get_order(order_id: int, request: Request):
    org = require_login(request)

    res = (
        supabase.table("orders")
        .select("*")
        .eq("order_id", order_id)
        .eq("org", org)
        .execute()
    )

    if not res.data:
        raise HTTPException(404, "Order not found")

    return res.data[0]


# -------------------------------------------------
# 4️⃣ UPDATE ORDER (FIXED LOGIC)
# -------------------------------------------------
@router.put("/{order_id}")
def update_order(order_id: int, payload: dict, request: Request):
    org = require_login(request)

    res = (
        supabase.table("orders")
        .select("*")
        .eq("order_id", order_id)
        .eq("org", org)
        .execute()
    )

    if not res.data:
        raise HTTPException(404, "Order not found")

    order = res.data[0]

    new_quantity = payload.get("quantity", order["quantity"])
    new_price = payload.get("price", order["price"])
    new_gst = payload.get("gst", order["gst"])
    new_advance = payload.get("advance_payment", order["advance_payment"])

    if new_quantity <= 0:
        raise HTTPException(400, "Quantity must be positive")

    if new_price < 0 or new_gst < 0 or new_advance < 0:
        raise HTTPException(400, "Price, GST, and advance payment must be non-negative")

    if new_quantity < order["delivered_quantity"]:
        raise HTTPException(400, "Quantity cannot be less than delivered quantity")

    basic_price, total_with_gst, _ = calculate_amounts(
        new_quantity, new_price, new_gst, new_advance
    )

    if new_advance > total_with_gst:
        raise HTTPException(400, "Advance payment cannot exceed total order amount")

    # ✅ CORRECT RECEIVED MONEY CALCULATION
    delivered_payments = (
        order["total_amount_with_gst"]
        - order["pending_amount"]
        - order["advance_payment"]
    )

    if delivered_payments < 0:
        delivered_payments = 0

    pending_amount = total_with_gst - new_advance - delivered_payments

    if pending_amount < 0:
        raise HTTPException(400, "Update results in negative pending amount")

    update_data = {
        "receiver_name": payload.get("receiver_name", order["receiver_name"]),
        "date": payload.get("date", order["date"]),
        "expected_delivery_date": payload.get(
            "expected_delivery_date", order["expected_delivery_date"]
        ),
        "product": payload.get("product", order["product"]),
        "description": payload.get("description", order["description"]),
        "quantity": new_quantity,
        "price": new_price,
        "basic_price": basic_price,
        "gst": new_gst,
        "advance_payment": new_advance,
        "total_amount_with_gst": total_with_gst,
        "pending_amount": pending_amount,
        "status": "Completed" if pending_amount == 0 else "Pending",
        "url": payload.get("url", order.get("url")),
        "custom_data": payload.get("custom_data", order.get("custom_data", {})),
    }

    supabase.table("orders").update(update_data).eq("order_id", order_id).eq(
        "org", org
    ).execute()

    logger.info(f"Order updated: {order_id} | Org: {org}")
    return {"message": "Order updated successfully"}


# -------------------------------------------------
# 5️⃣ DELETE ORDER
# -------------------------------------------------
@router.delete("/{order_id}")
def delete_order(order_id: int, request: Request):
    org = require_login(request)

    res = (
        supabase.table("orders")
        .select("order_id")
        .eq("order_id", order_id)
        .eq("org", org)
        .execute()
    )

    if not res.data:
        raise HTTPException(404, "Order not found")

    supabase.table("orders").delete().eq("order_id", order_id).eq("org", org).execute()

    logger.warning(f"Order deleted: {order_id} | Org: {org}")
    return {"message": "Order deleted successfully"}
