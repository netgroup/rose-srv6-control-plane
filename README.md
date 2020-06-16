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
    * [Installation](#Installation-1)
    * [Usage](#Usage-1)
* [Usage examples](#usage-examples)
* [Requirements](#requirements)
* [Links](#links)
* [Issues](#issues)
* [Contributing](#contributing)
* [License](#license)


## Getting Started

This project provides a collection of modules implementing different control plane functionalities of a Software Defined Network (SDN).

First, you need to clone this repository.

```console
$ cd workspace
$ git clone https://github.com/netgroup/rose-srv6-control-plane
```

The project is structured as follows:

    .
    ├── db_update           # Database utilities
    ├── control_plane       # Modules implementing control plane functionalities
    └── README.md


## Database utilities
The *db_update* folder contains several modules used by the Controller to interact with an ArangoDB database.


## Control plane functionalities

The Controller uses a gRPC API to contact the Linux nodes. A gRPC server (Node Manager) must be run on the Linux nodes that you want to control through the Controller. The gRPC server receives gRPC requests from the Controller, performs the requested task and returns a reply containing the status code of the operation and other parameters depending on the specific operation.

The Controller leverages the gRPC API to enforce rules and commands on the Linux nodes, such as the setup of SRv6 paths and behaviors.

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

The **control_plane/node-manager** folder contains some modules that allow a Linux node to interact with a Controller by using the gRPC protocol.

A Node Manager instance must be executed on each node that you want to control from the Controller.

For more information about the installation and usage of the Node Manager follow the instructions contained in the *README.md* file under the *node-manager* folder.


## Controller
The **control_plane/controller** folder provides a collection of modules implmenting different functionalities of a Controller.

For more information about the installation and usage of the Node Manager follow the instructions contained in the *README.md* file under the *controller* folder.


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
--
