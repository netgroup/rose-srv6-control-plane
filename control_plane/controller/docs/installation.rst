.. _controller-installation:

Installation
============

This section explains how to install the Controller and all the required dependencies.

You have two ways to install the Controller:

* :ref:`controller-installation-venv`
* :ref:`controller-installation-novenv`

.. note:: The installation into a virtual environment is the suggested option.

Prerequisites
-------------

The following dependencies are necessary:

* Linux kernel 4.14 or above
* Python 3.6 or above

.. _controller-installation-venv:

Installation into a virtual environment (suggested)
---------------------------------------------------

#. Create a Python 3 virtual environment for the Controller:

   .. code:: console

     $ python3 -m venv ~/.envs/controller-venv

#. Activate the virtual environment:

   .. code:: console

     $ source ~/.envs/controller-venv/bin/activate

#. Clone the *rose-srv6-control-plane* repository using ``git``:

   .. code:: console

     $ git clone https://github.com/netgroup/rose-srv6-control-plane.git

#. Then, ``cd`` to the *control_plane/controller* directory under the *rose-srv6-control-plane* folder and run the install command:

   .. code:: console

     $ cd rose-srv6-control-plane/control_plane/controller
     $ python setup.py install

#. This project depends on the gRPC protocol, which requires protobuf modules. ``cd`` to the *control_plane/protos* directory under the *rose-srv6-control-plane* folder and run the setup command to build and install the proto files:

   .. code:: console

     $ cd rose-srv6-control-plane/control_plane/protos
     $ python setup.py install


Configuration
^^^^^^^^^^^^^

The Controller comes with a default configuration:

.. literalinclude:: ../controller/config/controller.env
  :language: shell
  :caption: controller.env
  :name: controller.env_installation_config_2

If you want to override the default settings, you can create a *.env*
file containing the configuration parameters.
For a description of the supported configuration options, see the
:ref:`controller-configuration` section.


Optional requirements
^^^^^^^^^^^^^^^^^^^^^

* Database utilities are required for the ArangoDB integration features.
  You need to activate the controller virtual environment and install
  the *db_update* package contained in the *rose-srv6-control-plane*
  repository if you want to use these features:

  .. code:: console

    $ source ~/.envs/controller-venv/bin/activate
    $ cd rose-srv6-control-plane/db_update
    $ python setup.py install

* Exporting the network topology as an image file requires *graphviz* and *libgraphviz-dev*:

  .. code:: console

    $ apt-get install graphviz libgraphviz-dev

* *kafka-python* is required for Kafka integration. Activate the controller virtual environment and run the install command:

  .. code:: console

    $ source ~/.envs/controller-venv/bin/activate
    $ pip install kafka-python


.. _controller-installation-novenv:

Installation without a virtual environment
------------------------------------------

#. Clone the *rose-srv6-control-plane* repository using ``git``:

   .. code:: console

     $ git clone https://github.com/netgroup/rose-srv6-control-plane.git

#. Then, ``cd`` to the *control_plane/controller* directory under the *rose-srv6-control-plane* folder and run the install command:

   .. code:: console

     $ cd rose-srv6-control-plane/control_plane/controller
     $ python setup.py install

#. This project depends on the gRPC protocol, which requires protobuf modules. ``cd`` to the *control_plane/protos* directory under the *rose-srv6-control-plane* folder and run the setup command to build and install the proto files:

   .. code:: console

     $ cd rose-srv6-control-plane/control_plane/protos
     $ python setup.py install


Configuration
^^^^^^^^^^^^^

The Controller comes with a default configuration:

.. literalinclude:: ../controller/config/controller.env
  :language: shell
  :caption: controller.env
  :name: controller.env_installation_config

If you want to override the default settings, you can create a *.env*
file containing the configuration parameters.
For a description of the supported configuration options, see the
:ref:`controller-configuration` section.


.. _controller-installation-opt-req:

Optional requirements
^^^^^^^^^^^^^^^^^^^^^

* Database utilities are required for the ArangoDB integration features.
  You need to install the *db_update* package contained in the
  *rose-srv6-control-plane* repository if you want to use these features:

  .. code:: console

    $ cd rose-srv6-control-plane/db_update
    $ python setup.py install

* Exporting the network topology as an image file requires *graphviz* and *libgraphviz-dev*:

  .. code:: console

    $ apt-get install graphviz libgraphviz-dev

* *kafka-python* is required for Kafka integration. You can install it by running the install command:

  .. code:: console

    $ pip install kafka-python
