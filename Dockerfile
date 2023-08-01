# FROM public.ecr.aws/docker/library/python:bookworm AS build-image

# # Copiar dependencias para a pasta opt
# COPY requirements.txt /opt
# COPY lambda_function.py venv/lib/python3.10/site-packages/local_utils.py /opt/
# # Install any necessary dependencies
# RUN pip install -r /opt/requirements.txt --target /opt
# # RUN pip install --target ${FUNCTION_DIR} awslambdaric
# CMD [ "lambda_function.lambda_handler" ]


# Define custom function directory

FROM public.ecr.aws/docker/library/python:bookworm AS build-image

# Include global arg in this stage of the build

# Copy function code
# RUN mkdir -p ${FUNCTION_DIR}
# RUN mkdir /opt/extensions

# Copiar dependencias para a pasta opt
COPY requirements.txt lambda.py /opt/
# COPY lambda_function.py venv/lib/python3.10/site-packages/local_utils.py ${FUNCTION_DIR}
COPY venv/lib/python3.10/site-packages/local_utils.py /opt/extensions/


# Install the function's dependencies
RUN pip install \
    --target /opt/extensions \
    awslambdaric

RUN pip install --target /opt/extensions -r /opt/requirements.txt

# Use a slim version of the base Python image to reduce the final image size
FROM python:3.10-slim

# Include global arg in this stage of the build
# Set working directory to function root directory
WORKDIR /opt

# Copy in the built dependencies
COPY --from=build-image /opt .
RUN chmod -R o+rX .
# Set runtime interface client as default command for the container runtime
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
# Pass the name of the function handler as an argument to the runtime

# CMD [ "lambda_function.lambda_handler" ]
CMD [ "lambda.handler" ]