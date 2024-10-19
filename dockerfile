FROM python:3

# To copy and make executable we need to run this as root
ADD https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /usr/bin/aws-lambda-rie
RUN chmod 755 /usr/bin/aws-lambda-rie

# To upgrade pip for the system we need to run this as root
RUN python3 -m pip install --no-cache-dir --upgrade pip

# Install aws-lambda-cpp build dependencies for awslambdaric
RUN apt-get update && \
  apt-get install -y \
  g++ \
  make \
  cmake \
  unzip \
  libcurl4-openssl-dev

# Add user
RUN useradd --create-home --shell /bin/bash threatuser
USER threatuser
WORKDIR /home/threatuser

# Install the dependencies
COPY requirements.txt requirements.txt
RUN python3 -m pip install --no-cache-dir -r requirements.txt --target .

# Install the runtime interface client
RUN python3 -m pip install --no-cache-dir --target . awslambdaric

# Copy code
COPY --chown=threatuser . .
RUN chmod 755 entry.sh

ENTRYPOINT [ "/home/threatuser/entry.sh" ]
CMD [ "actions.handler.lambda_handler" ]