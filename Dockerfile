# Define custom function directory
ARG FUNCTION_DIR="/function"

FROM public.ecr.aws/docker/library/python:bookworm AS build-image

# Include global arg in this stage of the build
ARG FUNCTION_DIR

# Copy function code
RUN mkdir -p ${FUNCTION_DIR}
COPY requirements.txt lambda_function.py local_utils.py organizations.json .env ${FUNCTION_DIR}

# Install the function's dependencies
RUN pip install \
    --target ${FUNCTION_DIR} \
    awslambdaric

RUN pip install \
    --target ${FUNCTION_DIR} \
    -r ${FUNCTION_DIR}/requirements.txt

# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}

# Set runtime interface client as default command for the container runtime
ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
# Pass the name of the function handler as an argument to the runtime
CMD [ "lambda_function.lambda_handler" ]