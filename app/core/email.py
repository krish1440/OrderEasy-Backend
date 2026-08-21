"""
Advanced Email Service & Template Engine for OrderEasy Analytics Backend
Uses Resend API to deliver responsive, high-end HTML email alerts
"""

import os
import resend
from typing import List, Dict, Any
from app.core.logger import get_logger

logger = get_logger(__name__)

# Initialize Resend API Key from Environment
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "krishchaudhary144@gmail.com")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://order-easy-blond.vercel.app")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


def build_advanced_admin_alert_html(orders: List[Dict[str, Any]]) -> str:
    """
    Generates an enterprise-grade, responsive HTML email template for 5-Day Pending Orders.
    Includes Order IDs, Customer Info, Expected Delivery Dates, Total Amounts, Items & CTA Button.
    """
    total_orders = len(orders)
    total_value = sum(float(o.get('total_amount', 0) or 0) for o in orders)
    orders_url = f"{FRONTEND_URL}/#/orders"

    orders_rows = ""
    for o in orders:
        order_id = o.get('id', 'N/A')
        customer = o.get('customer_name') or o.get('user_email') or 'Guest Customer'
        expected_date = o.get('expected_delivery_date') or o.get('delivery_date') or 'Approaching Soon'
        status = o.get('status', 'Pending').capitalize()
        amount = f"₹{float(o.get('total_amount', 0) or 0):,.2f}"
        items_count = o.get('total_items') or len(o.get('items', [])) or 1

        orders_rows += f"""
        <tr>
            <td style="padding: 14px 16px; border-bottom: 1px solid #e2e8f0; font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 700; color: #4f46e5;">
                #{str(order_id)[:8]}
            </td>
            <td style="padding: 14px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; font-weight: 600; color: #1e293b;">
                {customer}
            </td>
            <td style="padding: 14px 16px; border-bottom: 1px solid #e2e8f0; font-size: 13px; color: #d97706; font-weight: 700;">
                <span style="background: #fffbeb; border: 1px solid #fde68a; padding: 4px 10px; border-radius: 6px; display: inline-block;">
                    📅 {expected_date}
                </span>
            </td>
            <td style="padding: 14px 16px; border-bottom: 1px solid #e2e8f0; font-size: 13px; color: #64748b;">
                {items_count} item(s)
            </td>
            <td style="padding: 14px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; font-weight: 800; color: #059669; text-align: right;">
                {amount}
            </td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>5-Day Pending Orders Alert</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">
    
    <!-- Email Wrapper Container -->
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; padding: 30px 15px;">
        <tr>
            <td align="center">
                
                <!-- Main Email Card -->
                <table role="presentation" width="100%" style="max-width: 650px; background-color: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05);">
                    
                    <!-- Header Banner -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #4f46e5 0%, #3730a3 100%); padding: 32px 30px; text-align: left;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td>
                                        <div style="font-size: 22px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px;">
                                            OrderEasy <span style="font-size: 12px; font-weight: 600; background: rgba(255,255,255,0.2); padding: 3px 8px; border-radius: 20px; vertical-align: middle;">ADMIN ALERT</span>
                                        </div>
                                        <div style="color: #c7d2fe; font-size: 13px; margin-top: 4px;">
                                            Enterprise Intelligence & Automated Dispatch Engine
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Alert Badge & Heading -->
                    <tr>
                        <td style="padding: 30px 30px 10px 30px;">
                            <div style="display: inline-block; background-color: #fef2f2; border: 1px solid #fecaca; color: #dc2626; font-size: 12px; font-weight: 700; padding: 6px 14px; border-radius: 20px; text-transform: uppercase; letter-spacing: 0.5px;">
                                ⚠️ Action Required: 5-Day Delivery Deadline
                            </div>
                            <h2 style="font-size: 20px; font-weight: 800; color: #0f172a; margin: 16px 0 8px 0;">
                                Approaching Pending Delivery Alert
                            </h2>
                            <p style="font-size: 14px; color: #475569; line-height: 1.6; margin: 0;">
                                Hello Admin, the following <strong>{total_orders} pending order(s)</strong> have an expected delivery date arriving within the next <strong>5 days</strong>. Please review and ensure fulfillment dispatch.
                            </p>
                        </td>
                    </tr>

                    <!-- Key Metrics Summary Grid -->
                    <tr>
                        <td style="padding: 15px 30px 25px 30px;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px;">
                                <tr>
                                    <td width="50%" style="text-align: center; border-right: 1px solid #e2e8f0; padding-right: 10px;">
                                        <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #64748b; letter-spacing: 0.5px;">Approaching Orders</div>
                                        <div style="font-size: 24px; font-weight: 800; color: #4f46e5; margin-top: 2px;">{total_orders}</div>
                                    </td>
                                    <td width="50%" style="text-align: center; padding-left: 10px;">
                                        <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #64748b; letter-spacing: 0.5px;">Total Order Value</div>
                                        <div style="font-size: 24px; font-weight: 800; color: #059669; margin-top: 2px;">₹{total_value:,.2f}</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Itemized Orders Table -->
                    <tr>
                        <td style="padding: 0 30px 25px 30px;">
                            <div style="font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 12px;">
                                📋 Pending Orders Breakdown:
                            </div>
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse: collapse; border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden;">
                                <thead>
                                    <tr style="background-color: #f1f5f9;">
                                        <th style="padding: 10px 16px; text-align: left; font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase;">Order ID</th>
                                        <th style="padding: 10px 16px; text-align: left; font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase;">Customer</th>
                                        <th style="padding: 10px 16px; text-align: left; font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase;">Expected Date</th>
                                        <th style="padding: 10px 16px; text-align: left; font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase;">Items</th>
                                        <th style="padding: 10px 16px; text-align: right; font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase;">Amount</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {orders_rows}
                                </tbody>
                            </table>
                        </td>
                    </tr>

                    <!-- CTA Mobile Button -->
                    <tr>
                        <td style="padding: 10px 30px 35px 30px; text-align: center;">
                            <a href="{orders_url}" target="_blank" style="display: inline-block; background-color: #4f46e5; color: #ffffff; font-size: 15px; font-weight: 700; text-decoration: none; padding: 14px 32px; border-radius: 10px; box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35);">
                                📦 View & Process Pending Orders ➔
                            </a>
                            <div style="font-size: 12px; color: #94a3b8; margin-top: 10px;">
                                One-tap redirection to OrderEasy Platform
                            </div>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 20px 30px; border-top: 1px solid #e2e8f0; text-align: center; font-size: 12px; color: #64748b;">
                            <div>Sent to <strong>{ADMIN_EMAIL}</strong> • OrderEasy Analytics Platform</div>
                            <div style="margin-top: 4px; color: #94a3b8;">
                                Note: Duplicate alert protection is active. This notification will be sent only once per order.
                            </div>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def send_admin_pending_orders_alert(orders: List[Dict[str, Any]], recipient_email: str = None) -> bool:
    """
    Dispatches the batched 5-day pending orders alert email via Resend API to the specific organization/user email.
    """
    if not RESEND_API_KEY:
        logger.error("RESEND_API_KEY is not configured in environment variables.")
        return False

    if not orders:
        logger.info("No approaching pending orders to notify.")
        return False

    target_email = recipient_email or ADMIN_EMAIL
    html_content = build_advanced_admin_alert_html(orders)
    subject = f"⚠️ Action Required: {len(orders)} Pending Order(s) Approaching 5-Day Delivery"

    try:
        response = resend.Emails.send({
            "from": "OrderEasy Alerts <onboarding@resend.dev>",
            "to": target_email,
            "subject": subject,
            "html": html_content
        })
        logger.info(f"Successfully sent pending orders alert email to {target_email} via Resend. ID: {response}")
        return True
    except Exception as e:
        logger.error(f"Failed to send pending orders alert email to {target_email}: {e}")
        return False
