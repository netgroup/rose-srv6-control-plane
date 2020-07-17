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


'''
Control-Plane functionalities for SRv6 Manager
'''

# General imports
import logging
import math
import pprint
import sys
from ipaddress import IPv6Address

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
# Default number of bits for the SID Locator
DEFAULT_LOCATOR_BITS = 32
# Default number of bits for the uSID identifier
DEFAULT_USID_ID_BITS = 16


# Parser for gRPC errors
def parse_grpc_error(err):
    '''
    Parse a gRPC error
    '''

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
                     device='', encapmode="encap", table=-1, metric=-1,
                     bsid_addr='', fwd_engine='Linux'):
    '''
    Handle a SRv6 Path
    '''

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
    # Set the BSID address (required for VPP)
    path.bsid_addr = str(bsid_addr)
    # Handle SRv6 policy for VPP
    if fwd_engine == 'VPP':
        if bsid_addr == '':
            logger.error('"bsid_addr" argument is mandatory for VPP')
            return None
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
        if res != commons_pb2.STATUS_SUCCESS:
            logger.error('Cannot create SRv6 policy: error %s' % res)
            return None
    # Forwarding engine (Linux or VPP)
    try:
        path_request.fwd_engine = srv6_manager_pb2.FwdEngine.Value(fwd_engine)
    except ValueError:
        logger.error('Invalid forwarding engine: %s', fwd_engine)
        return None
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


def handle_srv6_policy(operation, channel, bsid_addr, segments=None,
                       table=-1, metric=-1, fwd_engine='Linux'):
    '''
    Handle a SRv6 Path
    '''

    # pylint: disable=too-many-locals, too-many-arguments

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
        return None
    try:
        # Get the reference of the stub
        stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
        # Fill the request depending on the operation
        # and send the request
        if operation == 'add':
            if len(segments) == 0:
                logger.error('*** Missing segments for seg6 route')
                return commons_pb2.STATUS_INTERNAL_ERROR
            # Iterate on the segments and build the SID list
            for segment in segments:
                # Append the segment to the SID list
                srv6_segment = policy.sr_path.add()
                srv6_segment.segment = text_type(segment)
            # Create the SRv6 path
            response = stub.Create(request)
        elif operation == 'get':
            # Get the SRv6 path
            response = stub.Get(request)
        elif operation == 'change':
            # Iterate on the segments and build the SID list
            for segment in segments:
                # Append the segment to the SID list
                srv6_segment = policy.sr_path.add()
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
                         interface="", segments=None, metric=-1,
                         fwd_engine='Linux'):
    '''
    Handle a SRv6 behavior
    '''
    # pylint: disable=too-many-arguments, too-many-locals
    #
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
        return None
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


class InvalidSIDError(SRv6Exception):
    '''
    SID is invalid.
    '''


def print_node_to_addr_mapping(nodes_filename):
    '''
    This function reads a YAML file containing the mapping
    of node names to IP addresses and pretty print it

    :param node_to_addr_filename: Name of the YAML file containing the
                                  mapping of node names to IP addresses
    :type node_to_addr_filename: str
    '''
    # Read the mapping from the file
    with open(nodes_filename, 'r') as nodes_file:
        nodes = yaml.safe_load(nodes_file)
    # Validate the IP addresses
    for addr in [node['grpc_ip'] for node in nodes['nodes'].values()]:
        if not utils.validate_ipv6_address(addr):
            logger.error('Invalid IPv6 address %s in %s',
                         addr, nodes_filename)
            raise InvalidConfigurationError
    # Validate the SIDs
    for sid in [node['uN'] for node in nodes['nodes'].values()]:
        if not utils.validate_ipv6_address(sid):
            logger.error('Invalid SID %s in %s',
                         sid, nodes_filename)
            raise InvalidConfigurationError
    # Validate the forwarding engine
    for fwd_engine in [node['fwd_engine'] for node in nodes['nodes'].values()]:
        if fwd_engine not in ['Linux', 'VPP', 'P4']:
            logger.error('Invalid forwarding engine %s in %s',
                         fwd_engine, nodes_filename)
            raise InvalidConfigurationError
    # Get the #bits of the locator
    locator_bits = nodes.get('locator_bits')
    # Validate #bits for the SID Locator
    if locator_bits is not None and \
            (int(locator_bits) < 0 or int(locator_bits) > 128):
        raise InvalidConfigurationError
    # Get the #bits of the uSID identifier
    usid_id_bits = nodes.get('usid_id_bits')
    # Validate #bits for the uSID ID
    if usid_id_bits is not None and \
            (int(usid_id_bits) < 0 or int(usid_id_bits) > 128):
        raise InvalidConfigurationError
    if locator_bits is not None and usid_id_bits is not None and \
            int(usid_id_bits) + int(locator_bits) > 128:
        raise InvalidConfigurationError
    print('\nList of available devices:')
    pprint.PrettyPrinter(indent=4).pprint(list(nodes['nodes'].keys()))
    print()


def read_nodes(nodes_filename):
    '''
    Convert a list of node names into a list of IP addresses.

    :param nodes_filename: Name of the YAML file containing the
                           IP addresses
    :type nodes_filename: str
    :return: Tuple (List of IP addresses, Locator bits, uSID ID bits)
    :rtype: tuple
    :raises NodeNotFoundError: Node name not found in the mapping file
    :raises InvalidConfigurationError: The mapping file is not a valid
                                       YAML file
    '''
    # Read the mapping from the file
    with open(nodes_filename, 'r') as nodes_file:
        nodes = yaml.safe_load(nodes_file)
    # Validate the IP addresses
    for addr in [node['grpc_ip'] for node in nodes['nodes'].values()]:
        if not utils.validate_ipv6_address(addr):
            logger.error('Invalid IPv6 address %s in %s',
                         addr, nodes_filename)
            raise InvalidConfigurationError
    # Validate the SIDs
    for sid in [node['uN'] for node in nodes['nodes'].values()]:
        if not utils.validate_ipv6_address(sid):
            logger.error('Invalid SID %s in %s',
                         sid, nodes_filename)
            raise InvalidConfigurationError
    # Validate the forwarding engine
    for fwd_engine in [node['fwd_engine'] for node in nodes['nodes'].values()]:
        if fwd_engine not in ['Linux', 'VPP', 'P4']:
            logger.error('Invalid forwarding engine %s in %s',
                         fwd_engine, nodes_filename)
            raise InvalidConfigurationError
    # Get the #bits of the locator
    locator_bits = nodes.get('locator_bits')
    # Validate #bits for the SID Locator
    if locator_bits is not None and \
            (int(locator_bits) < 0 or int(locator_bits) > 128):
        raise InvalidConfigurationError
    # Get the #bits of the uSID identifier
    usid_id_bits = nodes.get('usid_id_bits')
    # Validate #bits for the uSID ID
    if usid_id_bits is not None and \
            (int(usid_id_bits) < 0 or int(usid_id_bits) > 128):
        raise InvalidConfigurationError
    if locator_bits is not None and usid_id_bits is not None and \
            int(usid_id_bits) + int(locator_bits) > 128:
        raise InvalidConfigurationError
    # Enforce case-sensitivity
    for node in nodes['nodes'].values():
        nodes['nodes'][node['name']]['grpc_ip'] = node['grpc_ip'].lower()
        nodes['nodes'][node['name']]['uN'] = node['uN'].lower()
    # Return the nodes list
    return nodes['nodes'], locator_bits, usid_id_bits


def segments_to_micro_segment(locator, segments,
                              locator_bits=DEFAULT_LOCATOR_BITS,
                              usid_id_bits=DEFAULT_USID_ID_BITS):
    '''
    Convert a SID list (with #segments <= 6) into a uSID.

    :param locator: The SID Locator of the segments.
                    All the segments must use the same SID Locator.
    :type locator: str
    :param segments: The SID List to be compressed
    :type segments: list
    :param locator_bits: Number of bits of the locator part of the SIDs
    :type locator_bits: int
    :param usid_id_bits: Number of bits of the uSID identifiers
    :type usid_id_bits: int
    :return: The uSID containing all the segments
    :rtype: str
    :raises TooManySegmentsError: segments arg contains too many segments
    :raises SIDLocatorError: SID Locator is wrong for one or more segments
    :raises InvalidSIDError: SID is wrong for one or more segments
    '''
    # Locator mask, used to extract the locator from the SIDs
    #
    # It is computed with a binary manipulation
    # We start from the IPv6 address 111...11111, then we put to zero
    # the bits of the non-locator part
    # The remaining part is the locator, which is converted to an IPv6Address
    locator_mask = str(IPv6Address(int('1' * 128, 2) ^
                                   int('1' * (128 - locator_bits), 2)))
    # uSID identifier mask
    #
    # It is computed with a binary manipulation
    # We start from the IPv6 address 111...11111, then we perform a shift
    # operation
    usid_id_mask = str(IPv6Address(int('1' * usid_id_bits, 2) <<
                                   (128 - locator_bits - usid_id_bits)))
    # Enforce case-sensitivity
    locator = locator.lower()
    _segments = list()
    for segment in segments:
        _segments.append(segment.lower())
    segments = _segments
    # Validation check
    # We need to verify if there is space in the uSID for all the segments
    if len(segments) > math.floor((128 - locator_bits) / usid_id_bits):
        logger.error('Too many segments')
        raise TooManySegmentsError
    # uSIDs always start with the SID Locator
    usid_int = int(IPv6Address(locator))
    # Offset of the uSIDs
    offset = 0
    # Iterate on the segments
    for segment in segments:
        # Split the segment in...
        # ...segment locator
        segment_locator = \
            str(IPv6Address(int(IPv6Address(locator_mask)) &
                            int(IPv6Address(segment))))
        if locator != segment_locator:
            # All the segments must have the same Locator
            logger.error('Wrong locator for the SID %s', ''.join(segment))
            raise SIDLocatorError
        # ...and uSID identifier
        usid_id = \
            str(IPv6Address(int(IPv6Address(usid_id_mask)) &
                            int(IPv6Address(segment))))
        # Other bits should be equal to zero
        if int(IPv6Address(segment)) & (
                0b1 * (128 - locator_bits - usid_id_bits)) != 0:
            # The SID is invalid
            logger.error('SID %s is invalid. Final bits should be zero',
                         segment)
            raise InvalidSIDError
        # And append to the uSID
        usid_int += int(IPv6Address(usid_id)) >> offset
        # Increase offset
        offset += usid_id_bits
    # Get a string representation of the uSID
    usid = str(IPv6Address(usid_int))
    # Enforce case-sensitivity and return the uSID
    return usid.lower()


def get_sid_locator(sid_list, locator_bits=DEFAULT_LOCATOR_BITS):
    '''
    Get the SID Locator (i.e. the first 32 bits) from a SID List.

    :param sid_list: SID List
    :type sid_list: list
    :param locator_bits: Number of bits of the locator part of the SIDs
    :type locator_bits: int
    :return: SID Locator
    :rtype: str
    :raises SIDLocatorError: SID Locator is wrong for one or more segments
    '''
    # Locator mask, used to extract the locator from the SIDs
    #
    # It is computed with a binary manipulation
    # We start from the IPv6 address 111...11111, then we put to zero
    # the bits of the non-locator part
    # The remaining part is the locator, which is converted to an IPv6Address
    locator_mask = str(IPv6Address(int('1' * 128, 2) ^
                                   int('1' * (128 - locator_bits), 2)))
    # Enforce case-sensitivity
    _sid_list = list()
    for segment in sid_list:
        _sid_list.append(segment.lower())
    sid_list = _sid_list
    # Locator
    locator = ''
    # Iterate on the SID list
    for segment in sid_list:
        # Split the segment in...
        # ...segment locator
        segment_locator = \
            str(IPv6Address(int(IPv6Address(locator_mask)) &
                            int(IPv6Address(segment))))
        if locator == '':
            # Store the segment
            locator = segment_locator
        elif locator != segment_locator:
            # All the segments must have the same Locator
            logger.error('Wrong locator')
            raise SIDLocatorError
    # Return the SID Locator
    return locator


def sidlist_to_usidlist(sid_list, udt_sids=[],
                        locator_bits=DEFAULT_LOCATOR_BITS,
                        usid_id_bits=DEFAULT_USID_ID_BITS):
    '''
    Convert a SID List into a uSID List.

    :param sid_list: SID List to be converted
    :type sid_list: list
    :param locator_bits: Number of bits of the locator part of the SIDs
    :type locator_bits: int
    :param usid_id_bits: Number of bits of the uSID identifiers
    :type usid_id_bits: int
    :return: uSID List containing
    :rtype: list
    :raises TooManySegmentsError: segments arg contains too many segments
    :raises SIDLocatorError: SID Locator is wrong for one or more segments
    '''
    # Size of the group of SIDs to be compressed in one uSID
    # The size depends on the locator bits and uSID ID bits
    # Last slot should be always leaved free
    sid_group_size = math.floor((128 - locator_bits) / usid_id_bits) - 1
    # Get the locator
    locator = get_sid_locator(sid_list=sid_list, locator_bits=locator_bits)
    # Micro segments list
    usid_list = []
    # Iterate on the SID list
    while len(sid_list) + len(udt_sids) > 0:
        # Extract the SIDs to be encoded in one uSID
        sids_group = sid_list[:sid_group_size]
        # uDT list should not be broken into different SIDs
        if len(sid_list) + len(udt_sids) <= sid_group_size:
            sids_group += udt_sids
            udt_sids = []
        # Segments are encoded in groups of X
        # Take the first X SIDs, build the uSID and add it to the uSID list
        usid_list.append(
            segments_to_micro_segment(
                locator=locator,
                segments=sids_group,
                locator_bits=locator_bits,
                usid_id_bits=usid_id_bits
            )
        )
        # Advance SID list
        sid_list = sid_list[sid_group_size:]
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
    nodes_info, locator_bits, usid_id_bits = read_nodes(node_addrs_filename)
    for node in nodes:
        sid_list = nodes_info[node]['uN']
    if locator_bits is None:
        locator_bits = DEFAULT_LOCATOR_BITS
    if usid_id_bits is None:
        usid_id_bits = DEFAULT_USID_ID_BITS
    # Compress the SID list into a uSID list
    usid_list = sidlist_to_usidlist(
        sid_list=sid_list,
        locator_bits=locator_bits,
        usid_id_bits=usid_id_bits
    )
    # Return the uSID list
    return usid_list


# def handle_srv6_usid_policy_uni(operation, nodes_filename,
#                                 destination, nodes=None,
#                                 table=-1, metric=-1):
#     '''
#     Handle a SRv6 Policy (unidirectional) using uSIDs

#     :param operation: The operation to be performed on the uSID policy
#                       (i.e. add, get, change, del)
#     :type operation: str
#     :param nodes_filename: Name of the YAML file containing the
#                            mapping of node names to IP addresses
#     :type nodes_filename: str
#     :param destination: Destination of the SRv6 route
#     :type destination: str
#     :param nodes: Waypoints of the SRv6 route
#     :type nodes: list
#     :param device: Device of the SRv6 route. If not provided, the device
#                    is selected automatically by the node.
#     :type device: str, optional
#     :param table: Routing table containing the SRv6 route. If not provided,
#                   the main table (i.e. table 254) will be used.
#     :type table: int, optional
#     :param metric: Metric for the SRv6 route. If not provided, the default
#                    metric will be used.
#     :type metric: int, optional
#     :return: Status Code of the operation (e.g. 0 for STATUS_SUCCESS)
#     :rtype: int
#     :raises NodeNotFoundError: Node name not found in the mapping file
#     :raises InvalidConfigurationError: The mapping file is not a valid
#                                        YAML file
#     :raises TooManySegmentsError: segments arg contains more than 6 segments
#     :raises SIDLocatorError: SID Locator is wrong for one or more segments
#     :raises InvalidSIDError: SID is wrong for one or more segments
#     '''
#     # pylint: disable=too-many-locals, too-many-arguments
#     #
#     # In order to perform this translation, a file containing the
#     # mapping of node names to IPv6 addresses is required
#     #
#     # Create the SRv6 Policy
#     try:
#         # Read nodes from YAML file
#         nodes_info, locator_bits, usid_id_bits = read_nodes(nodes_filename)
#         # Prefix length for local segment
#         prefix_len = locator_bits + usid_id_bits
#         # Ingress node
#         ingress_node = nodes_info[nodes[0]]
#         # Intermediate nodes
#         intermediate_nodes = list()
#         for node in nodes[1:-1]:
#             intermediate_nodes.append(nodes_info[node])
#         # Egress node
#         egress_node = nodes_info[nodes[-1]]
#         # Extract the segments
#         segments = list()
#         for node in nodes[1:]:
#             segments.append(nodes_info[node]['uN'])
#         # Ingress node
#         with utils.get_grpc_session(ingress_node['grpc_ip'],
#                                     ingress_node['grpc_port']) as channel:
#             # VPP requires a BSID address
#             bsid_addr = ''
#             if ingress_node['fwd_engine'] == 'VPP':
#                 for c in destination:
#                     if c != '0' and c != ':':
#                         bsid_addr += c
#                 add_colon = False
#                 if len(bsid_addr) <= 28:
#                     add_colon = True
#                 bsid_addr = [(bsid_addr[i:i+4]) for i in range(0, len(bsid_addr), 4)]
#                 ':'.join(bsid_addr)
#                 if add_colon:
#                     bsid_addr += '::'
#             # We need to convert the SID list into a uSID list
#             #  before creating the SRv6 policy
#             usid_list = sidlist_to_usidlist(
#                 sid_list=segments[1:] + [egress_node['uDT']],   # TODO bug: FIXME
#                 locator_bits=locator_bits,
#                 usid_id_bits=usid_id_bits
#             )
#             # Handle a SRv6 path
#             response = handle_srv6_path(
#                 operation=operation,
#                 channel=channel,
#                 destination=destination,
#                 segments=usid_list,
#                 encapmode='encap.red',
#                 table=table,
#                 metric=metric,
#                 bsid_addr=bsid_addr,
#                 fwd_engine=ingress_node['fwd_engine']
#             )
#             if response != commons_pb2.STATUS_SUCCESS:
#                 # Error
#                 return response
#         # Intermediate nodes
#         for node in intermediate_nodes:
#             with utils.get_grpc_session(node['grpc_ip'],
#                                         node['grpc_port']) as channel:
#                 # Create the uN behavior
#                 response = handle_srv6_behavior(
#                     operation=operation,
#                     channel=channel,
#                     segment='%s/%s' % (node['uN'], prefix_len),
#                     action='uN',
#                     fwd_engine=node['fwd_engine']
#                 )
#                 if response != commons_pb2.STATUS_SUCCESS:
#                     # Error
#                     return response
#         # Egress node
#         with utils.get_grpc_session(egress_node['grpc_ip'],
#                                     egress_node['grpc_port']) as channel:
#             # Create the uN behavior
#             response = handle_srv6_behavior(
#                 operation=operation,
#                 channel=channel,
#                 segment='%s/%s' % (egress_node['uN'], prefix_len),
#                 action='uN',
#                 fwd_engine=egress_node['fwd_engine']
#             )
#             if response != commons_pb2.STATUS_SUCCESS:
#                 # Error
#                 return response
#             # Create the End behavior
#             response = handle_srv6_behavior(
#                 operation=operation,
#                 channel=channel,
#                 segment='%s/%s' % (egress_node['uN'], 64),
#                 action='End',
#                 fwd_engine=egress_node['fwd_engine']
#             )
#             if response != commons_pb2.STATUS_SUCCESS:
#                 # Error
#                 return response
#             # Create the decap behavior
#             response = handle_srv6_behavior(
#                 operation=operation,
#                 channel=channel,
#                 segment='%s/%s' % (egress_node['uDT'], 64),
#                 action='End.DT6',
#                 lookup_table=254,
#                 fwd_engine=egress_node['fwd_engine']
#             )
#             if response != commons_pb2.STATUS_SUCCESS:
#                 # Error
#                 return response
#     except (InvalidConfigurationError, NodeNotFoundError,
#             TooManySegmentsError, SIDLocatorError, InvalidSIDError):
#         return commons_pb2.STATUS_INTERNAL_ERROR
#     # Return the response
#     return response


def handle_srv6_usid_policy(operation, nodes_filename,
                            lr_destination, rl_destination, nodes_lr=None,
                            nodes_rl=None, table=-1, metric=-1):
    '''
    Handle a SRv6 Policy using uSIDs

    :param operation: The operation to be performed on the uSID policy
                      (i.e. add, get, change, del)
    :type operation: str
    :param nodes_filename: Name of the YAML file containing the
                           mapping of node names to IP addresses
    :type nodes_filename: str
    :param destination: Destination of the SRv6 route
    :type destination: str
    :param nodes: Waypoints of the SRv6 route
    :type nodes: list
    :param device: Device of the SRv6 route. If not provided, the device
                   is selected automatically by the node.
    :type device: str, optional
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
    :raises InvalidSIDError: SID is wrong for one or more segments
    '''
    # pylint: disable=too-many-locals, too-many-arguments
    #
    # In order to perform this translation, a file containing the
    # mapping of node names to IPv6 addresses is required
    #
    # If right to left nodes list is not provided, we use the reverse left to
    # right SID list (symmetric path)
    if nodes_rl is None:
        nodes_rl = nodes_lr[::-1]
    # The two SID lists must have the same endpoints
    if nodes_lr[0] != nodes_rl[-1] or nodes_rl[0] != nodes_lr[-1]:
        logger.error('Bad tunnel endpoints')
        return None
    # Create the SRv6 Policy
    try:
        # Read nodes from YAML file
        nodes_info, locator_bits, usid_id_bits = read_nodes(nodes_filename)
        # # Prefix length for local segment
        # prefix_len = locator_bits + usid_id_bits
        # Ingress node
        ingress_node = nodes_info[nodes_lr[0]]
        # Intermediate nodes
        intermediate_nodes_lr = list()
        for node in nodes_lr[1:-1]:
            intermediate_nodes_lr.append(nodes_info[node])
        intermediate_nodes_rl = list()
        for node in nodes_rl[1:-1]:
            intermediate_nodes_rl.append(nodes_info[node])
        # Egress node
        egress_node = nodes_info[nodes_lr[-1]]
        # Extract the segments
        segments_lr = list()
        for node in nodes_lr:
            segments_lr.append(nodes_info[node]['uN'])
        segments_rl = list()
        for node in nodes_rl:
            segments_rl.append(nodes_info[node]['uN'])

        # Ingress node
        with utils.get_grpc_session(ingress_node['grpc_ip'],
                                    ingress_node['grpc_port']) as channel:
            # Currently ony Linux and VPP are suppoted for the encap
            if ingress_node['fwd_engine'] not in ['Linux', 'VPP']:
                logger.error('Encap operation is not supported for '
                             '%s with fwd engine %s' % ingress_node['name'],
                             ingress_node['fwd_engine'])
                return commons_pb2.STATUS_INTERNAL_ERROR
            # VPP requires a BSID address
            bsid_addr = ''
            if ingress_node['fwd_engine'] == 'VPP':
                for c in lr_destination:
                    if c != '0' and c != ':':
                        bsid_addr += c
                add_colon = False
                if len(bsid_addr) <= 28:
                    add_colon = True
                bsid_addr = [(bsid_addr[i:i+4]) for i in range(0, len(bsid_addr), 4)]
                bsid_addr = ':'.join(bsid_addr)
                if add_colon:
                    bsid_addr += '::'

            udt_sids = list()
            # Locator mask
            locator_mask = str(IPv6Address(int('1' * 128, 2) ^
                                        int('1' * (128 - locator_bits), 2)))
            # uDT mask
            udt_mask_1 =  str(IPv6Address(int('1' * usid_id_bits, 2) <<
                                        (128 - locator_bits - usid_id_bits)))
            udt_mask_2 =  str(IPv6Address(int('1' * usid_id_bits, 2) <<
                                        (128 - locator_bits - 2*usid_id_bits)))
            # Build uDT sid list
            locator_int = int(IPv6Address(egress_node['uDT'])) & int(IPv6Address(locator_mask))
            udt_mask_1_int = int(IPv6Address(egress_node['uDT'])) & int(IPv6Address(udt_mask_1))
            udt_mask_2_int = int(IPv6Address(egress_node['uDT'])) & int(IPv6Address(udt_mask_2))
            udt_sids += [str(IPv6Address(locator_int + udt_mask_1_int))]
            udt_sids += [str(IPv6Address(locator_int + (udt_mask_2_int << usid_id_bits)))]
            # We need to convert the SID list into a uSID list
            #  before creating the SRv6 policy
            usid_list = sidlist_to_usidlist(
                sid_list=segments_lr[1:][:-1],
                udt_sids=[segments_lr[1:][-1]] + udt_sids,
                locator_bits=locator_bits,
                usid_id_bits=usid_id_bits
            )
            # Handle a SRv6 path
            response = handle_srv6_path(
                operation=operation,
                channel=channel,
                destination=lr_destination,
                segments=usid_list,
                encapmode='encap.red',
                table=table,
                metric=metric,
                bsid_addr=bsid_addr,
                fwd_engine=ingress_node['fwd_engine']
            )
            if response != commons_pb2.STATUS_SUCCESS:
                # Error
                return response
            # # Create the uN behavior
            # response = handle_srv6_behavior(
            #     operation=operation,
            #     channel=channel,
            #     segment='%s/%s' % (ingress_node['uN'], prefix_len),
            #     action='uN',
            #     fwd_engine=ingress_node['fwd_engine']
            # )
            # if response != commons_pb2.STATUS_SUCCESS:
            #     # Error
            #     return response
            # # Create the End behavior
            # response = handle_srv6_behavior(
            #     operation=operation,
            #     channel=channel,
            #     segment='%s/%s' % (ingress_node['uN'], 64),
            #     action='End',
            #     fwd_engine=ingress_node['fwd_engine']
            # )
            # if response != commons_pb2.STATUS_SUCCESS:
            #     # Error
            #     return response
            # # Create the decap behavior
            # response = handle_srv6_behavior(
            #     operation=operation,
            #     channel=channel,
            #     segment='%s/%s' % (ingress_node['uDT'], 64),
            #     action='End.DT6',
            #     lookup_table=254,
            #     fwd_engine=ingress_node['fwd_engine']
            # )
            # if response != commons_pb2.STATUS_SUCCESS:
            #     # Error
            #     return response
        # # Intermediate nodes
        # for node in intermediate_nodes:
        #     with utils.get_grpc_session(node['grpc_ip'],
        #                                 node['grpc_port']) as channel:
        #         # Create the uN behavior
        #         response = handle_srv6_behavior(
        #             operation=operation,
        #             channel=channel,
        #             segment='%s/%s' % (node['uN'], prefix_len),
        #             action='uN',
        #             fwd_engine=node['fwd_engine']
        #         )
        #         if response != commons_pb2.STATUS_SUCCESS:
        #             # Error
        #             return response
        # Egress node
        with utils.get_grpc_session(egress_node['grpc_ip'],
                                    egress_node['grpc_port']) as channel:
            # Currently ony Linux and VPP are suppoted for the encap
            if egress_node['fwd_engine'] not in ['Linux', 'VPP']:
                logger.error('Encap operation is not supported for '
                             '%s with fwd engine %s' % egress_node['name'],
                             egress_node['fwd_engine'])
                return commons_pb2.STATUS_INTERNAL_ERROR
            # VPP requires a BSID address
            bsid_addr = ''
            if egress_node['fwd_engine'] == 'VPP':
                for c in lr_destination:
                    if c != '0' and c != ':':
                        bsid_addr += c
                add_colon = False
                if len(bsid_addr) <= 28:
                    add_colon = True
                bsid_addr = [(bsid_addr[i:i+4]) for i in range(0, len(bsid_addr), 4)]
                bsid_addr = ':'.join(bsid_addr)
                if add_colon:
                    bsid_addr += '::'
            # # Create the uN behavior
            # response = handle_srv6_behavior(
            #     operation=operation,
            #     channel=channel,
            #     segment='%s/%s' % (egress_node['uN'], prefix_len),
            #     action='uN',
            #     fwd_engine=egress_node['fwd_engine']
            # )
            # if response != commons_pb2.STATUS_SUCCESS:
            #     # Error
            #     return response
            # # Create the End behavior
            # response = handle_srv6_behavior(
            #     operation=operation,
            #     channel=channel,
            #     segment='%s/%s' % (egress_node['uN'], 64),
            #     action='End',
            #     fwd_engine=egress_node['fwd_engine']
            # )
            # if response != commons_pb2.STATUS_SUCCESS:
            #     # Error
            #     return response
            # # Create the decap behavior
            # response = handle_srv6_behavior(
            #     operation=operation,
            #     channel=channel,
            #     segment='%s/%s' % (egress_node['uDT'], 64),
            #     action='End.DT6',
            #     lookup_table=254,
            #     fwd_engine=egress_node['fwd_engine']
            # )
            # if response != commons_pb2.STATUS_SUCCESS:
            #     # Error
            #     return response

            udt_sids = list()
            # Locator mask
            locator_mask = str(IPv6Address(int('1' * 128, 2) ^
                                        int('1' * (128 - locator_bits), 2)))
            # uDT mask
            udt_mask_1 =  str(IPv6Address(int('1' * usid_id_bits, 2) <<
                                        (128 - locator_bits - usid_id_bits)))
            udt_mask_2 =  str(IPv6Address(int('1' * usid_id_bits, 2) <<
                                        (128 - locator_bits - 2*usid_id_bits)))
            # Build uDT sid list
            locator_int = int(IPv6Address(ingress_node['uDT'])) & int(IPv6Address(locator_mask))
            udt_mask_1_int = int(IPv6Address(ingress_node['uDT'])) & int(IPv6Address(udt_mask_1))
            udt_mask_2_int = int(IPv6Address(ingress_node['uDT'])) & int(IPv6Address(udt_mask_2))
            udt_sids += [str(IPv6Address(locator_int + udt_mask_1_int))]
            udt_sids += [str(IPv6Address(locator_int + (udt_mask_2_int << usid_id_bits)))]
            # We need to convert the SID list into a uSID list
            #  before creating the SRv6 policy
            usid_list = sidlist_to_usidlist(
                sid_list=segments_rl[1:][:-1],
                udt_sids=[segments_rl[1:][-1]] + udt_sids,
                locator_bits=locator_bits,
                usid_id_bits=usid_id_bits
            )
            # Handle a SRv6 path
            response = handle_srv6_path(
                operation=operation,
                channel=channel,
                destination=rl_destination,
                segments=usid_list,
                encapmode='encap.red',
                table=table,
                metric=metric,
                bsid_addr=bsid_addr,
                fwd_engine=egress_node['fwd_engine']
            )
            if response != commons_pb2.STATUS_SUCCESS:
                # Error
                return response
    except (InvalidConfigurationError, NodeNotFoundError,
            TooManySegmentsError, SIDLocatorError, InvalidSIDError):
        return commons_pb2.STATUS_INTERNAL_ERROR
    # Return the response
    return response


def handle_srv6_usid_policy_complete(operation, nodes_filename,
                                     lr_destination, rl_destination,
                                     nodes=None, table=-1, metric=-1):
    '''
    Handle a SRv6 Policy using uSIDs

    :param operation: The operation to be performed on the uSID policy
                      (i.e. add, get, change, del)
    :type operation: str
    :param nodes_filename: Name of the YAML file containing the
                           mapping of node names to IP addresses
    :type nodes_filename: str
    :param destination: Destination of the SRv6 route
    :type destination: str
    :param nodes: Waypoints of the SRv6 route
    :type nodes: list
    :param device: Device of the SRv6 route. If not provided, the device
                   is selected automatically by the node.
    :type device: str, optional
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
    :raises InvalidSIDError: SID is wrong for one or more segments
    '''
    # pylint: disable=too-many-locals, too-many-arguments
    #
    # In order to perform this translation, a file containing the
    # mapping of node names to IPv6 addresses is required
    #
    # Create the SRv6 Policy
    try:
        # Read nodes from YAML file
        nodes_info, locator_bits, usid_id_bits = read_nodes(nodes_filename)
        # Prefix length for local segment
        prefix_len = locator_bits + usid_id_bits
        # Ingress node
        ingress_node = nodes_info[nodes[0]]
        # Intermediate nodes
        intermediate_nodes = list()
        for node in nodes[1:-1]:
            intermediate_nodes.append(nodes_info[node])
        # Egress node
        egress_node = nodes_info[nodes[-1]]
        # Extract the segments
        segments = list()
        for node in nodes:
            segments.append(nodes_info[node]['uN'])

        # Ingress node
        with utils.get_grpc_session(ingress_node['grpc_ip'],
                                    ingress_node['grpc_port']) as channel:
            # We need to convert the SID list into a uSID list
            #  before creating the SRv6 policy
            usid_list = sidlist_to_usidlist(
                sid_list=segments[1:] + [egress_node['uDT']],
                locator_bits=locator_bits,
                usid_id_bits=usid_id_bits
            )
            # Handle a SRv6 path
            response = handle_srv6_path(
                operation=operation,
                channel=channel,
                destination=lr_destination,
                segments=usid_list[::-1],
                encapmode='encap.red',
                table=table,
                metric=metric,
                fwd_engine=ingress_node['fwd_engine']
            )
            if response != commons_pb2.STATUS_SUCCESS:
                # Error
                return response
            # Create the uN behavior
            response = handle_srv6_behavior(
                operation=operation,
                channel=channel,
                segment='%s/%s' % (ingress_node['uN'], prefix_len),
                action='uN',
                fwd_engine=ingress_node['fwd_engine']
            )
            if response != commons_pb2.STATUS_SUCCESS:
                # Error
                return response
            # Create the End behavior
            response = handle_srv6_behavior(
                operation=operation,
                channel=channel,
                segment='%s/%s' % (ingress_node['uN'], 64),
                action='End',
                fwd_engine=ingress_node['fwd_engine']
            )
            if response != commons_pb2.STATUS_SUCCESS:
                # Error
                return response
            # Create the decap behavior
            response = handle_srv6_behavior(
                operation=operation,
                channel=channel,
                segment='%s/%s' % (ingress_node['uDT'], 64),
                action='End.DT6',
                lookup_table=254,
                fwd_engine=ingress_node['fwd_engine']
            )
            if response != commons_pb2.STATUS_SUCCESS:
                # Error
                return response
        # Intermediate nodes
        for node in intermediate_nodes:
            with utils.get_grpc_session(node['grpc_ip'],
                                        node['grpc_port']) as channel:
                # Create the uN behavior
                response = handle_srv6_behavior(
                    operation=operation,
                    channel=channel,
                    segment='%s/%s' % (node['uN'], prefix_len),
                    action='uN',
                    fwd_engine=node['fwd_engine']
                )
                if response != commons_pb2.STATUS_SUCCESS:
                    # Error
                    return response
        # Egress node
        with utils.get_grpc_session(egress_node['grpc_ip'],
                                    egress_node['grpc_port']) as channel:
            # Create the uN behavior
            response = handle_srv6_behavior(
                operation=operation,
                channel=channel,
                segment='%s/%s' % (egress_node['uN'], prefix_len),
                action='uN',
                fwd_engine=egress_node['fwd_engine']
            )
            if response != commons_pb2.STATUS_SUCCESS:
                # Error
                return response
            # Create the End behavior
            response = handle_srv6_behavior(
                operation=operation,
                channel=channel,
                segment='%s/%s' % (egress_node['uN'], 64),
                action='End',
                fwd_engine=egress_node['fwd_engine']
            )
            if response != commons_pb2.STATUS_SUCCESS:
                # Error
                return response
            # Create the decap behavior
            response = handle_srv6_behavior(
                operation=operation,
                channel=channel,
                segment='%s/%s' % (egress_node['uDT'], 64),
                action='End.DT6',
                lookup_table=254,
                fwd_engine=egress_node['fwd_engine']
            )
            if response != commons_pb2.STATUS_SUCCESS:
                # Error
                return response
            # We need to convert the SID list into a uSID list
            #  before creating the SRv6 policy
            usid_list = sidlist_to_usidlist(
                sid_list=segments[::-1][1:] + [ingress_node['uDT']],
                locator_bits=locator_bits,
                usid_id_bits=usid_id_bits
            )
            # Handle a SRv6 path
            response = handle_srv6_path(
                operation=operation,
                channel=channel,
                destination=rl_destination,
                segments=usid_list,
                encapmode='encap.red',
                table=table,
                metric=metric,
                fwd_engine=egress_node['fwd_engine']
            )
            if response != commons_pb2.STATUS_SUCCESS:
                # Error
                return response
    except (InvalidConfigurationError, NodeNotFoundError,
            TooManySegmentsError, SIDLocatorError, InvalidSIDError):
        return commons_pb2.STATUS_INTERNAL_ERROR
    # Return the response
    return response


def create_uni_srv6_tunnel(ingress_channel, egress_channel,
                           destination, segments, localseg=None,
                           bsid_addr='', fwd_engine='Linux'):
    '''
    Create a unidirectional SRv6 tunnel from <ingress> to <egress>

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
    :param fwd_engine: Forwarding engine for the SRv6 route. Default: Linux.
    :type fwd_engine: str, optional
    '''
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
                           of the SRv6 tunnel
    :type node_l_channel: class: `grpc._channel.Channel`
    :param node_r_channel: The gRPC Channel to the right endpoint (node_r)
                           of the SRv6 tunnel
    :type node_r_channel: class: `grpc._channel.Channel`
    :param sidlist_lr: The SID list to be installed on the packets going
                       from <node_l> to <node_r>
    :type sidlist_lr: list
    :param sidlist_rl: The SID list to be installed on the packets going
                       from <node_r> to <node_l>
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
    :param fwd_engine: Forwarding engine for the SRv6 route. Default: Linux.
    :type fwd_engine: str, optional
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

    :param ingress_channel: The gRPC Channel to the ingress node
    :type ingress_channel: class: `grpc._channel.Channel`
    :param egress_channel: The gRPC Channel to the egress node
    :type egress_channel: class: `grpc._channel.Channel`
    :param destination: The destination prefix of the SRv6 path.
                        It can be a IP address or a subnet.
    :type destination: str
    :param localseg: The local segment associated to the End.DT6 seg6local
                     function on the egress node. If the argument 'localseg'
                     isn't passed in, the End.DT6 function is not removed.
    :type localseg: str, optional
    :param fwd_engine: Forwarding engine for the SRv6 route. Default: Linux.
    :type fwd_engine: str, optional
    :param ignore_errors: Whether to ignore "No such process" errors or not
                          (default is False)
    :type ignore_errors: bool, optional
    '''
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
                           SRv6 tunnel (node_l)
    :type node_l_channel: class: `grpc._channel.Channel`
    :param node_r_channel: The gRPC channel to the right endpoint of the
                           SRv6 tunnel (node_r)
    :type node_r_channel: class: `grpc._channel.Channel`
    :param node_l: The IP address of the left endpoint of the SRv6 tunnel
    :type node_l: str
    :param node_r: The IP address of the right endpoint of the SRv6 tunnel
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
    :param fwd_engine: Forwarding engine for the SRv6 route. Default: Linux.
    :type fwd_engine: str, optional
    :param ignore_errors: Whether to ignore "No such process" errors or not
                          (default is False)
    :type ignore_errors: bool, optional
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
