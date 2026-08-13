import os
import httpx
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="Massive Data Compactor for ChatGPT")

# SECURE STORAGE: Fetches your key from Render Environment Variables
MASSIVE_API_KEY = os.getenv("MASSIVE_API_KEY", "YOUR_ACTUAL_MASSIVE_KEY")

# Fixed fallback group to monitor
DEFAULT_WATCHLIST = ["SPY", "QQQ", "AAPL", "NVDA", "TSLA"]

@app.get("/market-conditions")
async def get_compact_conditions(
    tickers: str = Query(None, description="Comma-separated tickers, e.g., AAPL,NVDA")
):
    """
    Queries Massive with cross-compatible mapping to stop 500 crashes
    """
    target_tickers = tickers.split(",") if tickers else DEFAULT_WATCHLIST
    ticker_string = ",".join(target_tickers)
    
    # Standard v3 snapshot URL
    url = "https://api.polygon.io/v3/snapshot"
    
    params = {
        "ticker.anyof": ticker_string,
        "apiKey": MASSIVE_API_KEY
    }
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            
            if response.status_code != 200:
                return {
                    "market_conditions": f"Massive API connection error. Status Code: {response.status_code}"
                }
                
            raw_data = response.json()
        except Exception as e:
            return {"market_conditions": f"Failed to connect to data provider: {str(e)}"}
            
    # Parse the v3 layout defensively without allowing crashes
    compact_results = []
    results_list = raw_data.get("results", [])
    
    if not results_list:
        return {"market_conditions": "No live tickers returned. Check market hours or API Key permissions."}

    for item in results_list:
        # Prevent crashes if fields are missing or structured differently
        ticker_symbol = item.get("ticker", "UNKNOWN")
        
        # Massive's universal v3 snapshot can place variables inside the main dictionary
        # or inside a sub-dictionary depending on tier limits. We check both paths:
        spot_price = item.get("price") or item.get("session", {}).get("close") or "N/A"
        
        todays_change_pct = item.get("todays_change_percent") or item.get("todaysChangePerc") or 0.0
        
        volume = item.get("volume") or item.get("session", {}).get("volume") or 0
        
        # Safely convert to float for text formatting strings
        try:
            pct_val = float(todays_change_pct)
            pct_str = f"{pct_val:.2f}%"
        except:
            pct_str = "0.00%"
            
        compact_string = f"{ticker_symbol}: Spot ${spot_price} | Daily Change {pct_str} | Vol {volume:,}"
        compact_results.append(compact_string)
        
    return {"market_conditions": "\n".join(compact_results)}
