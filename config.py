# config.py
# Central configuration file for the entire dashboard
# All settings, constants, and configurations live here

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ==========================================
# APPLICATION SETTINGS
# ==========================================

APP_CONFIG = {
    'app_name': 'Sales Tracker Dashboard',
    'version': '1.0.0',
    'author': 'Akshay Som',
    'description': 'Real-time sales analytics for small businesses',
    'timezone': 'US/Eastern',  # We can change to any timezone
}


# ==========================================
# FILE PATHS
# ==========================================

PATHS = {
    # Data files
    'raw_data': 'data/raw/sales_data.csv',
    'processed_completed': 'data/processed/sales_completed.csv',
    'processed_refunded': 'data/processed/sales_refunded.csv',
    'processed_pending': 'data/processed/sales_pending.csv',
    'processed_all': 'data/processed/sales_all.csv',
    
    # Output folders
    'reports_folder': 'reports/',
    'assets_folder': 'assets/',
    'logs_folder': 'logs/',
    
    # Report templates
    'report_template': 'assets/report_template.html',
    
    # Logo (optional)
    'logo': 'assets/logo.png',
}


# ==========================================
# EMAIL CONFIGURATION
# ==========================================
# These values come from our .env file
# NEVER hardcode passwords in our code

EMAIL_CONFIG = {
    # Sender email settings
    'sender_email': os.getenv('EMAIL_SENDER', ''),
    'sender_password': os.getenv('EMAIL_PASSWORD', ''),
    'sender_name': os.getenv('EMAIL_SENDER_NAME', 'Sales Dashboard Bot'),
    
    # SMTP server settings
    # Gmail settings (most common)
    'smtp_host': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', '587')),
    'use_tls': True,
    
    # Other popular SMTP servers:
    # Outlook: smtp-mail.outlook.com, port 587
    # Yahoo: smtp.mail.yahoo.com, port 587
    # Zoho: smtp.zoho.com, port 587
    
    # Default recipients
    'default_recipients': os.getenv(
        'EMAIL_RECIPIENTS', 
        'manager@business.com'
    ).split(','),
    
    # Email schedule settings
    'daily_report_time': '08:00',  # Send daily report at 8 AM
    'weekly_report_day': 'monday',  # Send weekly report on Monday
    'weekly_report_time': '09:00',  # Send weekly report at 9 AM
    'monthly_report_day': 1,  # Send monthly report on 1st of month
}


# ==========================================
# REPORT CONFIGURATION
# ==========================================

REPORT_CONFIG = {
    # Report types to generate
    'generate_daily': True,
    'generate_weekly': True,
    'generate_monthly': True,
    
    # Report format
    'format': 'html',  # 'html' or 'pdf'
    
    # Company branding
    'company_name': os.getenv('COMPANY_NAME', 'Your Company Name'),
    'company_logo': 'assets/logo.png',
    'primary_color': '#667eea',
    'secondary_color': '#764ba2',
    
    # What to include in reports
    'include_sections': {
        'kpi_summary': True,
        'revenue_trend': True,
        'top_products': True,
        'channel_performance': True,
        'geographic_breakdown': True,
        'customer_analysis': True,
        'forecast': True,
        'recommendations': True,
    },
    
    # Number of top items to show
    'top_n_products': 10,
    'top_n_customers': 5,
    'top_n_cities': 5,
}


# ==========================================
# FORECASTING CONFIGURATION
# ==========================================

FORECAST_CONFIG = {
    # How many days to forecast into the future
    'forecast_days': 30,
    
    # Minimum data needed to make a forecast
    'min_data_points': 30,
    
    # Confidence interval (80 = 80% confidence band)
    'confidence_interval': 0.80,
    
    # Seasonality settings
    'yearly_seasonality': True,
    'weekly_seasonality': True,
    'daily_seasonality': False,
    
    # Model to use
    # 'prophet' = Facebook Prophet (best for business data)
    # 'linear' = Simple linear regression (fast, less accurate)
    # 'auto' = Automatically choose based on data
    'model': 'prophet',
    
    # What to forecast
    'forecast_metrics': ['revenue', 'orders'],
}


# ==========================================
# DASHBOARD CONFIGURATION
# ==========================================

DASHBOARD_CONFIG = {
    'cache_ttl': 300,
    'default_period': 'Last 30 Days',
    'currency_symbol': '$',
    
    'primary_color': '#667eea',
    'secondary_color': '#764ba2',
    'success_color': '#28a745',
    'danger_color': '#dc3545',
    'warning_color': '#ffc107',

    'chart_palette':    [
        '#667eea', '#764ba2', '#f093fb',
        '#4facfe', '#00f2fe', '#43e97b',
        '#fa709a', '#fee140', '#30cfd0',
        '#a18cd1', '#fbc2eb', '#ffecd2'
    ],

    'alerts': {
        'min_daily_revenue':    500,
        'min_profit_margin':    20,
        'max_refund_rate':      10,
        'min_daily_orders':     10,
    },
}


# ==========================================
# DATA GENERATION CONFIGURATION
# ==========================================
# Only used when running data_generator.py

DATA_GEN_CONFIG = {
    'num_records': 5000,
    'start_date': '2023-01-01',
    'random_seed': 42,
    
    # Products catalog
    'products': {
        'Laptop Pro X1': {'category': 'Electronics', 'price': 1299.99, 'cost': 800},
        'Wireless Headphones': {'category': 'Electronics', 'price': 299.99, 'cost': 120},
        'Smart Watch Series 5': {'category': 'Electronics', 'price': 449.99, 'cost': 180},
        'Bluetooth Speaker': {'category': 'Electronics', 'price': 129.99, 'cost': 45.00},
        'USB-C Hub 7-in-1': {'category': 'Accessories', 'price': 79.99, 'cost': 25},
        'Phone Case Premium': {'category': 'Accessories', 'price': 34.99, 'cost': 8},
        'Laptop Bag Leather': {'category': 'Accessories', 'price': 89.99, 'cost': 30},
        'Screen Protector': {'category': 'Accessories', 'price': 19.99, 'cost': 4.00},
        'Python Course': {'category': 'Digital', 'price': 199.99, 'cost': 5},
        'Data Science Bundle': {'category': 'Digital', 'price': 299.99, 'cost': 5},
        'Excel Masterclass': {'category': 'Digital', 'price': 99.99, 'cost': 5},
        'SQL for Beginners': {'category': 'Digital', 'price': 79.99, 'cost': 5.00},
        'Desk Organizer': {'category': 'Office', 'price': 49.99, 'cost': 15},
        'Ergonomic Mouse': {'category': 'Office', 'price': 69.99, 'cost': 22},
        'Mechanical Keyboard': {'category': 'Office', 'price': 159.99, 'cost': 65},
        'Monitor Stand': {'category': 'Office', 'price': 89.99, 'cost': 28.00},
    },
    
    # Sales channels with probability weights
    # Higher weight = appears more often in data
    'channels': {
        'Website': 35,  # 35% of sales
        'Mobile App': 25,  # 25% of sales
        'Amazon': 20,  # 20% of sales
        'Social Media': 12,  # 12% of sales
        'Email Campaign': 8,  # 8%  of sales
    },
}


# ==========================================
# LOGGING CONFIGURATION
# ==========================================

LOGGING_CONFIG = {
    'log_level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
    'log_to_file': True,
    'log_file': 'logs/app.log',
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'max_log_size': 10 * 1024 * 1024,  # 10 MB max log file size
    'backup_count': 3,  # Keep 3 old log files
}


# ==========================================
# WHAT TO PUT IN OUR .env FILE
# ==========================================
"""
Create a file called .env in our project root
and add these lines (replace with our actual values):

EMAIL_SENDER=ouremail@gmail.com
EMAIL_PASSWORD=our_app_password_here
EMAIL_SENDER_NAME=Sales Dashboard
EMAIL_RECIPIENTS=boss@company.com,manager@company.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
COMPANY_NAME=My Awesome Store

HOW TO GET GMAIL APP PASSWORD:
1. Go to myaccount.google.com
2. Security → 2-Step Verification (enable it)
3. Security → App passwords
4. Create new app password for "Mail"
5. Copy the 16-character password
6. Paste it as EMAIL_PASSWORD in .env

IMPORTANT: 
- Add .env to our .gitignore file
- NEVER push .env to GitHub
- Your real password stays private
"""


# ==========================================
# HELPER FUNCTION TO VALIDATE CONFIG
# ==========================================

def validate_config():
    """
    Check if all required configuration is present
    Call this when starting the application
    """
    
    issues = []
    warnings = []
    
    # Check email config
    if not EMAIL_CONFIG['sender_email']:
        warnings.append("EMAIL_SENDER not set in .env - email reports disabled")
    
    if not EMAIL_CONFIG['sender_password']:
        warnings.append("EMAIL_PASSWORD not set in .env - email reports disabled")
    
    # Check if data files exist
    if not os.path.exists(PATHS['raw_data']):
        issues.append(f"Raw data file not found: {PATHS['raw_data']}")
        issues.append("Run: python data_generator.py")
    
    # Check if folders exist, create if not
    folders_to_check = [
        'data/raw',
        'data/processed',
        'reports',
        'assets',
        'logs'
    ]
    
    for folder in folders_to_check:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            print(f"📁 Created folder: {folder}")
    
    # Print results
    if issues:
        print("\n❌ CONFIGURATION ERRORS:")
        for issue in issues:
            print(f"   → {issue}")
    
    if warnings:
        print("\n⚠️  CONFIGURATION WARNINGS:")
        for warning in warnings:
            print(f"   → {warning}")
    
    if not issues and not warnings:
        print("✅ Configuration looks good!")
    
    return len(issues) == 0  # Returns True if no critical errors


# Run validation when this file is imported
if __name__ == '__main__':
    print("Validating configuration...")
    validate_config()
    
    print("\n📋 Current Configuration:")
    print(f"   App: {APP_CONFIG['app_name']} v{APP_CONFIG['version']}")
    print(f"   Forecast Days: {FORECAST_CONFIG['forecast_days']}")
    print(f"   Daily Report Time: {EMAIL_CONFIG['daily_report_time']}")
    print(f"   Cache TTL: {DASHBOARD_CONFIG['cache_ttl']} seconds")
    print(f"   Email Sender: {EMAIL_CONFIG['sender_email'] or 'NOT SET'}")