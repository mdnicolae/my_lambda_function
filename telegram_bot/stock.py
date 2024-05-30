import requests
import helper
import finnhub as fh

secret_name = "telegram/bot_token"
secrets = helper.get_secret(secret_name)
STOCK_API_TOKEN = secrets.get('STOCK_API_TOKEN')
FINNHUB_API_TOKEN = secrets.get('FINNHUB_API_TOKEN')

SEARCH_URL = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords=AAPL&apikey={STOCK_API_TOKEN}"


def get_stock_price(ticker):
    try:
        price_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={ticker}&interval=5min&apikey={STOCK_API_TOKEN}"
        response = requests.get(price_url)
        data = response.json()
        # Get the close price from the last 5 minutes interval
        last_refreshed = data['Meta Data']['3. Last Refreshed']
        return (data['Time Series (5min)'][last_refreshed]['4. close'])

    except Exception as e:
        print(f"Error retrieving stock price: {e}")
        return None


def ticker_exists(ticker):
    try:
        search_url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={ticker}&apikey={STOCK_API_TOKEN}"
        response = requests.get(search_url)
        data = response.json()

        if 'bestMatches' not in data:
            return False

        for match in data['bestMatches']:
            if match['1. symbol'] == ticker:
                return True
        return False
    except Exception as e:
        print(f"Error searching stock: {e}")
        return None


def get_stock_price_finnhub(ticker):
    client = fh.Client(api_key=FINNHUB_API_TOKEN)
    try:
        res = client.quote(ticker)
        return res['c']
    except Exception as e:
        print(f"Error retrieving stock price: {e}")
        return None
