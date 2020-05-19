# rose-srv6-control-plane

## Docker

### Build the Docker image

From the root directory of the repository execute the following command

    docker build -t rose-srv6-control-plane:<tag_name> . --no-cache

### Run in a Docker container

Currently the exposed port is 12345
    docker run --name <container_name> -p HOST_PORT:12345 rose-srv6-control-plane:<tag_name>
