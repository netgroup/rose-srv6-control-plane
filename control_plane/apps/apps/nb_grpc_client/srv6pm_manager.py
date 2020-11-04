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
# Implementation of SRv6-PM Manager for the Northbound gRPC client
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


"""
This module provides an implementation of a SRv6-PM Manager for the Northbound
gRPC client.
"""

# General imports
from enum import Enum
# Proto dependencies
import srv6pm_manager_pb2
import srv6pm_manager_pb2_grpc
# gRPC client dependencies
from apps.nb_grpc_client import utils


# ############################################################################
# Peformance Measurement driver (PMDriver)
class PMDriver(Enum):
    """
    Driver used for Performance Measurement.
    """
    EBPF = srv6pm_manager_pb2.PMDriver.Value('EBPF')
    IPSET = srv6pm_manager_pb2.PMDriver.Value('IPSET')


# Mapping python representation of PM Driver to gRPC representation
py_to_grpc_pmdriver = {
    'ebpf': PMDriver.EBPF.value,
    'ipset': PMDriver.IPSET.value
}

# Mapping gRPC representation of PM Driver to python representation
grpc_to_py_pmdriver = {v: k for k, v in py_to_grpc_pmdriver.items()}


# ############################################################################
# Measurement Protocol
class MeasurementProtocol(Enum):
    """
    Measurement protocol.
    """
    TWAMP = srv6pm_manager_pb2.MeasurementProtocol.Value('TWAMP')
    STAMP = srv6pm_manager_pb2.MeasurementProtocol.Value('STAMP')


# Mapping python representation of Measurement Protocol to gRPC representation
py_to_grpc_measurement_protocol = {
    'twamp': MeasurementProtocol.TWAMP.value,
    'stamp': MeasurementProtocol.STAMP.value
}

# Mapping gRPC representation of Measurement Protocol to python representation
grpc_to_py_measurement_protocol = {
    v: k for k, v in py_to_grpc_measurement_protocol.items()}


# ############################################################################
# Measurement Type
class MeasurementType(Enum):
    """
    Measurement type.
    """
    DELAY = srv6pm_manager_pb2.MeasurementType.Value('DELAY')
    LOSS = srv6pm_manager_pb2.MeasurementType.Value('LOSS')


# Mapping python representation of Measurement Type to gRPC representation
py_to_grpc_measurement_type = {
    'delay': MeasurementType.DELAY.value,
    'loss': MeasurementType.LOSS.value
}

# Mapping gRPC representation of Measurement Type to python representation
grpc_to_py_measurement_type = {
    v: k for k, v in py_to_grpc_measurement_type.items()}


# ############################################################################
# Authentication Mode
class AuthenticationMode(Enum):
    """
    Authentication mode.
    """
    HMAC_SHA_256 = srv6pm_manager_pb2.AuthenticationMode.Value('HMAC_SHA_256')


# Mapping python representation of Authentication Mode to gRPC representation
py_to_grpc_authentication_mode = {
    'hmac_sha_256': AuthenticationMode.HMAC_SHA_256.value
}

# Mapping gRPC representation of Authentication Mode to python representation
grpc_to_py_authentication_mode = {
    v: k for k, v in py_to_grpc_authentication_mode.items()}


# ############################################################################
# Timestamp Format
class TimestampFormat(Enum):
    """
    Timestamp format.
    """
    PTPv2 = srv6pm_manager_pb2.TimestampFormat.Value('PTPv2')
    NTP = srv6pm_manager_pb2.TimestampFormat.Value('NTP')


# Mapping python representation of Timestamp Format to gRPC representation
py_to_grpc_timestamp_format = {
    'ptpv2': TimestampFormat.PTPv2.value,
    'ntp': TimestampFormat.NTP.value,
}

# Mapping gRPC representation of Timestamp Format to python representation
grpc_to_py_timestamp_format = {
    v: k for k, v in py_to_grpc_timestamp_format.items()}


# ############################################################################
# Delay Measurement Mode
class DelayMeasurementMode(Enum):
    """
    Delay measurement mode.
    """
    ONE_WAY = srv6pm_manager_pb2.DelayMeasurementMode.Value('OneWay')
    TWO_WAY = srv6pm_manager_pb2.DelayMeasurementMode.Value('TwoWay')
    LOOPBACK_MODE = \
        srv6pm_manager_pb2.DelayMeasurementMode.Value('LoopbackMode')


# Mapping python representation of Delay Measurement Mode to gRPC
# representation
py_to_grpc_delay_measurement_mode = {
    'oneway': DelayMeasurementMode.ONE_WAY.value,
    'twoway': DelayMeasurementMode.TWO_WAY.value,
    'loopback': DelayMeasurementMode.LOOPBACK_MODE.value
}

# Mapping gRPC representation of Delay Measurement Mode to python
# representation
grpc_to_py_delay_measurement_mode = {
    v: k for k, v in py_to_grpc_delay_measurement_mode.items()}


# ############################################################################
# Loss Measurement Mode
class LossMeasurementMode(Enum):
    """
    Loss measurement mode.
    """
    INFERRED = srv6pm_manager_pb2.LossMeasurementMode.Value('Inferred')
    DIRECT = srv6pm_manager_pb2.LossMeasurementMode.Value('Direct')


# Mapping python representation of Loss Measurement Mode to gRPC
# representation
py_to_grpc_loss_measurement_mode = {
    'inferred': LossMeasurementMode.INFERRED.value,
    'direct': LossMeasurementMode.DIRECT.value
}

# Mapping gRPC representation of Loss Measurement Mode to python
# representation
grpc_to_py_loss_measurement_mode = {
    v: k for k, v in py_to_grpc_loss_measurement_mode.items()}


# ############################################################################
# gRPC client APIs

def set_configuration(controller_channel, sender, reflector,
                      sender_port, reflector_port, send_udp_port,
                      refl_udp_port, interval_duration, delay_margin,
                      number_of_color, pm_driver, in_interfaces=None,
                      out_interfaces=None):
    """
    Configure a node.
    """
    # pylint: disable=too-many-arguments
    #
    # Create request message
    request = srv6pm_manager_pb2.SRv6PMConfigurationRequest()
    # Set the gRPC IP address of the sender node
    request.sender.address = sender
    # Set the gRPC port number of the sender node
    request.sender.port = sender_port
    # Set the gRPC IP address of the reflector node
    request.reflector.address = reflector
    # Set the gRPC port number of the reflector node
    request.reflector.port = reflector_port
    # Set the UDP port used by the sender
    request.send_udp_port = send_udp_port
    # Set the UDP port used by the reflector
    request.refl_udp_port = refl_udp_port
    # Set the interval duration
    request.color_options.interval_duration = interval_duration
    # Set the delay margin
    request.color_options.delay_margin = delay_margin
    # Set the number of color
    request.color_options.numbers_of_color = number_of_color
    # Set the driver to be used for Performance Monitoring
    if pm_driver not in py_to_grpc_pmdriver:
        raise utils.InvalidArgumentError
    request.pm_driver = py_to_grpc_pmdriver[pm_driver]
    # Set the ingress interface to monitor
    if in_interfaces is not None:
        request.in_interfaces.extend(in_interfaces)
    # Set the egress interface to monitor
    if out_interfaces is not None:
        request.out_interfaces.extend(out_interfaces)
    # Request message is ready
    #
    # Get the reference of the stub
    stub = srv6pm_manager_pb2_grpc.SRv6PMManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.SetConfiguration(request)
    # Check the status code and raise an exception if an error occurred
    utils.raise_exception_on_error(response.status)


def reset_configuration(controller_channel, sender, reflector,
                        sender_port, reflector_port):
    """
    Clear node configuration.
    """
    # Create request message
    request = srv6pm_manager_pb2.SRv6PMConfigurationRequest()
    # Set the gRPC IP address of the sender node
    request.sender.address = sender
    # Set the gRPC port number of the sender node
    request.sender.port = sender_port
    # Set the gRPC IP address of the reflector node
    request.reflector.address = reflector
    # Set the gRPC port number of the reflector node
    request.reflector.port = reflector_port
    # Request message is ready
    #
    # Get the reference of the stub
    stub = srv6pm_manager_pb2_grpc.SRv6PMManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.ResetConfiguration(request)
    # Check the status code and raise an exception if an error occurred
    utils.raise_exception_on_error(response.status)


def start_experiment(controller_channel, sender, reflector,
                     sender_port, reflector_port, send_refl_dest,
                     refl_send_dest, send_refl_sidlist, refl_send_sidlist,
                     measurement_protocol, measurement_type,
                     authentication_mode, authentication_key,
                     timestamp_format, delay_measurement_mode,
                     padding_mbz, loss_measurement_mode, measure_id=None,
                     send_refl_localseg=None, refl_send_localseg=None,
                     force=False):
    """
    Start an experiment.
    """
    # pylint: disable=too-many-arguments, too-many-locals
    #
    # Create request message
    request = srv6pm_manager_pb2.SRv6PMExperimentRequest()
    # Set the gRPC address of the sender
    request.sender.address = sender
    # Set the gRPC port number of the sender
    request.sender.port = sender_port
    # Set the gRPC address of the reflector
    request.reflector.address = reflector
    # Set the gRPC port number of the reflector
    request.reflector.address = reflector_port
    # Set the destination for the sender to reflector path
    request.send_refl_dest = send_refl_dest
    # Set the destination for the reflector to sender path
    request.refl_send_dest = refl_send_dest
    # Set the SID list for the sender to reflector path
    request.send_refl_sidlist.extend(send_refl_sidlist)
    # Set the SID list for the reflector to sender path
    request.refl_send_sidlist.extend(refl_send_sidlist)
    # Set the measurement protocol
    if measurement_protocol not in py_to_grpc_measurement_protocol:
        raise utils.InvalidArgumentError
    request.measurement_protocol = \
        py_to_grpc_measurement_protocol[measurement_protocol]
    # Set the measurement type
    if measurement_type not in py_to_grpc_measurement_type:
        raise utils.InvalidArgumentError
    request.measurement_type = \
        py_to_grpc_measurement_type[measurement_type]
    # Set the authentication mode
    if authentication_mode not in py_to_grpc_authentication_mode:
        raise utils.InvalidArgumentError
    request.authentication_mode = \
        py_to_grpc_authentication_mode[authentication_mode]
    # Set the authentication key
    request.authentication_key = authentication_key
    # Set the timestamp format
    if timestamp_format not in py_to_grpc_timestamp_format:
        raise utils.InvalidArgumentError
    request.timestamp_format = \
        py_to_grpc_timestamp_format[timestamp_format]
    # Set the delay measurement mode
    if delay_measurement_mode not in py_to_grpc_delay_measurement_mode:
        raise utils.InvalidArgumentError
    request.delay_measurement_mode = \
        py_to_grpc_delay_measurement_mode[delay_measurement_mode]
    # Set the padding
    request.padding_mbz = padding_mbz
    # Set the loss measurement mode
    if loss_measurement_mode not in py_to_grpc_loss_measurement_mode:
        raise utils.InvalidArgumentError
    request.loss_measurement_mode = \
        py_to_grpc_loss_measurement_mode[loss_measurement_mode]
    # Set the measure ID
    request.measure_id = measure_id
    # Set the local segment for the left to right path
    request.send_refl_localseg = send_refl_localseg
    # Set the local segment for the right to left path
    request.refl_send_localseg = refl_send_localseg
    # Set the force flag
    request.force = force
    # Request message is ready
    #
    # Get the reference of the stub
    stub = srv6pm_manager_pb2_grpc.SRv6PMManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.StartExperiment(request)
    # Check the status code and raise an exception if an error occurred
    utils.raise_exception_on_error(response.status)


def get_experiment_results(controller_channel, sender, reflector,
                           sender_port, reflector_port,
                           send_refl_sidlist, refl_send_sidlist):
    """
    Get the results of a running experiment.
    """
    # pylint: disable=too-many-arguments
    #
    # Create request message
    request = srv6pm_manager_pb2.SRv6PMExperimentRequest()
    # Set the gRPC address of the sender
    request.sender.address = sender
    # Set the gRPC port number of the sender
    request.sender.port = sender_port
    # Set the gRPC address of the reflector
    request.reflector.address = reflector
    # Set the gRPC port number of the reflector
    request.reflector.address = reflector_port
    # Set the SID list for the sender to reflector path
    request.send_refl_sidlist.extend(send_refl_sidlist)
    # Set the SID list for the reflector to sender path
    request.refl_send_sidlist.extend(refl_send_sidlist)
    # Request message is ready
    #
    # Get the reference of the stub
    stub = srv6pm_manager_pb2_grpc.SRv6PMManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.GetExperimentResults(request)
    # Check the status code and raise an exception if an error occurred
    utils.raise_exception_on_error(response.status)
    # Extract the measurement data from the response message
    measurement_data = list()
    for data in response.measurement_data:
        measurement_data.append({
            'meas_id': data.meas_id,
            'ssSeqNum': data.ssSeqNum,
            'interval': data.interval,
            'timestamp': data.timestamp,
            'ssTxCounter': data.ssTxCounter,
            'rfRxCounter': data.rfRxCounter,
            'fwColor': data.fwColor,
            'rfSeqNum': data.rfSeqNum,
            'rfTxCounter': data.rfTxCounter,
            'ssRxCounter': data.ssRxCounter,
            'rvColor': data.rvColor,
        })
    # Done, return the list of collected data
    return measurement_data


def stop_experiment(controller_channel, sender, reflector,
                    sender_port, reflector_port, send_refl_dest,
                    refl_send_dest, send_refl_sidlist, refl_send_sidlist,
                    send_refl_localseg=None, refl_send_localseg=None):
    """
    Stop a running experiment.
    """
    # pylint: disable=too-many-arguments
    #
    # Create request message
    request = srv6pm_manager_pb2.SRv6PMExperimentRequest()
    # Set the gRPC address of the sender
    request.sender.address = sender
    # Set the gRPC port number of the sender
    request.sender.port = sender_port
    # Set the gRPC address of the reflector
    request.reflector.address = reflector
    # Set the gRPC port number of the reflector
    request.reflector.address = reflector_port
    # Set the destination for the sender to reflector path
    request.send_refl_dest = send_refl_dest
    # Set the destination for the reflector to sender path
    request.refl_send_dest = refl_send_dest
    # Set the SID list for the sender to reflector path
    request.send_refl_sidlist.extend(send_refl_sidlist)
    # Set the SID list for the reflector to sender path
    request.refl_send_sidlist.extend(refl_send_sidlist)
    # Set the local segment for the left to right path
    request.send_refl_localseg = send_refl_localseg
    # Set the local segment for the right to left path
    request.refl_send_localseg = refl_send_localseg
    # Request message is ready
    #
    # Get the reference of the stub
    stub = srv6pm_manager_pb2_grpc.SRv6PMManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.StopExperiment(request)
    # Check the status code and raise an exception if an error occurred
    utils.raise_exception_on_error(response.status)
