from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from app.core.supabase import supabase
from app.core.session import require_login
from app.core.logger import get_logger

from typing import Optional
import pandas as pd
import io
import zipfile

router = APIRouter()
logger = get_logger(__name__)

# -------------------------------------------------
# Helper: Convert DataFrame to Excel
# -------------------------------------------------
def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    output.seek(0)
    return output.read()


# -------------------------------------------------
# 1️⃣ EXPORT ORDER LIST (STATUS + DATE RANGE)
# -------------------------------------------------
@router.get("/orders")
def export_orders(
    request: Request,
    status: Optional[str] = None,        # Completed / Pending / None (All)
    start_date: Optional[str] = None,    # YYYY-MM-DD
    end_date: Optional[str] = None       # YYYY-MM-DD
):
    org = require_login(request)

    query = supabase.table("orders").select("*").eq("org", org)

    if status and status.lower() != "all":
        query = query.eq("status", status)

    if start_date:
        query = query.gte("date", start_date)

    if end_date:
        query = query.lte("date", end_date)

    orders = query.execute().data

    if not orders:
        raise HTTPException(404, "No orders found for selected filters")

    df = pd.DataFrame(orders)
    excel_bytes = df_to_excel_bytes(df, "Orders")

    logger.info(f"Orders exported | Org: {org}")

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=orders.xlsx"}
    )


# -------------------------------------------------
# 2️⃣ REVENUE SUMMARY (MONTHLY + YEARLY WITH RANGE)
# -------------------------------------------------
@router.get("/revenue-summary")
def export_revenue_summary(
    request: Request,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None
):
    org = require_login(request)

    orders = supabase.table("orders") \
        .select("date,total_amount_with_gst") \
        .eq("org", org) \
        .execute().data

    if not orders:
        raise HTTPException(404, "No revenue data found")

    df = pd.DataFrame(orders)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.strftime("%Y-%m")

    if start_year:
        df = df[df["year"] >= start_year]

    if end_year:
        df = df[df["year"] <= end_year]

    if df.empty:
        raise HTTPException(404, "No revenue data for selected year range")

    # Monthly Revenue
    monthly = df.groupby("month")["total_amount_with_gst"] \
        .sum().reset_index(name="monthly_revenue")

    # Yearly Revenue
    yearly = df.groupby("year")["total_amount_with_gst"] \
        .sum().reset_index(name="yearly_revenue")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        monthly.to_excel(writer, index=False, sheet_name="Monthly Revenue")
        yearly.to_excel(writer, index=False, sheet_name="Yearly Revenue")

    output.seek(0)

    logger.info(f"Revenue summary exported | Org: {org}")

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition":
            "attachment; filename=revenue_summary.xlsx"
        }
    )


# -------------------------------------------------
# 3️⃣ EXPORT ALL DELIVERIES (DATE RANGE + ZIP)
# -------------------------------------------------
@router.get("/deliveries-zip")
def export_all_deliveries_zip(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    org = require_login(request)

    query = supabase.table("deliveries") \
        .select("*") \
        .eq("org", org)

    if start_date:
        query = query.gte("delivery_date", start_date)

    if end_date:
        query = query.lte("delivery_date", end_date)

    deliveries = query.execute().data

    if not deliveries:
        raise HTTPException(404, "No deliveries found for selected date range")

    df = pd.DataFrame(deliveries)
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for order_id, group in df.groupby("order_id"):
            excel_bytes = df_to_excel_bytes(group, f"Order_{order_id}")
            zipf.writestr(
                f"order_{order_id}_deliveries.xlsx",
                excel_bytes
            )

    zip_buffer.seek(0)

    logger.info(f"All deliveries ZIP exported | Org: {org}")

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition":
            "attachment; filename=all_deliveries.zip"
        }
    )


# -------------------------------------------------
# 4️⃣ EXPORT DELIVERIES FOR A SPECIFIC ORDER
# -------------------------------------------------
@router.get("/deliveries/{order_id}")
def export_deliveries_for_order(order_id: int, request: Request):
    org = require_login(request)

    deliveries = supabase.table("deliveries") \
        .select("*") \
        .eq("order_id", order_id) \
        .eq("org", org) \
        .execute().data

    if not deliveries:
        raise HTTPException(404, "No deliveries found for this order")

    df = pd.DataFrame(deliveries)
    excel_bytes = df_to_excel_bytes(df, f"Order_{order_id}_Deliveries")

    logger.info(f"Deliveries exported | Order: {order_id} | Org: {org}")

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition":
            f"attachment; filename=order_{order_id}_deliveries.xlsx"
        }
    )
