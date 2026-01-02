from fastapi import APIRouter, Request, HTTPException
from app.core.supabase import supabase
from app.core.session import require_login
from collections import defaultdict
import pandas as pd
import datetime

router = APIRouter()

# -------------------------------------------------
# Segment Definitions (BUSINESS MEANING)
# -------------------------------------------------
SEGMENT_MEANINGS = {
    "VIP Customers": (
        "Recent, frequent, and high-spending customers. "
        "Focus on retaining them with premium support and exclusive offers."
    ),
    "Loyal Customers": (
        "Regular buyers who purchase frequently. "
        "Offer loyalty rewards to keep them engaged."
    ),
    "Occasional Customers": (
        "Infrequent buyers with moderate spending. "
        "Encourage repeat purchases with promotions."
    ),
    "At-Risk Customers": (
        "Customers who have not ordered recently. "
        "Reach out with re-engagement campaigns."
    ),
}

# -------------------------------------------------
# 🔁 RFM CALCULATION
# -------------------------------------------------
@router.get("/rfm")
def rfm_segmentation(request: Request):
    """
    Returns:
    - RFM table
    - Customer segments
    - Customer names per segment
    - Segment explanations
    """

    org = require_login(request)

    orders = supabase.table("orders") \
        .select("receiver_name,date,total_amount_with_gst") \
        .eq("org", org) \
        .execute().data

    if not orders:
        raise HTTPException(400, "No order data available for RFM analysis")

    df = pd.DataFrame(orders)
    df["date"] = pd.to_datetime(df["date"])

    today = df["date"].max()

    # -------------------------------------------------
    # Compute R, F, M
    # -------------------------------------------------
    rfm = df.groupby("receiver_name").agg({
        "date": lambda x: (today - x.max()).days,
        "receiver_name": "count",
        "total_amount_with_gst": "sum"
    })
    # -------------------------------------------------
    # Guard: Ensure enough customers for quartile-based RFM
    # -------------------------------------------------
    if len(rfm) < 4:
        raise HTTPException(
        status_code=400,
        detail="Not enough customers for RFM segmentation (minimum 4 required)"
    )


    rfm.columns = ["recency", "frequency", "monetary"]

    # -------------------------------------------------
    # Scoring (Quartiles)
    # -------------------------------------------------
    rfm["R_score"] = pd.qcut(
        rfm["recency"],
        4,
        labels=[4, 3, 2, 1]
    )

    rfm["F_score"] = pd.qcut(
        rfm["frequency"].rank(method="first"),
        4,
        labels=[1, 2, 3, 4]
    )

    rfm["M_score"] = pd.qcut(
        rfm["monetary"],
        4,
        labels=[1, 2, 3, 4]
    )

    rfm["RFM_Score"] = (
        rfm["R_score"].astype(int) +
        rfm["F_score"].astype(int) +
        rfm["M_score"].astype(int)
    )

    # -------------------------------------------------
    # Segment Assignment
    # -------------------------------------------------
    def segment(row):
        if row["RFM_Score"] >= 10:
            return "VIP Customers"
        elif row["RFM_Score"] >= 8:
            return "Loyal Customers"
        elif row["RFM_Score"] >= 6:
            return "Occasional Customers"
        else:
            return "At-Risk Customers"

    rfm["segment"] = rfm.apply(segment, axis=1)

    # -------------------------------------------------
    # Output Formatting
    # -------------------------------------------------
    segment_customers = defaultdict(list)

    for customer, row in rfm.iterrows():
        segment_customers[row["segment"]].append(customer)

    return {
        "segments": {
            segment: {
                "customers": customers,
                "count": len(customers),
                "business_explanation": SEGMENT_MEANINGS[segment]
            }
            for segment, customers in segment_customers.items()
        },
        "rfm_table": rfm.reset_index().to_dict(orient="records")
    }
