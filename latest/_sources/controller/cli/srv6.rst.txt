.. _controller-cli-srv6:

SRv6 Functions
==============

The Controller supports the creation and management of several types
of SRv6 entities. These functions are available under the section
``srv6`` of the Command-Line Interface.


Entering the ``srv6`` section
-----------------------------

.. code:: bash

  controller> srv6
  controller(srv6)> 

The ``srv6`` section supports the following commands:

.. code:: bash

  behavior  biditunnel  exit  help  path  unitunnel usid_policy


``behavior``
------------

Create, get, change or remove a SRv6 behavior in a node.

.. code:: bash

  controller(srv6)> behavior --help
  usage: behavior [-h] -g GRPC_IP -r GRPC_PORT [-s] [--server-cert SERVER_CERT] --op OP
                  --segment SEGMENT --action ACTION [--device DEVICE]
                  [--table TABLE] [--nexthop NEXTHOP]
                  [--lookup-table LOOKUP_TABLE] [--interface INTERFACE]
                  [--segments SEGMENTS] [--metric METRIC] [-d]

  Create, get, change or remove a SRv6 behavior in a node

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
    --segment SEGMENT     Segment
    --action ACTION       Action
    --device DEVICE       Device
    --table TABLE         Table
    --nexthop NEXTHOP     Next-hop
    --lookup-table LOOKUP_TABLE
                          Lookup Table
    --interface INTERFACE
                          Interface
    --segments SEGMENTS   Segments
    --metric METRIC       Metric
    -d, --debug           Activate debug logs


.. list-table:: Arguments for the ``behavior`` command
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
    * - ``--segment``
      - string
      - --
      - no
      - | Local segment associated to the SRv6
        | behavior.
    * - ``--action``
      - string
      - --
      - no
      - | SRv6 behavior to install in the node
        | (e.g. End.DT6 or End.DX4)
    * - ``--device``
      - string
      - --
      - yes
      - | Device to be associated to the SRv6
        | behavior. If not specified, the Node
        | Manager will select an interface
        | automatically from the list of the
        | interfaces of the device.
    * - ``--table``
      - integer
      - 254
      - yes
      - | The ID of the table where the SRv6
        | behavior must be created or removed
        | from. If not specified, the main table will
        | be used (table ID 254).
    * - ``--nexthop``
      - string
      - --
      - \*yes
      - | The next-hop used as argument of the
        | End.X, End.DX4 and End.DX6 behaviors.
        | This argument is mandatory if action is
        | End.X, End.DX4 or End.DX6, otherwise it
        | is not required.
    * - ``--lookup-table``
      - integer
      - --
      - \*yes
      - | The table used as argument of the End.T,
        | End.DT4 and End.DT6 behaviors. This
        | argument is mandatory if action is End.T,
        | End.DT4 or End.DT6, otherwise it is not
        | required.
    * - ``--interface``
      - string
      - --
      - \*yes
      - | The outgoing interface used as argument
        | of the End.DX2 behavior. This argument is
        | mandatory if action is End.DX2, otherwise
        | it is not required.
    * - ``--segments``
      - string
      - --
      - \*yes
      - | The segment list used as argument of the
        | End.B6 and End.B6.Encaps behaviors.
        | This argument is mandatory if action is
        | End.B6 or End.B6.Encaps, otherwise it is
        | not required.
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

.. note:: An asterisk (*) in the **Optional** column means that the argument is
  optional or not depending on a condition. More information about this
  condition is provided under the column **Description**.


``biditunnel``
--------------

Create, get, change or remove a bidirectional SRv6 tunnel between two nodes.

.. code:: bash

  controller(srv6)> biditunnel --help
  usage: biditunnel [-h] --op OP --left-grpc-ip L_GRPC_IP --right-grpc-ip
                    R_GRPC_IP --left-grpc-port L_GRPC_PORT --right-grpc-port
                    R_GRPC_PORT [-s] [--server-cert SERVER_CERT] --left-right-dest DEST_LR
                    --right-left-dest DEST_RL
                    [--left-right-localseg LOCALSEG_LR]
                    [--right-left-localseg LOCALSEG_RL] --left-right-sidlist
                    SIDLIST_LR --right-left-sidlist SIDLIST_RL [-d]
  
  Create, get, change or remove a bidirectional SRv6 tunnel between two nodes
  
  optional arguments:
    -h, --help            show this help message and exit
    --op OP               Operation
    --left-grpc-ip L_GRPC_IP
                          IP of the gRPC server
    --right-grpc-ip R_GRPC_IP
                          IP of the gRPC server
    --left-grpc-port L_GRPC_PORT
                          Port of the gRPC server
    --right-grpc-port R_GRPC_PORT
                          Port of the gRPC server
    -s, --secure          Activate secure mode
    --server-cert SERVER_CERT
                          CA certificate file
    --left-right-dest DEST_LR
                          Left to Right destination
    --right-left-dest DEST_RL
                          Right to Left destination
    --left-right-localseg LOCALSEG_LR
                          Left to Right Local segment
    --right-left-localseg LOCALSEG_RL
                          Right to Left Local segment
    --left-right-sidlist SIDLIST_LR
                          Left to Right SID list
    --right-left-sidlist SIDLIST_RL
                          Right to Left SID list
    -d, --debug           Activate debug logs


.. list-table:: Arguments for the ``biditunnel`` command
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
    * - ``--op``
      - string
      - --
      - no
      - Operation (add, change, get, del).
    * - ``--left-grpc-ip``
      - string
      - --
      - no
      - | IP of the gRPC server on the
        | Left node.
    * - ``--right-grpc-ip``
      - string
      - --
      - no
      - | IP of the gRPC server on the
        | Right node.
    * - ``--left-grpc-port``
      - integer
      - 12345
      - yes
      - | Port of the gRPC server on the
        | Left node.
    * - ``--right-grpc-port``
      - integer
      - 12345
      - yes
      - | Port of the gRPC server on the
        | Right node.
    * - ``--secure``
      - boolean
      - False
      - yes
      - | If True, the Controller will use the
        | TLS to encrypt and authenticate
        | the traffic sent to the Node
        | Manager on the gRPC Channel.
    * - ``--secure``
      - boolean
      - False
      - yes
      - | If True, the Controller will use the
        | TLS to encrypt and authenticate
        | the traffic sent to the Node
        | Manager on the gRPC Channel.
    * - ``--server-cert``
      - string
      - None
      - yes
      - | Name of CA certificate for the TLS,
        | required if GRPC_SECURE is True.
    * - ``--left-right-dest``
      - string
      - --
      - no
      - | Destination prefix used for the 
        | Left to Right path.
    * - ``--right-left-dest``
      - string
      - --
      - no
      - | Destination prefix used for the 
        | Right to Left path.
    * - ``--left-right-localseg``
      - string
      - --
      - yes
      - | Local segment used for the Left to
        | Right path (associated to the
        | End.DT6 behavior). If not
        | specified, the End.DT6 behavior
        | is not created.
    * - ``--right-left-localseg``
      - string
      - --
      - yes
      - | Local segment used for the Right to
        | Left path (associated to the
        | End.DT6 behavior). If not
        | specified, the End.DT6 behavior
        | is not created.
    * - ``--left-right-sidlist``
      - string
      - --
      - no
      - | SID list used for the Left to Right
        | path.
    * - ``--right-left-sidlist``
      - string
      - --
      - no
      - | SID list used for the Right to Left
        | path.
    * - ``--debug``
      - --
      - --
      - yes
      - | If True, the debug logging is
        | enabled.



``path``
--------

Create, get, change or remove a SRv6 path in a node.

.. code:: bash

  controller(srv6)> path --help
  usage: path [-h] -g GRPC_IP -r GRPC_PORT [-s] [--server-cert SERVER_CERT] --op OP
              --destination DESTINATION --segments SEGMENTS [--device DEVICE]
              [--encapmode {encap,inline,l2encap}] [--table TABLE]
              [--metric METRIC] [-d]

  Create, get, change or remove a SRv6 path in a node

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
    --segments SEGMENTS   Segments
    --device DEVICE       Device
    --encapmode {encap,inline,l2encap}
                          Encap mode
    --table TABLE         Table
    --metric METRIC       Metric
    -d, --debug           Activate debug logs


.. list-table:: Arguments for the ``path`` command
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
    * - ``--segments``
      - string
      - --
      - yes
      - | The segment list used for the SRv6 path.
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


``unitunnel``
-------------

Create, get, change or remove a unidirectional SRv6 tunnel between two nodes.

.. code:: bash

  controller(srv6)> unitunnel --help
  usage: unitunnel [-h] --op OP --ingress-grpc-ip INGRESS_GRPC_IP
                   --egress-grpc-ip EGRESS_GRPC_IP --ingress-grpc-port
                   INGRESS_GRPC_PORT --egress-grpc-port EGRESS_GRPC_PORT [-s]
                   [--server-cert SERVER_CERT] --dest DEST [--localseg LOCALSEG] --sidlist
                   SIDLIST [-d]

  Create, get, change or remove a unidirectional SRv6 tunnel between two nodes

  optional arguments:
    -h, --help            show this help message and exit
    --op OP               Operation
    --ingress-grpc-ip INGRESS_GRPC_IP
                          IP of the gRPC server
    --egress-grpc-ip EGRESS_GRPC_IP
                          IP of the gRPC server
    --ingress-grpc-port INGRESS_GRPC_PORT
                          Port of the gRPC server
    --egress-grpc-port EGRESS_GRPC_PORT
                          Port of the gRPC server
    -s, --secure          Activate secure mode
    --server-cert SERVER_CERT
                          CA certificate file
    --dest DEST           Destination
    --localseg LOCALSEG   Local segment
    --sidlist SIDLIST     SID list
    -d, --debug           Activate debug logs


.. list-table:: Arguments for the ``unitunnel`` command
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
    * - ``--op``
      - string
      - --
      - no
      - Operation (add, change, get, del).
    * - ``--ingress-grpc-ip``
      - string
      - --
      - no
      - | IP of the gRPC server on the
        | ingress node.
    * - ``--egress-grpc-ip``
      - string
      - --
      - no
      - | IP of the gRPC server on the
        | egress node.
    * - ``--ingress-grpc-port``
      - integer
      - 12345
      - yes
      - | Port of the gRPC server on the
        | ingress node.
    * - ``--egress-grpc-port``
      - integer
      - 12345
      - yes
      - | Port of the gRPC server on the
        | egress node.
    * - ``--secure``
      - boolean
      - False
      - yes
      - | If True, the Controller will use the
        | TLS to encrypt and authenticate
        | the traffic sent to the Node
        | Manager on the gRPC Channel.
    * - ``--server-cert``
      - string
      - None
      - yes
      - | Name of CA certificate for the TLS,
        | required if GRPC_SECURE is True.
    * - ``--dest``
      - string
      - --
      - no
      - | Destination prefix used for the 
        | SRv6 path.
    * - ``--localseg``
      - string
      - --
      - yes
      - | Local segment used for the SRv6
        | path (associated to the
        | End.DT6 behavior). If not
        | specified, the End.DT6 behavior
        | is not created.
    * - ``--sidlist``
      - string
      - --
      - no
      - | SID list used for the SRv6 path.
    * - ``--debug``
      - --
      - --
      - yes
      - | If True, the debug logging is
        | enabled.


``usid_policy``
---------------

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
