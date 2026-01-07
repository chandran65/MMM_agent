import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration
n_weeks = 104
start_date = datetime(2024, 1, 1)

# Generate dates
dates = [start_date + timedelta(weeks=i) for i in range(n_weeks)]

# Generate Spend Data (Drivers)
np.random.seed(42)
branded_search = np.random.normal(5000, 1000, n_weeks)
nonbranded_search = np.random.normal(8000, 1500, n_weeks)
facebook = np.random.normal(4000, 800, n_weeks)
print_spend = np.random.normal(2000, 500, n_weeks) * np.random.choice([0, 1], n_weeks, p=[0.3, 0.7]) # Flighting
ooh = np.random.normal(3000, 600, n_weeks)
tv = np.random.normal(15000, 3000, n_weeks)
radio = np.random.normal(1000, 200, n_weeks)

# Ensure no negative spend
spend_vars = [branded_search, nonbranded_search, facebook, print_spend, ooh, tv, radio]
for var in spend_vars:
    var[var < 0] = 0

# Generate Sales (Output)
# Base sales
baseline = 20000 
# Trend
trend = np.linspace(0, 5000, n_weeks)
# Seasonality (sine wave)
seasonality = 2000 * np.sin(np.linspace(0, 4*np.pi, n_weeks))

# Marketing Effect (simplified linear combination)
marketing_effect = (
    branded_search * 0.8 + 
    nonbranded_search * 0.5 + 
    facebook * 1.2 + 
    print_spend * 0.3 + 
    ooh * 0.4 + 
    tv * 0.15 + 
    radio * 0.2
)

# Total Sales + Noise
noise = np.random.normal(0, 1000, n_weeks)
sales = baseline + trend + seasonality + marketing_effect + noise

# Create DataFrame
df = pd.DataFrame({
    'Week': dates,
    'sales': sales,
    'branded_search_spend': branded_search,
    'nonbranded_search_spend': nonbranded_search,
    'facebook_spend': facebook,
    'print_spend': print_spend,
    'ooh_spend': ooh,
    'tv_spend': tv,
    'radio_spend': radio
})

# Save to CSV
output_path = 'data/raw/custom_sales_data.csv'
df.to_csv(output_path, index=False)
print(f"Generated {output_path} with {n_weeks} rows.")
