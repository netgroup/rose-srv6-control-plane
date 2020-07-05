.. _controller-cli-srv6-usid:

SRv6 uSID Functions
===================

The Controller supports the creation and management of several types
of SRv6 entities. These functions are available under the section
``srv6`` of the Command-Line Interface. The uSID sub-section contains
functions related to uSID.


Entering the ``srv6``/``usid`` section
--------------------------------------

.. note:: usid requires the argument --addrs-file, that is a YAML file
  containing the mapping of node names to IP addresses.

.. code:: bash

  controller> srv6
  controller(srv6)> usid --addrs-file nodes.yml
  controller(srv6-usid)> 

Section ``srv6``/``usid`` supports the following commands:

.. code:: bash

  exit  help  nodes  policy


``nodes``
------------

Print the list of the available nodes.

.. code:: bash

  controller(srv6-usid)> help nodes
  Show the list of the available devices


``policy``
----------

Create, get, change or remove a SRv6 uSID policy in a node.

.. code:: bash

  controller(srv6)> policy --help
  usage: path [-h] -g GRPC_IP -r GRPC_PORT [-s] [--server-cert SERVER_CERT] --op OP
              --destination DESTINATION --segments SEGMENTS [--device DEVICE]
              [--encapmode {encap,inline,l2encap}] [--table TABLE]
              [--metric METRIC] [-d]

  Create, get, change or remove a SRv6 uSID policy in a node.

  optional arguments:
    -h, --help            show this help message and exit
    -g GRPC_IP, --grpc-ip GRPC_IP
                          IP of the gRPC server
    -r GRPC_PORT, --grpc-port GRPC_PORT
                         Port of the gRPC server
    -s, --secure          Activate secure mode
    --server-cert SERVER_CERT
                          CA certificate file
    --op OP               Operation
    --destination DESTINATION
                          Destination
    --nodes NODES   Waypoints of the path
    --device DEVICE       Device
    --encapmode {encap,inline,l2encap}
                          Encap mode
    --table TABLE         Table
    --metric METRIC       Metric
    -d, --debug           Activate debug logs


.. list-table:: Arguments for the ``policy`` command
    :widths: 15 15 10 10 60
    :header-rows: 1


    * - Argument
      - Type
      - Default
      - Optional
      - Description
    * - ``--help``
      - --
      - --
      - --
      - Show an help message and exit.
    * - ``--grpc-ip``
      - string
      - --
      - no
      - | IP of the gRPC server executed
        | on the node.
    * - ``--grpc-port``
      - integer
      - 12345
      - yes
      - | Port of the gRPC server executed
        | on the node.
    * - ``--secure``
      - boolean
      - False
      - yes
      - | If True, the Controller will use the TLS to
        | encrypt and authenticate the traffic sent
        | to the Node Manager on the gRPC
        | Channel.
    * - ``--server-cert``
      - string
      - None
      - yes
      - | Name of CA certificate for the TLS,
        | required if GRPC_SECURE is True.
    * - ``--op``
      - string
      - --
      - no
      - Operation (add, change, get, del).
    * - ``--destination``
      - string
      - --
      - no
      - Destination of the SRv6 path.
    * - ``--nodes``
      - string
      - --
      - yes
      - | The list of the waypoints (device names) of the SRv6 path.
    * - ``--device``
      - string
      - --
      - yes
      - | Device to be associated to the SRv6
        | path. If not specified, the Node
        | Manager will select an interface
        | automatically from the list of the
        | interfaces of the device.
    * - ``--encapmode``
      - string
      - encap
      - yes
      - | The encap mode used for SRv6
        | (i.e. encap, inline or l2encap).
    * - ``--table``
      - integer
      - 254
      - yes
      - | The ID of the table where the SRv6
        | route must be created or removed
        | from. If not specified, the main table will
        | be used (table ID 254).
    * - ``--metric``
      - integer
      - --
      - yes
      - The metric to be assigned to the route.
    * - ``--debug``
      - --
      - --
      - yes
      - If True, the debug logging is enabled.


``exit``
--------

Exit from this section and return the previous section.

.. code:: bash

  controller(srv6)> exit


``help``
--------

Show a description of the commands.

.. code:: bash

  controller(srv6)> help
