import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="Deribit Vol Surface", layout="wide")
st.title("Deribit BTC Volatility Surface Dashboard")
st.markdown("Interactive explorer for 84-day Deribit BTC options surface")

DATA = "data/processed"
df = pd.read_csv(f"{DATA}/BTC_surface_1y.csv")
df['date'] = pd.to_datetime(df['datetime']).dt.date

st.sidebar.header("Filters")
available_dates = sorted(df['date'].unique(), reverse=True)
selected_date = st.sidebar.selectbox("Date", available_dates[:30])
df_filtered = df[df['date'] == selected_date].copy()

if len(df_filtered) == 0:
    st.warning("No data"); st.stop()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Spot", f"${df_filtered['underlying_close'].iloc[0]:,.0f}")
with col2:
    atm_iv = df_filtered[df_filtered['delta'].abs() < 0.1]['implied_volatility'].mean()
    st.metric("ATM IV", f"{atm_iv*100:.1f}%" if pd.notna(atm_iv) else "N/A")
with col3:
    st.metric("Options", len(df_filtered))
with col4:
    st.metric("Expiries", df_filtered['expiry_datetime'].nunique())

st.subheader("Implied Volatility Smile")
expiries = sorted(df_filtered['expiry_datetime'].unique())
selected_expiry = st.selectbox("Expiry", expiries)
exp_df = df_filtered[df_filtered['expiry_datetime'] == selected_expiry].sort_values('strike')

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(exp_df['strike'], exp_df['implied_volatility'], 'o-', color='purple')
ax.set_xlabel('Strike'); ax.set_ylabel('IV'); ax.grid(True, alpha=0.3)
st.pyplot(fig)

st.subheader("Options Chain")
st.dataframe(exp_df[['strike', 'option_type', 'implied_volatility', 'delta']].head(20))

st.caption("Data: Deribit API | github.com/jaswanthobbu645-hub/deribit-volatility-surface")