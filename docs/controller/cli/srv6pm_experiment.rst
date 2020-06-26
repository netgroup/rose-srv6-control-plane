.. _controller-cli-srv6pm-experiment:

SRv6 Performance Measurement Functions - Experiment
===================================================

The Controller allows to execute performance measurement experiments
on a network. The section ``srv6pm``/``configuration`` of the
Command-Line Interface provides several functions to start and control
performance experiments.


Entering the ``srv6pm``/``experiment`` section
----------------------------------------------

.. code:: bash

  controller> srv6pm
  controller(srv6pm)> experiment
  controller(srv6pm-experiment)> 

Section ``srv6pm``/``experiment`` supports the following commands:

.. code:: bash

  exit  help  show  start  stop


``show``
--------

Show the results of an experiment.

.. code:: bash

  controller(srv6pm-experiment)> show --help
  usage: show [-h] --sender-ip SENDER_IP --sender-port SENDER_PORT
              --reflector-ip REFLECTOR_IP --reflector-port REFLECTOR_PORT [-s]
              [-c SERVER_CERT] --send_refl_sidlist SEND_REFL_SIDLIST
              --refl_send_sidlist REFL_SEND_SIDLIST [-d]

  Show the results of an experiment

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
    -c SERVER_CERT, --server-cert SERVER_CERT
                          CA certificate file
    --send_refl_sidlist SEND_REFL_SIDLIST
                          send_refl_sidlist
    --refl_send_sidlist REFL_SEND_SIDLIST
                          refl_send_sidlist
    -d, --debug           Activate debug logs


``start``
---------

Start a new experiment.

.. code:: bash

  controller(srv6pm-experiment)> start --help
  usage: start [-h] --sender-ip SENDER_IP --sender-port SENDER_PORT
               --reflector-ip REFLECTOR_IP --reflector-port REFLECTOR_PORT [-s]
               [-c SERVER_CERT] --send_refl_dest SEND_REFL_DEST --refl_send_dest
               REFL_SEND_DEST --send_refl_sidlist SEND_REFL_SIDLIST
               --refl_send_sidlist REFL_SEND_SIDLIST
               [--measurement_protocol MEASUREMENT_PROTOCOL]
               [--measurement_type MEASUREMENT_TYPE]
               [--authentication_mode AUTHENTICATION_MODE]
               [--authentication_key AUTHENTICATION_KEY]
               [--timestamp_format TIMESTAMP_FORMAT]
               [--delay_measurement_mode DELAY_MEASUREMENT_MODE]
               [--padding_mbz PADDING_MBZ]
               [--loss_measurement_mode LOSS_MEASUREMENT_MODE] --measure_id
               MEASURE_ID [--send_refl_localseg SEND_REFL_LOCALSEG]
               [--refl_send_localseg REFL_SEND_LOCALSEG] [--force] [-d]

  Start a new experiment

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
    -c SERVER_CERT, --server-cert SERVER_CERT
                          CA certificate file
    --send_refl_dest SEND_REFL_DEST
                          send_refl_dest
    --refl_send_dest REFL_SEND_DEST
                          refl_send_dest
    --send_refl_sidlist SEND_REFL_SIDLIST
                          send_refl_sidlist
    --refl_send_sidlist REFL_SEND_SIDLIST
                          refl_send_sidlist
    --measurement_protocol MEASUREMENT_PROTOCOL
                          measurement_protocol
    --measurement_type MEASUREMENT_TYPE
                          measurement_type
    --authentication_mode AUTHENTICATION_MODE
                          authentication_mode
    --authentication_key AUTHENTICATION_KEY
                          authentication_key
    --timestamp_format TIMESTAMP_FORMAT
                          timestamp_format
    --delay_measurement_mode DELAY_MEASUREMENT_MODE
                          delay_measurement_mode
    --padding_mbz PADDING_MBZ
                          padding_mbz
    --loss_measurement_mode LOSS_MEASUREMENT_MODE
                          loss_measurement_mode
    --measure_id MEASURE_ID
                          measure_id
    --send_refl_localseg SEND_REFL_LOCALSEG
                          send_refl_localseg
    --refl_send_localseg REFL_SEND_LOCALSEG
                          refl_send_localseg
    --force               force
    -d, --debug           Activate debug logs


``stop``
--------

Stop a running experiment.

.. code:: bash

  controller(srv6pm-experiment)> stop --help
  usage: stop [-h] --sender-ip SENDER_IP --sender-port SENDER_PORT
              --reflector-ip REFLECTOR_IP --reflector-port REFLECTOR_PORT [-s]
              [-c SERVER_CERT] --send_refl_dest SEND_REFL_DEST --refl_send_dest
              REFL_SEND_DEST --send_refl_sidlist SEND_REFL_SIDLIST
              --refl_send_sidlist REFL_SEND_SIDLIST
              [--send_refl_localseg SEND_REFL_LOCALSEG]
              [--refl_send_localseg REFL_SEND_LOCALSEG] [-d]

  Stop a running experiment

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
    -c SERVER_CERT, --server-cert SERVER_CERT
                          CA certificate file
    --send_refl_dest SEND_REFL_DEST
                          send_refl_dest
    --refl_send_dest REFL_SEND_DEST
                          refl_send_dest
    --send_refl_sidlist SEND_REFL_SIDLIST
                          send_refl_sidlist
    --refl_send_sidlist REFL_SEND_SIDLIST
                          refl_send_sidlist
    --send_refl_localseg SEND_REFL_LOCALSEG
                          send_refl_localseg
    --refl_send_localseg REFL_SEND_LOCALSEG
                          refl_send_localseg
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

