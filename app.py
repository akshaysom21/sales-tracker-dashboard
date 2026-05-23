import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
import sys
from datetime import datetime, timedelta

from data_processor import load_data, add_time_features
from kpi_calculator import (
    calculate_revenue_metrics,
    calculate_product_performance,
    calculate_category_performance,
    calculate_channel_performance,
    calculate_daily_sales,
    calculate_monthly_sales,
    calculate_geographic_performance,
    calculate_regional_performance,
    calculate_payment_method_breakdown,
    calculate_customer_type_breakdown,
    calculate_hourly_patterns,
    calculate_top_customers,
)
from forecasting import run_full_forecast
from config import DASHBOARD_CONFIG, REPORT_CONFIG, APP_CONFIG

if 'chart_palette' not in DASHBOARD_CONFIG:
    DASHBOARD_CONFIG['chart_palette'] = [
        '#667eea', '#764ba2', '#f093fb',
        '#4facfe', '#00f2fe', '#43e97b',
        '#fa709a', '#fee140', '#30cfd0',
        '#a18cd1', '#fbc2eb', '#ffecd2'
    ]


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title = "Sales Tracker Dashboard",
    page_icon = "📊",
    layout = "wide",
    initial_sidebar_state = "expanded",
)


# ==========================================
# CUSTOM CSS
# ==========================================

st.markdown("""
<style>

    /* ===== FORCE LIGHT THEME EVERYWHERE ===== */
    
    html, body, [data-testid="stApp"] {
        background-color: #f4f6f9 !important;
        color: #1a1a2e !important;
    }

    /* Main content area */
    .main, .block-container {
        background-color: #f4f6f9 !important;
        color: #1a1a2e !important;
    }

    /* All text elements */
    p, span, div, label, h1, h2, h3, h4, h5, h6 {
        color: #1a1a2e;
    }

    /* Streamlit specific text */
    .stMarkdown, .stText, .stWrite {
        color: #1a1a2e !important;
    }

    /* Tab labels */
    .stTabs [data-baseweb="tab"] {
        color: #555555 !important;
        font-weight: 600;
        font-size: 14px;
        padding: 10px 16px;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #667eea !important;
        border-bottom: 3px solid #667eea;
    }

    .stTabs [data-baseweb="tab-list"] {
        background-color: #ffffff !important;
        border-radius: 8px;
        padding: 4px;
        gap: 4px;
        border-bottom: 1px solid #e0e0e0;
    }

    /* Selectbox */
    .stSelectbox > div > div {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
        border: 1px solid #ddd !important;
    }

    /* Date input */
    .stDateInput > div > div {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
    }

    /* Text input */
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
        border: 1px solid #ddd !important;
    }

    /* Slider */
    .stSlider > div {
        color: #1a1a2e !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #667eea !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        background-color: #5a6fd6 !important;
        box-shadow: 0 4px 12px rgba(102,126,234,0.4) !important;
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background-color: #667eea !important;
        color: white !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background-color: #28a745 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }

    /* Dataframe / Table */
    .stDataFrame {
        background-color: #ffffff !important;
    }

    .stDataFrame table {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
    }

    .stDataFrame th {
        background-color: #667eea !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    .stDataFrame td {
        color: #1a1a2e !important;
        border-bottom: 1px solid #f0f0f0 !important;
    }

    /* Info / Warning / Error / Success boxes */
    .stAlert {
        border-radius: 8px !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
        font-weight: 600 !important;
    }

    /* Metric widget */
    [data-testid="stMetric"] {
        background-color: #ffffff !important;
        border-radius: 10px !important;
        padding: 16px !important;
        border: 1px solid #eee !important;
    }

    [data-testid="stMetricLabel"] {
        color: #666666 !important;
        font-size: 13px !important;
    }

    [data-testid="stMetricValue"] {
        color: #1a1a2e !important;
        font-weight: 700 !important;
    }

    [data-testid="stMetricDelta"] {
        font-size: 13px !important;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }

    /* Progress bar */
    .stProgress > div > div {
        background-color: #667eea !important;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ===== SIDEBAR ===== */

    section[data-testid="stSidebar"] {
        background-color: #1a1a2e !important;
        border-right: 1px solid #2d2d4e !important;
    }

    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: #2d2d4e !important;
        color: #ffffff !important;
        border: 1px solid #3d3d6e !important;
    }

    section[data-testid="stSidebar"] .stSelectbox > div > div > div {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] .stButton > button {
        background-color: #667eea !important;
        color: #ffffff !important;
        width: 100% !important;
    }

    section[data-testid="stSidebar"] p {
        color: #cccccc !important;
    }

    section[data-testid="stSidebar"] small {
        color: #aaaaaa !important;
    }

    section[data-testid="stSidebar"] hr {
        border-color: #2d2d4e !important;
    }

    /* ===== KPI CARDS ===== */

    .kpi-card {
        background-color: #ffffff !important;
        border-radius: 12px;
        padding: 22px 20px;
        border-left: 5px solid #667eea;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        margin-bottom: 12px;
        min-height: 115px;
    }

    .kpi-card-green  { border-left-color: #28a745 !important; }
    .kpi-card-blue   { border-left-color: #17a2b8 !important; }
    .kpi-card-orange { border-left-color: #fd7e14 !important; }
    .kpi-card-purple { border-left-color: #764ba2 !important; }
    .kpi-card-red    { border-left-color: #dc3545 !important; }

    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1a1a2e !important;
        line-height: 1.2;
        margin: 6px 0 4px 0;
    }

    .kpi-label {
        font-size: 0.75rem;
        color: #888888 !important;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        font-weight: 600;
    }

    .kpi-change-pos     { font-size: 0.82rem; color: #28a745 !important; margin-top: 4px; }
    .kpi-change-neg     { font-size: 0.82rem; color: #dc3545 !important; margin-top: 4px; }
    .kpi-change-neutral { font-size: 0.82rem; color: #888888 !important; margin-top: 4px; }

    /* ===== SECTION TITLE ===== */

    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1a1a2e !important;
        border-bottom: 3px solid #667eea;
        padding-bottom: 8px;
        margin: 28px 0 18px 0;
    }

    /* ===== DASHBOARD HEADER ===== */

    .dash-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 14px;
        padding: 32px 36px;
        text-align: center;
        margin-bottom: 24px;
    }

    .dash-header h1 {
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        color: #ffffff !important;
    }

    .dash-header p {
        font-size: 1rem;
        color: rgba(255,255,255,0.85) !important;
        margin: 8px 0 0 0;
    }

    /* ===== ALERT BOXES ===== */

    .alert-success {
        background: #d4edda !important;
        border-left: 4px solid #28a745;
        padding: 13px 16px;
        border-radius: 7px;
        margin: 8px 0;
        font-size: 14px;
        color: #155724 !important;
        line-height: 1.5;
    }

    .alert-danger {
        background: #f8d7da !important;
        border-left: 4px solid #dc3545;
        padding: 13px 16px;
        border-radius: 7px;
        margin: 8px 0;
        font-size: 14px;
        color: #721c24 !important;
        line-height: 1.5;
    }

    .alert-warning {
        background: #fff3cd !important;
        border-left: 4px solid #ffc107;
        padding: 13px 16px;
        border-radius: 7px;
        margin: 8px 0;
        font-size: 14px;
        color: #856404 !important;
        line-height: 1.5;
    }

    .alert-info {
        background: #d1ecf1 !important;
        border-left: 4px solid #17a2b8;
        padding: 13px 16px;
        border-radius: 7px;
        margin: 8px 0;
        font-size: 14px;
        color: #0c5460 !important;
        line-height: 1.5;
    }

    /* ===== FILTER BAR ===== */

    .filter-bar {
        background: #ffffff !important;
        border-radius: 8px;
        padding: 12px 18px;
        border: 1px solid #e0e4ff;
        font-size: 13px;
        color: #444444 !important;
        margin-bottom: 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }

    /* ===== FOOTER ===== */

    .dash-footer {
        text-align: center;
        padding: 24px;
        color: #888888 !important;
        font-size: 13px;
        margin-top: 40px;
        border-top: 1px solid #e0e0e0;
        background-color: #f4f6f9 !important;
    }

    /* ===== PLOTLY CHARTS - force white background ===== */

    .js-plotly-plot .plotly {
        background-color: #ffffff !important;
    }

    .js-plotly-plot .plotly .svg-container {
        background-color: #ffffff !important;
    }

</style>
""", unsafe_allow_html=True)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def fmt_currency(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "$0.00"
    if value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value/1_000:.1f}K"
    return f"${value:,.2f}"


def fmt_number(value):
    if value is None:
        return "0"
    return f"{int(value):,}"


def fmt_percent(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "0.0%"
    return f"{value:.1f}%"


def change_html(value, suffix='%', invert=False):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        value = 0
    is_positive = value >= 0 if not invert else value <= 0
    if value == 0:
        css = "kpi-change-neutral"
        arrow = "→"
        sign = ""
    elif is_positive:
        css = "kpi-change-pos"
        arrow = "↑"
        sign = "+"
    else:
        css = "kpi-change-neg"
        arrow = "↓"
        sign = ""
    return f'<p class="{css}">{arrow} {sign}{abs(value):.1f}{suffix} vs prev period</p>'


def kpi_card(label, value, change=None, color='', suffix='', is_currency=True, invert=False):
    if is_currency:
        display_value = fmt_currency(value)
    elif suffix == '%':
        display_value = fmt_percent(value)
    else:
        display_value = fmt_number(value) + suffix

    change_section = ''
    if change is not None:
        change_section = change_html(change, invert=invert)

    card_class = f"kpi-card {color}"

    st.markdown(f"""
    <div class="{card_class}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{display_value}</div>
        {change_section}
    </div>
    """, unsafe_allow_html=True)


def section_title(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def apply_chart_style(fig, height=420):
    fig.update_layout(
        height = height,
        plot_bgcolor = '#ffffff',
        paper_bgcolor = '#ffffff',
        font = dict(
            family = 'Arial, sans-serif',
            size = 12,
            color = '#1a1a2e',
        ),
        margin = dict(l=10, r=10, t=45, b=10),
        legend = dict(
            orientation = 'h',
            yanchor = 'bottom',
            y = 1.01,
            xanchor = 'right',
            x = 1,
            font = dict(size=11, color='#1a1a2e'),
            bgcolor = 'rgba(255,255,255,0.9)',
            bordercolor = '#eeeeee',
            borderwidth = 1,
        ),
        xaxis = dict(
            showgrid = True,
            gridcolor = 'rgba(0,0,0,0.06)',
            showline = True,
            linecolor = 'rgba(0,0,0,0.15)',
            linewidth = 1,
            tickfont = dict(size=11, color='#444444'),
            title_font = dict(size=12, color='#333333'),
            zeroline = False,
        ),
        yaxis = dict(
            showgrid = True,
            gridcolor = 'rgba(0,0,0,0.06)',
            showline = False,
            tickfont = dict(size=11, color='#444444'),
            title_font = dict(size=12, color='#333333'),
            zeroline = False,
        ),
        title = dict(
            font = dict(size=15, color='#1a1a2e'),
            x = 0,
            xanchor = 'left',
        ),
        hoverlabel = dict(
            bgcolor = '#1a1a2e',
            font_size = 12,
            font_color = '#ffffff',
            bordercolor = '#667eea',
        ),
    )
    return fig


# ==========================================
# DATA LOADING
# ==========================================

@st.cache_data(ttl=DASHBOARD_CONFIG['cache_ttl'])
def load_all_data():
    filepath = 'data/processed/sales_completed.csv'
    if not os.path.exists(filepath):
        return None

    df          = load_data(filepath)
    df          = add_time_features(df)
    return df


@st.cache_data(ttl=DASHBOARD_CONFIG['cache_ttl'])
def load_all_orders():
    filepath = 'data/processed/sales_all.csv'
    if not os.path.exists(filepath):
        return None
    df          = pd.read_csv(filepath)
    df['date']  = pd.to_datetime(df['date'])
    return df


# ==========================================
# SIDEBAR
# ==========================================

def render_sidebar(df):

    with st.sidebar:

        st.markdown("""
        <div style="text-align:center;padding:20px 0 10px 0;">
            <div style="font-size:40px;">📊</div>
            <div style="color:white;font-size:18px;font-weight:700;margin-top:6px;">
                Sales Tracker
            </div>
            <div style="color:#aaa;font-size:12px;">v1.0.0</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<hr style="border-color:#333;margin:10px 0 20px 0;">', unsafe_allow_html=True)

        st.markdown('<p style="color:#aaa;font-size:12px;text-transform:uppercase;letter-spacing:1px;">📅 Date Range</p>', unsafe_allow_html=True)

        period_options = [
            'Today',
            'Yesterday',
            'Last 7 Days',
            'Last 30 Days',
            'Last 90 Days',
            'Last 365 Days',
            'This Month',
            'This Year',
            'All Time',
            'Custom Range',
        ]

        selected_period = st.selectbox(
            'Select Period',
            options     = period_options,
            index       = 3,
            label_visibility = 'collapsed',
        )

        start_date  = None
        end_date    = None

        if selected_period == 'Custom Range':
            st.markdown('<p style="color:#aaa;font-size:12px;margin-top:8px;">Start Date</p>', unsafe_allow_html=True)
            start_date = st.date_input('Start', df['date'].min().date(), label_visibility='collapsed')
            st.markdown('<p style="color:#aaa;font-size:12px;margin-top:4px;">End Date</p>', unsafe_allow_html=True)
            end_date   = st.date_input('End', df['date'].max().date(), label_visibility='collapsed')

        st.markdown('<hr style="border-color:#333;margin:18px 0;">', unsafe_allow_html=True)
        st.markdown('<p style="color:#aaa;font-size:12px;text-transform:uppercase;letter-spacing:1px;">🏷️ Category</p>', unsafe_allow_html=True)

        categories = ['All Categories'] + sorted(df['category'].dropna().unique().tolist())
        selected_cat = st.selectbox('Category', categories, label_visibility='collapsed')

        st.markdown('<hr style="border-color:#333;margin:18px 0;">', unsafe_allow_html=True)
        st.markdown('<p style="color:#aaa;font-size:12px;text-transform:uppercase;letter-spacing:1px;">📢 Sales Channel</p>', unsafe_allow_html=True)

        channels        = ['All Channels'] + sorted(df['channel'].dropna().unique().tolist())
        selected_chan   = st.selectbox('Channel', channels, label_visibility='collapsed')

        st.markdown('<hr style="border-color:#333;margin:18px 0;">', unsafe_allow_html=True)
        st.markdown('<p style="color:#aaa;font-size:12px;text-transform:uppercase;letter-spacing:1px;">🌍 Region</p>', unsafe_allow_html=True)

        regions         = ['All Regions'] + sorted(df['region'].dropna().unique().tolist())
        selected_region = st.selectbox('Region', regions, label_visibility='collapsed')

        st.markdown('<hr style="border-color:#333;margin:18px 0;">', unsafe_allow_html=True)
        st.markdown('<p style="color:#aaa;font-size:12px;text-transform:uppercase;letter-spacing:1px;">👥 Customer Type</p>', unsafe_allow_html=True)

        cust_types          = ['All Customers', 'New', 'Returning']
        selected_cust_type  = st.selectbox('Customer Type', cust_types, label_visibility='collapsed')

        st.markdown('<hr style="border-color:#333;margin:18px 0;">', unsafe_allow_html=True)

        if st.button('🔄 Refresh Data', use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown(f"""
        <div style="text-align:center;margin-top:20px;">
            <p style="color:#555;font-size:11px;">
                Last updated<br>
                {datetime.now().strftime('%b %d, %Y %I:%M %p')}
            </p>
        </div>
        """, unsafe_allow_html=True)

    return selected_period, selected_cat, selected_chan, selected_region, selected_cust_type, start_date, end_date


# ==========================================
# FILTER DATA
# ==========================================

def filter_data(df, selected_period, selected_cat, selected_chan, selected_region, selected_cust_type, start_date, end_date):

    today = pd.Timestamp.now().normalize()

    if selected_period == 'Today':
        df = df[df['date'] == today]
    elif selected_period == 'Yesterday':
        df = df[df['date'] == today - pd.Timedelta(days=1)]
    elif selected_period == 'Last 7 Days':
        df = df[df['date'] >= today - pd.Timedelta(days=7)]
    elif selected_period == 'Last 30 Days':
        df = df[df['date'] >= today - pd.Timedelta(days=30)]
    elif selected_period == 'Last 90 Days':
        df = df[df['date'] >= today - pd.Timedelta(days=90)]
    elif selected_period == 'Last 365 Days':
        df = df[df['date'] >= today - pd.Timedelta(days=365)]
    elif selected_period == 'This Month':
        df = df[df['date'] >= today.replace(day=1)]
    elif selected_period == 'This Year':
        df = df[df['year'] == today.year]
    elif selected_period == 'Custom Range':
        if start_date and end_date:
            df = df[
                (df['date'].dt.date >= start_date) &
                (df['date'].dt.date <= end_date)
            ]

    if selected_cat != 'All Categories':
        df = df[df['category'] == selected_cat]

    if selected_chan != 'All Channels':
        df = df[df['channel'] == selected_chan]

    if selected_region != 'All Regions':
        df = df[df['region'] == selected_region]

    if selected_cust_type != 'All Customers':
        df = df[df['customer_type'] == selected_cust_type]

    return df


def get_previous_period_data(df_full, selected_period, start_date, end_date):

    today = pd.Timestamp.now().normalize()

    if selected_period == 'Today':
        return df_full[df_full['date'] == today - pd.Timedelta(days=1)]
    elif selected_period == 'Yesterday':
        return df_full[df_full['date'] == today - pd.Timedelta(days=2)]
    elif selected_period == 'Last 7 Days':
        s = today - pd.Timedelta(days=14)
        e = today - pd.Timedelta(days=8)
        return df_full[(df_full['date'] >= s) & (df_full['date'] <= e)]
    elif selected_period == 'Last 30 Days':
        s = today - pd.Timedelta(days=60)
        e = today - pd.Timedelta(days=31)
        return df_full[(df_full['date'] >= s) & (df_full['date'] <= e)]
    elif selected_period == 'Last 90 Days':
        s = today - pd.Timedelta(days=180)
        e = today - pd.Timedelta(days=91)
        return df_full[(df_full['date'] >= s) & (df_full['date'] <= e)]
    elif selected_period == 'Last 365 Days':
        s = today - pd.Timedelta(days=730)
        e = today - pd.Timedelta(days=366)
        return df_full[(df_full['date'] >= s) & (df_full['date'] <= e)]
    elif selected_period == 'This Month':
        first_this  = today.replace(day=1)
        last_month  = first_this - pd.Timedelta(days=1)
        first_last  = last_month.replace(day=1)
        return df_full[(df_full['date'] >= first_last) & (df_full['date'] <= last_month)]
    elif selected_period == 'This Year':
        return df_full[df_full['year'] == today.year - 1]
    elif selected_period == 'Custom Range' and start_date and end_date:
        delta       = (end_date - start_date).days + 1
        prev_end    = start_date - timedelta(days=1)
        prev_start  = prev_end - timedelta(days=delta - 1)
        return df_full[
            (df_full['date'].dt.date >= prev_start) &
            (df_full['date'].dt.date <= prev_end)
        ]

    return pd.DataFrame()


# ==========================================
# TAB 1: OVERVIEW
# ==========================================

def render_overview_tab(df, df_prev):

    # KPI metrics
    metrics = calculate_revenue_metrics(df, df_prev if len(df_prev) > 0 else None)

    section_title("📈 Key Performance Indicators")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card(
            label = "💰 Total Revenue",
            value = metrics['total_revenue'],
            change = metrics.get('revenue_growth'),
            is_currency = True,
        )

    with c2:
        kpi_card(
            label = "🛒 Total Orders",
            value = metrics['total_orders'],
            change = metrics.get('orders_growth'),
            is_currency = False,
            color = 'kpi-card-purple',
        )

    with c3:
        kpi_card(
            label = "💎 Total Profit",
            value = metrics['total_profit'],
            change = metrics.get('profit_growth'),
            is_currency = True,
            color = 'kpi-card-green',
        )

    with c4:
        kpi_card(
            label = "🎯 Avg Order Value",
            value = metrics['avg_order_value'],
            is_currency = True,
            color = 'kpi-card-blue',
        )

    c5, c6, c7, c8 = st.columns(4)

    with c5:
        kpi_card(
            label = "👥 Unique Customers",
            value = metrics['unique_customers'],
            is_currency = False,
            color = 'kpi-card-orange',
        )

    with c6:
        kpi_card(
            label = "📦 Units Sold",
            value = metrics['total_units_sold'],
            is_currency = False,
            color = 'kpi-card-purple',
        )

    with c7:
        kpi_card(
            label = "📊 Profit Margin",
            value = metrics['avg_profit_margin'],
            is_currency = False,
            suffix = '%',
            color = 'kpi-card-green',
        )

    with c8:
        kpi_card(
            label = "🔄 Return Rate",
            value = metrics['returning_rate'],
            is_currency = False,
            suffix = '%',
            color = 'kpi-card-blue',
        )

    # Alerts
    alerts = DASHBOARD_CONFIG['alerts']

    if len(df) > 0:
        daily_rev = metrics['total_revenue'] / max(df['date'].nunique(), 1)
        margin = metrics['avg_profit_margin']

        if daily_rev < alerts['min_daily_revenue']:
            st.markdown(f'<div class="alert-danger">⚠️ Daily revenue (${daily_rev:,.0f}) is below the minimum threshold of ${alerts["min_daily_revenue"]:,}. Consider running a promotion.</div>', unsafe_allow_html=True)

        if margin < alerts['min_profit_margin']:
            st.markdown(f'<div class="alert-warning">⚠️ Profit margin ({margin:.1f}%) is below target of {alerts["min_profit_margin"]}%. Review pricing or reduce costs.</div>', unsafe_allow_html=True)

    # Revenue trend
    section_title("📉 Revenue Trend")

    daily_sales = calculate_daily_sales(df)

    if len(daily_sales) > 0:
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x = daily_sales['date'],
            y = daily_sales['revenue'],
            name = 'Daily Revenue',
            marker_color = 'rgba(102, 126, 234, 0.65)',
            hovertemplate = '<b>%{x|%b %d, %Y}</b><br>Revenue: $%{y:,.2f}<extra></extra>',
        ))

        fig.add_trace(go.Scatter(
            x = daily_sales['date'],
            y = daily_sales['revenue_7day_avg'],
            name = '7-Day Avg',
            mode = 'lines',
            line = dict(color='#764ba2', width=2.5),
            hovertemplate = '<b>%{x|%b %d, %Y}</b><br>7-Day Avg: $%{y:,.2f}<extra></extra>',
        ))

        fig = apply_chart_style(fig, height=380)
        fig.update_layout(
            title       = '📊 Daily Revenue with 7-Day Moving Average',
            hovermode   = 'x unified',
            yaxis       = dict(tickprefix='$', showgrid=True, gridcolor='rgba(0,0,0,0.04)'),
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No data available for the selected period.")

    # Cumulative revenue
    if len(daily_sales) > 1:
        section_title("📈 Cumulative Revenue Growth")

        fig_cum = go.Figure()

        fig_cum.add_trace(go.Scatter(
            x = daily_sales['date'],
            y = daily_sales['revenue_cumulative'],
            name = 'Cumulative Revenue',
            mode = 'lines',
            fill = 'tozeroy',
            fillcolor = 'rgba(102, 126, 234, 0.12)',
            line = dict(color='#667eea', width=2.5),
            hovertemplate = '<b>%{x|%b %d, %Y}</b><br>Cumulative: $%{y:,.2f}<extra></extra>',
        ))

        fig_cum = apply_chart_style(fig_cum, height=300)
        fig_cum.update_layout(
            title   = 'Cumulative Revenue Over Selected Period',
            yaxis   = dict(tickprefix='$', showgrid=True, gridcolor='rgba(0,0,0,0.04)'),
        )

        st.plotly_chart(fig_cum, use_container_width=True)

    # Monthly summary table
    if len(df) > 0:
        section_title("📅 Monthly Summary")

        monthly = calculate_monthly_sales(df)

        if len(monthly) > 0:
            display_monthly = monthly.copy()
            display_monthly['revenue'] = display_monthly['revenue'].apply(fmt_currency)
            display_monthly['profit'] = display_monthly['profit'].apply(fmt_currency)
            display_monthly['avg_order_value'] = display_monthly['avg_order_value'].apply(fmt_currency)
            display_monthly['revenue_mom_growth'] = display_monthly['revenue_mom_growth'].apply(
                lambda x: f"+{x:.1f}%" if x > 0 else f"{x:.1f}%" if not np.isnan(x) else "—"
            )

            display_monthly.columns = [
                'Month', 'Revenue', 'Orders', 'Profit',
                'Customers', 'Units Sold', 'Revenue MoM %', 'Orders MoM %', 'Avg Order Value'
            ]

            st.dataframe(
                display_monthly.sort_values('Month', ascending=False),
                use_container_width = True,
                hide_index = True,
            )


# ==========================================
# TAB 2: PRODUCTS
# ==========================================

def render_products_tab(df):

    section_title("🏆 Product Performance")

    if len(df) == 0:
        st.info("No product data for the selected filters.")
        return

    products = calculate_product_performance(df)
    categories = calculate_category_performance(df)

    col_l, col_r = st.columns(2)

    with col_l:
        top_n = st.slider("Show top N products", 5, 16, 10, key='prod_slider')
        top_prods = products.head(top_n)

        fig = px.bar(
            top_prods.sort_values('total_revenue'),
            x = 'total_revenue',
            y = 'product_name',
            orientation = 'h',
            color = 'total_revenue',
            color_continuous_scale = 'Viridis',
            labels = {'total_revenue': 'Revenue ($)', 'product_name': 'Product'},
            title = f'Top {top_n} Products by Revenue',
            text = top_prods.sort_values('total_revenue')['total_revenue'].apply(fmt_currency),
        )

        fig.update_traces(textposition='outside', textfont_size=10)
        fig = apply_chart_style(fig, height=420)
        fig.update_layout(
            coloraxis_showscale = False,
            yaxis_title = '',
            xaxis = dict(
                showgrid = True,
                gridcolor = 'rgba(0,0,0,0.04)',
            ),
            margin = dict(l=10, r=120, t=45, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        fig_pie = px.pie(
            categories,
            values  = 'total_revenue',
            names   = 'category',
            hole    = 0.42,
            title   = 'Revenue Share by Category',
            color_discrete_sequence = DASHBOARD_CONFIG['chart_palette'],
        )

        fig_pie.update_traces(
            textposition    = 'inside',
            textinfo        = 'percent+label',
            hovertemplate   = '<b>%{label}</b><br>Revenue: $%{value:,.2f}<br>Share: %{percent}<extra></extra>',
        )

        fig_pie.update_layout(
            height = 420,
            paper_bgcolor = '#ffffff',
            plot_bgcolor = '#ffffff',
            font = dict(color='#1a1a2e'),
            showlegend = True,
            legend = dict(orientation='v', x=1.02),
            margin = dict(l=10, r=10, t=40, b=10),
        )

        st.plotly_chart(fig_pie, use_container_width=True)

    # Profit margin by product
    section_title("💎 Profit Margin by Product")

    top_margin = products.head(12).sort_values('avg_margin', ascending=True)

    colors = ['#dc3545' if m < 20 else '#28a745' for m in top_margin['avg_margin']]

    fig_margin = go.Figure(go.Bar(
        x               = top_margin['avg_margin'],
        y               = top_margin['product_name'],
        orientation     = 'h',
        marker_color    = colors,
        text            = top_margin['avg_margin'].apply(lambda x: f"{x:.1f}%"),
        textposition    = 'outside',
        hovertemplate   = '<b>%{y}</b><br>Margin: %{x:.1f}%<extra></extra>',
    ))

    fig_margin.add_vline(
        x               = 20,
        line_dash       = 'dash',
        line_color      = '#ffc107',
        annotation_text = 'Target 20%',
        annotation_font = dict(color='#ffc107', size=11),
    )

    fig_margin = apply_chart_style(fig_margin, height=380)
    fig_margin.update_layout(
        title       = 'Profit Margin by Product (Red = Below 20% target)',
        xaxis       = dict(ticksuffix='%'),
        yaxis_title = '',
    )

    st.plotly_chart(fig_margin, use_container_width=True)

    # Category detail table
    section_title("📋 Category Detail")

    cat_display = categories.copy()
    cat_display['total_revenue']    = cat_display['total_revenue'].apply(fmt_currency)
    cat_display['total_profit']     = cat_display['total_profit'].apply(fmt_currency)
    cat_display['avg_margin']       = cat_display['avg_margin'].apply(fmt_percent)
    cat_display['avg_order_value']  = cat_display['avg_order_value'].apply(fmt_currency)
    cat_display['revenue_share']    = cat_display['revenue_share'].apply(fmt_percent)

    cat_display.columns = [
        'Category', 'Revenue', 'Units', 'Orders',
        'Profit', 'Margin', 'Products', 'Avg Order', 'Revenue Share'
    ]

    st.dataframe(cat_display, use_container_width=True, hide_index=True)

    # Full product table
    section_title("📦 All Products Detail")

    prod_display = products.copy()
    prod_display['total_revenue'] = prod_display['total_revenue'].apply(fmt_currency)
    prod_display['total_profit'] = prod_display['total_profit'].apply(fmt_currency)
    prod_display['avg_order_value'] = prod_display['avg_order_value'].apply(fmt_currency)
    prod_display['avg_margin'] = prod_display['avg_margin'].apply(fmt_percent)
    prod_display['revenue_share'] = prod_display['revenue_share'].apply(fmt_percent)

    cols_to_show = ['rank', 'product_name', 'category', 'total_revenue',
                    'total_orders', 'total_units', 'avg_order_value',
                    'total_profit', 'avg_margin', 'revenue_share']

    prod_display = prod_display[[c for c in cols_to_show if c in prod_display.columns]]
    prod_display.columns = [c.replace('_', ' ').title() for c in prod_display.columns]

    st.dataframe(prod_display, use_container_width=True, hide_index=True)


# ==========================================
# TAB 3: CUSTOMERS
# ==========================================

def render_customers_tab(df):

    section_title("👥 Customer Analytics")

    if len(df) == 0:
        st.info("No customer data for the selected filters.")
        return

    metrics         = calculate_revenue_metrics(df)
    cust_types      = calculate_customer_type_breakdown(df)
    top_customers   = calculate_top_customers(df, top_n=10)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card("👥 Unique Customers",      metrics['unique_customers'],     is_currency=False)
    with c2:
        kpi_card("🆕 New Customers",         metrics['new_customers'],        is_currency=False, color='kpi-card-green')
    with c3:
        kpi_card("🔄 Returning Customers",   metrics['returning_customers'],  is_currency=False, color='kpi-card-blue')
    with c4:
        kpi_card("💰 Revenue per Customer",  metrics['revenue_per_customer'], is_currency=True,  color='kpi-card-purple')

    col_l, col_r = st.columns(2)

    with col_l:
        if len(cust_types) > 0:
            fig = px.pie(
                cust_types,
                values = 'total_revenue',
                names = 'customer_type',
                hole = 0.4,
                title = 'Revenue: New vs Returning Customers',
                color_discrete_sequence = ['#667eea', '#28a745'],
            )
            fig.update_traces(
                textposition = 'inside',
                textinfo = 'percent+label',
                hovertemplate = '<b>%{label}</b><br>Revenue: $%{value:,.2f}<br>%{percent}<extra></extra>',
            )
            fig.update_layout(
                height = 380,
                paper_bgcolor = '#ffffff',
                plot_bgcolor = '#ffffff',
                font = dict(color='#1a1a2e', size=12),
                margin = dict(l=10, r=10, t=40, b=10),
                legend = dict(font=dict(color='#1a1a2e')),
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        if len(cust_types) > 0:
            fig2 = px.bar(
                cust_types,
                x               = 'customer_type',
                y               = 'avg_order_value',
                color           = 'customer_type',
                title           = 'Avg Order Value: New vs Returning',
                color_discrete_sequence = ['#667eea', '#28a745'],
                labels          = {'avg_order_value': 'Avg Order Value ($)', 'customer_type': 'Customer Type'},
                text            = cust_types['avg_order_value'].apply(fmt_currency),
            )
            fig2.update_traces(textposition='outside')
            fig2 = apply_chart_style(fig2, height=380)
            fig2.update_layout(yaxis=dict(tickprefix='$'), showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

    # Daily new vs returning
    section_title("📅 New vs Returning Customers Over Time")

    if 'customer_type' in df.columns:
        daily_cust = df.groupby(['date', 'customer_type']).agg(
            orders=('order_id', 'count')
        ).reset_index()

        fig3 = px.line(
            daily_cust,
            x               = 'date',
            y               = 'orders',
            color           = 'customer_type',
            title           = 'Daily Orders by Customer Type',
            color_discrete_sequence = ['#667eea', '#28a745'],
            labels          = {'orders': 'Number of Orders', 'date': 'Date', 'customer_type': 'Type'},
        )

        fig3.update_traces(mode='lines', line=dict(width=2))
        fig3 = apply_chart_style(fig3, height=340)
        st.plotly_chart(fig3, use_container_width=True)

    # Top customers table
    section_title("🏆 Top 10 Customers by Revenue")

    if len(top_customers) > 0:
        tc_display = top_customers.copy()
        tc_display['total_revenue']     = tc_display['total_revenue'].apply(fmt_currency)
        tc_display['avg_order_value']   = tc_display['avg_order_value'].apply(fmt_currency)
        tc_display['total_profit']      = tc_display['total_profit'].apply(fmt_currency)

        cols = ['rank', 'customer_name', 'customer_type', 'total_orders',
                'total_revenue', 'avg_order_value', 'total_profit']

        tc_display = tc_display[[c for c in cols if c in tc_display.columns]]
        tc_display.columns = [c.replace('_', ' ').title() for c in tc_display.columns]

        st.dataframe(tc_display, use_container_width=True, hide_index=True)

    # Payment method breakdown
    section_title("💳 Payment Method Breakdown")

    pay_data = calculate_payment_method_breakdown(df)

    if len(pay_data) > 0:
        col_a, col_b = st.columns(2)

        with col_a:
            fig_pay = px.bar(
                pay_data.sort_values('total_revenue', ascending=True),
                x               = 'total_revenue',
                y               = 'payment_method',
                orientation     = 'h',
                color           = 'total_revenue',
                color_continuous_scale = 'Blues',
                title           = 'Revenue by Payment Method',
                text            = pay_data.sort_values('total_revenue')['total_revenue'].apply(fmt_currency),
            )
            fig_pay.update_traces(textposition='outside')
            fig_pay = apply_chart_style(fig_pay, height=320)
            fig_pay.update_layout(coloraxis_showscale=False, xaxis=dict(tickprefix='$'), yaxis_title='')
            st.plotly_chart(fig_pay, use_container_width=True)

        with col_b:
            fig_pay2 = px.pie(
                pay_data,
                values  = 'total_orders',
                names   = 'payment_method',
                hole    = 0.4,
                title   = 'Orders by Payment Method',
                color_discrete_sequence = DASHBOARD_CONFIG['chart_palette'],
            )
            fig_pay2.update_traces(textposition='inside', textinfo='percent+label')
            fig_pay2.update_layout(height=320, paper_bgcolor='#ffffff', margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_pay2, use_container_width=True)


# ==========================================
# TAB 4: CHANNELS & GEOGRAPHY
# ==========================================

def render_channels_tab(df):

    section_title("📢 Sales Channel Performance")

    if len(df) == 0:
        st.info("No channel data for the selected filters.")
        return

    channels = calculate_channel_performance(df)
    geo      = calculate_geographic_performance(df)
    regional = calculate_regional_performance(df)

    col_l, col_r = st.columns(2)

    with col_l:
        fig = px.bar(
            channels.sort_values('total_revenue', ascending=True),
            x = 'total_revenue',
            y = 'channel',
            orientation = 'h',
            color = 'total_revenue',
            color_continuous_scale = 'Purples',
            title = 'Revenue by Sales Channel',
            labels = {'total_revenue': 'Revenue ($)', 'channel': ''},
            text = channels.sort_values('total_revenue')['total_revenue'].apply(fmt_currency),
        )
        fig.update_traces(textposition='outside')
        fig = apply_chart_style(fig, height=360)
        fig.update_layout(coloraxis_showscale=False, xaxis=dict(tickprefix='$'), yaxis_title='')
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        fig2 = px.bar(
            channels.sort_values('profit_margin', ascending=True),
            x               = 'profit_margin',
            y               = 'channel',
            orientation     = 'h',
            color           = 'profit_margin',
            color_continuous_scale = 'RdYlGn',
            title           = 'Profit Margin by Channel (%)',
            labels          = {'profit_margin': 'Profit Margin (%)', 'channel': ''},
            text            = channels.sort_values('profit_margin')['profit_margin'].apply(fmt_percent),
        )
        fig2.update_traces(textposition='outside')
        fig2 = apply_chart_style(fig2, height=360)
        fig2.update_layout(coloraxis_showscale=False, xaxis=dict(ticksuffix='%'), yaxis_title='')
        st.plotly_chart(fig2, use_container_width=True)

    # Orders by channel pie
    col_a, col_b = st.columns(2)

    with col_a:
        fig3 = px.pie(
            channels,
            values  = 'total_orders',
            names   = 'channel',
            hole    = 0.4,
            title   = 'Order Share by Channel',
            color_discrete_sequence = DASHBOARD_CONFIG['chart_palette'],
        )
        fig3.update_traces(textposition='inside', textinfo='percent+label')
        fig3.update_layout(height=340, paper_bgcolor='#ffffff', margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig3, use_container_width=True)

    with col_b:
        fig4 = px.bar(
            channels,
            x               = 'channel',
            y               = 'avg_order_value',
            color           = 'channel',
            title           = 'Avg Order Value by Channel',
            color_discrete_sequence = DASHBOARD_CONFIG['chart_palette'],
            text            = channels['avg_order_value'].apply(fmt_currency),
        )
        fig4.update_traces(textposition='outside')
        fig4 = apply_chart_style(fig4, height=340)
        fig4.update_layout(showlegend=False, yaxis=dict(tickprefix='$'), xaxis_title='')
        st.plotly_chart(fig4, use_container_width=True)

    # Channel table
    section_title("📋 Channel Detail Table")

    ch_display = channels.copy()
    ch_display['total_revenue']     = ch_display['total_revenue'].apply(fmt_currency)
    ch_display['total_profit']      = ch_display['total_profit'].apply(fmt_currency)
    ch_display['avg_order_value']   = ch_display['avg_order_value'].apply(fmt_currency)
    ch_display['revenue_share']     = ch_display['revenue_share'].apply(fmt_percent)
    ch_display['profit_margin']     = ch_display['profit_margin'].apply(fmt_percent)

    ch_display.columns = ['Channel', 'Revenue', 'Orders', 'Profit',
                          'Avg Order', 'Units', 'Customers', 'Share', 'Margin']

    st.dataframe(ch_display, use_container_width=True, hide_index=True)

    # Geography
    section_title("🌍 Geographic Performance")

    col_1, col_2 = st.columns(2)

    with col_1:
        fig_reg = px.pie(
            regional,
            values  = 'total_revenue',
            names   = 'region',
            hole    = 0.4,
            title   = 'Revenue by Region',
            color_discrete_sequence = DASHBOARD_CONFIG['chart_palette'],
        )
        fig_reg.update_traces(textposition='inside', textinfo='percent+label')
        fig_reg.update_layout(height=360, paper_bgcolor='#ffffff', margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_reg, use_container_width=True)

    with col_2:
        fig_city = px.bar(
            geo.head(10).sort_values('total_revenue'),
            x               = 'total_revenue',
            y               = 'city',
            orientation     = 'h',
            color           = 'total_revenue',
            color_continuous_scale = 'Teal',
            title           = 'Top 10 Cities by Revenue',
            text            = geo.head(10).sort_values('total_revenue')['total_revenue'].apply(fmt_currency),
        )
        fig_city.update_traces(textposition='outside')
        fig_city = apply_chart_style(fig_city, height=360)
        fig_city.update_layout(coloraxis_showscale=False, xaxis=dict(tickprefix='$'), yaxis_title='')
        st.plotly_chart(fig_city, use_container_width=True)

    # Geo table
    section_title("🏙️ City Performance Table")

    geo_display = geo.copy()
    geo_display['total_revenue']    = geo_display['total_revenue'].apply(fmt_currency)
    geo_display['total_profit']     = geo_display['total_profit'].apply(fmt_currency)
    geo_display['avg_order_value']  = geo_display['avg_order_value'].apply(fmt_currency)

    geo_display.columns = ['City', 'State', 'Region', 'Revenue', 'Orders', 'Customers', 'Avg Order', 'Profit']
    st.dataframe(geo_display, use_container_width=True, hide_index=True)


# ==========================================
# TAB 5: TIME PATTERNS
# ==========================================

def render_patterns_tab(df):

    section_title("⏰ Sales Patterns & Trends")

    if len(df) == 0:
        st.info("No data available for the selected filters.")
        return

    hourly, daily_pattern = calculate_hourly_patterns(df)

    col_l, col_r = st.columns(2)

    with col_l:
        if len(hourly) > 0:
            fig = px.line(
                hourly,
                x               = 'hour',
                y               = 'orders',
                title           = 'Orders by Hour of Day',
                markers         = True,
                labels          = {'hour': 'Hour (24H)', 'orders': 'Orders'},
            )
            fig.update_traces(line=dict(color='#667eea', width=2.5), marker=dict(size=7, color='#764ba2'))
            fig = apply_chart_style(fig, height=360)
            fig.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=2))
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        if len(hourly) > 0:
            fig2 = px.bar(
                hourly,
                x               = 'hour',
                y               = 'revenue',
                title           = 'Revenue by Hour of Day',
                color           = 'revenue',
                color_continuous_scale = 'Blues',
                labels          = {'hour': 'Hour (24H)', 'revenue': 'Revenue ($)'},
            )
            fig2 = apply_chart_style(fig2, height=360)
            fig2.update_layout(
                coloraxis_showscale = False,
                xaxis               = dict(tickmode='linear', tick0=0, dtick=2),
                yaxis               = dict(tickprefix='$'),
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Day of week patterns
    section_title("📅 Day of Week Patterns")

    col_a, col_b = st.columns(2)

    with col_a:
        if len(daily_pattern) > 0:
            fig3 = px.bar(
                daily_pattern,
                x               = 'day_name',
                y               = 'orders',
                title           = 'Orders by Day of Week',
                color           = 'orders',
                color_continuous_scale = 'Viridis',
                labels          = {'day_name': 'Day', 'orders': 'Orders'},
            )
            fig3 = apply_chart_style(fig3, height=320)
            fig3.update_layout(coloraxis_showscale=False, xaxis_title='')
            st.plotly_chart(fig3, use_container_width=True)

    with col_b:
        if len(daily_pattern) > 0:
            fig4 = px.bar(
                daily_pattern,
                x               = 'day_name',
                y               = 'revenue',
                title           = 'Revenue by Day of Week',
                color           = 'revenue',
                color_continuous_scale = 'Purples',
                labels          = {'day_name': 'Day', 'revenue': 'Revenue ($)'},
            )
            fig4 = apply_chart_style(fig4, height=320)
            fig4.update_layout(coloraxis_showscale=False, xaxis_title='', yaxis=dict(tickprefix='$'))
            st.plotly_chart(fig4, use_container_width=True)

    # Heatmap orders by day and hour
    section_title("🔥 Sales Heatmap — Day vs Hour")

    if 'hour' in df.columns and 'day_name' in df.columns:
        heatmap_data = df.groupby(['day_name', 'hour']).agg(
            orders=('order_id', 'count')
        ).reset_index()

        heatmap_pivot = heatmap_data.pivot(
            index   = 'day_name',
            columns = 'hour',
            values  = 'orders'
        ).fillna(0)

        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_pivot = heatmap_pivot.reindex(
            [d for d in day_order if d in heatmap_pivot.index]
        )

        fig_heat = px.imshow(
            heatmap_pivot,
            color_continuous_scale  = 'Blues',
            title                   = 'Number of Orders by Day and Hour',
            labels                  = dict(x='Hour of Day', y='Day of Week', color='Orders'),
            aspect                  = 'auto',
        )

        fig_heat.update_layout(
            height          = 380,
            paper_bgcolor   = '#ffffff',
            plot_bgcolor    = 'white',
            margin          = dict(l=10, r=10, t=40, b=10),
            xaxis           = dict(tickmode='linear', tick0=0, dtick=2),
        )

        st.plotly_chart(fig_heat, use_container_width=True)

    # Monthly revenue bar
    section_title("📆 Monthly Revenue Comparison")

    if 'year_month' in df.columns:
        monthly = calculate_monthly_sales(df)

        if len(monthly) > 0:
            fig_mon = go.Figure()

            fig_mon.add_trace(go.Bar(
                x               = monthly['year_month'],
                y               = monthly['revenue'],
                name            = 'Revenue',
                marker_color    = '#667eea',
                hovertemplate   = '<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>',
            ))

            fig_mon.add_trace(go.Scatter(
                x               = monthly['year_month'],
                y               = monthly['profit'],
                name            = 'Profit',
                mode            = 'lines+markers',
                line            = dict(color='#28a745', width=2.5),
                marker          = dict(size=7),
                yaxis           = 'y',
                hovertemplate   = '<b>%{x}</b><br>Profit: $%{y:,.2f}<extra></extra>',
            ))

            fig_mon = apply_chart_style(fig_mon, height=360)
            fig_mon.update_layout(
                title       = 'Monthly Revenue and Profit',
                hovermode   = 'x unified',
                yaxis       = dict(tickprefix='$'),
            )

            st.plotly_chart(fig_mon, use_container_width=True)

    # Seasonal analysis
    if 'season' in df.columns:
        section_title("🌸 Seasonal Analysis")

        seasonal = df.groupby('season').agg(
            revenue=('revenue', 'sum'),
            orders=('order_id', 'count'),
            profit=('profit', 'sum'),
        ).reset_index()

        season_order = ['Spring', 'Summer', 'Fall', 'Winter']
        seasonal['season'] = pd.Categorical(seasonal['season'], categories=season_order, ordered=True)
        seasonal = seasonal.sort_values('season')

        col_x, col_y = st.columns(2)

        with col_x:
            fig_sea = px.bar(
                seasonal,
                x               = 'season',
                y               = 'revenue',
                color           = 'season',
                title           = 'Revenue by Season',
                color_discrete_sequence = ['#28a745', '#ffc107', '#fd7e14', '#17a2b8'],
                text            = seasonal['revenue'].apply(fmt_currency),
            )
            fig_sea.update_traces(textposition='outside')
            fig_sea = apply_chart_style(fig_sea, height=320)
            fig_sea.update_layout(showlegend=False, yaxis=dict(tickprefix='$'), xaxis_title='')
            st.plotly_chart(fig_sea, use_container_width=True)

        with col_y:
            fig_sea2 = px.bar(
                seasonal,
                x               = 'season',
                y               = 'orders',
                color           = 'season',
                title           = 'Orders by Season',
                color_discrete_sequence = ['#28a745', '#ffc107', '#fd7e14', '#17a2b8'],
                text            = seasonal['orders'].apply(fmt_number),
            )
            fig_sea2.update_traces(textposition='outside')
            fig_sea2 = apply_chart_style(fig_sea2, height=320)
            fig_sea2.update_layout(showlegend=False, xaxis_title='')
            st.plotly_chart(fig_sea2, use_container_width=True)


# ==========================================
# TAB 6: FORECASTING
# ==========================================

def render_forecast_tab(df):

    section_title("🔮 Sales Forecasting")

    st.markdown("""
    <div class="alert-info">
        📌 <strong>About this forecast:</strong> Uses Facebook Prophet (or linear regression as fallback)
        to predict future sales based on historical patterns, weekly seasonality, and trend analysis.
        Shaded area shows the confidence band — actual results will likely fall within this range.
    </div>
    """, unsafe_allow_html=True)

    if len(df) == 0:
        st.warning("Not enough data for forecasting. Select a wider date range.")
        return

    col_l, col_r = st.columns([1, 3])

    with col_l:
        metric_choice = st.selectbox(
            "What to Forecast",
            options = ['revenue', 'orders', 'profit', 'units'],
            index   = 0,
            format_func = lambda x: {
                'revenue':  '💰 Revenue',
                'orders':   '🛒 Orders',
                'profit':   '💎 Profit',
                'units':    '📦 Units Sold',
            }.get(x, x)
        )

        forecast_days = st.slider(
            "Forecast Days",
            min_value   = 7,
            max_value   = 90,
            value       = 30,
            step        = 7,
            help        = "How many days into the future to forecast"
        )

        run_btn = st.button("🚀 Run Forecast", use_container_width=True, type='primary')

    with col_r:
        if run_btn or st.session_state.get('forecast_ran', False):
            st.session_state['forecast_ran'] = True

            with st.spinner("Running forecast model... This may take 20-30 seconds."):
                result = run_full_forecast(df, metric=metric_choice, forecast_days=forecast_days)

            if result['success']:

                fm = result['metrics']
                is_currency = metric_choice in ['revenue', 'profit']

                m1, m2, m3, m4 = st.columns([1.2, 1, 1, 1.2])

                with m1:
                    kpi_card(
                        label = f"📊 Predicted Total ({forecast_days}d)",
                        value = fm['total_predicted'],
                        is_currency = is_currency,
                    )
                with m2:
                    kpi_card(
                        label       = "📅 Daily Average",
                        value       = fm['daily_avg_predicted'],
                        is_currency = is_currency,
                        color       = 'kpi-card-blue',
                    )
                with m3:
                    kpi_card(
                        label       = "🚀 Best Case Total",
                        value       = fm['best_case_total'],
                        is_currency = is_currency,
                        color       = 'kpi-card-green',
                    )
                with m4:
                    kpi_card(
                        label       = "⚠️ Worst Case Total",
                        value       = fm['worst_case_total'],
                        is_currency = is_currency,
                        color       = 'kpi-card-red',
                    )

                st.plotly_chart(result['chart'], use_container_width=True)

                change = fm.get('expected_change_pct', 0)
                if change > 10:
                    st.markdown(f'<div class="alert-success">📈 Forecast shows {change:.1f}% growth expected over the next {forecast_days} days compared to the same recent period. Strong positive trend detected.</div>', unsafe_allow_html=True)
                elif change > 0:
                    st.markdown(f'<div class="alert-info">📊 Forecast shows modest {change:.1f}% growth expected. Stable trend with slight upward momentum.</div>', unsafe_allow_html=True)
                elif change > -10:
                    st.markdown(f'<div class="alert-warning">📉 Forecast shows slight decline of {abs(change):.1f}%. Consider running promotions to offset this trend.</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="alert-danger">⚠️ Forecast shows significant decline of {abs(change):.1f}%. Urgent action recommended — review marketing, pricing, and product availability.</div>', unsafe_allow_html=True)

            else:
                st.error(f"Forecast failed: {result.get('error', 'Unknown error')}")
                st.markdown("""
                    <div class="alert-warning">
                        💡 <strong>Not enough data for this period.</strong><br>
                        Switch the date filter to <strong>All Time</strong> or <strong>Last 365 Days</strong>
                        to get enough historical data for an accurate forecast.
                        You need at least 30 days of sales history.
                    </div>
                    """, unsafe_allow_html=True)

        else:
            st.markdown("""
            <div style="text-align:center;padding:60px 20px;color:#999;">
                <div style="font-size:60px;">🔮</div>
                <p style="font-size:18px;margin-top:16px;color:#666;">
                    Configure your forecast settings and click <strong>Run Forecast</strong>
                </p>
                <p style="font-size:14px;color:#aaa;">
                    Requires at least 30 days of historical data
                </p>
            </div>
            """, unsafe_allow_html=True)

    # Forecast summary table
    if st.session_state.get('forecast_ran', False) and 'result' in dir():
        if result['success'] and len(result['summary_table']) > 0:
            section_title("📋 Weekly Forecast Breakdown")

            tbl = result['summary_table'].copy()
            is_currency = metric_choice in ['revenue', 'profit']

            for col in ['Predicted Total', 'Best Case', 'Worst Case', 'Daily Average']:
                if col in tbl.columns:
                    tbl[col] = tbl[col].apply(fmt_currency if is_currency else fmt_number)

            st.dataframe(tbl, use_container_width=True, hide_index=True)


# ==========================================
# TAB 7: RAW DATA
# ==========================================

def render_data_tab(df):

    section_title("🗂️ Raw Data Explorer")

    if len(df) == 0:
        st.info("No data available for the selected filters.")
        return

    col_l, col_r = st.columns([2, 1])

    with col_l:
        st.markdown(f"""
        <div class="filter-bar">
            📊 Showing <strong>{len(df):,}</strong> records &nbsp;|&nbsp;
            💰 Total Revenue: <strong>{fmt_currency(df['revenue'].sum())}</strong> &nbsp;|&nbsp;
            🛒 Orders: <strong>{fmt_number(len(df))}</strong>
        </div>
        """, unsafe_allow_html=True)

    with col_r:
        search = st.text_input("🔍 Search product name", "", placeholder="Type to filter...")

    display_df = df.copy()

    if search:
        display_df = display_df[
            display_df['product_name'].str.contains(search, case=False, na=False)
        ]

    cols_to_show = [
        'order_id', 'date', 'product_name', 'category',
        'quantity', 'unit_price', 'discount_pct',
        'revenue', 'cost', 'profit', 'profit_margin',
        'channel', 'payment_method', 'customer_type',
        'city', 'state', 'region', 'status'
    ]

    cols_available = [c for c in cols_to_show if c in display_df.columns]

    st.dataframe(
        display_df[cols_available].head(500),
        use_container_width = True,
        hide_index          = True,
        column_config       = {
            'revenue':       st.column_config.NumberColumn('Revenue',       format='$%.2f'),
            'profit':        st.column_config.NumberColumn('Profit',        format='$%.2f'),
            'cost':          st.column_config.NumberColumn('Cost',          format='$%.2f'),
            'unit_price':    st.column_config.NumberColumn('Unit Price',    format='$%.2f'),
            'profit_margin': st.column_config.NumberColumn('Margin %',      format='%.1f%%'),
            'discount_pct':  st.column_config.NumberColumn('Discount %',    format='%.0f%%'),
        }
    )

    if len(display_df) > 500:
        st.info(f"Showing first 500 of {len(display_df):,} records. Download the full dataset below.")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        csv = display_df[cols_available].to_csv(index=False)
        st.download_button(
            label               = "📥 Download as CSV",
            data                = csv,
            file_name           = f"sales_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime                = 'text/csv',
            use_container_width = True,
        )

    with col_b:
        json_data = display_df[cols_available].to_json(orient='records', date_format='iso')
        st.download_button(
            label               = "📥 Download as JSON",
            data                = json_data,
            file_name           = f"sales_data_{datetime.now().strftime('%Y%m%d')}.json",
            mime                = 'application/json',
            use_container_width = True,
        )

    with col_c:
        st.markdown(f"""
        <div style="text-align:center;padding:8px;background:#f8f9ff;
                    border-radius:8px;font-size:13px;color:#555;border:1px solid #e0e0ff;">
            📋 {len(display_df):,} rows × {len(cols_available)} columns
        </div>
        """, unsafe_allow_html=True)

    # Quick stats
    section_title("📊 Quick Statistics")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Numeric Summary**")
        numeric_cols = ['revenue', 'profit', 'profit_margin', 'quantity', 'unit_price']
        numeric_cols = [c for c in numeric_cols if c in display_df.columns]
        st.dataframe(display_df[numeric_cols].describe().round(2), use_container_width=True)

    with col2:
        st.markdown("**Value Counts — Status**")
        if 'status' in display_df.columns:
            status_counts = display_df['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            status_counts['Percentage'] = (status_counts['Count'] / len(display_df) * 100).round(1).astype(str) + '%'
            st.dataframe(status_counts, use_container_width=True, hide_index=True)


# ==========================================
# MAIN APPLICATION
# ==========================================

def main():

    df_full = load_all_data()

    if df_full is None:
        st.markdown("""
        <div class="dash-header">
            <h1>📊 Sales Tracker Dashboard</h1>
            <p>Data files not found. Please run the setup scripts first.</p>
        </div>
        """, unsafe_allow_html=True)

        st.error("❌ Could not find data files.")

        st.markdown("""
        ### 🚀 Quick Setup

        Open your terminal and run these commands in order:

        ```bash
        python data_generator.py
        python data_processor.py
        streamlit run app.py
        ```
        """)
        return

    # Render sidebar and get filter values
    (
        selected_period,
        selected_cat,
        selected_chan,
        selected_region,
        selected_cust_type,
        start_date,
        end_date,
    ) = render_sidebar(df_full)

    # Apply filters
    df_filtered = filter_data(
        df_full,
        selected_period,
        selected_cat,
        selected_chan,
        selected_region,
        selected_cust_type,
        start_date,
        end_date,
    )

    # Get previous period for comparison
    df_prev = get_previous_period_data(df_full, selected_period, start_date, end_date)

    # Dashboard header
    st.markdown(f"""
    <div class="dash-header">
        <h1>📊 Sales Tracker Dashboard</h1>
        <p>{REPORT_CONFIG['company_name']} &nbsp;·&nbsp; {selected_period} &nbsp;·&nbsp; {len(df_filtered):,} records</p>
    </div>
    """, unsafe_allow_html=True)

    # Filter summary bar
    active_filters = []
    if selected_cat != 'All Categories': active_filters.append(f"📦 {selected_cat}")
    if selected_chan != 'All Channels': active_filters.append(f"📢 {selected_chan}")
    if selected_region != 'All Regions': active_filters.append(f"🌍 {selected_region}")
    if selected_cust_type != 'All Customers': active_filters.append(f"👥 {selected_cust_type}")

    filter_text = " &nbsp;|&nbsp; ".join(active_filters) if active_filters else "No additional filters applied"

    st.markdown(f"""
    <div class="filter-bar">
        📅 <strong>{selected_period}</strong> &nbsp;|&nbsp; {filter_text} &nbsp;|&nbsp;
        🔢 <strong>{len(df_filtered):,}</strong> completed orders
    </div>
    """, unsafe_allow_html=True)

    if len(df_filtered) == 0:
        st.warning("⚠️ No data found for the selected filters. Try changing your filter settings.")
        return

    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Overview",
        "🏆 Products",
        "👥 Customers",
        "📢 Channels & Geo",
        "⏰ Time Patterns",
        "🔮 Forecast",
        "🗂️ Raw Data",
    ])

    with tab1:
        render_overview_tab(df_filtered, df_prev)

    with tab2:
        render_products_tab(df_filtered)

    with tab3:
        render_customers_tab(df_filtered)

    with tab4:
        render_channels_tab(df_filtered)

    with tab5:
        render_patterns_tab(df_filtered)

    with tab6:
        render_forecast_tab(df_filtered)

    with tab7:
        render_data_tab(df_filtered)

    # Footer
    st.markdown(f"""
    <div class="dash-footer">
        📊 {APP_CONFIG['app_name']} v{APP_CONFIG['version']} &nbsp;·&nbsp;
        Built with Python & Streamlit &nbsp;·&nbsp;
        Data refreshes every {DASHBOARD_CONFIG['cache_ttl'] // 60} minutes
    </div>
    """, unsafe_allow_html=True)


if __name__ == '__main__':
    main()