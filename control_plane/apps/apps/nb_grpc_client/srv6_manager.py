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
# Implementation of SRv6 Manager for the Northbound gRPC client
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


"""
This module provides an implementation of a SRv6 Manager for the Northbound
gRPC client.
"""

# General imports
import logging
from enum import Enum
# Proto dependencies
import nb_commons_pb2
import nb_srv6_manager_pb2
import nb_srv6_manager_pb2_grpc
# gRPC client dependencies
from apps.nb_grpc_client import utils


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
    END_DT46 = nb_commons_pb2.SRv6Action.Value('END_DT46')

# Mapping python representation of SRv6 Action to gRPC representation
py_to_grpc_srv6_action = {
    'unspec': SRv6Action.UNSPEC.value,
    'End': SRv6Action.END.value,
    'End.X': SRv6Action.END_X.value,
    'End.T': SRv6Action.END_T.value,
    'End.DX4': SRv6Action.END_DX4.value,
    'End.DX6': SRv6Action.END_DX6.value,
    'End.DX2': SRv6Action.END_DX2.value,
    'End.DT4': SRv6Action.END_DT4.value,
    'End.DT6': SRv6Action.END_DT6.value,
    'End.B6': SRv6Action.END_B6.value,
    'End.B6.Encaps': SRv6Action.END_B6_ENCAPS.value,
    'End.DT46': SRv6Action.END_DT46.value
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
    'unspec': FwdEngine.UNSPEC.value,
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
    'unspec': EncapMode.UNSPEC.value,
    'inline': EncapMode.INLINE.value,
    'encap': EncapMode.ENCAP.value,
    'l2encap': EncapMode.L2ENCAP.value
}

# Mapping gRPC representation of Encap Mode to python representation
grpc_to_py_encap_mode = {
    v: k for k, v in py_to_grpc_encap_mode.items()}


# ############################################################################
# gRPC client APIs


def handle_srv6_usid_policy(controller_channel, operation,
                            lr_destination, rl_destination, nodes_lr=None,
                            nodes_rl=None, table=-1, metric=-1, _id=None,
                            l_grpc_ip=None, l_grpc_port=None,
                            l_fwd_engine=None, r_grpc_ip=None,
                            r_grpc_port=None, r_fwd_engine=None,
                            decap_sid=None, locator=None):
    """
    Handle a SRv6 uSID policy.
    """
    # pylint: disable=too-many-arguments
    #
    # Create request message
    request = nb_srv6_manager_pb2.SRv6MicroSIDRequest()
    # Create a policy
    micro_sid = request.srv6_micro_sids.add()
    # Set the operation
    micro_sid.operation = operation
    # Set the destination for the left to right path
    micro_sid.lr_destination = lr_destination
    # Set the destination for the right to left path
    micro_sid.rl_destination = rl_destination
    # Set the waypoints list for the left to right path
    micro_sid.nodes_lr.extend(nodes_lr)
    # Set the waypoints list for the right to left path
    micro_sid.nodes_rl.extend(nodes_rl)
    # Set the table ID
    micro_sid.table = table
    # Set the metric
    micro_sid.metric = metric
    # Set the entity ID
    micro_sid._id = _id
    # Set the gRPC address of the left node
    micro_sid.l_grpc_ip = l_grpc_ip
    # Set the gRPC port number of the left node
    micro_sid.l_grpc_port = l_grpc_port
    # Set the forwarding engine of the left node
    if l_fwd_engine not in py_to_grpc_fwd_engine:
        # Invalid forwarding engine
        logger.error('Invalid forwarding engine: %s', l_fwd_engine)
        raise utils.InvalidArgumentError
    micro_sid.l_fwd_engine = py_to_grpc_fwd_engine[l_fwd_engine]
    # Set the gRPC address of the right node
    micro_sid.r_grpc_ip = r_grpc_ip
    # Set the gRPC port number of the right node
    micro_sid.r_grpc_port = r_grpc_port
    # Set the forwarding engine of the right node
    if r_fwd_engine not in py_to_grpc_fwd_engine:
        # Invalid forwarding engine
        logger.error('Invalid forwarding engine: %s', r_fwd_engine)
        raise utils.InvalidArgumentError
    micro_sid.r_fwd_engine = py_to_grpc_fwd_engine[r_fwd_engine]
    # Set the decapsulation SID
    micro_sid.decap_sid = decap_sid
    # Set the locator
    micro_sid.locator = locator
    # Request message is ready
    #
    # Get the reference of the stub
    stub = nb_srv6_manager_pb2_grpc.SRv6ManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.HandleSRv6MicroSIDPolicy(request)
    # Check the status code and raise an exception if an error occurred
    utils.raise_exception_on_error(response.status)
    # Done, return the list of uSIDs, if any
    return list(response.srv6_micro_sids)


def handle_srv6_path(controller_channel, operation, grpc_address, grpc_port=-1,
                     destination='', segments="", device='', encapmode="encap",
                     table=-1, metric=-1, bsid_addr='', fwd_engine='linux',
                     key=''):
    """
    Handle a SRv6 path.
    """
    # pylint: disable=too-many-arguments
    #
    # Create request message
    request = nb_srv6_manager_pb2.SRv6PathRequest()
    # Create a SRv6 path
    srv6_path = request.srv6_paths.add()
    # Set the operation
    srv6_path.operation = operation
    # Set the gRPC address
    if grpc_address is not None:
        srv6_path.grpc_address = grpc_address
    # Set the gRPC port
    if grpc_port is not None:
        srv6_path.grpc_port = grpc_port
    # Set the destination
    if destination is not None:
        srv6_path.destination = destination
    # Set the segments
    srv6_path.segments.extend(segments)
    # Set the device
    srv6_path.device = device
    # Set the encap mode
    if encapmode == '':
        srv6_path.encapmode = EncapMode.UNSPEC.value
    else:
        if encapmode not in py_to_grpc_encap_mode:
            # Invalid encap mode
            logger.error('Invalid encap mode: %s', encapmode)
            raise utils.InvalidArgumentError
        srv6_path.encapmode = py_to_grpc_encap_mode[encapmode]
    # Set the table ID
    srv6_path.table = table
    # Set the metric
    srv6_path.metric = metric
    # Set the BSID address
    srv6_path.bsid_addr = bsid_addr
    # Set the forwarding engine
    if encapmode == '':
        srv6_path.fwd_engine = FwdEngine.UNSPEC.value
    else:
        if fwd_engine not in py_to_grpc_fwd_engine:
            # Invalid forwarding engine
            logger.error('Invalid forwarding engine: %s', fwd_engine)
            raise utils.InvalidArgumentError
        srv6_path.fwd_engine = py_to_grpc_fwd_engine[fwd_engine]
    # Set the key
    srv6_path.key = key
    # Request message is ready
    #
    # Get the reference of the stub
    stub = nb_srv6_manager_pb2_grpc.SRv6ManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.HandleSRv6Path(request)
    # Check the status code and raise an exception if an error occurred
    utils.raise_exception_on_error(response.status)
    # Extract the SRv6 paths from the response message, if any
    srv6_paths = []
    for srv6_path in response.srv6_paths:
        srv6_paths.append({
            'grpc_address': srv6_path.grpc_address,
            'grpc_port': srv6_path.grpc_port,
            'destination': srv6_path.destination,
            'segments': srv6_path.segments,
            'device': srv6_path.device,
            'encapmode': encapmode,
            'table': srv6_path.table,
            'metric': srv6_path.metric,
            'bsid_addr': srv6_path.bsid_addr,
            'fwd_engine': srv6_path.fwd_engine,
            'key': srv6_path.key
        })
    # Done, return the list of SRv6 paths
    return srv6_paths


def handle_srv6_behavior(controller_channel, operation, grpc_address,
                         grpc_port, segment, action='', device='',
                         table=-1, nexthop="", lookup_table=-1, interface="",
                         segments="", metric=-1, fwd_engine='linux', key=''):
    """
    Handle a SRv6 behavior.
    """
    # pylint: disable=too-many-arguments
    #
    # Create request message
    request = nb_srv6_manager_pb2.SRv6BehaviorRequest()
    # Create a SRv6 behavior
    srv6_behavior = request.srv6_behaviors.add()
    # Set the operation
    srv6_behavior.operation = operation
    # Set the gRPC address
    srv6_behavior.grpc_address = grpc_address
    # Set the gRPC port
    srv6_behavior.grpc_port = grpc_port
    # Set the segment
    srv6_behavior.segment = segment
    # Set the action
    if action == '':
        srv6_behavior.action = SRv6Action.UNSPEC.value
    else:
        if action not in py_to_grpc_srv6_action:
            # Invalid SRv6 action
            logger.error('Invalid SRv6 action: %s', action)
            raise utils.InvalidArgumentError
        srv6_behavior.action = py_to_grpc_srv6_action[action]
    # Set the device
    srv6_behavior.device = device
    # Set the table ID
    srv6_behavior.table = table
    # Set the nexthop
    srv6_behavior.nexthop = nexthop
    # Set the lookup table
    srv6_behavior.lookup_table = lookup_table
    # Set the interface
    srv6_behavior.interface = interface
    # Set the segments
    srv6_behavior.segments.extend(segments)
    # Set the metric
    srv6_behavior.metric = metric
    # Set the forwarding engine
    if fwd_engine not in py_to_grpc_fwd_engine:
        # Invalid forwarding engine
        logger.error('Invalid forwarding engine: %s', fwd_engine)
        raise utils.InvalidArgumentError
    srv6_behavior.fwd_engine = py_to_grpc_fwd_engine[fwd_engine]
    # Set the key
    srv6_behavior.key = key
    # Request message is ready
    #
    # Get the reference of the stub
    stub = nb_srv6_manager_pb2_grpc.SRv6ManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.HandleSRv6Behavior(request)
    # Check the status code and raise an exception if an error occurred
    utils.raise_exception_on_error(response.status)
    # Extract the SRv6 behaviors from the response message, if any
    srv6_behaviors = []
    for srv6_behavior in response.srv6_behaviors:
        srv6_behaviors.append({
            'grpc_address': srv6_behavior.grpc_address,
            'grpc_port': srv6_behavior.grpc_port,
            'segment': srv6_behavior.segment,
            'action': srv6_behavior.action,
            'device': srv6_behavior.device,
            'table': srv6_behavior.table,
            'nexthop': srv6_behavior.nexthop,
            'lookup_table': srv6_behavior.lookup_table,
            'interface': srv6_behavior.interface,
            'segments': srv6_behavior.segments,
            'metric': srv6_behavior.metric,
            'fwd_engine': srv6_behavior.fwd_engine,
            'key': srv6_behavior.key
        })
    # Done, return the list of SRv6 behaviors, if any
    return srv6_behaviors


def handle_srv6_unitunnel(controller_channel, operation, ingress_ip,
                          ingress_port, egress_ip, egress_port,
                          destination, segments=None, localseg=None,
                          bsid_addr='', fwd_engine='linux', key=''):
    """
    Handle a SRv6 unidirectional tunnel.
    """
    # pylint: disable=too-many-arguments
    #
    # Create request message
    request = nb_srv6_manager_pb2.SRv6UniTunnelRequest()
    # Create a SRv6 behavior
    srv6_unitunnel = request.srv6_unitunnels.add()
    # Set the operation
    srv6_unitunnel.operation = operation
    # Set the gRPC IP address of the ingress node
    srv6_unitunnel.ingress_ip = ingress_ip
    # Set the gRPC port number of the ingress node
    srv6_unitunnel.ingress_port = ingress_port
    # Set the gRPC IP adress of the egress node
    srv6_unitunnel.egress_ip = egress_ip
    # Set the gRPC port number of the egress node
    srv6_unitunnel.egress_port = egress_port
    # Set the destination
    srv6_unitunnel.destination = destination
    # Set the segments
    if segments is not None:
        srv6_unitunnel.segments.extend(segments)
    # Set the local segment
    if localseg is not None:
        srv6_unitunnel.localseg = localseg
    # Set the BSID address
    srv6_unitunnel.bsid_addr = bsid_addr
    # Set the forwarding engine
    if fwd_engine not in py_to_grpc_fwd_engine:
        # Invalid forwarding engine
        logger.error('Invalid forwarding engine: %s', fwd_engine)
        raise utils.InvalidArgumentError
    srv6_unitunnel.fwd_engine = py_to_grpc_fwd_engine[fwd_engine]
    # Set the key
    srv6_unitunnel.key = key
    # Request message is ready
    #
    # Get the reference of the stub
    stub = nb_srv6_manager_pb2_grpc.SRv6ManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.HandleSRv6UniTunnel(request)
    # Check the status code and raise an exception if an error occurred
    utils.raise_exception_on_error(response.status)
    # Extract the SRv6 tunnels from the response message, if any
    srv6_tunnels = []
    for srv6_tunnel in response.srv6_unitunnels:
        srv6_tunnels.append({
            'ingress_ip': srv6_tunnel.ingress_ip,
            'ingress_port': srv6_tunnel.ingress_port,
            'egress_ip': srv6_tunnel.egress_ip,
            'egress_port': srv6_tunnel.egress_port,
            'destination': srv6_tunnel.destination,
            'segments': srv6_tunnel.segments,
            'bsid_addr': srv6_tunnel.bsid_addr,
            'fwd_engine': srv6_tunnel.fwd_engine,
            'key': srv6_tunnel.key
        })
    # Done, return the list of SRv6 unidirectional tunnels, if any
    return srv6_tunnels


def handle_srv6_biditunnel(controller_channel, operation, node_l_ip,
                           node_l_port, node_r_ip, node_r_port,
                           dest_lr, dest_rl, sidlist_lr=None, sidlist_rl=None,
                           localseg_lr=None, localseg_rl=None,
                           bsid_addr='', fwd_engine='linux', key=''):
    """
    Handle SRv6 bidirectional tunnel.
    """
    # pylint: disable=too-many-arguments,too-many-locals
    #
    # Create request message
    request = nb_srv6_manager_pb2.SRv6BidiTunnelRequest()
    # Create a SRv6 behavior
    srv6_biditunnel = request.srv6_biditunnels.add()
    # Set the operation
    srv6_biditunnel.operation = operation
    # Set the gRPC address of the left node
    srv6_biditunnel.node_l_ip = node_l_ip
    # Set the port number of the left node
    srv6_biditunnel.node_l_port = node_l_port
    # Set the gRPC address of the right node
    srv6_biditunnel.node_r_ip = node_r_ip
    # Set the port number of the right node
    srv6_biditunnel.node_r_port = node_r_port
    # SID list of the path left to right
    if sidlist_lr is not None:
        srv6_biditunnel.sidlist_lr.extend(sidlist_lr)
    # SID list of the path right to left
    if sidlist_rl is not None:
        srv6_biditunnel.sidlist_rl.extend(sidlist_rl)
    # Destination of the path left to right
    srv6_biditunnel.dest_lr = dest_lr
    # Destinaton of the path right to left
    srv6_biditunnel.dest_rl = dest_rl
    # Local segment of the path left to right
    if localseg_lr is not None:
        srv6_biditunnel.localseg_lr = localseg_lr
    # Local segment of the path right to left
    if localseg_rl is not None:
        srv6_biditunnel.localseg_rl = localseg_rl
    # BSID address
    srv6_biditunnel.bsid_addr = bsid_addr
    # Forwarding engine
    if fwd_engine not in py_to_grpc_fwd_engine:
        # Invalid forwarding engine
        logger.error('Invalid forwarding engine: %s', fwd_engine)
        raise utils.InvalidArgumentError
    srv6_biditunnel.fwd_engine = py_to_grpc_fwd_engine[fwd_engine]
    # Set the key
    srv6_biditunnel.key = key
    # Request message is ready
    #
    # Get the reference of the stub
    stub = nb_srv6_manager_pb2_grpc.SRv6ManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.HandleSRv6BidiTunnel(request)
    # Check the status code and raise an exception if an error occurred
    utils.raise_exception_on_error(response.status)
    # Extract the SRv6 tunnels from the response message, if any
    srv6_tunnels = []
    for srv6_tunnel in response.srv6_biditunnels:
        srv6_tunnels.append({
            'node_l_ip': srv6_tunnel.node_l_ip,
            'node_r_ip': srv6_tunnel.node_r_ip,
            'node_l_port': srv6_tunnel.node_l_port,
            'node_r_port': srv6_tunnel.node_r_port,
            'sidlist_lr': srv6_tunnel.sidlist_lr,
            'sidlist_rl': srv6_tunnel.sidlist_rl,
            'dest_lr': srv6_tunnel.dest_lr,
            'dest_rl': srv6_tunnel.dest_rl,
            'localseg_lr': srv6_tunnel.localseg_lr,
            'localseg_rl': srv6_tunnel.localseg_rl,
            'bsid_addr': srv6_tunnel.bsid_addr,
            'fwd_engine': srv6_tunnel.fwd_engine,
            'key': srv6_tunnel.key
        })
    # Done, return the list of SRv6 bidirectional tunnels, if any
    return srv6_tunnels
