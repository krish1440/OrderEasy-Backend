"""
Enterprise Developer Portal UI Generator for OrderEasy Analytics Backend
Serves a clean, modern API Hub at the root route `/` matching the Frontend UI Theme
"""

def get_api_portal_html() -> str:
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OrderEasy Analytics — API Developer Hub</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-body: #f8fafc;
            --bg-card: #ffffff;
            --bg-card-hover: #ffffff;
            --bg-drawer: #f1f5f9;
            --border-color: #e2e8f0;
            --border-highlight: #cbd5e1;
            
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #64748b;
            
            --brand-primary: #4f46e5;
            --brand-secondary: #3730a3;
            --brand-light: #eef2ff;

            --get-bg: #ecfdf5;
            --get-color: #059669;
            --get-border: #a7f3d0;

            --post-bg: #eff6ff;
            --post-color: #2563eb;
            --post-border: #bfdbfe;

            --put-bg: #fffbeb;
            --put-color: #d97706;
            --put-border: #fde68a;

            --delete-bg: #fef2f2;
            --delete-color: #dc2626;
            --delete-border: #fecaca;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-body);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }

        /* Top Navbar */
        .top-navbar {
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-color);
            padding: 0.85rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .brand-logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            text-decoration: none;
        }

        .brand-svg {
            width: 34px;
            height: 34px;
            transition: transform 0.3s ease;
        }

        .brand-logo:hover .brand-svg {
            transform: rotate(6deg) scale(1.05);
        }

        .brand-title {
            font-size: 1.3rem;
            font-weight: 800;
            background: linear-gradient(135deg, #4f46e5 0%, #3730a3 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.02em;
        }

        .brand-subtitle {
            font-size: 0.75rem;
            color: var(--text-muted);
            font-weight: 500;
        }

        .nav-right {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.55rem 1.15rem;
            border-radius: 10px;
            font-size: 0.875rem;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.2s ease;
            cursor: pointer;
            border: none;
        }

        .btn-primary {
            background: #4f46e5;
            color: white;
            box-shadow: 0 4px 14px rgba(79, 70, 229, 0.25);
        }

        .btn-primary:hover {
            background: #4338ca;
            transform: translateY(-1px);
            box-shadow: 0 6px 18px rgba(79, 70, 229, 0.35);
        }

        .btn-outline {
            background: white;
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
        }

        .btn-outline:hover {
            background: var(--bg-body);
            color: var(--brand-primary);
            border-color: #cbd5e1;
        }

        .status-pill {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            font-size: 0.8rem;
            color: #059669;
            background: #ecfdf5;
            padding: 0.35rem 0.75rem;
            border-radius: 9999px;
            border: 1px solid #a7f3d0;
            font-weight: 600;
        }

        .status-dot {
            width: 7px;
            height: 7px;
            background: #10b981;
            border-radius: 50%;
            box-shadow: 0 0 8px #10b981;
        }

        /* Layout Grid */
        .layout-wrapper {
            display: flex;
            max-width: 1440px;
            margin: 0 auto;
            min-height: calc(100vh - 65px);
        }

        /* Sidebar Navigation */
        .sidebar {
            width: 270px;
            background: white;
            border-right: 1px solid var(--border-color);
            padding: 1.5rem 1rem;
            position: sticky;
            top: 65px;
            height: calc(100vh - 65px);
            overflow-y: auto;
            flex-shrink: 0;
        }

        .sidebar-title {
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--text-muted);
            margin: 1.25rem 0.5rem 0.5rem 0.5rem;
        }

        .sidebar-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.65rem 0.85rem;
            border-radius: 10px;
            color: var(--text-secondary);
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-bottom: 0.25rem;
            user-select: none;
        }

        .sidebar-item-left {
            display: flex;
            align-items: center;
            gap: 0.65rem;
        }

        .sidebar-icon {
            width: 18px;
            height: 18px;
            stroke-width: 2;
            flex-shrink: 0;
        }

        .sidebar-item:hover {
            background: var(--brand-light);
            color: var(--brand-primary);
        }

        .sidebar-item.active {
            background: var(--brand-primary);
            color: white;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
        }

        .sidebar-badge {
            font-size: 0.75rem;
            background: rgba(0, 0, 0, 0.05);
            color: currentColor;
            padding: 0.15rem 0.55rem;
            border-radius: 9999px;
            font-weight: 600;
        }

        .sidebar-item.active .sidebar-badge {
            background: rgba(255, 255, 255, 0.2);
            color: white;
        }

        /* Main Content */
        .main-content {
            flex: 1;
            padding: 2rem 2.5rem;
            max-width: 1170px;
        }

        /* Hero Banner */
        .hero-banner {
            background: white;
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 2rem 2.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
            position: relative;
            overflow: hidden;
        }

        .hero-banner::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #10b981, #3b82f6, #4f46e5);
        }

        .hero-title {
            font-size: 1.85rem;
            font-weight: 800;
            color: var(--text-primary);
            margin-bottom: 0.4rem;
        }

        .hero-subtitle {
            color: var(--text-secondary);
            font-size: 0.975rem;
            max-width: 780px;
            margin-bottom: 1.5rem;
        }

        .stats-bar {
            display: flex;
            gap: 2.5rem;
            flex-wrap: wrap;
            padding-top: 1.25rem;
            border-top: 1px solid var(--border-color);
        }

        .stat-item {
            display: flex;
            flex-direction: column;
        }

        .stat-num {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--brand-primary);
            font-family: 'JetBrains Mono', monospace;
        }

        .stat-desc {
            font-size: 0.775rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 600;
        }

        /* Search & Filter controls */
        .controls-card {
            background: white;
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 2rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
        }

        .search-box {
            position: relative;
        }

        .search-box input {
            width: 100%;
            background: #f8fafc;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 0.85rem 1.25rem 0.85rem 2.8rem;
            color: var(--text-primary);
            font-size: 0.95rem;
            font-family: inherit;
            outline: none;
            transition: all 0.2s ease;
        }

        .search-box input:focus {
            background: white;
            border-color: var(--brand-primary);
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15);
        }

        .search-box svg {
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            width: 18px;
            height: 18px;
        }

        .method-filters {
            display: flex;
            gap: 0.5rem;
            align-items: center;
            flex-wrap: wrap;
        }

        .chip {
            padding: 0.35rem 0.85rem;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 600;
            background: #f1f5f9;
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s ease;
            user-select: none;
        }

        .chip:hover {
            background: var(--brand-light);
            color: var(--brand-primary);
        }

        .chip.active {
            background: var(--brand-primary);
            border-color: var(--brand-primary);
            color: white;
        }

        /* Route Card */
        .group-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin: 2rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--border-color);
        }

        .group-header h2 {
            font-size: 1.35rem;
            font-weight: 700;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }

        .group-icon-svg {
            width: 22px;
            height: 22px;
            color: var(--brand-primary);
            stroke-width: 2;
        }

        .route-card {
            background: white;
            border: 1px solid var(--border-color);
            border-radius: 14px;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
            overflow: hidden;
            transition: all 0.2s ease;
        }

        .route-card:hover {
            border-color: #cbd5e1;
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.06);
        }

        .route-main {
            padding: 1.25rem 1.5rem;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            gap: 0.65rem;
        }

        .route-top-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .route-path-group {
            display: flex;
            align-items: center;
            gap: 0.85rem;
            flex-wrap: wrap;
            flex: 1;
        }

        .method-badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.775rem;
            font-weight: 700;
            padding: 0.3rem 0.75rem;
            border-radius: 6px;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            min-width: 68px;
            text-align: center;
        }

        .method-GET { background: var(--get-bg); color: var(--get-color); border: 1px solid var(--get-border); }
        .method-POST { background: var(--post-bg); color: var(--post-color); border: 1px solid var(--post-border); }
        .method-PUT { background: var(--put-bg); color: var(--put-color); border: 1px solid var(--put-border); }
        .method-DELETE { background: var(--delete-bg); color: var(--delete-color); border: 1px solid var(--delete-border); }

        .route-path {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.95rem;
            color: var(--text-primary);
            font-weight: 600;
        }

        .route-actions {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .action-btn {
            background: #f8fafc;
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 0.35rem 0.65rem;
            border-radius: 6px;
            font-size: 0.775rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            font-family: inherit;
        }

        .action-btn:hover {
            background: var(--brand-light);
            color: var(--brand-primary);
            border-color: #c7d2fe;
        }

        .route-summary {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        /* Drawer */
        .route-drawer {
            background: #f8fafc;
            border-top: 1px solid var(--border-color);
            padding: 1.5rem;
            display: none;
        }

        .route-drawer.open {
            display: block;
        }

        .drawer-section-title {
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--brand-primary);
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        /* Code blocks */
        .code-block-wrapper {
            position: relative;
            background: #0f172a;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            overflow-x: auto;
            border: 1px solid #1e293b;
        }

        .code-block {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            color: #38bdf8;
            white-space: pre-wrap;
            word-break: break-all;
        }

        .copy-code-btn {
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #94a3b8;
            font-size: 0.7rem;
            padding: 0.25rem 0.5rem;
            border-radius: 6px;
            cursor: pointer;
        }

        .copy-code-btn:hover {
            background: rgba(255, 255, 255, 0.25);
            color: white;
        }

        /* Table */
        .param-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
            margin-bottom: 1.25rem;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border-color);
        }

        .param-table th, .param-table td {
            text-align: left;
            padding: 0.65rem 0.85rem;
            border-bottom: 1px solid var(--border-color);
        }

        .param-table th {
            background: #f1f5f9;
            color: var(--text-muted);
            font-weight: 700;
            text-transform: uppercase;
            font-size: 0.725rem;
            letter-spacing: 0.05em;
        }

        .param-name {
            font-family: 'JetBrains Mono', monospace;
            color: #2563eb;
            font-weight: 600;
        }

        .param-type {
            font-family: 'JetBrains Mono', monospace;
            color: #d97706;
            font-size: 0.8rem;
        }

        .badge-req {
            font-size: 0.7rem;
            background: #fef2f2;
            color: #dc2626;
            padding: 0.1rem 0.4rem;
            border-radius: 4px;
            font-weight: 700;
            border: 1px solid #fecaca;
        }

        .badge-opt {
            font-size: 0.7rem;
            background: #f1f5f9;
            color: var(--text-muted);
            padding: 0.1rem 0.4rem;
            border-radius: 4px;
        }

        /* Toast */
        .toast {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: var(--brand-primary);
            color: white;
            padding: 0.75rem 1.25rem;
            border-radius: 10px;
            font-size: 0.875rem;
            font-weight: 600;
            box-shadow: 0 10px 25px rgba(79, 70, 229, 0.4);
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s ease;
            pointer-events: none;
            z-index: 1000;
        }

        .toast.show {
            opacity: 1;
            transform: translateY(0);
        }

        @media (max-width: 900px) {
            .layout-wrapper { flex-direction: column; }
            .sidebar { width: 100%; height: auto; position: relative; top: 0; }
            .main-content { padding: 1.5rem 1rem; }
        }
    </style>
</head>
<body>

    <!-- Navbar -->
    <header class="top-navbar">
        <a href="/" class="brand-logo">
            <!-- Official OrderEasy SVG Logo -->
            <svg viewBox="0 0 512 512" fill="none" xmlns="http://www.w3.org/2000/svg" class="brand-svg">
                <defs>
                    <linearGradient id="brandGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stop-color="#10B981" stop-opacity="1" />
                        <stop offset="100%" stop-color="#3B82F6" stop-opacity="1" />
                    </linearGradient>
                    <filter id="brandShadow" x="-20%" y="-20%" width="140%" height="140%">
                        <feDropShadow dx="4" dy="8" stdDeviation="6" flood-opacity="0.2" />
                    </filter>
                </defs>
                <path d="M60 260 L180 380 L300 120 L380 220 L460 60"
                    stroke="url(#brandGradient)"
                    stroke-width="80"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    filter="url(#brandShadow)" />
                <circle cx="460" cy="60" r="30" fill="#3B82F6" />
            </svg>
            <div>
                <div class="brand-title">OrderEasy</div>
                <div class="brand-subtitle">API Developer Hub</div>
            </div>
        </a>

        <div class="nav-right">
            <div class="status-pill">
                <div class="status-dot"></div>
                <span>Backend Online</span>
            </div>
            <a href="/docs" class="btn btn-primary">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                Interactive Swagger Docs
            </a>
            <a href="/openapi.json" target="_blank" class="btn btn-outline">
                OpenAPI Spec JSON
            </a>
        </div>
    </header>

    <!-- Layout Wrapper -->
    <div class="layout-wrapper">

        <!-- Sidebar Navigation -->
        <aside class="sidebar">
            <div class="sidebar-title">Route Groups</div>
            <div id="sidebar-nav">
                <div class="sidebar-item active" onclick="filterByGroup('ALL', this)">
                    <div class="sidebar-item-left">
                        <svg class="sidebar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
                        <span>All Routes</span>
                    </div>
                    <span class="sidebar-badge" id="side-total-count">--</span>
                </div>
            </div>
        </aside>

        <!-- Main Content -->
        <main class="main-content">

            <!-- Hero Banner -->
            <section class="hero-banner">
                <h1 class="hero-title">Developer API Reference</h1>
                <p class="hero-subtitle">Interactive documentation, query specifications, JSON request payload schemas, and operational endpoints for OrderEasy Analytics Engine.</p>

                <div class="stats-bar">
                    <div class="stat-item">
                        <span class="stat-num" id="stat-routes">--</span>
                        <span class="stat-desc">Endpoints</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-num" id="stat-categories">--</span>
                        <span class="stat-desc">Modules</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-num" id="stat-version" style="color:#10b981;">v2.4.1</span>
                        <span class="stat-desc">Version</span>
                    </div>
                </div>
            </section>

            <!-- Search & Filters -->
            <section class="controls-card">
                <div class="search-box">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    <input type="text" id="search-input" placeholder="Search by route path, parameter, summary, or category... (e.g. /auth/login, analytics, forecast)">
                </div>

                <div class="method-filters">
                    <span style="font-size:0.8rem; color:var(--text-muted); font-weight:700; margin-right:0.4rem;">HTTP METHOD:</span>
                    <span class="chip active" onclick="filterByMethod('ALL', this)">ALL</span>
                    <span class="chip" onclick="filterByMethod('GET', this)">GET</span>
                    <span class="chip" onclick="filterByMethod('POST', this)">POST</span>
                    <span class="chip" onclick="filterByMethod('PUT', this)">PUT</span>
                    <span class="chip" onclick="filterByMethod('DELETE', this)">DELETE</span>
                </div>
            </section>

            <!-- Endpoint List Container -->
            <section id="endpoints-container">
                <div style="text-align:center; padding: 4rem; color: var(--text-muted);">
                    Loading OpenAPI specifications...
                </div>
            </section>
        </main>
    </div>

    <!-- Toast Notification -->
    <div id="toast" class="toast">Copied to clipboard!</div>

    <script>
        let apiSchema = null;
        let allEndpoints = [];
        let activeGroup = 'ALL';
        let activeMethod = 'ALL';
        let searchQuery = '';

        // Meaningful SVG Icons for each module category
        const categorySvgIcons = {
            'Authentication': '<svg class="sidebar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>',
            'Orders': '<svg class="sidebar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><line x1="16.5" y1="9.4" x2="7.5" y2="4.21"></line><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>',
            'Deliveries': '<svg class="sidebar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="1" y="3" width="15" height="13"></rect><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"></polygon><circle cx="5.5" cy="18.5" r="2.5"></circle><circle cx="18.5" cy="18.5" r="2.5"></circle></svg>',
            'Analytics': '<svg class="sidebar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
            'Forecasting': '<svg class="sidebar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>',
            'Exports': '<svg class="sidebar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><polyline points="9 15 12 18 15 15"></polyline></svg>',
            'RFM Analysis': '<svg class="sidebar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>',
            'Advanced Analytics': '<svg class="sidebar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>',
            'Uploads': '<svg class="sidebar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>',
            'Admin': '<svg class="sidebar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><path d="M9 12l2 2 4-4"></path></svg>',
            'Default': '<svg class="sidebar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>'
        };

        // Fetch OpenAPI schema
        async function loadSchema() {
            try {
                const res = await fetch('/openapi.json');
                if (!res.ok) throw new Error('Could not fetch openapi.json');
                apiSchema = await res.json();
                parseEndpoints();
                renderSidebar();
                renderContent();
            } catch (err) {
                document.getElementById('endpoints-container').innerHTML = `
                    <div style="padding: 3rem; text-align:center; color:#dc2626;">
                        <h3>Failed to load API Spec</h3>
                        <p style="margin-top:0.5rem;">${err.message}</p>
                    </div>
                `;
            }
        }

        // Parse paths & schemas
        function parseEndpoints() {
            allEndpoints = [];
            const paths = apiSchema.paths || {};

            for (const [path, methods] of Object.entries(paths)) {
                for (const [method, details] of Object.entries(methods)) {
                    if (['get', 'post', 'put', 'delete', 'patch'].includes(method.toLowerCase())) {
                        const tags = details.tags && details.tags.length ? details.tags : ['Default'];
                        
                        // Extract Payload Schema if present
                        const payloadInfo = extractPayloadSchema(details.requestBody);

                        allEndpoints.push({
                            path: path,
                            method: method.toUpperCase(),
                            summary: details.summary || details.operationId || 'Endpoint',
                            description: details.description || '',
                            tags: tags,
                            operationId: details.operationId || '',
                            parameters: details.parameters || [],
                            payload: payloadInfo
                        });
                    }
                }
            }

            document.getElementById('stat-routes').innerText = allEndpoints.length;
            document.getElementById('side-total-count').innerText = allEndpoints.length;
            const uniqueTags = new Set(allEndpoints.flatMap(e => e.tags));
            document.getElementById('stat-categories').innerText = uniqueTags.size;

            const version = apiSchema.info && apiSchema.info.version ? apiSchema.info.version : '2.4.1';
            const vEl = document.getElementById('stat-version');
            if (vEl) vEl.innerText = `v${version}`;
        }

        // Resolve Schema Reference
        function resolveRef(refString) {
            if (!refString || !refString.startsWith('#/')) return null;
            const parts = refString.replace('#/', '').split('/');
            let current = apiSchema;
            for (const p of parts) {
                if (current && current[p]) current = current[p];
                else return null;
            }
            return current;
        }

        // Extract Request Payload Schema & Build Sample JSON
        function extractPayloadSchema(requestBody) {
            if (!requestBody || !requestBody.content) return null;
            const jsonContent = requestBody.content['application/json'];
            if (!jsonContent || !jsonContent.schema) return null;

            let schema = jsonContent.schema;
            if (schema['$ref']) {
                schema = resolveRef(schema['$ref']) || schema;
            }

            if (!schema || !schema.properties) {
                return { sampleJson: "{}", properties: [] };
            }

            const properties = [];
            const sampleObj = {};

            const reqList = schema.required || [];

            for (const [propName, propDef] of Object.entries(schema.properties)) {
                let pType = propDef.type || 'string';
                if (propDef['$ref']) {
                    pType = 'object';
                }
                const isRequired = reqList.includes(propName);
                
                properties.push({
                    name: propName,
                    type: pType,
                    description: propDef.title || propDef.description || '',
                    required: isRequired
                });

                // Build sample payload value
                if (pType === 'string') sampleObj[propName] = propDef.example || (propName.includes('email') ? 'user@example.com' : (propName.includes('password') ? 'secret123' : 'string'));
                else if (pType === 'integer' || pType === 'number') sampleObj[propName] = propDef.example || 1;
                else if (pType === 'boolean') sampleObj[propName] = true;
                else if (pType === 'array') sampleObj[propName] = [];
                else sampleObj[propName] = {};
            }

            return {
                sampleJson: JSON.stringify(sampleObj, null, 2),
                properties: properties
            };
        }

        // Render Sidebar Category Navigation
        function renderSidebar() {
            const sidebar = document.getElementById('sidebar-nav');
            const tags = Array.from(new Set(allEndpoints.flatMap(e => e.tags))).sort();

            tags.forEach(tag => {
                const count = allEndpoints.filter(e => e.tags.includes(tag)).length;
                const iconSvg = categorySvgIcons[tag] || categorySvgIcons['Default'];
                const div = document.createElement('div');
                div.className = 'sidebar-item';
                div.innerHTML = `
                    <div class="sidebar-item-left">
                        ${iconSvg}
                        <span>${tag}</span>
                    </div>
                    <span class="sidebar-badge">${count}</span>
                `;
                div.onclick = (e) => filterByGroup(tag, div);
                sidebar.appendChild(div);
            });
        }

        // Filter Handlers
        function filterByGroup(group, el) {
            document.querySelectorAll('.sidebar-item').forEach(i => i.classList.remove('active'));
            el.classList.add('active');
            activeGroup = group;
            renderContent();
        }

        function filterByMethod(method, el) {
            document.querySelectorAll('.method-filters .chip').forEach(c => c.classList.remove('active'));
            el.classList.add('active');
            activeMethod = method;
            renderContent();
        }

        document.getElementById('search-input').addEventListener('input', (e) => {
            searchQuery = e.target.value;
            renderContent();
        });

        // Render Main Route Cards
        function renderContent() {
            const container = document.getElementById('endpoints-container');
            container.innerHTML = '';

            const filtered = allEndpoints.filter(e => {
                const matchGroup = activeGroup === 'ALL' || e.tags.includes(activeGroup);
                const matchMethod = activeMethod === 'ALL' || e.method === activeMethod;
                const q = searchQuery.toLowerCase();
                const matchSearch = !q || 
                    e.path.toLowerCase().includes(q) ||
                    e.summary.toLowerCase().includes(q) ||
                    e.tags.some(t => t.toLowerCase().includes(q));

                return matchGroup && matchMethod && matchSearch;
            });

            if (filtered.length === 0) {
                container.innerHTML = `
                    <div style="background:white; border:1px solid var(--border-color); border-radius:16px; padding:4rem 2rem; text-align:center; color:var(--text-secondary);">
                        <h3>No routes match your search or filter</h3>
                        <p style="margin-top:0.5rem; font-size:0.9rem; color:var(--text-muted);">Try selecting 'All Routes' or searching for another keyword.</p>
                    </div>
                `;
                return;
            }

            // Group by Tag
            const groups = {};
            filtered.forEach(e => {
                const tag = e.tags[0] || 'Default';
                if (!groups[tag]) groups[tag] = [];
                groups[tag].push(e);
            });

            for (const [tag, items] of Object.entries(groups)) {
                const iconSvg = categorySvgIcons[tag] || categorySvgIcons['Default'];
                const groupDiv = document.createElement('div');

                let cardsHtml = items.map((ep, idx) => {
                    const drawerId = `drawer-${tag.replace(/\s+/g, '')}-${idx}`;
                    const swaggerUrl = `/docs#/${encodeURIComponent(tag)}/${ep.operationId}`;

                    // Params table HTML
                    let paramsHtml = '';
                    if (ep.parameters.length > 0) {
                        paramsHtml = `
                            <div class="drawer-section-title">📌 Query & Path Parameters</div>
                            <table class="param-table">
                                <thead>
                                    <tr>
                                        <th>Parameter</th>
                                        <th>Type</th>
                                        <th>Required</th>
                                        <th>In</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${ep.parameters.map(p => `
                                        <tr>
                                            <td class="param-name">${p.name}</td>
                                            <td class="param-type">${p.schema ? p.schema.type || 'string' : 'string'}</td>
                                            <td>${p.required ? '<span class="badge-req">REQUIRED</span>' : '<span class="badge-opt">OPTIONAL</span>'}</td>
                                            <td style="color:var(--text-muted);">${p.in || 'query'}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        `;
                    }

                    // Request Payload HTML
                    let payloadHtml = '';
                    if (ep.payload) {
                        payloadHtml = `
                            <div class="drawer-section-title">📥 Request Body Payload Schema</div>
                            ${ep.payload.properties.length > 0 ? `
                                <table class="param-table">
                                    <thead>
                                        <tr>
                                            <th>Field</th>
                                            <th>Data Type</th>
                                            <th>Required</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${ep.payload.properties.map(p => `
                                            <tr>
                                                <td class="param-name">${p.name}</td>
                                                <td class="param-type">${p.type}</td>
                                                <td>${p.required ? '<span class="badge-req">REQUIRED</span>' : '<span class="badge-opt">OPTIONAL</span>'}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            ` : ''}

                            <div style="font-size:0.8rem; color:var(--text-muted); margin-bottom:0.4rem; font-weight:700;">Sample JSON Request Body:</div>
                            <div class="code-block-wrapper">
                                <button class="copy-code-btn" onclick="copyText(\`${ep.payload.sampleJson.replace(/`/g, '\\`')}\`)">Copy JSON</button>
                                <pre class="code-block">${ep.payload.sampleJson}</pre>
                            </div>
                        `;
                    }

                    return `
                        <div class="route-card">
                            <div class="route-main" onclick="toggleDrawer('${drawerId}')">
                                <div class="route-top-row">
                                    <div class="route-path-group">
                                        <span class="method-badge method-${ep.method}">${ep.method}</span>
                                        <span class="route-path">${ep.path}</span>
                                    </div>
                                    <div class="route-actions" onclick="event.stopPropagation()">
                                        <button class="action-btn" onclick="copyText('${ep.path}')">
                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                                            Copy Route
                                        </button>
                                        <a href="${swaggerUrl}" class="action-btn" style="text-decoration:none; color:#4f46e5;">
                                            Open in Docs ➔
                                        </a>
                                    </div>
                                </div>
                                <div class="route-summary">${ep.summary}</div>
                            </div>

                            <div class="route-drawer" id="${drawerId}">
                                ${paramsHtml}
                                ${payloadHtml}
                                ${!paramsHtml && !payloadHtml ? '<div style="font-size:0.85rem; color:var(--text-muted);">No request payload or query parameters required for this endpoint.</div>' : ''}
                            </div>
                        </div>
                    `;
                }).join('');

                groupDiv.innerHTML = `
                    <div class="group-header">
                        <h2>
                            <span style="display:inline-flex; align-items:center;">${iconSvg}</span> 
                            <span>${tag}</span>
                        </h2>
                    </div>
                    <div>${cardsHtml}</div>
                `;

                container.appendChild(groupDiv);
            }
        }

        // Toggle Drawer
        function toggleDrawer(id) {
            const el = document.getElementById(id);
            if (el) {
                el.classList.toggle('open');
            }
        }

        // Copy Text Toast
        function copyText(text) {
            navigator.clipboard.writeText(text).then(() => {
                const toast = document.getElementById('toast');
                toast.classList.add('show');
                setTimeout(() => toast.classList.remove('show'), 2000);
            });
        }

        // Load Schema on Startup
        loadSchema();
    </script>
</body>
</html>
"""
