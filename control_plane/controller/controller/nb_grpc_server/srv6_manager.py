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


"""
This module provides an implementation of a SRv6 Manager for the
Northbound gRPC server. The SRv6 Manager implements different
control plane functionalities to setup SRv6 entities.
"""

# General imports
import logging
import os
from contextlib import contextmanager
from enum import Enum
# Proto dependencies
import nb_commons_pb2
import nb_srv6_manager_pb2
import nb_srv6_manager_pb2_grpc
# Controller dependencies
from controller import arangodb_driver
from controller import srv6_utils, srv6_usid, utils
from controller.nb_grpc_server import utils as nb_utils


# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)


# ############################################################################
# SRv6 Action
class SRv6Action(Enum):
    """
    SRv6 action.
    """
    UNSPEC = nb_commons_pb2.SRv6Action.Value('SRV6_ACTION_UNSPEC')
    END = nb_commons_pb2.SRv6Action.Value('END')
    END_X = nb_commons_pb2.SRv6Action.Value('END_X')
    END_T = nb_commons_pb2.SRv6Action.Value('END_T')
    END_DX4 = nb_commons_pb2.SRv6Action.Value('END_DX4')
    END_DX6 = nb_commons_pb2.SRv6Action.Value('END_DX6')
    END_DX2 = nb_commons_pb2.SRv6Action.Value('END_DX2')
    END_DT4 = nb_commons_pb2.SRv6Action.Value('END_DT4')
    END_DT6 = nb_commons_pb2.SRv6Action.Value('END_DT6')
    END_B6 = nb_commons_pb2.SRv6Action.Value('END_B6')
    END_B6_ENCAPS = nb_commons_pb2.SRv6Action.Value('END_B6_ENCAPS')


# Mapping python representation of SRv6 Action to gRPC representation
py_to_grpc_srv6_action = {
    '': SRv6Action.UNSPEC.value,
    'End': SRv6Action.END.value,
    'End.X': SRv6Action.END_X.value,
    'End.T': SRv6Action.END_T.value,
    'End.DX4': SRv6Action.END_DX4.value,
    'End.DX6': SRv6Action.END_DX6.value,
    'End.DX2': SRv6Action.END_DX2.value,
    'End.DT4': SRv6Action.END_DT4.value,
    'End.DT6': SRv6Action.END_DT6.value,
    'End.B6': SRv6Action.END_B6.value,
    'End.B6.Encaps': SRv6Action.END_B6_ENCAPS.value
}

# Mapping gRPC representation of SRv6 Action to python representation
grpc_to_py_srv6_action = {
    v: k for k, v in py_to_grpc_srv6_action.items()}


# ############################################################################
# Forwarding Engine
class FwdEngine(Enum):
    """
    Forwarding Engine.
    """
    UNSPEC = nb_commons_pb2.FwdEngine.Value('FWD_ENGINE_UNSPEC')
    LINUX = nb_commons_pb2.FwdEngine.Value('LINUX')
    VPP = nb_commons_pb2.FwdEngine.Value('VPP')


# Mapping python representation of Forwarding Engine to gRPC representation
py_to_grpc_fwd_engine = {
    '': FwdEngine.UNSPEC.value,
    'linux': FwdEngine.LINUX.value,
    'vpp': FwdEngine.VPP.value
}

# Mapping gRPC representation of Forwarding Engine to python representation
grpc_to_py_fwd_engine = {
    v: k for k, v in py_to_grpc_fwd_engine.items()}


# ############################################################################
# Encap Mode
class EncapMode(Enum):
    """
    Encap Mode.
    """
    UNSPEC = nb_commons_pb2.EncapMode.Value('ENCAP_MODE_UNSPEC')
    INLINE = nb_commons_pb2.EncapMode.Value('INLINE')
    ENCAP = nb_commons_pb2.EncapMode.Value('ENCAP')
    L2ENCAP = nb_commons_pb2.EncapMode.Value('L2ENCAP')


# Mapping python representation of Encap Mode to gRPC representation
py_to_grpc_encap_mode = {
    '': EncapMode.UNSPEC.value,
    'inline': EncapMode.INLINE.value,
    'encap': EncapMode.ENCAP.value,
    'l2encap': EncapMode.L2ENCAP.value
}

# Mapping gRPC representation of Encap Mode to python representation
grpc_to_py_encap_mode = {
    v: k for k, v in py_to_grpc_encap_mode.items()}


# ############################################################################
# gRPC server APIs


@contextmanager
def srv6_mgr_error_handling():
    """
    This function handles the exceptions that can be raised by SRv6 functions.
    """
    # Create reply message
    response = nb_srv6_manager_pb2.SRv6ManagerReply()
    try:
        # Set status code
        yield response
        # Operation completed successfully, set status code
        logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[
            nb_commons_pb2.STATUS_SUCCESS])
        response.status = nb_commons_pb2.STATUS_SUCCESS
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


class SRv6Manager(nb_srv6_manager_pb2_grpc.SRv6ManagerServicer):
    """
    gRPC request handler.
    """

    def __init__(self, db_client=None):
        """
        SRv6 Manager init method.

        :param db_client: ArangoDB client.
        :type db_client: class: `arango.client.ArangoClient`
        """
        # Establish a connection to the "srv6" database
        # We will keep the connection open forever
        self.db_conn = arangodb_driver.connect_db(
            client=db_client,
            db_name='srv6',
            username=os.getenv('ARANGO_USER'),
            password=os.getenv('ARANGO_PASSWORD')
        )

    def HandleSRv6MicroSIDPolicy(self, request, context):
        """
        Handle a SRv6 uSID policy.
        """
        # Extract "nodes_lr" from gRPC request
        nodes_lr = None
        if request.nodes_lr is not None:
            nodes_lr = list(request.nodes_lr)
        # Extract "nodes_rl" from gRPC request
        nodes_rl = None
        if request.nodes_rl is not None:
            nodes_rl = list(request.nodes_rl)
        # Handle SRv6 uSID policy
        res = srv6_usid.handle_srv6_usid_policy(
            operation=request.operation,
            lr_destination=request.lr_destination,
            rl_destination=request.rl_destination,
            nodes_lr=nodes_lr,
            nodes_rl=nodes_rl,
            table=request.table,
            metric=request.metric,
            _id=request._id,
            l_grpc_ip=request.l_grpc_ip,
            l_grpc_port=request.l_grpc_port,
            l_fwd_engine=grpc_to_py_fwd_engine[request.l_fwd_engine],
            r_grpc_ip=request.r_grpc_ip,
            r_grpc_port=request.r_grpc_port,
            r_fwd_engine=grpc_to_py_fwd_engine[request.r_fwd_engine],
            decap_sid=request.decap_sid,
            locator=request.locator,
            db_conn=self.db_conn
        )
        if res is not None:  # TODO replace status code with exceptions
            logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[res])
        # Create reply message
        response = nb_srv6_manager_pb2.SRv6ManagerReply()
        # Set status code
        response.status = nb_utils.sb_status_to_nb_status[res]
        # Done, return the reply
        return response

    def HandleSRv6Path(self, request, context):
        """
        Handle a SRv6 path.
        """
        # Iterate on the SRv6 paths
        srv6_paths = None
        for srv6_path in request.srv6_paths:
            # Perform the operation
            #
            # The "with" block is used to avoid duplicating the error handling
            # code
            with srv6_mgr_error_handling() as response:
                # Extract the encap mode
                encapmode = grpc_to_py_encap_mode[srv6_path.encapmode]
                # Extract the forwarding engine
                fwd_engine = grpc_to_py_fwd_engine[srv6_path.fwd_engine]
                if fwd_engine == 'FWD_ENGINE_UNSPEC':
                    fwd_engine = ''
                # Handle SRv6 path
                srv6_paths = srv6_utils.handle_srv6_path(
                    operation=srv6_path.operation,
                    grpc_address=srv6_path.grpc_address,
                    grpc_port=srv6_path.grpc_port,
                    destination=srv6_path.destination,
                    segments=list(srv6_path.segments),
                    device=srv6_path.device,
                    encapmode=encapmode,
                    table=srv6_path.table,
                    metric=srv6_path.metric,
                    bsid_addr=srv6_path.bsid_addr,
                    fwd_engine=fwd_engine,
                    key=srv6_path.key if srv6_path.key != '' else None,
                    db_conn=self.db_conn
                )
        # If an error occurred, return immediately
        if response.status != nb_commons_pb2.STATUS_SUCCESS:
            return response
        # Add the SRv6 paths to the response message
        if srv6_paths is not None:
            for path in srv6_paths:
                _srv6_path = response.srv6_paths.add()
                _srv6_path.grpc_address = path['grpc_address']
                _srv6_path.grpc_port = path['grpc_port']
                _srv6_path.destination = path['destination']
                _srv6_path.segments.extend(path['segments'])
                _srv6_path.encapmode = py_to_grpc_encap_mode[path['encapmode']]
                _srv6_path.device = path['device']
                _srv6_path.table = path['table']
                _srv6_path.metric = path['metric']
                _srv6_path.bsid_addr = path['bsid_addr']
                _srv6_path.fwd_engine = py_to_grpc_fwd_engine[path['fwd_engine']]
                if '_key' in path:
                    _srv6_path.key = path['_key']
        # Done, return the reply
        return response

    def HandleSRv6Behavior(self, request, context):
        """
        Handle a SRv6 behavior.
        """
        # Iterate on the SRv6 behaviors
        srv6_behaviors = None
        for srv6_behavior in request.srv6_behaviors:
            # Perform the operation
            #
            # The "with" block is used to avoid duplicating the error handling
            # code
            with srv6_mgr_error_handling() as response:
                # Extract the SRv6 action
                action = grpc_to_py_srv6_action[srv6_behavior.action]
                # Handle the behavior
                srv6_behaviors = srv6_utils.handle_srv6_behavior(
                    operation=srv6_behavior.operation,
                    grpc_address=srv6_behavior.grpc_address,
                    grpc_port=srv6_behavior.grpc_port,
                    segment=srv6_behavior.segment,
                    action=action,
                    device=srv6_behavior.device,
                    table=srv6_behavior.table,
                    nexthop=srv6_behavior.nexthop,
                    lookup_table=srv6_behavior.lookup_table,
                    interface=srv6_behavior.interface,
                    segments=list(srv6_behavior.segments),
                    metric=srv6_behavior.metric,
                    fwd_engine=grpc_to_py_fwd_engine[srv6_behavior.fwd_engine],
                    key=srv6_behavior.key if srv6_behavior.key != '' else None,
                    db_conn=self.db_conn
                )
        # If an error occurred, return immediately
        if response.status != nb_commons_pb2.STATUS_SUCCESS:
            return response
        # Add the SRv6 behaviors to the response message
        if srv6_behaviors is not None:
            for behavior in srv6_behaviors:
                _srv6_behavior = response.srv6_behaviors.add()
                _srv6_behavior.grpc_address = behavior['grpc_address']
                _srv6_behavior.grpc_port = behavior['grpc_port']
                _srv6_behavior.segment = behavior['segment']
                _srv6_behavior.action = py_to_grpc_srv6_action[behavior['action']]
                _srv6_behavior.nexthop = behavior['nexthop']
                _srv6_behavior.lookup_table = behavior['lookup_table']
                _srv6_behavior.interface = behavior['interface']
                _srv6_behavior.segments.extend(behavior['segments'])
                _srv6_behavior.device = behavior['device']
                _srv6_behavior.table = behavior['table']
                _srv6_behavior.metric = behavior['metric']
                _srv6_behavior.fwd_engine = py_to_grpc_fwd_engine[behavior['fwd_engine']]
                if '_key' in behavior:
                    _srv6_behavior.key = behavior['_key']
        # Done, return the reply
        return response

    def HandleSRv6UniTunnel(self, request, context):
        """
        Handle a SRv6 unidirectional tunnel.
        """
        # Create reply message
        response = nb_srv6_manager_pb2.SRv6ManagerReply()
        # Perform the operation
        srv6_tunnels = None
        for srv6_tunnel in request.srv6_unitunnels:
            # The "with" block is used to avoid duplicating the error handling
            # code
            with srv6_mgr_error_handling() as response:
                srv6_tunnels = None
                fwd_engine = grpc_to_py_fwd_engine[srv6_tunnel.fwd_engine]
                if srv6_tunnel.operation == 'add':
                    srv6_utils.create_uni_srv6_tunnel(
                        ingress_ip=srv6_tunnel.ingress_ip,
                        ingress_port=srv6_tunnel.ingress_port,
                        egress_ip=srv6_tunnel.egress_ip,
                        egress_port=srv6_tunnel.egress_port,
                        destination=srv6_tunnel.destination,
                        segments=list(srv6_tunnel.segments),
                        localseg=srv6_tunnel.localseg,
                        bsid_addr=srv6_tunnel.bsid_addr,
                        fwd_engine=grpc_to_py_fwd_engine[srv6_tunnel.fwd_engine],
                        key=srv6_tunnel.key if srv6_tunnel.key != '' else None,
                        db_conn=self.db_conn
                    )
                    logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[nb_commons_pb2.STATUS_SUCCESS])
                elif srv6_tunnel.operation == 'del':
                    srv6_utils.destroy_uni_srv6_tunnel(
                        ingress_ip=srv6_tunnel.ingress_ip,
                        ingress_port=srv6_tunnel.ingress_port,
                        egress_ip=srv6_tunnel.egress_ip,
                        egress_port=srv6_tunnel.egress_port,
                        destination=srv6_tunnel.destination,
                        localseg=srv6_tunnel.localseg,
                        bsid_addr=srv6_tunnel.bsid_addr,
                        fwd_engine=grpc_to_py_fwd_engine[srv6_tunnel.fwd_engine],
                        key=srv6_tunnel.key if srv6_tunnel.key != '' else None,
                        db_conn=self.db_conn
                    )
                    logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[nb_commons_pb2.STATUS_SUCCESS])
                elif srv6_tunnel.operation == 'get':
                    srv6_tunnels = srv6_utils.get_uni_srv6_tunnel(
                        ingress_ip=srv6_tunnel.ingress_ip,
                        ingress_port=srv6_tunnel.ingress_port,
                        egress_ip=srv6_tunnel.egress_ip,
                        egress_port=srv6_tunnel.egress_port,
                        destination=srv6_tunnel.destination if srv6_tunnel.destination != '' else None,
                        segments=list(srv6_tunnel.segments) if srv6_tunnel.segments != [''] else None,
                        localseg=srv6_tunnel.localseg if srv6_tunnel.localseg != '' else None,
                        bsid_addr=srv6_tunnel.bsid_addr if srv6_tunnel.localseg != '' else None,
                        fwd_engine=grpc_to_py_fwd_engine[srv6_tunnel.fwd_engine] if srv6_tunnel.fwd_engine != '' else None,
                        key=srv6_tunnel.key if srv6_tunnel.key != '' else None,
                        db_conn=self.db_conn
                    )
                    logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[nb_commons_pb2.STATUS_SUCCESS])
                else:
                    logger.error('Invalid operation %s', srv6_tunnel.operation)
                    # Set status code
                    response.status = \
                        nb_commons_pb2.STATUS_OPERATION_NOT_SUPPORTED
                    return response
        # If an error occurred, return immediately
        if response.status != nb_commons_pb2.STATUS_SUCCESS:
            return response
        # Add the SRv6 behaviors to the response message
        if srv6_tunnels is not None:
            for tunnel in srv6_tunnels:
                _srv6_unitunnel = response.srv6_unitunnels.add()
                _srv6_unitunnel.ingress_ip = tunnel['l_grpc_address']
                _srv6_unitunnel.ingress_port = tunnel['l_grpc_port']
                _srv6_unitunnel.egress_ip = tunnel['r_grpc_address']
                _srv6_unitunnel.egress_port = tunnel['r_grpc_port']
                _srv6_unitunnel.destination = tunnel['dest_lr']
                _srv6_unitunnel.segments.extend(tunnel['sidlist_lr'])
                _srv6_unitunnel.localseg = tunnel['localseg_lr']
                _srv6_unitunnel.bsid_addr = tunnel['bsid_addr']
                _srv6_unitunnel.fwd_engine = py_to_grpc_fwd_engine[tunnel['fwd_engine']]
                if '_key' in tunnel:
                    _srv6_unitunnel.key = tunnel['_key']
        # Done, return the reply
        return response

    def HandleSRv6BidiTunnel(self, request, context):
        """
        Handle SRv6 bidirectional tunnel.
        """
        # Create reply message
        response = nb_srv6_manager_pb2.SRv6ManagerReply()
        # Perform the operation
        srv6_tunnels = None
        for srv6_tunnel in request.srv6_biditunnels:
            # The "with" block is used to avoid duplicating the error handling
            # code
            with srv6_mgr_error_handling() as response:
                srv6_tunnels = None
                fwd_engine = grpc_to_py_fwd_engine[srv6_tunnel.fwd_engine]
                if srv6_tunnel.operation == 'add':
                    srv6_utils.create_srv6_tunnel(
                        node_l_ip=srv6_tunnel.node_l_ip,
                        node_l_port=srv6_tunnel.node_l_port,
                        node_r_ip=srv6_tunnel.node_r_ip,
                        node_r_port=srv6_tunnel.node_r_port,
                        sidlist_lr=list(srv6_tunnel.sidlist_lr),
                        sidlist_rl=list(srv6_tunnel.sidlist_rl),
                        dest_lr=srv6_tunnel.dest_lr,
                        dest_rl=srv6_tunnel.dest_rl,
                        localseg_lr=srv6_tunnel.localseg_lr,
                        localseg_rl=srv6_tunnel.localseg_rl,
                        bsid_addr=srv6_tunnel.bsid_addr,
                        fwd_engine=grpc_to_py_fwd_engine[srv6_tunnel.fwd_engine],
                        key=srv6_tunnel.key if srv6_tunnel.key != '' else None,
                        db_conn=self.db_conn
                    )
                    logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[nb_commons_pb2.STATUS_SUCCESS])
                elif srv6_tunnel.operation == 'del':
                    srv6_utils.destroy_srv6_tunnel(
                        node_l_ip=srv6_tunnel.node_l_ip,
                        node_l_port=srv6_tunnel.node_l_port,
                        node_r_ip=srv6_tunnel.node_r_ip,
                        node_r_port=srv6_tunnel.node_r_port,
                        dest_lr=srv6_tunnel.dest_lr,
                        dest_rl=srv6_tunnel.dest_rl,
                        localseg_lr=srv6_tunnel.localseg_lr,
                        localseg_rl=srv6_tunnel.localseg_rl,
                        bsid_addr=srv6_tunnel.bsid_addr,
                        fwd_engine=grpc_to_py_fwd_engine[srv6_tunnel.fwd_engine],
                        key=srv6_tunnel.key if srv6_tunnel.key != '' else None,
                        db_conn=self.db_conn
                    )
                    logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[nb_commons_pb2.STATUS_SUCCESS])
                elif srv6_tunnel.operation == 'get':
                    srv6_tunnels = srv6_utils.get_srv6_tunnel(
                        node_l_ip=srv6_tunnel.node_l_ip,
                        node_l_port=srv6_tunnel.node_l_port,
                        node_r_ip=srv6_tunnel.node_r_ip,
                        node_r_port=srv6_tunnel.node_r_port,
                        sidlist_lr=list(srv6_tunnel.sidlist_lr) if srv6_tunnel.sidlist_lr != [''] else None,
                        sidlist_rl=list(srv6_tunnel.sidlist_rl) if srv6_tunnel.sidlist_rl != [''] else None,
                        dest_lr=srv6_tunnel.dest_lr if srv6_tunnel.dest_lr != '' else None,
                        dest_rl=srv6_tunnel.dest_rl if srv6_tunnel.dest_rl != '' else None,
                        localseg_lr=srv6_tunnel.localseg_lr if srv6_tunnel.localseg_lr != '' else None,
                        localseg_rl=srv6_tunnel.localseg_rl if srv6_tunnel.localseg_rl != '' else None,
                        bsid_addr=srv6_tunnel.bsid_addr if srv6_tunnel.bsid_addr != '' else None,
                        fwd_engine=srv6_tunnel.fwd_engine if srv6_tunnel.fwd_engine != '' else None,
                        key=srv6_tunnel.key if srv6_tunnel.key != '' else None,
                        db_conn=self.db_conn
                    )
                    logger.debug('%s\n\n', utils.STATUS_CODE_TO_DESC[nb_commons_pb2.STATUS_SUCCESS])
                else:
                    logger.error('Invalid operation %s', srv6_tunnel.operation)
                    # Set status code
                    response.status = \
                        nb_commons_pb2.STATUS_OPERATION_NOT_SUPPORTED
                    return response
        # If an error occurred, return immediately
        if response.status != nb_commons_pb2.STATUS_SUCCESS:
            return response
        # Add the SRv6 behaviors to the response message
        if srv6_tunnels is not None:
            for tunnel in srv6_tunnels:
                _srv6_biditunnel = response.srv6_biditunnels.add()
                _srv6_biditunnel.node_l_ip = tunnel['l_grpc_address']
                _srv6_biditunnel.node_l_port = tunnel['l_grpc_port']
                _srv6_biditunnel.node_r_ip = tunnel['node_r_ip']
                _srv6_biditunnel.node_r_port = tunnel['node_r_port']
                _srv6_biditunnel.dest_lr = tunnel['dest_lr']
                _srv6_biditunnel.dest_rl = tunnel['dest_rl']
                _srv6_biditunnel.sidlist_lr.extend(tunnel['sidlist_lr'])
                _srv6_biditunnel.sidlist_rl.extend(tunnel['sidlist_rl'])
                _srv6_biditunnel.localseg_lr = tunnel['localseg_lr']
                _srv6_biditunnel.localseg_rl = tunnel['localseg_rl']
                _srv6_biditunnel.bsid_addr = tunnel['bsid_addr']
                if '_key' in tunnel:
                    _srv6_biditunnel.key = tunnel['_key']
                _srv6_biditunnel.fwd_engine = py_to_grpc_fwd_engine[tunnel['fwd_engine']]
        # Done, return the reply
        return response
