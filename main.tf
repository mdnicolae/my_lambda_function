provider "aws" {
  region = "eu-central-1"
}

resource "aws_iam_role" "lambda_role" {
  name = "lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_dynamodb_table" "telegram_stocks" {
  name         = "telegram_stocks"
  billing_mode = "PAY_PER_REQUEST" # This is the on-demand mode which falls under Free Tier
  hash_key     = "chat_id"
  range_key    = "ticker"

  attribute {
    name = "chat_id"
    type = "S"
  }

  attribute {
    name = "ticker"
    type = "S"
  }

  # Global Secondary Indexes (optional, if you need additional query patterns)
  global_secondary_index {
    name            = "ticker-index"
    hash_key        = "ticker"
    projection_type = "ALL"
  }
}

resource "aws_s3_bucket" "lambda_bucket" {
  bucket = "telegram-bot-lambda-bucket"
}

resource "aws_lambda_function" "telegram_bot" {
  s3_bucket        = aws_s3_bucket.lambda_bucket.bucket
  s3_key           = "lambda_function.zip"
  function_name    = "telegram_bot"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.8"
  timeout          = 60
  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.telegram_stocks.name
    }
  }
}

resource "aws_lambda_layer_version" "my_layer" {
  layer_name = "my-bot-layer"
  s3_bucket        = aws_s3_bucket.lambda_bucket.bucket
  s3_key           = "python.zip"
  compatible_runtimes = ["python3.8"]
}

resource "aws_cloudwatch_event_rule" "us_stock_market_hours" {
  name                = "us_stock_market_hours"
  description         = "Trigger every 5 minutes during US stock market trading hours (Monday to Friday, 9:30 AM - 4:00 PM ET)"
  schedule_expression = "cron(*/5 13-22 ? * MON-FRI *)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.us_stock_market_hours.name
  target_id = "telegram_bot"
  arn       = aws_lambda_function.telegram_bot.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.telegram_bot.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.us_stock_market_hours.arn
}
