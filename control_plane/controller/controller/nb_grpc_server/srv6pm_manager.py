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
                measurement_protocol=srv6pm_manager_pb2.Name(
                    request.measurement_protocol).lower(),
                measurement_type=srv6pm_manager_pb2.Name(
                    request.measurement_type).lower(),
                authentication_mode=srv6pm_manager_pb2.Name(
                    request.authentication_mode).lower(),
                authentication_key=srv6pm_manager_pb2.Name(
                    request.authentication_key).lower(),
                timestamp_format=srv6pm_manager_pb2.Name(
                    request.timestamp_format).lower(),
                delay_measurement_mode=srv6pm_manager_pb2.Name(
                    request.delay_measurement_mode).lower(),
                padding_mbz=srv6pm_manager_pb2.Name(
                    request.padding_mbz).lower(),
                loss_measurement_mode=srv6pm_manager_pb2.Name(
                    request.loss_measurement_mode).lower(),
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
        with utils.get_grpc_session(request.sender.address,
                                    request.sender.port) as sender_channel, \
                utils.get_grpc_session(request.reflector.address,
                                       request.reflector.port) as refl_channel:
            print(srv6_pm.get_experiment_results(   # TODO
                sender_channel=sender_channel,
                reflector_channel=refl_channel,
                send_refl_sidlist=list(request.send_refl_sidlist),
                refl_send_sidlist=list(request.refl_send_sidlist)
            ))

    def StopExperiment(self, request, context):
        """
        Stop a running experiment.
        """
        # pylint: disable=invalid-name, unused-argument, no-self-use
        with utils.get_grpc_session(request.sender.address,
                                    request.sender.port) as sender_channel, \
                utils.get_grpc_session(request.reflector.address,
                                       request.reflector.port) as refl_channel:
            srv6_pm.stop_experiment(
                sender_channel=sender_channel,
                reflector_channel=refl_channel,
                send_refl_dest=request.send_refl_dest,
                refl_send_dest=request.refl_send_dest,
                send_refl_sidlist=list(request.send_refl_sidlist),
                refl_send_sidlist=list(request.refl_send_sidlist),
                send_refl_localseg=request.send_refl_localseg,
                refl_send_localseg=request.refl_send_localseg
            )
