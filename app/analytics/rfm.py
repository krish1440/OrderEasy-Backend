from fastapi import APIRouter, Request, HTTPException
from app.core.supabase import supabase
from app.core.session import require_login
from collections import defaultdict
import pandas as pd

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
def rfm_segmentation(request: Request) -> dict:
    """
    Performs Recency, Frequency, and Monetary (RFM) analysis on customer data.
    
    Segments customers into behavioral groups (VIP, Loyal, Occasional, At-Risk) 
    using quartile-based statistical scoring. This analysis provides actionable 
    insights for targeted marketing and retention strategies.
    
    Args:
        request (Request): The FastAPI request object for authentication.
        
    Returns:
        dict: A comprehensive report with segment counts, customer lists, 
              and the detailed RFM scoring table.
    """

    org = require_login(request)

    orders = (
        supabase.table("orders")
        .select("receiver_name,date,total_amount_with_gst")
        .eq("org", org)
        .execute()
        .data
    )

    if not orders:
        raise HTTPException(400, "No order data available for RFM analysis")

    df = pd.DataFrame(orders)
    df["date"] = pd.to_datetime(df["date"])

    today = df["date"].max()

    # -------------------------------------------------
    # 2. Compute Recency, Frequency, and Monetary (RFM)
    # -------------------------------------------------
    # Recency: Days since last order
    # Frequency: Total order count
    # Monetary: Total revenue with GST
    rfm = df.groupby("receiver_name").agg(
        {
            "date": lambda x: (today - x.max()).days,
            "receiver_name": "count",
            "total_amount_with_gst": "sum",
        }
    )
    # -------------------------------------------------
    # Guard: Ensure enough customers for quartile-based RFM
    # -------------------------------------------------
    if len(rfm) < 4:
        raise HTTPException(
            status_code=400,
            detail="Not enough customers for RFM segmentation (minimum 4 required)",
        )

    rfm.columns = ["recency", "frequency", "monetary"]

    # -------------------------------------------------
    # 3. Scoring (Quartiles)
    # -------------------------------------------------
    # R: 1 (Worst) to 4 (Best - Most Recent)
    rfm["R_score"] = pd.qcut(rfm["recency"], 4, labels=[4, 3, 2, 1])
    
    # F: 1 (Worst) to 4 (Best - Most Frequent)
    rfm["F_score"] = pd.qcut(
        rfm["frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4]
    )
    
    # M: 1 (Worst) to 4 (Best - Highest Spending)
    rfm["M_score"] = pd.qcut(rfm["monetary"], 4, labels=[1, 2, 3, 4])
    
    # Combined Score (3 to 12)
    rfm["RFM_Score"] = (
        rfm["R_score"].astype(int)
        + rfm["F_score"].astype(int)
        + rfm["M_score"].astype(int)
    )

    # -------------------------------------------------
    # 4. Segment Assignment
    # -------------------------------------------------
    def segment(row: pd.Series) -> str:
        """
        Maps a combined RFM score to a business-meaningful category.
        
        Args:
            row (pd.Series): A row from the RFM DataFrame.
            
        Returns:
            str: The segment identifier.
        """
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
    # 5. Output Formatting
    # -------------------------------------------------
    # Group results by segment for frontend visualization
    segment_customers = defaultdict(list)

    for customer, row in rfm.iterrows():
        segment_customers[row["segment"]].append(customer)

    return {
        "segments": {
            segment: {
                "customers": customers,
                "count": len(customers),
                "business_explanation": SEGMENT_MEANINGS[segment],
            }
            for segment, customers in segment_customers.items()
        },
        "rfm_table": rfm.reset_index().to_dict(orient="records"),
    }
