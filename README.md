# rose-srv6-control-plane
> Control plane functionalities for SDN.

![Python package](https://github.com/netgroup/rose-srv6-control-plane/workflows/Python%20package/badge.svg)
![GitHub](https://img.shields.io/github/license/netgroup/rose-srv6-control-plane)

## Table of Contents
* [Getting Started](#getting-started)
* [Control plane functionalities](#control-plane-functionalities)
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

The Controller uses a gRPC API to contact the Linux nodes. A gRPC server (Node manager) must be run on the Linux nodes that we want to control through the Controller. This gRPC server listens for connections coming from the Controller on a given TCP port. It receives gRPC requests from the Controller, performs the requested task and returns a reply containing the status code of the operation and other parameters depending on the specific operation.

The Controller leverages the gRPC API to enforce rules and commands on the Linux nodes, such as the setup of SRv6 paths and behaviors.

This project also provides a collection of examples showing the interaction of a Controller with a Linux node.

The control plane modules are organized as follows:

    .
    ├── ...
    ├── srv6_controller     # Control plane modules
    |   ├── controller      # Controller (gRPC client)
    |   ├── examples        # Usage examples
    |   ├── node-manager    # Node manager (gRPC server)
    |   └── protos          # Protocol buffer files
    └── ...


## Node manager

The folder **srv6_controller/node-manager** contains some modules implementing the functionalities of a Node manager.

A Node manager instance must be executed on each node that we want to be able to control by using the Controller.


### Installation

Create a virtual environment for the Node manager.

```console
user@rose-srv6:~$ virtualenv -p python3 /root/.node-mgr-venv
```

Activate the virtual environment.

```console
user@rose-srv6:~$ source /root/.node-mgr-venv/bin/activate
```

Navigate to the folder of the Node manager.

```console
user@rose-srv6:~$ cd srv6_controller/node-manager
```

Install the dependencies.

```console
user@rose-srv6:~$ pip install -r requirements.txt
```

Edit the file *.venv* in the node-manager folder to make it pointing to the virtual environment folder.
```text
/root/.node-mgr-venv
```

Compile the protocol buffers.

```console
user@rose-srv6:~$ cd protos
user@rose-srv6:~$ bash build.sh
```


### Usage

Activate the virtual environment of the Node manager.

```console
user@rose-srv6:~$ source /root/.node-mgr-venv/bin/activate
```

*Note: If you have configured the *.venv* to point to the virtual environment folder, the manual activation of the virtual environment is not needed, because the virtual environment provided by .venv is activated automatically when the scripts are loaded.*

Navigate to the folder of the Node manager.

```console
user@rose-srv6:~$ cd srv6_controller/node-manager
```

Run a Node manager listening on any interface.
Note: *srv6_manager.py* needs root permission.

```console
user@rose-srv6:/root/rose# python srv6_manager.py --grpc_port 50000
```

Optionally, you can pass some command-line parameters to the Node manager.
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

The script **srv6_controller.py** implements functionalities related to Segment Routing over IPv6 (SRv6), including the setup of the connection with nodes and the configuration of SRv6 paths and SRv6 behaviors on the nodes.

The script **ti_extraction.py** implements functionalities related to extraction of the network topology from a set of nodes running IS-IS routing protocol.

Moreover, several functions are provided to export the network topology in different formats (such as JSON and YAML).
These functions can be used in combination with the functionalities provided by *db_update* modules of this project to upload the topology graph on ArangoDB.


### Installation

Create a virtual environment for the Controller modules.

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

Compile the protocol buffers (not requested if you have already done it for the Node manager).

```console
user@rose-srv6:~$ cd protos
user@rose-srv6:~$ bash build.sh
```


### Usage

Activate the virtual environment of the Controller.

```console
user@rose-srv6:~$ source /root/.controller-venv/bin/activate
```

*Note: If you have configured the *.venv* to point to the virtual environment folder, the manual activation of the virtual environment is not needed, because the virtual environment provided by .venv is activated automatically when the scripts are loaded.*

Navigate to the folder of the Controller.

```console
user@rose-srv6:~$ cd srv6_controller/controller
```

You have two options to use the functionalities provided by the Controller:
* Use the controller functionalities from a python script.
* Use the CLI interface provided by this project.


#### From a python script

Add the containing the controller modules to the system path in your script.

```python
import sys
sys.path.append('/root/rose/workspace/rose-srv6-control-plane/srv6_controller/controller/')
```

Import the srv6_controller module.

```python
import srv6_controller
```

See https://docs.google.com/document/d/1izO3H8dUt7VoemXtcH-RG4cL127tG9m48edOdFFmktU for a detailed explaination of the functionalities supported by the Controller.

Example of SRv6 path:

```python
# Get a gRPC Channel to the gRPC server executing on 'fcff:1::1'
r1_chan = srv6_controller.get_grpc_session('fcff:1::1', 50000)
# Get a gRPC Channel to the gRPC server executing on 'fcff:8::1'
r1_chan = srv6_controller.get_grpc_session('fcff:8::1', 50000)
# Create a SRv6 path from 'fcff:1::1' to 'fcff:8::1'
srv6_controller.handle_srv6_path('add', r1_chan, destination='fd00:0:83::/64', segments=['fcff:7::1', 'fcff:8::100'], device='r1-h11', metric=100)
# Create the decap behavior on 'fcff:8::1'
srv6_controller.handle_srv6_behavior('add', r8_chan, segment='fcff:8::100', action='End.DT6', lookup_table=254, device='r8-h83', metric=100)
# Close the gRPC Channel
channel.close()
```

Example of interaction with ArangoDB:

```python
# Extract the topology from the two nodes 'fcff:1::1' and 'fcff:2::1', export it to 'nodes.yaml' and 'edges.yaml' files and load the topology on ArangoDB
srv6_controller.extract_topo_from_isis_and_load_on_arango(isis_nodes=['fcff:1::1-2608','fcff:2::1-2608'], arango_url='http://localhost:8529',
                                                          arango_user='root',
                                                          arango_password='12345678',
                                                          nodes_yaml='nodes.yaml', edges_yaml='edges.yaml',
                                                          period=0, verbose=False)
```


#### From a CLI

This feature is not yet available.


## Usage examples

This project also provides a collection of examples showing the interaction of a Controller with a Linux node.

The examples are structure as follows:

    .
    ├── ...
    ├── srv6_controller
    |   ├── ...
    |   ├── examples
    |   |   ├── create_tunnel_r1r4r8.py           # Create a SRv6 tunnel passing though the router r4
    |   |   ├── create_tunnel_r1r7r8.py           # Create tunnel passing though the router r7
    |   |   ├── shift_path.py                     # Change the SRv6 tunnel used to route the packets
    |   |   ├── remove_tunnel_r1r4r8.py           # Remove the tunnel passing though the router r4
    |   |   ├── remove_tunnel_r1r7r8.py           # Remove the tunnel passing though the router r7
    |   |   └── load_topo_on_arango.py            # Extract network topology and load it on ArangoDB
    |   └── ...
    └── ...

These examples are intented to be run on the *8r-1c-in-band-isis* Mininet-emulated topology, provided by https://github.com/netgroup/rose-srv6-tutorial.

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
