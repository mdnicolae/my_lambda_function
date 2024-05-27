import json
import os
import requests
import boto3
from datetime import datetime

# Constants
DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE')
STOCK_API_URL = "https://api.example.com/stocks"  # Replace with actual stock API

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
secretsmanager = boto3.client('secretsmanager')
table = dynamodb.Table(DYNAMODB_TABLE)


def get_secret(secret_name):
    response = secretsmanager.get_secret_value(SecretId=secret_name)
    secret = json.loads(response['SecretString'])
    return secret


# Retrieve the Telegram token from Secrets Manager
secret_name = "telegram/bot_token"
secrets = get_secret(secret_name)
TELEGRAM_TOKEN = secrets['TELEGRAM_TOKEN']
TELEGRAM_API_URL = "https://api.telegram.org/bot{}/".format(TELEGRAM_TOKEN)


def send_message(chat_id, text):
    url = TELEGRAM_API_URL + "sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    requests.post(url, json=payload)


def get_stock_price(ticker):
    response = requests.get(STOCK_API_URL, params={'symbol': ticker})
    data = response.json()
    return data['price']  # Adjust this according to your API response


def register_user(data):
    chat_id = data['message']['chat']['id']
    text = data['message']['text']

    if text.startswith("/register"):
        _, ticker, percentage = text.split()
        ticker = ticker.upper()
        percentage = float(percentage.replace('%', ''))

        table.put_item(
            Item={
                'chat_id': str(chat_id),
                'ticker': ticker,
                'percentage': percentage,
                'last_price': get_stock_price(ticker)
            }
        )
        send_message(chat_id, f"Registered {ticker} with {percentage}% threshold")
    else:
        send_message(chat_id, "Use /register $TICKER:THRESHOLD% to register a stock")


def check_stocks(event, context):
    response = table.scan()
    items = response.get('Items', [])

    for item in items:
        chat_id = item['chat_id']
        ticker = item['ticker']
        threshold = item['percentage']

        current_price = get_stock_price(ticker)
        last_price = item.get('last_price', current_price)

        change_percent = ((current_price - last_price) / last_price) * 100

        if abs(change_percent) >= threshold:
            send_message(chat_id, f"{ticker} has changed by {change_percent:.2f}%")
            table.update_item(
                Key={'chat_id': chat_id, 'ticker': ticker},
                UpdateExpression="SET last_price = :val",
                ExpressionAttributeValues={':val': current_price}
            )


def lambda_handler(event, context):
    # if 'message' in event:
    #     register_user(event)
    # else:
    #     check_stocks(event, context)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
