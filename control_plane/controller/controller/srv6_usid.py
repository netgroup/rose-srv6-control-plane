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
import os
from ipaddress import IPv6Address

from pyaml import yaml

# Proto dependencies
import commons_pb2
# Controller dependencies
from controller import srv6_utils
from controller import utils
try:
    from controller import arangodb_driver
except ImportError:
    print('ArangoDB modules not installed')

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


class InvalidConfigurationError(srv6_utils.SRv6Exception):
    '''
    Configuration file is not valid.
    '''


class NodeNotFoundError(srv6_utils.SRv6Exception):
    '''
    Node not found error.
    '''


class TooManySegmentsError(srv6_utils.SRv6Exception):
    '''
    Too many segments error.
    '''


class SIDLocatorError(srv6_utils.SRv6Exception):
    '''
    SID Locator is invalid error.
    '''


class InvalidSIDError(srv6_utils.SRv6Exception):
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


def sidlist_to_usidlist(sid_list, udt_sids=None,
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
    if udt_sids is None:
        udt_sids = list()
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
    sid_list = list()
    for node in nodes:
        if node not in nodes_info:
            raise NodeNotFoundError
        sid_list.append(nodes_info[node]['uN'])
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


def validate_usid_id(usid_id):
    '''
    Validate a uSID identifier. A valid uSID id should be an integer in the
    range (0, 0xffff).

    :param usid_id: uSID idenfier to validate.
    :type usid_id: str
    :return: True if the uSID identifier is valid.
    :rtype: bool
    '''
    try:
        # A valid uSID id should be an integer in the range (0, 0xffff)
        return int(usid_id, 16) >= 0x0 and int(usid_id, 16) <= 0xffff
    except ValueError:
        # The uSID id is invalid
        return False
    return True


def usid_id_to_usid(usid_id, locator):
    '''
    Convert a uSID identifier into a SID.

    :param usid_id: uSID idenfier to convert.
    :type usid_id: str
    :param locator: Locator part to be used for the SID.
    :type locator: str
    :return: Generated SID.
    :rtype: str
    '''
    return str(IPv6Address(int(IPv6Address(locator)) +
                           (int(usid_id, 16) << 80)))


def handle_srv6_usid_policy(operation, nodes_filename=None,
                            lr_destination=None, rl_destination=None,
                            nodes_lr=None,
                            nodes_rl=None, table=-1, metric=-1,
                            persistency=True, _id=None, l_grpc_ip=None,
                            l_grpc_port=None, l_fwd_engine=None,
                            r_grpc_ip=None, r_grpc_port=None,
                            r_fwd_engine=None, decap_sid=None, locator=None):
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
    # pylint: disable=too-many-return-statements, too-many-branches
    # pylint: disable=too-many-statements
    #
    # ArangoDB params
    arango_url = os.getenv('ARANGO_URL')
    arango_user = os.getenv('ARANGO_USER')
    arango_password = os.getenv('ARANGO_PASSWORD')
    #
    # Validate arguments
    if lr_destination is None:
        if operation in ['add']:
            logger.error('"lr_destination" argument is mandatory for %s '
                         'operation', operation)
            return None
    if rl_destination is None:
        if operation in ['add']:
            logger.error('"rl_destination" argument is mandatory for %s '
                         'operation', operation)
            return None
    if nodes_lr is None:
        if operation in ['add']:
            logger.error('"nodes_lr" argument is mandatory for %s '
                         'operation', operation)
            return None
    if nodes_rl is None:
        pass
    if nodes_filename is None:
        if operation in ['add', 'del']:
            logger.error('"nodes_filename" argument is mandatory for %s '
                         'operation', operation)
            return None
    if operation == 'change':
        logger.error('Operation not yet implemented: %s', operation)
        return None
    if operation == 'get':
        if not persistency:
            logger.error('Error in get(): Persistency is disabled')
            return None
        # Connect to ArangoDB
        client = arangodb_driver.connect_arango(
            url=arango_url)     # TODO keep arango connection open
        # Connect to the db
        database = arangodb_driver.connect_srv6_usid_db(
            client=client,
            username=arango_user,
            password=arango_password
        )
        # Get the policy from the db
        policies = arangodb_driver.find_usid_policy(
            database=database,
            key=_id,
            lr_dst=lr_destination,
            rl_dst=rl_destination,
            lr_nodes=nodes_lr,
            rl_nodes=nodes_rl,
            table=table if table != -1 else None,
            metric=metric if metric != -1 else None
        )
        # Print policies
        print('\n\n*** uSID policies:')
        pprint.PrettyPrinter(indent=4).pprint(list(policies))
        print('\n\n')
        return 0
    if operation in ['add', 'del']:
        #
        # In order to perform this translation, a file containing the
        # mapping of node names to IPv6 addresses is required
        #
        # Read nodes from YAML file
        nodes_info, locator_bits, usid_id_bits = read_nodes(nodes_filename)

        # nodes = list()
        # if nodes_rl is not None:
        #     nodes = list(set(nodes_lr).union(set(nodes_rl)))
        # elif nodes_lr is not None:
        #     nodes = nodes_lr

        # nodes_array = []
        # if nodes_lr is not None:
        #     nodes_array.append(nodes_lr)
        # if nodes_rl is not None:
        #     nodes_array.append(nodes_rl)
        if nodes_lr is not None:
            nodes = nodes_lr
            for idx in range(len(nodes)):
                node = nodes[idx]
                # if node in nodes_info:
                #     # Config file contains node info, nothing to do
                #     pass
                # elif utils.validate_ipv6_address(node):
                if utils.validate_ipv6_address(node):
                    grpc_ip = None
                    grpc_port = None
                    un = None
                    udt = None
                    fwd_engine = None
                    if locator is None:
                        logger.error('locator is mandatory')
                        return None
                    if idx == 0:
                        # left node
                        if l_grpc_ip is None:
                            logger.error('l_grpc_ip is mandatory')
                            return None
                        if l_grpc_port is None:
                            logger.error('l_grpc_port is mandatory')
                        if l_fwd_engine is None:
                            logger.error('l_fwd_engine is mandatory')
                        if decap_sid is not None and \
                                not utils.validate_ipv6_address(decap_sid):
                            udt = usid_id_to_usid(decap_sid, locator)
                        grpc_ip = l_grpc_ip
                        grpc_port = l_grpc_port
                        fwd_engine = l_fwd_engine
                    elif idx == len(nodes) - 1:
                        # right node
                        if r_grpc_ip is None:
                            logger.error('r_grpc_ip is mandatory')
                            return None
                        if r_grpc_port is None:
                            logger.error('r_grpc_port is mandatory')
                        if r_fwd_engine is None:
                            logger.error('r_fwd_engine is mandatory')
                        if decap_sid is not None and \
                                not utils.validate_ipv6_address(decap_sid):
                            udt = usid_id_to_usid(decap_sid, locator)
                        grpc_ip = r_grpc_ip
                        grpc_port = r_grpc_port
                        fwd_engine = r_fwd_engine
                    nodes_info[str(node)] = {
                        'name': node,
                        'grpc_ip': grpc_ip,
                        'grpc_port': grpc_port,
                        'uN': node,
                        'uDT': udt,
                        'fwd_engine': fwd_engine
                    }
                elif validate_usid_id(node):
                    grpc_ip = None
                    grpc_port = None
                    un = None
                    udt = None
                    fwd_engine = None
                    if locator is None:
                        logger.error('locator is mandatory')
                        return None
                    if idx == 0:
                        if l_grpc_ip is None:
                            logger.error('l_grpc_ip is mandatory')
                            return None
                        if l_grpc_port is None:
                            logger.error('l_grpc_port is mandatory')
                            return None
                        if l_fwd_engine is None:
                            logger.error('l_fwd_engine is mandatory')
                            return None
                        if decap_sid is not None and \
                                not utils.validate_ipv6_address(decap_sid):
                            udt = usid_id_to_usid(decap_sid, locator)
                        grpc_ip = l_grpc_ip
                        grpc_port = l_grpc_port
                        fwd_engine = l_fwd_engine
                    if idx == len(nodes) - 1:
                        if r_grpc_ip is None:
                            logger.error('r_grpc_ip is mandatory')
                            return None
                        if r_grpc_port is None:
                            logger.error('r_grpc_port is mandatory')
                            return None
                        if r_fwd_engine is None:
                            logger.error('r_fwd_engine is mandatory')
                            return None
                        if decap_sid is not None and \
                                not utils.validate_ipv6_address(decap_sid):
                            udt = usid_id_to_usid(decap_sid, locator)
                        grpc_ip = r_grpc_ip
                        grpc_port = r_grpc_port
                        fwd_engine = r_fwd_engine
                    un = usid_id_to_usid(node, locator)
                    nodes_info[str(node)] = {
                        'name': node,
                        'grpc_ip': grpc_ip,
                        'grpc_port': grpc_port,
                        'uN': un,
                        'uDT': udt,
                        'fwd_engine': fwd_engine
                    }
                else:
                    # logger.error('Unknown node: %s', node)
                    # return None
                    pass
        if nodes_rl is not None:
            nodes = nodes_rl
            for idx in range(len(nodes)):
                node = nodes[idx]
                # if node in nodes_info:
                #     # Config file contains node info, nothing to do
                #     pass
                # elif utils.validate_ipv6_address(node):
                if utils.validate_ipv6_address(node):
                    grpc_ip = None
                    grpc_port = None
                    un = None
                    udt = None
                    fwd_engine = None
                    if locator is None:
                        logger.error('locator is mandatory')
                        return None
                    if idx == 0:
                        # left node
                        if l_grpc_ip is None:
                            logger.error('l_grpc_ip is mandatory')
                            return None
                        if l_grpc_port is None:
                            logger.error('l_grpc_port is mandatory')
                        if l_fwd_engine is None:
                            logger.error('l_fwd_engine is mandatory')
                        if decap_sid is not None and \
                                not utils.validate_ipv6_address(decap_sid):
                            udt = usid_id_to_usid(decap_sid, locator)
                        grpc_ip = r_grpc_ip
                        grpc_port = r_grpc_port
                        fwd_engine = r_fwd_engine
                    elif idx == len(nodes) - 1:
                        # right node
                        if r_grpc_ip is None:
                            logger.error('r_grpc_ip is mandatory')
                            return None
                        if r_grpc_port is None:
                            logger.error('r_grpc_port is mandatory')
                        if r_fwd_engine is None:
                            logger.error('r_fwd_engine is mandatory')
                        if decap_sid is not None and \
                                not utils.validate_ipv6_address(decap_sid):
                            udt = usid_id_to_usid(decap_sid, locator)
                        grpc_ip = l_grpc_ip
                        grpc_port = l_grpc_port
                        fwd_engine = l_fwd_engine
                    nodes_info[node] = {
                        'name': node,
                        'grpc_ip': grpc_ip,
                        'grpc_port': grpc_port,
                        'uN': node,
                        'uDT': udt,
                        'fwd_engine': fwd_engine
                    }
                elif validate_usid_id(node):
                    grpc_ip = None
                    grpc_port = None
                    un = None
                    udt = None
                    fwd_engine = None
                    if locator is None:
                        logger.error('locator is mandatory')
                        return None
                    if idx == 0:
                        if l_grpc_ip is None:
                            logger.error('l_grpc_ip is mandatory')
                            return None
                        if l_grpc_port is None:
                            logger.error('l_grpc_port is mandatory')
                            return None
                        if l_fwd_engine is None:
                            logger.error('l_fwd_engine is mandatory')
                            return None
                        if decap_sid is not None and \
                                not utils.validate_ipv6_address(decap_sid):
                            udt = usid_id_to_usid(decap_sid, locator)
                        grpc_ip = r_grpc_ip
                        grpc_port = r_grpc_port
                        fwd_engine = r_fwd_engine
                    if idx == len(nodes) - 1:
                        if r_grpc_ip is None:
                            logger.error('r_grpc_ip is mandatory')
                            return None
                        if r_grpc_port is None:
                            logger.error('r_grpc_port is mandatory')
                            return None
                        if r_fwd_engine is None:
                            logger.error('r_fwd_engine is mandatory')
                            return None
                        if decap_sid is not None and \
                                not utils.validate_ipv6_address(decap_sid):
                            udt = usid_id_to_usid(decap_sid, locator)
                        grpc_ip = l_grpc_ip
                        grpc_port = l_grpc_port
                        fwd_engine = l_fwd_engine
                    un = usid_id_to_usid(node, locator)
                    nodes_info[node] = {
                        'name': node,
                        'grpc_ip': grpc_ip,
                        'grpc_port': grpc_port,
                        'uN': un,
                        'uDT': udt,
                        'fwd_engine': fwd_engine
                    }
                else:
                    # logger.error('Unknown node: %s', node)
                    # return None
                    pass
        # Add
        if operation == 'add':
            policies = [{
                'lr_dst': lr_destination,
                'rl_dst': rl_destination,
                'lr_nodes': nodes_lr,
                'rl_nodes': nodes_rl
            }]
        if operation == 'del':
            #
            # Connect to ArangoDB
            client = arangodb_driver.connect_arango(
                url=arango_url)     # TODO keep arango connection open
            # Connect to the db
            database = arangodb_driver.connect_srv6_usid_db(
                client=client,
                username=arango_user,
                password=arango_password
            )
            # Get the policy from the db
            policies = arangodb_driver.find_usid_policy(
                database=database,
                key=_id,
                lr_dst=lr_destination,
                rl_dst=rl_destination,
                lr_nodes=nodes_lr,
                rl_nodes=nodes_rl,
                table=table if table != -1 else None,
                metric=metric if metric != -1 else None
            )

            policies = list(policies)
            for policy in policies:
                # nodes = list()
                # if policy.get('rl_nodes') is not None:
                #     nodes = list(set(policy['lr_nodes']).union(set(policy['rl_nodes'])))
                # elif policy.get('lr_nodes') is not None:
                #     nodes = policy['lr_nodes']

                # nodes_array = []
                # if policy.get('lr_nodes') is not None:
                #     nodes_array.append(policy.get('lr_nodes'))
                # if policy.get('rl_nodes') is not None:
                #     nodes_array.append(policy.get('rl_nodes'))
                # print('naaaa', nodes_array)
                if policy.get('lr_nodes') is not None:
                    nodes = policy.get('lr_nodes')
                    for idx in range(len(nodes)):
                        node = str(nodes[idx])
                        print('/*************************', node)
                        #if node in nodes_info:
                        #    # Config file contains node info, nothing to do
                        #    pass
                        #elif utils.validate_ipv6_address(node):
                        if utils.validate_ipv6_address(node):
                            grpc_ip = None
                            grpc_port = None
                            un = None
                            udt = None
                            fwd_engine = None
                            if idx == 0:
                                # left node
                                if policy.get('decap_sid') is not None and \
                                        not utils.validate_ipv6_address(policy.get('decap_sid')):
                                    udt = usid_id_to_usid(policy['decap_sid'], policy['locator'])
                                grpc_ip = policy.get('l_grpc_ip')
                                grpc_port = policy.get('l_grpc_port')
                                fwd_engine = policy.get('l_fwd_engine')
                                locator = policy['locator']
                            elif idx == len(nodes) - 1:
                                # right node
                                if policy.get('decap_sid') is not None and \
                                        not utils.validate_ipv6_address(policy.get('decap_sid')):
                                    udt = usid_id_to_usid(policy['decap_sid'], policy['locator'])
                                grpc_ip = policy.get('r_grpc_ip')
                                grpc_port = policy.get('r_grpc_port')
                                fwd_engine = policy.get('r_fwd_engine')
                                locator = policy['locator']
                            nodes_info[node] = {
                                'name': node,
                                'grpc_ip': grpc_ip,
                                'grpc_port': grpc_port,
                                'uN': node,
                                'uDT': udt,
                                'fwd_engine': fwd_engine
                            }
                        elif validate_usid_id(node):
                            grpc_ip = None
                            grpc_port = None
                            un = None
                            udt = None
                            fwd_engine = None
                            if idx == 0:
                                # left node
                                if policy.get('decap_sid') is not None and \
                                        not utils.validate_ipv6_address(policy.get('decap_sid')):
                                    udt = usid_id_to_usid(policy['decap_sid'], policy['locator'])
                                grpc_ip = policy.get('l_grpc_ip')
                                grpc_port = policy.get('l_grpc_port')
                                fwd_engine = policy.get('l_fwd_engine')
                                locator = policy['locator']
                            elif idx == len(nodes) - 1:
                                # right node
                                if policy.get('decap_sid') is not None and \
                                        not utils.validate_ipv6_address(policy.get('decap_sid')):
                                    udt = usid_id_to_usid(policy['decap_sid'], policy['locator'])
                                grpc_ip = policy.get('r_grpc_ip')
                                grpc_port = policy.get('r_grpc_port')
                                fwd_engine = policy.get('r_fwd_engine')
                                locator = policy['locator']
                            un = usid_id_to_usid(node, locator)
                            nodes_info[node] = {
                                'name': node,
                                'grpc_ip': grpc_ip,
                                'grpc_port': grpc_port,
                                'uN': un,
                                'uDT': udt,
                                'fwd_engine': fwd_engine
                            }
                            print('nininin\n\n\n', nodes_info[node])
                        else:
                            # logger.error('Unknown node: %s', node)
                            # return None
                            pass
                if policy.get('rl_nodes') is not None:
                    nodes = policy.get('rl_nodes')
                    for idx in range(len(nodes)):
                        node = nodes[idx]
                        #if node in nodes_info:
                        #    # Config file contains node info, nothing to do
                        #    pass
                        #elif utils.validate_ipv6_address(node):
                        if utils.validate_ipv6_address(node):
                            grpc_ip = None
                            grpc_port = None
                            un = None
                            udt = None
                            fwd_engine = None
                            if idx == 0:
                                # left node
                                if policy.get('decap_sid') is not None and \
                                        not utils.validate_ipv6_address(policy.get('decap_sid')):
                                    udt = usid_id_to_usid(policy['decap_sid'], policy['locator'])
                                grpc_ip = policy.get('r_grpc_ip')
                                grpc_port = policy.get('r_grpc_port')
                                fwd_engine = policy.get('r_fwd_engine')
                                locator = policy['locator']
                            elif idx == len(nodes) - 1:
                                # right node
                                if policy.get('decap_sid') is not None and \
                                        not utils.validate_ipv6_address(policy.get('decap_sid')):
                                    udt = usid_id_to_usid(policy['decap_sid'], policy['locator'])
                                grpc_ip = policy.get('l_grpc_ip')
                                grpc_port = policy.get('l_grpc_port')
                                fwd_engine = policy.get('l_fwd_engine')
                                locator = policy['locator']
                            nodes_info[str(node)] = {
                                'name': node,
                                'grpc_ip': grpc_ip,
                                'grpc_port': grpc_port,
                                'uN': node,
                                'uDT': udt,
                                'fwd_engine': fwd_engine
                            }
                        elif validate_usid_id(node):
                            grpc_ip = None
                            grpc_port = None
                            un = None
                            udt = None
                            fwd_engine = None
                            if idx == 0:
                                # left node
                                if policy.get('decap_sid') is not None and \
                                        not utils.validate_ipv6_address(policy.get('decap_sid')):
                                    udt = usid_id_to_usid(policy['decap_sid'], policy['locator'])
                                grpc_ip = policy.get('r_grpc_ip')
                                grpc_port = policy.get('r_grpc_port')
                                fwd_engine = policy.get('r_fwd_engine')
                                locator = policy['locator']
                            elif idx == len(nodes) - 1:
                                # right node
                                if policy.get('decap_sid') is not None and \
                                        not utils.validate_ipv6_address(policy.get('decap_sid')):
                                    udt = usid_id_to_usid(policy['decap_sid'], policy['locator'])
                                grpc_ip = policy.get('l_grpc_ip')
                                grpc_port = policy.get('l_grpc_port')
                                fwd_engine = policy.get('l_fwd_engine')
                                locator = policy['locator']
                            un = usid_id_to_usid(node, locator)
                            nodes_info[str(node)] = {
                                'name': node,
                                'grpc_ip': grpc_ip,
                                'grpc_port': grpc_port,
                                'uN': un,
                                'uDT': udt,
                                'fwd_engine': fwd_engine
                            }
                            print('nininin\n\n\n', nodes_info[node])
                        else:
                            # logger.error('Unknown node: %s', node)
                            # return None
                            pass
        print('\n\n', nodes_info)
        if len(policies) == 0:
            logger.error('Policy not found')
            return None
        # Iterate on the policies
        for policy in policies:
            print(1)
            lr_destination = policy.get('lr_dst')
            rl_destination = policy.get('rl_dst')
            nodes_lr = policy.get('lr_nodes')
            nodes_rl = policy.get('rl_nodes')
            _id = policy.get('_key')
            #
            # If right to left nodes list is not provided, we use the reverse
            # left to right SID list (symmetric path)
            if nodes_rl is None:
                nodes_rl = nodes_lr[::-1]
            # The two SID lists must have the same endpoints
            if nodes_lr[0] != nodes_rl[-1] or nodes_rl[0] != nodes_lr[-1]:
                logger.error('Bad tunnel endpoints')
                return None
            # Create the SRv6 Policy
            try:
                print(2)
                # # Prefix length for local segment
                # prefix_len = locator_bits + usid_id_bits
                # Ingress node
                print(nodes_info)
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
                                            ingress_node['grpc_port']
                                            ) as channel:
                    print(3)
                    # Currently ony Linux and VPP are suppoted for the encap
                    if ingress_node['fwd_engine'] not in ['Linux', 'VPP']:
                        logger.error(
                            'Encap operation is not supported for '
                            '%s with fwd engine %s',
                            ingress_node['name'],
                            ingress_node['fwd_engine'])
                        return commons_pb2.STATUS_INTERNAL_ERROR
                    # VPP requires a BSID address
                    bsid_addr = ''
                    if ingress_node['fwd_engine'] == 'VPP':
                        for char in lr_destination:
                            if char not in ('0', ':'):
                                bsid_addr += char
                        add_colon = False
                        if len(bsid_addr) <= 28:
                            add_colon = True
                        bsid_addr = [(bsid_addr[i:i + 4])
                                     for i in range(0, len(bsid_addr), 4)]
                        bsid_addr = ':'.join(bsid_addr)
                        if add_colon:
                            bsid_addr += '::'

                    udt_sids = list()
                    # Locator mask
                    locator_mask = str(IPv6Address(
                        int('1' * 128, 2) ^
                        int('1' * (128 - locator_bits), 2)))
                    # uDT mask
                    udt_mask_1 = str(
                        IPv6Address(int('1' * usid_id_bits, 2) <<
                                    (128 - locator_bits - usid_id_bits)))
                    udt_mask_2 = str(
                        IPv6Address(int('1' * usid_id_bits, 2) <<
                                    (128 - locator_bits - 2 * usid_id_bits)))
                    # Build uDT sid list
                    locator_int = int(IPv6Address(egress_node['uDT'])) & \
                        int(IPv6Address(locator_mask))
                    udt_mask_1_int = int(IPv6Address(egress_node['uDT'])) & \
                        int(IPv6Address(udt_mask_1))
                    udt_mask_2_int = int(IPv6Address(egress_node['uDT'])) & \
                        int(IPv6Address(udt_mask_2))
                    udt_sids += [str(IPv6Address(locator_int +
                                                 udt_mask_1_int))]
                    udt_sids += [str(IPv6Address(locator_int +
                                                 (udt_mask_2_int <<
                                                  usid_id_bits)))]
                    # We need to convert the SID list into a uSID list
                    #  before creating the SRv6 policy
                    usid_list = sidlist_to_usidlist(
                        sid_list=segments_lr[1:][:-1],
                        udt_sids=[segments_lr[1:][-1]] + udt_sids,
                        locator_bits=locator_bits,
                        usid_id_bits=usid_id_bits
                    )

                    print(ingress_node)
                    print(operation)
                    print(lr_destination)
                    print(usid_list)
                    print(table)
                    print(metric)
                    print(bsid_addr)
                    print(ingress_node['fwd_engine'])

                    # Handle a SRv6 path
                    response = srv6_utils.handle_srv6_path(
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
                #                                 node['grpc_port']
                #                                 ) as channel:
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
                                            egress_node['grpc_port']
                                            ) as channel:
                    print(4)
                    # Currently ony Linux and VPP are suppoted for the encap
                    if egress_node['fwd_engine'] not in ['Linux', 'VPP']:
                        logger.error(
                            'Encap operation is not supported for '
                            '%s with fwd engine %s',
                            egress_node['name'], egress_node['fwd_engine'])
                        return commons_pb2.STATUS_INTERNAL_ERROR
                    # VPP requires a BSID address
                    bsid_addr = ''
                    if egress_node['fwd_engine'] == 'VPP':
                        for char in lr_destination:
                            if char not in ('0', ':'):
                                bsid_addr += char
                        add_colon = False
                        if len(bsid_addr) <= 28:
                            add_colon = True
                        bsid_addr = [(bsid_addr[i:i + 4])
                                     for i in range(0, len(bsid_addr), 4)]
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
                    locator_mask = str(IPv6Address(
                        int('1' * 128, 2) ^
                        int('1' * (128 - locator_bits), 2)))
                    # uDT mask
                    udt_mask_1 = str(IPv6Address(int('1' * usid_id_bits, 2) <<
                                                 (128 - locator_bits -
                                                  usid_id_bits)))
                    udt_mask_2 = str(IPv6Address(int('1' * usid_id_bits, 2) <<
                                                 (128 - locator_bits -
                                                  2 * usid_id_bits)))
                    # Build uDT sid list
                    locator_int = int(
                        IPv6Address(
                            ingress_node['uDT'])) & int(
                                IPv6Address(locator_mask))
                    udt_mask_1_int = int(
                        IPv6Address(
                            ingress_node['uDT'])) & int(
                                IPv6Address(udt_mask_1))
                    udt_mask_2_int = int(
                        IPv6Address(
                            ingress_node['uDT'])) & int(
                                IPv6Address(udt_mask_2))
                    udt_sids += [str(IPv6Address(locator_int +
                                                 udt_mask_1_int))]
                    udt_sids += [str(IPv6Address(locator_int +
                                                 (udt_mask_2_int <<
                                                  usid_id_bits)))]
                    # We need to convert the SID list into a uSID list
                    #  before creating the SRv6 policy
                    usid_list = sidlist_to_usidlist(
                        sid_list=segments_rl[1:][:-1],
                        udt_sids=[segments_rl[1:][-1]] + udt_sids,
                        locator_bits=locator_bits,
                        usid_id_bits=usid_id_bits
                    )

                    print()
                    print(egress_node)
                    print(operation)
                    print(rl_destination)
                    print(usid_list)
                    print(table)
                    print(metric)
                    print(bsid_addr)
                    print(egress_node['fwd_engine'])
                    # Handle a SRv6 path
                    response = srv6_utils.handle_srv6_path(
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
                # Persist uSID policy to database
                if persistency:
                    print(5)
                    if operation == 'add':
                        # Connect to ArangoDB
                        client = arangodb_driver.connect_arango(
                            url=arango_url)  # TODO keep arango connection open
                        # Connect to the db
                        database = arangodb_driver.connect_srv6_usid_db(
                            client=client,
                            username=arango_user,
                            password=arango_password
                        )
                        # Save the policy to the db
                        arangodb_driver.insert_usid_policy(
                            database=database,
                            lr_dst=lr_destination,
                            rl_dst=rl_destination,
                            lr_nodes=nodes_lr,
                            rl_nodes=nodes_rl,
                            table=table if table != -1 else None,
                            metric=metric if metric != -1 else None,
                            l_grpc_ip = l_grpc_ip,
                            l_grpc_port = l_grpc_port,
                            l_fwd_engine = l_fwd_engine,
                            r_grpc_ip = r_grpc_ip,
                            r_grpc_port = r_grpc_port,
                            r_fwd_engine = r_fwd_engine,
                            decap_sid = decap_sid,
                            locator = locator
                        )
                    elif operation == 'del':
                        # TODO keep arango connection open
                        # Connect to ArangoDB
                        client = arangodb_driver.connect_arango(
                            url=arango_url)
                        # Connect to the db
                        database = arangodb_driver.connect_srv6_usid_db(
                            client=client,
                            username=arango_user,
                            password=arango_password
                        )
                        # Save the policy to the db
                        arangodb_driver.delete_usid_policy(
                            database=database,
                            key=_id,
                            lr_dst=lr_destination,
                            rl_dst=rl_destination,
                            lr_nodes=nodes_lr,
                            rl_nodes=nodes_rl,
                            table=table if table != -1 else None,
                            metric=metric if metric != -1 else None
                        )
                    else:
                        print('errrrr')
                        logger.error('Unsupported operation: %s', operation)
                    print(6)
            except (InvalidConfigurationError, NodeNotFoundError,
                    TooManySegmentsError, SIDLocatorError, InvalidSIDError):
                return commons_pb2.STATUS_INTERNAL_ERROR
        # Return the response
        return response
    logger.error('Unsupported operation: %s', operation)
    return None
