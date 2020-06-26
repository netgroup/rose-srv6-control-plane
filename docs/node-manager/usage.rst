.. _node-mgr-usage:

Usage
=====

In this section we explain how to use the Node Manager.
Before continuing, be sure that you have the Node Manager installed
in your system or in a virtual environment. If not, you can follow the
instructions provided in the :ref:`node-mgr-installation` section to install it.

.. note:: The Node Manager comes with a default configuration.
  If you want to override the default settings, you can create a *.env* file
  containing the configuration parameters.
  For a description of the supported configuration options, see the
  :ref:`node-mgr-configuration` section.


Starting the Node Manager
---------------------------

#. If you have installed the Node Manager in a virtual environment,
   you need to activate the node manager virtual environment:

   .. code:: console

     $ source ~/.envs/node-mgr-venv/bin/activate

#. To start the Node Manager:

   .. code:: console

     $ node_manager --env-file .env

  Optionally, you can provide command-line arguments to override the
  configuration parameters set in the *.env* file.
  For a detailed description of the available parameters,
  you can start the node_manager with the --help command-line argument:

  .. code:: console

    # python node-manager --help
    usage: node_manager [-h] [-e ENV_FILE] [-g GRPC_IP] [-r GRPC_PORT] [-s] [-c SERVER_CERT] [-k SERVER_KEY] [-d]

    gRPC Southbound APIs for SRv6 Controller

    optional arguments:
    -h, --help            show this help message and exit
    -e ENV_FILE, --env-file ENV_FILE
                            Path to the .env file containing the parameters for the node manager
    -g GRPC_IP, --grpc-ip GRPC_IP
                            IP of the gRPC server
    -r GRPC_PORT, --grpc-port GRPC_PORT
                            Port of the gRPC server
    -s, --secure          Activate secure mode
    -c SERVER_CERT, --server-cert SERVER_CERT
                            Server certificate file
    -k SERVER_KEY, --server-key SERVER_KEY
                            Server key file
    -d, --debug           Activate debug logs


  .. note:: The command-line arguments have priority over the parameters
    defined in the *.env* file.

  .. note:: The Node Manager comes with a default configuration.
    If you want to override the default settings, you can create a *.env* file
    containing the configuration parameters.
    For a description of the supported configuration options, see the
    :ref:`node-mgr-configuration` section.
