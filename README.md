# ROSE SRv6 Control Plane
> Control plane functionalities for SDN.

![Python package](https://github.com/netgroup/rose-srv6-control-plane/workflows/Python%20package/badge.svg)
![Python Lint Code Base](https://github.com/netgroup/rose-srv6-control-plane/workflows/Lint%20Code%20Base/badge.svg)
![GitHub](https://img.shields.io/github/license/netgroup/rose-srv6-control-plane)
![Release Version](https://img.shields.io/github/v/tag/netgroup/rose-srv6-control-plane?sort=semver)

## Table of Contents
* [Getting Started](#getting-started)
* [Docker](#docker)
    * [Build the Docker image](build-the-docker-image)
    * [Run the controller container](#run-the-controller-container)
    * [Run the node-manager container](#run-the-node-manager-container)
    * [Access to the Docker container](#access-to-the-docker-container)
* [Database utilities](#database-utilities)
* [Control plane functionalities](#control-plane-functionalities)
    * [Node manager](#node-manager)
    * [Controller](#controller)
    * [Protocol Buffers](#protocol-buffers)
    * [Usage examples](#usage-examples)
        * [How to use the Controller CLI](#how-to-use-the-controller-cli)
        * [How to use the Controller API in your Python application](#how-to-use-the-controller-api-in-your-python-application)
* [Requirements](#requirements)
* [Links](#links)
* [Issues](#issues)
* [Contributing](#contributing)
* [License](#license)


## Getting Started

This project provides a collection of modules implementing different control plane functionalities of a Software Defined Network (SDN).

First, you need to clone this repository.

```console
$ git clone https://github.com/netgroup/rose-srv6-control-plane
```

The project is structured as follows:

    .
    ├── db_update           # Database utilities
    ├── control_plane       # Modules implementing control plane functionalities
    └── README.md


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

    docker run --name rose-srv6-node-manager -p 12345:12345 rose-srv6-node-manager:latest

### Access to the Docker container

    docker exec -it <container_name> bash

for instance access to rose-srv6-controller with:

    docker exec -it rose-srv6-node-manager bash


## Database utilities
The *db_update* folder contains several modules used by the Controller to interact with an ArangoDB database.


## Control plane functionalities

The Controller uses a gRPC API to contact the Linux nodes. A gRPC server (Node Manager) must be run on the Linux nodes that you want to control through the Controller.

The Controller interacts with the gRPC server executed on the nodes to enforce rules and commands, such as the setup of SRv6 paths and behaviors.

The control-plane modules are organized as follows:

    .
    ├── ...
    ├── control_plane     # Control plane modules
    |   ├── controller      # Controller (gRPC client)
    |   ├── examples        # Usage examples
    |   ├── node-manager    # Node Manager (gRPC server)
    |   └── protos          # Protocol buffer files
    └── ...


## Node manager

The **control_plane/node-manager** package implements the functionalities of a gRPC server.
A gRPC server must be executed on each node that you want to control from the Controller.

For more information about the installation and usage of the Node Manager follow the instructions contained in the *README.md* file under the *node-manager* folder.


## Controller
The **control_plane/controller** package provides a collection of modules implmenting different functionalities of a Controller.

For more information about the installation and usage of the Node Manager follow the instructions contained in the *README.md* file under the *controller* folder.


## Protocol Buffers
This project depends on the **grpcio** library that provides an implementation of the gRPC protocol. gRPC services use Protocol Buffers as Interface Description Language (IDL). Consequently, both the Controller and the Node Manager require some Python classes generated from the .proto files stored in the **control_plane/protos** folder.
Since the compilation and generation of the Python classes from the .proto files has been automated in the setup scripts, the manual generation of this classes is no longer required.


## Usage examples
There are two ways to use the functionalities offered by the Controller. You can execute the Python Command-Line Interface (CLI) provided by the Controller or you can import the Controller modules in your Python modules and use the API exposed by the Controller.

### How to use the Controller CLI
A description of the CLI and the supported commands is provided in the documentation contained in [control_plane/controller](control_plane/controller/README.md).

### How to use the Controller API in your Python application
The **control_plane/examples** directory contains several usage examples for the API exposed by the Controller. For the description of the API and the examples, check the documentation contained in the [control_plane/examples folder](control_plane/examples/README.md).


## Requirements
Python >= 3.6


## Links
* Research on Open SRv6 Ecosystem (ROSE): https://netgroup.github.io/rose/
* Source code: https://github.com/netgroup/rose-srv6-control-plane
* Report a bug: https://github.com/netgroup/rose-srv6-control-plane/issues


## Issues
You are welcome to open github issues for bug reports and feature requests, in [this repository](https://github.com/netgroup/rose-srv6-control-plane/issues) or in the [ROSE repository](https://github.com/netgroup/rose/issues).


## Contributing
If you want to contribute to the ecosystem, provide feedback or get in touch with us, see our contact page: https://netgroup.github.io/rose/rose-contacts.html.


## License
This project is licensed under the [Apache License, Version 2.0](https://github.com/netgroup/rose-srv6-control-plane/blob/master/LICENSE).
