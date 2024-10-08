import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# ===================== Streamlit Application =====================
st.set_page_config(page_title="Portfolio vs Index Comparison by GeekendZone", page_icon="favicon.ico")

st.header("Portfolio vs Index Comparison by GeekendZone:sunglasses:", divider="gray")

# Inputs for the user
st.sidebar.header("Input Parameters")

# Ticker input for a stock
ticker_list = st.sidebar.text_input("Enter the ticker symbols (separated by comma)", "AAPL, MSFT, GOOGL, AMZN")
tickers = [x.strip() for x in ticker_list.split(',')]

# Input for Index Fund (like SPY or QQQ)
index_ticker = st.sidebar.text_input("Enter index ticker (e.g., SPY, QQQ)", "SPY")

# Input for start and end dates
start_date = st.sidebar.date_input("Start Date", value=datetime(2014, 1, 1))
end_date = st.sidebar.date_input("End Date", value=datetime(2024, 9, 1))

# Initial investment amount and contribution
initial_amount = st.sidebar.number_input("Initial Investment (in USD)", value=1000, step=100)
contribution = st.sidebar.number_input("Monthly or Weekly Contribution (in USD)", value=800, step=100)

# Contribution frequency selection
contrib_freq = st.sidebar.selectbox("Contribution Frequency", ["Daily", "Weekly", "Monthly", "Annually"])

# Customizable interval selection
interval = st.sidebar.selectbox("Select Data Interval", ["1d", "1wk", "1mo"], index=2)

# Function to handle contribution frequency
def convert_contribution_frequency(contribution, freq):
    if freq == "Daily":
        return contribution * 30  # Approx. 30 days per month
    elif freq == "Weekly":
        return contribution * 4.33  # Approx. 4.33 weeks per month
    elif freq == "Annual":
        return contribution / 12  # Annual to monthly
    return contribution  # For monthly

# Function to download data (use the selected interval now)
@st.cache_data
def download_data(tickers, start, end, interval):
    data = yf.download(tickers, start=start, end=end, interval=interval, auto_adjust=True)
    return data['Close']

# Simulation logic for portfolio with selected stocks and initial investment
def simulate_portfolio(stock_prices, total_contribution, contrib_freq, initial_investment):
    months = stock_prices.index
    num_tickers = len(stock_prices.columns)
    monthly_contribution = convert_contribution_frequency(total_contribution, contrib_freq) / num_tickers

    # Dictionary to store number of shares bought for each stock
    shares_bought = {ticker: np.zeros(len(stock_prices)) for ticker in stock_prices.columns}
    leftover_cash = {ticker: 0 for ticker in stock_prices.columns}

    portfolio_value_over_time = []

    # Initial Investment Handling
    initial_per_stock = initial_investment / num_tickers

    for ticker in stock_prices.columns:
        initial_shares = initial_per_stock // stock_prices[ticker].iloc[0]
        leftover_cash[ticker] = initial_per_stock % stock_prices[ticker].iloc[0]
        shares_bought[ticker][0] = initial_shares

    for i in range(1, len(months)):
        portfolio_value = 0
        for ticker in stock_prices.columns:
            price = stock_prices[ticker].iloc[i]
            total_money = monthly_contribution + leftover_cash[ticker]
            shares_to_buy = total_money // price
            leftover_cash[ticker] = total_money % price
            shares_bought[ticker][i] = shares_bought[ticker][i-1] + shares_to_buy

            # Holding value of all shares for this stock
            holding_value = shares_bought[ticker][i] * price
            portfolio_value += holding_value

        portfolio_value_over_time.append(portfolio_value)

    return pd.DataFrame({'Portfolio Value': portfolio_value_over_time}, index=months[1:])

# Simulation logic for index investment like SPY with initial investment
def simulate_index_investment(index_prices, total_contribution, contrib_freq, initial_investment):
    months = index_prices.index
    monthly_contribution = convert_contribution_frequency(total_contribution, contrib_freq)

    shares_bought = np.zeros(len(index_prices))
    leftover_cash = 0
    portfolio_value_over_time = []

    # Initial Investment Handling
    initial_shares = initial_investment // index_prices.iloc[0]
    leftover_cash = initial_investment % index_prices.iloc[0]
    shares_bought[0] = initial_shares

    # Simulate periodic investments
    for i in range(1, len(months)):
        price = index_prices.iloc[i]
        total_money = monthly_contribution + leftover_cash
        shares_to_buy = total_money // price
        leftover_cash = total_money % price
        shares_bought[i] = shares_bought[i-1] + shares_to_buy

        holding_value = shares_bought[i] * price
        portfolio_value_over_time.append(holding_value)

    return pd.DataFrame({'Index Value': portfolio_value_over_time}, index=months[1:])

# ============================ MAIN LOGIC ==========================

with st.spinner('Fetching data and performing computation...'):
    # Download data for selected stocks and index
    stock_prices = download_data(tickers, start_date, end_date, interval)
    index_prices = download_data(index_ticker, start_date, end_date, interval)

    # Error Handling
    if stock_prices.empty or index_prices.empty:
        st.error("Error fetching data. Please check your input tickers and try again.")
        st.stop()

# Simulating the investments
individual_portfolio_df = simulate_portfolio(stock_prices, contribution, contrib_freq, initial_amount)
index_portfolio_df = simulate_index_investment(index_prices, contribution, contrib_freq, initial_amount)

# == Visualization ==
st.subheader(f"Performance of Portfolio vs {index_ticker} Index Fund")

# Matplotlib figure creation
fig, ax = plt.subplots(figsize=(10, 6))
ax.set_title('Consolidated Portfolio vs Index Fund Over Time')

# Plotting performance of the individual stocks portfolio
ax.plot(individual_portfolio_df['Portfolio Value'], label=f'Portfolio (Selected Stocks)', color='blue', linewidth=2)

# Plotting performance of the index fund investment (e.g., SPY)
ax.plot(index_portfolio_df['Index Value'], label=f'{index_ticker} Index Fund', color='green', linewidth=2)

# Add labels, legend, and grid
ax.legend()
ax.set_xlabel('Time')
ax.set_ylabel('Portfolio Value (USD)')
ax.grid(True)

# Display the plot in Streamlit
st.pyplot(fig)

# Showing the final portfolio values at the end date
st.subheader("Final Portfolio Values")
final_stock_value = individual_portfolio_df['Portfolio Value'].iloc[-1]
final_index_value = index_portfolio_df['Index Value'].iloc[-1]
st.write(f"Final Value of Selected Stocks Portfolio: ${final_stock_value:,.2f}")
st.write(f"Final Value of {index_ticker} Index Fund: ${final_index_value:,.2f}")

# Download option for the portfolio results as a CSV
st.download_button(
    label="Download Portfolio Data (CSV)",
    data=individual_portfolio_df.to_csv(),
    file_name='portfolio_data.csv',
    mime='text/csv',
)

st.write("Thanks for using my simulator, Jose Cedeno!")
