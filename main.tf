terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0.1"
    }
  }

  required_version = ">= 1.2.0"
}

provider "aws" {
  region = "sa-east-1" # Substitua pela região desejada
}

# Crie o repositório ECR para armazenar a imagem Docker
resource "aws_ecr_repository" "my_ecr_repo" {
  name = "my-lambda-container-repo" # Substitua pelo nome desejado para o repositório
}

# Data source para recuperar informações da imagem Docker
data "docker_image" "my_lambda_container" {
  name = "python_bookworm:latest" # Substitua pelo nome da imagem Docker que você criou usando o Dockerfile
}

# Faça o push da imagem para o ECR
resource "aws_ecr_image" "my_ecr_image" {
  name         = aws_ecr_repository.my_ecr_repo.repository_url
  image_tag    = "latest"
  image_digest = data.docker_image.my_lambda_container.digest
}


# Use a imagem URI do ECR para criar o Layer do Lambda
resource "aws_lambda_layer_version" "my_lambda_layer" {
  compatible_runtimes = ["python3.11"] # Substitua pela versão do Python desejada
  description         = "My custom Lambda layer with Docker container"
  source_code_hash    = filebase64sha256("./Dockerfile") # Substitua pelo caminho do Dockerfile
  source_code_size    = file("./Dockerfile")             # Substitua pelo caminho do Dockerfile

  # Especifique a imagem URI do ECR no formato correto
  source_code_url = "${aws_ecr_repository.my_ecr_repo.repository_url}@${data.docker_image.my_lambda_container.digest}"
}


# Crie a função do Lambda
resource "aws_lambda_function" "my_lambda_function" {
  function_name = "my-lambda-function"
  handler       = "lambda_function.lambda_handler" # Substitua pelo nome do arquivo e da função Lambda
  runtime       = "python3.11"
  role          = aws_iam_role.lambda_exec.arn

  # Defina as configurações adicionais da função do Lambda aqui

  # Use o Layer personalizado no Lambda
  layers = [aws_lambda_layer_version.my_lambda_layer.arn]
}

# Crie a permissão para a função do Lambda usar o Layer personalizado
resource "aws_lambda_permission" "layer_permission" {
  statement_id  = "AllowLayer"
  action        = "lambda:GetLayerVersion"
  function_name = aws_lambda_function.my_lambda_function.function_name
  principal     = "lambda.amazonaws.com"
}
