.. _controller-cli-topology:

Topology Utilities
==================

The Controller allows to extract the network topology from a set of
nodes running the IS-IS protocol. The Command-Line Interface (CLI)
offers several functions to export and manipulate the network topology.
These functions are available under the section ``topology`` of the CLI.


Entering the ``topology`` section
---------------------------------

.. code:: console

  controller> topology
  controller(topology)> 

Section ``topology`` supports the following commands:

.. code:: console

  exit  extract  extract_and_load_on_arango  help  load_on_arango


``extract``
-----------

Extract the topology from a set of routers running the IS-IS protocol.
Optionally, the topology can be exported as a JSON file, YAML file and image file.

.. code:: console

  controller(topology)> extract --help
  usage: extract [-h] --routers ROUTERS [--period PERIOD]
                 [--isisd-pwd ISISD_PWD] [--topo-file-json TOPO_FILE_JSON]
                 [--nodes-file-yaml NODES_FILE_YAML]
                 [--edges-file-yaml EDGES_FILE_YAML] [--addrs-yaml ADDRS_YAML]
                 [--hosts-yaml HOSTS_YAML] [--topo-graph TOPO_GRAPH] [-v] [-d]

  Extract the topology from a set of routers running the IS-IS protocol

  optional arguments:
    -h, --help            show this help message and exit
    --routers ROUTERS     routers
    --period PERIOD       period
    --isisd-pwd ISISD_PWD
                          period
    --topo-file-json TOPO_FILE_JSON
                          topo_file_json
    --nodes-file-yaml NODES_FILE_YAML
                          nodes_file_yaml
    --edges-file-yaml EDGES_FILE_YAML
                          edges_file_yaml
    --addrs-yaml ADDRS_YAML
                          addrs_yaml
    --hosts-yaml HOSTS_YAML
                          hosts_yaml
    --topo-graph TOPO_GRAPH
                          topo_graph
    -v, --verbose         Enable verbose mode
    -d, --debug           Activate debug logs


``extract_and_load_on_arango``
------------------------------

Extract the topology from a set of routers running the IS-IS protocol and
load it on a ArangoDB database. Optionally, the topology can be exported
as a JSON file, YAML file and image file.

.. code:: console

  controller(topology)> extract_and_load_on_arango --help
  usage: extract_and_load_on_arango [-h] --isis-nodes ISIS_NODES
                                    [--isisd-pwd ISISD_PWD]
                                    [--arango-url ARANGO_URL]
                                    [--arango-user ARANGO_USER]
                                    [--arango-password ARANGO_PASSWORD]
                                    [--period PERIOD] [--nodes-yaml NODES_YAML]
                                    [--edges-yaml EDGES_YAML]
                                    [--addrs-yaml ADDRS_YAML]
                                    [--hosts-yaml HOSTS_YAML] [-v] [-d]

  Extract the topology from a set of routers running the IS-IS protocol and load it on a ArangoDB database

  optional arguments:
    -h, --help            show this help message and exit
    --isis-nodes ISIS_NODES
                          isis_nodes
    --isisd-pwd ISISD_PWD
                          period
    --arango-url ARANGO_URL
                          arango_url
    --arango-user ARANGO_USER
                          arango_user
    --arango-password ARANGO_PASSWORD
                          arango_password
    --period PERIOD       period
    --nodes-yaml NODES_YAML
                          nodes_yaml
    --edges-yaml EDGES_YAML
                          edges_yaml
    --addrs-yaml ADDRS_YAML
                          addrs_yaml
    --hosts-yaml HOSTS_YAML
                          hosts_yaml
    -v, --verbose         Enable verbose mode
    -d, --debug           Activate debug logs


``load_on_arango``
------------------

Read the topology from a YAML file and load it on a ArangoDB database.

.. code:: console

  controller(topology)> load_on_arango --help
  usage: load_on_arango [-h] [--arango-url ARANGO_URL]
                        [--arango-user ARANGO_USER]
                        [--arango-password ARANGO_PASSWORD]
                        [--nodes-yaml NODES_YAML] [--edges-yaml EDGES_YAML] [-v]
                        [-d]

  Read the topology from a YAML file and load it on a ArangoDB database

  optional arguments:
    -h, --help            show this help message and exit
    --arango-url ARANGO_URL
                          arango_url
    --arango-user ARANGO_USER
                          arango_user
    --arango-password ARANGO_PASSWORD
                          arango_password
    --nodes-yaml NODES_YAML
                          nodes_yaml
    --edges-yaml EDGES_YAML
                          edges_yaml
    -v, --verbose         Enable verbose mode
    -d, --debug           Activate debug logs


``exit``
--------

Exit from this section and return the previous section.

.. code:: console

  controller(srv6)> exit


``help``
--------

Show a description of the commands.

.. code:: console

  controller(srv6)> help
