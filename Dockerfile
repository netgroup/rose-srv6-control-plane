FROM python:3.6-slim-buster as builder
# Preparing working environment.
RUN mkdir -p /root/workspace/rose-srv6-control-plane/srv6_controller
WORKDIR /root/workspace/rose-srv6-control-plane
COPY ./srv6_controller ./srv6_controller
# Add generated grcp pyhton to PYTHONPATH
ENV PYTHONPATH "${PYTHONPATH}:/root/workspace/srv6_controller/protos/gen-py"


FROM builder as controller
RUN apt-get update && apt-get install -y iputils-ping vim net-tools iproute2
# Install python requirements controller
RUN pip3 install -r srv6_controller/controller/requirements.txt
# Build GRPC protos
WORKDIR /root/workspace/rose-srv6-control-plane/srv6_controller/protos
RUN sh build.sh
WORKDIR /root/workspace/rose-srv6-control-plane/srv6_controller/
SHELL ["/bin/bash", "-c", "source controller/.env"]
SHELL ["/bin/bash", "-c", "source examples/.env"]
RUN ls -la -R
# Dummy command to keep the container running
# at moment the controller is just a CLI
CMD ["tail", "-f", "/dev/null"]

FROM builder as node-manager
# Install python requirements node-manager
RUN pip3 install -r node-manager/requirements.txt
# Build GRPC protos
WORKDIR /root/workspace/rose-srv6-control-plane/srv6_controller/protos
RUN sh build.sh
# Move to node-manager directory and start node-manger
WORKDIR /root/workspace/rose-srv6-control-plane/srv6_controller/node-manager
SHELL ["/bin/bash", "-c", "source .env"]
EXPOSE 12345
CMD [ "python", "srv6_manager.py" ]