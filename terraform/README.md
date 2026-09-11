# Terraform Folder Contents 
`main.tf` - all the Terraform used in the project including:
- DynamoDB
- ETL Lambda Function
- ETL EventBridge Scheduler
- API Gateway
- API Gateway backend Lambda Function
- ECS for Dashboard deployment

The ECRs containing the Images were created manually in the console.

`variables.tf` - environment variables that need setting in `terraform.tfvars` to correctly apply the Terraform.

`lambda/Dockerfile` - The Dockerfile used for the Image for the API Gateway backend Lambda.

`lambda/handler.py` - Python script containing API endpoints and function calls.

`lambda/handler_functions.py` - Python script containing functions connecting to and calling data from the DynamoDB.

`lambda/requirements.txt` - Requirements file for `lambda/` folder.

# Instructions

## To create all the resources for the project:


### Terraform Root Folder

Intialise Terraform:

``` bash 
terraform init
``` 

Deploy Resources on AWS:

``` bash
terraform apply
```

Remove all resources from AWS:
```bash
terraform destroy
```

## To reset the API Gateway Lambda after adding new code to the `handler.py` or `handler_functions.py` run:

### `lambda/` Folder

To build and push the Docker Image to the ECR:
- Authenticate your Docker client and AWS CLI to your registry. 

Build the Image:

``` bash
docker build --platform linux/amd64 --provenance=false --sbom=false -t c25-gabi-api-gateway .
```

Tag the Image:

``` bash
docker tag c25-gabi-api-gateway:latest 129033205317.dkr.ecr.eu-west-2.amazonaws.com/c25-gabi-api-gateway:latest
```

Push the Image:

``` bash
docker push 129033205317.dkr.ecr.eu-west-2.amazonaws.com/c25-gabi-api-gateway:latest
```

### Terraform Root Folder

Reset the Lambda to use the newly pushed Image:

``` bash
terraform apply -replace=aws_lambda_function.api_handler
```
Reapply the `lambda_permissions` resource block:

```bash
terraform apply
```




