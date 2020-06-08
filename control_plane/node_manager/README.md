# Node Manager

## Installation

1. Clone this project:
    ```console
    $ git clone https://github.com/netgroup/rose-srv6-control-plane.git
    ```
1. Enter the node-manager folder under the project directory:
    ```console
    cd rose-srv6-control-plane/srv6_controller/node-manager
    ```
1. Create a Python 3 virtualenv:
    ```console
    $ python3 -m venv ./.venv
    ```
1. Activate the virtualenv:
    ```console
    $ source ./.venv/bin/activate
    ```
1. Install dependencies:
    ```console
    $ pip install -r requirements.txt
    ```
1. Enter the protos folder and build the .proto files:
    ```console
    $ cd ../protos
    $ bash build.sh
    ```
    A *gen-py* folder is create under the *protos* folder. This folder contain the files auto-generated from the .proto files.
1. Create a *.env* file in the node-manager directory, containing something like:
    ```sh
    export PROTO_PATH=/home/rose/workspace/rose-srv6-control-plane/srv6_controller/protos/gen-py
    export ENABLE_SRV6_MANAGER=True
    ```
    *PROTO_PATH* must point to the folder containing the files auto-generated from the .proto files

    *ENABLE_SRV6_MANAGER* flag defines whether to enable or not SRv6 tunnel capabilities (default is True)
1. Other parameters are optional and can be used to override the default values:
    ```sh
    export GRPC_IP=::
    export GRPC_PORT=12345
    export GRPC_SECURE=True
    export GRPC_SERVER_CERTIFICATE_PATH=/tmp/server.crt
    export GRPC_SERVER_KEY_PATH=/tmp/server.key
    export DEBUG=True
    ```
1. If you want to use the gRPC interface node->controller, you need to set the following parameters:
    ```sh
    export GRPC_CLIENT_SECURE=True
    export GRPC_CA_CERTIFICATE_PATH=/tmp/ca.crt
    export CONTROLLER_GRPC_IP=fcff:c::1
    export CONTROLLER_GRPC_PORT=12345
    ```

In order to simplify the configuration, we provide a sample configuration file named sample.env

## Optional Requirements

Some functions require extra packages:
* SRv6 PFPLM requires [SRv6 PFPLM implementation using XDP/eBPF and tc/eBPF](https://github.com/netgroup/srv6-pm-xdp-ebpf) and [ROSE SRv6 Data-Plane](https://github.com/netgroup/rose-srv6-data-plane)
    
    If you want to use SRv6 PFPLM functions, you need to clone the two repositories:
    ```console
    $ git clone https://github.com/netgroup/srv6-pm-xdp-ebpf.git
    $ git clone https://github.com/netgroup/rose-srv6-data-plane.git
    ```
    And you need to set the *ENABLE_SRV6_PM_MANAGER* flag and the paths to the repositories in the *.env* file:

    ```sh
    export ENABLE_SRV6_PM_MANAGER=True
    export SRV6_PM_XDP_EBPF_PATH=/home/rose/workspace/srv6-pm-xdp-ebpf
    export ROSE_SRV6_DATA_PLANE_PATH=/home/rose/workspace/rose-srv6-data-plane
    ```

## Starting the Node Manager

1. Enter the node-manager folder under the project directory:
    ```console
    cd rose-srv6-control-plane/srv6_controller/node-manager
    ```
1. Activate the virtualenv:
    ```console
    $ source ./.venv/bin/activate
    ```
1. To start the Node Manager:
    ```console
    $ python node-manager.py
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