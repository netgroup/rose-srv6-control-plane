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
# Implementation of SRv6 Manager for the Northbound gRPC server
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
This module provides an implementation of a SRv6 Manager for the Northbound
gRPC server.
'''

# General imports
import logging
import os

# Proto dependencies
import commons_pb2
import nb_commons_pb2
import nb_srv6_manager_pb2
import nb_srv6_manager_pb2_grpc

# Controller dependencies
from controller import arangodb_driver
from controller import srv6_utils, srv6_usid, utils
from controller.nb_grpc_server import utils as nb_utils


# Logger reference
logger = logging.getLogger(__name__)


class SRv6Manager(nb_srv6_manager_pb2_grpc.SRv6ManagerServicer):
    '''
    gRPC request handler.
    '''

    def HandleSRv6MicroSIDPolicy(self, request, context):
        '''
        Handle a SRv6 uSID policy.
        '''
        # Create reply message
        response = nb_srv6_manager_pb2.SRv6ManagerReply()
        # Handle SRv6 uSID policy
        res = srv6_usid.handle_srv6_usid_policy(
            operation=request.operation,
            lr_destination=request.lr_destination,
            rl_destination=request.rl_destination,
            nodes_lr=list(request.nodes_lr)
            if request.nodes_lr is not None else None,
            nodes_rl=list(request.nodes_rl)
            if request.nodes_rl is not None else None,
            table=request.table,
            metric=request.metric,
            _id=request._id,
            l_grpc_ip=request.l_grpc_ip,
            l_grpc_port=request.l_grpc_port,
            l_fwd_engine=nb_commons_pb2.FwdEngine.Name(
                request.l_fwd_engine).lower(),
            r_grpc_ip=request.r_grpc_ip,
            r_grpc_port=request.r_grpc_port,
            r_fwd_engine=nb_commons_pb2.FwdEngine.Name(
                request.r_fwd_engine).lower(),
            decap_sid=request.decap_sid,
            locator=request.locator
        )
        if res is not None:
            logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[res])
        # Set status code
        response.status = nb_utils.sb_status_to_nb_status[res]
        # Done, return the reply
        return response

    def HandleSRv6Path(self, request, context):
        '''
        Handle a SRv6 path.
        '''
        # Create reply message
        response = nb_srv6_manager_pb2.SRv6ManagerReply()
        # Iterate on the SRv6 paths
        for srv6_path in request.srv6_paths:
            # Perform the operation
            with utils.get_grpc_session(srv6_path.grpc_address,
                                        srv6_path.grpc_port) as channel:
                res = srv6_utils.handle_srv6_path(
                    operation=srv6_path.operation,
                    channel=channel,
                    destination=srv6_path.destination,
                    segments=list(srv6_path.segments),
                    device=srv6_path.device,
                    encapmode=nb_commons_pb2.EncapMode.Name(
                        srv6_path.encapmode).lower(),
                    table=srv6_path.table,
                    metric=srv6_path.metric,
                    bsid_addr=srv6_path.bsid_addr,
                    fwd_engine=nb_commons_pb2.FwdEngine.Name(
                        srv6_path.fwd_engine).lower()
                )
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[res])
            # Set status code
            if res != commons_pb2.STATUS_SUCCESS:
                # Error
                response.status = nb_utils.sb_status_to_nb_status[res]
                return response
        # Set status code
        response.status = nb_utils.sb_status_to_nb_status[res]
        # Done, return the reply
        return response

    def HandleSRv6Behavior(self, request, context):
        '''
        Handle a SRv6 behavior.
        '''
        # Create reply message
        response = nb_srv6_manager_pb2.SRv6ManagerReply()
        # Iterate on the SRv6 behaviors
        for srv6_behavior in request.srv6_behaviors:
            # Perform the operation
            with utils.get_grpc_session(srv6_behavior.grpc_address,
                                        srv6_behavior.grpc_port) as channel:
                res = srv6_utils.handle_srv6_behavior(
                    operation=srv6_behavior.operation,
                    channel=channel,
                    segment=srv6_behavior.segment,
                    action=nb_utils.grpc_repr_to_action[nb_commons_pb2.SRv6Action.Name(srv6_behavior.action)],
                    device=srv6_behavior.device,
                    table=srv6_behavior.table,
                    nexthop=srv6_behavior.nexthop,
                    lookup_table=srv6_behavior.lookup_table,
                    interface=srv6_behavior.interface,
                    segments=list(srv6_behavior.segments),
                    metric=srv6_behavior.metric,
                    fwd_engine=nb_commons_pb2.FwdEngine.Name(
                        srv6_behavior.fwd_engine).lower()
                )
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[res])
            # Set status code
            if res != commons_pb2.STATUS_SUCCESS:
                # Error
                response.status = nb_utils.sb_status_to_nb_status[res]
                return response
        # Set status code
        response.status = nb_utils.sb_status_to_nb_status[res]
        # Done, return the reply
        return response

    def HandleSRv6UniTunnel(self, request, context):
        '''
        Handle a SRv6 unidirectional tunnel.
        '''
        # Create reply message
        response = nb_srv6_manager_pb2.SRv6ManagerReply()
        # Perform the operation
        for srv6_tunnel in request.srv6_unitunnels:
            with utils.get_grpc_session(srv6_tunnel.ingress_ip,
                                        srv6_tunnel.ingress_port) as ingress_channel, \
                    utils.get_grpc_session(srv6_tunnel.egress_ip,
                                        srv6_tunnel.egress_port) as egress_channel:
                if srv6_tunnel.operation == 'add':
                    res = srv6_utils.create_uni_srv6_tunnel(
                        ingress_channel=ingress_channel,
                        egress_channel=egress_channel,
                        destination=srv6_tunnel.destination,
                        segments=list(srv6_tunnel.segments),
                        localseg=srv6_tunnel.localseg,
                        bsid_addr=srv6_tunnel.bsid_addr,
                        fwd_engine=nb_commons_pb2.FwdEngine.Name(
                            srv6_tunnel.fwd_engine).lower()
                    )
                    logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[res])
                    # Set status code
                    if res != commons_pb2.STATUS_SUCCESS:
                        # Error
                        response.status = nb_utils.sb_status_to_nb_status[res]
                        return response
                elif srv6_tunnel.operation == 'del':
                    res = srv6_utils.destroy_uni_srv6_tunnel(
                        ingress_channel=ingress_channel,
                        egress_channel=egress_channel,
                        destination=srv6_tunnel.destination,
                        localseg=srv6_tunnel.localseg,
                        bsid_addr=srv6_tunnel.bsid_addr,
                        fwd_engine=nb_commons_pb2.FwdEngine.Name(
                            srv6_tunnel.fwd_engine).lower()
                    )
                    logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[res])
                    # Set status code
                    if res != commons_pb2.STATUS_SUCCESS:
                        # Error
                        response.status = nb_utils.sb_status_to_nb_status[res]
                        return response
                else:
                    logger.error('Invalid operation %s', srv6_tunnel.operation)
                    # Set status code
                    response.status = \
                        nb_commons_pb2.STATUS_OPERATION_NOT_SUPPORTED
                    return response
        # Set status code
        response.status = nb_utils.sb_status_to_nb_status[res]
        # Done, return the reply
        return response

    def HandleSRv6BidiTunnel(self, request, context):
        '''
        Handle SRv6 bidirectional tunnel.
        '''
        # Create reply message
        response = nb_srv6_manager_pb2.SRv6ManagerReply()
        # Perform the operation
        for srv6_tunnel in request.srv6_biditunnels:
            with utils.get_grpc_session(srv6_tunnel.node_l_ip,
                                        srv6_tunnel.node_l_port) as node_l_channel, \
                    utils.get_grpc_session(srv6_tunnel.node_r_ip,
                                        srv6_tunnel.node_r_port) as node_r_channel:
                if srv6_tunnel.operation == 'add':
                    res = srv6_utils.create_srv6_tunnel(
                        node_l_channel=node_l_channel,
                        node_r_channel=node_r_channel,
                        sidlist_lr=list(srv6_tunnel.sidlist_lr),
                        sidlist_rl=list(srv6_tunnel.sidlist_rl),
                        dest_lr=srv6_tunnel.dest_lr,
                        dest_rl=srv6_tunnel.dest_rl,
                        localseg_lr=srv6_tunnel.localseg_lr,
                        localseg_rl=srv6_tunnel.localseg_rl,
                        bsid_addr=srv6_tunnel.bsid_addr,
                        fwd_engine=nb_commons_pb2.FwdEngine.Name(
                            srv6_tunnel.fwd_engine).lower()
                    )
                    logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[res])
                    # Set status code
                    if res != commons_pb2.STATUS_SUCCESS:
                        # Error
                        response.status = nb_utils.sb_status_to_nb_status[res]
                        return response
                elif srv6_tunnel.operation == 'del':
                    res = srv6_utils.destroy_srv6_tunnel(
                        node_l_channel=node_l_channel,
                        node_r_channel=node_r_channel,
                        dest_lr=srv6_tunnel.dest_lr,
                        dest_rl=srv6_tunnel.dest_rl,
                        localseg_lr=srv6_tunnel.localseg_lr,
                        localseg_rl=srv6_tunnel.localseg_rl,
                        bsid_addr=srv6_tunnel.bsid_addr,
                        fwd_engine=nb_commons_pb2.FwdEngine.Name(
                            srv6_tunnel.fwd_engine).lower()
                    )
                    logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[res])
                    # Set status code
                    if res != commons_pb2.STATUS_SUCCESS:
                        # Error
                        response.status = nb_utils.sb_status_to_nb_status[res]
                        return response
                else:
                    logger.error('Invalid operation %s', srv6_tunnel.operation)
                    # Set status code
                    response.status = \
                        nb_commons_pb2.STATUS_OPERATION_NOT_SUPPORTED
                    return response
        # Set status code
        response.status = nb_utils.sb_status_to_nb_status[res]
        # Done, return the reply
        return response
