# Node Manager

## Installation

1. Clone this project:
    ```console
    $ git clone https://github.com/netgroup/rose-srv6-control-plane.git
    ```
1. Enter the controller folder under the project directory:
    ```console
    cd rose-srv6-control-plane/srv6_controller/controller
    ```
1. Create a Python 3 virtualenv:
    ```console
    $ python3 -m venv ./.venv
    ```
1. Activate the virtualenv:
    ```console
    $ source ./.venv/bin/activate
    ```
1. Install the dependencies:
    ```console
    $ pip install -r requirements.txt
    ```
1. Enter the protos folder and build the .proto files:
    ```console
    $ cd ../protos
    $ bash build.sh
    ```
    A *gen-py* folder is create under the *protos* folder. This folder contain the files auto-generated from the .proto files.
1. Create a *.env* file in the *controller* directory, containing something like:
    ```sh
    export PROTO_PATH=/home/rose/workspace/rose-srv6-control-plane/srv6_controller/protos/gen-py
    ```
    *PROTO_PATH* must point to the *gen-py* folder containing the files auto-generated from the .proto files
1. Other parameters are optional and can be used to override the default values:
    ```sh
    export GRPC_SECURE=True
    export GRPC_CA_CERTIFICATE_PATH=/tmp/ca.crt
    export DEBUG=True
    ```
1. Other parameters are feature-specific:
    1. ArangoDB related params
        ```sh
        export ENABLE_ARANGO_INTEGRATION=True
        export ARANGO_URL=http://localhost:8082
        export ARANGO_USER=root
        export ARANGO_PASSWORD=12345678
        ```
    1. Kafka related params:
        ```sh
        export ENABLE_KAFKA_INTEGRATION=True
        export KAFKA_SERVERS=kafka:9092
        ```
    1. gRPC server on controller (interface node->controller)
        ```sh
        export ENABLE_GRPC_SERVER=True
        export GRPC_SERVER_IP=::
        export GRPC_SERVER_PORT=12345
        export GRPC_SERVER_SECURE=True
        export GRPC_SERVER_CERTIFICATE_PATH=/tmp/server.crt
        export GRPC_SERVER_KEY_PATH=/tmp/server.key
        ```

In order to simplify the configuration, we provide a sample configuration file named sample.env

## Starting the Controller CLI

1. Enter the controller folder under the project directory:
    ```console
    cd rose-srv6-control-plane/srv6_controller/controller
    ```
1. Activate the virtualenv:
    ```console
    $ source ./.venv/bin/activate
    ```
1. To start the Controller CLI:
    ```console
    $ python controller.py
    ```
Optionally, you can provide command-line arguments to set configuration parameters. A description of the available parameters can be seen with this command:
```console
$ python node-manager.py --help
usage: node_manager.py [-h] [-e ENV_FILE] [-g GRPC_IP] [-r GRPC_PORT] [-s] [-c SERVER_CERT] [-k SERVER_KEY] [-d]

gRPC Southbound APIs for SRv6 Controller

optional arguments:
-h, --help            show this help message and exit
-e ENV_FILE, --env-file ENV_FILE
                        Path to the .env file containing the parameters for the node manager
-g GRPC_IP, --grpc-ip GRPC_IP
                        IP of the gRPC server
-r GRPC_PORT, --grpc-port GRPC_PORT
                        Port of the gRPC server
-s, --secure          Activate secure mode
-c SERVER_CERT, --server-cert SERVER_CERT
                        Server certificate file
-k SERVER_KEY, --server-key SERVER_KEY
                        Server key file
-d, --debug           Activate debug logs

```

Note that command-line arguments have priority over the parameters defined in the *.env* file