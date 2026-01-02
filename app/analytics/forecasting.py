from fastapi import APIRouter, Request, HTTPException
from app.core.supabase import supabase
from app.core.session import require_login
from app.core.logger import get_logger

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import r2_score
from scipy import stats
from datetime import timedelta, datetime

router = APIRouter()
logger = get_logger(__name__)

# -------------------------------------------------
# Helper: Prepare daily revenue dataframe
# -------------------------------------------------
# -------------------------------------------------
# Helper: Prepare Monthly Revenue Dataframe
# -------------------------------------------------
def get_monthly_revenue(org: str) -> pd.DataFrame:
    """
    Returns DataFrame with columns:
    [month_date, revenue]
    Aggregated by Month (First day of month)
    """

    orders = supabase.table("orders") \
        .select("date,total_amount_with_gst") \
        .eq("org", org) \
        .execute().data

    if not orders:
        raise HTTPException(400, "Not enough data for forecasting")

    df = pd.DataFrame(orders)
    df["date"] = pd.to_datetime(df["date"])
    # Normalize to 1st of the month
    df["month_date"] = df["date"].dt.to_period('M').dt.to_timestamp()
    
    df = df.groupby("month_date")["total_amount_with_gst"].sum().reset_index()
    df = df.sort_values("month_date")

    return df


# -------------------------------------------------
# Helper: Train Robust Regression Model (Log-Linear + Seasonal)
# -------------------------------------------------
def train_model(df: pd.DataFrame):
    """
    Trains Huber Regressor on Log-Transformed revenue with Seasonal Harmonics.
    
    Model: log(y + 1) = w1*Time + w2*Sin(Month) + w3*Cos(Month) + c
    
    This captures:
    1. Trend (Time)
    2. Seasonality (Sin/Cos) - "Months based analysis"
    3. Positivity (Log)
    """

    # Feature 1: Time Trend
    df["month_index"] = np.arange(len(df))
    
    # Feature 2 & 3: Seasonal Harmonics (Cyclic Time)
    # We use month 1-12 to generate a smooth wave
    months = df["month_date"].dt.month
    df["sin_month"] = np.sin(2 * np.pi * months / 12)
    df["cos_month"] = np.cos(2 * np.pi * months / 12)

    # Prepare X (Features) and y (Target)
    X = df[["month_index", "sin_month", "cos_month"]].values
    y = df["total_amount_with_gst"].values
    
    # 1. Log-Transform Target
    y_log = np.log1p(y)

    # 2. Train Robust Regressor
    # HuberRegressor is robust to short-term anomalies
    model = HuberRegressor(epsilon=1.35)
    model.fit(X, y_log)

    # 3. Predict on Training Data
    log_predictions = model.predict(X)
    
    # 4. Inverse Transform for R2
    predictions = np.expm1(log_predictions)
    predictions = np.maximum(0, predictions)

    r2 = r2_score(y, predictions)

    return model, r2, log_predictions, y_log


# -------------------------------------------------
# Helper: Confidence Interval
# -------------------------------------------------
def confidence_interval(y_log, y_pred_log, alpha=0.20):
    """
    Computes 80% confidence interval on the LOG scale.
    (Business Standard vs Scientific 95%)
    """
    n = len(y_log)
    if n < 3: return 0.1
    
    # Standard Error of Estimate
    residuals = y_log - y_pred_log
    std_err = np.sqrt(np.sum(residuals ** 2) / (n - 2))
    
    t_val = stats.t.ppf(1 - alpha / 2, n - 2)
    return t_val * std_err


# -------------------------------------------------
# 🔮 FORECAST ENDPOINT (12 MONTHS)
# -------------------------------------------------
@router.get("/forecast")
def revenue_forecast(request: Request):
    """
    Returns:
    - 12-month "Advanced" forecast (Trend + Seasonality)
    - 80% Confidence Interval
    """

    org = require_login(request)

    # Use Monthly Data
    df = get_monthly_revenue(org)

    if len(df) < 2:
        raise HTTPException(
            400,
            "At least 2 months of data required for monthly forecasting"
        )

    # Train Model
    model, r2, train_pred_log, y_train_log = train_model(df)
    
    # Calculate Uncertainty (Defaults to 80%)
    ci_log = confidence_interval(y_train_log, train_pred_log)

    last_month_index = df["month_index"].iloc[-1]
    last_date = df["month_date"].iloc[-1]

    # Predict Next 12 Months
    forecast = []
    
    def add_months(source_date, months):
        month = source_date.month - 1 + months
        year = source_date.year + month // 12
        month = month % 12 + 1
        return datetime(year, month, 1)

    # Generate Future Features
    # We need to build the X array for each future month
    for i in range(1, 13):
        # 1. Future Month Date
        future_date = add_months(last_date, i)
        
        # 2. Future Features
        feat_time = last_month_index + i
        feat_sin = np.sin(2 * np.pi * future_date.month / 12)
        feat_cos = np.cos(2 * np.pi * future_date.month / 12)
        
        # Shape: (1, 3)
        X_future = np.array([[feat_time, feat_sin, feat_cos]])
        
        # 3. Predict (Log Scale)
        val_log = model.predict(X_future)[0]
        
        # 4. Bounds (Log Scale)
        low_log = val_log - ci_log
        high_log = val_log + ci_log
        
        # 5. Inverse Transform (Revenue Scale)
        pred = max(0, float(np.expm1(val_log)))
        low = max(0, float(np.expm1(low_log)))
        high = max(0, float(np.expm1(high_log)))

        forecast.append({
            "month": future_date.strftime("%b %Y"),
            "predicted_revenue": round(pred, 2),
            "lower_bound": round(low, 2),
            "upper_bound": round(high, 2)
        })

    logger.info(f"Seasonal Harmonic forecast generated for org: {org}")

    return {
        "r2_score": round(float(r2), 4),
        "confidence_level": "80%",
        "forecast_12_months": forecast
    }
