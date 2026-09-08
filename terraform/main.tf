# DynamoDB Configuration

resource "aws_dynamodb_table" "c25-gabi-db" {
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

# Extract Lambda Function Configuration

resource "aws_lambda_function" "extract_function" {
    function_name = "c25_gabi_extract"
    role = ""
    package_type = "Image"
    image_uri = "" 

    memory_size = 512
    timeout = 60
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
        arn = ""
        role_arn = ""
    }
}

# Lambda for API Gateway Configuration

resource "aws_lambda_function" "api_gateway_function" {
    function_name = "c25_gabi_api_gateway"
    role = ""
    package_type = "Image"
    image_uri = "" 

    memory_size = 512
    timeout = 60
}


# API Gateway Configuration

resource 