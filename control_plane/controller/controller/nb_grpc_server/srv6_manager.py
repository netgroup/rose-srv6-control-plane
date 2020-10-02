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
            try:
                channel = None
                if srv6_path.grpc_address not in [None, ''] and \
                        srv6_path.grpc_port not in [None, -1]:
                    channel = utils.get_grpc_session(srv6_path.grpc_address,
                                                     srv6_path.grpc_port)
                # Extract the encap mode
                encapmode = nb_commons_pb2.EncapMode.Name(srv6_path.encapmode)
                if encapmode == 'ENCAP_MODE_UNSPEC':
                    encapmode = ''
                # Extract the forwarding engine
                fwd_engine = \
                    nb_commons_pb2.FwdEngine.Name(srv6_path.fwd_engine)
                if fwd_engine == 'FWD_ENGINE_UNSPEC':
                    fwd_engine = ''
                # Handle SRv6 path
                srv6_paths = srv6_utils.handle_srv6_path(
                    operation=srv6_path.operation,
                    channel=channel,
                    destination=srv6_path.destination,
                    segments=list(srv6_path.segments),
                    device=srv6_path.device,
                    encapmode=encapmode,
                    table=srv6_path.table,
                    metric=srv6_path.metric,
                    bsid_addr=srv6_path.bsid_addr,
                    fwd_engine=fwd_engine
                )
                if channel is not None:
                    channel.close()
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[nb_commons_pb2.STATUS_SUCCESS])
            except utils.OperationNotSupportedException:
                response.status = nb_commons_pb2.STATUS_OPERATION_NOT_SUPPORTED
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.InternalError:
                response.status = nb_commons_pb2.STATUS_INTERNAL_ERROR
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.InvalidGRPCRequestException:
                response.status = nb_commons_pb2.STATUS_INVALID_GRPC_REQUEST
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.FileExistsException:
                response.status = nb_commons_pb2.STATUS_FILE_EXISTS
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.NoSuchProcessException:
                response.status = nb_commons_pb2.STATUS_NO_SUCH_PROCESS
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.InvalidActionException:
                response.status = nb_commons_pb2.STATUS_INVALID_ACTION
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.GRPCServiceUnavailableException:
                response.status = \
                    nb_commons_pb2.STATUS_GRPC_SERVICE_UNAVAILABLE
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.GRPCUnauthorizedException:
                response.status = nb_commons_pb2.STATUS_GRPC_UNAUTHORIZED
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.NotConfiguredException:
                response.status = nb_commons_pb2.STATUS_NOT_CONFIGURED
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.AlreadyConfiguredException:
                response.status = nb_commons_pb2.STATUS_ALREADY_CONFIGURED
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.BadRequestException:
                response.status = nb_commons_pb2.STATUS_BAD_REQUEST
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.NoSuchDevicecException:
                response.status = nb_commons_pb2.STATUS_NO_SUCH_DEVICE
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.InvalidActionException:
                response.status = nb_commons_pb2.STATUS_INTERNAL_ERROR
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            # Add the SRv6 paths to the response message
            if srv6_paths is not None:
                for path in srv6_paths:
                    _srv6_path = response.srv6_paths.add()
                    _srv6_path.grpc_address = path['grpc_address']
                    _srv6_path.grpc_port = path['grpc_port']
                    _srv6_path.destination = path['destination']
                    _srv6_path.segments.extend(path['segments'])
                    _srv6_path.encapmode = nb_commons_pb2.EncapMode.Value(path['encapmode'].upper())
                    _srv6_path.device = path['device']
                    _srv6_path.table = path['table']
                    _srv6_path.metric = path['metric']
                    _srv6_path.bsid_addr = path['bsid_addr']
                    _srv6_path.fwd_engine = nb_commons_pb2.FwdEngine.Value(path['fwd_engine'].upper())
                    if '_key' in path:
                        _srv6_path.key = path['_key']
        # Set status code
        response.status = nb_commons_pb2.STATUS_SUCCESS
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
            try:
                channel = None
                if srv6_behavior.grpc_address not in [None, ''] and \
                        srv6_behavior.grpc_port not in [None, -1]:
                    channel = utils.get_grpc_session(srv6_behavior.grpc_address,
                                                     srv6_behavior.grpc_port)
                srv6_behaviors = srv6_utils.handle_srv6_behavior(
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
                if channel is not None:
                    channel.close()
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[nb_commons_pb2.STATUS_SUCCESS])
            except utils.OperationNotSupportedException:
                response.status = nb_commons_pb2.STATUS_OPERATION_NOT_SUPPORTED
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.InternalError:
                response.status = nb_commons_pb2.STATUS_INTERNAL_ERROR
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.InvalidGRPCRequestException:
                response.status = nb_commons_pb2.STATUS_INVALID_GRPC_REQUEST
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.FileExistsException:
                response.status = nb_commons_pb2.STATUS_FILE_EXISTS
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.NoSuchProcessException:
                response.status = nb_commons_pb2.STATUS_NO_SUCH_PROCESS
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.InvalidActionException:
                response.status = nb_commons_pb2.STATUS_INVALID_ACTION
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.GRPCServiceUnavailableException:
                response.status = \
                    nb_commons_pb2.STATUS_GRPC_SERVICE_UNAVAILABLE
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.GRPCUnauthorizedException:
                response.status = nb_commons_pb2.STATUS_GRPC_UNAUTHORIZED
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.NotConfiguredException:
                response.status = nb_commons_pb2.STATUS_NOT_CONFIGURED
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.AlreadyConfiguredException:
                response.status = nb_commons_pb2.STATUS_ALREADY_CONFIGURED
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.BadRequestException:
                response.status = nb_commons_pb2.STATUS_BAD_REQUEST
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.NoSuchDevicecException:
                response.status = nb_commons_pb2.STATUS_NO_SUCH_DEVICE
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.InvalidActionException:
                response.status = nb_commons_pb2.STATUS_INTERNAL_ERROR
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            # Add the SRv6 behaviors to the response message
            if srv6_behaviors is not None:
                for behavior in srv6_behaviors:
                    _srv6_behavior = response.srv6_behaviors.add()
                    _srv6_behavior.grpc_address = behavior['grpc_address']
                    _srv6_behavior.grpc_port = behavior['grpc_port']
                    _srv6_behavior.segment = behavior['segment']
                    _srv6_behavior.action = behavior['action']
                    _srv6_behavior.nexthop = behavior['nexthop']
                    _srv6_behavior.lookup_table = behavior['lookup_table']
                    _srv6_behavior.interface = behavior['interface']
                    _srv6_behavior.segs.extend(behavior['segs'])
                    _srv6_behavior.device = behavior['device']
                    _srv6_behavior.table = behavior['table']
                    _srv6_behavior.metric = behavior['metric']
                    _srv6_behavior.fwd_engine = nb_commons_pb2.FwdEngine.Value(behavior['fwd_engine'].upper())
        # Set status code
        response.status = nb_commons_pb2.STATUS_SUCCESS
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
            try:
                ingress_channel = None
                egress_channel = None
                srv6_tunnels = None
                if srv6_tunnel.ingress_ip not in [None, ''] and \
                        srv6_tunnel.ingress_port not in [None, -1] and \
                        srv6_tunnel.egress_ip not in [None, ''] and \
                        srv6_tunnel.egress_port not in [None, -1]:
                    ingress_channel = utils.get_grpc_session(srv6_tunnel.ingress_ip,
                                                srv6_tunnel.ingress_port)
                    egress_channel = utils.get_grpc_session(srv6_tunnel.egress_ip,
                                                srv6_tunnel.egress_port)
                if srv6_tunnel.operation == 'add':
                    srv6_utils.create_uni_srv6_tunnel(
                        ingress_channel=ingress_channel,
                        egress_channel=egress_channel,
                        destination=srv6_tunnel.destination,
                        segments=list(srv6_tunnel.segments),
                        localseg=srv6_tunnel.localseg,
                        bsid_addr=srv6_tunnel.bsid_addr,
                        fwd_engine=nb_commons_pb2.FwdEngine.Name(
                            srv6_tunnel.fwd_engine).lower()
                    )
                    if ingress_channel is not None:
                        ingress_channel.close()
                    if egress_channel is not None:
                        egress_channel.close()
                    logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[nb_commons_pb2.STATUS_SUCCESS])
                elif srv6_tunnel.operation == 'del':
                    srv6_utils.destroy_uni_srv6_tunnel(
                        ingress_channel=ingress_channel,
                        egress_channel=egress_channel,
                        destination=srv6_tunnel.destination,
                        localseg=srv6_tunnel.localseg,
                        bsid_addr=srv6_tunnel.bsid_addr,
                        fwd_engine=nb_commons_pb2.FwdEngine.Name(
                            srv6_tunnel.fwd_engine).lower()
                    )
                    if ingress_channel is not None:
                        ingress_channel.close()
                    if egress_channel is not None:
                        egress_channel.close()
                    logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[nb_commons_pb2.STATUS_SUCCESS])
                elif srv6_tunnel.operation == 'get':
                    srv6_tunnels = srv6_utils.get_uni_srv6_tunnel(
                        ingress_channel=ingress_channel,
                        egress_channel=egress_channel,
                        destination=srv6_tunnel.destination if srv6_tunnel.destination != '' else None,
                        segments=list(srv6_tunnel.segments) if srv6_tunnel.segments != [''] else None,
                        localseg=srv6_tunnel.localseg if srv6_tunnel.localseg != '' else None,
                        bsid_addr=srv6_tunnel.bsid_addr if srv6_tunnel.localseg != '' else None,
                        fwd_engine=nb_commons_pb2.FwdEngine.Name(
                            srv6_tunnel.fwd_engine).lower() if srv6_tunnel.fwd_engine != '' else None
                    )
                    if ingress_channel is not None:
                        ingress_channel.close()
                    if egress_channel is not None:
                        egress_channel.close()
                    logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[nb_commons_pb2.STATUS_SUCCESS])
                else:
                    logger.error('Invalid operation %s', srv6_tunnel.operation)
                    # Set status code
                    response.status = \
                        nb_commons_pb2.STATUS_OPERATION_NOT_SUPPORTED
                    return response
            except utils.OperationNotSupportedException:
                response.status = nb_commons_pb2.STATUS_OPERATION_NOT_SUPPORTED
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.InternalError:
                response.status = nb_commons_pb2.STATUS_INTERNAL_ERROR
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.InvalidGRPCRequestException:
                response.status = nb_commons_pb2.STATUS_INVALID_GRPC_REQUEST
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.FileExistsException:
                response.status = nb_commons_pb2.STATUS_FILE_EXISTS
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.NoSuchProcessException:
                response.status = nb_commons_pb2.STATUS_NO_SUCH_PROCESS
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.InvalidActionException:
                response.status = nb_commons_pb2.STATUS_INVALID_ACTION
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.GRPCServiceUnavailableException:
                response.status = \
                    nb_commons_pb2.STATUS_GRPC_SERVICE_UNAVAILABLE
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.GRPCUnauthorizedException:
                response.status = nb_commons_pb2.STATUS_GRPC_UNAUTHORIZED
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.NotConfiguredException:
                response.status = nb_commons_pb2.STATUS_NOT_CONFIGURED
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.AlreadyConfiguredException:
                response.status = nb_commons_pb2.STATUS_ALREADY_CONFIGURED
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.BadRequestException:
                response.status = nb_commons_pb2.STATUS_BAD_REQUEST
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.NoSuchDevicecException:
                response.status = nb_commons_pb2.STATUS_NO_SUCH_DEVICE
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.InvalidActionException:
                response.status = nb_commons_pb2.STATUS_INTERNAL_ERROR
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            # Add the SRv6 behaviors to the response message
            if srv6_tunnels is not None:
                for tunnel in srv6_tunnels:
                    _srv6_unitunnel = response.srv6_unitunnels.add()
                    _srv6_unitunnel.ingress_ip = tunnel['ingress_ip']
                    _srv6_unitunnel.ingress_port = tunnel['ingress_port']
                    _srv6_unitunnel.egress_ip = tunnel['egress_ip']
                    _srv6_unitunnel.egress_port = tunnel['egress_port']
                    _srv6_unitunnel.destination = tunnel['destination']
                    _srv6_unitunnel.segments.extend(tunnel['segments'])
                    _srv6_unitunnel.localseg = tunnel['localseg']
                    _srv6_unitunnel.bsid_addr = tunnel['bsid_addr']
                    _srv6_unitunnel.fwd_engine = nb_commons_pb2.FwdEngine.Value(tunnel['fwd_engine'].upper())
        # Set status code
        response.status = nb_commons_pb2.STATUS_SUCCESS
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
            try:
                node_l_channel = None
                node_r_channel = None
                srv6_tunnels = None
                if srv6_tunnel.node_l_ip not in [None, ''] and \
                        srv6_tunnel.node_l_port not in [None, -1] and \
                        srv6_tunnel.node_r_ip not in [None, ''] and \
                        srv6_tunnel.node_r_port not in [None, -1]:
                    node_l_channel = utils.get_grpc_session(srv6_tunnel.node_l_ip,
                                                srv6_tunnel.node_l_port)
                    node_r_channel = utils.get_grpc_session(srv6_tunnel.node_r_ip,
                                                srv6_tunnel.node_r_port)
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
                    if node_l_channel is not None:
                        node_l_channel.close()
                    if node_r_channel is not None:
                        node_r_channel.close()
                    logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[nb_commons_pb2.STATUS_SUCCESS])
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
                    if node_l_channel is not None:
                        node_l_channel.close()
                    if node_r_channel is not None:
                        node_r_channel.close()
                    logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[nb_commons_pb2.STATUS_SUCCESS])
                elif srv6_tunnel.operation == 'get':
                    srv6_tunnels = srv6_utils.get_srv6_tunnel(
                        node_l_channel=node_l_channel,
                        node_r_channel=node_r_channel,
                        sidlist_lr=srv6_tunnel.sidlist_lr if srv6_tunnel.sidlist_lr != [''] else None,
                        sidlist_rl=srv6_tunnel.sidlist_rl if srv6_tunnel.sidlist_rl != [''] else None,
                        dest_lr=srv6_tunnel.dest_lr if srv6_tunnel.dest_lr != '' else None,
                        dest_rl=srv6_tunnel.dest_rl if srv6_tunnel.dest_rl != '' else None,
                        localseg_lr=srv6_tunnel.localseg_lr if srv6_tunnel.localseg_lr != '' else None,
                        localseg_rl=srv6_tunnel.localseg_rl if srv6_tunnel.localseg_rl != '' else None,
                        bsid_addr=srv6_tunnel.bsid_addr if srv6_tunnel.bsid_addr != '' else None,
                        fwd_engine=srv6_tunnel.fwd_engine if srv6_tunnel.fwd_engine != '' else None,
                        key=srv6_tunnel.key if srv6_tunnel.key != '' else None
                    )
                    if node_l_channel is not None:
                        node_l_channel.close()
                    if node_r_channel is not None:
                        node_r_channel.close()
                    logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[nb_commons_pb2.STATUS_SUCCESS])
                else:
                    logger.error('Invalid operation %s', srv6_tunnel.operation)
                    # Set status code
                    response.status = \
                        nb_commons_pb2.STATUS_OPERATION_NOT_SUPPORTED
                    return response
            except utils.OperationNotSupportedException:
                response.status = nb_commons_pb2.STATUS_OPERATION_NOT_SUPPORTED
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.InternalError:
                response.status = nb_commons_pb2.STATUS_INTERNAL_ERROR
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.InvalidGRPCRequestException:
                response.status = nb_commons_pb2.STATUS_INVALID_GRPC_REQUEST
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.FileExistsException:
                response.status = nb_commons_pb2.STATUS_FILE_EXISTS
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.NoSuchProcessException:
                response.status = nb_commons_pb2.STATUS_NO_SUCH_PROCESS
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.InvalidActionException:
                response.status = nb_commons_pb2.STATUS_INVALID_ACTION
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.GRPCServiceUnavailableException:
                response.status = \
                    nb_commons_pb2.STATUS_GRPC_SERVICE_UNAVAILABLE
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.GRPCUnauthorizedException:
                response.status = nb_commons_pb2.STATUS_GRPC_UNAUTHORIZED
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.NotConfiguredException:
                response.status = nb_commons_pb2.STATUS_NOT_CONFIGURED
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.AlreadyConfiguredException:
                response.status = nb_commons_pb2.STATUS_ALREADY_CONFIGURED
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.BadRequestException:
                response.status = nb_commons_pb2.STATUS_BAD_REQUEST
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.NoSuchDevicecException:
                response.status = nb_commons_pb2.STATUS_NO_SUCH_DEVICE
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            except utils.InvalidActionException:
                response.status = nb_commons_pb2.STATUS_INTERNAL_ERROR
                logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[response.status])
                return response
            # Add the SRv6 behaviors to the response message
            if srv6_tunnels is not None:
                for tunnel in srv6_tunnels:
                    _srv6_biditunnel = response.srv6_biditunnels.add()
                    _srv6_biditunnel.node_l_ip = tunnel['node_l_ip']
                    _srv6_biditunnel.node_l_port = tunnel['node_l_port']
                    _srv6_biditunnel.node_r_ip = tunnel['node_r_ip']
                    _srv6_biditunnel.node_r_port = tunnel['node_r_port']
                    _srv6_biditunnel.dest_lr = tunnel['dest_lr']
                    _srv6_biditunnel.dest_rl = tunnel['dest_rl']
                    _srv6_biditunnel.sidlist_lr.extend(tunnel['sidlist_lr'])
                    _srv6_biditunnel.sidlist_rl.extend(tunnel['sidlist_rl'])
                    _srv6_biditunnel.localseg_lr = tunnel['localseg_lr']
                    _srv6_biditunnel.localseg_rl = tunnel['localseg_rl']
                    _srv6_biditunnel.bsid_addr = tunnel['bsid_addr']
                    _srv6_biditunnel.fwd_engine = nb_commons_pb2.FwdEngine.Value(tunnel['fwd_engine'].upper())
        # Set status code
        response.status = nb_commons_pb2.STATUS_SUCCESS
        # Done, return the reply
        return response
