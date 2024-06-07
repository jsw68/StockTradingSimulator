import yfinance as yf
import json

msft = yf.Ticker("msft")
print(json.dumps(msft.info))
