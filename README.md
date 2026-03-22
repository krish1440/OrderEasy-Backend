# 🚀 OrderEazy Backend: Secure, Scalable, and Smart

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase)](https://supabase.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql)](https://www.postgresql.org/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge&logo=googlegemini)](https://ai.google.dev/)

Welcome to the power engine of **OrderEazy**. A high-performance RESTful API built on **FastAPI**, designed to handle complex order management, secure authentication, and AI-driven business intelligence.

---

## 🏁 Live Documentation
Access the interactive API docs directly on Render:
🔗 **[Live API Swagger Docs](https://ordereasy-backend-fwl1.onrender.com/docs)**

---

## ⚡ Key Technical Features

### 🛡️ Core Infrastructure & Security
- **FastAPI Engine**: High-speed, modern framework with asynchronous support.
- **Supabase Integration**: Real-time DB interactions with **PostgreSQL**.
- **JWT Authentication**: Robust security layer with access control and session management.
- **CORS Protection**: Secure communication channels across heterogeneous origins.

### 🤖 Business Intelligence & AI
- **Gemini AI Integration**: Real-time strategic business advice based on order trends.
- **RFM Segmentation**: Technical data science module calculating Recency, Frequency, and Monetary scores for customer grouping.
- **Revenue Forecasting**: Time-series analysis and regression forecasting using **Pandas** and custom math engines.

### 📦 Logistics & Operations
- **Advanced Export System**: Dynamic generation of Excel and PDF reports.
- **Order Lifecycle Management**: Optimized routes for tracking revenue, deliveries, and fulfillment gaps.

---

## 🛠️ Technology Stack
- **Languages**: Python 3.10+
- **Framework**: FastAPI
- **Database**: PostgreSQL (via Supabase)
- **AI/ML**: Google Gemini Pro, Pandas
- **Reporting**: ReportLab (PDF), OpenPyXL (Excel)
- **Security**: PyJWT, Passlib (Bcrypt)

---

## 👥 The OrderEazy Team

| Contributor | Primary Role | GitHub ID |
| :--- | :--- | :--- |
| **Dhruvin** | Backend Architect & Security | [@dhruvin2303](https://github.com/dhruvin2303) |
| **Krish** | AI Integration & Analytics Lead | [@krish1440](https://github.com/krish1440) |
| **Harsh** | Visual BI & All Chart Features | [@harshdholakiya21](https://github.com/harshdholakiya21) |
| **Raj** | UI/UX & Application Interactions | [@Raj-Kapuriya](https://github.com/Raj-Kapuriya) |

---

## 🚀 Getting Started

1. **Clone & Install**:
   ```bash
   git clone [repository-url]
   cd OrderEazy/Backend
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Create a `.env` file with your `SUPABASE_URL`, `SUPABASE_KEY`, and `GEMINI_API_KEY`.

3. **Run Development Server**:
   ```bash
   uvicorn app.main:app --reload
   ```

---
