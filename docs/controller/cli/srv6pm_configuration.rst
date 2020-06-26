.. _controller-cli-srv6pm-configuration:

SRv6 Performance Measurement Functions - Configuration
======================================================

The Controller allows to execute performance measurement experiments
on a network. The configuration functions are available under the
section ``srv6pm``/``configuration`` of the Command-Line Interface.


Entering the ``srv6pm``/``configuration`` section
-------------------------------------------------

.. code:: bash

  controller> srv6pm
  controller(srv6pm)> configuration
  controller(srv6pm-configuration)> 

Section ``srv6pm``/``configuration`` supports the following commands:

.. code:: bash

  exit  help  reset  set


``reset``
---------

Clear configuration settings on both sender and reflector nodes.

.. code:: bash

  controller(srv6pm-configuration)> reset --help
  usage: start [-h] --sender-ip SENDER_IP --sender-port SENDER_PORT
               --reflector-ip REFLECTOR_IP --reflector-port REFLECTOR_PORT [-s]
               [--server-cert SERVER_CERT] [-d]

  Clear configuration settings on both sender and reflector nodes

  optional arguments:
    -h, --help            show this help message and exit
    --sender-ip SENDER_IP
                          IP of the gRPC server of the sender
    --sender-port SENDER_PORT
                          Port of the gRPC server of the sender
    --reflector-ip REFLECTOR_IP
                          IP of the gRPC server of the reflector
    --reflector-port REFLECTOR_PORT
                          Port of the gRPC server of the reflector
    -s, --secure          Activate secure mode
    --server-cert SERVER_CERT
                          CA certificate file
    -d, --debug           Activate debug logs


``set``
-------

Set the configuration on both sender and reflector nodes.

.. code:: bash

  controller(srv6pm-configuration)> set --help
  usage: start [-h] --sender-ip SENDER_IP --sender-port SENDER_PORT
               --reflector-ip REFLECTOR_IP --reflector-port REFLECTOR_PORT [-s]
               [--server-cert SERVER_CERT] [--send_in_interfaces SEND_IN_INTERFACES]
               [--refl_in_interfaces REFL_IN_INTERFACES]
               [--send_out_interfaces SEND_OUT_INTERFACES]
               [--refl_out_interfaces REFL_OUT_INTERFACES]
               [--send_udp_port SEND_UDP_PORT] [--refl_udp_port REFL_UDP_PORT]
               [--interval_duration INTERVAL_DURATION]
               [--delay_margin DELAY_MARGIN] [--number_of_color NUMBER_OF_COLOR]
               [--pm_driver PM_DRIVER] [-d]

  Set the configuration on both sender and reflector nodes

  optional arguments:
    -h, --help            show this help message and exit
    --sender-ip SENDER_IP
                          IP of the gRPC server of the sender
    --sender-port SENDER_PORT
                          Port of the gRPC server of the sender
    --reflector-ip REFLECTOR_IP
                          IP of the gRPC server of the reflector
    --reflector-port REFLECTOR_PORT
                          Port of the gRPC server of the reflector
    -s, --secure          Activate secure mode
    --server-cert SERVER_CERT
                          CA certificate file
    --send_in_interfaces SEND_IN_INTERFACES
                          send_in_interfaces
    --refl_in_interfaces REFL_IN_INTERFACES
                          refl_in_interfaces
    --send_out_interfaces SEND_OUT_INTERFACES
                          send_out_interfaces
    --refl_out_interfaces REFL_OUT_INTERFACES
                          refl_out_interfaces
    --send_udp_port SEND_UDP_PORT
                          send_udp_port
    --refl_udp_port REFL_UDP_PORT
                          refl_udp_port
    --interval_duration INTERVAL_DURATION
                          interval_duration
    --delay_margin DELAY_MARGIN
                          delay_margin
    --number_of_color NUMBER_OF_COLOR
                          number_of_color
    --pm_driver PM_DRIVER
                          pm_driver
    -d, --debug           Activate debug logs


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
