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
  region = "sa-east-1"
}

variable "chat_id" {}
variable "bot_token" {}

# Carregue o arquivo .zip para o bucket do S3
resource "aws_s3_object" "my_deployment_package_zip" {
  bucket = "autoclippinglambdabucket"
  key    = "my_deployment_package.zip"   # Substitua pelo nome desejado do arquivo .zip no bucket
  source = "./my_deployment_package.zip" # Substitua pelo caminho local do arquivo .zip

  etag = filemd5("./my_deployment_package.zip")
}

# Crie a função Lambda
resource "aws_lambda_function" "lambda_function" {
  function_name = "get-dodf-lambda" # Substitua pelo nome desejado da função Lambda
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler" # Substitua pelo nome do arquivo principal e a função a ser chamada
  runtime       = "python3.10"                     # Substitua pela versão do Node.js desejada
  timeout       = 90

  environment {
    variables = {
      chat_id   = var.chat_id,
      bot_token = var.bot_token,
    }
  }

  # Especifique o código da função Lambda
  s3_bucket = aws_s3_object.my_deployment_package_zip.bucket
  s3_key    = aws_s3_object.my_deployment_package_zip.key
}

# Crie uma função IAM para a função Lambda
resource "aws_iam_role" "lambda_role" {
  name = "get_dodf_lambda_execution_role" # Substitua pelo nome desejado da função IAM

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Anexe a política que permite que a função Lambda leia o objeto do bucket S3
resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess" # Política pré-definida da AWS para leitura no S3
  role       = aws_iam_role.lambda_role.name
}

# Crie a regra do EventBridge para agendar a execução da Lambda
resource "aws_cloudwatch_event_rule" "lambda_event_rule" {
  name        = "get_dodf_lambda_event_rule" # Substitua pelo nome desejado da regra do EventBridge
  description = "Regra para acionar a Lambda às 6:05 da manhã de segunda a sexta-feira"

  # Defina a expressão cron para executar a regra às 8 da manhã de segunda a sexta-feira (UTC time)
  schedule_expression = "cron(5 9 ? * MON-FRI *)"

  # Defina a arquitetura do alvo da regra (aqui, acionando a função Lambda)
  event_bus_name = "default" # O nome padrão do barramento de eventos
}

resource "aws_cloudwatch_event_target" "lambda_function" {
  rule      = aws_cloudwatch_event_rule.lambda_event_rule.name
  target_id = "SendToLambda"
  arn       = aws_lambda_function.lambda_function.arn
}

# Crie a permissão para o EventBridge enviar eventos à função Lambda
resource "aws_lambda_permission" "eventbridge_lambda_permission" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_event_rule.arn
}
