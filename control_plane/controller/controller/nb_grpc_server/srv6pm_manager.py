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
# Implementation of SRv6-PM Manager for the Northbound gRPC server
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


"""
This module provides an implementation of a SRv6-PM Manager for the Northbound
gRPC server. The SRv6-PM Manager implements different
control plane functionalities to setup SRv6 entities
"""

# General imports
import logging
import os
# Proto dependencies
import nb_commons_pb2
import srv6pm_manager_pb2
import srv6pm_manager_pb2_grpc
# Controller dependencies
from controller import srv6_pm, utils
from controller import arangodb_driver


# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)


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
    LOOPBACK_MODE = srv6pm_manager_pb2.DelayMeasurementMode.Value('LoopbackMode')


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
# gRPC server APIs


class SRv6PMManager(srv6pm_manager_pb2_grpc.SRv6PMManagerServicer):
    """
    gRPC request handler.
    """

    def __init__(self, db_client=None):
        """
        SRv6-PM Manager init method.

        :param db_client: ArangoDB client.
        :type db_client: class: `arango.client.ArangoClient`
        """
        # Establish a connection to the "srv6pm" database
        # We will keep the connection open forever
        self.db_conn = arangodb_driver.connect_db(
            client=db_client,
            db_name='srv6pm',
            username=os.getenv('ARANGO_USER'),
            password=os.getenv('ARANGO_PASSWORD')
        )

    def SetConfiguration(self, request, context):
        """
        Configure sender and reflector nodes for running an experiment.
        """
        # pylint: disable=invalid-name, unused-argument, no-self-use
        #
        # Establish a gRPC connection to the sender and to the reflector
        with utils.get_grpc_session(request.sender.address,
                                    request.sender.port) as sender_channel, \
            utils.get_grpc_session(request.reflector.address,
                                   request.reflector.port) as refl_channel:
            # Send the set configuration request
            logger.debug('Trying to set the experiment configuration')
            res = srv6_pm.set_configuration(
                sender_channel=sender_channel,
                reflector_channel=refl_channel,
                send_udp_port=request.send_udp_port,
                refl_udp_port=request.refl_udp_port,
                interval_duration=request.color_options.interval_duration,
                delay_margin=request.color_options.delay_margin,
                number_of_color=request.color_options.number_of_color,
                pm_driver=request.pm_driver
            )
            logger.debug('Configuration installed successfully')
            # TODO set_configuration should return an exception in case of error
            logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[res])
        # Done, create a reply
        return srv6pm_manager_pb2_grpc.SRv6PMManagerReply(
            status=nb_commons_pb2.STATUS_SUCCESS
        )

    def ResetConfiguration(self, request, context):
        """
        Clear node configuration.
        """
        # pylint: disable=invalid-name, unused-argument, no-self-use
        #
        # Establish a gRPC connection to the sender and to the reflector
        with utils.get_grpc_session(request.sender.address,
                                    request.sender.port) as sender_channel, \
                utils.get_grpc_session(request.reflector.address,
                                       request.reflector.port) as refl_channel:
            # Send the reset configuration request
            logger.debug('Trying to reset the experiment configuration')
            res = srv6_pm.reset_configuration(
                sender_channel=sender_channel,
                reflector_channel=refl_channel
            )
            logger.debug('Configuration reset successfully')
            # TODO reset_configuration should return an exception in case of error
            logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[res])
        # Done, create a reply
        return srv6pm_manager_pb2_grpc.SRv6PMManagerReply(
            status=nb_commons_pb2.STATUS_SUCCESS
        )

    def StartExperiment(self, request, context):
        """
        Start an experiment.
        """
        # pylint: disable=invalid-name, unused-argument, no-self-use
        #
        # Establish a gRPC connection to the sender and to the reflector
        with utils.get_grpc_session(request.sender.address,
                                    request.sender.port) as sender_channel, \
                utils.get_grpc_session(request.reflector.address,
                                       request.reflector.port) as refl_channel:
            # Trying to start the experiment
            logger.debug('Trying to start the experiment')
            res = srv6_pm.start_experiment(
                sender_channel=sender_channel,
                reflector_channel=refl_channel,
                send_refl_dest=request.send_refl_dest,
                refl_send_dest=request.refl_send_dest,
                send_refl_sidlist=list(request.send_refl_sidlist),
                refl_send_sidlist=list(request.refl_send_sidlist),
                measurement_protocol=grpc_to_py_measurement_protocol(request.measurement_protocol),
                measurement_type=grpc_to_py_measurement_type(request.measurement_type),
                authentication_mode=grpc_to_py_authentication_mode(request.authentication_mode),
                authentication_key=request.authentication_key,
                timestamp_format=grpc_to_py_timestamp_format(request.timestamp_format),
                delay_measurement_mode=grpc_to_py_delay_measurement_mode(request.delay_measurement_mode),
                padding_mbz=request.padding_mbz,
                loss_measurement_mode=grpc_to_py_loss_measurement_mode(request.loss_measurement_mode),
                measure_id=request.measure_id,
                send_refl_localseg=request.send_refl_localseg,
                refl_send_localseg=request.refl_send_localseg,
                force=request.force
            )
            logger.debug('Experiment started successfully')
            # TODO start_experiment should return an exception in case of error
            logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[res])
        # Done, create a reply
        return srv6pm_manager_pb2_grpc.SRv6PMManagerReply(
            status=nb_commons_pb2.STATUS_SUCCESS
        )

    def GetExperimentResults(self, request, context):
        """
        Get the results of a running experiment.
        """
        # pylint: disable=invalid-name, unused-argument, no-self-use
        #
        # Establish a gRPC connection to the sender and to the reflector
        with utils.get_grpc_session(request.sender.address,
                                    request.sender.port) as sender_channel, \
                utils.get_grpc_session(request.reflector.address,
                                       request.reflector.port) as refl_channel:
            # Trying to collect the experiment results
            logger.debug('Trying to collect the experiment results')
            print(srv6_pm.get_experiment_results(
                sender_channel=sender_channel,
                reflector_channel=refl_channel,
                send_refl_sidlist=list(request.send_refl_sidlist),
                refl_send_sidlist=list(request.refl_send_sidlist)
            ))
            logger.debug('Results retrieved successfully')
            # TODO get_experiment_results should return an exception in case of error
            # TODO get_experiment_results should return the results instead of printing them
        # Done, create a reply
        return srv6pm_manager_pb2_grpc.SRv6PMManagerReply(
            status=nb_commons_pb2.STATUS_SUCCESS
        )

    def StopExperiment(self, request, context):
        """
        Stop a running experiment.
        """
        # pylint: disable=invalid-name, unused-argument, no-self-use
        #
        # Establish a gRPC connection to the sender and to the reflector
        with utils.get_grpc_session(request.sender.address,
                                    request.sender.port) as sender_channel, \
                utils.get_grpc_session(request.reflector.address,
                                       request.reflector.port) as refl_channel:
            # Trying to stop the experiment
            logger.debug('Trying to stop the experiment')
            res = srv6_pm.stop_experiment(
                sender_channel=sender_channel,
                reflector_channel=refl_channel,
                send_refl_dest=request.send_refl_dest,
                refl_send_dest=request.refl_send_dest,
                send_refl_sidlist=list(request.send_refl_sidlist),
                refl_send_sidlist=list(request.refl_send_sidlist),
                send_refl_localseg=request.send_refl_localseg,
                refl_send_localseg=request.refl_send_localseg
            )
            logger.debug('Experiment stopped successfully')
            # TODO stop_experiment should return an exception in case of error
            logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[res])
        # Done, create a reply
        return srv6pm_manager_pb2_grpc.SRv6PMManagerReply(
            status=nb_commons_pb2.STATUS_SUCCESS
        )
