# data_generator.py
# This creates realistic fake sales data for our dashboard
# In real world, this would connect to actual database

import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import os

# Initialize faker for generating fake names, emails etc
fake = Faker()

# Set seed for reproducibility (same data every time)
np.random.seed(42)
random.seed(42)

def generate_sales_data(num_records=5000, start_date='2023-01-01'):
    """
    Generate realistic sales transaction data
    
    Parameters:
    -----------
    num_records : int - number of sales records to generate
    start_date : str - when sales data starts from
    
    Returns:
    --------
    DataFrame with all sales transactions
    """
    print(f"Generating {num_records} sales records...")

    # ==============================================
    # Define Our Business Data
    # ==============================================

    # Products our business sells
    products = {
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
    }

    # Sales channels
    channels = {
        'Website': 35,
        'Mobile App': 25,
        'Amazon': 20,
        'Social Media': 12,
        'Email Campaign': 8,
    }

    # Customer Locations
    cities = {
        'New York': {'state': 'NY', 'region': 'Northeast'},
        'Los Angeles': {'state': 'CA', 'region': 'West'},
        'Chicago': {'state': 'IL', 'region': 'Midwest'},
        'Houston': {'state': 'TX', 'region': 'South'},
        'Phoenix': {'state': 'AZ', 'region': 'West'},
        'Philadelphia': {'state': 'PA', 'region': 'Northeast'},
        'San Antonio': {'state': 'TX', 'region': 'South'},
        'San Diego': {'state': 'CA', 'region': 'West'},
        'Dallas': {'state': 'TX', 'region': 'South'},
        'Seattle': {'state': 'WA', 'region': 'West'},
        'Denver': {'state': 'CO', 'region': 'West'},
        'Boston': {'state': 'MA', 'region': 'Northeast'},
        'Atlanta': {'state': 'GA', 'region': 'South'},
        'Miami': {'state': 'FL', 'region': 'South'},
        'Minneapolis': {'state': 'MN', 'region': 'Midwest'},
    }

    # Payment methods
    payment_methods = ['Credit Card', 'Debit Card', 'PayPal', 'Apple Pay', 'Bank Transfer']

    # Order status
    statuses = ['Completed', 'Completed', 'Completed', 'Refunded', 'Pending']
    # More completed = more realistic

    # Extract channel names and weights for random selection
    channel_names = list(channels.keys())
    channel_weights = list(channels.values())

    # ==============================================
    # Generate Date Range
    # ==============================================

    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.now()
    date_range = (end - start).days

    # ==============================================
    # Create Records
    # ==============================================

    records = []

    # Track customers (some will be returning)
    customer_pool = [fake.email() for _ in range(int(num_records * 0.6))]

    for i in range(num_records):

        # Generate random date (with trends - more sales on weekends)
        random_days = random.randint(0, date_range)
        date = start + timedelta(days=random_days)

        # Add time (more sales during lunch and evening)
        hour = random.choices(
            range(24),
            weights=[1,1,1,1,1,2,3,4,5,6,7,8,9,10,9,8,10,12,11,9,7,5,3,2]
        )[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        full_datetime = date.replace(hour=hour, minute=minute, second=second)

        # Pick a product
        product_name = random.choice(list(products.keys()))
        product_info = products[product_name]

        # Pick quantity (most people buy 1, some buy more)
        quantity = random.choices([1, 2, 3, 4, 5], weights=[60, 25, 10, 3, 2])[0]

        # Calculate prices
        unit_price = product_info['price']
        unit_cost = product_info['cost']

        # Apply random discount sometimes
        discount_pct = random.choices(
            [0, 5, 10, 15, 20, 25],
            weights=[50, 15, 15, 10, 7, 3]
        )[0]

        gross_revenue = unit_price * quantity
        discount_amount = gross_revenue * (discount_pct / 100)
        revenue = gross_revenue - discount_amount
        cost = unit_cost * quantity
        profit = revenue - cost
        profit_margin = (profit / revenue * 100) if revenue > 0 else 0

        # Pick location
        city = random.choice(list(cities.keys()))
        city_info = cities[city]

        # Customer (mix of new and returning)
        if random.random() < 0.4:  # 40% returning customers
            customer_email = random.choice(customer_pool)
            customer_type = 'Returning'
        else:
            customer_email = fake.email()
            customer_pool.append(customer_email)
            customer_type = 'New'
        
        customer_name = fake.name()

        # Status
        status = random.choices(
            ['Completed', 'Refunded', 'Pending'],
            weights=[85, 10, 5]
        )[0]

        channel = random.choices(channel_names, weights=channel_weights)[0]
        payment = random.choice(payment_methods)

        # Create record
        record = {
            'order_id': f'ORD-{10000 + i}',
            'date': full_datetime.strftime('%Y-%m-%d'),
            'time': full_datetime.strftime('%H:%M:%S'),
            'datetime': full_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            'product_name': product_name,
            'category': product_info['category'],
            'quantity': quantity,
            'unit_price': round(unit_price, 2),
            'unit_cost':        round(unit_cost, 2),
            'discount_pct':     discount_pct,
            'discount_amount':  round(discount_amount, 2),
            'gross_revenue':    round(gross_revenue, 2),
            'revenue':          round(revenue, 2),
            'cost':             round(cost, 2),
            'profit':           round(profit, 2),
            'profit_margin':    round(profit_margin, 2),
            'channel':          channel,
            'payment_method':   payment,
            'status':           status,
            'customer_email':   customer_email,
            'customer_name':    customer_name,
            'customer_type':    customer_type,
            'city':             city,
            'state':            city_info['state'],
            'region':           city_info['region'],
        }
        
        records.append(record)
        
        # Show progress
        if (i + 1) % 1000 == 0:
            print(f"  Generated {i + 1} records...")


    # Convert to DataFrame
    df = pd.DataFrame(records)
    
    # Sort by date
    df = df.sort_values('datetime').reset_index(drop=True)
    
    print(f"\n-> Generation complete!")
    print(f"   Total Records : {len(df):,}")
    print(f"   Date Range : {df['date'].min()} to {df['date'].max()}")
    print(f"   Total Revenue : ${df[df['status']=='Completed']['revenue'].sum():,.2f}")
    print(f"   Total Orders : {len(df):,}")
    print(f"   Products : {df['product_name'].nunique()}")
    print(f"   Unique Customers : {df['customer_email'].nunique():,}")

    return df


def save_data(df, filename='sales_data.csv'):
    """Save data to CSV file"""
    
    filepath = os.path.join('data', 'raw', filename)
    df.to_csv(filepath, index=False)
    print(f"-> Data saved to {filepath}")
    return filepath


# Run this file directly to generate data
if __name__ == '__main__':
    df = generate_sales_data(num_records=5000, start_date='2023-01-01')
    save_data(df)
    
    # Preview the data
    print("\n📊 Data Preview:")
    print(df.head(3).to_string())
    print(f"\n📋 Columns: {list(df.columns)}")
    print(f"\n📈 Data Shape: {df.shape}")