#!/usr/bin/python

##########################################################################
# Copyright (C) 2020 Carmine Scarpitta - (Consortium GARR and University of Rome "Tor Vergata")
# www.garr.it - www.uniroma2.it/netgroup
#
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Example showing how it is possible to switch from a SRv6
# tunnel to another by acting on the metric parameter
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


# Imports
import os
import logging
import time
from threading import Thread

# SRv6PM dependencies
from controller import srv6_pm
from controller import utils

# Proto dependencies
import srv6pmCommons_pb2

# Folder containing this script
BASE_PATH = os.path.dirname(os.path.realpath(__file__))


# Global variables definition
#
#
# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)
#
# Port of the gRPC server
GRPC_PORT = 12345

SENDER = 'fcfd:0:0:1::1'
REFLECTOR = 'fcfd:0:0:8::1'


def set_configuration():
    """Start a new experiment"""

    logger.info('*** Set experiment configuration')
    # IP addresses
    sender = SENDER
    reflector = REFLECTOR
    logger.info('Sender: %s' % sender)
    logger.info('Reflector: %s' % reflector)
    # Open gRPC channels
    with utils.get_grpc_session(sender, GRPC_PORT) as sender_channel, \
            utils.get_grpc_session(reflector, GRPC_PORT) as reflector_channel:
        # Start the experiment
        srv6_pm.set_configuration(
            sender_channel=sender_channel,
            reflector_channel=reflector_channel,
            send_udp_port=1205,
            refl_udp_port=1206,
            interval_duration=10,
            delay_margin=5,  # sec assert(<interval)
            number_of_color=2,  # sec assert(==2)
            pm_driver=srv6pmCommons_pb2.PMDriver.Value('eBPF')
        )


def start_experiment():
    """Start a new experiment"""

    logger.info('*** Starting a new experiment')
    # IP addresses
    sender = SENDER
    reflector = REFLECTOR
    logger.info('Sender: %s' % sender)
    logger.info('Reflector: %s' % reflector)
    # Open gRPC channels
    with utils.get_grpc_session(sender, GRPC_PORT) as sender_channel, \
            utils.get_grpc_session(reflector, GRPC_PORT) as reflector_channel:
        # Start the experiment
        srv6_pm.start_experiment(
            sender_channel=sender_channel,
            reflector_channel=reflector_channel,
            send_refl_dest='fd00:0:83::2',
            refl_send_dest='fd00:0:13::2',
            send_refl_sidlist=['fcff:3::1', 'fcff:4::1', 'fcff:8::100'],
            refl_send_sidlist=['fcff:4::1', 'fcff:3::1', 'fcff:1::100'],
            send_refl_localseg='fcff:8::100',
            refl_send_localseg='fcff:1::100',
            send_in_interfaces=['r1-r2'],
            refl_in_interfaces=['r8-r6'],
            send_out_interfaces=['r1-r2_egr'],
            refl_out_interfaces=['r8-r6_egr'],
            measurement_protocol='TWAMP',
            measurement_type='LOSS',
            authentication_mode='HMAC_SHA_256',
            authentication_key='s75pbhd-xsh;290f',
            timestamp_format='PTPv2',
            delay_measurement_mode='OneWay',
            padding_mbz=10,
            loss_measurement_mode='Inferred',
            force=True
        )


# def start_experiment_no_measure_id():         No longer supported?
#     """Start a new experiment (without the measure_id)"""

#     logger.info('*** Starting a new experiment')
#     # IP addresses
#     sender = SENDER
#     reflector = REFLECTOR
#     logger.info('Sender: %s' % sender)
#     logger.info('Reflector: %s' % reflector)
#     # Open gRPC channels
#     with utils.get_grpc_session(sender, GRPC_PORT) as sender_channel, \
#             utils.get_grpc_session(reflector, GRPC_PORT) as reflector_channel:
#         # Start the experiment
#         srv6_pm.start_experiment(
#             measure_id=100,
#             sender_channel=sender_channel,
#             reflector_channel=reflector_channel,
#             send_refl_dest='fd00:0:83::/64',
#             refl_send_dest='fd00:0:13::/64',
#             send_refl_sidlist=['fcff:3::1', 'fcff:8::100'],
#             refl_send_sidlist=['fcff:3::1', 'fcff:1::100'],
#             send_refl_localseg='fcff:8::100',
#             refl_send_localseg='fcff:1::100',
#             send_in_interfaces=[],
#             refl_in_interfaces=[],
#             send_out_interfaces=[],
#             refl_out_interfaces=[],
#             measurement_protocol='TWAMP',
#             measurement_type='LOSS',
#             authentication_mode='HMAC_SHA_256',
#             authentication_key='s75pbhd-xsh;290f',
#             timestamp_format='PTPv2',
#             delay_measurement_mode='OneWay',
#             padding_mbz=10,
#             loss_measurement_mode='Inferred',
#         )


def get_experiment_results():
    """Get the results of a running experiment"""

    logger.info('*** Get experiment results')
    # IP addresses
    sender = SENDER
    reflector = REFLECTOR
    logger.info('Sender: %s' % sender)
    logger.info('Reflector: %s' % reflector)
    # Open gRPC channels
    with utils.get_grpc_session(sender, GRPC_PORT) as sender_channel, \
            utils.get_grpc_session(reflector, GRPC_PORT) as reflector_channel:
        # Get the results
        results = srv6_pm.get_experiment_results(
            sender_channel=sender_channel,
            reflector_channel=reflector_channel,
            send_refl_sidlist=['fcff:3::1', 'fcff:4::1', 'fcff:8::100'],
            refl_send_sidlist=['fcff:4::1', 'fcff:3::1', 'fcff:1::100'],
        )
    # Check for errors
    if results is None:
        print('Error in get_experiment_results()')
        print()
        return
    # Print the results
    for result in results:
        print("------------------------------")
        print("Measurement ID: %s" % result['measure_id'])
        print("Interval: %s" % result['interval'])
        print("Timestamp: %s" % result['timestamp'])
        print("FW Color: %s" % result['fw_color'])
        print("RV Color: %s" % result['rv_color'])
        print("sender_seq_num: %s" % result['sender_seq_num'])
        print("reflector_seq_num: %s" % result['reflector_seq_num'])
        print("Sender TX counter: %s" % result['sender_tx_counter'])
        print("Sender RX counter: %s" % result['sender_rx_counter'])
        print("Reflector TX counter: %s" % result['reflector_tx_counter'])
        print("Reflector RX counter: %s" % result['reflector_rx_counter'])
        print("------------------------------")
        print()
    print()


def stop_experiment():
    """Stop a running experiment"""

    logger.info('*** Stopping experiment')
    # IP addresses
    sender = SENDER
    reflector = REFLECTOR
    logger.info('Sender: %s' % sender)
    logger.info('Reflector: %s' % reflector)
    # Open gRPC channels
    with utils.get_grpc_session(sender, GRPC_PORT) as sender_channel, \
            utils.get_grpc_session(reflector, GRPC_PORT) as reflector_channel:
        # Stop the experiment
        srv6_pm.stop_experiment(
            sender_channel=sender_channel,
            reflector_channel=reflector_channel,
            send_refl_dest='fd00:0:83::2',
            refl_send_dest='fd00:0:13::2',
            send_refl_sidlist=['fcff:3::1', 'fcff:4::1', 'fcff:8::100'],
            refl_send_sidlist=['fcff:4::1', 'fcff:3::1', 'fcff:1::100'],
            send_refl_localseg='fcff:8::100',
            refl_send_localseg='fcff:1::100',
        )


# Entry point for this script
if __name__ == "__main__":
    # Enable debug mode
    debug = True
    # IP address of the gRPC server
    grpc_server_ip = '::'
    # Port of the gRPC server
    grpc_server_port = 50051
    # Port of the gRPC client
    grpc_client_port = 50052
    # Create a new SRv6 Controller
    Thread(
        target=srv6_pm.__start_grpc_server,
        kwargs={
            'grpc_ip': grpc_server_ip,
            'grpc_port': grpc_server_port,
            'secure': False
        }
    ).start()
    # Start a new experiment
    print()
    print()
    set_configuration()
    # start_experiment_no_measure_id()
    start_experiment()
    # Collects results
    for i in range(100):
        # Wait for 10 seconds
        time.sleep(10)
        # Get the results
        get_experiment_results()
    # Wait for few seconds
    time.sleep(2)
    # Stop the experiment
    stop_experiment()
    print()
    print()
