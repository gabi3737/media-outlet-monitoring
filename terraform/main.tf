# DynamoDB Configuration

resource "aws_dynamodb_table" "c25_gabi_db" {
    name = "c25-gabi-db"
    billing_mode = "PAY_PER_REQUEST"
    hash_key = "article_id"
    range_key = "published"

    attribute {
        name = "article_id"
        type = "S"
    }

    attribute {
        name = "published"
        type = "S"
    }
}

# Extract Lambda Role Configuration

resource "aws_iam_role" "extract_lambda_role" {
  name = "c25-gabi-extract-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Effect = "Allow"

      Principal = {
        Service = "lambda.amazonaws.com"
      }

      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  role = aws_iam_role.extract_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]

        Resource = "*"
      },
      {
        Effect = "Allow"

        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]

        Resource = aws_dynamodb_table.c25_gabi_db.arn
      }
    ]
  })
}



# Extract Lambda Function Configuration

resource "aws_lambda_function" "extract_function" {
    function_name = "c25_gabi_extract"
    role = aws_iam_role.extract_lambda_role.arn
    package_type = "Image"
    image_uri = "" 

    memory_size = 512
    timeout = 60
}

# EventBridge Scheduler Role Configuration

resource "aws_iam_role" "eventbridge_scheduler_role" {
    name = "c25-gabi-eventbridge-scheduler-role"
    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = "sts:AssumeRole"
                Effect = "Allow"
                Principal = {
                    Service = "scheduler.amazonaws.com"
                }
            }
        ]
    })
}

resource "aws_iam_role_policy" "scheduler_lambda_policy" {
  role = aws_iam_role.eventbridge_scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "lambda:InvokeFunction"
      Resource = aws_lambda_function.extract_function.arn
    }]
  })
}

resource "aws_lambda_permission" "allow_scheduler" {
  statement_id  = "AllowExecutionFromScheduler"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.extract_function.function_name
  principal     = "scheduler.amazonaws.com"
  source_arn    = aws_scheduler_schedule.c25_gabi_schedule.arn
}


# EventBridge Scheduler Configuration

resource "aws_scheduler_schedule" "c25_gabi_schedule" {
    name = "c25-gabi-schedule"
    group_name = "default"

    flexible_time_window {
      mode = "OFF"
    }

    schedule_expression = "cron(0 */1 * * ? *)"

    target {
        arn = aws_lambda_function.extract_function.arn
        role_arn = aws_iam_role.eventbridge_scheduler_role.arn
    }
}

# Execution Role for API Gateway Lambda Function

resource "aws_iam_role" "lambda_exec" {
  name = "c25-gabi-lambda-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "c25-gabi-lambda-dynamodb-access"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["dynamodb:Query", "dynamodb:GetItem"]
      Resource = [
        aws_dynamodb_table.c25_gabi_db.arn,
        "${aws_dynamodb_table.c25_gabi_db.arn}/index/*"
      ]
    }]
  })
}

# Passing in ZIP file with Python

data "archive_file" "lambda_zip" {
  type = "zip"
  source_dir = "lambda"
  output_path = "zip/handler.zip"
}

# Lambda for API Gateway Configuration

resource "aws_lambda_function" "api_handler" {
    function_name = "c25_gabi_gateway_function"
    runtime = "python3.11"
    handler = "handler.handler" #Handler function name in Python code
    filename = data.archive_file.lambda_zip.output_path 
    source_code_hash = data.archive_file.lambda_zip.output_base64sha256  #Redeploys code when we change it, as Terraform apply doesn't redeploy
    role = aws_iam_role.lambda_exec.arn 
    timeout = 20
    environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.c25_gabi_db.name
    }
  }
}


# API Gateway Configuration

resource "aws_apigatewayv2_api" "c25_gabi_api" {
    name        = "c25-gabi-api"
    protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "api_handler" {
    api_id = aws_apigatewayv2_api.c25_gabi_api.id
    integration_type = "AWS_PROXY"
    integration_uri = aws_lambda_function.api_handler.invoke_arn
    integration_method = "POST" #This is how the API invokes the Lambdas, not how the user interacts with the API. (Very odd)
    payload_format_version = "2.0"
}

# API Routes
resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.c25_gabi_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.api_handler.id}"
}

resource "aws_apigatewayv2_route" "get_article" {
  api_id    = aws_apigatewayv2_api.c25_gabi_api.id
  route_key = "GET /articles/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.api_handler.id}"
}

resource "aws_apigatewayv2_route" "get_keywords" {
  api_id    = aws_apigatewayv2_api.c25_gabi_api.id
  route_key = "GET /keywords/{keyword}"
  target    = "integrations/${aws_apigatewayv2_integration.api_handler.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.c25_gabi_api.id
  name        = "$default"
  auto_deploy = true
} #This is where the API deploys to

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.c25_gabi_api.execution_arn}/*/*"
}

# ECS and Dashboard Configuration

