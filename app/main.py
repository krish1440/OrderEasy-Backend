from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import SECRET_KEY
from app.core.logger import get_logger

# Routers
from app.auth.routes import router as auth_router
from app.orders.routes import router as orders_router
from app.deliveries.routes import router as deliveries_router
from app.analytics.routes import router as analytics_router
from app.admin.routes import router as admin_router
from app.analytics.forecasting import router as forecast_router
from app.exports.routes import router as export_router
from app.analytics.rfm import router as rfm_router
from app.analytics.advanced_routes import router as advanced_analytics_router
from app.upload.routes import router as upload_router


# -------------------------------------------------
# App Initialization
# -------------------------------------------------
app = FastAPI(
    title="OrderEasy Analytics",
    description="Enterprise Order & Business Intelligence Platform",
    version="1.0.0"
)

logger = get_logger(__name__)

# -------------------------------------------------
# CORS Middleware (Frontend Access)
# -------------------------------------------------
# Must exactly match the browser's "Origin" header
# Must exactly match the browser's "Origin" header
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "https://order-easy-blond.vercel.app",
    "https://order-easy-blond.vercel.app/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # allow_origin_regex="https?://.*", # Disabled in favor of specific origins for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Session Middleware
# -------------------------------------------------
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=False  # set True in production with HTTPS
)

# -------------------------------------------------
# Router Registration
# -------------------------------------------------
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(orders_router, prefix="/orders", tags=["Orders"])
app.include_router(deliveries_router, prefix="/deliveries", tags=["Deliveries"])
app.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(forecast_router, prefix="/analytics", tags=["Forecasting"])
app.include_router(export_router, prefix="/exports", tags=["Exports"])
app.include_router(rfm_router, prefix="/analytics", tags=["RFM Analysis"])
app.include_router(
    advanced_analytics_router,
    prefix="/analytics",
    tags=["Advanced Analytics"]
)
app.include_router(upload_router, prefix="/upload", tags=["Uploads"])


# ------------------------------------------------
# Health Check
# -------------------------------------------------
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "OrderEasy Analytics Backend"
    }

logger.info("OrderEasy Analytics backend initialized")
