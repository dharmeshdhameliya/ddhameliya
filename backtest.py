import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import timedelta

# Define valid usernames and passwords
USER_CREDENTIALS = {
    "1": "1",  # Replace with your desired username and password
    "22": "22"
}

def fetch_stock_data(symbol, start_date, end_date):
    """
    Fetch stock data from Yahoo Finance between start_date and end_date.
    """
    stock_data = yf.download(symbol, start=start_date, end=end_date)
    stock_data = stock_data[stock_data.index.dayofweek < 5]  # Ensure only weekdays (Monday to Friday) are considered
    return stock_data

def process_data(df):
    all_results = {f'trading_day_{i + 1}': {'Yes': 0, 'No': 0, 'Highs': []} for i in range(10)}
    total_symbols = len(df)
    results = []

    for _, row in df.iterrows():
        symbol = row['symbol']
        date = row['date']
        next_day = date + timedelta(days=1)

        # Fetch data for the required date range (next 10 business days)
        stock_data = fetch_stock_data(symbol, date, next_day + timedelta(days=30))

        if not stock_data.empty:
            try:
                # Get closing price for the specified date
                closing_price = stock_data.loc[date.strftime('%Y-%m-%d')]['Close']

                # Initialize results for the current row
                row_result = {
                    'symbol': symbol,
                    'date': date.strftime('%d-%m-%Y'),
                    'closing_price': closing_price
                }

                # Process results for the next 10 trading days
                for i in range(10):
                    try:
                        trading_day = stock_data.index[i + 1]
                        next_day_high = stock_data.iloc[i + 1]['High']
                        result = 'Yes' if closing_price * 1.01 <= next_day_high else 'No'
                        all_results[f'trading_day_{i + 1}'][result] += 1
                    except (KeyError, IndexError):
                        result = 'No'  # If data is missing, consider it as 'No'

                    # Add result to the row
                    row_result[f'trading_day_{i + 1}_date'] = trading_day.strftime('%d-%m-%Y') if trading_day else None
                    row_result[f'trading_day_{i + 1}_high'] = next_day_high if trading_day else None
                    row_result[f'trading_day_{i + 1}_result'] = result

                    # Skip further days if a Yes is achieved
                    if result == 'Yes':
                        break

                results.append(row_result)

            except KeyError:
                row_result = {
                    'symbol': symbol,
                    'date': date.strftime('%d-%m-%Y'),
                    'closing_price': None,
                }
                for i in range(10):
                    row_result[f'trading_day_{i + 1}_date'] = None
                    row_result[f'trading_day_{i + 1}_high'] = None
                    row_result[f'trading_day_{i + 1}_result'] = 'None'
                results.append(row_result)

    # Create DataFrame from results
    results_df = pd.DataFrame(results)

    # Determine the day on which all "No" results turned to "Yes"
    remaining_no = total_symbols  # Start with all symbols
    max_trading_day_yes = None
    for i in range(10):
        trading_day_index = f'trading_day_{i + 1}'
        remaining_no -= all_results[trading_day_index]['Yes']
        if remaining_no == 0:
            max_trading_day_yes = i + 1
            break

    return results_df, all_results, max_trading_day_yes

def sidebar_login():
    """
    Sidebar login page for the Streamlit app.
    """
    st.sidebar.title("Login")

    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.sidebar.success("Login successful!")
        else:
            st.sidebar.error("Invalid username or password. Please try again.")

def main():
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        sidebar_login()
    else:
        st.title("Stock Data Processor")

        # Main page content
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

        if uploaded_file is not None:
            # Read the CSV file
            df = pd.read_csv(uploaded_file, parse_dates=['date'], dayfirst=True)

            # Process the data
            results_df, all_results, max_trading_day_yes = process_data(df)

            # Display results
            st.write("Processed Data:")
            st.dataframe(results_df)

            # Display results and percentages
            if max_trading_day_yes:
                st.write(f"100% Yes results achieved on Trading Day {max_trading_day_yes}")
            else:
                st.write("100% Yes results not achieved within 10 trading days")

            # Show Trading Day Results
            st.write("Trading Day Results:")
            for i in range(10):
                trading_day_index = f'trading_day_{i + 1}'
                day_results = all_results[trading_day_index]
                total_results = day_results['Yes'] + day_results['No']
                yes_percentage = (day_results['Yes'] / total_results * 100) if total_results > 0 else 0
                no_percentage = (day_results['No'] / total_results * 100) if total_results > 0 else 0

                st.write(f"Trading Day {i + 1}:")
                st.write(f"  Total Yes: {day_results['Yes']}")
                st.write(f"  Total No: {day_results['No']}")
                st.write(f"  Yes Percentage: {yes_percentage:.2f}%")
                st.write(f"  No Percentage: {no_percentage:.2f}%")

            # Convert DataFrame to CSV for download
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="Download results as CSV",
                data=csv,
                file_name='processed_stock_data.csv',
                mime='text/csv'
            )

if __name__ == "__main__":
    main()
