from datetime import date, datetime, timedelta
from fastapi import APIRouter, Request, HTTPException
from app.core.supabase import supabase
from app.core.session import require_login
from app.core.logger import get_logger
from app.core.email import send_admin_pending_orders_alert

router = APIRouter()
logger = get_logger(__name__)


# -------------------------------------------------
# Helper: Calculate Order Amounts
# -------------------------------------------------
def calculate_amounts(quantity: int, price: float, gst: float, advance: float) -> tuple[float, float, float]:
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
# 🔔 5-DAY PENDING ORDER ALERT TRIGGER (CRON / MULTI-TENANT)
# -------------------------------------------------
@router.get("/check-5day-alerts")
def check_5day_pending_alerts(token: str = None):
    """
    Checks Supabase database for pending orders with an expected delivery date arriving within 5 days.
    Groups orders by organization (user account), fetches each user's email address,
    and sends a SINGLE batched email alert to each user containing ONLY their own orders.
    Marks `admin_alert_sent = True` to guarantee NO duplicate alerts for the same order.
    Requires `token` matching CRON_SECRET_TOKEN environment variable for security.
    """
    import os
    cron_secret = os.getenv("CRON_SECRET_TOKEN", "ordereasy_cron_secret_2026")
    if token != cron_secret:
        raise HTTPException(401, "Unauthorized: Invalid or missing cron security token.")

    try:
        today = date.today()
        five_days_hence = today + timedelta(days=5)

        # Query pending orders approaching delivery date (strictly status == Pending)
        res = (
            supabase.table("orders")
            .select("*")
            .eq("status", "Pending")
            .lte("expected_delivery_date", five_days_hence.isoformat())
            .execute()
        )

        orders_data = res.data or []

        # Filter out orders that have already received an alert
        unnotified_orders = [
            o for o in orders_data
            if not o.get("admin_alert_sent", False)
        ]

        if not unnotified_orders:
            return {
                "status": "ok",
                "message": "No pending orders approaching 5-day delivery deadline.",
                "count": 0
            }

        # Group unnotified orders by organization / user
        org_orders_map = {}
        for o in unnotified_orders:
            org_key = o.get("org") or o.get("created_by") or "default"
            if org_key not in org_orders_map:
                org_orders_map[org_key] = []
            org_orders_map[org_key].append(o)

        # Fetch user email addresses for each organization from Supabase
        user_res = supabase.table("users").select("organization, email").execute()
        user_email_map = {}
        if user_res.data:
            for u in user_res.data:
                if u.get("organization") and u.get("email"):
                    user_email_map[u["organization"]] = u["email"]

        sent_count = 0
        total_emails_sent = 0

        # Send personalized batched email to each user/organization
        for org_key, org_orders in org_orders_map.items():
            # Get user's email or fallback to admin email
            recipient_email = user_email_map.get(org_key)
            if not recipient_email and "@" in org_key:
                recipient_email = org_key

            email_sent = send_admin_pending_orders_alert(org_orders, recipient_email=recipient_email)

            if email_sent:
                total_emails_sent += 1
                sent_count += len(org_orders)
                # Mark orders as alerted in Supabase
                for order in org_orders:
                    order_db_id = order.get("id") or order.get("order_id")
                    try:
                        if order.get("id"):
                            supabase.table("orders").update({"admin_alert_sent": True}).eq("id", order["id"]).execute()
                        else:
                            supabase.table("orders").update({"admin_alert_sent": True}).eq("order_id", order["order_id"]).execute()
                    except Exception as update_err:
                        logger.error(f"Failed to update admin_alert_sent for order {order_db_id}: {update_err}")

        logger.info(f"Successfully processed 5-day alert for {sent_count} order(s) across {total_emails_sent} user(s).")
        return {
            "status": "success",
            "message": f"Successfully sent 5-day alert email to {total_emails_sent} user(s) for {sent_count} pending order(s).",
            "emails_sent": total_emails_sent,
            "orders_processed": sent_count
        }

    except Exception as e:
        logger.error(f"Error checking 5-day pending alerts: {e}")
        return {"status": "error", "message": str(e)}


# -------------------------------------------------
# 1️⃣ CREATE ORDER
# -------------------------------------------------
@router.post("/")
def create_order(payload: dict, request: Request):
    """
    Creates a new order for the organization.
    
    Validates all required fields, calculates totals, and handles database insertion.
    
    Args:
        payload (dict): The order details from the request body.
        request (Request): The FastAPI request object for authentication.
        
    Returns:
        dict: A success message and order confirmation.
    """
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
    """
    Retrieves a list of all orders belonging to the logged-in organization.
    
    Args:
        request (Request): The FastAPI request object for authentication.
        
    Returns:
        list: A list of order records sorted by date.
    """
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
    """
    Retrieves the full details of a specific order by its ID.
    
    Args:
        order_id (int): The ID of the order to retrieve.
        request (Request): The FastAPI request object for authentication.
        
    Returns:
        dict: The order details.
    """
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
    """
    Updates an existing order with new details.
    
    Performs complex recalulation of totals and pending amounts based on current state.
    
    Args:
        order_id (int): The ID of the order to update.
        payload (dict): The fields to update.
        request (Request): The FastAPI request object for authentication.
        
    Returns:
        dict: A success message.
    """
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
    """
    Permanently deletes an order record from the system.
    
    Args:
        order_id (int): The ID of the order to delete.
        request (Request): The FastAPI request object for authentication.
        
    Returns:
        dict: A success message.
    """
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
