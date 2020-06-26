.. _node-mgr-configuration:

Configuration
=============

The Node Manager is configured with a env-based configuration file, ``node_manager.env``.

The ``config/node_manager.env`` file contains an example of configuration for the
Node Manager, which is the configuration used by default:

.. literalinclude:: ../../control_plane/node-manager/node_manager/config/node_manager.env
  :language: bash
  :caption: node_manager.env
  :name: node_manager.env

If you want to override the default settings, you can create a *node_manager.env*
file containing the desired configuration parameters.

The next section shows the available configuration options.

Configuration options
~~~~~~~~~~~~~~~~~~~~~

This section shows a list of the available configuration options for the Node Manager.
You can set configuration parameters by using the syntax of the environment variables:

.. code:: bash

  export ATTRIBUTE=VALUE

where ATTRIBUTE is the name of the configuration option that you want to set
and VALUE is the value to be assigned to the option.

To use your custom configuration, you can pass your *.env* configuration file
to the Node Manager when it is started, as explained in the
:ref:`node-mgr-load-config` section.

General settings
################

.. list-table:: General settings for node_manager.env
    :widths: 15 15 10 60
    :header-rows: 1


    * - Attribute
      - Type
      - Default
      - Description
    * - GRPC_IP
      - string
      - \::
      - IP of the gRPC server.
    * - GRPC_PORT
      - integer
      - 12345
      - Port of the gRPC server.
    * - GRPC_SECURE
      - boolean
      - False
      - | If True, the Node Manager will use
        | the TLS to encrypt and authenticate
        | the traffic sent to the Node Manager
        | on the gRPC Channel.
    * - GRPC_SERVER_CERTIFICATE_PATH
      - string
      - None
      - | Name of server certificate for the TLS,
        | required if GRPC_SECURE is True.
    * - GRPC_SERVER_KEY_PATH
      - string
      - None
      - | Name of server key for the TLS,
        | required if GRPC_SECURE is True.
    * - DEBUG
      - boolean
      - False
      - If True, the debug logging is enabled.

The design of the node manager is highly modular. It is composed by different
components that can be enabled or disabled in your configuration file.

The current release has two components: :ref:`node-mgr-configuration-srv6-manager` and :ref:`node-mgr-configuration-srv6pm-manager`,
described in the next sections.

.. _node-mgr-configuration-srv6-manager:

SRv6 Manager
############

The **SRv6 Manager** allows a Controller to enforce SRv6 rules and behaviors to
the node. This can be used for example to create SRv6 tunnels between two nodes
of the network. This component is enabled by default.

.. list-table:: SRv6 Manager settings for node_manager.env
    :widths: 15 15 10 60
    :header-rows: 1


    * - Attribute
      - Type
      - Default
      - Description
    * - ENABLE_SRV6_MANAGER
      - boolean
      - True
      - If True, the SRv6 Manager is enabled.


.. _node-mgr-configuration-srv6pm-manager:

SRv6-PM Manager
###############

SRv6 PFPLM functionalities depend on the SRv6-PM Manager.

If you want to use these features, you need to enable the SRv6-PM Manager
support in your configuration and to set the parameters listed in this
section.

If you are not interested in using SRv6 PM features, you can skip this
section.

.. note:: SRv6 PFPLM support requires `SRv6 PFPLM implementation using
  XDP/eBPF and tc/eBPF <https://github.com/netgroup/srv6-pm-xdp-ebpf>`_
  and `ROSE SRv6 Data-Plane <https://github.com/netgroup/rose-srv6-data-plane>`_.
  Follow the instructions provided in :ref:`node-mgr-installation-opt-req`
  section to setup the required dependencies.

.. list-table:: SRv6-PM Manager settings for node_manager.env
    :widths: 15 15 10 60
    :header-rows: 1


    * - Attribute
      - Type
      - Default
      - Description
    * - ENABLE_SRV6_PM_MANAGER
      - boolean
      - False
      - If True, the SRv6 PM features are enabled.
    * - SRV6_PM_XDP_EBPF_PATH
      - string
      - None
      - | Path to folder where you cloned the
        | srv6-pm-xdp-ebpf-path library.

"gRPC server on the Controller" settings
########################################

The Controller uses the gRPC protocol to interact with the nodes.
In most use-cases it acts as a gRPC client, while the node executes the
gRPC server.
Optionally, you can also executes a gRPC server on the Controller.
This enables several use-cases where the nodes need to send information to
the Controller (e.g. performance measurement data).
To use this feature, you need to enable and configure it in the
Controller configuration. Then you need to set some parameters in the
configuration of the Node Manager.
This section explains how to configure this functionality on the Node Manager.

.. list-table:: gRPC server settings for node_manager.env
    :widths: 15 15 10 60
    :header-rows: 1


    * - Attribute
      - Type
      - Default
      - Description
    * - CONTROLLER_GRPC_IP
      - string
      - --
      - The IP address of the Controller.
    * - CONTROLLER_GRPC_PORT
      - integer
      - 12345
      - | The TCP port on which the Controller
        | will listen for gRPC connections.
    * - GRPC_CLIENT_SECURE
      - boolean
      - False
      - | If True, the Node Manager will use
        | the TLS to encrypt and authenticate 
        | the traffic exchanged with the
        | Controller on the
        | (Node -> Controller) gRPC Channel.
    * - GRPC_CA_CERTIFICATE_PATH
      - string
      - None
      - | Name of CA certificate for the TLS,
        | required if GRPC_CLIENT_SECURE is True.



Verifying configuration
-----------------------

You can verify that your configuration is correct with the ``check_node_manager_config`` script:

.. code:: console

  check_node_manager_config /etc/rose-srv6-control-plane/node_manager.env

Configuration examples
----------------------

For an example of configuration, you can see the ``config/node_manager.env`` file.
It is the default configuration used by the Node Manager. You can use this file as
a template for your custom configuration.

.. _node-mgr-load-config:

Load configuration
------------------

In order to load your configuration in the Node Manager, you can pass the
path of your *node_manager.env* configuration file when you start the
Node Manager:

.. code:: console

  $ node_manager --env-file node_manager.env

For more information about the usage of the Node Manager and the supported
Command-Line arguments, see the :ref:`node-mgr-usage` section.

Command-Line arguments
----------------------

You can provide Command-Line arguments to the Node Manager to override
the settings written in your *node_manager.env* file such as paths
for certificate files and port numbers.

For more information about the supported Command-Line arguments,
see the :ref:`node-mgr-usage` section.
