#!/usr/bin/python

##########################################################################
# Copyright (C) 2020 Carmine Scarpitta
# (Consortium GARR and University of Rome "Tor Vergata")
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
# Control-Plane functionalities used for SRv6 Performance Monitoring
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
This module implements control-plane functionalities for SRv6 Performance
Monitoring.
'''

# pylint: disable=too-many-lines

# General imports
import json
import logging
import os
import sys
import time
from concurrent import futures

# gRPC dependencies
import grpc

# SRv6PM dependencies
import commons_pb2
import srv6pmCommons_pb2
import srv6pmReflector_pb2
import srv6pmSender_pb2
import srv6pmService_pb2_grpc
import srv6pmServiceController_pb2
import srv6pmServiceController_pb2_grpc
# Controller dependencies
from controller import srv6_utils, utils

# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)

# Read configuration parameters from the environment variables
#
# Kafka support (default: disabled)
ENABLE_KAFKA_INTEGRATION = os.getenv('ENABLE_KAFKA_INTEGRATION', 'false')
ENABLE_KAFKA_INTEGRATION = ENABLE_KAFKA_INTEGRATION.lower() == 'true'
# gRPC server (default: disabled)
# In the standard operation mode, the SDN Controller acts as gRPC client
# sending requests to the gRPC servers executed on the nodes. In some project,
# we need a gRPC server executed on the Controller and ready to accepts
# commands sent by the nodes
ENABLE_GRPC_SERVER = os.getenv('ENABLE_GRPC_SERVER', 'false')
ENABLE_GRPC_SERVER = ENABLE_GRPC_SERVER.lower() == 'true'
# Comma-separated Kafka servers (default: "kafka:9092")
KAFKA_SERVERS = os.getenv('KAFKA_SERVERS', 'kafka:9092').split(',')

# Kafka depedencies
if ENABLE_KAFKA_INTEGRATION:
    try:
        from kafka import KafkaProducer
        from kafka.errors import KafkaError
    except ImportError:
        logger.fatal('ENABLE_KAFKA_INTEGRATION is set in the configuration.')
        logger.fatal('kafka-python is required to run')
        logger.fatal('kafka-python not found.')
        sys.exit(-2)


# Global variables definition
#
#
# Default parameters for SRv6 controller
#
# Default IP address of the gRPC server
DEFAULT_GRPC_SERVER_IP = '::'
# Default port of the gRPC server
DEFAULT_GRPC_SERVER_PORT = 12345
# Define whether to use SSL or not for the gRPC server
DEFAULT_SERVER_SECURE = False
# SSL certificate of the gRPC server
DEFAULT_SERVER_CERTIFICATE = 'server_cert.pem'
# SSL key of the gRPC server
DEFAULT_SERVER_KEY = 'server_cert.pem'

# Kafka topic for TWAMP data
TOPIC_TWAMP = 'twamp'
# Kafka topic for iperf data
TOPIC_IPERF = 'iperf'


def publish_to_kafka(bootstrap_servers, topic, measure_id, interval,
                     timestamp, fw_color, rv_color, sender_seq_num,
                     reflector_seq_num, sender_tx_counter, sender_rx_counter,
                     reflector_tx_counter, reflector_rx_counter):
    '''
    Publish the measurement data to a Kafka topic.

    :param bootstrap_servers: Kafka servers ("host[:port]" string (or list of
                              "host[:port]" strings).
    :type bootstrap_servers: str or list
    :param topic: Kafka topic.
    :type topic: str
    :param measure_id: An identifier for the measure.
    :type measure_id: int
    :param interval: The duration of the interval.
    :type interval: int
    :param timestamp: The timestamp of the measurement.
    :type timestamp: str
    :param fw_color: Color for the forward path.
    :type fw_color: int
    :param rv_color: Color for the reverse path.
    :type rv_color: int
    :param sender_seq_num: Sequence number of the sender (for the forward
                           path).
    :type sender_seq_num: int
    :param reflector_seq_num: Sequence number of the reflector (for the
                              reverse path).
    :type reflector_seq_num: int
    :param sender_tx_counter: Transmission counter of the sender (for the
                              forward path).
    :type sender_tx_counter: int
    :param sender_rx_counter: Reception counter of the sender (for the
                              reverse path)
    :type sender_rx_counter: int
    :param reflector_tx_counter: Transmission counter of the reflector (for the
                                 reverse path).
    :type reflector_tx_counter: int
    :param reflector_rx_counter: Reception counter of the reflector (for the
                                 forward path).
    :type reflector_rx_counter: int
    :return: Resolves to RecordMetadata.
    :rtype: kafka.FutureRecordMetadata
    :raises KafkaTimeoutError: If unable to fetch topic metadata, or unable to
                               obtain memory buffer prior to configured
                               max_block_ms.
    '''
    # pylint: disable=too-many-arguments, too-many-locals
    #
    # Init producer and result
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
            value={
                'measure_id': measure_id,
                'interval': interval,
                'timestamp': timestamp,
                'fw_color': fw_color,
                'rv_color': rv_color,
                'sender_seq_num': sender_seq_num,
                'reflector_seq_num': reflector_seq_num,
                'sender_tx_counter': sender_tx_counter,
                'sender_rx_counter': sender_rx_counter,
                'reflector_tx_counter': reflector_tx_counter,
                'reflector_rx_counter': reflector_rx_counter}
        )
    except KafkaError as err:
        logger.error('Cannot publish data to Kafka: %s', err)
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
    '''
    Publish IPERF data to a Kafka topic.

    :param bootstrap_servers: Kafka servers ("host[:port]" string (or list of
                              "host[:port]" strings).
    :type bootstrap_servers: str or list
    :param topic: Kafka topic.
    :type topic: str
    :param _from: A string representing the originator of the iperf data
                  (e.g "client")
    :type _from: str
    :param measure_id: An identifier for the measure.
    :type measure_id: int
    :param generator_id: Generator ID.
    :type generator_id: int
    :param interval: The duration of the interval.
    :type interval: int
    :param transfer: Transferred data (value).
    :type transfer: int
    :param transfer_dim: Transferred data (unit of measurement).
    :type transfer_dim: str
    :param bitrate: Bitrate (value).
    :type bitrate: int
    :param bitrate_dim: Bitrate (unit of measurement).
    :type bitrate_dim: str
    :param retr: Number of TCP segments retransmitted.
    :type retr: int
    :param cwnd: Congestion window (value)
    :type cwnd: int
    :param cwnd_dim: Congestion window (unit of measurement).
    :type cwnd_dim: str
    :return: Resolves to RecordMetadata.
    :rtype: kafka.FutureRecordMetadata
    :raises KafkaTimeoutError: If unable to fetch topic metadata, or unable to
                               obtain memory buffer prior to configured
                               max_block_ms.
    '''
    # pylint: disable=too-many-arguments
    #
    # Init producer and result
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
                   'cwnd_dim': cwnd_dim}
        )
    except KafkaError as err:
        logger.error('Cannot publish data to Kafka: %s', err)
    finally:
        # Close the producer
        if producer is not None:
            producer.close()
    # Return result
    return result


def start_experiment_sender(channel, sidlist, rev_sidlist,
                            measurement_protocol,
                            measurement_type, authentication_mode,
                            authentication_key, timestamp_format,
                            delay_measurement_mode, padding_mbz,
                            loss_measurement_mode):
    '''
    RPC used to start an experiment on the sender.

    :param channel: A gRPC channel to the sender.
    :type channel: class: `grpc._channel.Channel`
    :param sidlist: The SID list of the path to be tested with the experiment.
    :type sidlist: list
    :param rev_sidlist: The SID list of the reverse path to be tested with the
                        experiment.
    :type rev_sidlist: list
    :param measurement_protocol: The measurement protocol (i.e. TWAMP or
                                 STAMP)
    :type measurement_protocol: str
    :param measurement_type: The measurement type (i.e. delay or loss)
    :type measurement_type: str
    :param authentication_mode: The authentication mode (i.e. HMAC_SHA_256)
    :type authentication_mode: str
    :param authentication_key: The authentication key
    :type authentication_key: str
    :param timestamp_format: The Timestamp Format (i.e. PTPv2 or NTP)
    :type timestamp_format: str
    :param delay_measurement_mode: Delay measurement mode (i.e. one-way,
                                   two-way or loopback mode)
    :type delay_measurement_mode: str
    :param padding_mbz: The padding size
    :type padding_mbz: int
    :param loss_measurement_mode: The loss measurement mode (i.e. Inferred
                                  or Direct mode)
    :type loss_measurement_mode: str
    '''
    # pylint: disable=too-many-arguments, too-many-return-statements
    #
    # ########################################################################
    # Convert string args to int
    #
    # Measurement Protocol
    if isinstance(measurement_protocol, str):
        try:
            measurement_protocol = \
                srv6pmCommons_pb2.MeasurementProtocol.Value(
                    measurement_protocol)
        except ValueError:
            logger.error('Invalid Measurement protocol: %s',
                         measurement_protocol)
            return None
    # Measurement Type
    if isinstance(measurement_type, str):
        try:
            measurement_type = \
                srv6pmCommons_pb2.MeasurementType.Value(measurement_type)
        except ValueError:
            logger.error('Invalid Measurement Type: %s', measurement_type)
            return None
    # Authentication Mode
    if isinstance(authentication_mode, str):
        try:
            authentication_mode = \
                srv6pmCommons_pb2.AuthenticationMode.Value(authentication_mode)
        except ValueError:
            logger.error('Invalid  Authentication Mode: %s',
                         authentication_mode)
            return None
    # Timestamp Format
    if isinstance(timestamp_format, str):
        try:
            timestamp_format = \
                srv6pmCommons_pb2.TimestampFormat.Value(timestamp_format)
        except ValueError:
            logger.error('Invalid Timestamp Format: %s', timestamp_format)
            return None
    # Delay Measurement Mode
    if isinstance(delay_measurement_mode, str):
        try:
            delay_measurement_mode = \
                srv6pmCommons_pb2.MeasurementDelayMode.Value(
                    delay_measurement_mode)
        except ValueError:
            logger.error('Invalid Delay Measurement Mode: %s',
                         delay_measurement_mode)
            return None
    # Loss Measurement Mode
    if isinstance(loss_measurement_mode, str):
        try:
            loss_measurement_mode = \
                srv6pmCommons_pb2.MeasurementLossMode.Value(
                    loss_measurement_mode)
        except ValueError:
            logger.error('Invalid Loss Measurement Mode: %s',
                         loss_measurement_mode)
            return None
    # ########################################################################
    # Get the reference of the stub
    stub = srv6pmService_pb2_grpc.SRv6PMStub(channel)
    # Create the request
    request = srv6pmSender_pb2.StartExperimentSenderRequest()
    # Set the SID list
    request.sdlist = '/'.join(sidlist)
    # Set the reverse SID list
    request.sdlistreverse = '/'.join(rev_sidlist)
    # ########################################################################
    # Set the sender options
    #
    # Set the measurement protocol
    (request.sender_options.measurement_protocol) = \
        measurement_protocol                # pylint: disable=no-member
    # Set the authentication mode
    request.sender_options.authentication_mode = \
        authentication_mode                 # pylint: disable=no-member
    # Set the authentication key
    request.sender_options.authentication_key = \
        str(authentication_key)             # pylint: disable=no-member
    # Set the measurement type
    request.sender_options.measurement_type = \
        measurement_type                    # pylint: disable=no-member
    # Set the timestamp format
    request.sender_options.timestamp_format = \
        timestamp_format                    # pylint: disable=no-member
    # Set the measurement delay mode
    request.sender_options.measurement_delay_mode = \
        delay_measurement_mode              # pylint: disable=no-member
    # Set the padding
    request.sender_options.padding_mbz = \
        int(padding_mbz)                    # pylint: disable=no-member
    # Set the measurement loss mode
    request.sender_options.measurement_loss_mode = \
        loss_measurement_mode               # pylint: disable=no-member
    # ########################################################################
    # Start the experiment on the sender and return the response
    return stub.startExperimentSender(request=request)


def stop_experiment_sender(channel, sidlist):
    '''
    RPC used to stop an experiment on the sender.

    :param channel: A gRPC channel to the sender.
    :type channel: class: `grpc._channel.Channel`
    :param sidlist: The SID list of the path under test.
    :type sidlist: list
    '''
    # Get the reference of the stub
    stub = srv6pmService_pb2_grpc.SRv6PMStub(channel)
    # Create the request message
    request = srv6pmCommons_pb2.StopExperimentRequest()
    # Set the SID list
    request.sdlist = '/'.join(sidlist)
    # Stop the experiment on the sender and return the response
    return stub.stopExperimentSender(request=request)


def retrieve_experiment_results_sender(channel, sidlist):
    '''
    RPC used to get the results of a running experiment.

    :param channel: A gRPC channel to the sender.
    :type channel: class: `grpc._channel.Channel`
    :param sidlist: The SID list of the path under test.
    :type sidlist: list
    '''
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
    '''
    RPC used to set the configuration on a node (sender or reflector).

    :param channel: A gRPC channel to the node.
    :type channel: class: `grpc._channel.Channel`
    :param send_udp_port: UDP port of the sender.
    :type send_udp_port: int
    :param send_udp_port: UDP port of the reflector.
    :type send_udp_port: int
    :param interval_duration: The duration of the interval.
    :type interval_duration: int
    :param delay_margin: The delay margin.
    :type delay_margin: int
    :param number_of_color: The number of the color.
    :type number_of_color: int
    :param pm_driver: The driver to use for the experiments (i.e. eBPF or
                      IPSet).
    '''
    # pylint: disable=too-many-arguments
    #
    # ########################################################################
    # Convert string args to int
    #
    # PM Driver
    if isinstance(pm_driver, str):
        try:
            pm_driver = srv6pmCommons_pb2.PMDriver.Value(pm_driver)
        except ValueError:
            logger.error('Invalid PM Driver: %s', pm_driver)
            return None
    # ########################################################################
    # Get the reference of the stub
    stub = srv6pmService_pb2_grpc.SRv6PMStub(channel)
    # Create the request message
    request = srv6pmCommons_pb2.Configuration()
    # Set the destination UDP port of the sender
    request.ss_udp_port = int(send_udp_port)
    # Set the destination UDP port of the reflector
    request.refl_udp_port = int(refl_udp_port)
    # ########################################################################
    # Set the color options
    #
    # Set the interval duration
    request.color_options.interval_duration = \
        int(interval_duration)                # pylint: disable=no-member
    # Set the delay margin
    request.color_options.delay_margin = \
        int(delay_margin)                     # pylint: disable=no-member
    # Set the number of color
    request.color_options.numbers_of_color = \
        int(number_of_color)                  # pylint: disable=no-member
    # ########################################################################
    # Set driver
    request.pm_driver = pm_driver
    # ########################################################################
    # Start the experiment on the reflector and return the response
    return stub.setConfiguration(request=request)


def reset_node_configuration(channel):
    '''
    RPC used to clear the configuration on a node (sender or reflector).

    :param channel: A gRPC channel to the node.
    :type channel: class: `grpc._channel.Channel`
    '''
    # Get the reference of the stub
    stub = srv6pmService_pb2_grpc.SRv6PMStub(channel)
    # Create the request message
    request = srv6pmCommons_pb2.Configuration()
    # Start the experiment on the reflector and return the response
    return stub.resetConfiguration(request=request)


def start_experiment_reflector(channel, sidlist, rev_sidlist,
                               measurement_protocol, measurement_type,
                               authentication_mode, authentication_key,
                               loss_measurement_mode):
    '''
    RPC used to start an experiment on the reflector.

    :param channel: A gRPC channel to the reflector.
    :type channel: class: `grpc._channel.Channel`
    :param sidlist: The SID list of the path to be tested with the experiment.
    :type sidlist: list
    :param rev_sidlist: The SID list of the reverse path to be tested with the
                        experiment.
    :type rev_sidlist: list
    :param measurement_protocol: The measurement protocol (i.e. TWAMP or
                                 STAMP)
    :type measurement_protocol: str
    :param measurement_type: The measurement type (i.e. delay or loss)
    :type measurement_type: str
    :param authentication_mode: The authentication mode (i.e. HMAC_SHA_256)
    :type authentication_mode: str
    :param authentication_key: The authentication key
    :type authentication_key: str
    :param loss_measurement_mode: The loss measurement mode (i.e. Inferred
                                  or Direct mode)
    :type loss_measurement_mode: str
    '''
    # pylint: disable=too-many-arguments
    #
    # ########################################################################
    # Convert string args to int
    #
    # Measurement Protocol
    if isinstance(measurement_protocol, str):
        try:
            measurement_protocol = \
                srv6pmCommons_pb2.MeasurementProtocol.Value(
                    measurement_protocol)
        except ValueError:
            logger.error('Invalid Measurement protocol: %s',
                         measurement_protocol)
            return None
    # Measurement Type
    if isinstance(measurement_type, str):
        try:
            measurement_type = \
                srv6pmCommons_pb2.MeasurementType.Value(measurement_type)
        except ValueError:
            logger.error('Invalid Measurement Type: %s', measurement_type)
            return None
    # Authentication Mode
    if isinstance(authentication_mode, str):
        try:
            authentication_mode = \
                srv6pmCommons_pb2.AuthenticationMode.Value(authentication_mode)
        except ValueError:
            logger.error('Invalid  Authentication Mode: %s',
                         authentication_mode)
            return None
    # Loss Measurement Mode
    if isinstance(loss_measurement_mode, str):
        try:
            loss_measurement_mode = \
                srv6pmCommons_pb2.MeasurementLossMode.Value(
                    loss_measurement_mode)
        except ValueError:
            logger.error('Invalid Loss Measurement Mode: %s',
                         loss_measurement_mode)
            return None
    # ########################################################################
    # Get the reference of the stub
    stub = srv6pmService_pb2_grpc.SRv6PMStub(channel)
    # Create the request message
    request = srv6pmReflector_pb2.StartExperimentReflectorRequest()
    # Set the SID list
    request.sdlist = '/'.join(sidlist)
    # Set the reverse SID list
    request.sdlistreverse = '/'.join(rev_sidlist)
    # ########################################################################
    # Set the reflector options
    #
    # Set the measurement protocol
    request.reflector_options.measurement_protocol = \
        measurement_protocol                    # pylint: disable=no-member
    # Set the authentication mode
    request.reflector_options.authentication_mode = \
        authentication_mode                     # pylint: disable=no-member
    # Set the authentication key
    request.reflector_options.authentication_key = \
        str(authentication_key)                 # pylint: disable=no-member
    # Set the measurement type
    request.reflector_options.measurement_type = \
        measurement_type                        # pylint: disable=no-member
    # Set the measurement loss mode
    request.reflector_options.measurement_loss_mode = \
        loss_measurement_mode                   # pylint: disable=no-member
    # ########################################################################
    # Start the experiment on the reflector and return the response
    return stub.startExperimentReflector(request=request)


def stop_experiment_reflector(channel, sidlist):
    '''
    RPC used to stop an experiment on the reflector.

    :param channel: A gRPC channel to the reflector.
    :type channel: class: `grpc._channel.Channel`
    :param sidlist: The SID list of the path under test.
    :type sidlist: list
    '''
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
                        measurement_protocol, measurement_type,
                        authentication_mode, authentication_key,
                        timestamp_format, delay_measurement_mode,
                        padding_mbz, loss_measurement_mode):
    '''
    Start the measurement process on reflector and sender.

    :param measure_id: Identifier for the experiment
    :type measure_id: int
    :param sender_channel: The gRPC Channel to the sender node
    :type sender_channel: class: `grpc._channel.Channel`
    :param reflector_channel: The gRPC Channel to the reflector node
    :type reflector_channel: class: `grpc._channel.Channel`
    :param send_refl_sidlist: The SID list to be used for the path
                              sender->reflector
    :type send_refl_sidlist: list
    :param refl_send_sidlist: The SID list to be used for the path
                              reflector->sender
    :type refl_send_sidlist: list
    :param measurement_protocol: The measurement protocol (i.e. TWAMP or
                                 STAMP)
    :type measurement_protocol: str
    :param measurement_type: The measurement type (i.e. delay or loss)
    :type measurement_type: str
    :param authentication_mode: The authentication mode (i.e. HMAC_SHA_256)
    :type authentication_mode: str
    :param authentication_key: The authentication key
    :type authentication_key: str
    :param timestamp_format: The Timestamp Format (i.e. PTPv2 or NTP)
    :type timestamp_format: str
    :param delay_measurement_mode: Delay measurement mode (i.e. one-way,
                                   two-way or loopback mode)
    :type delay_measurement_mode: str
    :param padding_mbz: The padding size
    :type padding_mbz: int
    :param loss_measurement_mode: The loss measurement mode (i.e. Inferred
                                  or Direct mode)
    :type loss_measurement_mode: str
    '''
    # pylint: disable=too-many-arguments, unused-argument
    #
    print("\n************** Start Measurement **************\n")
    # Start the experiment on the reflector
    refl_res = start_experiment_reflector(
        channel=reflector_channel,
        sidlist=send_refl_sidlist,
        rev_sidlist=refl_send_sidlist,
        measurement_protocol=measurement_protocol,
        measurement_type=measurement_type,
        authentication_mode=authentication_mode,
        authentication_key=authentication_key,
        loss_measurement_mode=loss_measurement_mode,
    )
    # Pretty print status code
    utils.print_status_message(
        status_code=refl_res.status,
        success_msg='Started Measure Reflector',
        failure_msg='Error in start_experiment_reflector()'
    )
    # Check for errors
    if refl_res is None:
        return commons_pb2.STATUS_INTERNAL_ERROR
    if refl_res.status != commons_pb2.STATUS_SUCCESS:
        return refl_res.status
    # Start the experiment on the sender
    sender_res = start_experiment_sender(
        channel=sender_channel,
        sidlist=send_refl_sidlist,
        rev_sidlist=refl_send_sidlist,
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
    utils.print_status_message(
        status_code=sender_res.status,
        success_msg='Started Measure Sender',
        failure_msg='Error in start_experiment_sender()'
    )
    # Check for errors
    if sender_res is None:
        return commons_pb2.STATUS_INTERNAL_ERROR
    if sender_res.status != commons_pb2.STATUS_SUCCESS:
        return sender_res.status
    # Success
    return commons_pb2.STATUS_SUCCESS


def __get_measurement_results(sender_channel, reflector_channel,
                              send_refl_sidlist, refl_send_sidlist):
    '''
    Get the results of a measurement process.

    :param sender_channel: The gRPC Channel to the sender node
    :type sender_channel: class: `grpc._channel.Channel`
    :param reflector_channel: The gRPC Channel to the reflector node
    :type reflector_channel: class: `grpc._channel.Channel`
    :param send_refl_sidlist: The SID list used for sender->reflector path
    :type send_refl_sidlist: list
    :param refl_send_sidlist: The SID list used for reflector->sender path
    :type refl_send_sidlist: list
    '''
    # pylint: disable=unused-argument
    #
    # Retrieve the results of the experiment
    print("\n************** Get Measurement Data **************\n")
    # Retrieve the results from the sender
    sender_res = retrieve_experiment_results_sender(
        channel=sender_channel,
        sidlist=send_refl_sidlist
    )
    # Pretty print status code
    utils.print_status_message(
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
    '''
    Stop a measurement process on reflector and sender.

    :param sender_channel: The gRPC Channel to the sender node
    :type sender_channel: class: `grpc._channel.Channel`
    :param reflector_channel: The gRPC Channel to the reflector node
    :type reflector_channel: class: `grpc._channel.Channel`
    :param send_refl_sidlist: The SID list used for the path
                              sender->reflector
    :type send_refl_sidlist: list
    :param refl_send_sidlist: The SID list used for the path
                              reflector->sender
    :type refl_send_sidlist: list
    '''
    #
    print("\n************** Stop Measurement **************\n")
    # Stop the experiment on the sender
    sender_res = stop_experiment_sender(
        channel=sender_channel,
        sidlist=send_refl_sidlist
    )
    # Pretty print status code
    utils.print_status_message(
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
    utils.print_status_message(
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
    '''
    Set the configuration

    :param sender_channel: The gRPC Channel to the sender
    :type sender_channel: class: `grpc._channel.Channel`
    :param reflector_channel: The gRPC Channel to the reflector node
    :type reflector_channel: class: `grpc._channel.Channel`
    :param send_dst_udp_port: The destination UDP port used by the sender
    :type send_dst_udp_port: int
    :param refl_dst_udp_port: The destination UDP port used by the reflector
    :type refl_dst_udp_port: int
    :param interval_duration: The duration of the interval
    :type interval_duration: int
    :param delay_margin: The delay margin
    :type delay_margin: int
    :param number_of_color: The number of the color
    :type number_of_color: int
    '''
    # pylint: disable=too-many-arguments
    #
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
    '''
    Reset the configuration

    :param sender_channel: The gRPC Channel to the sender node
    :type sender_channel: class: `grpc._channel.Channel`
    :param reflector_channel: The gRPC Channel to the reflector node
    :type reflector_channel: class: `grpc._channel.Channel`
    :param send_dst_udp_port: The destination UDP port used by the sender
    :type send_dst_udp_port: int
    :param refl_dst_udp_port: The destination UDP port used by the reflector
    :type refl_dst_udp_port: int
    :param interval_duration: The duration of the interval
    :type interval_duration: int
    :param delay_margin: The delay margin
    :type delay_margin: int
    :param number_of_color: The number of the color
    :type number_of_color: int
    '''
    #
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
                     measurement_protocol, measurement_type,
                     authentication_mode, authentication_key,
                     timestamp_format, delay_measurement_mode,
                     padding_mbz, loss_measurement_mode, measure_id=None,
                     send_refl_localseg=None, refl_send_localseg=None,
                     force=False):
    '''
    Start an experiment.

    :param sender_channel: The gRPC Channel to the sender node
    :type sender_channel: class: `grpc._channel.Channel`
    :param reflector_channel: The gRPC Channel to the reflector node
    :type reflector_channel: class: `grpc._channel.Channel`
    :param send_refl_dest: The destination of the SRv6 path
                           sender->reflector
    :type send_refl_dest: str
    :param refl_send_dest: The destination of the SRv6 path
                           reflector->sender
    :type refl_send_dest: str
    :param send_refl_sidlist: The SID list to be used for the path
                              sender->reflector
    :type send_refl_sidlist:  list
    :param refl_send_sidlist: The SID list to be used for the path
                              reflector->sender
    :type refl_send_sidlist: list
    :param measurement_protocol: The measurement protocol (i.e. TWAMP
                                 or STAMP)
    :type measurement_protocol: str
    :param measurement_type: The measurement type (i.e. delay or loss)
    :type measurement_type: str
    :param authentication_mode: The authentication mode (i.e. HMAC_SHA_256)
    :type authentication_mode: str
    :param authentication_key: The authentication key
    :type authentication_key: str
    :param timestamp_format: The Timestamp Format (i.e. PTPv2 or NTP)
    :type timestamp_format: str
    :param delay_measurement_mode: Delay measurement mode (i.e. one-way,
                                   two-way or loopback mode)
    :type delay_measurement_mode: str
    :param padding_mbz: The padding size
    :type padding_mbz: int
    :param loss_measurement_mode: The loss measurement mode (i.e. Inferred
                                  or Direct mode)
    :type loss_measurement_mode: str
    :param measure_id: Identifier for the experiment (default is None).
                        automatically generated.
    :type measure_id: int, optional
    :param send_refl_localseg: The local segment associated to the End.DT6
                               (decap) function for the path
                               sender->reflector (default is None).
                               If the argument 'send_localseg' isn't passed
                               in, the seg6local End.DT6 route is not created.
    :type send_refl_localseg: str, optional
    :param refl_send_localseg: The local segment associated to the End.DT6
                               (decap) function for the path
                               reflector->sender (default is None).
                               If the argument 'send_localseg' isn't passed
                               in, the seg6local End.DT6 route is not created.
    :type refl_send_localseg: str, optional
    :param force: If set, force the controller to start an experiment if a
                  SRv6 path for the destination already exists. The old SRv6
                  path is replaced with the new one (default is False).
    :type force: bool, optional
    '''
    # pylint: disable=too-many-arguments, too-many-locals
    #
    # If the force flag is set and SRv6 path already exists, remove
    # the old path before creating the new one
    if force:
        res = srv6_utils.destroy_srv6_tunnel(
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
    res = srv6_utils.create_srv6_tunnel(
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
    '''
    Get the results of an experiment.

    :param sender_channel: The gRPC Channel to the sender node
    :type sender_channel: class: `grpc._channel.Channel`
    :param reflector_channel: The gRPC Channel to the reflector node
    :type reflector_channel: class: `grpc._channel.Channel`
    :param send_refl_sidlist: The SID list to be used for the path
                              sender->reflector
    :type send_refl_sidlist: list
    :param refl_send_sidlist: The SID list to be used for the path
                              reflector->sender
    :type refl_send_sidlist: list
    :param kafka_servers: IP:port of Kafka server
    :type kafka_servers: str
    '''
    # pylint: disable=too-many-arguments, too-many-locals
    #
    # Get the results
    results = __get_measurement_results(
        sender_channel=sender_channel,
        reflector_channel=reflector_channel,
        send_refl_sidlist=send_refl_sidlist,
        refl_send_sidlist=refl_send_sidlist
    )
    if results is None:
        print('No measurement data available')
        return None
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
    '''
    Stop a running experiment.

    :param sender_channel: The gRPC Channel to the sender node
    :type sender_channel: class: `grpc._channel.Channel`
    :param reflector_channel: The gRPC Channel to the reflector node
    :type reflector_channel: class: `grpc._channel.Channel`
    :param send_refl_dest: The destination of the SRv6 path
                           sender->reflector
    :type send_refl_dest: str
    :param refl_send_dest: The destination of the SRv6 path
                           reflector->sender
    :type refl_send_dest: str
    :param send_refl_sidlist: The SID list used for the path
                              sender->reflector
    :type send_refl_sidlist: list
    :param refl_send_sidlist: The SID list used for the path
                              reflector->sender
    :type refl_send_sidlist: list
    :param send_refl_localseg: The local segment associated to the End.DT6
                               (decap) function for the path sender->reflector
                               (default is None). If the argument
                               'send_localseg' isn't passed in, the seg6local
                               End.DT6 route is not removed.
    :type send_refl_localseg: str, optional
    :param refl_send_localseg: The local segment associated to the End.DT6
                              (decap) function for the path reflector->sender
                              (default is None). If the argument
                              'send_localseg' isn't passed in, the seg6local
                              End.DT6 route is not removed.
    :type refl_send_localseg: str, optional
    '''
    # pylint: disable=too-many-arguments
    #
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
    res = srv6_utils.destroy_srv6_tunnel(
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
        '''
        Private class implementing methods exposed by the gRPC server
        '''

        def __init__(self, kafka_servers=KAFKA_SERVERS):
            self.kafka_servers = kafka_servers

        def SendMeasurementData(self, request, context):
            '''
            RPC used to send measurement data to the controller
            '''
            # pylint: disable=too-many-locals
            #
            logger.debug('Measurement data received: %s', request)
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
            '''
            RPC used to send iperf data to the controller
            '''
            #
            # pylint: disable=too-many-locals
            #
            logger.debug('Iperf data received: %s', request)
            # Extract data from the request
            for data in request.iperf_data:
                # From client/server
                _from = data._from      # pylint: disable=protected-access
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


def __start_grpc_server(grpc_ip=DEFAULT_GRPC_SERVER_IP,
                        grpc_port=DEFAULT_GRPC_SERVER_PORT,
                        secure=DEFAULT_SERVER_SECURE,
                        key=DEFAULT_SERVER_KEY,
                        certificate=DEFAULT_SERVER_CERTIFICATE):
    '''
    Start gRPC server on the controller.

    :param grpc_ip: The IP address of the gRPC server.
    :type grpc_ip: str
    :param grpc_port: The port of the gRPC server.
    :type grpc_port: int
    :param secure: define whether to use SSL or not for the gRPC server
                    (default is False).
    :type secure: bool
    :param certificate: The path of the server certificate required
                        for the SSL (default is None).
    :type certificate: str
    :param key: the path of the server key required for the SSL
                (default is None).
    :type key: str
    :raises controller.utils.InvalidArgumentError: If gRPC server is disabled
                                                   in the configuration.
    '''
    # pylint: disable=too-many-arguments
    #
    # To start a gRPC server on the Controller, ENABLE_GRPC_SERVER must be
    # True
    if not ENABLE_GRPC_SERVER:
        logger.error('gRPC server is disabled. Check your configuration.')
        raise utils.InvalidArgumentError
    # ########################################################################
    # Setup gRPC server
    #
    # Create the server and add the handler
    grpc_server = grpc.server(futures.ThreadPoolExecutor())
    (srv6pmServiceController_pb2_grpc
        .add_SRv6PMControllerServicer_to_server(_SRv6PMService(),
                                                grpc_server))
    # If secure mode is enabled, we need to create a secure endpoint
    if secure:
        # Read key and certificate
        with open(key) as key_file:
            key = key_file.read()
        with open(certificate) as certificate_file:
            certificate = certificate_file.read()
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
    # ###########################################################################
    # Start the loop for gRPC
    logger.info('Listening gRPC')
    grpc_server.start()
    while True:
        time.sleep(5)
