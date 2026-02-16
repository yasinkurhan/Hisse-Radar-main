
import borsapy as bp
import pandas as pd

try:
    print("Initializing Borsapy...")
    # borsapy usually has Ticker class
    try:
        ticker = bp.Ticker('THYAO')
        print("Using bp.Ticker('THYAO')")
    except AttributeError:
        print("bp.Ticker not found, exploring bp...")
        print(dir(bp))
        exit()
    
    print("Fetching news...")
    news = ticker.news
    
    if news is None:
        print("No news returned (None)")
    else:
        print(f"Type: {type(news)}")
        if isinstance(news, pd.DataFrame):
            print("Columns:", news.columns.tolist())
            print("Head:\n", news.head())
            if not news.empty:
                print("First row dict:", news.iloc[0].to_dict())
        elif isinstance(news, list):
            print(f"List length: {len(news)}")
            if len(news) > 0:
                print("First item:", news[0])
        else:
            print("Content:", news)
            
except Exception as e:
    print(f"Error: {e}")
