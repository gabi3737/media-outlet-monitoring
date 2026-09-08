# DynamoDB Configuration

resource "aws_dynamodb_table" "c25_gabi_db" {
    name = "c25-gabi-db"
    billing_mode = "PAY_PER_REQUEST"
    hash_key = "id"
    range_key = "publication_time"

    attribute {
        name = "id"
        type = "S"
    }

    attribute {
        name = "publication_time"
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

        Resource = aws_dynamodb_table.c25-gabi-db.arn
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

resource "aws_scheduler_schedule" "c25-gabi-schedule" {
    name = "c25-gabi-schedule"
    group_name = "default"

    flexible_time_window {
      mode = "OFF"
    }

    schedule_expression = "0 */1 * * *"

    target {
        arn = aws_lambda_function.extract_function.arn
        role_arn = aws_iam_role.eventbridge_scheduler_role.arn
    }
}

# Lambda for API Gateway Configuration



# API Gateway Configuration



# ECS and Dashboard Configuration

