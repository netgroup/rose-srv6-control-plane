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
# Implementation of SRv6 Controller
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


"""Control-Plane functionalities for SRv6 Manager"""

# General imports
import logging

import grpc
from pyaml import yaml
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


# Parser for gRPC errors
def parse_grpc_error(err):
    """Parse a gRPC error"""

    status_code = err.code()
    details = err.details()
    logger.error('gRPC client reported an error: %s, %s',
                 status_code, details)
    if grpc.StatusCode.UNAVAILABLE == status_code:
        code = commons_pb2.STATUS_GRPC_SERVICE_UNAVAILABLE
    elif grpc.StatusCode.UNAUTHENTICATED == status_code:
        code = commons_pb2.STATUS_GRPC_UNAUTHORIZED
    else:
        code = commons_pb2.STATUS_INTERNAL_ERROR
    # Return an error message
    return code


def handle_srv6_path(operation, channel, destination, segments=None,
                     device='', encapmode="encap", table=-1, metric=-1):
    """Handle a SRv6 Path"""

    # pylint: disable=too-many-locals, too-many-arguments

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
    try:
        # Get the reference of the stub
        stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
        # Fill the request depending on the operation
        # and send the request
        if operation == 'add':
            # Set encapmode
            path.encapmode = text_type(encapmode)
            if len(segments) == 0:
                logger.error('*** Missing segments for seg6 route')
                return commons_pb2.STATUS_INTERNAL_ERROR
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
                         interface="", segments=None, metric=-1):
    """Handle a SRv6 behavior"""

    # pylint: disable=too-many-arguments, too-many-locals

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
    try:
        # Get the reference of the stub
        stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
        # Fill the request depending on the operation
        # and send the request
        if operation == 'add':
            if action == '':
                logger.error('*** Missing action for seg6local route')
                return commons_pb2.STATUS_INTERNAL_ERROR
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
            logger.error('Invalid operation: %s', operation)
            return None
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


class InvalidConfigurationError(SRv6Exception):
    '''
    Configuration file is not valid.
    '''


class NodeNotFoundError(SRv6Exception):
    '''
    Node not found error.
    '''


class TooManySegmentsError(SRv6Exception):
    '''
    Too many segments error.
    '''


class SIDLocatorError(SRv6Exception):
    '''
    SID Locator is invalid error.
    '''


def nodes_to_addrs(nodes, node_to_addr_filename):
    '''
    Convert a list of node names into a list of IP addresses.

    :param nodes: List of node names
    :type node: list
    :param node_to_addr_filename: Name of the YAML file containing the
                                  mapping of node names to IP addresses
    :type node_to_addr_filename: str
    :return: List of IP addresses
    :rtype: list
    :raises NodeNotFoundError: Node name not found in the mapping file
    :raises InvalidConfigurationError: The mapping file is not a valid
                                       YAML file
    '''
    # Read the mapping from the file
    with open(node_to_addr_filename, 'r') as node_to_addr_file:
        node_to_addr = yaml.safe_load(node_to_addr_file)
    # Validate the file
    for addr in node_to_addr.values():
        if not utils.validate_ipv6_address(addr):
            logger.error('Invalid IPv6 address %s in %s',
                         addr, node_to_addr_file)
            raise InvalidConfigurationError
    # Translate nodes into IP addresses
    node_addrs = list()
    for node in nodes:
        # Check if the node exists in the mapping file
        if node not in node_to_addr:
            logger.error('Node %s not found in configuration file %s',
                         node, node_to_addr_filename)
            raise NodeNotFoundError
        # Get the address of the node
        # and enforce case-sensitivity
        node_addrs.append(node_to_addr[node].lower())
    # Return the IP addresses list
    return node_addrs


def segments_to_micro_segment(locator, segments):
    '''
    Convert a SID list (with #segments <= 6) into a uSID.

    :param locator: The SID Locator of the segments.
                    All the segments must use the same SID Locator.
    :type locator: str
    :param segments: The SID List to be compressed
    :type segments: list
    :return: The uSID containing all the segments
    :rtype: str
    :raises TooManySegmentsError: segments arg contains more than 6 segments
    :raises SIDLocatorError: SID Locator is wrong for one or more segments
    '''
    # Enforce case-sensitivity
    locator = locator.lower()
    _segments = list()
    for segment in segments:
        _segments.append(segment.lower())
    segments = _segments
    # Validation check
    if len(segments) > 6:
        logger.error('Too many segments')
        raise TooManySegmentsError
    # uSIDs always start with the SID Locator
    usid = locator
    # Iterate on the segments
    for segment in segments:
        segment = segment.split(':')
        if locator != '%s:%s' % (segment[0], segment[1]):
            # All the segments must have the same Locator
            logger.error('Wrong locator for the SID %s', ''.join(segment))
            raise SIDLocatorError
        # Take the uSID identifier
        usid_id = segment[2]
        # And append to the uSID
        usid += ':%s' % usid_id
    # If we have less than 6 SIDs, fill the remaining ones with zeroes
    if len(segments) < 6:
        usid += '::'
    # Enforce case-sensitivity and return the uSID
    return usid.lower()


def get_sid_locator(sid_list):
    '''
    Get the SID Locator (i.e. the first 32 bits) from a SID List.

    :param sid_list: SID List
    :type sid_list: list
    :return: SID Locator
    :rtype: str
    :raises SIDLocatorError: SID Locator is wrong for one or more segments
    '''
    # Enforce case-sensitivity
    _sid_list = list()
    for segment in sid_list:
        _sid_list.append(segment.lower())
    sid_list = _sid_list
    # Locator
    locator = ''
    # Iterate on the SID list
    for segment in sid_list:
        segment = segment.split(':')
        if locator == '':
            # Store the segment
            locator = '%s:%s' % (segment[0], segment[1])
        elif locator != '%s:%s' % (segment[0], segment[1]):
            # All the segments must have the same Locator
            logger.error('Wrong locator')
            raise SIDLocatorError
    # Return the SID Locator
    return locator


def sidlist_to_usidlist(sid_list):
    '''
    Convert a SID List into a uSID List.

    :param sid_list: SID List to be converted
    :type sid_list: list
    :return: uSID List containing
    :rtype: list
    :raises TooManySegmentsError: segments arg contains more than 6 segments
    :raises SIDLocatorError: SID Locator is wrong for one or more segments
    '''
    # Get the locator
    locator = get_sid_locator(sid_list)
    # Micro segments list
    usid_list = []
    # Iterate on the SID list
    while len(sid_list) > 0:
        # Segments are encoded in groups of 6
        # Take the first 6 SIDs, build the uSID and add it to the uSID list
        usid_list.append(segments_to_micro_segment(locator, sid_list[:6]))
        # Advance SID list
        sid_list = sid_list[6:]
    # Return the uSID list
    return usid_list


def nodes_to_micro_segments(nodes, node_addrs_filename):
    '''
    Convert a list of nodes into a list of micro segments (uSID List)

    :param nodes: List of node names
    :type node: list
    :param node_to_addr_filename: Name of the YAML file containing the
                                  mapping of node names to IP addresses
    :type node_to_addr_filename: str
    :return: uSID List
    :rtype: list
    :raises NodeNotFoundError: Node name not found in the mapping file
    :raises InvalidConfigurationError: The mapping file is not a valid
                                       YAML file
    :raises TooManySegmentsError: segments arg contains more than 6 segments
    :raises SIDLocatorError: SID Locator is wrong for one or more segments
    '''

    # Convert the list of nodes into a list of IP addresses (SID list)
    # Translation is based on a file containing the mapping
    # of node names to IP addresses
    sid_list = nodes_to_addrs(nodes, node_addrs_filename)
    # Compress the SID list into a uSID list
    usid_list = sidlist_to_usidlist(sid_list)
    # Return the uSID list
    return usid_list


def handle_srv6_usid_policy(operation, channel, node_to_addr_filename,
                            destination, nodes=None,
                            device='', encapmode="encap", table=-1,
                            metric=-1):
    '''
    Handle a SRv6 Policy using uSIDs

    :param operation: The operation to be performed on the uSID policy
                      (i.e. add, get, change, del)
    :type operation: str
    :param channel: The gRPC Channel to the node
    :type channel: class: `grpc._channel.Channel`
    :param node_to_addr_filename: Name of the YAML file containing the
                                  mapping of node names to IP addresses
    :type node_to_addr_filename: str
    :param destination: Destination of the SRv6 route
    :type destination: str
    :param nodes: Waypoints of the SRv6 route
    :type nodes: list
    :param device: Device of the SRv6 route. If not provided, the device
                   is selected automatically by the node.
    :type device: str, optional
    :param encapmode: Encap mode for the SRv6 route (i.e. encap, inline or
                      l2encap). Default: encap.
    :type encapmode: str, optional
    :param table: Routing table containing the SRv6 route. If not provided,
                  the main table (i.e. table 254) will be used.
    :type table: int, optional
    :param metric: Metric for the SRv6 route. If not provided, the default
                   metric will be used.
    :type metric: int, optional
    :return: Status Code of the operation (e.g. 0 for STATUS_SUCCESS)
    :rtype: int
    :raises NodeNotFoundError: Node name not found in the mapping file
    :raises InvalidConfigurationError: The mapping file is not a valid
                                       YAML file
    :raises TooManySegmentsError: segments arg contains more than 6 segments
    :raises SIDLocatorError: SID Locator is wrong for one or more segments
    '''
    # pylint: disable=too-many-locals, too-many-arguments
    #
    # This function receives a list of node names; we need to convert
    # this list into a uSID list, before creating the SRv6 policy
    # In order to perform this translation, a file containing the
    # mapping of node names to IPv6 addresses is required
    segments = nodes_to_micro_segments(nodes, node_to_addr_filename)
    # Create the SRv6 Policy
    try:
        response = handle_srv6_path(
            operation=operation,
            channel=channel,
            destination=destination,
            segments=segments,
            device=device,
            encapmode=encapmode,
            table=table,
            metric=metric
        )
    except (InvalidConfigurationError,
            NodeNotFoundError, TooManySegmentsError, SIDLocatorError):
        return commons_pb2.STATUS_INTERNAL_ERROR
    # Return the response
    return response


def create_uni_srv6_tunnel(ingress_channel, egress_channel,
                           destination, segments, localseg=None):
    """Create a unidirectional SRv6 tunnel from <ingress> to <egress>

    Parameters
    ----------
    ingress_channel : <gRPC Channel>
        The gRPC Channel to the ingress node
    egress_channel : <gRPC Channel>
        The gRPC Channel to the egress node
    destination : str
        The destination prefix of the SRv6 path.
        It can be a IP address or a subnet.
    segments : list
        The SID list to be applied to the packets going to the destination
    localseg : str, optional
        The local segment to be associated to the End.DT6 seg6local
        function on the egress node.
        If the argument 'localseg' isn't passed in, the End.DT6 function
        is not created.
    """

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
        segments=segments
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
            lookup_table=254
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
                       localseg_lr=None, localseg_rl=None):
    """Create a bidirectional SRv6 tunnel.

    Parameters
    ----------
    node_l_channel : str
        The gRPC Channel to the left endpoint of the SRv6 tunnel
    node_r : str
        The gRPC Channel to the right endpoint of the SRv6 tunnel
    sidlist_lr : list
        The SID list to be installed on the packets going
        from <node_l> to <node_r>
    sidlist_rl : list
        SID list to be installed on the packets going
        from <node_r> to <node_l>
    dest_lr : str
        The destination prefix of the SRv6 path from <node_l> to <node_r>.
        It can be a IP address or a subnet.
    dest_rl : str
        The destination prefix of the SRv6 path from <node_r> to <node_l>.
        It can be a IP address or a subnet.
    localseg_lr : str, optional
        The local segment to be associated to the End.DT6 seg6local
        function for the SRv6 path from <node_l> to <node_r>.
        If the argument 'localseg_l' isn't passed in, the End.DT6 function
        is not created.
    localseg_rl : str, optional
        The local segment to be associated to the End.DT6 seg6local
        function for the SRv6 path from <node_r> to <node_l>.
        If the argument 'localseg_r' isn't passed in, the End.DT6 function
        is not created.
    """

    # pylint: disable=too-many-arguments

    # Create a unidirectional SRv6 tunnel from <node_l> to <node_r>
    res = create_uni_srv6_tunnel(
        ingress_channel=node_l_channel,
        egress_channel=node_r_channel,
        destination=dest_lr,
        segments=sidlist_lr,
        localseg=localseg_lr
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
        localseg=localseg_rl
    )
    # If an error occurred, abort the operation
    if res != commons_pb2.STATUS_SUCCESS:
        return res
    # Success
    return commons_pb2.STATUS_SUCCESS


def destroy_uni_srv6_tunnel(ingress_channel, egress_channel, destination,
                            localseg=None, ignore_errors=False):
    """Destroy a unidirectional SRv6 tunnel from <ingress> to <egress>

    Parameters
    ----------
    ingress_channel : <gRPC Channel>
        The gRPC Channel to the ingress node
    egress_channel : <gRPC Channel>
        The gRPC Channel to the egress node
    destination : str
        The destination prefix of the SRv6 path.
        It can be a IP address or a subnet.
    localseg : str, optional
        The local segment associated to the End.DT6 seg6local
        function on the egress node.
        If the argument 'localseg' isn't passed in, the End.DT6 function
        is not removed.
    ignore_errors : bool, optional
        Whether to ignore "No such process" errors or not (default is False)
    """

    # Remove seg6 route from <ingress> to steer the packets sent to
    # <destination> through the SID list <segments>
    #
    # Equivalent to the command:
    #    ingress: ip -6 route del <destination> encap seg6 mode encap \
    #             segs <segments> dev <device>
    res = handle_srv6_path(
        operation='del',
        channel=ingress_channel,
        destination=destination
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
            segment=localseg
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
                        ignore_errors=False):
    """Destroy a bidirectional SRv6 tunnel

    Parameters
    ----------
    node_l_channel : <gRPC channel>
        The gRPC channel to the left endpoint of the SRv6 tunnel
    node_r_channel : <gRPC channel>
        The gRPC channel to the right endpoint of the SRv6 tunnel
    node_l : str
        The IP address of the left endpoint of the SRv6 tunnel
    node_r : str
        The IP address of the right endpoint of the SRv6 tunnel
    dest_lr : str
        The destination prefix of the SRv6 path from <node_l> to <node_r>.
        It can be a IP address or a subnet.
    dest_rl : str
        The destination prefix of the SRv6 path from <node_r> to <node_l>.
        It can be a IP address or a subnet.
    localseg_lr : str, optional
        The local segment associated to the End.DT6 seg6local
        function for the SRv6 path from <node_l> to <node_r>.
        If the argument 'localseg_l' isn't passed in, the End.DT6 function
        is not removed.
    localseg_rl : str, optional
        The local segment associated to the End.DT6 seg6local
        function for the SRv6 path from <node_r> to <node_l>.
        If the argument 'localseg_r' isn't passed in, the End.DT6 function
        is not removed.
    ignore_errors : bool, optional
        Whether to ignore "No such process" errors or not (default is False)
    """

    # pylint: disable=too-many-arguments

    # Remove unidirectional SRv6 tunnel from <node_l> to <node_r>
    res = destroy_uni_srv6_tunnel(
        ingress_channel=node_l_channel,
        egress_channel=node_r_channel,
        destination=dest_lr,
        localseg=localseg_lr,
        ignore_errors=ignore_errors
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
        ignore_errors=ignore_errors
    )
    # If an error occurred, abort the operation
    if res != commons_pb2.STATUS_SUCCESS:
        return res
    # Success
    return commons_pb2.STATUS_SUCCESS
