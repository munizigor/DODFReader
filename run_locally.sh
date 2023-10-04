#!/bin/bash

export bot_token="5144694768:AAFOrRICs066PoDx2Ed5IsC4JRnFNCx4apw"

python3 -c "import lambda_function;lambda_function.lambda_handler('{\"mode\":\"dev\"}',None)"