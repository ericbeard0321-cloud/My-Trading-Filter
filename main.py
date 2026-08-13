import os
import httpx
from fastapi import FastAPI, HTTPException, Query
from typing import List

app = FastAPI(title="Massive Data Compactor for ChatGPT")

# SECURE STORAGE: Set these in your hosting environment variables
MASSIVE_API_KEY = os.getenv("MASSIVE_API_KEY", "YOUR_ACTUAL_MASSIVE_KEY")
MASSIVE_BASE_URL = "https://massive.com" # Base server URL for the data pipeline

# YOUR FIXED WATCHLIST: Limits focus to a small group of highly active assets
DEFAULT_WATCHLIST = ["SPY", "QQQ", "AAPL", "NVDA", "TSLA", "MSFT", "AMZN"]

@app.get("/market-conditions")
async def get_compact_conditions(
    tickers: str = Query(None, description="Comma-separated tickers, e.g., AAPL,NVDA")
):
    """
    Fetches real-time snapshots from Massive, strips out data waste, 
    and returns a tiny, cost-efficient payload optimized for ChatGPT.
    """
    # 1. Determine the small focus group
    target_tickers = tickers.split(",") if tickers else DEFAULT_WATCHLIST
    ticker_string = ",".join(target_tickers)
    
    # 2. Query Massive's snapshot endpoint
    # (Using the unified snapshot route to get data for our specific group)
    url = f"{MASSIVE_BASE_URL}/v2/snapshot/locale/us/markets/stocks/tickers"
    params = {
        "tickers": ticker_string,
        "apiKey": MASSIVE_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed fetching from Massive API")
            raw_data = response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")
            
    # 3. THE COMPACTOR: Strip away thousands of lines of data waste
    # We extract ONLY critical market condition signals
    compact_results = []
    
    # Massive returns a 'tickers' list or 'results' array depending on endpoint setup
    tickers_list = raw_data.get("tickers", raw_data.get("results", []))
    
    for item in tickers_list:
        ticker_symbol = item.get("ticker")
        
        # Isolate nested structures cleanly
        todays_change_pct = item.get("todaysChangePerc", 0)
        day_data = item.get("day", {})
        min_data = item.get("min", {}) # Most recent minute bar
        
        # Build a highly compressed string for ChatGPT
        # This uses roughly 90% fewer tokens than raw JSON
        compact_string = (
            f"{ticker_symbol}: Spot ${min_data.get('c', 'N/A')} | "
            f"Daily Change {todays_change_pct:.2f}% | "
            f"Vol {day_data.get('v', 0):,}"
        )
        compact_results.append(compact_string)
        
    # 4. Return clean, newline-separated text that LLMs read perfectly
    return {"market_conditions": "\n".join(compact_results)}
