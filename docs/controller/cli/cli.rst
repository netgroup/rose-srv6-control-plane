.. _controller-cli:

Command-Line Interface (CLI) Reference
======================================

This section describes the usage of the Command-Line Interface (CLI) of
the Controller.

If you have installed the Controller in a virtual environment, you need to
activate it before continuing:

.. code:: bash

  $ source ~/.envs/controller-venv/bin/activate

The CLI can be started by typing the command ``controller`` in your terminal:

.. code:: bash

  $ controller

Optionally, you can pass the path of the configuration file containing your settings:

.. code:: bash

  $ controller --env-file config/controller.env


The Controller CLI will start and load the configuration:

.. code:: bash

  INFO:apps.cli.cli:*** Loading configuration from /home/rose/.envs/controller-venv/lib/python3.8/site-packages/rose_srv6_control_plane_controller-0.0.1-py3.8.egg/controller/cli/../config/controller.env
  INFO:root:SERVER_DEBUG: False
  INFO:apps.cli.cli:*** Validating configuration

  ****************** CONFIGURATION ******************

  ArangoDB URL: http://localhost:8529
  ArangoDB username: root
  ArangoDB password: ************
  Kafka servers: kafka:9092
  Enable debug: False

  ***************************************************


  Welcome! Type ? to list commands
  controller> 

Now the CLI is ready to receive commands. For a list of the available
commands, you can see the next sections or type the ``help`` command:

.. code:: bash

  controller> help


.. list-table:: Commands supported by the Controller CLI
    :widths: 15 15 10 60
    :header-rows: 1


    * - Command
      - Description
      - Arguments
      - Documentation
    * - ``help``
      - Description of the interactive CLI
      - -
      - -
    * - ``exit``
      - Exit from the CLI
      - -
      - -
    * - ``srv6``
      - Enter the SRv6 section
      - -
      - :ref:`controller-cli-srv6`
    * - ``srv6pm``
      - Enter the SRv6 Performance Measurement section
      - -
      - :ref:`controller-cli-srv6pm`
    * - ``topology``
      - Enter the Topology section
      - -
      - :ref:`controller-cli-topology`


.. toctree ::
   :maxdepth: 2
   :hidden:

   srv6
   srv6pm
   topology
