"""
Professional Anti-Spam Email Service & Template Engine for OrderEasy Platform
Uses Resend API with clean corporate formatting, 0 emojis, and anti-spam optimization.
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
    Generates an executive-grade, professional HTML email template for 5-Day Pending Orders.
    Optimized for high deliverability (0 emojis, clean markup, anti-spam headers).
    """
    total_orders = len(orders)
    
    total_value = 0.0
    for o in orders:
        val = o.get('total_amount_with_gst') or o.get('total_amount') or o.get('pending_amount') or o.get('price') or 0
        try:
            total_value += float(val)
        except (ValueError, TypeError):
            pass

    orders_url = f"{FRONTEND_URL}/#/orders"

    orders_rows = ""
    for o in orders:
        order_num = o.get('order_id') if o.get('order_id') is not None else o.get('id', 'N/A')
        customer = o.get('receiver_name') or o.get('customer_name') or o.get('org') or 'Customer'
        expected_date = o.get('expected_delivery_date') or o.get('date') or 'Approaching Soon'
        product_name = o.get('product') or 'Order Item'
        qty = o.get('quantity') or 1
        
        val = o.get('total_amount_with_gst') or o.get('pending_amount') or o.get('total_amount') or o.get('price') or 0
        try:
            amount_num = float(val)
            amount_str = f"₹{amount_num:,.2f}"
        except (ValueError, TypeError):
            amount_str = "₹0.00"

        orders_rows += f"""
        <tr>
            <td style="padding: 14px 16px; border-bottom: 1px solid #e2e8f0; font-family: Arial, sans-serif; font-size: 14px; font-weight: bold; color: #4f46e5;">
                #{order_num}
            </td>
            <td style="padding: 14px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; font-weight: 600; color: #1e293b;">
                <div>{customer}</div>
                <div style="font-size: 12px; color: #64748b; font-weight: normal; margin-top: 2px;">Item: {product_name}</div>
            </td>
            <td style="padding: 14px 16px; border-bottom: 1px solid #e2e8f0; font-size: 13px; color: #b45309; font-weight: bold;">
                <span style="background-color: #fffbeb; border: 1px solid #fde68a; padding: 4px 10px; border-radius: 6px; display: inline-block;">
                    {expected_date}
                </span>
            </td>
            <td style="padding: 14px 16px; border-bottom: 1px solid #e2e8f0; font-size: 13px; color: #64748b;">
                {qty} qty
            </td>
            <td style="padding: 14px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; font-weight: bold; color: #059669; text-align: right;">
                {amount_str}
            </td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OrderEasy Pending Orders Notification</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: Arial, sans-serif; -webkit-font-smoothing: antialiased;">
    
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; padding: 30px 15px;">
        <tr>
            <td align="center">
                
                <table role="presentation" width="100%" style="max-width: 650px; background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                    
                    <!-- Header Banner -->
                    <tr>
                        <td style="background-color: #4f46e5; padding: 28px 30px; text-align: left;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td>
                                        <div style="font-size: 22px; font-weight: bold; color: #ffffff; letter-spacing: -0.5px;">
                                            OrderEasy <span style="font-size: 12px; font-weight: bold; background-color: rgba(255,255,255,0.2); padding: 3px 8px; border-radius: 4px; vertical-align: middle;">ADMIN NOTIFICATION</span>
                                        </div>
                                        <div style="color: #c7d2fe; font-size: 13px; margin-top: 4px;">
                                            Automated Order Management System
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Alert Badge & Heading -->
                    <tr>
                        <td style="padding: 30px 30px 10px 30px;">
                            <div style="display: inline-block; background-color: #fef3c7; border: 1px solid #fde68a; color: #92400e; font-size: 12px; font-weight: bold; padding: 5px 12px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.5px;">
                                Delivery Schedule Alert
                            </div>
                            <h2 style="font-size: 20px; font-weight: bold; color: #0f172a; margin: 16px 0 8px 0;">
                                Upcoming Pending Orders Delivery Notice
                            </h2>
                            <p style="font-size: 14px; color: #475569; line-height: 1.6; margin: 0;">
                                Hello, the following <strong>{total_orders} pending order(s)</strong> have an expected delivery date scheduled within the next <strong>5 days</strong>. Please review and ensure order fulfillment.
                            </p>
                        </td>
                    </tr>

                    <!-- Key Metrics Summary Grid -->
                    <tr>
                        <td style="padding: 15px 30px 25px 30px;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px;">
                                <tr>
                                    <td width="50%" style="text-align: center; border-right: 1px solid #e2e8f0; padding-right: 10px;">
                                        <div style="font-size: 11px; text-transform: uppercase; font-weight: bold; color: #64748b; letter-spacing: 0.5px;">Pending Orders</div>
                                        <div style="font-size: 24px; font-weight: bold; color: #4f46e5; margin-top: 2px;">{total_orders}</div>
                                    </td>
                                    <td width="50%" style="text-align: center; padding-left: 10px;">
                                        <div style="font-size: 11px; text-transform: uppercase; font-weight: bold; color: #64748b; letter-spacing: 0.5px;">Total Order Value</div>
                                        <div style="font-size: 24px; font-weight: bold; color: #059669; margin-top: 2px;">₹{total_value:,.2f}</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Itemized Orders Table -->
                    <tr>
                        <td style="padding: 0 30px 25px 30px;">
                            <div style="font-size: 14px; font-weight: bold; color: #0f172a; margin-bottom: 12px;">
                                Schedule Breakdown:
                            </div>
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse: collapse; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
                                <thead>
                                    <tr style="background-color: #f1f5f9;">
                                        <th style="padding: 10px 16px; text-align: left; font-size: 11px; font-weight: bold; color: #475569; text-transform: uppercase;">Order ID</th>
                                        <th style="padding: 10px 16px; text-align: left; font-size: 11px; font-weight: bold; color: #475569; text-transform: uppercase;">Receiver & Details</th>
                                        <th style="padding: 10px 16px; text-align: left; font-size: 11px; font-weight: bold; color: #475569; text-transform: uppercase;">Expected Date</th>
                                        <th style="padding: 10px 16px; text-align: left; font-size: 11px; font-weight: bold; color: #475569; text-transform: uppercase;">Qty</th>
                                        <th style="padding: 10px 16px; text-align: right; font-size: 11px; font-weight: bold; color: #475569; text-transform: uppercase;">Amount</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {orders_rows}
                                </tbody>
                            </table>
                        </td>
                    </tr>

                    <!-- CTA Button -->
                    <tr>
                        <td style="padding: 10px 30px 35px 30px; text-align: center;">
                            <a href="{orders_url}" target="_blank" style="display: inline-block; background-color: #4f46e5; color: #ffffff; font-size: 14px; font-weight: bold; text-decoration: none; padding: 12px 28px; border-radius: 8px;">
                                View Pending Orders &rarr;
                            </a>
                            <div style="font-size: 12px; color: #94a3b8; margin-top: 10px;">
                                Direct link to your OrderEasy management portal
                            </div>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 20px 30px; border-top: 1px solid #e2e8f0; text-align: center; font-size: 12px; color: #64748b;">
                            <div>OrderEasy Analytics System Notification</div>
                            <div style="margin-top: 4px; color: #94a3b8;">
                                Automated status report. Duplicate notifications are disabled.
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
    Guarantees each user receives ONLY their own orders at their registered email.
    """
    if not RESEND_API_KEY:
        logger.error("RESEND_API_KEY is not configured in environment variables.")
        return False

    if not orders:
        logger.info("No approaching pending orders to notify.")
        return False

    target_email = recipient_email or ADMIN_EMAIL
    if not target_email or "@" not in str(target_email):
        logger.warning(f"Skipping email alert dispatch: No valid recipient email found for orders: {orders}")
        return False
    html_content = build_advanced_admin_alert_html(orders)
    
    # Professional Anti-Spam Subject Line (no emojis, no ALL-CAPS spam triggers)
    subject = f"OrderEasy Notification: Pending Order Delivery Schedule ({len(orders)} Orders)"

    try:
        response = resend.Emails.send({
            "from": "OrderEasy System <onboarding@resend.dev>",
            "to": target_email,
            "subject": subject,
            "html": html_content
        })
        logger.info(f"Successfully sent pending orders alert email to {target_email} via Resend. ID: {response}")
        return True
    except Exception as e:
        logger.error(f"Failed to send pending orders alert email to {target_email}: {e}")
        return False
