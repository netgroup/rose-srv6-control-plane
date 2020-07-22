.. _controller-cli-srv6-usid:

SRv6 uSID Functions
===================

The Controller supports the creation and management of several types
of SRv6 entities. These functions are available under the section
``srv6`` of the Command-Line Interface. The uSID sub-section contains
functions related to uSID.


Entering the ``srv6``/``usid`` section
--------------------------------------

.. note:: usid requires the argument --nodes-file, that is a YAML file
  containing the mapping of node names to IP addresses.

.. code:: bash

  controller> srv6
  controller(srv6)> usid --nodes-file nodes.yml
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
  usage: policy [-h] [--secure] [--server-cert SERVER_CERT] --op OP
                [--lr-destination LR_DESTINATION]
                [--rl-destination RL_DESTINATION] [--nodes NODES]
                [--nodes-rev NODES_REV] [--table TABLE] [--metric METRIC]
                [--id ID] [--debug]

  gRPC Southbound APIs for SRv6 Controller

  optional arguments:
    -h, --help            show this help message and exit
    --secure              Activate secure mode
    --server-cert SERVER_CERT
                          CA certificate file
    --op OP               Operation
    --lr-destination LR_DESTINATION
                          Left to Right Destination
    --rl-destination RL_DESTINATION
                          Right to Left Destination
    --nodes NODES         Nodes
    --nodes-rev NODES_REV
                          Reverse nodes list
    --table TABLE         Table
    --metric METRIC       Metric
    --id ID               id
    --debug               Activate debug logs


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
    * - ``--lr-destination``
      - string
      - --
      - yes
      - Destination of the SRv6 left-to-right path.
    * - ``--rl-destination``
      - string
      - --
      - yes
      - Destination of the SRv6 right-to-left path.
    * - ``--nodes``
      - string
      - --
      - yes
      - | The list of the waypoints (device names) of
        | the SRv6 path (left-to-right).
    * - ``--nodes-rev``
      - string
      - --
      - yes
      - | The list of the waypoints (device names) of the
        | reverse SRv6 path (right-to-left).
        | If not provided, the same nodes of the
        | left-to-right path in reverse order
        | will be used.
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
