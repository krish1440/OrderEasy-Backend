from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from app.core.supabase import supabase
from app.core.session import require_login
from app.core.logger import get_logger

from typing import Optional
import pandas as pd
import io
import zipfile
import requests as http_requests
from datetime import date, datetime
from urllib.parse import unquote

# ReportLab for PDF
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

# Latest production sync: 2026-03-07
router = APIRouter()
logger = get_logger(__name__)

# Brand colours
BRAND_MID = colors.HexColor("#312e81")
BRAND_ACCENT = colors.HexColor("#4f46e5")
STRIPE = colors.HexColor("#f8fafc")


# -------------------------------------------------
# HELPER: fetch org branding from users table
# -------------------------------------------------
def get_org_info(org: str) -> dict:
    try:
        res = (
            supabase.table("users")
            .select("organization,email,logo_url")
            .eq("organization", org)
            .limit(1)
            .execute()
        )
        if res.data:
            return res.data[0]
    except Exception:
        pass
    return {"organization": org, "email": "", "logo_url": None}


# -------------------------------------------------
# HELPER: branded PDF builder
# All text uses only ASCII/Latin-1 safe characters
# Rs. instead of Rs symbol (Helvetica can't render it)
# -------------------------------------------------
def build_pdf(
    title: str,
    columns: list,
    rows: list,
    org_info: dict,
    col_widths: Optional[list] = None,
    landscape_mode: bool = False,
) -> bytes:
    buf = io.BytesIO()
    page = landscape(A4) if landscape_mode else A4

    # Pull org info first so we can embed it in PDF metadata
    org_name = org_info.get("organization", "OrderEazy User")
    org_email = org_info.get("email", "")
    logo_url = org_info.get("logo_url") or ""
    generated = datetime.now().strftime("%d %b %Y, %I:%M %p")

    doc = SimpleDocTemplate(
        buf,
        pagesize=page,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=15 * mm,
        title=title,
        author=org_name,
        subject=f"{title} generated for {org_name}",
        creator="OrderEazy",
        producer="OrderEazy Document Engine",
    )

    page_w = page[0] - 24 * mm  # usable width

    # ---- Header banner -----------------------------------------------

    logo_img = None
    if logo_url:
        try:
            r = http_requests.get(logo_url, timeout=5)
            if r.status_code == 200:
                logo_img = Image(io.BytesIO(r.content), width=28 * mm, height=11 * mm)
        except Exception:
            pass

    logo_cell = (
        logo_img
        if logo_img
        else Paragraph(
            '<font size="18" color="white"><b>OE</b></font>',
            ParagraphStyle("lp", textColor=colors.white),
        )
    )

    hdr_data = [
        [
            logo_cell,
            Paragraph(
                f'<font size="16" color="white"><b>{org_name}</b></font>'
                f'<br/><font size="9" color="#c7d2fe">{org_email}</font>',
                ParagraphStyle("hp", fontName="Helvetica-Bold", textColor=colors.white),
            ),
            Paragraph(
                f'<font size="9" color="#c7d2fe">Generated<br/>{generated}</font>',
                ParagraphStyle("tp", alignment=TA_RIGHT),
            ),
        ]
    ]

    hdr_table = Table(hdr_data, colWidths=[32 * mm, page_w - 78 * mm, 46 * mm])
    hdr_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BRAND_MID),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    elements = [hdr_table, Spacer(1, 5 * mm)]

    # ---- Report title ------------------------------------------------
    elements.append(
        Paragraph(
            f'<font size="13" color="#1e293b"><b>{title}</b></font>',
            ParagraphStyle("t", spaceAfter=3),
        )
    )
    elements.append(Spacer(1, 2 * mm))

    # ---- Data table --------------------------------------------------
    if not rows:
        elements.append(
            Paragraph("No data available.", getSampleStyleSheet()["Normal"])
        )
    else:
        # Styles for header and data cells
        hdr_cell_style = ParagraphStyle(
            "hdr_cell",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=colors.white,
            leading=10,
        )
        data_cell_style = ParagraphStyle(
            "data_cell",
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.HexColor("#1e293b"),
            leading=10,  # line spacing
            wordWrap="CJK",  # enables per-character word-break for long words
            spaceAfter=0,
        )

        # Convert header strings to Paragraph
        header_row = [Paragraph(str(c), hdr_cell_style) for c in columns]

        # Convert every data cell to Paragraph — long text auto-wraps,
        # short text stays single-line; row height adjusts per-row automatically.
        para_rows = []
        for row in rows:
            para_rows.append([Paragraph(str(cell), data_cell_style) for cell in row])

        table_data = [header_row] + para_rows

        if col_widths is None:
            col_widths = [page_w / len(columns)] * len(columns)

        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(
            TableStyle(
                [
                    # Header styling
                    ("BACKGROUND", (0, 0), (-1, 0), BRAND_ACCENT),
                    ("TOPPADDING", (0, 0), (-1, 0), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("LEFTPADDING", (0, 0), (-1, 0), 4),
                    ("RIGHTPADDING", (0, 0), (-1, 0), 4),
                    # Data row styling
                    ("TOPPADDING", (0, 1), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
                    ("LEFTPADDING", (0, 1), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 1), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, STRIPE]),
                    # Grid
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
                    # Align top so multi-line rows start at the top of the cell
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        elements.append(t)

    # ---- Footer ------------------------------------------------------
    elements.append(Spacer(1, 8 * mm))
    elements.append(
        Paragraph(
            f'<font size="8" color="#94a3b8">Powered by <b>OrderEazy</b>  |  {org_name}  |  {generated}</font>',
            ParagraphStyle("footer", alignment=TA_CENTER),
        )
    )

    doc.build(elements)
    buf.seek(0)
    return buf.read()


# -------------------------------------------------
# HELPER: DataFrame to Excel bytes
# -------------------------------------------------
def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    output.seek(0)
    return output.read()


# -------------------------------------------------
# 1. EXPORT ORDERS - Excel
# -------------------------------------------------
@router.get("/orders")
def export_orders(
    request: Request,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
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
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=orders.xlsx"},
    )


# -------------------------------------------------
# 1b. EXPORT ORDERS - PDF
# -------------------------------------------------
@router.get("/orders/pdf")
def export_orders_pdf(
    request: Request,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    org = require_login(request)
    query = (
        supabase.table("orders")
        .select(
            "order_id,date,receiver_name,product,quantity,total_amount_with_gst,advance_payment,pending_amount,status"
        )
        .eq("org", org)
    )
    if status and status.lower() != "all":
        query = query.eq("status", status)
    if start_date:
        query = query.gte("date", start_date)
    if end_date:
        query = query.lte("date", end_date)
    orders = query.order("date", desc=True).execute().data or []

    org_info = get_org_info(org)
    cols = [
        "#",
        "Date",
        "Customer",
        "Product",
        "Qty",
        "Total (Rs.)",
        "Advance (Rs.)",
        "Pending (Rs.)",
        "Status",
    ]
    rows = []
    for i, o in enumerate(orders, 1):
        rows.append(
            [
                str(i),
                str(o.get("date", "")),
                str(o.get("receiver_name", "")),
                str(o.get("product", "")),
                str(o.get("quantity", 0)),
                f"Rs.{o.get('total_amount_with_gst', 0):,.0f}",
                f"Rs.{o.get('advance_payment', 0):,.0f}",
                f"Rs.{o.get('pending_amount', 0):,.0f}",
                str(o.get("status", "")),
            ]
        )

    # 273mm usable landscape width: #(10)+Date(22)+Customer(55)+Product(50)+Qty(13)+Total(30)+Advance(30)+Pending(30)+Status(23)=273
    col_w = [
        10 * mm,
        22 * mm,
        55 * mm,
        50 * mm,
        13 * mm,
        30 * mm,
        30 * mm,
        30 * mm,
        23 * mm,
    ]
    pdf_bytes = build_pdf(
        "Orders Report", cols, rows, org_info, col_widths=col_w, landscape_mode=True
    )
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=orders_report.pdf"},
    )


# -------------------------------------------------
# 2. REVENUE SUMMARY - Excel
# -------------------------------------------------
@router.get("/revenue-summary")
def export_revenue_summary(
    request: Request, start_year: Optional[int] = None, end_year: Optional[int] = None
):
    org = require_login(request)
    orders = (
        supabase.table("orders")
        .select("date,total_amount_with_gst")
        .eq("org", org)
        .execute()
        .data
    )
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
    monthly = (
        df.groupby("month")["total_amount_with_gst"]
        .sum()
        .reset_index(name="monthly_revenue")
    )
    yearly = (
        df.groupby("year")["total_amount_with_gst"]
        .sum()
        .reset_index(name="yearly_revenue")
    )
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        monthly.to_excel(writer, index=False, sheet_name="Monthly Revenue")
        yearly.to_excel(writer, index=False, sheet_name="Yearly Revenue")
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=revenue_summary.xlsx"},
    )


# -------------------------------------------------
# 2b. REVENUE SUMMARY - PDF
# -------------------------------------------------
@router.get("/revenue-summary/pdf")
def export_revenue_summary_pdf(
    request: Request, start_year: Optional[int] = None, end_year: Optional[int] = None
):
    org = require_login(request)
    orders = (
        supabase.table("orders")
        .select("date,total_amount_with_gst")
        .eq("org", org)
        .execute()
        .data
        or []
    )

    org_info = get_org_info(org)
    df = (
        pd.DataFrame(orders)
        if orders
        else pd.DataFrame(columns=["date", "total_amount_with_gst"])
    )
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.strftime("%Y-%m")
        if start_year:
            df = df[df["year"] >= start_year]
        if end_year:
            df = df[df["year"] <= end_year]

    monthly = (
        df.groupby("month")["total_amount_with_gst"].sum().reset_index(name="revenue")
        if not df.empty
        else pd.DataFrame()
    )

    cols = ["Month", "Revenue (Rs.)", "% of Total"]
    rows = []
    total = monthly["revenue"].sum() if not monthly.empty else 0
    for _, r in monthly.iterrows():
        pct = (r["revenue"] / total * 100) if total > 0 else 0
        rows.append([str(r["month"]), f"Rs.{r['revenue']:,.0f}", f"{pct:.1f}%"])

    pdf_bytes = build_pdf("Revenue Summary Report", cols, rows, org_info)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=revenue_summary.pdf"},
    )


# -------------------------------------------------
# 3. DELIVERIES ZIP - Excel
# -------------------------------------------------
@router.get("/deliveries-zip")
def export_all_deliveries_zip(
    request: Request, start_date: Optional[str] = None, end_date: Optional[str] = None
):
    org = require_login(request)
    query = supabase.table("deliveries").select("*").eq("org", org)
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
            zipf.writestr(f"order_{order_id}_deliveries.xlsx", excel_bytes)
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=all_deliveries.zip"},
    )


# -------------------------------------------------
# 3b. DELIVERIES - PDF
# -------------------------------------------------
@router.get("/deliveries/pdf")
def export_deliveries_pdf(
    request: Request, start_date: Optional[str] = None, end_date: Optional[str] = None
):
    org = require_login(request)
    query = (
        supabase.table("deliveries")
        .select(
            "order_id,delivery_id,delivery_date,delivery_quantity,total_amount_received"
        )
        .eq("org", org)
    )
    if start_date:
        query = query.gte("delivery_date", start_date)
    if end_date:
        query = query.lte("delivery_date", end_date)
    deliveries = query.order("delivery_date", desc=True).execute().data or []

    org_info = get_org_info(org)
    cols = ["Order #", "Delivery #", "Date", "Units Delivered", "Amount Received (Rs.)"]
    rows = [
        [
            str(d.get("order_id", "")),
            str(d.get("delivery_id", "")),
            str(d.get("delivery_date", "")),
            str(d.get("delivery_quantity", 0)),
            f"Rs.{d.get('total_amount_received', 0):,.0f}",
        ]
        for d in deliveries
    ]

    pdf_bytes = build_pdf("Deliveries Report", cols, rows, org_info)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=deliveries_report.pdf"},
    )


# -------------------------------------------------
# 4. SPECIFIC ORDER DELIVERIES - Excel
# -------------------------------------------------
@router.get("/deliveries/{order_id}")
def export_deliveries_for_order(order_id: int, request: Request):
    org = require_login(request)
    deliveries = (
        supabase.table("deliveries")
        .select("*")
        .eq("order_id", order_id)
        .eq("org", org)
        .execute()
        .data
    )
    if not deliveries:
        raise HTTPException(404, "No deliveries found for this order")
    df = pd.DataFrame(deliveries)
    excel_bytes = df_to_excel_bytes(df, f"Order_{order_id}_Deliveries")
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=order_{order_id}_deliveries.xlsx"
        },
    )


# -------------------------------------------------
# 5. CUSTOMER STATEMENT - Excel
# -------------------------------------------------
@router.get("/customer-statement")
def export_customer_statement(request: Request, customer: str):
    org = require_login(request)
    customer = unquote(customer)
    logger.info(f"Exporting Excel statement for customer: {customer}")
    orders = (
        supabase.table("orders")
        .select("*")
        .eq("org", org)
        .eq("receiver_name", customer)
        .order("date", desc=True)
        .execute()
        .data
        or []
    )
    if not orders:
        raise HTTPException(404, f"No orders found for customer: {customer}")

    df = pd.DataFrame(orders)
    display_cols = [
        "order_id",
        "date",
        "product",
        "quantity",
        "total_amount_with_gst",
        "advance_payment",
        "pending_amount",
        "status",
        "expected_delivery_date",
    ]
    df = df[[c for c in display_cols if c in df.columns]]
    excel_bytes = df_to_excel_bytes(df, "Customer Statement")
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=statement_{customer}.xlsx"
        },
    )


# -------------------------------------------------
# 5b. CUSTOMER STATEMENT - PDF
# -------------------------------------------------
@router.get("/customer-statement/pdf")
def export_customer_statement_pdf(request: Request, customer: str):
    org = require_login(request)
    customer = unquote(customer)
    logger.info(f"Exporting PDF statement for customer: {customer}")
    orders = (
        supabase.table("orders")
        .select(
            "order_id,date,product,quantity,total_amount_with_gst,advance_payment,pending_amount,status,expected_delivery_date"
        )
        .eq("org", org)
        .eq("receiver_name", customer)
        .order("date", desc=True)
        .execute()
        .data
        or []
    )

    if not orders:
        raise HTTPException(404, f"No orders found for customer: {customer}")

    org_info = get_org_info(org)
    total_value = sum(o.get("total_amount_with_gst", 0) for o in orders)
    total_pending = sum(o.get("pending_amount", 0) for o in orders)
    total_paid = total_value - total_pending

    cols = [
        "Order#",
        "Date",
        "Product",
        "Qty",
        "Value (Rs.)",
        "Paid (Rs.)",
        "Pending (Rs.)",
        "Status",
    ]
    rows = []
    for o in orders:
        paid = o.get("total_amount_with_gst", 0) - o.get("pending_amount", 0)
        rows.append(
            [
                str(o.get("order_id", "")),
                str(o.get("date", "")),
                str(o.get("product", "")),
                str(o.get("quantity", 0)),
                f"Rs.{o.get('total_amount_with_gst', 0):,.0f}",
                f"Rs.{paid:,.0f}",
                f"Rs.{o.get('pending_amount', 0):,.0f}",
                str(o.get("status", "")),
            ]
        )
    # Summary row
    rows.append(
        [
            "",
            "",
            "TOTAL",
            "",
            f"Rs.{total_value:,.0f}",
            f"Rs.{total_paid:,.0f}",
            f"Rs.{total_pending:,.0f}",
            "",
        ]
    )

    # 273mm usable landscape width: Order#(18)+Date(24)+Product(70)+Qty(14)+Value(38)+Paid(38)+Pending(38)+Status(33)=273
    col_w = [18 * mm, 24 * mm, 70 * mm, 14 * mm, 38 * mm, 38 * mm, 38 * mm, 33 * mm]
    pdf_bytes = build_pdf(
        f"Account Statement - {customer}",
        cols,
        rows,
        org_info,
        col_widths=col_w,
        landscape_mode=True,
    )
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=statement_{customer}.pdf"
        },
    )


# -------------------------------------------------
# 6. GST REPORT - Excel
# -------------------------------------------------
@router.get("/gst-report")
def export_gst_report(
    request: Request, start_date: Optional[str] = None, end_date: Optional[str] = None
):
    org = require_login(request)
    query = (
        supabase.table("orders")
        .select("date,product,quantity,price,gst,total_amount_with_gst")
        .eq("org", org)
    )
    if start_date:
        query = query.gte("date", start_date)
    if end_date:
        query = query.lte("date", end_date)
    orders = query.execute().data or []
    if not orders:
        raise HTTPException(404, "No orders found for selected range")

    df = pd.DataFrame(orders)
    df["basic_price"] = (df["quantity"] * df["price"]).round(2)
    df["gst_amount"] = (df["basic_price"] * df["gst"] / 100).round(2)
    df = df.rename(
        columns={
            "date": "Date",
            "product": "Product",
            "quantity": "Qty",
            "price": "Unit Price (Rs.)",
            "gst": "GST %",
            "basic_price": "Basic Price (Rs.)",
            "gst_amount": "GST Amount (Rs.)",
            "total_amount_with_gst": "Total (Rs.)",
        }
    )
    slabs = (
        df.groupby("GST %")
        .agg(
            Orders=("Date", "count"),
            Total_Basic=("Basic Price (Rs.)", "sum"),
            Total_GST=("GST Amount (Rs.)", "sum"),
            Total_Revenue=("Total (Rs.)", "sum"),
        )
        .reset_index()
    )

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df = df[
            [
                "Date",
                "Product",
                "Qty",
                "Unit Price (Rs.)",
                "Basic Price (Rs.)",
                "GST %",
                "GST Amount (Rs.)",
                "Total (Rs.)",
            ]
        ]
        export_df.to_excel(writer, index=False, sheet_name="All Orders")

        # --- Totals row at the bottom of All Orders sheet ---
        ws = writer.sheets["All Orders"]
        next_row = len(export_df) + 2  # +1 for header, +1 for 1-indexed
        totals = [
            "TOTAL",
            "",
            int(df["Qty"].sum()),
            "",
            round(df["Basic Price (Rs.)"].sum(), 2),
            "",
            round(df["GST Amount (Rs.)"].sum(), 2),
            round(df["Total (Rs.)"].sum(), 2),
        ]
        for col_idx, val in enumerate(totals, start=1):
            cell = ws.cell(row=next_row, column=col_idx, value=val)
            cell.font = __import__("openpyxl").styles.Font(bold=True)
            cell.fill = __import__("openpyxl").styles.PatternFill(
                "solid", fgColor="E0E7FF"
            )

        slabs.to_excel(writer, index=False, sheet_name="GST Slab Summary")
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=gst_report.xlsx"},
    )


# -------------------------------------------------
# 6b. GST REPORT - PDF
# -------------------------------------------------
@router.get("/gst-report/pdf")
def export_gst_report_pdf(
    request: Request, start_date: Optional[str] = None, end_date: Optional[str] = None
):
    org = require_login(request)
    query = (
        supabase.table("orders")
        .select("date,product,quantity,price,gst,total_amount_with_gst")
        .eq("org", org)
    )
    if start_date:
        query = query.gte("date", start_date)
    if end_date:
        query = query.lte("date", end_date)
    orders = query.execute().data or []

    org_info = get_org_info(org)
    cols = [
        "Date",
        "Product",
        "Qty",
        "Unit Price",
        "Basic Amt",
        "GST%",
        "GST Amt",
        "Total",
    ]
    rows = []
    for o in orders:
        basic = round(o.get("quantity", 0) * o.get("price", 0), 2)
        gst_amt = round(basic * o.get("gst", 0) / 100, 2)
        rows.append(
            [
                str(o.get("date", "")),
                str(o.get("product", "")),
                str(o.get("quantity", 0)),
                f"Rs.{o.get('price', 0):,.0f}",
                f"Rs.{basic:,.0f}",
                f"{o.get('gst', 0)}%",
                f"Rs.{gst_amt:,.0f}",
                f"Rs.{o.get('total_amount_with_gst', 0):,.0f}",
            ]
        )
    # Compute totals for PDF summary row
    total_qty = sum(o.get("quantity", 0) for o in orders)
    total_basic = sum(
        round(o.get("quantity", 0) * o.get("price", 0), 2) for o in orders
    )
    total_gst_amt = sum(
        round(o.get("quantity", 0) * o.get("price", 0) * o.get("gst", 0) / 100, 2)
        for o in orders
    )
    total_revenue = sum(o.get("total_amount_with_gst", 0) for o in orders)

    # Append bold TOTAL row
    rows.append(
        [
            "TOTAL",
            "",
            str(total_qty),
            "",
            f"Rs.{total_basic:,.0f}",
            "",
            f"Rs.{total_gst_amt:,.0f}",
            f"Rs.{total_revenue:,.0f}",
        ]
    )

    col_w = [28 * mm, 85 * mm, 16 * mm, 32 * mm, 32 * mm, 18 * mm, 30 * mm, 32 * mm]
    pdf_bytes = build_pdf(
        "GST Tax Report", cols, rows, org_info, col_widths=col_w, landscape_mode=True
    )
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=gst_report.pdf"},
    )


# -------------------------------------------------
# 7. PENDING ORDERS URGENCY - PDF
# -------------------------------------------------
@router.get("/pending-orders/pdf")
def export_pending_orders_pdf(request: Request):
    org = require_login(request)
    orders = (
        supabase.table("orders")
        .select(
            "order_id,date,receiver_name,product,quantity,delivered_quantity,pending_amount,expected_delivery_date"
        )
        .eq("org", org)
        .eq("status", "Pending")
        .execute()
        .data
        or []
    )

    today = date.today()

    def urgency_key(o):
        exp = o.get("expected_delivery_date")
        if not exp:
            return 9999
        try:
            d = date.fromisoformat(exp.split("T")[0])
            return (d - today).days
        except Exception:
            return 9999

    orders_sorted = sorted(orders, key=urgency_key)
    org_info = get_org_info(org)

    cols = [
        "#",
        "Order ID",
        "Customer",
        "Product",
        "Rem. Units",
        "Pending (Rs.)",
        "Due Date",
        "Days Left",
    ]
    rows = []
    for i, o in enumerate(orders_sorted, 1):
        exp = o.get("expected_delivery_date", "")
        days_left = "-"
        if exp:
            try:
                d = date.fromisoformat(exp.split("T")[0])
                diff = (d - today).days
                prefix = "OVERDUE " if diff < 0 else ""
                days_left = f"{prefix}{diff}d"
            except Exception:
                days_left = "-"
        remaining = o.get("quantity", 0) - (o.get("delivered_quantity") or 0)
        rows.append(
            [
                str(i),
                str(o.get("order_id", "")),
                str(o.get("receiver_name", "")),
                str(o.get("product", "")),
                str(remaining),
                f"Rs.{o.get('pending_amount', 0):,.0f}",
                exp.split("T")[0] if exp else "-",
                days_left,
            ]
        )

    # Use landscape + wider columns so "Days Left" isn't cut off
    # 273mm usable landscape width: #(10)+OrderID(20)+Customer(70)+Product(65)+RemUnits(22)+Pending(32)+DueDate(28)+DaysLeft(26)=273
    col_w = [10 * mm, 20 * mm, 70 * mm, 65 * mm, 22 * mm, 32 * mm, 28 * mm, 26 * mm]
    pdf_bytes = build_pdf(
        "Pending Orders - Urgency Report",
        cols,
        rows,
        org_info,
        col_widths=col_w,
        landscape_mode=True,
    )
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=pending_orders_urgent.pdf"
        },
    )


# -------------------------------------------------
# 8. CUSTOMER LIST (for frontend dropdown)
# -------------------------------------------------
@router.get("/customers/list")
def get_customer_list(request: Request):
    org = require_login(request)
    orders = (
        supabase.table("orders").select("receiver_name").eq("org", org).execute().data
        or []
    )
    names = sorted({o["receiver_name"] for o in orders if o.get("receiver_name")})
    return {"customers": names}
