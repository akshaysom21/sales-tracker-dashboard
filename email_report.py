import smtplib
import os
import pandas as pd
import numpy as np
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
import schedule
import time
import logging

from config import EMAIL_CONFIG, REPORT_CONFIG, PATHS

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_report_data():

    filepath = PATHS['processed_completed']

    if not os.path.exists(filepath):
        logger.error(f"Data file not found: {filepath}")
        logger.error("Run data_generator.py then data_processor.py first")
        return None

    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'])
    logger.info(f"Loaded {len(df):,} records for report generation")
    return df


def get_period_data(df, period='daily'):

    today = datetime.now().date()

    if period == 'daily':
        curr_start = today - timedelta(days=1)
        curr_end = today - timedelta(days=1)
        prev_start = today - timedelta(days=2)
        prev_end = today - timedelta(days=2)
        label = f"Yesterday — {curr_start.strftime('%A, %B %d, %Y')}"

    elif period == 'weekly':
        days_back = today.weekday() + 7
        curr_start = today - timedelta(days=days_back)
        curr_end = curr_start + timedelta(days=6)
        prev_start = curr_start - timedelta(days=7)
        prev_end = curr_end - timedelta(days=7)
        label = f"Week of {curr_start.strftime('%B %d')} – {curr_end.strftime('%B %d, %Y')}"

    elif period == 'monthly':
        first_this = today.replace(day=1)
        curr_end = first_this - timedelta(days=1)
        curr_start = curr_end.replace(day=1)
        prev_end = curr_start - timedelta(days=1)
        prev_start = prev_end.replace(day=1)
        label = curr_start.strftime('%B %Y')

    else:
        raise ValueError(f"period must be 'daily', 'weekly', or 'monthly'")

    df_curr = df[
        (df['date'].dt.date >= curr_start) &
        (df['date'].dt.date <= curr_end)
    ].copy()

    df_prev = df[
        (df['date'].dt.date >= prev_start) &
        (df['date'].dt.date <= prev_end)
    ].copy()

    return df_curr, df_prev, label


def compute_metrics(data):

    if len(data) == 0:
        return {
            'revenue': 0.0,
            'orders': 0,
            'profit': 0.0,
            'avg_order_value': 0.0,
            'profit_margin': 0.0,
            'customers': 0,
            'units_sold': 0,
        }

    return {
        'revenue': round(data['revenue'].sum(), 2),
        'orders': len(data),
        'profit': round(data['profit'].sum(), 2),
        'avg_order_value': round(data['revenue'].mean(), 2),
        'profit_margin': round(data['profit_margin'].mean(), 2),
        'customers': data['customer_email'].nunique(),
        'units_sold': int(data['quantity'].sum()),
    }


def pct_change(current, previous):
    if previous == 0:
        return 0.0
    return round((current - previous) / previous * 100, 2)


def get_top_products(data, n=5):
    if len(data) == 0:
        return []

    top = (
        data.groupby('product_name')
        .agg(revenue=('revenue', 'sum'), orders=('order_id', 'count'))
        .reset_index()
        .sort_values('revenue', ascending=False)
        .head(n)
    )
    return top.to_dict('records')


def get_channel_breakdown(data):
    if len(data) == 0:
        return []

    ch = (
        data.groupby('channel')
        .agg(revenue=('revenue', 'sum'), orders=('order_id', 'count'))
        .reset_index()
        .sort_values('revenue', ascending=False)
    )
    total = ch['revenue'].sum()
    ch['share'] = ((ch['revenue'] / total * 100) if total > 0 else 0).round(1)
    return ch.to_dict('records')


def generate_insights(curr, prev, changes):

    insights = []

    rev_chg = changes['revenue']
    if rev_chg >= 20:
        insights.append(('🚀', '#28a745',
            f"Revenue surged {rev_chg:.1f}%! Keep doing what's working — "
            f"this is exceptional growth."))
    elif rev_chg >= 5:
        insights.append(('📈', '#17a2b8',
            f"Revenue grew {rev_chg:.1f}% compared to the previous period. "
            f"Positive momentum — stay consistent."))
    elif rev_chg <= -20:
        insights.append(('🚨', '#dc3545',
            f"Revenue dropped {abs(rev_chg):.1f}%. Investigate immediately — "
            f"check traffic, inventory, and any technical issues."))
    elif rev_chg <= -5:
        insights.append(('⚠️', '#ffc107',
            f"Revenue is down {abs(rev_chg):.1f}%. Consider running a promotion "
            f"or increasing ad spend to recover."))

    margin = curr['profit_margin']
    if margin >= 40:
        insights.append(('💎', '#28a745',
            f"Outstanding profit margin of {margin:.1f}%! Your pricing and cost "
            f"structure are working extremely well."))
    elif margin < 15:
        insights.append(('💸', '#dc3545',
            f"Profit margin is only {margin:.1f}%. Review your pricing, reduce "
            f"unnecessary discounts, or find cheaper suppliers."))

    aov_chg = changes['avg_order_value']
    if aov_chg >= 10:
        insights.append(('🎯', '#28a745',
            f"Average order value increased {aov_chg:.1f}%. "
            f"Your upsell and bundle strategies are working!"))
    elif aov_chg <= -10:
        insights.append(('🎯', '#ffc107',
            f"Average order value dropped {abs(aov_chg):.1f}%. "
            f"Consider adding product bundles or a minimum-order discount."))

    ord_chg = changes['orders']
    if ord_chg >= 15:
        insights.append(('🛒', '#17a2b8',
            f"Orders jumped {ord_chg:.1f}%! Make sure inventory and "
            f"fulfillment capacity can handle increased demand."))

    if not insights:
        insights.append(('📊', '#6c757d',
            "Performance is stable this period. Set clear growth targets "
            "and review your marketing strategy to accelerate growth."))

    return insights


def fmt_usd(value):
    if value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value/1_000:.1f}K"
    return f"${value:,.2f}"


def fmt_num(value):
    return f"{int(value):,}"


def fmt_pct(value):
    return f"{value:.1f}%"


def arrow_html(change):
    if change > 0:
        return f'<span style="color:#28a745;">↑ {abs(change):.1f}% vs prev</span>'
    elif change < 0:
        return f'<span style="color:#dc3545;">↓ {abs(change):.1f}% vs prev</span>'
    else:
        return f'<span style="color:#6c757d;">→ No change</span>'


def build_html_report(period_label, curr, changes, top_products, channels, insights, period_type):

    company = REPORT_CONFIG['company_name']
    now = datetime.now().strftime('%B %d, %Y at %I:%M %p')

    products_rows = ''
    for i, p in enumerate(top_products):
        bg = '#f8f9ff' if i % 2 == 0 else '#ffffff'
        products_rows += f"""
        <tr style="background:{bg};">
            <td style="padding:11px 14px;font-weight:bold;color:#667eea;">#{i+1}</td>
            <td style="padding:11px 14px;">{p['product_name']}</td>
            <td style="padding:11px 14px;text-align:right;font-weight:bold;">{fmt_usd(p['revenue'])}</td>
            <td style="padding:11px 14px;text-align:center;">{fmt_num(p['orders'])}</td>
        </tr>"""

    if not products_rows:
        products_rows = '<tr><td colspan="4" style="padding:20px;text-align:center;color:#999;">No sales recorded this period</td></tr>'

    channel_rows = ''
    for i, ch in enumerate(channels):
        bg = '#f8f9ff' if i % 2 == 0 else '#ffffff'
        share = ch.get('share', 0)
        channel_rows += f"""
        <tr style="background:{bg};">
            <td style="padding:11px 14px;">{ch['channel']}</td>
            <td style="padding:11px 14px;text-align:right;font-weight:bold;">{fmt_usd(ch['revenue'])}</td>
            <td style="padding:11px 14px;text-align:center;">{fmt_num(ch['orders'])}</td>
            <td style="padding:11px 14px;">
                <div style="background:#e9ecef;border-radius:8px;height:9px;width:100%;margin-bottom:3px;">
                    <div style="background:#667eea;border-radius:8px;height:9px;width:{min(share,100):.0f}%;"></div>
                </div>
                <small style="color:#666;">{share:.1f}%</small>
            </td>
        </tr>"""

    if not channel_rows:
        channel_rows = '<tr><td colspan="4" style="padding:20px;text-align:center;color:#999;">No data</td></tr>'

    insights_html = ''
    for icon, color, text in insights:
        insights_html += f"""
        <div style="background:{color}12;border-left:4px solid {color};
                    padding:13px 16px;margin:10px 0;border-radius:5px;
                    display:flex;align-items:flex-start;">
            <span style="font-size:20px;margin-right:12px;line-height:1.4;">{icon}</span>
            <span style="color:#333;font-size:14px;line-height:1.6;">{text}</span>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{company} Sales Report</title>
</head>
<body style="margin:0;padding:0;background:#f0f2f5;font-family:Arial,Helvetica,sans-serif;color:#333;">

<table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f2f5;padding:30px 10px;">
<tr><td align="center">

<table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;">

<!-- HEADER -->
<tr><td>
<div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
            border-radius:16px 16px 0 0;padding:40px 40px 35px 40px;text-align:center;">
    <div style="font-size:36px;margin-bottom:12px;">📊</div>
    <h1 style="color:#fff;margin:0;font-size:26px;font-weight:700;letter-spacing:-0.5px;">
        Sales Performance Report
    </h1>
    <p style="color:rgba(255,255,255,0.85);margin:8px 0 0 0;font-size:15px;font-weight:500;">
        {company}
    </p>
    <p style="color:rgba(255,255,255,0.65);margin:6px 0 0 0;font-size:13px;">
        {period_label} &nbsp;·&nbsp; Generated {now}
    </p>
</div>
</td></tr>

<!-- KPI SECTION -->
<tr><td style="background:#fff;padding:35px 40px 25px 40px;">

    <h2 style="margin:0 0 22px 0;font-size:17px;color:#1a1a2e;
               border-bottom:2px solid #667eea;padding-bottom:10px;">
        📈 Key Metrics
    </h2>

    <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
        <td width="49%" style="vertical-align:top;padding-right:8px;">
            <div style="background:#f7f8ff;border-radius:12px;padding:20px;
                        border-left:5px solid #667eea;margin-bottom:14px;">
                <p style="margin:0;font-size:12px;color:#888;text-transform:uppercase;
                           letter-spacing:0.5px;">💰 Total Revenue</p>
                <p style="margin:8px 0 4px;font-size:30px;font-weight:700;color:#1a1a2e;">
                    {fmt_usd(curr['revenue'])}
                </p>
                <p style="margin:0;font-size:13px;">{arrow_html(changes['revenue'])}</p>
            </div>
        </td>
        <td width="49%" style="vertical-align:top;padding-left:8px;">
            <div style="background:#f7f8ff;border-radius:12px;padding:20px;
                        border-left:5px solid #764ba2;margin-bottom:14px;">
                <p style="margin:0;font-size:12px;color:#888;text-transform:uppercase;
                           letter-spacing:0.5px;">🛒 Total Orders</p>
                <p style="margin:8px 0 4px;font-size:30px;font-weight:700;color:#1a1a2e;">
                    {fmt_num(curr['orders'])}
                </p>
                <p style="margin:0;font-size:13px;">{arrow_html(changes['orders'])}</p>
            </div>
        </td>
    </tr>
    <tr>
        <td width="49%" style="vertical-align:top;padding-right:8px;">
            <div style="background:#f7f8ff;border-radius:12px;padding:20px;
                        border-left:5px solid #28a745;margin-bottom:14px;">
                <p style="margin:0;font-size:12px;color:#888;text-transform:uppercase;
                           letter-spacing:0.5px;">💎 Total Profit</p>
                <p style="margin:8px 0 4px;font-size:30px;font-weight:700;color:#1a1a2e;">
                    {fmt_usd(curr['profit'])}
                </p>
                <p style="margin:0;font-size:13px;">{arrow_html(changes['profit'])}</p>
            </div>
        </td>
        <td width="49%" style="vertical-align:top;padding-left:8px;">
            <div style="background:#f7f8ff;border-radius:12px;padding:20px;
                        border-left:5px solid #17a2b8;margin-bottom:14px;">
                <p style="margin:0;font-size:12px;color:#888;text-transform:uppercase;
                           letter-spacing:0.5px;">🎯 Avg Order Value</p>
                <p style="margin:8px 0 4px;font-size:30px;font-weight:700;color:#1a1a2e;">
                    {fmt_usd(curr['avg_order_value'])}
                </p>
                <p style="margin:0;font-size:13px;">{arrow_html(changes['avg_order_value'])}</p>
            </div>
        </td>
    </tr>
    </table>

    <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
        <td style="text-align:center;background:#f7f8ff;border-radius:10px;
                   padding:16px 10px;width:33%;">
            <p style="margin:0;font-size:11px;color:#888;text-transform:uppercase;">
                👥 Customers
            </p>
            <p style="margin:6px 0 0;font-size:22px;font-weight:700;color:#1a1a2e;">
                {fmt_num(curr['customers'])}
            </p>
        </td>
        <td width="10px"></td>
        <td style="text-align:center;background:#f7f8ff;border-radius:10px;
                   padding:16px 10px;width:33%;">
            <p style="margin:0;font-size:11px;color:#888;text-transform:uppercase;">
                📦 Units Sold
            </p>
            <p style="margin:6px 0 0;font-size:22px;font-weight:700;color:#1a1a2e;">
                {fmt_num(curr['units_sold'])}
            </p>
        </td>
        <td width="10px"></td>
        <td style="text-align:center;background:#f7f8ff;border-radius:10px;
                   padding:16px 10px;width:33%;">
            <p style="margin:0;font-size:11px;color:#888;text-transform:uppercase;">
                📊 Profit Margin
            </p>
            <p style="margin:6px 0 0;font-size:22px;font-weight:700;color:#1a1a2e;">
                {fmt_pct(curr['profit_margin'])}
            </p>
        </td>
    </tr>
    </table>

</td></tr>

<!-- TOP PRODUCTS -->
<tr><td style="background:#fff;padding:0 40px 30px 40px;">

    <h2 style="margin:0 0 18px 0;font-size:17px;color:#1a1a2e;
               border-bottom:2px solid #667eea;padding-bottom:10px;">
        🏆 Top Products This Period
    </h2>

    <table width="100%" cellpadding="0" cellspacing="0"
           style="border-collapse:collapse;border-radius:10px;overflow:hidden;
                  border:1px solid #eee;">
        <thead>
            <tr style="background:#667eea;color:#fff;">
                <th style="padding:12px 14px;text-align:left;font-size:13px;font-weight:600;">
                    #
                </th>
                <th style="padding:12px 14px;text-align:left;font-size:13px;font-weight:600;">
                    Product
                </th>
                <th style="padding:12px 14px;text-align:right;font-size:13px;font-weight:600;">
                    Revenue
                </th>
                <th style="padding:12px 14px;text-align:center;font-size:13px;font-weight:600;">
                    Orders
                </th>
            </tr>
        </thead>
        <tbody>{products_rows}</tbody>
    </table>

</td></tr>

<!-- CHANNELS -->
<tr><td style="background:#f7f8ff;padding:30px 40px;">

    <h2 style="margin:0 0 18px 0;font-size:17px;color:#1a1a2e;
               border-bottom:2px solid #764ba2;padding-bottom:10px;">
        📢 Sales by Channel
    </h2>

    <table width="100%" cellpadding="0" cellspacing="0"
           style="border-collapse:collapse;border-radius:10px;overflow:hidden;
                  border:1px solid #e0e0e0;">
        <thead>
            <tr style="background:#764ba2;color:#fff;">
                <th style="padding:12px 14px;text-align:left;font-size:13px;font-weight:600;">
                    Channel
                </th>
                <th style="padding:12px 14px;text-align:right;font-size:13px;font-weight:600;">
                    Revenue
                </th>
                <th style="padding:12px 14px;text-align:center;font-size:13px;font-weight:600;">
                    Orders
                </th>
                <th style="padding:12px 14px;text-align:left;font-size:13px;font-weight:600;">
                    Share
                </th>
            </tr>
        </thead>
        <tbody>{channel_rows}</tbody>
    </table>

</td></tr>

<!-- INSIGHTS -->
<tr><td style="background:#fff;padding:30px 40px;">

    <h2 style="margin:0 0 18px 0;font-size:17px;color:#1a1a2e;
               border-bottom:2px solid #667eea;padding-bottom:10px;">
        💡 Insights & Recommendations
    </h2>
    {insights_html}

</td></tr>

<!-- FOOTER -->
<tr><td>
<div style="background:#1a1a2e;border-radius:0 0 16px 16px;
            padding:28px 40px;text-align:center;">
    <p style="color:rgba(255,255,255,0.8);margin:0;font-size:14px;font-weight:500;">
        📊 {company} — Automated Sales Report
    </p>
    <p style="color:rgba(255,255,255,0.45);margin:8px 0 0 0;font-size:12px;">
        This report is generated automatically. Do not reply to this email.
    </p>
</div>
</td></tr>

</table>

</td></tr>
</table>

</body>
</html>"""

    return html


def send_email_report(recipients, subject, html_body):

    if not EMAIL_CONFIG['sender_email'] or not EMAIL_CONFIG['sender_password']:
        logger.warning("Email credentials not configured in .env file")
        logger.warning("Skipping email send — report saved locally only")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{EMAIL_CONFIG['sender_name']} <{EMAIL_CONFIG['sender_email']}>"
        msg['To'] = ', '.join(recipients)

        msg.attach(MIMEText(html_body, 'html'))

        logger.info(f"Connecting to {EMAIL_CONFIG['smtp_host']}:{EMAIL_CONFIG['smtp_port']} ...")

        with smtplib.SMTP(EMAIL_CONFIG['smtp_host'], EMAIL_CONFIG['smtp_port']) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.sendmail(
                EMAIL_CONFIG['sender_email'],
                recipients,
                msg.as_string()
            )

        logger.info(f"-> Email sent to: {', '.join(recipients)}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("Authentication failed.")
        logger.error("For Gmail: use an App Password, not your regular password.")
        logger.error("Guide: myaccount.google.com → Security → App Passwords")
        return False

    except smtplib.SMTPConnectError:
        logger.error(f"Cannot connect to {EMAIL_CONFIG['smtp_host']}:{EMAIL_CONFIG['smtp_port']}")
        logger.error("Check your internet connection and SMTP settings in .env")
        return False

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


def generate_and_send(period='daily', recipients=None, save_local=True):

    logger.info(f"\n{'='*55}")
    logger.info(f"  GENERATING {period.upper()} REPORT")
    logger.info(f"{'='*55}")

    df = load_report_data()
    if df is None:
        return False

    df_curr, df_prev, label = get_period_data(df, period=period)

    curr = compute_metrics(df_curr)
    prev = compute_metrics(df_prev)

    changes = {
        key: pct_change(curr[key], prev[key])
        for key in curr
    }

    top_products = get_top_products(df_curr, n=REPORT_CONFIG['top_n_products'])
    channels = get_channel_breakdown(df_curr)
    insights = generate_insights(curr, prev, changes)

    html = build_html_report(
        period_label = label,
        curr = curr,
        changes = changes,
        top_products = top_products,
        channels = channels,
        insights = insights,
        period_type = period,
    )

    if save_local:
        os.makedirs('reports', exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"reports/{period}_report_{ts}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        logger.info(f"Report saved locally: {filename}")

    recipients = recipients or [r for r in EMAIL_CONFIG['default_recipients'] if r]

    if recipients:
        company = REPORT_CONFIG['company_name']
        subjects = {
            'daily': f"📊 Daily Sales Report — {label} | {company}",
            'weekly': f"📊 Weekly Sales Report — {label} | {company}",
            'monthly': f"📊 Monthly Sales Report — {label} | {company}",
        }
        subject = subjects.get(period, f"📊 Sales Report — {label}")
        return send_email_report(recipients, subject, html)

    logger.info("No recipients configured — skipping email send")
    return True


def start_scheduler():

    logger.info("🕐 Report scheduler started")
    logger.info(f"   Daily : every day at {EMAIL_CONFIG['daily_report_time']}")
    logger.info(f"   Weekly : every {EMAIL_CONFIG['weekly_report_day']} at {EMAIL_CONFIG['weekly_report_time']}")
    logger.info(f"   Monthly: 1st of each month at 07:00")
    logger.info("   Press Ctrl+C to stop\n")

    schedule.every().day.at(
        EMAIL_CONFIG['daily_report_time']
    ).do(generate_and_send, period='daily')

    getattr(
        schedule.every(), EMAIL_CONFIG['weekly_report_day']
    ).at(EMAIL_CONFIG['weekly_report_time']).do(generate_and_send, period='weekly')

    def check_monthly():
        if datetime.now().day == EMAIL_CONFIG['monthly_report_day']:
            generate_and_send(period='monthly')

    schedule.every().day.at("07:00").do(check_monthly)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()

        if arg == '--schedule':
            start_scheduler()
        elif arg == '--weekly':
            generate_and_send(period='weekly')
        elif arg == '--monthly':
            generate_and_send(period='monthly')
        elif arg == '--daily':
            generate_and_send(period='daily')
        else:
            print(f"Unknown argument: {arg}")
            print("Usage:")
            print("  python email_report.py              → daily report")
            print("  python email_report.py --weekly     → weekly report")
            print("  python email_report.py --monthly    → monthly report")
            print("  python email_report.py --schedule   → start scheduler")
    else:
        generate_and_send(period='daily', save_local=True)