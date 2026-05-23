# kpi_calculator.py
# Calculates all business metrics for the dashboard

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def calculate_revenue_metrics(df, df_prev=None):
    """
    Calculate all revenue-related KPIs
    
    Parameters:
    -----------
    df : current period data
    df_prev : previous period data (for comparison)
    """
    if len(df) == 0:
        return {
            'total_revenue': 0, 'total_orders': 0, 'total_units_sold': 0,
            'total_profit': 0, 'avg_order_value': 0, 'avg_profit_margin': 0,
            'unique_customers': 0, 'new_customers': 0, 'returning_customers': 0,
            'returning_rate': 0, 'revenue_per_customer': 0,
            'revenue_growth': 0, 'orders_growth': 0,
            'total_discount_given': 0, 'refund_rate': 0,
        }
    
    metrics = {}
    
    # ==========================================
    # BASIC REVENUE METRICS
    # ==========================================
    
    metrics['total_revenue'] = df['revenue'].sum()
    metrics['total_orders'] = len(df)
    metrics['total_units_sold'] = df['quantity'].sum()
    metrics['total_profit'] = df['profit'].sum()
    metrics['avg_order_value'] = df['revenue'].mean()
    metrics['avg_profit_margin'] = df['profit_margin'].mean()
    metrics['median_order_value'] = round(df['revenue'].median(), 2)
    metrics['max_order_value'] = round(df['revenue'].max(), 2)
    metrics['min_order_value'] = round(df['revenue'].min(), 2)
    
    if 'discount_amount' in df.columns:
        metrics['total_discount_given'] = round(df['discount_amount'].sum(), 2)
    else:
        metrics['total_discount_given'] = 0

    metrics['unique_customers'] = df['customer_email'].nunique()

    if 'customer_type' in df.columns:
        new_mask = df['customer_type'] == 'New'
        returning_mask = df['customer_type'] == 'Returning'
        metrics['new_customers'] = df[new_mask]['customer_email'].nunique()
        metrics['returning_customers'] = df[returning_mask]['customer_email'].nunique()
    else:
        metrics['new_customers'] = 0
        metrics['returning_customers'] = 0

    if metrics['unique_customers'] > 0:
        metrics['returning_rate'] = round(
            metrics['returning_customers'] / metrics['unique_customers'] * 100, 2
        )
        metrics['revenue_per_customer'] = round(
            metrics['total_revenue'] / metrics['unique_customers'], 2
        )
    else:
        metrics['returning_rate'] = 0
        metrics['revenue_per_customer'] = 0

    metrics['revenue_growth'] = 0
    metrics['orders_growth'] = 0
    metrics['profit_growth'] = 0

    if df_prev is not None and len(df_prev) > 0:
        prev_revenue = df_prev['revenue'].sum()
        prev_orders  = len(df_prev)
        prev_profit  = df_prev['profit'].sum()

        if prev_revenue > 0:
            metrics['revenue_growth'] = round(
                (metrics['total_revenue'] - prev_revenue) / prev_revenue * 100, 2
            )
        if prev_orders > 0:
            metrics['orders_growth'] = round(
                (metrics['total_orders'] - prev_orders) / prev_orders * 100, 2
            )
        if prev_profit > 0:
            metrics['profit_growth'] = round(
                (metrics['total_profit'] - prev_profit) / prev_profit * 100, 2
            )

    metrics['refund_rate'] = 0

    return metrics


def calculate_product_performance(df):
    """
    Calculate product-level performance metrics
    """
    if len(df) == 0:
        return pd.DataFrame()
    
    product_stats = df.groupby('product_name').agg(
        total_revenue = ('revenue', 'sum'),
        total_units = ('quantity', 'sum'),
        total_orders = ('order_id', 'count'),
        avg_order_value = ('revenue', 'mean'),
        total_profit = ('profit', 'sum'),
        avg_margin = ('profit_margin', 'mean'),
        min_price = ('unit_price', 'min'),
        max_price = ('unit_price', 'max'),
    ).reset_index()
    
    product_stats = product_stats.merge(
        df[['product_name', 'category']].drop_duplicates(),
        on='product_name', how='left'
    )

    total_rev = product_stats['total_revenue'].sum()
    if total_rev > 0:
        product_stats['revenue_share'] = round(
            product_stats['total_revenue'] / total_rev * 100, 2
        )
    else:
        product_stats['revenue_share'] = 0

    product_stats['total_revenue'] = product_stats['total_revenue'].round(2)
    product_stats['total_profit'] = product_stats['total_profit'].round(2)
    product_stats['avg_order_value'] = product_stats['avg_order_value'].round(2)
    product_stats['avg_margin'] = product_stats['avg_margin'].round(2)

    product_stats = product_stats.sort_values('total_revenue', ascending=False).reset_index(drop=True)
    product_stats['rank'] = product_stats.index + 1

    return product_stats


def calculate_category_performance(df):
    """
    Calculate category-level performance metrics
    """
    if len(df) == 0:
        return pd.DataFrame()
    
    category_stats = df.groupby('category').agg(
        total_revenue = ('revenue', 'sum'),
        total_units = ('quantity', 'sum'),
        total_orders = ('order_id', 'count'),
        total_profit = ('profit', 'sum'),
        avg_margin = ('profit_margin', 'mean'),
        num_products = ('product_name', 'nunique'),
        avg_order_value = ('revenue', 'mean'),
    ).reset_index()
    
    # Revenue share per category
    total = category_stats['total_revenue'].sum()
    if total > 0:
        category_stats['revenue_share'] = round(
            category_stats['total_revenue'] / total * 100, 2
        )
    else:
        category_stats['revenue_share'] = 0

    category_stats['total_revenue'] = category_stats['total_revenue'].round(2)
    category_stats['total_profit'] = category_stats['total_profit'].round(2)
    category_stats['avg_margin'] = category_stats['avg_margin'].round(2)
    category_stats['avg_order_value'] = category_stats['avg_order_value'].round(2)

    category_stats = category_stats.sort_values('total_revenue', ascending=False).reset_index(drop=True)

    return category_stats


def calculate_channel_performance(df):
    """
    Calculate sales channel performance
    """
    if len(df) == 0:
        return pd.DataFrame()
    
    channel_stats = df.groupby('channel').agg(
        total_revenue = ('revenue', 'sum'),
        total_orders = ('order_id', 'count'),
        total_profit = ('profit', 'sum'),
        avg_order_value = ('revenue', 'mean'),
        total_units = ('quantity', 'sum'),
        unique_customers = ('customer_email', 'nunique'),
    ).reset_index()
    
    total = channel_stats['total_revenue'].sum()
    if total > 0:
        channel_stats['revenue_share'] = round(
            channel_stats['total_revenue'] / total * 100, 2
        )
    else:
        channel_stats['revenue_share'] = 0

    channel_stats['profit_margin'] = round(
        channel_stats['total_profit'] / channel_stats['total_revenue'] * 100, 2
    )

    channel_stats['total_revenue'] = channel_stats['total_revenue'].round(2)
    channel_stats['total_profit'] = channel_stats['total_profit'].round(2)
    channel_stats['avg_order_value'] = channel_stats['avg_order_value'].round(2)

    channel_stats = channel_stats.sort_values('total_revenue', ascending=False).reset_index(drop=True)

    return channel_stats


def calculate_daily_sales(df):
    """
    Calculate daily sales totals for trend charts
    """
    if len(df) == 0:
        return pd.DataFrame()
    
    daily = df.groupby('date').agg(
        revenue = ('revenue', 'sum'),
        orders = ('order_id', 'count'),
        profit = ('profit', 'sum'),
        units = ('quantity', 'sum'),
        customers = ('customer_email', 'nunique'),
    ).reset_index()
    
    daily = daily.sort_values('date').reset_index(drop=True)

    daily['revenue_7day_avg'] = daily['revenue'].rolling(window=7, min_periods=1).mean().round(2)
    daily['orders_7day_avg'] = daily['orders'].rolling(window=7, min_periods=1).mean().round(2)
    daily['revenue_cumulative'] = daily['revenue'].cumsum().round(2)
    daily['orders_cumulative'] = daily['orders'].cumsum()

    daily['revenue'] = daily['revenue'].round(2)
    daily['profit'] = daily['profit'].round(2)

    return daily


def calculate_monthly_sales(df):
    """
    Calculate monthly sales totals
    """
    if len(df) == 0:
        return pd.DataFrame()
    
    monthly = df.groupby('year_month').agg(
        revenue = ('revenue', 'sum'),
        orders = ('order_id', 'count'),
        profit = ('profit', 'sum'),
        customers = ('customer_email', 'nunique'),
        units = ('quantity', 'sum'),
    ).reset_index()
    
    monthly = monthly.sort_values('year_month').reset_index(drop=True)

    monthly['revenue_mom_growth'] = monthly['revenue'].pct_change().multiply(100).round(2)
    monthly['orders_mom_growth'] = monthly['orders'].pct_change().multiply(100).round(2)
    monthly['avg_order_value'] = (monthly['revenue'] / monthly['orders']).round(2)

    monthly['revenue'] = monthly['revenue'].round(2)
    monthly['profit'] = monthly['profit'].round(2)

    return monthly


def calculate_geographic_performance(df):
    """
    Calculate performance by location
    """
    if len(df) == 0:
        return pd.DataFrame()
    
    geo_stats = df.groupby(['city', 'state', 'region']).agg(
        total_revenue = ('revenue', 'sum'),
        total_orders = ('order_id', 'count'),
        total_customers = ('customer_email', 'nunique'),
        avg_order_value = ('revenue', 'mean'),
        total_profit = ('profit', 'sum'),
    ).reset_index()
    
    geo_stats['total_revenue'] = geo_stats['total_revenue'].round(2)
    geo_stats['total_profit'] = geo_stats['total_profit'].round(2)
    geo_stats['avg_order_value'] = geo_stats['avg_order_value'].round(2)

    geo_stats = geo_stats.sort_values('total_revenue', ascending=False).reset_index(drop=True)

    return geo_stats


def calculate_regional_performance(df):

    if len(df) == 0:
        return pd.DataFrame()

    region_stats = df.groupby('region').agg(
        total_revenue = ('revenue', 'sum'),
        total_orders = ('order_id', 'count'),
        total_customers = ('customer_email', 'nunique'),
        avg_order_value = ('revenue', 'mean'),
        total_profit = ('profit', 'sum'),
    ).reset_index()

    total = region_stats['total_revenue'].sum()
    if total > 0:
        region_stats['revenue_share'] = round(
            region_stats['total_revenue'] / total * 100, 2
        )
    else:
        region_stats['revenue_share'] = 0

    region_stats['total_revenue'] = region_stats['total_revenue'].round(2)
    region_stats['total_profit'] = region_stats['total_profit'].round(2)
    region_stats['avg_order_value'] = region_stats['avg_order_value'].round(2)

    region_stats = region_stats.sort_values('total_revenue', ascending=False).reset_index(drop=True)

    return region_stats


def calculate_payment_method_breakdown(df):

    if len(df) == 0:
        return pd.DataFrame()

    payment_stats = df.groupby('payment_method').agg(
        total_revenue = ('revenue', 'sum'),
        total_orders = ('order_id', 'count'),
        avg_order_value = ('revenue', 'mean'),
    ).reset_index()

    total = payment_stats['total_revenue'].sum()
    if total > 0:
        payment_stats['revenue_share'] = round(
            payment_stats['total_revenue'] / total * 100, 2
        )
    else:
        payment_stats['revenue_share'] = 0

    payment_stats = payment_stats.sort_values('total_revenue', ascending=False).reset_index(drop=True)

    return payment_stats


def calculate_customer_type_breakdown(df):

    if len(df) == 0:
        return pd.DataFrame()

    customer_stats = df.groupby('customer_type').agg(
        total_revenue = ('revenue', 'sum'),
        total_orders = ('order_id', 'count'),
        avg_order_value = ('revenue', 'mean'),
        total_profit = ('profit', 'sum'),
        unique_customers = ('customer_email', 'nunique'),
    ).reset_index()

    total = customer_stats['total_revenue'].sum()
    if total > 0:
        customer_stats['revenue_share'] = round(
            customer_stats['total_revenue'] / total * 100, 2
        )
    else:
        customer_stats['revenue_share'] = 0

    customer_stats['total_revenue'] = customer_stats['total_revenue'].round(2)
    customer_stats['avg_order_value'] = customer_stats['avg_order_value'].round(2)

    return customer_stats


def calculate_hourly_patterns(df):
    """
    Find what hours/days have most sales
    """
    if len(df) == 0:
        return pd.DataFrame(), pd.DataFrame()
    
    # By hour
    hourly = df.groupby('hour').agg(
        revenue = ('revenue', 'sum'),
        orders = ('order_id', 'count'),
        profit = ('profit', 'sum'),
    ).reset_index()
    
    hourly['revenue'] = hourly['revenue'].round(2)
    hourly['profit'] = hourly['profit'].round(2)

    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    # By day of week
    daily_pattern = df.groupby(['day_of_week', 'day_name']).agg(
        revenue = ('revenue', 'sum'),
        orders = ('order_id', 'count'),
        profit = ('profit', 'sum'),
    ).reset_index()
    
    daily_pattern['revenue'] = daily_pattern['revenue'].round(2)
    daily_pattern['profit'] = daily_pattern['profit'].round(2)
    daily_pattern = daily_pattern.sort_values('day_of_week').reset_index(drop=True)

    return hourly, daily_pattern


def calculate_top_customers(df, top_n=10):

    if len(df) == 0:
        return pd.DataFrame()

    customer_stats = df.groupby(['customer_email', 'customer_name', 'customer_type']).agg(
        total_revenue = ('revenue', 'sum'),
        total_orders = ('order_id', 'count'),
        total_units = ('quantity', 'sum'),
        avg_order_value = ('revenue', 'mean'),
        total_profit = ('profit', 'sum'),
        first_purchase = ('date', 'min'),
        last_purchase = ('date', 'max'),
    ).reset_index()

    customer_stats['total_revenue'] = customer_stats['total_revenue'].round(2)
    customer_stats['avg_order_value'] = customer_stats['avg_order_value'].round(2)
    customer_stats['total_profit'] = customer_stats['total_profit'].round(2)

    customer_stats = customer_stats.sort_values('total_revenue', ascending=False).head(top_n).reset_index(drop=True)
    customer_stats['rank'] = customer_stats.index + 1

    return customer_stats


def get_all_kpis(df):
    """
    Run all KPI calculations and return everything
    """
    
    print("Calculating all KPIs...")

    hourly, daily_pattern = calculate_hourly_patterns(df)
    
    results = {
        'summary': calculate_revenue_metrics(df),
        'products': calculate_product_performance(df),
        'categories': calculate_category_performance(df),
        'channels': calculate_channel_performance(df),
        'daily_sales': calculate_daily_sales(df),
        'monthly_sales': calculate_monthly_sales(df),
        'geographic': calculate_geographic_performance(df),
        'regional': calculate_regional_performance(df),
        'payment_methods': calculate_payment_method_breakdown(df),
        'customer_types': calculate_customer_type_breakdown(df),
        'hourly_pattern': hourly,
        'daily_pattern': daily_pattern,
        'top_customers': calculate_top_customers(df),
    }
    
    print("-> All KPIs calculated")
    return results


if __name__ == '__main__':
    import os
    # Test the calculator
    filepath = 'data/processed/sales_completed.csv'
    if not os.path.exists(filepath):
        print("Run data_generator.py and data_processor.py first")
    else:
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])

        kpis = get_all_kpis(df)

        print("\n📊 Summary Metrics:")
        for key, value in kpis['summary'].items():
            if isinstance(value, float):
                print(f"   {key:<25}: {value:>12,.2f}")
            else:
                print(f"   {key:<25}: {value:>12,}")

        print(f"\n🏆 Top 5 Products:")
        print(kpis['products'][['rank', 'product_name', 'total_revenue', 'revenue_share']].head(5).to_string(index=False))