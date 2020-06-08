#!/usr/bin/python

##############################################################################################
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
# Topology information extraction
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


# General imports
import os
from concurrent import futures
import grpc
import logging
import time
import json

# Controller dependencies
from control_plane.controller import utils
from control_plane.controller import srv6_utils

# Configuration parameters
#
# Kafka support
ENABLE_KAFKA_INTEGRATION = os.getenv('ENABLE_KAFKA_INTEGRATION', 'false')
if ENABLE_KAFKA_INTEGRATION.lower() == 'true':
    ENABLE_KAFKA_INTEGRATION = True
else:
    ENABLE_KAFKA_INTEGRATION = False
# gRPC sserver
ENABLE_GRPC_SERVER = os.getenv('ENABLE_GRPC_SERVER', 'false')
if ENABLE_GRPC_SERVER.lower() == 'true':
    ENABLE_GRPC_SERVER = True
else:
    ENABLE_GRPC_SERVER = False
# Kafka server
KAFKA_SERVERS = os.getenv('KAFKA_SERVERS', 'kafka:9092')

# Kafka depedencies
if ENABLE_KAFKA_INTEGRATION:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError

# SRv6PM dependencies
import commons_pb2
import srv6pmCommons_pb2
import srv6pmSender_pb2
import srv6pmReflector_pb2
import srv6pmService_pb2_grpc
import srv6pmServiceController_pb2_grpc
import srv6pmServiceController_pb2


# Global variables definition
#
#
# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)
# Default parameters for SRv6 controller
#
# Default IP address of the gRPC server
DEFAULT_GRPC_SERVER_IP = '::'
# Default port of the gRPC server
DEFAULT_GRPC_SERVER_PORT = 12345
# Default port of the gRPC client
DEFAULT_GRPC_CLIENT_PORT = 12345
# Define whether to use SSL or not for the gRPC client
DEFAULT_CLIENT_SECURE = False
# SSL certificate of the root CA
DEFAULT_CLIENT_CERTIFICATE = 'client_cert.pem'
# Define whether to use SSL or not for the gRPC server
DEFAULT_SERVER_SECURE = False
# SSL certificate of the gRPC server
DEFAULT_SERVER_CERTIFICATE = 'server_cert.pem'
# SSL key of the gRPC server
DEFAULT_SERVER_KEY = 'server_cert.pem'

# Topic for TWAMP data
TOPIC_TWAMP = 'twamp'
# Topic for iperf data
TOPIC_IPERF = 'iperf'

# Kafka servers
if KAFKA_SERVERS is not None:
    KAFKA_SERVERS = KAFKA_SERVERS.split(',')


"""
A class used to represent a SRv6 Controller

...

Attributes
----------
grpc_server_ip : str
    the IP address of the gRPC server
grpc_server_port : int
    the port of the gRPC server
grpc_client_port : int
    the port of the gRPC client
grpc_client_secure : bool
    define whether to use SSL or not to communicate with the gRPC server
    (default is False)
grpc_client_certificate : str
    the path of the CA root certificate required for the SSL
    (default is None)
grpc_server_secure : bool
    define whether to use SSL or not for the gRPC server
    (default is False)
grpc_server_certificate : str
    the path of the server certificate required for the SSL
    (default is None)
grpc_server_key : str
    the path of the server key required for the SSL
    (default is None)
debug : bool
    Define whether to enable debug mode or not (default is False)

Methods
-------
start_experiment(send_ip, refl_ip, send_dest, refl_dest, send_sidlist,
                    refl_sidlist, send_in_interfaces, refl_in_interfaces,
                    send_out_interfaces, refl_out_interfaces,
                    measurement_protocol, send_dst_udp_port,
                    refl_dst_udp_port, measurement_type, authentication_mode,
                    authentication_key, timestamp_format,
                    delay_measurement_mode, padding_mbz,
                    loss_measurement_mode, interval_duration, delay_margin,
                    number_of_color, measure_id=None, send_localseg=None,
                    refl_localseg=None)
    Start an experiment

get_experiment_results(sender, reflector,
                        send_refl_sidlist, refl_send_sidlist)
    Get the results of a running experiment

stop_experiment(sender, reflector, send_refl_dest,
                refl_send_dest, send_refl_sidlist, refl_send_sidlist,
                send_refl_localseg=None, refl_send_localseg=None)
    Stop a running experiment
"""


# def __init__(self, grpc_server_ip, grpc_server_port, grpc_client_port,
#              grpc_client_secure=False, grpc_client_certificate=None,
#              grpc_server_secure=False, grpc_server_certificate=None,
#              grpc_server_key=None, debug=False):
#     """
#     Parameters
#     ----------
#     grpc_server_ip : str
#         the IP address of the gRPC server
#     grpc_server_port : int
#         the port of the gRPC server
#     grpc_client_port : int
#         the port of the gRPC client
#     grpc_client_secure : bool
#         define whether to use SSL or not to communicate with the gRPC server
#         (default is False)
#     grpc_client_certificate : str
#         the path of the CA root certificate required for the SSL
#         (default is None)
#     grpc_server_secure : bool
#         define whether to use SSL or not for the gRPC server
#         (default is False)
#     grpc_server_certificate : str
#         the path of the server certificate required for the SSL
#         (default is None)
#     grpc_server_key : str
#         the path of the server key required for the SSL
#         (default is None)
#     debug : bool
#         define whether to enable debug mode or not (default is False)
#     """

#     logger.info('Initializing SRv6 controller')
#     # Port of the gRPC client
#     self.grpc_client_port = grpc_client_port
#     # Measure ID
#     self.measure_id = -1
#     # gRPC secure mode
#     self.grpc_client_secure = grpc_client_secure
#     # SSL certificate of the root CA required for gRPC secure mode
#     self.grpc_client_certificate = grpc_client_certificate
#     # Debug mode
#     self.debug = debug
#     # Setup properly the logger
#     if self.debug:
#         logger.setLevel(level=logging.DEBUG)
#     else:
#         logger.setLevel(level=logging.INFO)
#     # Mapping IP address to gRPC channels
#     self.grpc_channels = dict()
#     # Start the gRPC server
#     # This is a blocking operation, so we need to execute it
#     # in a separated thread
#     kwargs = {
#         'grpc_ip': grpc_server_ip,
#         'grpc_port': grpc_server_port,
#         'secure': grpc_server_secure,
#         'key': grpc_server_key,
#         'certificate': grpc_server_certificate
#     }
#     Thread(target=self.__start_grpc_server, kwargs=kwargs).start()
#     time.sleep(1)


def publish_to_kafka(bootstrap_servers, topic, measure_id, interval,
                     timestamp, fw_color, rv_color, sender_seq_num,
                     reflector_seq_num, sender_tx_counter, sender_rx_counter,
                     reflector_tx_counter, reflector_rx_counter):
    producer = None
    result = None
    try:
        # Create an istance of Kafka producer
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            security_protocol='PLAINTEXT',
            value_serializer=lambda m: json.dumps(m).encode('ascii')
        )
        # Publish measurement data to the provided topic
        result = producer.send(
            topic=topic,
            value={'measure_id': measure_id, 'interval': interval,
                'timestamp': timestamp, 'fw_color': fw_color,
                'rv_color': rv_color, 'sender_seq_num': sender_seq_num,
                'reflector_seq_num': reflector_seq_num,
                'sender_tx_counter': sender_tx_counter,
                'sender_rx_counter': sender_rx_counter,
                'reflector_tx_counter': reflector_tx_counter,
                'reflector_rx_counter': reflector_rx_counter}
        )
    except KafkaError as e:
        logger.error('Cannot publish data to Kafka: %s' % e)
    finally:
        # Close the producer
        if producer is not None:
            producer.close()
    # Return result
    return result


def publish_iperf_data_to_kafka(bootstrap_servers, topic, _from, measure_id,
                                generator_id, interval, transfer,
                                transfer_dim, bitrate, bitrate_dim,
                                retr, cwnd, cwnd_dim):
    producer = None
    result = None
    try:
        # Create an istance of Kafka producer
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            security_protocol='PLAINTEXT',
            value_serializer=lambda m: json.dumps(m).encode('ascii')
        )
        # Publish measurement data to the provided topic
        result = producer.send(
            topic=topic,
            value={'from': _from,
                'measure_id': measure_id,
                'generator_id': generator_id,
                'interval': interval,
                'transfer': transfer,
                'transfer_dim': transfer_dim,
                'bitrate': bitrate,
                'bitrate_dim': bitrate_dim,
                'retr': retr,
                'cwnd': cwnd,
                'cwnd_dim': cwnd_dim
                }
        )
    except KafkaError as e:
        logger.error('Cannot publish data to Kafka: %s' % e)
    finally:
        # Close the producer
        if producer is not None:
            producer.close()
    # Return result
    return result


def start_experiment_sender(channel, sidlist, rev_sidlist,
                            # in_interfaces, out_interfaces,
                            measurement_protocol,
                            measurement_type, authentication_mode,
                            authentication_key, timestamp_format,
                            delay_measurement_mode, padding_mbz,
                            loss_measurement_mode):
    # Convert string args to int
    #
    # Measurement Protocol
    try:
        if type(measurement_protocol) == str:
            measurement_protocol = \
                srv6pmCommons_pb2.MeasurementProtocol.Value(
                    measurement_protocol)
    except ValueError:
        logger.error('Invalid Measurement protocol: %s' % measurement_protocol)
        return None
    # Measurement Type
    try:
        if type(measurement_type) == str:
            measurement_type = \
                srv6pmCommons_pb2.MeasurementType.Value(measurement_type)
    except ValueError:
        logger.error('Invalid Measurement Type: %s' % measurement_type)
        return None
    # Authentication Mode
    try:
        if type(authentication_mode) == str:
            authentication_mode = \
                srv6pmCommons_pb2.AuthenticationMode.Value(authentication_mode)
    except ValueError:
        logger.error('Invalid  Authentication Mode: %s' % authentication_mode)
        return None
    # Timestamp Format
    try:
        if type(timestamp_format) == str:
            timestamp_format = \
                srv6pmCommons_pb2.TimestampFormat.Value(timestamp_format)
    except ValueError:
        logger.error('Invalid Timestamp Format: %s' % timestamp_format)
        return None
    # Delay Measurement Mode
    try:
        if type(delay_measurement_mode) == str:
            delay_measurement_mode = \
                srv6pmCommons_pb2.MeasurementDelayMode.Value(
                    delay_measurement_mode)
    except ValueError:
        logger.error('Invalid Delay Measurement Mode: %s'
                     % delay_measurement_mode)
        return None
    # Loss Measurement Mode
    try:
        if type(loss_measurement_mode) == str:
            loss_measurement_mode = \
                srv6pmCommons_pb2.MeasurementLossMode.Value(
                    loss_measurement_mode)
    except ValueError:
        logger.error('Invalid Loss Measurement Mode: %s'
                     % loss_measurement_mode)
        return None
    #
    # Get the reference of the stub
    stub = srv6pmService_pb2_grpc.SRv6PMStub(channel)
    # Create the request
    request = srv6pmSender_pb2.StartExperimentSenderRequest()
    # Set the SID list
    request.sdlist = '/'.join(sidlist)
    # Set the reverse SID list
    request.sdlistreverse = '/'.join(rev_sidlist)
    # Set the incoming interfaces
    # request.in_interfaces.extend(in_interfaces)
    # # Set the outgoing interfaces
    # request.out_interfaces.extend(out_interfaces)
    #
    # Set the sender options
    #
    # Set the measureemnt protocol
    request.sender_options.measurement_protocol = measurement_protocol
    # Set the authentication mode
    request.sender_options.authentication_mode = authentication_mode
    # Set the authentication key
    request.sender_options.authentication_key = str(authentication_key)
    # Set the measurement type
    request.sender_options.measurement_type = measurement_type
    # Set the timestamp format
    request.sender_options.timestamp_format = timestamp_format
    # Set the measurement delay mode
    request.sender_options.measurement_delay_mode = delay_measurement_mode
    # Set the padding
    request.sender_options.padding_mbz = int(padding_mbz)
    # Set the measurement loss mode
    request.sender_options.measurement_loss_mode = loss_measurement_mode
    #
    # Start the experiment on the sender and return the response
    return stub.startExperimentSender(request=request)


def stop_experiment_sender(channel, sidlist):
    # Get the reference of the stub
    stub = srv6pmService_pb2_grpc.SRv6PMStub(channel)
    # Create the request message
    request = srv6pmCommons_pb2.StopExperimentRequest()
    # Set the SID list
    request.sdlist = '/'.join(sidlist)
    # Stop the experiment on the sender and return the response
    return stub.stopExperimentSender(request=request)


def retrieve_experiment_results_sender(channel, sidlist):
    # Get the reference of the stub
    stub = srv6pmService_pb2_grpc.SRv6PMStub(channel)
    # Create the request message
    request = srv6pmCommons_pb2.RetriveExperimentDataRequest()
    # Set the SID list
    request.sdlist = '/'.join(sidlist)
    # Retrieve the experiment results from the sender and return them
    return stub.retriveExperimentResults(request=request)


def set_node_configuration(channel, send_udp_port, refl_udp_port,
                           interval_duration, delay_margin,
                           number_of_color, pm_driver):
    # Convert string args to int
    #
    # PM Driver
    try:
        if type(pm_driver) == str:
            pm_driver = srv6pmCommons_pb2.PMDriver.Value(pm_driver)
    except ValueError:
        logger.error('Invalid PM Driver: %s' % pm_driver)
        return None
    #
    # Get the reference of the stub
    stub = srv6pmService_pb2_grpc.SRv6PMStub(channel)
    # Create the request message
    request = srv6pmCommons_pb2.Configuration()
    # Set the destination UDP port of the sender
    request.ss_udp_port = int(send_udp_port)
    # Set the destination UDP port of the reflector
    request.refl_udp_port = int(refl_udp_port)
    #
    # Set the color options
    #
    # Set the interval duration
    request.color_options.interval_duration = int(interval_duration)
    # Set the delay margin
    request.color_options.delay_margin = int(delay_margin)
    # Set the number of color
    request.color_options.numbers_of_color = int(number_of_color)
    #
    # Set driver
    request.pm_driver = pm_driver
    # Start the experiment on the reflector and return the response
    return stub.setConfiguration(request=request)


def reset_node_configuration(channel):
    # Get the reference of the stub
    stub = srv6pmService_pb2_grpc.SRv6PMStub(channel)
    # Create the request message
    request = srv6pmCommons_pb2.Configuration()
    # Start the experiment on the reflector and return the response
    return stub.resetConfiguration(request=request)


def start_experiment_reflector(channel, sidlist, rev_sidlist,
                               # in_interfaces, out_interfaces,
                               measurement_protocol, measurement_type,
                               authentication_mode, authentication_key,
                               loss_measurement_mode):
    # Convert string args to int
    #
    # Measurement Protocol
    try:
        if type(measurement_protocol) == str:
            measurement_protocol = \
                srv6pmCommons_pb2.MeasurementProtocol.Value(
                    measurement_protocol)
    except ValueError:
        logger.error('Invalid Measurement protocol: %s' % measurement_protocol)
        return None
    # Measurement Type
    try:
        if type(measurement_type) == str:
            measurement_type = \
                srv6pmCommons_pb2.MeasurementType.Value(measurement_type)
    except ValueError:
        logger.error('Invalid Measurement Type: %s' % measurement_type)
        return None
    # Authentication Mode
    try:
        if type(authentication_mode) == str:
            authentication_mode = \
                srv6pmCommons_pb2.AuthenticationMode.Value(authentication_mode)
    except ValueError:
        logger.error('Invalid  Authentication Mode: %s' % authentication_mode)
        return None
    # Loss Measurement Mode
    try:
        if type(loss_measurement_mode) == str:
            loss_measurement_mode = \
                srv6pmCommons_pb2.MeasurementLossMode.Value(
                    loss_measurement_mode)
    except ValueError:
        logger.error('Invalid Loss Measurement Mode: %s'
                     % loss_measurement_mode)
        return None
    #
    # Get the reference of the stub
    stub = srv6pmService_pb2_grpc.SRv6PMStub(channel)
    # Create the request message
    request = srv6pmReflector_pb2.StartExperimentReflectorRequest()
    # Set the SID list
    request.sdlist = '/'.join(sidlist)
    # Set the reverse SID list
    request.sdlistreverse = '/'.join(rev_sidlist)
    # Set the incoming interfaces
    # request.in_interfaces.extend(in_interfaces)
    # # Set the outgoing interfaces
    # request.out_interfaces.extend(out_interfaces)
    #
    # Set the reflector options
    #
    # Set the measurement protocol
    request.reflector_options.measurement_protocol = measurement_protocol
    # Set the authentication mode
    request.reflector_options.authentication_mode = authentication_mode
    # Set the authentication key
    request.reflector_options.authentication_key = str(authentication_key)
    # Set the measurement type
    request.reflector_options.measurement_type = measurement_type
    # Set the measurement loss mode
    request.reflector_options.measurement_loss_mode = loss_measurement_mode
    # Start the experiment on the reflector and return the response
    return stub.startExperimentReflector(request=request)


def stop_experiment_reflector(channel, sidlist):
    # Get the reference of the stub
    stub = srv6pmService_pb2_grpc.SRv6PMStub(channel)
    # Create the request message
    request = srv6pmCommons_pb2.StopExperimentRequest()
    # Set the SID list
    request.sdlist = '/'.join(sidlist)
    # Stop the experiment on the reflector and return the response
    return stub.stopExperimentReflector(request=request)


def __start_measurement(measure_id, sender_channel, reflector_channel,
                        send_refl_sidlist, refl_send_sidlist,
                        # send_in_interfaces, refl_in_interfaces,
                        # send_out_interfaces, refl_out_interfaces,
                        measurement_protocol, measurement_type,
                        authentication_mode, authentication_key,
                        timestamp_format, delay_measurement_mode,
                        padding_mbz, loss_measurement_mode):
    """Start the measurement process on reflector and sender.

    Parameters
    ----------
    measure_id : int
        Identifier for the experiment
    sender_channel : <gRPC Channel>
        The gRPC Channel to the sender node
    reflector_channel : <gRPC Channel>
        The gRPC Channel to the reflector node
    send_refl_sidlist : list
        The SID list to be used for the path sender->reflector
    refl_send_sidlist : list
        The SID list to be used for the path reflector->sender
    send_in_interfaces : list
        The list of the incoming interfaces of the sender
    refl_in_interfaces : list
        The list of the incoming interfaces of the reflector
    send_out_interfaces : list
        The list of the outgoing interfaces of the sender
    refl_out_interfaces : list
        The list of the outgoing interfaces of the reflector
    measurement_protocol : str
        The measurement protocol (i.e. TWAMP or STAMP)
    measurement_type : str
        The measurement type (i.e. delay or loss)
    authentication_mode : str
        The authentication mode (i.e. HMAC_SHA_256)
    authentication_key : str
        The authentication key
    timestamp_format : str
        The Timestamp Format (i.e. PTPv2 or NTP)
    delay_measurement_mode : str
        Delay measurement mode (i.e. one-way, two-way or loopback mode)
    padding_mbz : int
        The padding size
    loss_measurement_mode : str
        The loss measurement mode (i.e. Inferred or Direct mode)
    """

    print("\n************** Start Measurement **************\n")
    # Start the experiment on the reflector
    refl_res = start_experiment_reflector(
        channel=reflector_channel,
        sidlist=send_refl_sidlist,
        rev_sidlist=refl_send_sidlist,
        # in_interfaces=refl_in_interfaces,
        # out_interfaces=refl_out_interfaces,
        measurement_protocol=measurement_protocol,
        measurement_type=measurement_type,
        authentication_mode=authentication_mode,
        authentication_key=authentication_key,
        loss_measurement_mode=loss_measurement_mode,
    )
    # Pretty print status code
    utils.__print_status_message(
        status_code=refl_res.status,
        success_msg='Started Measure Reflector',
        failure_msg='Error in start_experiment_reflector()'
    )
    # Check for errors
    if refl_res is None:
        return commons_pb2.STATUS_INTERNAL_ERROR
    elif refl_res.status != commons_pb2.STATUS_SUCCESS:
        return refl_res.status
    # Start the experiment on the sender
    sender_res = start_experiment_sender(
        channel=sender_channel,
        sidlist=send_refl_sidlist,
        rev_sidlist=refl_send_sidlist,
        # in_interfaces=send_in_interfaces,
        # out_interfaces=send_out_interfaces,
        measurement_protocol=measurement_protocol,
        measurement_type=measurement_type,
        authentication_mode=authentication_mode,
        authentication_key=authentication_key,
        timestamp_format=timestamp_format,
        delay_measurement_mode=delay_measurement_mode,
        padding_mbz=padding_mbz,
        loss_measurement_mode=loss_measurement_mode,
    )
    # Pretty print status code
    utils.__print_status_message(
        status_code=sender_res.status,
        success_msg='Started Measure Sender',
        failure_msg='Error in start_experiment_sender()'
    )
    # Check for errors
    if sender_res is None:
        return commons_pb2.STATUS_INTERNAL_ERROR
    elif sender_res.status != commons_pb2.STATUS_SUCCESS:
        return sender_res.status
    # Success
    return commons_pb2.STATUS_SUCCESS


def __get_measurement_results(sender_channel, reflector_channel,
                              send_refl_sidlist, refl_send_sidlist):
    """Get the results of a measurement process.

    Parameters
    ----------
    sender_channel : <gRPC Channel>
        The gRPC Channel to the sender node
    reflector_channel : <gRPC Channel>
        The gRPC Channel to the reflector node
    send_refl_sidlist : list
        The SID list used for sender->reflector path
    refl_send_sidlist : list
        The SID list used for reflector->sender path
    """

    # Retrieve the results of the experiment
    print("\n************** Get Measurement Data **************\n")
    # Retrieve the results from the sender
    sender_res = retrieve_experiment_results_sender(
        channel=sender_channel,
        sidlist=send_refl_sidlist
    )
    # Pretty print status code
    utils.__print_status_message(
        status_code=sender_res.status,
        success_msg='Received Data Sender',
        failure_msg='Error in retrieve_experiment_results_sender()'
    )
    # Collect the results
    res = None
    if sender_res.status == commons_pb2.STATUS_SUCCESS:
        res = list()
        for data in sender_res.measurement_data:
            res.append({
                'measure_id': data.meas_id,
                'interval': data.interval,
                'timestamp': data.timestamp,
                'fw_color': data.fwColor,
                'rv_color': data.rvColor,
                'sender_seq_num': data.ssSeqNum,
                'reflector_seq_num': data.rfSeqNum,
                'sender_tx_counter': data.ssTxCounter,
                'sender_rx_counter': data.ssRxCounter,
                'reflector_tx_counter': data.rfTxCounter,
                'reflector_rx_counter': data.rfRxCounter,
            })
    # Return the results
    return res


def __stop_measurement(sender_channel, reflector_channel,
                       send_refl_sidlist, refl_send_sidlist):
    """Stop a measurement process on reflector and sender.

    Parameters
    ----------
    sender_channel : <gRPC Channel>
        The gRPC Channel to the sender node
    reflector_channel : <gRPC Channel>
        The gRPC Channel to the reflector node
    send_refl_sidlist : list
        The SID list used for the path sender->reflector
    refl_send_sidlist : list
        The SID list used for the path reflector->sender
    """

    print("\n************** Stop Measurement **************\n")
    # Stop the experiment on the sender
    sender_res = stop_experiment_sender(
        channel=sender_channel,
        sidlist=send_refl_sidlist
    )
    # Pretty print status code
    utils.__print_status_message(
        status_code=sender_res.status,
        success_msg='Stopped Measure Sender',
        failure_msg='Error in stop_experiment_sender()'
    )
    # Check for errors
    if sender_res.status != commons_pb2.STATUS_SUCCESS:
        return sender_res.status
    # Stop the experiment on the reflector
    refl_res = stop_experiment_reflector(
        channel=reflector_channel,
        sidlist=refl_send_sidlist
    )
    # Pretty print status code
    utils.__print_status_message(
        status_code=refl_res.status,
        success_msg='Stopped Measure Reflector',
        failure_msg='Error in stop_experiment_reflector()'
    )
    # Check for errors
    if refl_res.status != commons_pb2.STATUS_SUCCESS:
        return refl_res.status
    # Success
    return commons_pb2.STATUS_SUCCESS


def set_configuration(sender_channel, reflector_channel,
                      send_udp_port, refl_udp_port,
                      interval_duration, delay_margin,
                      number_of_color, pm_driver):
    """Set the configuration

    Parameters
    ----------
    sender_channel : <gRPC Channel>
        The gRPC Channel to the sender node
    reflector_channel : <gRPC Channel>
        The gRPC Channel to the reflector node
    send_dst_udp_port : int
        The destination UDP port used by the sender
    refl_dst_udp_port : int
        The destination UDP port used by the reflector
    interval_duration : int
        The duration of the interval
    delay_margin : int
        The delay margin
    number_of_color : int
        The number of the color
    """

    # Set configuration on the sender
    res = set_node_configuration(
        channel=sender_channel,
        send_udp_port=send_udp_port,
        refl_udp_port=refl_udp_port,
        interval_duration=interval_duration,
        delay_margin=delay_margin,
        number_of_color=number_of_color,
        pm_driver=pm_driver
    )
    # Check for errors
    if res.status != commons_pb2.STATUS_SUCCESS:
        return res
    # Set configuration on the reflector
    res = set_node_configuration(
        channel=reflector_channel,
        send_udp_port=send_udp_port,
        refl_udp_port=refl_udp_port,
        interval_duration=interval_duration,
        delay_margin=delay_margin,
        number_of_color=number_of_color,
        pm_driver=pm_driver
    )
    # Check for errors
    if res.status != commons_pb2.STATUS_SUCCESS:
        return res
    # Success
    return commons_pb2.STATUS_SUCCESS


def reset_configuration(sender_channel, reflector_channel):
    """Reset the configuration

    Parameters
    ----------
    sender_channel : <gRPC Channel>
        The gRPC Channel to the sender node
    reflector_channel : <gRPC Channel>
        The gRPC Channel to the reflector node
    send_dst_udp_port : int
        The destination UDP port used by the sender
    refl_dst_udp_port : int
        The destination UDP port used by the reflector
    interval_duration : int
        The duration of the interval
    delay_margin : int
        The delay margin
    number_of_color : int
        The number of the color
    """

    # Reset configuration on the sender
    res = reset_node_configuration(
        channel=sender_channel
    )
    # Check for errors
    if res.status != commons_pb2.STATUS_SUCCESS:
        return res
    # Reset configuration on the reflector
    res = reset_node_configuration(
        channel=reflector_channel
    )
    # Check for errors
    if res.status != commons_pb2.STATUS_SUCCESS:
        return res
    # Success
    return commons_pb2.STATUS_SUCCESS


def start_experiment(sender_channel, reflector_channel, send_refl_dest,
                     refl_send_dest, send_refl_sidlist, refl_send_sidlist,
                    #  send_in_interfaces, refl_in_interfaces,
                    #  send_out_interfaces, refl_out_interfaces,
                     measurement_protocol, measurement_type,
                     authentication_mode, authentication_key,
                     timestamp_format, delay_measurement_mode,
                     padding_mbz, loss_measurement_mode, measure_id=None,
                     send_refl_localseg=None, refl_send_localseg=None,
                     force=False):
    """Start an experiment.

    Parameters
    ----------
    sender_channel : <gRPC Channel>
        The gRPC Channel to the sender node
    reflector_channel : <gRPC Channel>
        The gRPC Channel to the reflector node
    send_refl_dest : str
        The destination of the SRv6 path sender->reflector
    refl_send_dest : str
        The destination of the SRv6 path reflector->sender
    send_refl_sidlist : list
        The SID list to be used for the path sender->reflector
    refl_send_sidlist : list
        The SID list to be used for the path reflector->sender
    send_in_interfaces : list
        The list of the incoming interfaces of the sender
    refl_in_interfaces : list
        The list of the incoming interfaces of the reflector
    send_out_interfaces : list
        The list of the outgoing interfaces of the sender
    refl_out_interfaces : list
        The list of the outgoing interfaces of the reflector
    measurement_protocol : str
        The measurement protocol (i.e. TWAMP or STAMP)
    measurement_type : str
        The measurement type (i.e. delay or loss)
    authentication_mode : str
        The authentication mode (i.e. HMAC_SHA_256)
    authentication_key : str
        The authentication key
    timestamp_format : str
        The Timestamp Format (i.e. PTPv2 or NTP)
    delay_measurement_mode : str
        Delay measurement mode (i.e. one-way, two-way or loopback mode)
    padding_mbz : int
        The padding size
    loss_measurement_mode : str
        The loss measurement mode (i.e. Inferred or Direct mode)
    measure_id : int, optional
        Identifier for the experiment (default is None).
        If the argument 'measure_id' isn't passed in, the measure_id is
        automatically generated.
    send_refl_localseg : str, optional
        The local segment associated to the End.DT6 (decap) function
        for the path sender->reflector (default is None).
        If the argument 'send_localseg' isn't passed in, the seg6local
        End.DT6 route is not created.
    refl_send_localseg : str, optional
        The local segment associated to the End.DT6 (decap) function
        for the path reflector->sender (default is None).
        If the argument 'send_localseg' isn't passed in, the seg6local
        End.DT6 route is not created.
    force : bool, optional
        If set, force the controller to start an experiment if a
        SRv6 path for the destination already exists. The old SRv6 path
        is replaced with the new one (default is False).
    """

    # If the force flag is set and SRv6 path already exists, remove
    # the old path before creating the new one
    if force:
        res = srv6_utils.__destroy_srv6_tunnel(
            node_l_channel=sender_channel,
            node_r_channel=reflector_channel,
            dest_lr=send_refl_dest,
            dest_rl=refl_send_dest,
            localseg_lr=send_refl_localseg,
            localseg_rl=refl_send_localseg,
            ignore_errors=True
        )
        if res != commons_pb2.STATUS_SUCCESS:
            return res
    # Create a bidirectional SRv6 tunnel between the sender and the
    # reflector
    res = srv6_utils.__create_srv6_tunnel(
        node_l_channel=sender_channel,
        node_r_channel=reflector_channel,
        dest_lr=send_refl_dest,
        dest_rl=refl_send_dest,
        localseg_lr=send_refl_localseg,
        localseg_rl=refl_send_localseg,
        sidlist_lr=send_refl_sidlist,
        sidlist_rl=refl_send_sidlist
    )
    # Check for errors
    if res != commons_pb2.STATUS_SUCCESS:
        return res
    # Start measurement process
    res = __start_measurement(
        measure_id=measure_id,
        sender_channel=sender_channel,
        reflector_channel=reflector_channel,
        send_refl_sidlist=send_refl_sidlist,
        refl_send_sidlist=refl_send_sidlist,
        # send_in_interfaces=send_in_interfaces,
        # send_out_interfaces=send_out_interfaces,
        # refl_in_interfaces=refl_in_interfaces,
        # refl_out_interfaces=refl_out_interfaces,
        measurement_protocol=measurement_protocol,
        measurement_type=measurement_type,
        authentication_mode=authentication_mode,
        authentication_key=authentication_key,
        timestamp_format=timestamp_format,
        delay_measurement_mode=delay_measurement_mode,
        padding_mbz=padding_mbz,
        loss_measurement_mode=loss_measurement_mode,
    )
    # Check for errors
    if res != commons_pb2.STATUS_SUCCESS:
        return res
    # Success
    return commons_pb2.STATUS_SUCCESS


def get_experiment_results(sender_channel, reflector_channel,
                           send_refl_sidlist, refl_send_sidlist,
                           kafka_servers=KAFKA_SERVERS):
    """Get the results of an experiment.

    Parameters
    ----------
    sender_channel : <gRPC Channel>
        The gRPC Channel to the sender node
    reflector_channel : <gRPC Channel>
        The gRPC Channel to the reflector node
    send_refl_sidlist : list
        The SID list to be used for the path sender->reflector
    refl_send_sidlist : list
        The SID list to be used for the path reflector->sender
    kafka_servers : str
        IP:port of Kafka server
    """

    # Get the results
    results = __get_measurement_results(
        sender_channel=sender_channel,
        reflector_channel=reflector_channel,
        send_refl_sidlist=send_refl_sidlist,
        refl_send_sidlist=refl_send_sidlist
    )
    if results is None:
        print('No measurement data available')
        return
    # Publish results to Kafka
    if ENABLE_KAFKA_INTEGRATION:
        for res in results:
            measure_id = res['measure_id']
            interval = res['interval']
            timestamp = res['timestamp']
            fw_color = res['fw_color']
            rv_color = res['rv_color']
            sender_seq_num = res['sender_seq_num']
            reflector_seq_num = res['reflector_seq_num']
            sender_tx_counter = res['sender_tx_counter']
            sender_rx_counter = res['sender_rx_counter']
            reflector_tx_counter = res['reflector_tx_counter']
            reflector_rx_counter = res['reflector_rx_counter']
            # Publish data to Kafka
            publish_to_kafka(
                bootstrap_servers=kafka_servers,
                topic=TOPIC_TWAMP,
                measure_id=measure_id,
                interval=interval,
                timestamp=timestamp,
                fw_color=fw_color,
                rv_color=rv_color,
                sender_seq_num=sender_seq_num,
                reflector_seq_num=reflector_seq_num,
                sender_tx_counter=sender_tx_counter,
                sender_rx_counter=sender_rx_counter,
                reflector_tx_counter=reflector_tx_counter,
                reflector_rx_counter=reflector_rx_counter
            )
    # Return the results
    return results


def stop_experiment(sender_channel, reflector_channel, send_refl_dest,
                    refl_send_dest, send_refl_sidlist, refl_send_sidlist,
                    send_refl_localseg=None, refl_send_localseg=None):
    """Stop a running experiment.

    Parameters
    ----------
    sender_channel : <gRPC Channel>
        The gRPC Channel to the sender node
    reflector_channel : <gRPC Channel>
        The gRPC Channel to the reflector node
    send_refl_dest : str
        The destination of the SRv6 path sender->reflector
    refl_send_dest : str
        The destination of the SRv6 path reflector->sender
    send_refl_sidlist : list
        The SID list used for the path sender->reflector
    refl_send_sidlist : list
        The SID list used for the path reflector->sender
    send_refl_localseg : str, optional
        The local segment associated to the End.DT6 (decap) function
        for the path sender->reflector
        (default is None).
        If the argument 'send_localseg' isn't passed in, the seg6local
        End.DT6 route is not removed.
    refl_send_localseg : str, optional
        The local segment associated to the End.DT6 (decap) function
        for the path reflector->sender
        If the argument 'send_localseg' isn't passed in, the seg6local
        End.DT6 route is not removed.
    """

    # Stop the experiment
    res = __stop_measurement(
        sender_channel=sender_channel,
        reflector_channel=reflector_channel,
        send_refl_sidlist=send_refl_sidlist,
        refl_send_sidlist=refl_send_sidlist
    )
    # Check for errors
    if res != commons_pb2.STATUS_SUCCESS:
        return res
    # Remove the SRv6 path
    res = srv6_utils.__destroy_srv6_tunnel(
        node_l_channel=sender_channel,
        node_r_channel=reflector_channel,
        dest_lr=send_refl_dest,
        dest_rl=refl_send_dest,
        localseg_lr=send_refl_localseg,
        localseg_rl=refl_send_localseg
    )
    # Check for errors
    if res != commons_pb2.STATUS_SUCCESS:
        return res
    # Success
    return commons_pb2.STATUS_SUCCESS


if ENABLE_GRPC_SERVER:
    class _SRv6PMService(
            srv6pmServiceController_pb2_grpc.SRv6PMControllerServicer):
        """Private class implementing methods exposed by the gRPC server"""

        def __init__(self, kafka_servers=KAFKA_SERVERS):
            self.kafka_servers = kafka_servers

        def SendMeasurementData(self, request, context):
            """RPC used to send measurement data to the controller"""

            logger.debug('Measurement data received: %s' % request)
            # Extract data from the request
            for data in request.measurement_data:
                measure_id = data.meas_id
                interval = data.interval
                timestamp = data.timestamp
                fw_color = data.fwColor
                rv_color = data.rvColor
                sender_seq_num = data.ssSeqNum
                reflector_seq_num = data.rfSeqNum
                sender_tx_counter = data.ssTxCounter
                sender_rx_counter = data.ssRxCounter
                reflector_tx_counter = data.rfTxCounter
                reflector_rx_counter = data.rfRxCounter
                # Publish data to Kafka
                if ENABLE_KAFKA_INTEGRATION:
                    publish_to_kafka(
                        bootstrap_servers=self.kafka_servers,
                        topic=TOPIC_TWAMP,
                        measure_id=measure_id,
                        interval=interval,
                        timestamp=timestamp,
                        fw_color=fw_color,
                        rv_color=rv_color,
                        sender_seq_num=sender_seq_num,
                        reflector_seq_num=reflector_seq_num,
                        sender_tx_counter=sender_tx_counter,
                        sender_rx_counter=sender_rx_counter,
                        reflector_tx_counter=reflector_tx_counter,
                        reflector_rx_counter=reflector_rx_counter
                    )
            status = commons_pb2.StatusCode.Value('STATUS_SUCCESS')
            return srv6pmServiceController_pb2.SendMeasurementDataResponse(
                status=status)

        def SendIperfData(self, request, context):
            """RPC used to send iperf data to the controller"""

            logger.debug('Iperf data received: %s' % request)
            # Extract data from the request
            for data in request.iperf_data:
                # From client/server
                _from = data._from
                # Measure ID
                measure_id = data.measure_id
                # Generator ID
                generator_id = data.generator_id
                # Interval
                interval = data.interval.val
                # Transfer
                transfer = data.transfer.val
                transfer_dim = data.transfer.dim
                # Bitrate
                bitrate = data.bitrate.val
                bitrate_dim = data.bitrate.dim
                # Retr
                retr = data.retr.val
                # Cwnd
                cwnd = data.cwnd.val
                cwnd_dim = data.cwnd.dim
                # Publish data to Kafka
                if ENABLE_KAFKA_INTEGRATION:
                    publish_iperf_data_to_kafka(
                        bootstrap_servers=self.kafka_servers,
                        topic=TOPIC_IPERF,
                        _from=_from,
                        measure_id=measure_id,
                        generator_id=generator_id,
                        interval=interval,
                        transfer=transfer,
                        transfer_dim=transfer_dim,
                        bitrate=bitrate,
                        bitrate_dim=bitrate_dim,
                        retr=retr,
                        cwnd=cwnd,
                        cwnd_dim=cwnd_dim,
                    )
            status = commons_pb2.StatusCode.Value('STATUS_SUCCESS')
            return srv6pmServiceController_pb2.SendIperfDataResponse(
                status=status)


if ENABLE_GRPC_SERVER:
    def __start_grpc_server(grpc_ip=DEFAULT_GRPC_SERVER_IP,
                            grpc_port=DEFAULT_GRPC_SERVER_PORT,
                            secure=DEFAULT_SERVER_SECURE,
                            key=DEFAULT_SERVER_KEY,
                            certificate=DEFAULT_SERVER_CERTIFICATE):
        """Start gRPC on the controller

        Parameters
        ----------
        grpc_ip : str
            the IP address of the gRPC server
        grpc_port : int
            the port of the gRPC server
        secure : bool
            define whether to use SSL or not for the gRPC server
            (default is False)
        certificate : str
            the path of the server certificate required for the SSL
            (default is None)
        key : str
            the path of the server key required for the SSL
            (default is None)
        """

        # Setup gRPC server
        #
        # Create the server and add the handler
        grpc_server = grpc.server(futures.ThreadPoolExecutor())
        srv6pmServiceController_pb2_grpc \
            .add_SRv6PMControllerServicer_to_server(_SRv6PMService(), grpc_server)
        # If secure mode is enabled, we need to create a secure endpoint
        if secure:
            # Read key and certificate
            with open(key) as f:
                key = f.read()
            with open(certificate) as f:
                certificate = f.read()
            # Create server SSL credentials
            grpc_server_credentials = grpc.ssl_server_credentials(
                ((key, certificate,),)
            )
            # Create a secure endpoint
            grpc_server.add_secure_port(
                '[%s]:%s' % (grpc_ip, grpc_port),
                grpc_server_credentials
            )
        else:
            # Create an insecure endpoint
            grpc_server.add_insecure_port(
                '[%s]:%s' % (grpc_ip, grpc_port)
            )
        # Start the loop for gRPC
        logger.info('Listening gRPC')
        grpc_server.start()
        while True:
            time.sleep(5)
