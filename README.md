# ROSE SRv6 Control Plane <img align="right" src="https://img.shields.io/github/stars/netgroup/rose-srv6-control-plane?style=social">

<div align="center">
    <div align="center">
        <img src="https://img.shields.io/badge/python-3.6|3.7|3.8-blue?logo=python">
        <img src="https://github.com/netgroup/rose-srv6-control-plane/workflows/Python%20package/badge.svg">
        <img src="https://github.com/netgroup/rose-srv6-control-plane/workflows/Lint%20Code%20Base/badge.svg">
        <img src="https://img.shields.io/github/license/netgroup/rose-srv6-control-plane">
        <img src="https://img.shields.io/github/v/release/netgroup/rose-srv6-control-plane?sort=semver">
    </div>
    <div align="center">
        <img src="https://img.shields.io/github/release-date/netgroup/rose-srv6-control-plane">
        <img src="https://img.shields.io/github/issues/netgroup/rose-srv6-control-plane">
        <img src="https://img.shields.io/github/issues-closed/netgroup/rose-srv6-control-plane">
        <img src="https://img.shields.io/github/issues-pr/netgroup/rose-srv6-control-plane">
        <img src="https://img.shields.io/github/issues-pr-closed/netgroup/rose-srv6-control-plane">
        <!--<img src="https://img.shields.io/github/contributors/netgroup/rose-srv6-control-plane">-->
        <!--<img src="https://img.shields.io/github/commit-activity/m/netgroup/rose-srv6-control-plane">-->
    </div>
</div>
<br />

> Control plane functionalities for SDN.

<img align="right" src="docs/images/rose-logo-recolored-red-200x60.png">
<br />

## Table of Contents
* [Getting Started](#getting-started)
* [Project Overview](#project-overview)
    * [Database utilities](#database-utilities)
    * [Control plane functionalities](#control-plane-functionalities)
        * [Node manager](#node-manager)
        * [Controller](#controller)
        * [Protocol Buffers](#protocol-buffers)
        * [Usage examples](#usage-examples)
            * [How to use the Controller CLI](#how-to-use-the-controller-cli)
            * [How to use the Controller API in your Python application](#how-to-use-the-controller-api-in-your-python-application)
* [Docker](#docker)
    * [Build the Docker image](build-the-docker-image)
    * [Run the controller container](#run-the-controller-container)
    * [Run the node-manager container](#run-the-node-manager-container)
    * [Access to the Docker container](#access-to-the-docker-container)
* [Requirements](#requirements)
* [Links](#links)
* [Issues](#issues)
* [Contributing](#contributing)
* [License](#license)


## Getting Started

This project provides a collection of modules implementing different control plane functionalities of a Software Defined Network (SDN), including SRv6 tunnel management aspects, exporting and uploading the network topology to a database and monitoring the performance of a network.

The project is part of a larger ecosystem called [Research on Open SRv6 Ecosystem (ROSE)](https://netgroup.github.io/rose/).

To start using the project, you need to clone this repository:

```console
$ git clone https://github.com/netgroup/rose-srv6-control-plane
```

## Project Overview

This repository is structured as follows:

    .
    ├── db_update           # Database utilities
    ├── control_plane       # Control plane modules
    ├── Dockerfile          # Dockerfile
    ├── LICENSE             # Apache 2.0 license text
    └── README.md


### Database utilities

*db_update* is a Python library used to connect the Controller to a database. Using this library, the Controller can interact with a database in order to store information like the topology graph of a network.


## Control plane functionalities

The *control_plane* folder contains the two main components of this project:
* Controller, a SDN Controller
* Node Manager, an agent that must be installed on the node that you want to control through the SDN Controller.

The Controller uses a gRPC API to contact the Linux nodes. A gRPC server (Node Manager) must be run on the Linux nodes that you want to control through the Controller.
The Controller (i.e. the gRPC client from the point of view of the gRPC protocol) interacts with the gRPC server executed on the nodes to enforce rules or configurations, such as the setup of SRv6 paths and behaviors.

The control-plane modules are organized as follows:

    .
    ├── ...
    ├── control_plane       # Control plane modules
    |   ├── controller      # Controller (gRPC client)
    |   ├── examples        # Usage examples
    |   ├── node-manager    # Node Manager (gRPC server)
    |   └── protos          # Protocol buffer files
    └── ...


### Node manager

The **control_plane/node-manager** package implements the functionalities of an agent which connects a Linux node to the Controller. A Node Manager must be executed on each node that you want to control through the Controller.

Refer the [Docker](#docker) section for details on how to use the Node Manager in a pre-built docker container. For more information about the installation and usage of the Node Manager follow the instructions contained in the *README.md* file under the *node-manager* folder.


### Controller
The **control_plane/controller** package implements different functionalities of a Controller.

Refer the [Docker](#docker) section for details on how to use the Controller in a pre-built docker container. For more information about the installation and usage of the Node Manager follow the instructions contained in the *README.md* file under the *controller* folder.


### Protocol Buffers
This project depends on the **grpcio** library that provides an implementation of the gRPC protocol. gRPC services use Protocol Buffers as Interface Description Language (IDL). Consequently, both the Controller and the Node Manager require some Python classes generated from the .proto files stored in the **control_plane/protos** folder.
The compilation and generation of the Python classes required by the gRPC protocol has been automated in the setup scripts of the Controller and Node Manager.


### Usage examples
There are two ways to use the functionalities offered by the Controller. You can execute the Python Command-Line Interface (CLI) provided by the Controller or you can import the Controller modules in your Python application and use the API exposed by the Controller.

#### How to use the Controller CLI
For a description of the CLI and the supported commands, see the documentation contained in the [control_plane/controller](control_plane/controller/README.md) folder.

#### How to use the Controller API in your Python application
For a description of the API exposed by the Controller, see the API reference contained in the [control_plane/controller](control_plane/controller/README.md) folder.
Moreover, the usage examples contained in the **control_plane/examples** folder can be an excellent starting point for understanding how to use the API and the features of the Controller.


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


## Requirements
* Linux kernel >= 4.14
* Python >= 3.6


## Links
* Research on Open SRv6 Ecosystem (ROSE): https://netgroup.github.io/rose/
* Source code: https://github.com/netgroup/rose-srv6-control-plane
* Report a bug: https://github.com/netgroup/rose-srv6-control-plane/issues


## Issues
You are welcome to open github issues for bug reports and feature requests, in [this repository](https://github.com/netgroup/rose-srv6-control-plane/issues) or in the [ROSE repository](https://github.com/netgroup/rose/issues).


## Contributing
If you want to contribute to the ecosystem, provide feedback or get in touch with us, see our contact page: https://netgroup.github.io/rose/rose-contacts.html.


## Versioning
We use [SemVer](https://semver.org/) for versioning.


## License
This project is licensed under the [Apache License, Version 2.0](https://github.com/netgroup/rose-srv6-control-plane/blob/master/LICENSE).
