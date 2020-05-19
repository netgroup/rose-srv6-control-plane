FROM python:3.6-slim-buster


# Preparing working environment.
RUN mkdir -p /root/workspace/srv6_controller
WORKDIR /root/workspace/srv6_controller
COPY ./srv6_controller .

# Install python requirements
RUN pip3 install -r controller/requirements.txt

# Build GRPC protos
WORKDIR /root/workspace/srv6_controller/protos
RUN sh build.sh

WORKDIR /root/workspace/srv6_controller