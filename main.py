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
    Queries the universal v3 snapshot endpoint which works reliably 
    across basic/developer subscription access tiers.
    """
    target_tickers = tickers.split(",") if tickers else DEFAULT_WATCHLIST
    ticker_string = ",".join(target_tickers)
    
    # UPDATED ENDPOINT: Universal v3 snapshot mapping
    url = "https://polygon.io"
    
    params = {
        "ticker.anyof": ticker_string, # Correct parameter syntax for grouped tracking
        "apiKey": MASSIVE_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            
            # Diagnostic trap: If it fails, show the exact error from Massive
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Massive API returned code {response.status_code}: {response.text}"
                )
                
            raw_data = response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Failed to reach Massive: {str(e)}")
            
    # Parse the clean v3 layout
    compact_results = []
    results_list = raw_data.get("results", [])
    
    if not results_list:
        return {"market_conditions": "No real-time data returned for these tickers. Market may be closed or key invalid."}

    for item in results_list:
        ticker_symbol = item.get("ticker", "UNKNOWN")
        
        # Pull key market data points cleanly
        spot_price = item.get("price", "N/A")
        todays_change_pct = item.get("todays_change_percent", 0.0)
        volume = item.get("volume", 0)
        
        compact_string = (
            f"{ticker_symbol}: Spot ${spot_price} | "
            f"Daily Change {todays_change_pct:.2f}% | "
            f"Vol {volume:,}"
        )
        compact_results.append(compact_string)
        
    return {"market_conditions": "\n".join(compact_results)}
