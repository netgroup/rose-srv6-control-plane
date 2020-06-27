.. _controller-cli-srv6pm:

SRv6 Performance Measurement Functions
======================================

The Controller allows to execute performance measurement experiments
on a network. These functions are available under the section ``srv6pm``
of the Command-Line Interface.


Entering the ``srv6pm`` section
-------------------------------

.. code:: bash

  controller> srv6pm
  controller(srv6pm)> 

Section ``srv6pm`` supports the following commands:
.. code:: bash

  configuration  exit  experiment  help


``configuration``
-----------------

Enter the ``configuration`` sub-section of the ``srv6pm`` CLI.

.. code:: bash

  controller(srv6)> configuration

See :ref:`controller-cli-srv6pm-configuration` for a description
of the commands available in the ``configuration`` section.


``experiment``
--------------

Enter the ``experiment`` sub-section of the ``srv6pm`` CLI.

.. code:: bash

  controller(srv6)> experiment

See :ref:`controller-cli-srv6pm-experiment` for a description
of the commands available in the ``experiment`` section.


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


.. toctree ::
   :maxdepth: 2
   :hidden:

   srv6pm_configuration
   srv6pm_experiment
