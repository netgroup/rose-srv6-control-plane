Release Log
===========

ROSE SRv6 Control Plane 0.1.0
-----------------------------

Release date: 23 June 2020

New features
~~~~~~~~~~~~
* Add a CLI for the controller
* Implement arguments tab-completion in Controller CLI
* Implement persistent command history for the Controller CLI
* Integrate topology extraction and ArangoDB functionalities in the controller
* Add SRv6 PM functionalities
* Add command-line arguments to Controller
* Add support for IPv4 addresses to gRPC client and server
* Separate venv for node-manager and controller
* Check root privileges in srv6_manager
* Improve controller and node manager configuration settings
* Add LICENSE file

Bug fixes
~~~~~~~~~
* Fix wrong proto_path and controller_path in srv6 controller scripts
* Improve setup of dependencies and fix import paths
* Clean and improve code
