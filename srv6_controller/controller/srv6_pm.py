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
from concurrent import futures
from threading import Thread
import grpc
import logging
import time

# Controller dependencies
import utils
import srv6_utils

# SRv6PM dependencies
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


def __init__(self, grpc_server_ip, grpc_server_port, grpc_client_port,
             grpc_client_secure=False, grpc_client_certificate=None,
             grpc_server_secure=False, grpc_server_certificate=None,
             grpc_server_key=None, debug=False):
    """
    Parameters
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
        define whether to enable debug mode or not (default is False)
    """

    logger.info('Initializing SRv6 controller')
    # Port of the gRPC client
    self.grpc_client_port = grpc_client_port
    # Measure ID
    self.measure_id = -1
    # gRPC secure mode
    self.grpc_client_secure = grpc_client_secure
    # SSL certificate of the root CA required for gRPC secure mode
    self.grpc_client_certificate = grpc_client_certificate
    # Debug mode
    self.debug = debug
    # Setup properly the logger
    if self.debug:
        logger.setLevel(level=logging.DEBUG)
    else:
        logger.setLevel(level=logging.INFO)
    # Mapping IP address to gRPC channels
    self.grpc_channels = dict()
    # Start the gRPC server
    # This is a blocking operation, so we need to execute it
    # in a separated thread
    kwargs = {
        'grpc_ip': grpc_server_ip,
        'grpc_port': grpc_server_port,
        'secure': grpc_server_secure,
        'key': grpc_server_key,
        'certificate': grpc_server_certificate
    }
    Thread(target=self.__start_grpc_server, kwargs=kwargs).start()
    time.sleep(1)


# Human-readable gRPC return status
status_code_to_str = {
    srv6pmCommons_pb2.STATUS_SUCCESS: 'Success',
    srv6pmCommons_pb2.STATUS_OPERATION_NOT_SUPPORTED: ('Operation '
                                                       'not supported'),
    srv6pmCommons_pb2.STATUS_BAD_REQUEST: 'Bad request',
    srv6pmCommons_pb2.STATUS_INTERNAL_ERROR: 'Internal error',
    srv6pmCommons_pb2.STATUS_INVALID_GRPC_REQUEST: 'Invalid gRPC request',
    srv6pmCommons_pb2.STATUS_FILE_EXISTS: 'An entity already exists',
    srv6pmCommons_pb2.STATUS_NO_SUCH_PROCESS: 'Entity not found',
    srv6pmCommons_pb2.STATUS_INVALID_ACTION: 'Invalid seg6local action',
    srv6pmCommons_pb2.STATUS_GRPC_SERVICE_UNAVAILABLE: ('gRPC service not '
                                                        'available'),
    srv6pmCommons_pb2.STATUS_GRPC_UNAUTHORIZED: 'Unauthorized'
}


def __print_status_message(status_code, success_msg, failure_msg):
    """Print success or failure message depending of the status code
        returned by a gRPC operation.

    Parameters
    ----------
    status_code : int
        The status code returned by the gRPC operation
    success_msg : str
        The message to print in case of success
    failure_msg : str
        The message to print in case of error
    """

    if status_code == srv6pmCommons_pb2.STATUS_SUCCESS:
        # Success
        print('%s (status code %s - %s)'
              % (success_msg, status_code,
                 status_code_to_str.get(status_code, 'Unknown')))
    else:
        # Error
        print('%s (status code %s - %s)'
              % (failure_msg, status_code,
                 status_code_to_str.get(status_code, 'Unknown')))


def start_experiment_sender(channel, sidlist, rev_sidlist,
                            in_interfaces, out_interfaces,
                            measurement_protocol, send_udp_port, refl_udp_port,
                            measurement_type, authentication_mode,
                            authentication_key, timestamp_format,
                            delay_measurement_mode, padding_mbz,
                            loss_measurement_mode, interval_duration,
                            delay_margin, number_of_color):
    # Get the reference of the stub
    stub = srv6pmService_pb2_grpc.SRv6PMStub(channel)
    # Create the request
    request = srv6pmSender_pb2.StartExperimentSenderRequest()
    # Set the SID list
    request.sdlist = '/'.join(sidlist)
    # Set the reverse SID list
    request.sdlistreverse = '/'.join(rev_sidlist)
    # Set the incoming interfaces
    request.in_interfaces.extend(in_interfaces)
    # Set the outgoing interfaces
    request.in_interfaces.extend(out_interfaces)
    #
    # Set the sender options
    #
    # Set the measureemnt protocol
    request.sender_options.measurement_protocol = \
        srv6pmCommons_pb2.MeasurementProtocol.Value(measurement_protocol)
    # Set the destination UDP port of the sender
    request.sender_options.ss_udp_port = int(send_udp_port)
    # Set the destination UDP port of the reflector
    request.sender_options.refl_udp_port = int(refl_udp_port)
    # Set the authentication mode
    request.sender_options.authentication_mode = \
        srv6pmCommons_pb2.AuthenticationMode.Value(authentication_mode)
    # Set the authentication key
    request.sender_options.authentication_key = str(authentication_key)
    # Set the measurement type
    request.sender_options.measurement_type = \
        srv6pmCommons_pb2.MeasurementType.Value(measurement_type)
    # Set the timestamp format
    request.sender_options.timestamp_format = \
        srv6pmCommons_pb2.TimestampFormat.Value(timestamp_format)
    # Set the measurement delay mode
    request.sender_options.measurement_delay_mode = \
        srv6pmCommons_pb2.MeasurementDelayMode.Value(delay_measurement_mode)
    # Set the padding
    request.sender_options.padding_mbz = int(padding_mbz)
    # Set the measurement loss mode
    request.sender_options.measurement_loss_mode = \
        srv6pmCommons_pb2.MeasurementLossMode.Value(loss_measurement_mode)
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


def start_experiment_reflector(channel, sidlist, rev_sidlist,
                               in_interfaces, out_interfaces,
                               measurement_protocol, send_udp_port,
                               refl_udp_port, measurement_type,
                               authentication_mode, authentication_key,
                               loss_measurement_mode, interval_duration,
                               delay_margin, number_of_color):
    # Get the reference of the stub
    stub = srv6pmService_pb2_grpc.SRv6PMStub(channel)
    # Create the request message
    request = srv6pmReflector_pb2.StartExperimentReflectorRequest()
    # Set the SID list
    request.sdlist = '/'.join(sidlist)
    # Set the reverse SID list
    request.sdlistreverse = '/'.join(rev_sidlist)
    # Set the incoming interfaces
    request.in_interfaces.extend(in_interfaces)
    # Set the outgoing interfaces
    request.in_interfaces.extend(out_interfaces)
    #
    # Set the reflector options
    #
    # Set the measureemnt protocol
    request.reflector_options.measurement_protocol = \
        srv6pmCommons_pb2.MeasurementProtocol.Value(measurement_protocol)
    # Set the destination UDP port of the sender
    request.reflector_options.ss_udp_port = int(send_udp_port)
    # Set the destination UDP port of the reflector
    request.reflector_options.refl_udp_port = int(refl_udp_port)
    # Set the authentication mode
    request.reflector_options.authentication_mode = \
        srv6pmCommons_pb2.AuthenticationMode.Value(authentication_mode)
    # Set the authentication key
    request.reflector_options.authentication_key = str(authentication_key)
    # Set the measurement type
    request.reflector_options.measurement_type = \
        srv6pmCommons_pb2.MeasurementType.Value(measurement_type)
    # Set the measurement loss mode
    request.reflector_options.measurement_loss_mode = \
        srv6pmCommons_pb2.MeasurementLossMode.Value(loss_measurement_mode)
    #
    # Set the color options
    #
    # Set the interval duration
    request.color_options.interval_duration = int(interval_duration)
    # Set the delay margin
    request.color_options.delay_margin = int(delay_margin)
    # Set the number of color
    request.color_options.numbers_of_color = int(number_of_color)
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
                        send_in_interfaces, refl_in_interfaces,
                        send_out_interfaces, refl_out_interfaces,
                        measurement_protocol, send_dst_udp_port,
                        refl_dst_udp_port, measurement_type,
                        authentication_mode, authentication_key,
                        timestamp_format, delay_measurement_mode,
                        padding_mbz, loss_measurement_mode,
                        interval_duration, delay_margin, number_of_color):
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
    send_dst_udp_port : int
        The destination UDP port used by the sender
    refl_dst_udp_port : int
        The destination UDP port used by the reflector
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
    interval_duration : int
        The duration of the interval
    delay_margin : int
        The delay margin
    number_of_color : int
        The number of the color
    """

    print("\n************** Start Measurement **************\n")
    # Start the experiment on the reflector
    refl_res = start_experiment_reflector(
        channel=reflector_channel,
        sidlist=send_refl_sidlist,
        rev_sidlist=refl_send_sidlist,
        in_interfaces=refl_in_interfaces,
        out_interfaces=refl_out_interfaces,
        measurement_protocol=measurement_protocol,
        send_udp_port=send_dst_udp_port,
        refl_udp_port=refl_dst_udp_port,
        measurement_type=measurement_type,
        authentication_mode=authentication_mode,
        authentication_key=authentication_key,
        loss_measurement_mode=loss_measurement_mode,
        interval_duration=interval_duration,
        delay_margin=delay_margin,
        number_of_color=number_of_color
    )
    # Pretty print status code
    __print_status_message(
        status_code=refl_res.status,
        success_msg='Started Measure Reflector',
        failure_msg='Error in start_experiment_reflector()'
    )
    # Check for errors
    if refl_res.status != srv6pmCommons_pb2.STATUS_SUCCESS:
        return refl_res.status
    # Start the experiment on the sender
    sender_res = start_experiment_sender(
        channel=sender_channel,
        sidlist=send_refl_sidlist,
        rev_sidlist=refl_send_sidlist,
        in_interfaces=send_in_interfaces,
        out_interfaces=send_out_interfaces,
        measurement_protocol=measurement_protocol,
        send_udp_port=send_dst_udp_port,
        refl_udp_port=refl_dst_udp_port,
        measurement_type=measurement_type,
        authentication_mode=authentication_mode,
        authentication_key=authentication_key,
        timestamp_format=timestamp_format,
        delay_measurement_mode=delay_measurement_mode,
        padding_mbz=padding_mbz,
        loss_measurement_mode=loss_measurement_mode,
        interval_duration=interval_duration,
        delay_margin=delay_margin,
        number_of_color=number_of_color
    )
    # Pretty print status code
    __print_status_message(
        status_code=sender_res.status,
        success_msg='Started Measure Sender',
        failure_msg='Error in start_experiment_sender()'
    )
    # Check for errors
    if sender_res.status != srv6pmCommons_pb2.STATUS_SUCCESS:
        return sender_res.status
    # Success
    return srv6pmCommons_pb2.STATUS_SUCCESS


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
    __print_status_message(
        status_code=sender_res.status,
        success_msg='Received Data Sender',
        failure_msg='Error in retrieve_experiment_results_sender()'
    )
    # Collect the results
    res = None
    if sender_res.status == srv6pmCommons_pb2.STATUS_SUCCESS:
        res = list()
        for data in sender_res.measurement_data:
            res.append({
                'measure_id': data.meas_id,
                'interval': data.interval,
                'timestamp': data.timestamp,
                'color': data.fwColor,
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
    __print_status_message(
        status_code=sender_res.status,
        success_msg='Stopped Measure Sender',
        failure_msg='Error in stop_experiment_sender()'
    )
    # Check for errors
    if sender_res.status != srv6pmCommons_pb2.STATUS_SUCCESS:
        return sender_res.status
    # Stop the experiment on the reflector
    refl_res = stop_experiment_reflector(
        channel=reflector_channel,
        sidlist=refl_send_sidlist
    )
    # Pretty print status code
    __print_status_message(
        status_code=refl_res.status,
        success_msg='Stopped Measure Reflector',
        failure_msg='Error in stop_experiment_reflector()'
    )
    # Check for errors
    if refl_res.status != srv6pmCommons_pb2.STATUS_SUCCESS:
        return refl_res.status
    # Success
    return srv6pmCommons_pb2.STATUS_SUCCESS


def start_experiment(sender_channel, reflector_channel, send_refl_dest,
                     refl_send_dest, send_refl_sidlist, refl_send_sidlist,
                     send_in_interfaces, refl_in_interfaces,
                     send_out_interfaces, refl_out_interfaces,
                     measurement_protocol, send_dst_udp_port,
                     refl_dst_udp_port, measurement_type,
                     authentication_mode, authentication_key,
                     timestamp_format, delay_measurement_mode,
                     padding_mbz, loss_measurement_mode,
                     interval_duration, delay_margin,
                     number_of_color, measure_id=None,
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
    send_dst_udp_port : int
        The destination UDP port used by the sender
    refl_dst_udp_port : int
        The destination UDP port used by the reflector
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
    interval_duration : int
        The duration of the interval
    delay_margin : int
        The delay margin
    number_of_color : int
        The number of the color
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

    # Get a new measure ID, if it isn't passed in as argument
    if measure_id is None:
        self.measure_id += 1
        measure_id = self.measure_id
    # If the force flag is set and SRv6 path already exists, remove
    # the old path before creating the new one
    if force:
        res = srv6_utils.__destroy_srv6_tunnel(
            node_l=sender_channel,
            node_r=reflector_channel,
            dest_lr=send_refl_dest,
            dest_rl=refl_send_dest,
            localseg_lr=send_refl_localseg,
            localseg_rl=refl_send_localseg,
            ignore_errors=True
        )
        if res != srv6pmCommons_pb2.STATUS_SUCCESS:
            return res
    # Create a bidirectional SRv6 tunnel between the sender and the
    # reflector
    res = srv6_utils.__create_srv6_tunnel(
        node_l=sender_channel,
        node_r=reflector_channel,
        dest_lr=send_refl_dest,
        dest_rl=refl_send_dest,
        localseg_lr=send_refl_localseg,
        localseg_rl=refl_send_localseg,
        sidlist_lr=send_refl_sidlist,
        sidlist_rl=refl_send_sidlist
    )
    # Check for errors
    if res != srv6pmCommons_pb2.STATUS_SUCCESS:
        return res
    # Start measurement process
    res = __start_measurement(
        measure_id=measure_id,
        sender=sender_channel,
        reflector=reflector_channel,
        send_refl_sidlist=send_refl_sidlist,
        refl_send_sidlist=refl_send_sidlist,
        send_in_interfaces=send_in_interfaces,
        send_out_interfaces=send_out_interfaces,
        refl_in_interfaces=refl_in_interfaces,
        refl_out_interfaces=refl_out_interfaces,
        measurement_protocol=measurement_protocol,
        send_dst_udp_port=send_dst_udp_port,
        refl_dst_udp_port=refl_dst_udp_port,
        measurement_type=measurement_type,
        authentication_mode=authentication_mode,
        authentication_key=authentication_key,
        timestamp_format=timestamp_format,
        delay_measurement_mode=delay_measurement_mode,
        padding_mbz=padding_mbz,
        loss_measurement_mode=loss_measurement_mode,
        interval_duration=interval_duration,
        delay_margin=delay_margin,
        number_of_color=number_of_color
    )
    # Check for errors
    if res != srv6pmCommons_pb2.STATUS_SUCCESS:
        return res
    # Success
    return srv6pmCommons_pb2.STATUS_SUCCESS


def get_experiment_results(sender_channel, reflector_channel,
                           send_refl_sidlist, refl_send_sidlist):
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
    """

    # Get the results
    return __get_measurement_results(
        sender=sender_channel,
        reflector=reflector_channel,
        send_refl_sidlist=send_refl_sidlist,
        refl_send_sidlist=refl_send_sidlist
    )


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
        sender=sender_channel,
        reflector=reflector_channel,
        send_refl_sidlist=send_refl_sidlist,
        refl_send_sidlist=refl_send_sidlist
    )
    # Check for errors
    if res != srv6pmCommons_pb2.STATUS_SUCCESS:
        return res
    # Remove the SRv6 path
    res = srv6_utils.srv6__destroy_srv6_tunnel(
        node_l=sender_channel,
        node_r=reflector_channel,
        dest_lr=send_refl_dest,
        dest_rl=refl_send_dest,
        localseg_lr=send_refl_localseg,
        localseg_rl=refl_send_localseg
    )
    # Check for errors
    if res != srv6pmCommons_pb2.STATUS_SUCCESS:
        return res
    # Success
    return srv6pmCommons_pb2.STATUS_SUCCESS


class _SRv6PMService(
        srv6pmServiceController_pb2_grpc.SRv6PMControllerServicer):
    """Private class implementing methods exposed by the gRPC server"""

    def SendMeasurementData(self, request, context):
        """RPC used to send measurement data to the controller"""

        logger.debug('Measurement data received: %s' % request)
        # Extract data from the request
        for data in request.measurement_data:
            measure_id = data.measure_id
            interval = data.interval
            timestamp = data.timestamp
            color = data.color
            sender_tx_counter = data.sender_tx_counter
            sender_rx_counter = data.sender_rx_counter
            reflector_tx_counter = data.reflector_tx_counter
            reflector_rx_counter = data.reflector_rx_counter
            # Publish data on Kafka
        status = srv6pmCommons_pb2.StatusCode.Value('STATUS_SUCCESS')
        return srv6pmServiceController_pb2.SendMeasurementDataResponse(
            status=status)


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
