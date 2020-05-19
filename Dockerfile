FROM python:3.6-slim-buster
LABEL description=""

# Preparing working environment.
RUN mkdir -p /root/workspace/srv6_controller
WORKDIR /root/workspace/srv6_controller
COPY ./srv6_controller .

# We don't need this in the Docker environment
RUN rm controller/.venv node-manager/.venv

# Install python requirements controller
RUN pip3 install -r controller/requirements.txt

# Install python requirements node-manager
RUN pip3 install -r node-manager/requirements.txt

# Build GRPC protos
WORKDIR /root/workspace/srv6_controller/protos
RUN sh build.sh

# Add generated pyhton to PYTHONPATH
ENV PYTHONPATH "${PYTHONPATH}:/root/workspace/srv6_controller/protos/gen-py"

WORKDIR /root/workspace/srv6_controller/node-manager
SHELL ["/bin/bash", "-c", "source .env"]
EXPOSE 12345
CMD [ "python", "srv6_manager.py" ]