#!/bin/bash

# Comandos para criar o pacote de implantação da função Lambda

# Entre no diretório das dependências da função Lambda
cd venv/lib/python3.10/site-packages

# Crie um arquivo zip contendo todas as dependências
zip -rq ../../../../my_deployment_package.zip .

# Saia do diretório de dependências e volte para o diretório raiz do projeto
cd ../../../../

# Adicione o arquivo lambda_function.py ao pacote de implantação
zip -q my_deployment_package.zip lambda_function.py