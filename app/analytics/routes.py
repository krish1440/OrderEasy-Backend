
from fastapi import APIRouter, Request, HTTPException
from app.core.supabase import supabase
from app.core.session import require_login
from app.core.logger import get_logger
from collections import defaultdict
import datetime
from . import forecasting, ai
from pydantic import BaseModel

router = APIRouter()
logger = get_logger(__name__)

class InsightsRequest(BaseModel):
    summary: dict

# @router.post("/ai-insights")
# async def get_ai_insights(req: Request, body: InsightsRequest):
#     org = require_login(req)
#     return {"insights": ai.generate_business_insights(body.summary, org)}

# -------------------------------------------------
# Helper: Extract YYYY-MM from date string
# -------------------------------------------------
def month_key(date_str: str) -> str:
    return date_str[:7]  # assuming YYYY-MM-DD


# -------------------------------------------------
# 1️⃣ DASHBOARD SUMMARY
# -------------------------------------------------
@router.get("/summary")
def dashboard_summary(request: Request):
    """
    High-level dashboard metrics.
    """
    org = require_login(request)

    orders = supabase.table("orders") \
        .select("*") \
        .eq("org", org) \
        .execute().data

    deliveries = supabase.table("deliveries") \
        .select("*") \
        .eq("org", org) \
        .execute().data

    total_orders = len(orders)
    completed_orders = sum(1 for o in orders if o["status"] == "Completed")
    pending_orders = total_orders - completed_orders
    total_units_delivered = sum(d["delivery_quantity"] for d in deliveries)

    return {
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "pending_orders": pending_orders,
        "total_units_delivered": total_units_delivered
    }


# -------------------------------------------------
# 2️⃣ MONTHLY REVENUE TREND
# -------------------------------------------------
@router.get("/revenue/monthly")
def monthly_revenue(request: Request):
    """
    Monthly revenue trend.
    """
    org = require_login(request)

    orders = supabase.table("orders") \
        .select("date,total_amount_with_gst") \
        .eq("org", org) \
        .execute().data

    revenue = defaultdict(float)

    for o in orders:
        revenue[month_key(o["date"])] += o["total_amount_with_gst"]

    return dict(sorted(revenue.items()))


# -------------------------------------------------
# 3️⃣ MONTHLY QUANTITY TREND
# -------------------------------------------------
@router.get("/quantity/monthly")
def monthly_quantity(request: Request):
    """
    Monthly delivered quantity trend.
    """
    org = require_login(request)

    deliveries = supabase.table("deliveries") \
        .select("delivery_date,delivery_quantity") \
        .eq("org", org) \
        .execute().data

    quantity = defaultdict(int)

    for d in deliveries:
        quantity[month_key(d["delivery_date"])] += d["delivery_quantity"]

    return dict(sorted(quantity.items()))


# -------------------------------------------------
# 4️⃣ TOP RECEIVERS (BY REVENUE & QUANTITY)
# -------------------------------------------------
@router.get("/receivers/top")
def top_receivers(request: Request):
    """
    Top receivers by revenue and quantity.
    """
    org = require_login(request)

    orders = supabase.table("orders") \
        .select("receiver_name,quantity,total_amount_with_gst") \
        .eq("org", org) \
        .execute().data

    revenue = defaultdict(float)
    quantity = defaultdict(int)

    for o in orders:
        name = o["receiver_name"]
        revenue[name] += o["total_amount_with_gst"]
        quantity[name] += o["quantity"]

    return {
        "by_revenue": dict(sorted(revenue.items(), key=lambda x: x[1], reverse=True)),
        "by_quantity": dict(sorted(quantity.items(), key=lambda x: x[1], reverse=True))
    }


# -------------------------------------------------
# 5️⃣ PRODUCT ANALYTICS
# -------------------------------------------------
@router.get("/products/top")
def product_analytics(request: Request):
    """
    Top products by quantity and revenue with case-insensitive grouping.
    """
    org = require_login(request)

    orders = supabase.table("orders") \
        .select("product,quantity,total_amount_with_gst,date") \
        .eq("org", org) \
        .execute().data

    product_stats = defaultdict(lambda: {
        "quantity": 0, 
        "revenue": 0.0, 
        "order_count": 0
    })

    for o in orders:
        if not o["product"]: continue
        # Normalize: Strip whitespace and convert to Title Case (iphone -> Iphone)
        p_name = o["product"].strip().title()
        
        product_stats[p_name]["quantity"] += o["quantity"]
        product_stats[p_name]["revenue"] += o["total_amount_with_gst"]
        product_stats[p_name]["order_count"] += 1

    # Convert to list for easier frontend consumption
    result = [
        {"name": name, **stats} 
        for name, stats in product_stats.items()
    ]

    return {
        "products": sorted(result, key=lambda x: x["revenue"], reverse=True)
    }


# -------------------------------------------------
# 6️⃣ CUSTOMER LIFETIME VALUE (CLV)
# -------------------------------------------------
@router.get("/customers/clv")
def customer_lifetime_value(request: Request):
    """
    CLV per receiver.
    """
    org = require_login(request)

    orders = supabase.table("orders") \
        .select("receiver_name,date,total_amount_with_gst") \
        .eq("org", org) \
        .execute().data

    clv = defaultdict(float)
    first_seen = {}
    last_seen = {}

    for o in orders:
        r = o["receiver_name"]
        clv[r] += o["total_amount_with_gst"]

        date = datetime.date.fromisoformat(o["date"])
        first_seen[r] = min(first_seen.get(r, date), date)
        last_seen[r] = max(last_seen.get(r, date), date)

    result = {}
    for r in clv:
        months = max(1, (last_seen[r] - first_seen[r]).days // 30)
        result[r] = {
            "total_clv": clv[r],
            "customer_age_months": months,
            "clv_per_month": clv[r] / months
        }

    return result


# -------------------------------------------------
# 7️⃣ CUSTOMER RETENTION
# -------------------------------------------------
@router.get("/customers/retention")
def customer_retention(request: Request):
    """
    Repeat customer rate.
    """
    org = require_login(request)

    orders = supabase.table("orders") \
        .select("receiver_name") \
        .eq("org", org) \
        .execute().data

    counts = defaultdict(int)
    for o in orders:
        counts[o["receiver_name"]] += 1

    total_customers = len(counts)
    repeat_customers = sum(1 for c in counts.values() if c > 1)

    return {
        "total_customers": total_customers,
        "repeat_customers": repeat_customers,
        "repeat_rate": (
            repeat_customers / total_customers if total_customers else 0
        )
    }
