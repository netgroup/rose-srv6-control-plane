# Node Manager

## Prerequisites

The following dependencies are necessary:

* Python 3.6 or above

## Installation

1. Create a Python 3 virtual environment for the Node Manager:
    ```console
    $ python3 -m venv ~/.envs/node-mgr-venv
    ```
1. Activate the virtual environment:
    ```console
    $ source ~/.envs/node-mgr-venv-venv/bin/activate
    ```
1. Clone *rose-srv6-control-plane* reposistory using ```git```:
    ```console
    $ cd workspace
    $ git clone https://github.com/netgroup/rose-srv6-control-plane.git
    ```
1. Then, ```cd``` to the *control_plane/node-manager* directory under the *rose-srv6-control-plane* folder and run the install command:
    ```console
    $ cd rose-srv6-control-plane/control_plane/node-manager
    $ python setup.py install
1. This project depends on the gRPC protocol, which requires protobuf modules. ```cd``` to the *control_plane/protos* directory under the *rose-srv6-control-plane* folder and run the install command to setup the proto files:
    ```console
    $ cd rose-srv6-control-plane/control_plane/protos
    $ python setup.py install
    ```    

## Configuration

* The node-manager comes with a default configuration. If you want to override the default settings, you can create a *.env* file containing the configuration parameters:
    ```sh
    export GRPC_IP=::
    export GRPC_PORT=12345
    export GRPC_SECURE=True
    export GRPC_SERVER_CERTIFICATE_PATH=/tmp/server.crt
    export GRPC_SERVER_KEY_PATH=/tmp/server.key
    export DEBUG=True
    ```
    * *DEBUG*: enable debug logs
* To enable the optional features, you need to set the following parameters in your *.env* file:
    * SRv6 Manager support:
        ```sh
        export ENABLE_SRV6_MANAGER=True
        ```
        *ENABLE_SRV6_MANAGER* flag defines whether to enable or not SRv6 tunnel capabilities (default is True)
    * gRPC server on the controller (interface node->controller):
        ```sh
        export GRPC_CLIENT_SECURE=True
        export GRPC_CA_CERTIFICATE_PATH=/tmp/ca.crt
        export CONTROLLER_GRPC_IP=fcff:c::1
        export CONTROLLER_GRPC_PORT=12345
        ```
    * SRv6 PFPLM support requires [SRv6 PFPLM implementation using XDP/eBPF and tc/eBPF](https://github.com/netgroup/srv6-pm-xdp-ebpf) and [ROSE SRv6 Data-Plane](https://github.com/netgroup/rose-srv6-data-plane). Follow the instructions provided in section [Optional requirements](#optional-requirements) to setup the required dependencies and then set the following parameters in your *.env* configuration file:
        ```sh
        export ENABLE_SRV6_PM_MANAGER=True
        export SRV6_PM_XDP_EBPF_PATH=/home/rose/workspace/srv6-pm-xdp-ebpf
        export ROSE_SRV6_DATA_PLANE_PATH=/home/rose/workspace/rose-srv6-data-plane
        ```
The *config* folder in the node-manager directory provides a sample configuration file.


## Optional requirements
* SRv6 PFPLM requires [SRv6 PFPLM implementation using XDP/eBPF and tc/eBPF](https://github.com/netgroup/srv6-pm-xdp-ebpf) and [ROSE SRv6 Data-Plane](https://github.com/netgroup/rose-srv6-data-plane).
* In order to setup *SRv6 PFPLM implementation using XDP/eBPF and tc/eBPF* you need to clone the github repository and follow the setup instructions contained in *README.md*:
    ```console
    $ git clone -b srv6-pfplm-dev-v2-rev_2 https://github.com/netgroup/srv6-pm-xdp-ebpf.git
    ```
Then, you need to add the path to the repository to your *.env* file, as described in the #configuration section.

* To setup the *rose-srv6-data-plane*, clone the repository and follow the setup instructions provided in *README.md*:
    ```console
    $ git clone https://github.com/netgroup/rose-srv6-data-plane.git
    ```
    and follow the setup instructions.


## Starting the Node Manager

1. Node Manager requires root permissions:
    ```console
    $ sudo su
    ```
1. Activate the Node Manager virtual environment:
    ```console
    # source ~/.envs/node-mgr-venv/bin/activate
    ```
1. To start the Node Manager:
    ```console
    # node_manager
    ```

    Optionally, you can provide command-line arguments to override the configuration parameters set in the *.env* file. For a detailed description of the available parameters, you can start the node_manager with the --help command-line argument:
    ```console
    # python node-manager --help
    usage: node_manager [-h] [-e ENV_FILE] [-g GRPC_IP] [-r GRPC_PORT] [-s] [-c SERVER_CERT] [-k SERVER_KEY] [-d]

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

    Note: the command-line arguments have priority over the parameters defined in the *.env* file.


## Documentation

For more information about the installation and usage of the Node Manager, see the full documentation at https://netgroup.github.io/rose-srv6-control-plane
