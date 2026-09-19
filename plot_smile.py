import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data you just saved
df = pd.read_csv('btc_options_snapshot.csv')

print(f"📊 Loaded {len(df)} options.")

# Separate Calls and Puts
calls = df[df['kind'] == 'Call']
puts = df[df['kind'] == 'Put']

# Create the plot
plt.figure(figsize=(12, 6))

# Plot Calls
plt.scatter(calls['strike'], calls['mark_iv'], color='green', label='Calls', alpha=0.6, s=30)

# Plot Puts
plt.scatter(puts['strike'], puts['mark_iv'], color='red', label='Puts', alpha=0.6, s=30)

# Labels and Title
plt.xlabel('Strike Price (USD)', fontsize=12)
plt.ylabel('Implied Volatility (%)', fontsize=12)
plt.title('BTC Implied Volatility Smile', fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)

# Save the plot
plt.savefig('volatility_smile.png', dpi=300)
print("✅ Plot saved as 'volatility_smile.png'")

# Show the plot (this will pop up in a new window)
plt.show()