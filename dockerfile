FROM python:3

# To copy and make executable we need to run this as root
ADD https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /usr/bin/aws-lambda-rie
RUN chmod 755 /usr/bin/aws-lambda-rie

# To upgrade pip for the system we need to run this as root
RUN python3 -m pip install --no-cache-dir --upgrade pip

# Add user
RUN useradd --create-home --shell /bin/bash threatuser
USER threatuser
WORKDIR /home/threatuser

# Install the function's dependencies
COPY requirements.txt requirements.txt
RUN python3 -m pip install --no-cache-dir -r requirements.txt --target .

# Install the function's dependencies and the runtime interface client
RUN python3 -m pip install --no-cache-dir --target . awslambdaric

# Copy function code
COPY --chown=threatuser . .
RUN chmod 755 entry.sh

ENTRYPOINT [ "/home/threatuser/entry.sh" ]
CMD [ "actions.handler.lambda_handler" ]