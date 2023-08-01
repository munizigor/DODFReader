terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
  }

  required_version = ">= 1.2.0"
}

provider "aws" {
  region = "sa-east-1" # Substitua pela região desejada
}

# Use a imagem Docker do repositório público como Layer do Lambda
resource "aws_lambda_layer_version" "my_lambda_layer" {
  compatible_runtimes = ["python3.10"] # Substitua pela versão do Python desejada
  description         = "My custom Lambda layer with public Docker image"
  source_code_hash    = filebase64sha256("./Dockerfile") # Substitua pelo caminho do Dockerfile (pode ser qualquer arquivo, pois você não usará sua própria imagem Docker)
  source_code_size    = file("./Dockerfile")             # Substitua pelo caminho do Dockerfile (pode ser qualquer arquivo, pois você não usará sua própria imagem Docker)

  # Especifique a imagem Docker pública no formato correto
  source_code_url = "public.ecr.aws/docker/library/python:bookworm" # Substitua pela imagem pública desejada
}

# Crie a função do Lambda
resource "aws_lambda_function" "my_lambda_function" {
  function_name = "my-lambda-function"
  handler       = "lambda_function.lambda_handler" # Substitua pelo nome do arquivo e da função Lambda
  runtime       = "python3.8"
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
