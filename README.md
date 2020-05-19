# rose-srv6-control-plane

## Docker

### Build the Docker image

From the root directory of the repository execute the following command
inorder to build the controller image:

    docker build --target controller -t rose-srv6-controller:latest . --no-cache

inorder to build the node-manager image:

    docker build --target node-manager -t rose-srv6-node-manager:latest . --no-cache

### Run the controller container


    docker run --name rose-srv6-controller  -it rose-srv6-controller:latest bash

### Run the node-manager container

Currently the exposed port is 12345

    docker run --name rose-srv6-node-manager -p HOST_PORT:12345 rose-srv6-node-manager:latest

### Access to the Docker container

    docker exec -it <container_name> bash

for instance access to rose-srv6-controller with:

    docker exec -it rose-srv6-node-manager bash
