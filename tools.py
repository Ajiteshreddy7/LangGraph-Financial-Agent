import yfinance as yf
import pandas as pd
import pandas_ta as ta
from langchain_core.tools import tool
from typing import List, Dict
import datetime

# --- Tool 1: Get Exact Current Price ---
@tool
def get_current_stock_price(ticker: str):
    """Fetches the most recent, near real-time stock price for a given ticker."""
    stock = yf.Ticker(ticker)
    price = stock.info.get("regularMarketPrice")
    if price:
        return {"price": price}
    else:
        try:
            return {"price": stock.history(period="1d")['Close'].iloc[-1]}
        except IndexError:
            return {"error": f"Could not fetch current price for {ticker}. The ticker may be invalid or delisted."}

# --- Tool 2: Get Full In-Depth Analysis ---
# (Helper functions for this tool remain the same)
def _get_stock_price_data(ticker: str, period: str = "1y"):
    """Internal helper to fetch historical price data."""
    return yf.Ticker(ticker).history(period=period)

def _get_historical_performance(ticker: str):
    """Internal helper to calculate historical returns."""
    stock = yf.Ticker(ticker)
    hist = stock.history(period="5y")
    if hist.empty: return {}
    price_today = hist['Close'].iloc[-1]
    current_year = datetime.date.today().year
    try:
        price_ytd_start = hist[hist.index.year == current_year]['Close'].iloc[0]
        ytd_return = (price_today - price_ytd_start) / price_ytd_start
    except IndexError:
        ytd_return = None
    price_1y_ago = hist['Close'].iloc[-252] if len(hist) > 252 else None
    one_year_return = (price_today - price_1y_ago) / price_1y_ago if price_1y_ago else None
    return {
        "52_week_high": hist['High'][-252:].max() if len(hist) > 252 else None,
        "52_week_low": hist['Low'][-252:].min() if len(hist) > 252 else None,
        "ytd_return_percentage": ytd_return * 100 if ytd_return is not None else "N/A",
        "1y_return_percentage": one_year_return * 100 if one_year_return is not None else "N/A",
    }

def _calculate_technical_indicators(price_data: pd.DataFrame):
    if price_data.empty: return {}
    indicators = {}
    try:
        indicators["rsi"] = price_data.ta.rsi().iloc[-1]
        macd = price_data.ta.macd()
        indicators["macd"] = macd['MACD_12_26_9'].iloc[-1]
        indicators["macd_signal"] = macd['MACDs_12_26_9'].iloc[-1]
    except Exception as e: print(f"Could not calculate indicators: {e}")
    return indicators

def _get_financial_metrics(ticker: str):
    stock_info = yf.Ticker(ticker).info
    return {
        "price_to_earnings_ratio": stock_info.get("trailingPE"),
        "debt_to_equity_ratio": stock_info.get("debtToEquity"),
        "profit_margins": stock_info.get("profitMargins"),
        "market_cap": stock_info.get("marketCap"),
    }

@tool
def get_full_stock_analysis(ticker: str):
    """Performs a full, in-depth stock analysis."""
    print(f"--- Performing full analysis for {ticker} ---")
    price_data = _get_stock_price_data(ticker)
    return {
        "historical_performance": _get_historical_performance(ticker),
        "technical_indicators": _calculate_technical_indicators(price_data),
        "financial_metrics": _get_financial_metrics(ticker)
    }

# --- Tool 3: Compare Multiple Stocks ---
def _get_comparison_metrics(ticker: str):
    """Internal helper that fetches key metrics for comparison."""
    stock_info = yf.Ticker(ticker).info
    return {
        "Market Cap": stock_info.get("marketCap"),
        "P/E Ratio": stock_info.get("trailingPE"),
        "Profit Margins": stock_info.get("profitMargins"),
        "Debt-to-Equity": stock_info.get("debtToEquity"),
    }

@tool
def compare_stocks(tickers: List[str]):
    """Compares key financial metrics for a list of stock tickers."""
    print(f"--- Comparing stocks: {tickers} ---")
    comparison_data = {}
    for ticker in tickers:
        comparison_data[ticker.upper()] = _get_comparison_metrics(ticker)
    return comparison_data

# --- Tool 4: Human-in-the-Loop ---
@tool
def request_user_clarification(question: str, options: List[str] = None):
    """
    Asks the user for clarification when the query is ambiguous.
    Call this tool when you are unsure about a ticker or the user's intent.
    :param question: The question to ask the user.
    :param options: A list of options for the user to choose from, if applicable.
    """
    # This tool's logic is handled in the agent graph. It returns the question
    # to be displayed in the UI.
    return {"question": question, "options": options or []}


# --- Final List of Tools for the Agent ---
tools = [
    get_current_stock_price, 
    get_full_stock_analysis, 
    compare_stocks,
    request_user_clarification
]

