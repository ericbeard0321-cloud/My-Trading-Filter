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
    Diagnostic wrapper that safely logs upstream HTTP status and 
    raw response text before attempting to parse raw JSON structures.
    """
    target_tickers = tickers.split(",") if tickers else DEFAULT_WATCHLIST
    ticker_string = ",".join(target_tickers)
    
    url = "https://massive.com"
    
    params = {
        "ticker": ticker_string
    }
    
    headers = {
        "Authorization": f"Bearer {MASSIVE_API_KEY}"
    }
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=10.0)
            
            # --- THE DIAGNOSTIC TRAP ---
            # If Massive sends back anything other than a clean 200 OK, we stop 
            # and bubble up the raw HTML text page directly to ChatGPT's window.
            if response.status_code != 200:
                # Truncate to 300 characters to keep it clean but readable
                raw_text_preview = response.text[:300].replace('\n', ' ')
                return {
                    "market_conditions": (
                        f"🚨 DIAGNOSTIC FEEDBACK | Upstream Status: {response.status_code} | "
                        f"Raw Response: {raw_text_preview}..."
                    )
                }
                
            # If it is 200 OK, we can safely attempt to parse it without crashing
            raw_data = response.json()
            
        except Exception as e:
            return {"market_conditions": f"Network transmission error: {str(e)}"}
            
    # Parse the v3 layout if we successfully bypass the diagnostic trap
    compact_results = []
    results_list = raw_data.get("results", [])
    
    if not results_list:
        return {"market_conditions": "No live tickers returned. Check market hours."}

    for item in results_list:
        ticker_symbol = item.get("ticker", "UNKNOWN")
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
