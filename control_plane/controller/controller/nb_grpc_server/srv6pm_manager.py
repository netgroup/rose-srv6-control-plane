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


'''
This module provides an implementation of a SRv6 Manager for the Northbound
gRPC server.
'''

# General imports
import logging

# Controller dependencies
import srv6pm_manager_pb2
import srv6pm_manager_pb2_grpc
from controller import srv6_pm, utils


# Logger reference
logger = logging.getLogger(__name__)


class SRv6PMManager(srv6pm_manager_pb2_grpc.SRv6PMManagerServicer):
    '''
    gRPC request handler.
    '''

    def SetConfiguration(self, request, context):
        '''
        Configure sender and reflector nodes for running an experiment.
        '''
        # pylint: disable=too-many-arguments
        with utils.get_grpc_session(request.sender.address,
                                    request.sender.port) as sender_channel, \
            utils.get_grpc_session(request.reflector.address,
                                   request.reflector.port) as refl_channel:
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
            logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[res])
        # TODO return value

    def ResetConfiguration(self, request, context):
        '''
        Clear node configuration.
        '''
        with utils.get_grpc_session(request.sender.address,
                                    request.sender.port) as sender_channel, \
                utils.get_grpc_session(request.reflector.address,
                                       request.reflector.port) as refl_channel:
            res = srv6_pm.reset_configuration(
                sender_channel=sender_channel,
                reflector_channel=refl_channel
            )
            logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[res])

    def StartExperiment(self, request, context):
        '''
        Start an experiment.
        '''
        # pylint: disable=too-many-arguments, too-many-locals
        with utils.get_grpc_session(request.sender.address,
                                    request.sender.port) as sender_channel, \
                utils.get_grpc_session(request.reflector.address,
                                       request.reflector.port) as refl_channel:
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
            logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[res])

    def GetExperimentResults(self, request, context):
        '''
        Get the results of a running experiment.
        '''
        # pylint: disable=too-many-arguments
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
        '''
        Stop a running experiment.
        '''
        # pylint: disable=too-many-arguments
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