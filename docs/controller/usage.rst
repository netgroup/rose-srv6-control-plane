.. _controller-usage:

Usage
=====

In this section we explain how to use the functionalities offered by the
Controller. Before continuing, be sure that you have the Controller installed
in your system or in a virtual environment. If not, you can follow the
instructions provided in the :ref:`controller-installation` section to install it.

There are two ways to use the Controller:

* Use the CLI
* Use the Controller functionalities in your Python application


Starting the Controller CLI
---------------------------

#. If you have installed the Controller in a virtual environment,
   you need to activate the controller virtual environment:

   .. code:: console

     $ source ~/.envs/controller-venv/bin/activate

#. To start the Controller CLI:

   .. code:: console

     $ controller --env-file .env

   .. code:: console

     $ controller --help
     usage: controller [-h] [-e ENV_FILE]

     Controller CLI

     optional arguments:
     -h, --help            show this help message and exit
     -e ENV_FILE, --env-file ENV_FILE
                             Path to the .env file containing the parameters for the controller

#. Show the usage of the CLI:

   .. code:: console

     controller> help

   For more information about the commands supported by the CLI, see :ref:`controller-cli`.

.. note:: The Controller comes with a default configuration.
  If you want to override the default settings, you can create a *.env* file
  containing the configuration parameters.
  For a description of the supported configuration options, see the
  :ref:`controller-configuration` section.


Use the Controller in your Python application
---------------------------------------------

Just import the Controller in your application and start using the API.
See :ref:`controller-api` for more details about the API specifications.
