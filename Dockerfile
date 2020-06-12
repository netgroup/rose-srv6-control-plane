FROM python:3.6-slim-buster as builder
# Preparing working environment.
RUN mkdir -p /root/workspace/rose-srv6-control-plane/
COPY . /root/workspace/rose-srv6-control-plane/
ENV SRV6_HOME "/root/workspace/rose-srv6-control-plane/"
WORKDIR /root/workspace/rose-srv6-control-plane/control_plane/protos
RUN python setup.py install
RUN apt-get update && apt-get install -y iputils-ping vim net-tools iproute2


FROM builder as controller
WORKDIR $SRV6_HOME/db_update
RUN python setup.py install
WORKDIR $SRV6_HOME/control_plane/controller
RUN python setup.py install
# Dummy command to keep the container running
# at moment the controller is just a CLI
CMD ["tail", "-f", "/dev/null"]

FROM builder as node-manager
WORKDIR $SRV6_HOME/control_plane/node-manager
RUN python setup.py install
WORKDIR $SRV6_HOME/control_plane/node-manager/node_manager
EXPOSE 12345
CMD [ "python", "node_manager.py" ]