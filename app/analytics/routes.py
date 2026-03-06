
from fastapi import APIRouter, Request, HTTPException
from app.core.supabase import supabase
from app.core.session import require_login
from app.core.logger import get_logger
from collections import defaultdict
import datetime
from . import forecasting, ai
from pydantic import BaseModel
from google import genai as google_genai
import os

# Read Gemini API key securely from environment (.env file)
_gemini_key = os.environ.get("GEMINI_API_KEY")
if not _gemini_key:
    raise RuntimeError("GEMINI_API_KEY not set in environment variables.")
GEMINI_CLIENT = google_genai.Client(api_key=_gemini_key)

router = APIRouter()
logger = get_logger(__name__)

class InsightsRequest(BaseModel):
    summary: dict

# -------------------------------------------------
# 🤖 AI EXECUTIVE SUMMARY (GEMINI) - Self-contained
# Gathers ALL chart data directly to feed Gemini
# -------------------------------------------------
@router.get("/ai-summary")
def generate_ai_summary(request: Request):
    """
    Self-contained AI summary: fetches all analytics data directly from DB
    and passes the full picture to Gemini for a rich, structured report.
    """
    org = require_login(request)
    import time

    # ---- Gather ALL data from DB ----
    try:
        orders = supabase.table("orders").select("*").eq("org", org).execute().data or []
        deliveries = supabase.table("deliveries").select("*").eq("org", org).execute().data or []
    except Exception as e:
        logger.error(f"DB fetch failed for {org}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics data.")

    # High-level order metrics
    total_orders = len(orders)
    completed = sum(1 for o in orders if o.get("status") == "Completed")
    pending_orders = total_orders - completed
    total_revenue = sum(o.get("total_amount_with_gst", 0) for o in orders)
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders else 0
    pending_payments = sum(o.get("total_amount_with_gst", 0) for o in orders if o.get("payment_status") in ["Pending", "Partial", None, ""])

    # Yearly revenue breakdown
    yearly_rev: dict = defaultdict(float)
    for o in orders:
        if o.get("date"):
            yearly_rev[o["date"][:4]] += o.get("total_amount_with_gst", 0)
    yearly_rev = {k: round(v, 2) for k, v in sorted(yearly_rev.items())}

    # Monthly revenue trend (last 12 months)
    monthly_rev: dict = defaultdict(float)
    for o in orders:
        if o.get("date"):
            monthly_rev[o["date"][:7]] += o.get("total_amount_with_gst", 0)
    sorted_months = sorted(monthly_rev.keys())[-12:]
    monthly_rev_last12 = {m: round(monthly_rev[m], 2) for m in sorted_months}

    # MoM growth rate (last 6 months)
    months_list = sorted(monthly_rev.keys())
    mom_growth = {}
    for i in range(1, len(months_list)):
        prev = monthly_rev[months_list[i-1]]
        curr = monthly_rev[months_list[i]]
        if prev > 0:
            mom_growth[months_list[i]] = round(((curr - prev) / prev) * 100, 1)
    mom_last6 = dict(list(mom_growth.items())[-6:])

    # Top 5 products by revenue and quantity
    product_stats: dict = defaultdict(lambda: {"quantity": 0, "revenue": 0.0, "orders": 0})
    for o in orders:
        if o.get("product"):
            p = o["product"].strip().title()
            product_stats[p]["quantity"] += o.get("quantity", 0)
            product_stats[p]["revenue"] += o.get("total_amount_with_gst", 0)
            product_stats[p]["orders"] += 1
    top_products = sorted(product_stats.items(), key=lambda x: x[1]["revenue"], reverse=True)[:5]
    top_products_data = [{"name": k, **v} for k, v in top_products]

    # Top 5 customers (receivers) by revenue
    cust_rev: dict = defaultdict(float)
    cust_orders: dict = defaultdict(int)
    for o in orders:
        r = o.get("receiver_name", "Unknown")
        cust_rev[r] += o.get("total_amount_with_gst", 0)
        cust_orders[r] += 1
    top_customers = sorted(cust_rev.items(), key=lambda x: x[1], reverse=True)[:5]
    top_customers_data = [{"name": k, "revenue": round(v, 2), "orders": cust_orders[k]} for k, v in top_customers]

    # Delivery performance
    total_deliveries = len(deliveries)
    total_qty_delivered = sum(d.get("delivery_quantity", 0) for d in deliveries)
    total_delivery_amount = sum(d.get("delivery_amount", 0) for d in deliveries)

    # ---- Build structured prompt ----
    prompt = f"""
You are a senior business intelligence analyst preparing a formal executive briefing for the leadership team of an organization called **{org}**.

Based on the comprehensive operational data provided below, produce a well-structured, professional AI Insights Report using clear headings and bullet points. Your response should be 100% data-driven, specific (use exact numbers), and actionable.

=== ORGANIZATION DATA ===

**ORDER OVERVIEW**
- Total Orders: {total_orders} | Completed: {completed} | Pending: {pending_orders}
- Total Revenue (All Time): ₹{total_revenue:,.2f}
- Average Order Value: ₹{avg_order_value:,.2f}
- Outstanding Payments (Pending/Partial): ₹{pending_payments:,.2f}

**YEARLY REVENUE BREAKDOWN**
{yearly_rev}

**MONTHLY REVENUE TREND (Last 12 Months)**
{monthly_rev_last12}

**MONTH-OVER-MONTH REVENUE GROWTH (Last 6 Months, %)**
{mom_last6}

**TOP 5 PRODUCTS BY REVENUE**
{top_products_data}

**TOP 5 CUSTOMERS BY REVENUE**
{top_customers_data}

**DELIVERY OPERATIONS**
- Total Deliveries: {total_deliveries}
- Total Units Delivered: {total_qty_delivered:,}
- Total Delivery Amount Collected: ₹{total_delivery_amount:,.2f}

=== OUTPUT FORMAT (STRICTLY FOLLOW THIS STRUCTURE) ===

## 📊 Business Overview
A 2–3 sentence summary of the overall business health using the high-level metrics.

## 💹 Revenue Performance
- Bullet points analysing revenue trends, year-over-year comparisons, and monthly growth/decline patterns.
- Call out specific months with significant spikes or drops with actual numbers.

## 🏆 Top Performers
- Bullet points for top products: which product drives the most revenue, which has highest volume.
- Bullet points for top customers: who are the highest-value clients.

## ⚠️ Areas of Concern
- Bullet points highlighting risks: pending payments amount, declining months, fulfillment gaps, etc.

## 🚀 Strategic Recommendations
- 3 highly specific, actionable recommendations based on this exact data to improve revenue or operations.

Use **bold** for all specific figures (revenue amounts, product names, customer names, percentages). Be concise but insightful. Avoid generic advice.
"""

    # Retry with exponential backoff for rate limit resilience
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = GEMINI_CLIENT.models.generate_content(
                model='models/gemini-2.5-flash',
                contents=prompt
            )
            return {"summary": response.text}
        except Exception as e:
            err_str = str(e)
            if '429' in err_str and attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 5
                logger.warning(f"Gemini rate limit hit for {org}, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Gemini API Error for {org}: {err_str}")
                raise HTTPException(status_code=503, detail="AI insights temporarily unavailable. Please try again in a moment.")



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
# 🫧 PRODUCT BUBBLE CHART DATA
# Returns per-product: revenue, quantity, order count
# -------------------------------------------------
@router.get("/dashboard/product-bubble")
def product_bubble_data(request: Request):
    org = require_login(request)
    orders = supabase.table("orders").select("product,quantity,total_amount_with_gst").eq("org", org).execute().data or []

    stats: dict = defaultdict(lambda: {"quantity": 0, "revenue": 0.0, "orders": 0})
    for o in orders:
        p = (o.get("product") or "Unknown").strip().title()
        stats[p]["quantity"] += o.get("quantity", 0)
        stats[p]["revenue"] += round(o.get("total_amount_with_gst", 0), 2)
        stats[p]["orders"] += 1

    # Return top 15 products sorted by revenue
    top = sorted(stats.items(), key=lambda x: x[1]["revenue"], reverse=True)[:15]
    return [{"name": k, **v} for k, v in top]


# -------------------------------------------------
# 📋 RECENT ACTIVITY FEED
# Returns last 10 orders with key display fields
# -------------------------------------------------
@router.get("/dashboard/recent-activity")
def recent_activity(request: Request):
    org = require_login(request)
    orders = supabase.table("orders") \
        .select("order_id,product,quantity,total_amount_with_gst,status,pending_amount,receiver_name,date") \
        .eq("org", org) \
        .order("date", desc=True) \
        .limit(10) \
        .execute().data or []

    result = []
    for o in orders:
        total = o.get("total_amount_with_gst", 0)
        pending = o.get("pending_amount", 0)
        
        # Calculate payment status dynamically
        if pending <= 0:
            payment_status = "Paid"
        elif pending < total:
            payment_status = "Partial"
        else:
            payment_status = "Pending"

        result.append({
            "id": str(o.get("order_id", "")),
            "product": (o.get("product") or "—").strip().title(),
            "receiver": (o.get("receiver_name") or "—").strip().title(),
            "amount": round(total, 2),
            "quantity": o.get("quantity", 0),
            "status": o.get("status", "Pending"),
            "payment_status": payment_status,
            "date": o.get("date", ""),
        })

    return result


# -------------------------------------------------
# ⏱️ FULFILLMENT GAP SCATTER PLOT
# Returns recent deliveries with days_gap (Expected vs Actual)
# -------------------------------------------------
@router.get("/dashboard/fulfillment-gap")
def fulfillment_gap(request: Request):
    org = require_login(request)
    from datetime import datetime
    
    # We need both order's expected date and delivery's actual date
    orders = supabase.table("orders").select("order_id,product,expected_delivery_date").eq("org", org).execute().data or []
    deliveries = supabase.table("deliveries").select("order_id,delivery_date").eq("org", org).execute().data or []
    
    # Map order_id to order info
    order_map = {o["order_id"]: o for o in orders if o.get("expected_delivery_date")}
    
    result = []
    # To keep the chart readable, we'll limit to the 50 most recent deliveries
    deliveries_sorted = sorted(deliveries, key=lambda d: d.get("delivery_date", ""), reverse=True)[:50]
    
    for d in deliveries_sorted:
        o_id = d.get("order_id")
        actual_date_str = d.get("delivery_date")
        
        if not actual_date_str or o_id not in order_map:
            continue
            
        expected_date_str = order_map[o_id].get("expected_delivery_date")
        product_name = (order_map[o_id].get("product") or "Unknown").strip().title()
        
        try:
            actual = datetime.strptime(actual_date_str, "%Y-%m-%d").date()
            expected = datetime.strptime(expected_date_str, "%Y-%m-%d").date()
            
            # days_gap: +ve means late (actual > expected), -ve means early (actual < expected)
            days_gap = (actual - expected).days
            
            result.append({
                "order_id": o_id,
                "product": product_name,
                "expected": expected_date_str,
                "actual": actual_date_str,
                "days_gap": days_gap
            })
        except ValueError:
            continue
            
    # Sort chronologically by actual delivery date for the UI timeline
    result.sort(key=lambda x: x["actual"])
    return result


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
