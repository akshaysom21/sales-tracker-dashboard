# data_processor.py
# This file cleans and prepares data for analysis

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def load_data(filepath = 'data/raw/sales_data.csv'):
    """
    Load raw sales data from CSV
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"File not found: {filepath}\n"
            f"Please run data_generator.py first.\n"
            f"Command: python data_generator.py"
        )
    print(f"Loading data from {filepath}...")

    df = pd.read_csv(filepath)

    # Convert date columns to proper datetime type
    df['date'] = pd.to_datetime(df['date'])
    df['datetime'] = pd.to_datetime(df['datetime'])

    print(f"-> Loaded {len(df):,} records")
    print(f"   Columns: {list(df.columns)}")
    return df

def clean_data(df):
    """
    Clean the data - handle missing values, duplicates, etc.
    """
    print("Cleaning data...")

    original_count = len(df)

    # Remove duplicate orders
    df = df.drop_duplicates(subset = ['order_id'])
    after_dedup = len(df)
    print(f"   Removed {original_count - after_dedup} duplicate orders")

    # Remove rows where revenue is negative or zero
    df = df[df['revenue'] > 0]
    after_revenue = len(df)
    print(f"   Removed {after_dedup - after_revenue} zero/negative revenue records")

    # Remove rows with missing critical fields
    df = df.dropna(subset = ['product_name', 'date', 'revenue', 'order_id'])
    after_na = len(df)
    print(f"   Removed {after_revenue - after_na} records with missing critical fields")

    # Fix any data type issues
    numeric_columns = [
        'quantity', 'unit_price', 'unit_cost',
        'revenue', 'cost', 'profit', 'profit_margin',
        'discount_pct', 'discount_amount', 'gross_revenue'
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(0)

    string_columns = [
        'product_name', 'category', 'channel',
        'payment_method', 'status', 'customer_email',
        'customer_name', 'customer_type', 'city', 'state', 'region'
    ]

    for col in string_columns:
        if col in df.columns:
            df[col] = df[col].fillna('Unknown')
            df[col] = df[col].str.strip()


    df = df[df['quantity'] >= 1]
    df = df[df['unit_price'] > 0]
    df = df[df['profit_margin'] >= -100]
    df = df[df['profit_margin'] <= 100]

    final_count = len(df)
    total_removed = original_count - final_count
    print(f"\n-> Cleaning complete!")
    print(f"   Original records : {original_count:,}")
    print(f"   Final records : {final_count:,}")
    print(f"   Total removed : {total_removed:,}")

    return df


def add_time_features(df):
    """
    Add useful time-based columns for analysis
    """
    print("Adding time features...")

    # Extract time components
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['month_name'] = df['date'].dt.strftime('%B')
    df['month_short'] = df['date'].dt.strftime('%b')
    df['week'] = df['date'].dt.isocalendar().week.astype(int)
    df['day_of_week'] = df['date'].dt.dayofweek
    df['day_name'] = df['date'].dt.strftime('%A')
    df['day_short'] = df['date'].dt.strftime('%a')
    df['day_of_month'] = df['date'].dt.day
    df['quarter'] = df['date'].dt.quarter
    df['quarter_label'] = 'Q' + df['quarter'].astype(str)
    df['is_weekend'] = df['day_of_week'].isin([5, 6])
    df['is_weekday'] = ~df['is_weekend']

    # Create period labels
    df['year_month'] = df['date'].dt.strftime('%Y-%m')
    df['year_quarter'] = df['date'].dt.to_period('Q').astype(str)
    df['year_week'] = df['date'].dt.strftime('%Y-W%U')
    
    # Hour of day (from time column)
    df['hour'] = pd.to_datetime(df['time'], format='%H:%M:%S').dt.hour
    
    # Time of day category
    def get_time_of_day(hour):
        if 5 <= hour < 12:
            return 'Morning'
        elif 12 <= hour < 17:
            return 'Afternoon'
        elif 17 <= hour < 21:
            return 'Evening'
        else:
            return 'Night'
    
    df['time_of_day'] = df['hour'].apply(get_time_of_day)

    def get_season(month):
        if month in [12, 1, 2]:
            return 'Winter'
        elif month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        else:
            return 'Fall'

    df['season'] = df['month'].apply(get_season)
    
    print("-> Time features added")
    print(f"   New columns added: year, month, month_name, week, day_of_week,")
    print(f"   day_name, quarter, is_weekend, year_month, hour, time_of_day, season")

    return df


def filter_by_status(df):

    df_completed = df[df['status'] == 'Completed'].copy()
    df_refunded = df[df['status'] == 'Refunded'].copy()
    df_pending = df[df['status'] == 'Pending'].copy()

    print(f"\nOrder Status Breakdown:")
    print(f"   Completed : {len(df_completed):,} ({len(df_completed)/len(df)*100:.1f}%)")
    print(f"   Refunded : {len(df_refunded):,} ({len(df_refunded)/len(df)*100:.1f}%)")
    print(f"   Pending : {len(df_pending):,} ({len(df_pending)/len(df)*100:.1f}%)")

    return df_completed, df_refunded, df_pending


def get_date_filtered_data(df, period='all'):
    """
    Filter data by time period
    
    Parameters:
    -----------
    period: 'today', 'yesterday', '7days', '30days', '90days', '365days', 'this_month', 'this_year'
    """
    today = pd.Timestamp.now().normalize()

    if period == 'today':
        start = today
        end = today
    elif period == 'yesterday':
        start = today - pd.Timedelta(days=1)
        end = today - pd.Timedelta(days=1)
    elif period == '7days':
        start = today - pd.Timedelta(days=7)
        end = today
    elif period == '30days':
        start = today - pd.Timedelta(days=30)
        end = today
    elif period == '90days':
        start = today - pd.Timedelta(days=90)
        end = today
    elif period == '365days':
        start = today - pd.Timedelta(days=365)
        end = today
    elif period == 'this_month':
        start = today.replace(day=1)
        end = today
    elif period == 'this_year':
        start = today.replace(month=1, day=1)
        end = today
    else:
        return df

    mask = (df['date'] >= start) & (df['date'] <= end)
    return df[mask].copy()


def save_processed_data(df_completed, df_refunded, df_pending, df_all):

    os.makedirs('data/processed', exist_ok=True)

    df_completed.to_csv('data/processed/sales_completed.csv', index=False)
    df_refunded.to_csv('data/processed/sales_refunded.csv', index=False)
    df_pending.to_csv('data/processed/sales_pending.csv', index=False)
    df_all.to_csv('data/processed/sales_all.csv', index=False)

    print(f"\n-> Processed files saved:")
    print(f"   data/processed/sales_completed.csv ({len(df_completed):,} rows)")
    print(f"   data/processed/sales_refunded.csv ({len(df_refunded):,} rows)")
    print(f"   data/processed/sales_pending.csv ({len(df_pending):,} rows)")
    print(f"   data/processed/sales_all.csv ({len(df_all):,} rows)")


def process_all_data():
    """
    Run complete data processing pipeline
    """
    print("=" * 50)
    print("RUNNING DATA PROCESSING PIPELINE")
    print("=" * 50)
    
    # Step 1: Load
    df = load_data()
    
    # Step 2: Clean
    df = clean_data(df)
    
    # Step 3: Add features
    df = add_time_features(df)
    
    # Step 4: Separate completed, refunded, and pending orders
    df_completed, df_refunded, df_pending = filter_by_status(df)
    
    # Step 5: Save processed data
    save_processed_data(df_completed, df_refunded, df_pending, df)
    
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  Total Revenue (Completed) : ${df_completed['revenue'].sum():,.2f}")
    print(f"  Total Profit (Completed) : ${df_completed['profit'].sum():,.2f}")
    print(f"  Avg Order Value : ${df_completed['revenue'].mean():,.2f}")
    print(f"  Unique Products : {df_completed['product_name'].nunique()}")
    print(f"  Unique Customers : {df_completed['customer_email'].nunique():,}")
    print(f"  Date Range : {df_completed['date'].min().date()} to {df_completed['date'].max().date()}")

    return df_completed, df_refunded, df_pending, df


if __name__ == '__main__':
    df_completed, df_refunded, df_pending, df_all = process_all_data()