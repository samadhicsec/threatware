# Define function directory
ARG FUNCTION_DIR="/function"

FROM python:3

ARG FUNCTION_DIR

RUN ln -s /tmp/.ssh /root/.ssh

#ADD https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /usr/bin/aws-lambda-rie

# Install the function's dependencies and the runtime interface client
#RUN python3 -m pip install --no-cache-dir --upgrade pip && \
#        python3 -m pip install --no-cache-dir --target ${FUNCTION_DIR} awslambdaric

#ADD https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /usr/bin/aws-lambda-rie
#COPY entry.sh /

# Copy function code
#COPY . ${FUNCTION_DIR}
#RUN python3 -m pip install --no-cache-dir -r ${FUNCTION_DIR}/requirements.txt --target ${FUNCTION_DIR}
#RUN chmod 755 /usr/bin/aws-lambda-rie ${FUNCTION_DIR}/entry.sh

# Set working directory to function root directory
#WORKDIR ${FUNCTION_DIR}

##ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
#ENTRYPOINT [ "/function/entry.sh" ]
#CMD [ "actions.handler.lambda_handler" ]