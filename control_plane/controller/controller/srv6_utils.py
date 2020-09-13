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
# SRv6 utilities for SRv6 SDN Controller
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
This module provides a collection of SRv6 utilities for SRv6 SDN Controller.
'''

# General imports
import logging
import grpc
from six import text_type

# Proto dependencies
import commons_pb2
import srv6_manager_pb2
# Controller dependencies
import srv6_manager_pb2_grpc
from controller import utils


# Global variables definition
#
#
# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)
# Default number of bits for the SID Locator
DEFAULT_LOCATOR_BITS = 32
# Default number of bits for the uSID identifier
DEFAULT_USID_ID_BITS = 16


# Parser for gRPC errors
def parse_grpc_error(err):
    '''
    Parse a gRPC error.

    :param err: The error to parse.
    :type err: grpc.RpcError
    :return: A status code corresponding to the gRPC error.
    :rtype: int
    '''
    # Extract the gRPC status code
    status_code = err.code()
    # Extract the error description
    details = err.details()
    logger.error('gRPC client reported an error: %s, %s',
                 status_code, details)
    if grpc.StatusCode.UNAVAILABLE == status_code:
        # gRPC server is not available
        code = commons_pb2.STATUS_GRPC_SERVICE_UNAVAILABLE
    elif grpc.StatusCode.UNAUTHENTICATED == status_code:
        # Authentication problem
        code = commons_pb2.STATUS_GRPC_UNAUTHORIZED
    else:
        # Generic gRPC error
        code = commons_pb2.STATUS_INTERNAL_ERROR
    # Return an error message
    return code


def handle_srv6_path(operation, channel, destination, segments=None,
                     device='', encapmode="encap", table=-1, metric=-1,
                     bsid_addr='', fwd_engine='Linux'):
    '''
    Handle a SRv6 path on a node.

    :param operation: The operation to be performed on the SRv6 path
                      (i.e. add, get, change, del).
    :type operation: str
    :param channel: The gRPC Channel to the node.
    :type channel: class: `grpc._channel.Channel`
    :param destination: The destination prefix of the SRv6 path.
                        It can be a IP address or a subnet.
    :type destination: str
    :param segments: The SID list to be applied to the packets going to
                     the destination (not required for "get" and "del"
                     operations).
    :type segments: list, optional
    :param device: Device of the SRv6 route. If not provided, the device
                   is selected automatically by the node.
    :type device: str, optional
    :param encapmode: The encap mode to use for the path, i.e. "inline" or
                      "encap" (default: encap).
    :type encapmode: str, optional
    :param table: Routing table containing the SRv6 route. If not provided,
                  the main table (i.e. table 254) will be used.
    :type table: int, optional
    :param metric: Metric for the SRv6 route. If not provided, the default
                   metric will be used.
    :type metric: int, optional
    :param bsid_addr: The Binding SID to be used for the route (only required
                      for VPP).
    :type bsid_addr: str, optional
    :param fwd_engine: Forwarding engine for the SRv6 route (default: Linux).
    :type fwd_engine: str, optional
    :return: The status code of the operation.
    :rtype: int
    :raises controller.utils.InvalidArgumentError: You provided an invalid
                                                   argument.
    '''
    # pylint: disable=too-many-locals, too-many-arguments, too-many-branches
    #
    # If segments argument is not provided, we initialize it to an empty list
    if segments is None:
        segments = []
    # Create request message
    request = srv6_manager_pb2.SRv6ManagerRequest()
    # Create a new SRv6 path request
    path_request = request.srv6_path_request       # pylint: disable=no-member
    # Create a new path
    path = path_request.paths.add()
    # Set destination
    path.destination = text_type(destination)
    # Set device
    # If the device is not specified (i.e. empty string),
    # it will be chosen by the gRPC server
    path.device = text_type(device)
    # Set table ID
    # If the table ID is not specified (i.e. table=-1),
    # the main table will be used
    path.table = int(table)
    # Set metric (i.e. preference value of the route)
    # If the metric is not specified (i.e. metric=-1),
    # the decision is left to the Linux kernel
    path.metric = int(metric)
    # Set the BSID address (required for VPP)
    path.bsid_addr = str(bsid_addr)
    # Forwarding engine (Linux or VPP)
    try:
        path_request.fwd_engine = srv6_manager_pb2.FwdEngine.Value(fwd_engine)
    except ValueError:
        logger.error('Invalid forwarding engine: %s', fwd_engine)
        raise utils.InvalidArgumentError
    # Handle SRv6 policy for VPP
    # A SRv6 path in VPP consists of:
    #     - a SRv6 policy
    #     - a rule to steer packets sent to a destination through the SRv6
    #       policy.
    # The steering rule matches the corresponding SRv6 policy through a
    # Binding SID (BSID)
    # Therefore, VPP requires some extra configuration with respect to Linux
    if fwd_engine == 'VPP':
        # VPP requires BSID address
        if bsid_addr == '':
            logger.error('"bsid_addr" argument is mandatory for VPP')
            raise utils.InvalidArgumentError
        # Handle SRv6 policy
        res = handle_srv6_policy(
            operation=operation,
            channel=channel,
            bsid_addr=bsid_addr,
            segments=segments,
            table=table,
            metric=metric,
            fwd_engine=fwd_engine
        )
        # Check for errors
        if res != commons_pb2.STATUS_SUCCESS:
            logger.error('Cannot create SRv6 policy: error %s', res)
            return res
    # The following steps are common for Linux and VPP
    try:
        # Get the reference of the stub
        stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
        # Fill the request depending on the operation
        # and send the request
        if operation == 'add':
            # Set encapmode
            path.encapmode = text_type(encapmode)
            # At least one segment is required for add operation
            if len(segments) == 0:
                logger.error('*** Missing segments for seg6 route')
                raise utils.InvalidArgumentError
            # Iterate on the segments and build the SID list
            for segment in segments:
                # Append the segment to the SID list
                srv6_segment = path.sr_path.add()
                srv6_segment.segment = text_type(segment)
            # Create the SRv6 path
            response = stub.Create(request)
        elif operation == 'get':
            # Get the SRv6 path
            response = stub.Get(request)
        elif operation == 'change':
            # Set encapmode
            path.encapmode = text_type(encapmode)
            # Iterate on the segments and build the SID list
            for segment in segments:
                # Append the segment to the SID list
                srv6_segment = path.sr_path.add()
                srv6_segment.segment = text_type(segment)
            # Update the SRv6 path
            response = stub.Update(request)
        elif operation == 'del':
            # Remove the SRv6 path
            response = stub.Remove(request)
        else:
            # The operation is unknown
            logger.error('Invalid operation: %s', operation)
            raise utils.InvalidArgumentError
        # Get the status code of the gRPC operation
        response = response.status
    except grpc.RpcError as err:
        # An error occurred during the gRPC operation
        # Parse the error and return it
        response = parse_grpc_error(err)
    # Return the response
    return response


def handle_srv6_policy(operation, channel, bsid_addr, segments=None,
                       table=-1, metric=-1, fwd_engine='Linux'):
    '''
    Handle a SRv6 policy on a node.

    :param operation: The operation to be performed on the SRv6 policy
                      (i.e. add, get, change, del).
    :type operation: str
    :param channel: The gRPC Channel to the node.
    :type channel: class: `grpc._channel.Channel`
    :param bsid_addr: The Binding SID to be used for the policy.
    :type bsid_addr: str
    :param segments: The SID list to be applied to the packets going to
                     the destination (not required for "get" and "del"
                     operations).
    :type segments: list, optional
    :param table: Routing table containing the SRv6 route. If not provided,
                  the main table (i.e. table 254) will be used.
    :type table: int, optional
    :param metric: Metric for the SRv6 route. If not provided, the default
                   metric will be used.
    :type metric: int, optional
    :param fwd_engine: Forwarding engine for the SRv6 route (default: Linux).
    :type fwd_engine: str, optional
    :return: The status code of the operation.
    :rtype: int
    :raises controller.utils.InvalidArgumentError: You provided an invalid
                                                   argument.
    '''
    # pylint: disable=too-many-locals, too-many-arguments
    #
    # If segments argument is not provided, we initialize it to an empty list
    if segments is None:
        segments = []
    # Create request message
    request = srv6_manager_pb2.SRv6ManagerRequest()
    # Create a new SRv6 path request
    policy_request = request.srv6_policy_request   # pylint: disable=no-member
    # Create a new path
    policy = policy_request.policies.add()
    # Set BSID address
    policy.bsid_addr = text_type(bsid_addr)
    # Set table ID
    # If the table ID is not specified (i.e. table=-1),
    # the main table will be used
    policy.table = int(table)
    # Set metric (i.e. preference value of the route)
    # If the metric is not specified (i.e. metric=-1),
    # the decision is left to the Linux kernel
    policy.metric = int(metric)
    # Forwarding engine (Linux or VPP)
    try:
        policy_request.fwd_engine = srv6_manager_pb2.FwdEngine.Value(
            fwd_engine)
    except ValueError:
        logger.error('Invalid forwarding engine: %s', fwd_engine)
        raise utils.InvalidArgumentError
    try:
        # Get the reference of the stub
        stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
        # Fill the request depending on the operation
        # and send the request
        if operation == 'add':
            # At least one segment is required for add operation
            if len(segments) == 0:
                logger.error('*** Missing segments for seg6 route')
                raise utils.InvalidArgumentError
            # Iterate on the segments and build the SID list
            for segment in segments:
                # Append the segment to the SID list
                srv6_segment = policy.sr_path.add()
                srv6_segment.segment = text_type(segment)
            # Create the SRv6 policy
            response = stub.Create(request)
        elif operation == 'get':
            # Get the SRv6 policy
            response = stub.Get(request)
        elif operation == 'change':
            # Iterate on the segments and build the SID list
            for segment in segments:
                # Append the segment to the SID list
                srv6_segment = policy.sr_path.add()
                srv6_segment.segment = text_type(segment)
            # Update the SRv6 policy
            response = stub.Update(request)
        elif operation == 'del':
            # Remove the SRv6 policy
            response = stub.Remove(request)
        else:
            # The operation is unknown
            logger.error('Invalid operation: %s', operation)
            raise utils.InvalidArgumentError
        # Get the status code of the gRPC operation
        response = response.status
    except grpc.RpcError as err:
        # An error occurred during the gRPC operation
        # Parse the error and return it
        response = parse_grpc_error(err)
    # Return the response
    return response


def handle_srv6_behavior(operation, channel, segment, action='', device='',
                         table=-1, nexthop="", lookup_table=-1,
                         interface="", segments=None, metric=-1,
                         fwd_engine='Linux'):
    '''
    Handle a SRv6 behavior on a node.

    :param operation: The operation to be performed on the SRv6 path
                      (i.e. add, get, change, del).
    :type operation: str
    :param channel: The gRPC Channel to the node.
    :type channel: class: `grpc._channel.Channel`
    :param segment: The local segment of the SRv6 behavior. It can be a IP
                    address or a subnet.
    :type segment: str
    :param action: The SRv6 action associated to the behavior (e.g. End or
                   End.DT6), (not required for "get" and "change").
    :type action: str, optional
    :param device: Device of the SRv6 route. If not provided, the device
                   is selected automatically by the node.
    :type device: str, optional
    :param table: Routing table containing the SRv6 route. If not provided,
                  the main table (i.e. table 254) will be used.
    :type table: int, optional
    :param nexthop: The nexthop of cross-connect behaviors (e.g. End.DX4
                    or End.DX6).
    :type nexthop: str, optional
    :param lookup_table: The lookup table for the decap behaviors (e.g.
                         End.DT4 or End.DT6).
    :type lookup_table: int, optional
    :param interface: The outgoing interface for the End.DX2 behavior.
    :type interface: str, optional
    :param segments: The SID list to be applied for the End.B6 behavior.
    :type segments: list, optional
    :param metric: Metric for the SRv6 route. If not provided, the default
                   metric will be used.
    :type metric: int, optional
    :param fwd_engine: Forwarding engine for the SRv6 route (default: Linux).
    :type fwd_engine: str, optional
    :return: The status code of the operation.
    :rtype: int
    :raises controller.utils.InvalidArgumentError: You provided an invalid
                                                   argument.
    '''
    # pylint: disable=too-many-arguments, too-many-locals
    #
    # If segments argument is not provided, we initialize it to an empty list
    if segments is None:
        segments = []
    # Create request message
    request = srv6_manager_pb2.SRv6ManagerRequest()
    # Create a new SRv6 behavior request
    behavior_request = (request               # pylint: disable=no-member
                        .srv6_behavior_request)
    # Create a new SRv6 behavior
    behavior = behavior_request.behaviors.add()
    # Set local segment for the seg6local route
    behavior.segment = text_type(segment)
    # Set the device
    # If the device is not specified (i.e. empty string),
    # it will be chosen by the gRPC server
    behavior.device = text_type(device)
    # Set the table where the seg6local must be inserted
    # If the table ID is not specified (i.e. table=-1),
    # the main table will be used
    behavior.table = int(table)
    # Set device
    # If the device is not specified (i.e. empty string),
    # it will be chosen by the gRPC server
    behavior.device = text_type(device)
    # Set metric (i.e. preference value of the route)
    # If the metric is not specified (i.e. metric=-1),
    # the decision is left to the Linux kernel
    behavior.metric = int(metric)
    # Forwarding engine (Linux or VPP)
    try:
        behavior_request.fwd_engine = srv6_manager_pb2.FwdEngine.Value(
            fwd_engine)
    except ValueError:
        logger.error('Invalid forwarding engine: %s', fwd_engine)
        raise utils.InvalidArgumentError
    try:
        # Get the reference of the stub
        stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
        # Fill the request depending on the operation
        # and send the request
        if operation == 'add':
            # The argument "action" is mandatory for the "add" operation
            if action == '':
                logger.error('*** Missing action for seg6local route')
                raise utils.InvalidArgumentError
            # Set the action for the seg6local route
            behavior.action = text_type(action)
            # Set the nexthop for the L3 cross-connect actions
            # (e.g. End.DX4, End.DX6)
            behavior.nexthop = text_type(nexthop)
            # Set the table for the "decap and table lookup" actions
            # (e.g. End.DT4, End.DT6)
            behavior.lookup_table = int(lookup_table)
            # Set the inteface for the L2 cross-connect actions
            # (e.g. End.DX2)
            behavior.interface = text_type(interface)
            # Set the segments for the binding SID actions
            # (e.g. End.B6, End.B6.Encaps)
            for seg in segments:
                # Create a new segment
                srv6_segment = behavior.segs.add()
                srv6_segment.segment = text_type(seg)
            # Create the SRv6 behavior
            response = stub.Create(request)
        elif operation == 'get':
            # Get the SRv6 behavior
            response = stub.Get(request)
        elif operation == 'change':
            # Set the action for the seg6local route
            behavior.action = text_type(action)
            # Set the nexthop for the L3 cross-connect actions
            # (e.g. End.DX4, End.DX6)
            behavior.nexthop = text_type(nexthop)
            # Set the table for the "decap and table lookup" actions
            # (e.g. End.DT4, End.DT6)
            behavior.lookup_table = int(lookup_table)
            # Set the inteface for the L2 cross-connect actions
            # (e.g. End.DX2)
            behavior.interface = text_type(interface)
            # Set the segments for the binding SID actions
            # (e.g. End.B6, End.B6.Encaps)
            for seg in segments:
                # Create a new segment
                srv6_segment = behavior.segs.add()
                srv6_segment.segment = text_type(seg)
            # Update the SRv6 behavior
            response = stub.Update(request)
        elif operation == 'del':
            # Remove the SRv6 behavior
            response = stub.Remove(request)
        else:
            # The operation is unknown
            logger.error('Invalid operation: %s', operation)
            raise utils.InvalidArgumentError
        # Get the status code of the gRPC operation
        response = response.status
    except grpc.RpcError as err:
        # An error occurred during the gRPC operation
        # Parse the error and return it
        response = parse_grpc_error(err)
    # Return the response
    return response


class SRv6Exception(Exception):
    '''
    Generic SRv6 Exception.
    '''


def create_uni_srv6_tunnel(ingress_channel, egress_channel,
                           destination, segments, localseg=None,
                           bsid_addr='', fwd_engine='Linux'):
    '''
    Create a unidirectional SRv6 tunnel from <ingress> to <egress>.

    :param ingress_channel: The gRPC Channel to the ingress node
    :type ingress_channel: class: `grpc._channel.Channel`
    :param egress_channel: The gRPC Channel to the egress node
    :type egress_channel: class: `grpc._channel.Channel`
    :param destination: The destination prefix of the SRv6 path.
                        It can be a IP address or a subnet.
    :type destination: str
    :param segments: The SID list to be applied to the packets going to
                     the destination
    :type segments: list
    :param localseg: The local segment to be associated to the End.DT6
                     seg6local function on the egress node. If the argument
                     'localseg' isn't passed in, the End.DT6 function
                     is not created.
    :type localseg: str, optional
    :param bsid_addr: The Binding SID to be used for the route (only required
                      for VPP).
    :type bsid_addr: str, optional
    :param fwd_engine: Forwarding engine for the SRv6 route. Default: Linux.
    :type fwd_engine: str, optional
    :return: The status code of the operation.
    :rtype: int
    '''
    # pylint: disable=too-many-arguments
    #
    # Add seg6 route to <ingress> to steer the packets sent to the
    # <destination> through the SID list <segments>
    #
    # Equivalent to the command:
    #    ingress: ip -6 route add <destination> encap seg6 mode encap \
    #            segs <segments> dev <device>
    res = handle_srv6_path(
        operation='add',
        channel=ingress_channel,
        destination=destination,
        segments=segments,
        bsid_addr=bsid_addr,
        fwd_engine=fwd_engine
    )
    # Pretty print status code
    utils.print_status_message(
        status_code=res,
        success_msg='Added SRv6 Path',
        failure_msg='Error in add_srv6_path()'
    )
    # If an error occurred, abort the operation
    if res != commons_pb2.STATUS_SUCCESS:
        return res
    # Perform "Decapsulaton and Specific IPv6 Table Lookup" function
    # on the egress node <egress>
    # The decap function is associated to the <localseg> passed in
    # as argument. If argument 'localseg' isn't passed in, the behavior
    # is not added
    #
    # Equivalent to the command:
    #    egress: ip -6 route add <localseg> encap seg6local action \
    #            End.DT6 table 254 dev <device>
    if localseg is not None:
        res = handle_srv6_behavior(
            operation='add',
            channel=egress_channel,
            segment=localseg,
            action='End.DT6',
            lookup_table=254,
            fwd_engine=fwd_engine
        )
        # Pretty print status code
        utils.print_status_message(
            status_code=res,
            success_msg='Added SRv6 Behavior',
            failure_msg='Error in add_srv6_behavior()'
        )
        # If an error occurred, abort the operation
        if res != commons_pb2.STATUS_SUCCESS:
            return res
    # Success
    return commons_pb2.STATUS_SUCCESS


def create_srv6_tunnel(node_l_channel, node_r_channel,
                       sidlist_lr, sidlist_rl, dest_lr, dest_rl,
                       localseg_lr=None, localseg_rl=None,
                       bsid_addr='', fwd_engine='Linux'):
    '''
    Create a bidirectional SRv6 tunnel between <node_l> and <node_r>.

    :param node_l_channel: The gRPC Channel to the left endpoint (node_l)
                           of the SRv6 tunnel.
    :type node_l_channel: class: `grpc._channel.Channel`
    :param node_r_channel: The gRPC Channel to the right endpoint (node_r)
                           of the SRv6 tunnel.
    :type node_r_channel: class: `grpc._channel.Channel`
    :param sidlist_lr: The SID list to be installed on the packets going
                       from <node_l> to <node_r>.
    :type sidlist_lr: list
    :param sidlist_rl: The SID list to be installed on the packets going
                       from <node_r> to <node_l>.
    :type sidlist_rl: list
    :param dest_lr: The destination prefix of the SRv6 path from <node_l>
                    to <node_r>. It can be a IP address or a subnet.
    :type dest_lr: str
    :param dest_rl: The destination prefix of the SRv6 path from <node_r>
                    to <node_l>. It can be a IP address or a subnet.
    :type dest_rl: str
    :param localseg_lr: The local segment to be associated to the End.DT6
                        seg6local function for the SRv6 path from <node_l>
                        to <node_r>. If the argument 'localseg_lr' isn't
                        passed in, the End.DT6 function is not created.
    :type localseg_lr: str, optional
    :param localseg_rl: The local segment to be associated to the End.DT6
                        seg6local function for the SRv6 path from <node_r>
                        to <node_l>. If the argument 'localseg_rl' isn't
                        passed in, the End.DT6 function is not created.
    :type localseg_rl: str, optional
    :param bsid_addr: The Binding SID to be used for the route (only required
                      for VPP).
    :type bsid_addr: str, optional
    :param fwd_engine: Forwarding engine for the SRv6 route. Default: Linux.
    :type fwd_engine: str, optional
    :return: The status code of the operation.
    :rtype: int
    '''
    # pylint: disable=too-many-arguments
    #
    # Create a unidirectional SRv6 tunnel from <node_l> to <node_r>
    res = create_uni_srv6_tunnel(
        ingress_channel=node_l_channel,
        egress_channel=node_r_channel,
        destination=dest_lr,
        segments=sidlist_lr,
        localseg=localseg_lr,
        bsid_addr=bsid_addr,
        fwd_engine=fwd_engine
    )
    # If an error occurred, abort the operation
    if res != commons_pb2.STATUS_SUCCESS:
        return res
    # Create a unidirectional SRv6 tunnel from <node_r> to <node_l>
    res = create_uni_srv6_tunnel(
        ingress_channel=node_r_channel,
        egress_channel=node_l_channel,
        destination=dest_rl,
        segments=sidlist_rl,
        localseg=localseg_rl,
        bsid_addr=bsid_addr,
        fwd_engine=fwd_engine
    )
    # If an error occurred, abort the operation
    if res != commons_pb2.STATUS_SUCCESS:
        return res
    # Success
    return commons_pb2.STATUS_SUCCESS


def destroy_uni_srv6_tunnel(ingress_channel, egress_channel, destination,
                            localseg=None, bsid_addr='', fwd_engine='Linux',
                            ignore_errors=False):
    '''
    Destroy a unidirectional SRv6 tunnel from <ingress> to <egress>.

    :param ingress_channel: The gRPC Channel to the ingress node.
    :type ingress_channel: class: `grpc._channel.Channel`
    :param egress_channel: The gRPC Channel to the egress node.
    :type egress_channel: class: `grpc._channel.Channel`
    :param destination: The destination prefix of the SRv6 path.
                        It can be a IP address or a subnet.
    :type destination: str
    :param localseg: The local segment associated to the End.DT6 seg6local
                     function on the egress node. If the argument 'localseg'
                     isn't passed in, the End.DT6 function is not removed.
    :type localseg: str, optional
    :param bsid_addr: The Binding SID to be used for the route (only required
                      for VPP).
    :type bsid_addr: str, optional
    :param fwd_engine: Forwarding engine for the SRv6 route. Default: Linux.
    :type fwd_engine: str, optional
    :param ignore_errors: Whether to ignore "No such process" errors or not
                          (default is False).
    :type ignore_errors: bool, optional
    :return: The status code of the operation.
    :rtype: int
    '''
    # pylint: disable=too-many-arguments
    #
    # Remove seg6 route from <ingress> to steer the packets sent to
    # <destination> through the SID list <segments>
    #
    # Equivalent to the command:
    #    ingress: ip -6 route del <destination> encap seg6 mode encap \
    #             segs <segments> dev <device>
    res = handle_srv6_path(
        operation='del',
        channel=ingress_channel,
        destination=destination,
        bsid_addr=bsid_addr,
        fwd_engine=fwd_engine
    )
    # Pretty print status code
    utils.print_status_message(
        status_code=res,
        success_msg='Removed SRv6 Path',
        failure_msg='Error in remove_srv6_path()'
    )
    # If an error occurred, abort the operation
    if res == commons_pb2.STATUS_NO_SUCH_PROCESS:
        # If the 'ignore_errors' flag is set, continue
        if not ignore_errors:
            return res
    elif res != commons_pb2.STATUS_SUCCESS:
        return res
    # Remove "Decapsulaton and Specific IPv6 Table Lookup" function
    # from the egress node <egress>
    # The decap function associated to the <localseg> passed in
    # as argument. If argument 'localseg' isn't passed in, the behavior
    # is not removed
    #
    # Equivalent to the command:
    #    egress: ip -6 route del <localseg> encap seg6local action \
    #            End.DT6 table 254 dev <device>
    if localseg is not None:
        res = handle_srv6_behavior(
            operation='del',
            channel=egress_channel,
            segment=localseg,
            fwd_engine=fwd_engine
        )
        # Pretty print status code
        utils.print_status_message(
            status_code=res,
            success_msg='Removed SRv6 behavior',
            failure_msg='Error in remove_srv6_behavior()'
        )
        # If an error occurred, abort the operation
        if res == commons_pb2.STATUS_NO_SUCH_PROCESS:
            # If the 'ignore_errors' flag is set, continue
            if not ignore_errors:
                return res
        elif res != commons_pb2.STATUS_SUCCESS:
            return res
    # Success
    return commons_pb2.STATUS_SUCCESS


def destroy_srv6_tunnel(node_l_channel, node_r_channel,
                        dest_lr, dest_rl, localseg_lr=None, localseg_rl=None,
                        bsid_addr='', fwd_engine='Linux',
                        ignore_errors=False):
    '''
    Destroy a bidirectional SRv6 tunnel between <node_l> and <node_r>.

    :param node_l_channel: The gRPC channel to the left endpoint of the
                           SRv6 tunnel (node_l).
    :type node_l_channel: class: `grpc._channel.Channel`
    :param node_r_channel: The gRPC channel to the right endpoint of the
                           SRv6 tunnel (node_r).
    :type node_r_channel: class: `grpc._channel.Channel`
    :param node_l: The IP address of the left endpoint of the SRv6 tunnel.
    :type node_l: str
    :param node_r: The IP address of the right endpoint of the SRv6 tunnel.
    :type node_r: str
    :param dest_lr: The destination prefix of the SRv6 path from <node_l>
                    to <node_r>. It can be a IP address or a subnet.
    :type dest_lr: str
    :param dest_rl: The destination prefix of the SRv6 path from <node_r>
                    to <node_l>. It can be a IP address or a subnet.
    :type dest_rl: str
    :param localseg_lr: The local segment associated to the End.DT6 seg6local
                        function for the SRv6 path from <node_l> to <node_r>.
                        If the argument 'localseg_l' isn't passed in, the
                        End.DT6 function is not removed.
    :type localseg_lr: str, optional
    :param localseg_rl: The local segment associated to the End.DT6 seg6local
                        function for the SRv6 path from <node_r> to <node_l>.
                        If the argument 'localseg_r' isn't passed in, the
                        End.DT6 function is not removed.
    :type localseg_rl: str, optional
    :param bsid_addr: The Binding SID to be used for the route (only required
                      for VPP).
    :type bsid_addr: str, optional
    :param fwd_engine: Forwarding engine for the SRv6 route. Default: Linux.
    :type fwd_engine: str, optional
    :param ignore_errors: Whether to ignore "No such process" errors or not
                          (default is False).
    :type ignore_errors: bool, optional
    :return: The status code of the operation.
    :rtype: int
    '''
    # pylint: disable=too-many-arguments
    #
    # Remove unidirectional SRv6 tunnel from <node_l> to <node_r>
    res = destroy_uni_srv6_tunnel(
        ingress_channel=node_l_channel,
        egress_channel=node_r_channel,
        destination=dest_lr,
        localseg=localseg_lr,
        ignore_errors=ignore_errors,
        bsid_addr=bsid_addr,
        fwd_engine=fwd_engine
    )
    # If an error occurred, abort the operation
    if res != commons_pb2.STATUS_SUCCESS:
        return res
    # Remove unidirectional SRv6 tunnel from <node_r> to <node_l>
    res = destroy_uni_srv6_tunnel(
        ingress_channel=node_r_channel,
        egress_channel=node_l_channel,
        destination=dest_rl,
        localseg=localseg_rl,
        ignore_errors=ignore_errors,
        bsid_addr=bsid_addr,
        fwd_engine=fwd_engine
    )
    # If an error occurred, abort the operation
    if res != commons_pb2.STATUS_SUCCESS:
        return res
    # Success
    return commons_pb2.STATUS_SUCCESS
