.. _controller-configuration:

Configuration
=============

The Controller is configured with a env-based configuration file, ``controller.env``.

The ``config/controller.env`` file contains an example of configuration for the
Controller, which is the configuration used by default:

.. literalinclude:: ../../control_plane/controller/controller/config/controller.env
  :language: bash
  :caption: controller.env
  :name: controller.env

If you want to override the default settings, you can create a *controller.env*
file containing the desired configuration parameters.

The next section shows the available configuration options.

Configuration options
~~~~~~~~~~~~~~~~~~~~~

This section shows a list of the available configuration options for the Controller.
You can set configuration parameters by using the syntax of the environment variables:

.. code:: bash

  export ATTRIBUTE=VALUE

where ATTRIBUTE is the name of the configuration option that you want to set
and VALUE is the value to be assigned to the option.

To use your custom configuration, you can pass your *.env* configuration file
to the Controller when it is started, as explained in the
:ref:`controller-load-config` section.

General settings
################

.. list-table:: General settings for controller.env
    :widths: 15 15 10 60
    :header-rows: 1


    * - Attribute
      - Type
      - Default
      - Description
    * - GRPC_SECURE
      - boolean
      - False
      - | If True, the Controller will use the TLS
        | to encrypt and authenticate the traffic
        | sent to the Node Manager on the gRPC
        | Channel.
    * - GRPC_CA_CERTIFICATE_PATH
      - string
      - None
      - | Name of CA certificate for the TLS,
        | required if GRPC_SECURE is True.
    * - DEBUG
      - boolean
      - False
      - If True, the debug logging is enabled.

ArangoDB settings
#################

Some features offered by the Controller are related to ArangoDB, such as exporting
the network topology to a database.

If you want to use these features, you need to enable the ArangoDB integration
and to configure the parameters listed in this section.

If you are not interested in using features that depend on ArangoDB, you
can skip this section.

.. list-table:: ArangoDB settings for controller.env
    :widths: 15 15 10 60
    :header-rows: 1


    * - Attribute
      - Type
      - Default
      - Description
    * - ENABLE_ARANGO_INTEGRATION
      - boolean
      - False
      - | If True, the ArangoDB features
        | are enabled.
    * - ARANGO_URL
      - string
      - None
      - | The URL of the ArangoDB database, 
        | required if
        | ENABLE_ARANGO_INTEGRATION
        | is True.
    * - ARANGO_USER
      - string
      - None
      - | The username used to log in the
        | ArangoDB database, required if
        | ENABLE_ARANGO_INTEGRATION
        | is True.
    * - ARANGO_PASSWORD
      - string
      - None
      - | The password used to log in the
        | ArangoDB database, required if
        | ENABLE_ARANGO_INTEGRATION
        | is True.

.. note:: the *db_update* library is required to support ArangoDB integration. 
  Follow the instructions provided in :ref:`controller-installation-opt-req`
  section to setup the required dependencies.

Kafka settings
##############

Some features offered by the Controller are related to Kafka, such as exporting
the performance measurement data.

If you want to use these features, you need to enable the Kafka integration
and to configure the parameters listed in this section.

If you are not interested in using features that depend on Kafka, you
can skip this section.

.. list-table:: Kafka settings for controller.env
    :widths: 15 15 10 60
    :header-rows: 1


    * - Attribute
      - Type
      - Default
      - Description
    * - ENABLE_KAFKA_INTEGRATION
      - boolean
      - False
      - If True, the Kafka features are enabled.
    * - KAFKA_SERVERS
      - string
      - None
      - | A comma-separated list of Kafka servers 
        | (e.g. "kafka:9092,localhost9000").

.. note:: the *kafka-python* package is required to support 
  Kafka integration. Follow the instructions provided in 
  :ref:`controller-installation-opt-req` section
  to setup the required dependencies.

gRPC server settings
####################

The Controller uses the gRPC protocol to interact with the nodes.
In most use-cases it acts as a gRPC client, while the node executes the
gRPC server.
Optionally, you can also executes a gRPC server on the Controller.
This enables several use-cases where the nodes need to send information to
the Controller (e.g. performance measurement data).
This section explains how to enable and configure this functionality.

.. list-table:: gRPC server settings for controller.env
    :widths: 15 15 10 60
    :header-rows: 1


    * - Attribute
      - Type
      - Default
      - Description
    * - ENABLE_GRPC_SERVER
      - boolean
      - False
      - | If True, a gRPC server will be
        | started on the Controller.
        | This will enable the creation of
        | (Node -> Controller) gRPC Channels.
        | This feature allows a Node to
        | contact the Controller and 
        | it is used in some use-case
        | like performance monitoring.
    * - GRPC_SERVER_IP
      - string
      - \::
      - | The IP address on which the gRPC
        | server will listen for 
        | connections ("::" means "any").
    * - GRPC_SERVER_PORT
      - integer
      - 12345
      - | The TCP port on which the gRPC
        | server will listen for connections.
    * - GRPC_SERVER_SECURE
      - boolean
      - False
      - | If True, the Controller will use
        | the TLS to encrypt and authenticate 
        | the traffic exchanged with the
        | Node Manager on the
        | (Node -> Controller) gRPC Channel.
    * - GRPC_SERVER_CERTIFICATE_PATH
      - string
      - None
      - | Name of the server certificate for
        | the TLS, required if
        | GRPC_SERVER_SECURE is True.
    * - GRPC_SERVER_KEY_PATH
      - string
      - None
      - | Name of the server private key for
        | the TLS, required if
        | GRPC_SERVER_SECURE is True.

Verifying configuration
-----------------------

You can verify that your configuration is correct with the ``check_controller_config`` script:

.. code:: console

  check_controller_config /etc/rose-srv6-control-plane/controller.env

Configuration examples
----------------------

For an example of configuration, you can see the ``config/controller.env`` file.
It is the default configuration used by the Controller. You can use this file as
a template for your custom configuration.

.. _controller-load-config:

Load configuration
------------------

In order to load your configuration in the Controller, you can pass the path of your
*controller.env* configuration file when you start the Controller:

.. code:: console

  $ controller --env-file controller.env

For more information about the usage of the Controller and the supported Command-Line
arguments, see the :ref:`controller-usage` section.

Command-Line arguments
----------------------

You can interact with the Controller through a CLI. You can provide Command-Line arguments
to the CLI to override the settings written in your *controller.env*
file such as paths for certificate files and port numbers.

For more information about the CLI and the supported Command-Line arguments,
see the :ref:`controller-usage` section.
