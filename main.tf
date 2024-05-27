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
      Action: "sts:AssumeRole"
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
}

resource "aws_lambda_function" "telegram_bot" {
  filename         = "lambda_function.zip"
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


resource "aws_cloudwatch_event_rule" "every_minute" {
  name                = "every_minute"
  schedule_expression = "rate(1 minute)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.every_minute.name
  target_id = "telegram_bot"
  arn       = aws_lambda_function.telegram_bot.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.telegram_bot.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_minute.arn
}