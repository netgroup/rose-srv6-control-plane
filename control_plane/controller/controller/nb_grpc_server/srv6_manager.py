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

# Controller dependencies
import nb_srv6_manager_pb2
import nb_srv6_manager_pb2_grpc
from controller import srv6_utils, srv6_usid, utils


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
        # Convert nodes config to a dict representation
        nodes_dict = dict()
        for node_config in request.nodes_config:
            nodes_dict[node_config.name] = {
                'name': node_config.name,
                'grpc_ip': node_config.grpc_ip,
                'grpc_port': node_config.grpc_port,
                'uN': node_config.uN,
                'uDT': node_config.uDT,
                'fwd_engine': node_config.fwd_engine
            }
        # Handle SRv6 uSID policy
        res = srv6_usid.handle_srv6_usid_policy(
            operation=request.operation,
            nodes_dict=nodes_dict,
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
            l_fwd_engine=nb_srv6_manager_pb2.Name(
                request.l_fwd_engine).lower(),
            r_grpc_ip=request.r_grpc_ip,
            r_grpc_port=request.r_grpc_port,
            r_fwd_engine=nb_srv6_manager_pb2.Name(
                request.r_fwd_engine).lower(),
            decap_sid=request.decap_sid,
            locator=request.locator
        )
        if res is not None:
            logger.debug('%s\n\n' % utils.STATUS_CODE_TO_DESC[res])

    def HandleSRv6PathPolicy(self, request, context):
        '''
        Handle a SRv6 path.
        '''
        with utils.get_grpc_session(request.grpc_address,
                                    request.grpc_port) as channel:
            res = srv6_utils.handle_srv6_path(
                operation=request.operation,
                channel=channel,
                destination=request.destination,
                segments=list(request.segments),
                device=request.device,
                encapmode=nb_srv6_manager_pb2.Name(
                    request.encapmode).lower(),
                table=request.table,
                metric=request.metric,
                bsid_addr=request.bsid_addr,
                fwd_engine=nb_srv6_manager_pb2.Name(
                    request.fwd_engine).lower()
            )
            logger.debug('%s\n\n' % utils.STATUS_CODE_TO_DESC[res])

    def HandleSRv6BehaviorPolicy(self, request, context):
        '''
        Handle a SRv6 behavior.
        '''
        with utils.get_grpc_session(request.grpc_address,
                                    request.grpc_port) as channel:
            res = srv6_utils.handle_srv6_behavior(
                operation=request.operation,
                channel=channel,
                segment=request.segment,
                action=nb_srv6_manager_pb2.Name(
                    request.action).lower(),
                device=request.device,
                table=request.table,
                nexthop=request.nexthop,
                lookup_table=request.lookup_table,
                interface=request.interface,
                segments=list(request.segments),
                metric=request.metric,
                fwd_engine=nb_srv6_manager_pb2.Name(
                    request.fwd_engine).lower()
            )
            logger.debug('%s\n\n' % utils.STATUS_CODE_TO_DESC[res])

    def HandleSRv6UniTunnel(self, request, context):
        '''
        Handle a SRv6 unidirectional tunnel.
        '''
        with utils.get_grpc_session(request.ingress_ip,
                                    request.ingress_port) as ingress_channel, \
                utils.get_grpc_session(request.egress_ip,
                                       request.egress_port) as egress_channel:
            if request.operation == 'add':
                res = srv6_utils.create_uni_srv6_tunnel(
                    ingress_channel=ingress_channel,
                    egress_channel=egress_channel,
                    destination=request.destination,
                    segments=list(request.segments),
                    localseg=request.localseg,
                    bsid_addr=request.bsid_addr,
                    fwd_engine=nb_srv6_manager_pb2.Name(
                        request.fwd_engine).lower()
                )
                logger.debug('%s\n\n' % utils.STATUS_CODE_TO_DESC[res])
            elif request.operation == 'del':
                res = srv6_utils.destroy_uni_srv6_tunnel(
                    ingress_channel=ingress_channel,
                    egress_channel=egress_channel,
                    destination=request.destination,
                    localseg=request.localseg,
                    bsid_addr=request.bsid_addr,
                    fwd_engine=nb_srv6_manager_pb2.Name(
                        request.fwd_engine).lower()
                )
                logger.debug('%s\n\n' % utils.STATUS_CODE_TO_DESC[res])
            else:
                logger.error('Invalid operation %s' % request.operation)

    def handle_srv6_biditunnel(self, request, context):
        '''
        Handle SRv6 bidirectional tunnel.
        '''
        with utils.get_grpc_session(request.node_l_ip,
                                    request.node_l_port) as node_l_channel, \
                utils.get_grpc_session(request.node_r_ip,
                                       request.node_r_port) as node_r_channel:
            if request.operation == 'add':
                res = srv6_utils.create_srv6_tunnel(
                    node_l_channel=node_l_channel,
                    node_r_channel=node_r_channel,
                    sidlist_lr=list(request.sidlist_lr),
                    sidlist_rl=list(request.sidlist_rl),
                    dest_lr=request.dest_lr,
                    dest_rl=request.dest_rl,
                    localseg_lr=request.localseg_lr,
                    localseg_rl=request.localseg_rl,
                    bsid_addr=request.bsid_addr,
                    fwd_engine=nb_srv6_manager_pb2.Name(
                        request.fwd_engine).lower()
                )
                logger.debug('%s\n\n' % utils.STATUS_CODE_TO_DESC[res])
            elif request.operation == 'del':
                res = srv6_utils.destroy_srv6_tunnel(
                    node_l_channel=node_l_channel,
                    node_r_channel=node_r_channel,
                    dest_lr=request.dest_lr,
                    dest_rl=request.dest_rl,
                    localseg_lr=request.localseg_lr,
                    localseg_rl=request.localseg_rl,
                    bsid_addr=request.bsid_addr,
                    fwd_engine=nb_srv6_manager_pb2.Name(
                        request.fwd_engine).lower()
                )
                logger.debug('%s\n\n' % utils.STATUS_CODE_TO_DESC[res])
            else:
                logger.error('Invalid operation %s' % request.operation)

    def GetNodes(self, request, context):
        '''
        Get the nodes.
        '''
        raise NotImplementedError
