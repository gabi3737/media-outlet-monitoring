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
          "dynamodb:UpdateItem",
          "dynamodb:Scan"
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
    image_uri = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c25-gabi-extract-lambda:latest"

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
      Action   = ["dynamodb:Query", "dynamodb:GetItem", "dynamodb:Scan"]
      Resource = [
        aws_dynamodb_table.c25_gabi_db.arn,
        "${aws_dynamodb_table.c25_gabi_db.arn}/index/*"
      ]
    }]
  })
}

# Lambda for API Gateway Configuration

resource "aws_lambda_function" "api_handler" {
    function_name = "c25_gabi_gateway_function"
    package_type = "Image"
    image_uri    = "" # Add API gateway lambda image uri here
    role = aws_iam_role.lambda_exec.arn 

    timeout = 20
    memory_size = 256
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

resource "aws_apigatewayv2_route" "get_person" {
  api_id    = aws_apigatewayv2_api.c25_gabi_api.id
  route_key = "GET /person/{person}"
  target    = "integrations/${aws_apigatewayv2_integration.api_handler.id}"
}

resource "aws_apigatewayv2_route" "get_company" {
  api_id    = aws_apigatewayv2_api.c25_gabi_api.id
  route_key = "GET /company/{company}"
  target    = "integrations/${aws_apigatewayv2_integration.api_handler.id}"
}

resource "aws_apigatewayv2_route" "get_person_sentiment" {
  api_id    = aws_apigatewayv2_api.c25_gabi_api.id
  route_key = "GET /person/{person}/sentiment"
  target    = "integrations/${aws_apigatewayv2_integration.api_handler.id}"
}

resource "aws_apigatewayv2_route" "get_company_sentiment" {
  api_id    = aws_apigatewayv2_api.c25_gabi_api.id
  route_key = "GET /company/{company}/sentiment"
  target    = "integrations/${aws_apigatewayv2_integration.api_handler.id}"
}

resource "aws_apigatewayv2_route" "get_articles" {
  api_id    = aws_apigatewayv2_api.c25_gabi_api.id
  route_key = "GET /articles"
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


data "aws_vpc" "main" {
  id = var.vpc_id
}

resource "aws_security_group" "ecs_service" {
  name        = "c25-gabi-dashboard-ecs-sg"
  vpc_id      = data.aws_vpc.main.id

  ingress {
    description = "Public access to Streamlit dashboard"
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"] 
  }
}

resource "aws_iam_role" "ecs_task_execution" {
  name = "c25-gabi-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Container Task Role 
resource "aws_iam_role" "ecs_task" {
  name = "c25-gabi-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}


resource "aws_iam_role_policy" "ecs_task_dynamodb" {
  role = aws_iam_role.ecs_task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["dynamodb:Query", "dynamodb:GetItem", "dynamodb:Scan"]
      Resource = [
        aws_dynamodb_table.c25_gabi_db.arn,
        "${aws_dynamodb_table.c25_gabi_db.arn}/index/*"
      ]
    }]
  })
}

resource "aws_cloudwatch_log_group" "dashboard" {
  name              = "/ecs/c25-gabi-dashboard"
  retention_in_days = 7
}

resource "aws_ecs_task_definition" "dashboard" {
  family                   = "c25-gabi-dashboard"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "dashboard"
    image     = "" # ADD IMAGE HERE
    essential = true
    portMappings = [{
      containerPort = 8501
      protocol      = "tcp"
    }]
    environment = [
      { name = "TABLE_NAME", value = aws_dynamodb_table.c25_gabi_db.name }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.dashboard.name
        "awslogs-region"        = "eu-west-2"
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

data "aws_ecs_cluster" "c25" {
  cluster_name = "c25-ecs-cluster"
}

resource "aws_ecs_service" "c25_gabi_dashboard" {
  name            = "c25-gabi-dashboard"
  cluster         = data.aws_ecs_cluster.c25.id
  task_definition = aws_ecs_task_definition.dashboard.arn
  desired_count   = 1

  launch_type = "FARGATE"

  network_configuration {
    subnets         = var.subnet_ids
    security_groups = [aws_security_group.ecs_service.id]
    assign_public_ip = true
  }
}
