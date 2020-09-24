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


'''
This module provides an implementation of a SRv6 Manager for the Northbound
gRPC client.
'''

# General imports

# Controller dependencies
import nb_commons_pb2
import nb_srv6_manager_pb2
import nb_srv6_manager_pb2_grpc


def handle_srv6_usid_policy(controller_channel, operation, nodes_dict,
                            lr_destination, rl_destination, nodes_lr=None,
                            nodes_rl=None, table=-1, metric=-1, _id=None,
                            l_grpc_ip=None, l_grpc_port=None,
                            l_fwd_engine=None, r_grpc_ip=None,
                            r_grpc_port=None, r_fwd_engine=None,
                            decap_sid=None, locator=None):
    '''
    Handle a SRv6 uSID policy.
    '''
    # pylint: disable=too-many-arguments
    #
    # Create request message
    request = nb_srv6_manager_pb2.SRv6MicroSIDRequest()
    # Set the operation
    request.operation = operation
    # Set the destination for the left to right path
    request.lr_destination = lr_destination
    # Set the destination for the right to left path
    request.rl_destination = rl_destination
    # Set the waypoints list for the left to right path
    request.nodes_lr.extend(nodes_lr)
    # Set the waypoints list for the right to left path
    request.nodes_rl.extend(nodes_rl)
    # Set the table ID
    request.table = table
    # Set the metric
    request.metric = metric
    # Set the entity ID
    request._id = _id
    # Set the gRPC address of the left node
    request.l_grpc_ip = l_grpc_ip
    # Set the gRPC port number of the left node
    request.l_grpc_port = l_grpc_port
    # Set the forwarding engine of the left node
    request.l_fwd_engine = nb_srv6_manager_pb2.Value(l_fwd_engine)
    # Set the gRPC address of the right node
    request.r_grpc_ip = r_grpc_ip
    # Set the gRPC port number of the right node
    request.r_grpc_port = r_grpc_port
    # Set the forwarding engine of the right node
    request.r_fwd_engine = nb_srv6_manager_pb2.Value(r_fwd_engine)
    # Set the decapsulation SID
    request.decap_sid = decap_sid
    # Set the locator
    request.locator = locator
    # Set the nodes configuration
    request.nodes_config = None     # TODO
    #
    # Get the reference of the stub
    stub = nb_srv6_manager_pb2_grpc.SRv6ManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.HandleSRv6MicroSIDPolicy(request)
    # Check the status code
    if response.status != nb_commons_pb2.STATUS_SUCCESS:
        return False       # TODO raise an exception?
    # Done, success
    return True


def handle_srv6_path(controller_channel, operation, grpc_address, grpc_port,
                     destination, segments="", device='', encapmode="encap",
                     table=-1, metric=-1, bsid_addr='', fwd_engine='Linux'):
    '''
    Handle a SRv6 path.
    '''
    # pylint: disable=too-many-arguments
    #
    # Create request message
    request = nb_srv6_manager_pb2.SRv6PathRequest()
    # Set the operation
    request.operation = operation
    # Set the gRPC address
    request.grpc_address = grpc_address
    # Set the gRPC port
    request.grpc_port = grpc_port
    # Set the destination
    request.destination = destination
    # Set the segments
    request.segments.extend(segments)
    # Set the device
    request.device = device
    # Set the encap mode
    request.encapmode = nb_srv6_manager_pb2.Value(encapmode)
    # Set the table ID
    request.table = table
    # Set the metric
    request.metric = metric
    # Set the BSID address
    request.bsid_addr = bsid_addr
    # Set the forwarding engine
    request.fwd_engine = nb_srv6_manager_pb2.Value(fwd_engine)
    #
    # Get the reference of the stub
    stub = nb_srv6_manager_pb2_grpc.SRv6ManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.HandleSRv6Path(request)
    # Check the status code
    if response.status != nb_commons_pb2.STATUS_SUCCESS:
        return False       # TODO raise an exception?
    # Done, success
    return True


def handle_srv6_behavior(controller_channel, operation, grpc_address,
                         grpc_port, segment, action='', device='',
                         table=-1, nexthop="", lookup_table=-1, interface="",
                         segments="", metric=-1, fwd_engine='Linux'):
    '''
    Handle a SRv6 behavior.
    '''
    # pylint: disable=too-many-arguments
    #
    # Create request message
    request = nb_srv6_manager_pb2.SRv6BehaviorRequest()
    # Set the operation
    request.operation = operation
    # Set the gRPC address
    request.grpc_address = grpc_address
    # Set the gRPC port
    request.grpc_port = grpc_port
    # Set the segment
    request.segment = segment
    # Set the action
    request.action = nb_srv6_manager_pb2.Value(action)
    # Set the device
    request.device = device
    # Set the table ID
    request.table = table
    # Set the nexthop
    request.nexthop = nexthop
    # Set the lookup table
    request.lookup_table = lookup_table
    # Set the interface
    request.interface = interface
    # Set the segments
    request.segments.extend(segments)
    # Set the metric
    request.metric = metric
    # Set the forwarding engine
    request.fwd_engine = nb_srv6_manager_pb2.Value(fwd_engine)
    #
    # Get the reference of the stub
    stub = nb_srv6_manager_pb2_grpc.SRv6ManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.HandleSRv6Behavior(request)
    # Check the status code
    if response.status != nb_commons_pb2.STATUS_SUCCESS:
        return False       # TODO raise an exception?
    # Done, success
    return True


def handle_srv6_unitunnel(controller_channel, operation, ingress_ip,
                          ingress_port, egress_ip, egress_port,
                          destination, segments, localseg=None,
                          bsid_addr='', fwd_engine='Linux'):
    '''
    Handle a SRv6 unidirectional tunnel.
    '''
    # pylint: disable=too-many-arguments
    #
    # Create request message
    request = nb_srv6_manager_pb2.SRv6UniTunnelRequest()
    # Set the operation
    request.operation = operation
    # Set the gRPC IP address of the ingress node
    request.ingress_ip = ingress_ip
    # Set the gRPC port number of the ingress node
    request.ingress_port = ingress_port
    # Set the gRPC IP adress of the egress node
    request.egress_ip = egress_ip
    # Set the gRPC port number of the egress node
    request.egress_port = egress_port
    # Set the destination
    request.destination = destination
    # Set the segments
    request.segments.extend(segments)
    # Set the local segment
    request.localseg = localseg
    # Set the BSID address
    request.bsid_addr = bsid_addr
    # Set the forwarding engine
    request.fwd_engine = nb_srv6_manager_pb2.Value(fwd_engine)
    #
    # Get the reference of the stub
    stub = nb_srv6_manager_pb2_grpc.SRv6ManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.HandleSRv6UniTunnel(request)
    # Check the status code
    if response.status != nb_commons_pb2.STATUS_SUCCESS:
        return False       # TODO raise an exception?
    # Done, success
    return True


def handle_srv6_biditunnel(controller_channel, operation, node_l_ip,
                           node_l_port, node_r_ip, node_r_port,
                           sidlist_lr, sidlist_rl, dest_lr, dest_rl,
                           localseg_lr=None, localseg_rl=None,
                           bsid_addr='', fwd_engine='Linux'):
    '''
    Handle SRv6 bidirectional tunnel.
    '''
    # pylint: disable=too-many-arguments,too-many-locals
    #
    # Create request message
    request = nb_srv6_manager_pb2.SRv6BidiTunnelRequest()
    # Set the operation
    request.operation = operation
    # Set the gRPC address of the left node
    request.node_l_ip = node_l_ip
    # Set the port number of the left node
    request.node_l_port = node_l_port
    # Set the gRPC address of the right node
    request.node_r_ip = node_r_ip
    # Set the port number of the right node
    request.node_r_port = node_r_port
    # SID list of the path left to right
    request.sidlist_lr.extend(sidlist_lr)
    # SID list of the path right to left
    request.sidlist_rl.extend(sidlist_rl)
    # Destination of the path left to right
    request.dest_lr = dest_lr
    # Destinaton of the path right to left
    request.dest_rl = dest_rl
    # Local segment of the path left to right
    request.localseg_lr = localseg_lr
    # Local segment of the path right to left
    request.localseg_rl = localseg_rl
    # BSID address
    request.bsid_addr = bsid_addr
    # Forwarding engine
    request.fwd_engine = nb_srv6_manager_pb2.Value(fwd_engine)
    #
    # Get the reference of the stub
    stub = nb_srv6_manager_pb2_grpc.SRv6ManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.HandleSRv6BidiTunnel(request)
    # Check the status code
    if response.status != nb_commons_pb2.STATUS_SUCCESS:
        return False       # TODO raise an exception?
    # Done, success
    return True


def get_nodes(controller_channel):
    '''
    Print nodes.
    '''
    #
    # Create request message
    request = nb_srv6_manager_pb2.EmptyRequest()
    #
    # Get the reference of the stub
    stub = nb_srv6_manager_pb2_grpc.SRv6ManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.GetNodes(request)
    # Check the status code
    if response.status != nb_commons_pb2.STATUS_SUCCESS:
        return False       # TODO raise an exception?
    # Done, success
    return True
