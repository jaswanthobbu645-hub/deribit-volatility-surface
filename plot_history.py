import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 1. Load the CORRECT file
df = pd.read_csv('metrics_history.csv')

# 2. Force pandas to read the dates as actual dates
df['date'] = pd.to_datetime(df['date'])

# 3. Sort chronologically (crucial for time series)
df = df.sort_values('date')

# 4. Plot the line with dots
plt.figure(figsize=(12, 6))
plt.plot(df['date'], df['risk_reversal'], marker='o', linestyle='-', color='blue', label='Risk Reversal (Skew)')

# 5. Format the axes
plt.title('BTC 25-delta Risk Reversal Over Time')
plt.xlabel('Date')
plt.ylabel('Risk Reversal (%)')
plt.grid(True, alpha=0.3)
plt.axhline(0, color='red', linestyle='--', alpha=0.5)
plt.legend()

# 6. FORCE the x-axis to zoom in on your actual data range
plt.xlim(df['date'].min() - pd.Timedelta(days=1), df['date'].max() + pd.Timedelta(days=1))

# 7. Rotate the dates so they don't overlap
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.gcf().autofmt_xdate()

plt.tight_layout()
plt.savefig('skew_history.png', dpi=300)
plt.show()