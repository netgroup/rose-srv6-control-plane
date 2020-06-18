# Controller

## Prerequisites

The following dependencies are necessary:

* Python 3.6 or above

## Installation

1. Create a Python 3 virtual environment for the controller:
    ```console
    $ python3 -m venv ~/.envs/controller-venv
    ```
1. Activate the virtual environment:
    ```console
    $ source ~/.envs/controller-venv/bin/activate
    ```
1. Clone the *rose-srv6-control-plane* repository using ```git```:
    ```console
    $ git clone https://github.com/netgroup/rose-srv6-control-plane.git
    ```
1. Then, ```cd``` to the *control_plane/controller* directory under the *rose-srv6-control-plane* folder and run the install command:
    ```console
    $ cd rose-srv6-control-plane/control_plane/controller
    $ python setup.py install
    ```
1. This project depends on the gRPC protocol, which requires protobuf modules. ```cd``` to the *control_plane/protos* directory under the *rose-srv6-control-plane* folder and run the setup command to build and install the proto files:
    ```console
    $ cd rose-srv6-control-plane/control_plane/protos
    $ python setup.py install
    ```

## Configuration

* The controller comes with a default configuration. If you want to override the default settings, you can create a *.env* file containing the configuration parameters:
    ```sh
    export GRPC_SECURE=True
    export GRPC_CA_CERTIFICATE_PATH=/tmp/ca.crt
    export DEBUG=True
    ```
    * *GRPC_SECURE*: define whether to enable the gRPC secure mode or not
    * *GRPC_CA_CERTIFICATE_PATH*: path to the certificate of the CA, required by gRPC secure mode
    * *DEBUG*: enable debug logs
* To enable the optional features, you need to set the following parameters in your *.env* file:
    * ArangoDB integration:
        ```sh
        export ENABLE_ARANGO_INTEGRATION=True
        export ARANGO_URL=http://localhost:8082
        export ARANGO_USER=root
        export ARANGO_PASSWORD=12345678
        ```
        Note: the *db_update* library is required to support ArangoDB integration. Follow the instructions provided in section [Optional requirements](#optional-requirements) to setup the required dependencies.
    * Kafka integration:
        ```sh
        export ENABLE_KAFKA_INTEGRATION=True
        export KAFKA_SERVERS=kafka:9092
        ```
        Note: the *kafka-python* package is required to support ArangoDB integration. Follow the instructions provided in section [Optional requirements](#optional-requirements) to setup the required dependencies.
    * gRPC server on the controller (interface node->controller):
        ```sh
        export ENABLE_GRPC_SERVER=True
        export GRPC_SERVER_IP=::
        export GRPC_SERVER_PORT=12345
        export GRPC_SERVER_SECURE=True
        export GRPC_SERVER_CERTIFICATE_PATH=/tmp/server.crt
        export GRPC_SERVER_KEY_PATH=/tmp/server.key
        ```
The *config* folder in the controller directory contains a sample configuration file.

## Optional requirements

* Database utilities are required for the ArangoDB integration features. You need to activate the controller virtual environment and install the *db_update* package contained in the *rose-srv6-control-plane* repository if you want to use these features:
    ```console
    $ source ~/.envs/controller-venv/bin/activate
    $ cd rose-srv6-control-plane/db_update
    $ python setup.py install
    ```
* Exporting the network topology as an image file requires *graphviz* and *libgraphviz-dev*:
    ```console
    $ apt-get install graphviz libgraphviz-dev
    ```
* *kafka-python* is required for Kafka integration. Activate the controller virtual environment and run the install command:
    ```console
    $ source ~/.envs/controller-venv/bin/activate
    $ pip install kafka-python
    ```

## Starting the Controller CLI

1. Activate the controller virtual environment:
    ```console
    $ source ~/.envs/controller-venv/bin/activate
    ```
1. To start the Controller CLI:
    ```console
    $ controller --env-file .env
    ```
    ```console
    $ controller --help
    usage: controller [-h] [-e ENV_FILE]

    Controller CLI

    optional arguments:
    -h, --help            show this help message and exit
    -e ENV_FILE, --env-file ENV_FILE
                            Path to the .env file containing the parameters for the controller
    ```
1. Show the usage of the CLI:
    ```console
    controller> help
    ```
