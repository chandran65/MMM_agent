"""
Sample Data Generator

Generates synthetic sales and marketing spend data for testing the MMX pipeline.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_sample_data(
    start_date: str = "2022-01-01",
    n_weeks: int = 104,
    n_categories: int = 10,
    channels: list = None,
    output_path: str = "data/raw/sales_data.csv"
):
    """
    Generate synthetic MMX data.
    
    Args:
        start_date: Start date for time series
        n_weeks: Number of weeks to generate
        n_categories: Number of sub-categories
        channels: List of marketing channels
        output_path: Where to save the data
    """
    if channels is None:
        channels = ['TV', 'Digital', 'Print', 'OOH', 'Radio']
    
    # Generate dates
    start = datetime.strptime(start_date, "%Y-%m-%d")
    dates = [start + timedelta(weeks=i) for i in range(n_weeks)]
    
    data = []
    
    for cat_idx in range(n_categories):
        cat_name = f"Category_{chr(65 + cat_idx)}"  # A, B, C, ...
        
        # Base sales level for this category
        base_sales = np.random.uniform(30000, 80000)
        
        for week_idx, date in enumerate(dates):
            # Trend component
            trend = week_idx * np.random.uniform(50, 200)
            
            # Seasonality (yearly)
            seasonality = 5000 * np.sin(2 * np.pi * week_idx / 52)
            
            # Marketing spend
            spend = {}
            total_spend = 0
            for channel in channels:
                channel_spend = np.random.uniform(5000, 25000)
                spend[f'{channel.lower()}_spend'] = channel_spend
                total_spend += channel_spend
            
            # Marketing effect (with diminishing returns)
            marketing_effect = 0
            for channel in channels:
                channel_spend = spend[f'{channel.lower()}_spend']
                # Hill saturation
                alpha = 2.0
                gamma = 15000
                saturated = (channel_spend ** alpha) / (gamma ** alpha + channel_spend ** alpha)
                marketing_effect += saturated * 20000  # Scale factor
            
            # Total sales
            noise = np.random.normal(0, 3000)
            total_sales = base_sales + trend + seasonality + marketing_effect + noise
            total_sales = max(total_sales, 0)  # No negative sales
            
            # Volume (assume average price)
            avg_price = np.random.uniform(40, 60)
            total_volume = total_sales / avg_price
            
            row = {
                'date': date.strftime('%Y-%m-%d'),
                'sub_category': cat_name,
                'sales': total_sales,
                'total_sales': total_sales,
                'total_volume': total_volume,
                **spend
            }
            
            data.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"Generated {len(df)} rows of sample data")
    print(f"Saved to: {output_path}")
    print(f"\nColumns: {list(df.columns)}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Categories: {df['sub_category'].unique().tolist()}")
    
    return df


def generate_events_data(output_path: str = "data/raw/events.csv"):
    """Generate sample events data."""
    events = [
        {'event_date': '2022-06-15', 'event_name': 'Summer Sale', 'type': 'promotion'},
        {'event_date': '2022-11-25', 'event_name': 'Black Friday', 'type': 'promotion'},
        {'event_date': '2022-12-25', 'event_name': 'Christmas', 'type': 'holiday'},
        {'event_date': '2023-01-01', 'event_name': 'New Year', 'type': 'holiday'},
        {'event_date': '2023-07-04', 'event_name': 'Independence Day', 'type': 'holiday'},
    ]
    
    df = pd.DataFrame(events)
    
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"Generated {len(df)} events")
    print(f"Saved to: {output_path}")
    
    return df


if __name__ == '__main__':
    print("Generating sample data for MMX POC...\n")
    
    # Generate main sales data
    sales_df = generate_sample_data(
        start_date="2022-01-01",
        n_weeks=104,  # 2 years
        n_categories=10,
        channels=['TV', 'Digital', 'Print', 'OOH', 'Radio']
    )
    
    print("\n" + "="*60 + "\n")
    
    # Generate events data
    events_df = generate_events_data()
    
    print("\n" + "="*60)
    print("Sample data generation complete!")
    print("Run the pipeline with:")
    print("  python -m cli.run_pipeline --input data/raw/sales_data.csv --auto-approve")
