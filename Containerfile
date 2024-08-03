FROM python:3

# To upgrade pip for the system we need to run this as root
RUN python3 -m pip install --no-cache-dir --upgrade pip

# Add user
RUN useradd --create-home --shell /bin/bash threatuser
USER threatuser
WORKDIR /home/threatuser
ENV PATH="${PATH}:/home/threatuser/.local/bin"

# Install the dependencies
COPY api_requirements.txt requirements.txt
#RUN python3 -m pip install --no-cache-dir -r requirements.txt --target .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# TODO Install threatware using pip
# Copy code
COPY --chown=threatuser . .

#ENV THREATWARE_CONFIG_REPO=http://gitlab.threatware.local:8080/threatuser/threatware-tryit-config
ENV THREATWARE_CONFIG_REPO=https://github.com/samadhicsec/threatware-config.git
ENV THREATWARE_CONFIG_REPO_BRANCH=tryit
ENV THREATWARE_CONFIG_DIR=/home/threatuser/.threatware

CMD ["fastapi", "run", "actions/api_main.py", "--port", "8080"]