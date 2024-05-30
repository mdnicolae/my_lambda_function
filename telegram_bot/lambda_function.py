import json
import os
import boto3
import stock
import telegram as tg
from decimal import Decimal
import helper

# Constants
DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)


def register_user(data):
    chat_id = data['message']['chat']['id']
    text = data['message']['text']

    if text.startswith("/register"):
        try:
            _, ticker_and_percentage = text.split()
            ticker = ticker_and_percentage.split(':')[0]
            percentage = float(ticker_and_percentage.split(':')[1])

            ticker = ticker.upper()

            if not stock.ticker_exists(ticker):
                tg.send_message(chat_id, f"{ticker} is not a valid stock")
                return

            current_price = stock.get_stock_price(ticker)
            if current_price is None:
                tg.send_message(chat_id, "Error retrieving stock price. Please retry later")
                return

            table.put_item(
                Item={
                    'chat_id': str(chat_id),
                    'ticker': ticker,
                    'percentage': Decimal(str(percentage)),
                    'last_price': Decimal(str(current_price))
                }
            )
            tg.send_message(chat_id, f"Registered {ticker} with {percentage}% threshold")

        except ValueError:
            tg.send_message(chat_id, "Use /register TICKER:THRESHOLD to register a stock")
    else:
        tg.send_message(chat_id, "Use /register TICKER:THRESHOLD to register a stock")


def check_all_registered_stocks():
    response = table.scan()
    for item in response['Items']:
        chat_id = item['chat_id']
        ticker = item['ticker']
        percentage = item['percentage']
        last_price = Decimal(str(item['last_price']))

        current_price = stock.get_stock_price(ticker)
        if current_price is None:
            tg.send_message(chat_id, "Something went wrong. Please contact the administrator.")
            return

        current_price = Decimal(str(current_price))

        if current_price > last_price * (1 + percentage / 100) or current_price < last_price * (1 - percentage / 100):
            tg.send_message(chat_id, f"⚠️ ${ticker} price has changed by more than {percentage}% and is now at ${current_price}")
            table.update_item(
                Key={
                    'chat_id': str(chat_id),
                    'ticker': ticker
                },
                UpdateExpression="set last_price = :p",
                ExpressionAttributeValues={
                    ':p': current_price
                }
            )

    if response['Count'] == 0:
        print("No registered stocks found")


def handle_command(data):
    chat_id = data['message']['chat']['id']
    text = data['message']['text']

    if text.startswith("/register"):
        register_user(data)
        return
    if text.startswith("/list"):
        response = table.scan()
        if response['Count'] == 0:
            tg.send_message(chat_id, "No registered stocks found")
        else:
            message = "Registered stocks:\n"
            for item in response['Items']:
                message += f"${item['ticker']} - {item['percentage']}%\n"
            tg.send_message(chat_id, message)
        return
    if text.startswith("/remove"):
        try:
            _, ticker = text.split()
            table.delete_item(
                Key={
                    'chat_id': str(chat_id),
                    'ticker': ticker.upper()
                }
            )
            tg.send_message(chat_id, f"Removed {ticker} from the list")
        except ValueError:
            tg.send_message(chat_id, "Something went wrong removing the stock. Please try again later")
        return
    if text.startswith("/help"):
        tg.send_message(chat_id, helper.read_help_file("help.txt"))
        return

    tg.send_message(chat_id, "Unknown command. Use /help to see the available commands")


def lambda_handler(event, context):
    if 'body' in event:
        try:
            body = json.loads(event['body'])
            if 'message' in body:
                handle_command(body)
        except json.JSONDecodeError:
            print("Failed to decode JSON body")
    else:
        # Check if the event is coming from EventBridge
        if 'source' in event and event['source'] == 'aws.events':
            check_all_registered_stocks()
        else:
            print("Unhandled event type")
            return {
                'statusCode': 400,
                'body': json.dumps('Bad Request')
            }

    return {
        'statusCode': 200,
        'body': json.dumps('Success')
    }
