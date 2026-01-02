from fastapi import APIRouter, Request, HTTPException
from app.core.supabase import supabase
from app.core.session import require_login
from collections import defaultdict
import datetime
import pandas as pd
import numpy as np

router = APIRouter()

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def month_key(date_str: str):
    return date_str[:7]

def year_key(date_str: str):
    return date_str[:4]


# -------------------------------------------------
# 1️⃣ CURRENT MONTH DASHBOARD METRICS
# -------------------------------------------------
@router.get("/dashboard/current-month")
def current_month_metrics(request: Request):
    org = require_login(request)
    current_month = datetime.date.today().strftime("%Y-%m")

    orders = supabase.table("orders") \
        .select("*") \
        .eq("org", org) \
        .execute().data

    deliveries = supabase.table("deliveries") \
        .select("*") \
        .eq("org", org) \
        .execute().data

    month_orders = [o for o in orders if month_key(o["date"]) == current_month]

    completed = [o for o in month_orders if o["status"] == "Completed"]
    pending = [o for o in month_orders if o["status"] == "Pending"]

    month_deliveries = [
        d for d in deliveries if month_key(d["delivery_date"]) == current_month
    ]

    return {
        "total_orders": len(month_orders),
        "completed_orders": len(completed),
        "pending_orders": len(pending),
        "units_delivered": sum(d["delivery_quantity"] for d in month_deliveries)
    }


# -------------------------------------------------
# 2️⃣ YEAR-WISE REVENUE SUMMARY
# -------------------------------------------------
@router.get("/revenue/yearly")
def yearly_revenue(request: Request):
    org = require_login(request)

    orders = supabase.table("orders") \
        .select("date,total_amount_with_gst") \
        .eq("org", org) \
        .execute().data

    yearly = defaultdict(float)

    for o in orders:
        yearly[year_key(o["date"])] += o["total_amount_with_gst"]

    return dict(sorted(yearly.items()))


# -------------------------------------------------
# 3️⃣ TOTAL REVENUE & AVERAGE ORDER VALUE
# -------------------------------------------------
@router.get("/revenue/summary")
def revenue_summary(request: Request):
    org = require_login(request)

    orders = supabase.table("orders") \
        .select("total_amount_with_gst") \
        .eq("org", org) \
        .execute().data

    total_revenue = sum(o["total_amount_with_gst"] for o in orders)
    avg_order_value = total_revenue / len(orders) if orders else 0

    return {
        "total_revenue": round(total_revenue, 2),
        "average_order_value": round(avg_order_value, 2)
    }


# -------------------------------------------------
# 4️⃣ MONTH-OVER-MONTH GROWTH %
# -------------------------------------------------
@router.get("/revenue/mom-growth")
def month_over_month_growth(request: Request):
    org = require_login(request)

    orders = supabase.table("orders") \
        .select("date,total_amount_with_gst") \
        .eq("org", org) \
        .execute().data

    revenue = defaultdict(float)

    for o in orders:
        revenue[month_key(o["date"])] += o["total_amount_with_gst"]

    months = sorted(revenue.keys())
    growth = {}

    for i in range(1, len(months)):
        prev = revenue[months[i - 1]]
        curr = revenue[months[i]]
        growth[months[i]] = (
            ((curr - prev) / prev) * 100 if prev > 0 else 0
        )

    return growth


# -------------------------------------------------
# 5️⃣ MONTHLY PENDING AMOUNT TREND
# -------------------------------------------------
@router.get("/pending/monthly")
def monthly_pending_amount(request: Request):
    org = require_login(request)

    orders = supabase.table("orders") \
        .select("date,pending_amount") \
        .eq("org", org) \
        .execute().data

    pending = defaultdict(float)

    for o in orders:
        pending[month_key(o["date"])] += o["pending_amount"]

    return dict(sorted(pending.items()))


# -------------------------------------------------
# 6️⃣ ORDER STATUS DISTRIBUTION
# -------------------------------------------------
@router.get("/orders/status-distribution")
def order_status_distribution(request: Request):
    org = require_login(request)

    orders = supabase.table("orders") \
        .select("status") \
        .eq("org", org) \
        .execute().data

    result = defaultdict(int)
    for o in orders:
        result[o["status"]] += 1

    return result


# -------------------------------------------------
# 7️⃣ ORDER SIZE ANALYSIS (TOP 5 CUSTOMERS)
# -------------------------------------------------
@router.get("/orders/top-customers")
def top_customers_by_order_size(request: Request):
    org = require_login(request)

    orders = supabase.table("orders") \
        .select("receiver_name,date,total_amount_with_gst") \
        .eq("org", org) \
        .execute().data

    df = pd.DataFrame(orders)
    if df.empty:
        return {"top_total": {}, "top_yearly": [], "top_monthly": []}
        
    df["year"] = df["date"].str[:4]
    df["month"] = df["date"].str[:7]

    return {
        "top_total": (
            df.groupby("receiver_name")["total_amount_with_gst"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
            .to_dict()
        ),
        "top_yearly": (
            df.groupby(["year", "receiver_name"])["total_amount_with_gst"]
            .sum()
            .reset_index()
            .groupby("year")
            .apply(lambda x: x.nlargest(5, "total_amount_with_gst"))
            .to_dict(orient="records")
        ),
        "top_monthly": (
            df.groupby(["month", "receiver_name"])["total_amount_with_gst"]
            .sum()
            .reset_index()
            .groupby("month")
            .apply(lambda x: x.nlargest(5, "total_amount_with_gst"))
            .to_dict(orient="records")
        )
    }


# -------------------------------------------------
# 8️⃣ DELIVERY PERFORMANCE METRICS
# -------------------------------------------------
@router.get("/metrics/delivery-performance")
def delivery_performance_metrics(request: Request):
    org = require_login(request)

    # Fetch Data
    dels = supabase.table("deliveries").select("*").eq("org", org).execute().data
    orders = supabase.table("orders").select("order_id").eq("org", org).execute().data

    # Calculate
    total_deliveries = len(dels)
    total_qty = sum(d["delivery_quantity"] for d in dels)
    total_amt = sum(d["total_amount_received"] for d in dels)
    
    return {
        "total_orders": len(orders),
        "total_deliveries": total_deliveries,
        "total_quantity": total_qty,
        "total_amount": total_amt
    }


# -------------------------------------------------
# 9️⃣ DELIVERY SIZE DISTRIBUTION (HISTOGRAM)
# -------------------------------------------------
@router.get("/charts/delivery-distribution")
def delivery_distribution(request: Request):
    org = require_login(request)
    
    dels = supabase.table("deliveries").select("delivery_quantity").eq("org", org).execute().data
    
    if not dels:
        return []

    quantities = [d["delivery_quantity"] for d in dels]
    
    # Define bins
    bins = [0, 10, 20, 50, 100, 500, 1000, 999999]
    labels = ["0-10", "10-20", "20-50", "50-100", "100-500", "500-1k", "1k+"]
    
    counts = defaultdict(int)
    for q in quantities:
        for i, upper in enumerate(bins[1:]):
            if q <= upper:
                counts[labels[i]] += 1
                break
                
    return [{"range": k, "count": counts[k]} for k in labels if counts[k] > 0]


# -------------------------------------------------
# 🔟 REVENUE SCATTER PLOT
# -------------------------------------------------
@router.get("/charts/scatter-revenue-qty")
def scatter_revenue_qty(request: Request):
    org = require_login(request)
    
    orders = supabase.table("orders") \
        .select("order_id,quantity,total_amount_with_gst,product") \
        .eq("org", org) \
        .execute().data
        
    return [
        {
            "order_id": o["order_id"],
            "quantity": o["quantity"],
            "revenue": o["total_amount_with_gst"],
            "product": o["product"] or "Unknown"
        }
        for o in orders
    ]


# -------------------------------------------------
# 1️⃣1️⃣ DELIVERY HEATMAP
# -------------------------------------------------
@router.get("/charts/delivery-heatmap")
def delivery_heatmap(request: Request):
    org = require_login(request)
    
    dels = supabase.table("deliveries").select("delivery_date").eq("org", org).execute().data
    
    counts = defaultdict(int)
    for d in dels:
        # Assuming format YYYY-MM-DD
        date = d["delivery_date"].split("T")[0]
        counts[date] += 1
        
    return [{"date": k, "count": v} for k, v in counts.items()]


# -------------------------------------------------
# 1️⃣2️⃣ EXPECTED DELIVERY SCHEDULE (PENDING ONLY)
# -------------------------------------------------
@router.get("/charts/expected-delivery-schedule")
def expected_delivery_schedule(request: Request):
    org = require_login(request)
    
    # Fetch only PENDING orders
    orders = supabase.table("orders") \
        .select("expected_delivery_date,quantity") \
        .eq("org", org) \
        .eq("status", "Pending") \
        .neq("expected_delivery_date", "None") \
        .execute().data
        
    schedule = defaultdict(int)
    for o in orders:
        # Standardize date format YYYY-MM-DD
        if o["expected_delivery_date"]:
            date_str = o["expected_delivery_date"].split("T")[0]
            schedule[date_str] += o["quantity"]
            
    return [{"date": k, "total_quantity": v} for k, v in schedule.items()]
