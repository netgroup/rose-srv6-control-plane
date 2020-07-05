.. _node-mgr-installation:

Installation
============

This section explains how to install the Node Manager and all the required
dependencies.

You have two ways to install the Controller:

* :ref:`node-mgr-installation-venv`
* :ref:`node-mgr-installation-novenv`

.. note:: The installation into a virtual environment is the suggested option.

Prerequisites
-------------

The following dependencies are necessary:

* Linux kernel 4.14 or above
* Python 3.6 or above

.. _node-mgr-installation-venv:

Installation into a virtual environment (suggested)
---------------------------------------------------

#. Create a Python 3 virtual environment for the Controller:

   .. code:: console

     $ python3 -m venv ~/.envs/node-mgr-venv

#. Activate the virtual environment:

   .. code:: console

     $ source ~/.envs/node-mgr-venv/bin/activate

#. Clone the *rose-srv6-control-plane* repository using ``git``:

   .. code:: console

     $ git clone https://github.com/netgroup/rose-srv6-control-plane.git

#. Then, ``cd`` to the *control_plane/node-manager* directory under the
   *rose-srv6-control-plane* folder and run the install command:

   .. code:: console

     $ cd rose-srv6-control-plane/control_plane/node-manager
     $ python setup.py install

#. This project depends on the gRPC protocol, which requires protobuf modules.
   ``cd`` to the *control_plane/protos* directory under the
   *rose-srv6-control-plane* folder and run the setup command to build and
   install the proto files:

   .. code:: console

     $ cd rose-srv6-control-plane/control_plane/protos
     $ python setup.py install


.. _node-mgr-installation-novenv:

Installation without a virtual environment
------------------------------------------

#. Clone the *rose-srv6-control-plane* repository using ``git``:

   .. code:: console

     $ git clone https://github.com/netgroup/rose-srv6-control-plane.git

#. Then, ``cd`` to the *control_plane/node_manager* directory under
   the *rose-srv6-control-plane* folder and run the install command:

   .. code:: console

     $ cd rose-srv6-control-plane/control_plane/node_manager
     $ python setup.py install

#. This project depends on the gRPC protocol, which requires protobuf modules.
   ``cd`` to the *control_plane/protos* directory under the
   *rose-srv6-control-plane* folder and run the setup command to build
   and install the proto files:

   .. code:: console

     $ cd rose-srv6-control-plane/control_plane/protos
     $ python setup.py install


Configuration
-------------

The Node Manager comes with a default configuration:

.. literalinclude:: ../../control_plane/node-manager/node_manager/config/node_manager.env
  :language: shell
  :caption: node_manager.env
  :name: node_manager.env_installation_config_2

If you want to override the default settings, you can create a *.env*
file containing the configuration parameters.
For a description of the supported configuration options, see the
:ref:`node-mgr-configuration` section.


.. _node-mgr-installation-opt-req:

Optional requirements
^^^^^^^^^^^^^^^^^^^^^

* SRv6 PFPLM requires `SRv6 PFPLM implementation using
  XDP/eBPF and tc/eBPF <https://github.com/netgroup/srv6-pm-xdp-ebpf>`_
  and `ROSE SRv6 Data-Plane <https://github.com/netgroup/rose-srv6-data-plane>`_.

  * In order to setup *SRv6 PFPLM implementation using XDP/eBPF and tc/eBPF*
    you need to clone the github repository and follow the setup instructions
    contained in *README.md*:

    .. code:: console

        $ git clone -b srv6-pfplm-dev-v2-rev_2 https://github.com/netgroup/srv6-pm-xdp-ebpf.git

    Then, you need to add the path to the repository to your *.env* file,
    as described in the :ref:`node-mgr-configuration-srv6pm-manager` section.

  * To setup the *rose-srv6-data-plane*, clone the repository and follow the
    setup instructions provided in *README.md*:
    
    .. code:: console

      $ git clone https://github.com/netgroup/rose-srv6-data-plane.git

    and follow the setup instructions.
