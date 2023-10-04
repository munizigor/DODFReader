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

# Crie o repositório ECR
# resource "aws_ecr_repository" "my_ecr_repo" {
#   name = "get-dodf"  # Substitua pelo nome desejado para o repositório
# }

variable "ecr_address" {}
variable "repository_name" {}
variable "ecr_tag" {}
variable "target_input" {}
variable "bot_token" {}

locals {
  get_dodf_ecr_address = "${var.ecr_address}/${var.repository_name}:${var.ecr_tag}"
  tag_name             = "${var.repository_name}:${var.ecr_tag}"
}

# Defina a autenticação para o Docker push
data "aws_ecr_authorization_token" "auth_token" {}

# Configuração do provedor Docker
provider "docker" {
  registry_auth {
    address = local.get_dodf_ecr_address
    username = data.aws_ecr_authorization_token.auth_token.username
    password = data.aws_ecr_authorization_token.auth_token.password
  }
}

# Construa a imagem Docker (substitua pelos seus comandos)
resource "null_resource" "build_docker_image" {
  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = "docker build -t ${var.repository_name} ."
    environment = {
      DOCKER_BUILDKIT = "1"
    }
  }
}

# Faça o push da imagem Docker para o ECR
resource "null_resource" "tag_docker_image" {
  triggers = {
    always_run = timestamp()
  }

  depends_on = [null_resource.build_docker_image]

  provisioner "local-exec" {
    command = "docker tag ${local.tag_name} ${local.get_dodf_ecr_address}"
  }
}

# Faça o push da imagem Docker para o ECR
resource "null_resource" "push_docker_image" {
  triggers = {
    always_run = timestamp()
  }

  depends_on = [null_resource.build_docker_image]

  provisioner "local-exec" {
    command = "docker push ${local.get_dodf_ecr_address}"
  }
}


#Definição de role para Lambda
resource "aws_iam_role" "lambda_role" {
  name = "lambda_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Atualize a função do Lambda
resource "aws_lambda_function" "updated_lambda" {
  function_name           = "get-dodf"
  role                    = aws_iam_role.lambda_role.arn
  image_uri               = local.get_dodf_ecr_address
  package_type            = "Image"
  timeout                 = 300
  memory_size             = 256
 
  environment {
    variables = {
      bot_token      = var.bot_token,
    }
  }
}


resource "aws_cloudwatch_event_rule" "lambda_event_rule" {
  name        = "6h30m_WORKDAY"  # Substitua pelo nome desejado da regra do EventBridge
  description = "Regra para acionar a Lambda às 6:30 da manhã (UTC-3) de segunda a sexta-feira"

  # Defina a expressão cron para executar a regra às 8 da manhã de segunda a sexta-feira (UTC time)
  schedule_expression = "cron(30 9 ? * MON-FRI *)"
  

}

resource "aws_cloudwatch_event_target" "my_target" {
  rule      = aws_cloudwatch_event_rule.lambda_event_rule.name
  arn       = aws_lambda_function.updated_lambda.arn  # Use o ARN correto da sua função Lambda
  target_id = "my-target-id"
  input     = var.target_input
}

# Crie a permissão para o EventBridge enviar eventos à função Lambda
resource "aws_lambda_permission" "eventbridge_lambda_permission" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.updated_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_event_rule.arn
}