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
    Queries the official Massive v3 snapshot endpoint using the mandatory 
    Bearer Token Header authentication method to eliminate 401 errors.
    """
    target_tickers = tickers.split(",") if tickers else DEFAULT_WATCHLIST
    ticker_string = ",".join(target_tickers)
    
    url = "https://massive.com"
    
    # We pass the focus tickers here
    params = {
        "ticker": ticker_string
    }
    
    # FIX: Pass the key securely inside the Headers dictionary, NOT the URL parameters
    headers = {
        "Authorization": f"Bearer {MASSIVE_API_KEY}"
    }
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            # We explicitly pass the url, params, AND headers to Massive
            response = await client.get(url, params=params, headers=headers, timeout=10.0)
            
            # Diagnostic trap: If it still fails, bubble up the exact response text
            if response.status_code != 200:
                return {
                    "market_conditions": f"Massive API returned code {response.status_code}. Detail: {response.text}"
                }
                
            raw_data = response.json()
        except Exception as e:
            return {"market_conditions": f"Failed to connect to Massive servers: {str(e)}"}
            
    # Parse the v3 layout defensively
    compact_results = []
    results_list = raw_data.get("results", [])
    
    if not results_list:
        return {"market_conditions": "No live tickers returned. Check your capitalization or ticker strings."}

    for item in results_list:
        ticker_symbol = item.get("ticker", "UNKNOWN")
        
        # Pull key market data points cleanly from the payload
        spot_price = item.get("price") or item.get("session", {}).get("close") or "N/A"
        todays_change_pct = item.get("todays_change_percent") or item.get("todaysChangePerc") or 0.0
        volume = item.get("volume") or item.get("session", {}).get("volume") or 0
        
        try:
            pct_val = float(todays_change_pct)
            pct_str = f"{pct_val:.2f}%"
        except:
            pct_str = "0.00%"
            
        compact_string = f"{ticker_symbol}: Spot ${spot_price} | Daily Change {pct_str} | Vol {volume:,}"
        compact_results.append(compact_string)
        
    return {"market_conditions": "\n".join(compact_results)}
