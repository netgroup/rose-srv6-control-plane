# rose-srv6-control-plane
> Control plane functionalities for SDN.

![Python package](https://github.com/netgroup/rose-srv6-control-plane/workflows/Python%20package/badge.svg)
![GitHub](https://img.shields.io/github/license/netgroup/rose-srv6-control-plane)

## Table of Contents
* [Getting Started](#getting-started)
* [Control plane functionalities](#control-plane-functionalities)
    * [Setup](#setup)
    * [Node manager](#node-manager)
        * [Installation](#Installation)
        * [Usage](#Usage)
    * [Controller](#controller)
        * [Installation](#Installation)
        * [Usage](#Usage)
    * [Usage examples](#usage-examples)
* [Requirements](#requirements)
* [Links](#links)
* [Issues](#issues)
* [Contributing](#contributing)
* [License](#license)


## Getting Started

This project provides a collection of modules implementing different control plane functionalities of a Software Defined Network (SDN).

The project is structured as follows:

    .
    ├── db_update           # Scripts for the interaction with ArangoDB
    ├── docs                # Project documentation
    ├── srv6_controller     # Modules implementing control plane functionalities
    └── README.md


First, you need to clone this repository.

```console
user@rose-srv6:~$ cd workspace
user@rose-srv6:~$ git clone https://github.com/netgroup/rose-srv6-control-plane
```


## Control plane functionalities
The Controller uses a gRPC API to contact the Linux nodes. A gRPC server (node manager) must be run on the Linux nodes that we want to control through the Controller. This gRPC server listen for connections coming from the Controller on a given TCP port. It receives gRPC requests from the Controller, performs the requested task and returns a reply containing the status code of the operation and other parameters depending on the specific operation.

The Controller leverages the gRPC API to enforce rules and commands on the Linux nodes, such as the setup of SRv6 paths and behaviors.

This project also provides a collection of examples showing the interaction of a Controller with a Linux node.

The control plane modules are organized as follows:

    .
    ├── ...
    ├── srv6_controller     # Control plane modules
    |   ├── controller      # Controller (gRPC client)
    |   ├── examples        # Usage examples
    |   ├── node-manager    # Node manager (gRPC server)
    |   └── protos          # Protobuf files
    └── ...


### Node manager

The folder **srv6_controller/node-manager** provides the implementation of Node manager.


#### Installation

Create a virtual environment for the node manager.

```console
user@rose-srv6:~$ virtualenv -p python3 /root/.node-mgr-venv
```

Activate the virtual environment.

```console
user@rose-srv6:~$ source /root/.node-mgr-venv/bin/activate
```

Navigate to the folder of the node manager.

```console
user@rose-srv6:~$ cd srv6_controller/node-manager
```

Install the dependencies.

```console
user@rose-srv6:~$ pip install -r requirements.txt
```

Edit the file *.venv* to make it pointing to the virtual environment folder.
```text
/root/.node-mgr-venv
```


#### Usage

Run a node manager listening on any interface.
*srv6_manager.py* needs root permission.

```console
user@rose-srv6:~$ python srv6_manager.py --grpc_port 50000
```

Optionally, you can pass some command-line parameters to the node manager.
You can invoke *srv6_manager.py* with the *--help* argument to show a list of the supported parameters.

```console
user@rose-srv6:/root/rose# python srv6_manager.py --help
usage: srv6_manager.py [-h] [-g GRPC_IP] [-r GRPC_PORT] [-s] [-c SERVER_CERT]
                       [-k SERVER_KEY] [-d]

gRPC Southbound APIs for SRv6 Controller

optional arguments:
  -h, --help            show this help message and exit
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


## Controller
The folder **srv6_controller/controller** provides a collection of modules implmenting different functionalities of a Controller.

The script **srv6_controller.py** implements functionalities related to Segment Routing over IPv6 (SRv6). This functionalities include the setup of the connection with nodes and the configuration of SRv6 paths and SRv6 behaviors on the nodes.

The script **ti_extraction.py** implements functionalities related to topology extraction.


#### Installation

Create a virtual environment for the controller.

```console
user@rose-srv6:~$ virtualenv -p python3 /root/.controller-venv
```

Activate the virtual environment.

```console
user@rose-srv6:~$ source /root/.controller-venv/bin/activate
```

Navigate to the folder of the controller.

```console
user@rose-srv6:~$ cd srv6_controller/controller
```

Install the dependencies.

```console
user@rose-srv6:~$ pip install -r requirements.txt
```

Edit the file *.venv* to make it pointing to the virtual environment folder of the controller.
```text
/root/.controller-venv
```


#### Usage

##### From a python script

Add the the controller folder to the path in your script.

```python
import sys
sys.path.append('/root/rose/workspace/rose-srv6-control-plane/srv6_controller/controller/')
```

Import the srv6_controller module.

```python
import srv6_controller
```

Get a gRPC Channel to a gRPC server.

```python
channel = srv6_controller.get_grpc_session('fcff:1::1', 50000)
```

Have fun with the API provided by the controller.

```python
srv6_channel.
```

Close the gRPC Channel.

```python
channel.close()
```

##### From a CLI

This feature is not yet available.


### Usage examples

This project also provides a collection of examples showing the interaction of a Controller with a Linux node.

The folder **srv6_controller/examples** contains the following examples:
* *create_tunnel_r1r4r8.py*, showing the creation of a SRv6 tunnel passing through the router r4.
* *create_tunnel_r1r7r8.py*, showing the creation of a SRv6 tunnel passing through the router r4.
* *shift_path.py*, showing how it is possible to change paths by playing with the metric value of the routes.
* *remove_tunnel_r1r4r8.py*, showing the removal of the SRv6 tunnel passing through the router r4.
* *remove_tunnel_r1r7r8.py*, showing the removal of the SRv6 tunnel passing through the router r7.
* *load_topo_on_arango*, showing how the network topology can be loaded on ArangoDB.

These examples are intented to be run on the 8r-1c-in-band-isis Mininet-emulated topology, provided by https://github.com/netgroup/rose-srv6-tutorial.

For a detailed explaination of the examples, see the documentation at https://docs.google.com/document/d/1izO3H8dUt7VoemXtcH-RG4cL127tG9m48edOdFFmktU/


## Requirements
Python >= 3.4


## Links
* Research on Open SRv6 Ecosystem (ROSE): https://netgroup.github.io/rose/
* Source code: https://github.com/netgroup/rose-srv6-control-plane
* Report a bug: https://github.com/netgroup/rose-srv6-control-plane/issues


## Issues
You are welcome to open github issues for bug reports and feature requests, in [this repository](https://github.com/netgroup/rose-srv6-control-plane/issues) or in the [ROSE repository](https://github.com/netgroup/rose/issues).


## Contributing
If you want to contribute to the ecosystem, provide feedback or get in touch with us, see our contact page: https://netgroup.github.io/rose/rose-contacts.html.


## License
--
