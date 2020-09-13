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
from ipaddress import ip_address
import logging
import grpc

# Proto dependencies
import commons_pb2
# Controller dependencies
import srv6_manager_pb2
import srv6_manager_pb2_grpc
from controller import utils
from controller import srv6_path
from controller import srv6_behavior
from controller import srv6_tunnel


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


# Initialize the list of the SRv6 handlers
srv6_handlers = list()


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


def add_srv6_entities(srv6_entities, grpc_channels=None):
    '''
    Add a set of SRv6 entities (e.g. paths, behaviors, tunnels).

    :param srv6_entities: A set containing the entities to add.
    :type srv6_entities: set
    :param grpc_channels: A list containing references to open gRPC channels.
                          This parameter can be used to reuse open channels
                          in order to improve the efficiency. To add a
                          SRv6 entity from a node, we first check if we have
                          an active gRPC channel to the node. If a channel is
                          available can use it, otherwise we need to open a
                          new channel to the node.
    :type grpc_channels: list, optional
    :return: A set of added entities.
    :rtype: set
    '''
    # If the persistency is enabled on the controller,  check some entities
    # already exist
    if utils.persistency_enabled():
        # Iterate on the entity handlers
        for handlers in srv6_handlers:
            # Extract the verifier
            #verifier = handlers['check_entities']  TODO
            # Check for the entities existency
            #verifier(srv6_entities) TODO
            pass
    # Initialize grpc_channels, if it is None
    grpc_channels = grpc_channels if grpc_channels is not None else []
    # Convert the grpc_channels list to a dict
    # This allows to make the access to the data structure simpler
    address_to_channel = dict()
    for grpc_channel in grpc_channels:
        # Extract the IP address of the target of the gRPC channel from the
        # channel
        import re
        search_results = re.finditer(r'\[.*?\]', grpc_channel._channel.target().decode())
        for item in search_results:
            grpc_address = \
                str(item.group(0))
            if grpc_address[0] == '[':
                grpc_address = grpc_address[1:]
            if grpc_address[-1] == ']':
                grpc_address = grpc_address[:-1]
            grpc_address = \
                str(ip_address(grpc_address))
            break
        # Add the mapping IP address - channel to the address_to_channel dict
        address_to_channel[grpc_address] = grpc_channel
    # Dict containing the SRv6ManagerRequest objects indexed by the IP address
    # of the target
    requests = dict()
    # Iterate on the entity handlers
    for handlers in srv6_handlers:
        # Extract the encoder
        encoder = handlers['encode_entities']
        # Encode the entities
        # This will convert the SRv6 entities to gRPC representations and will
        # add these representation to the request message
        encoder(srv6_entities, requests)
    # The entities processed by the encoder are removed from the srv6_entities
    # set; as we expect that all the entities have been processed by the
    # encoders, we chack that the srv6_entities is empty
    if len(srv6_entities) != 0:
        logger.error('Not all the entities have been processed')
        raise utils.InvalidArgumentError
    # Send the requests
    for grpc_address, request in requests.items():
        # Retrieve the channel to the gRPC address from the address_to_channel
        # dict; if no channel is present, grpc_channel will be set to None
        grpc_channel = address_to_channel.get(ip_address(grpc_address))
        # Flag used to indicate whether the channel must be closed or not
        # after the RPC
        close_channel = False
        try:
            # If no channel is available we need to open a new one
            if grpc_channel is None:
                # Get the channel
                grpc_channel = utils.get_grpc_session(grpc_address, 12345)  # FIXME
                # Enable the close flag to state that the channel must be
                # closed after the RPC
                close_channel = True
            # Get the reference of the stub
            stub = srv6_manager_pb2_grpc.SRv6ManagerStub(grpc_channel)
            # Create the SRv6 entities
            response = stub.Create(request)
            # Get the status code of the gRPC operation
            response = response.status
        except grpc.RpcError as err:
            # An error occurred during the gRPC operation
            # Parse the error and return it
            response = parse_grpc_error(err)
        finally:
            # Close the channel, if required
            if close_channel:
                grpc_channel.close()
        # Check if response is success; if not, we raise an exception
        utils.raise_exception_on_error(response)
    # Iterate on the entity handlers
    for handlers in srv6_handlers:
        # Extract the db remover
        db_saver = handlers['save_entities_to_db']
        # Save the entities to the database
        db_saver(srv6_entities)        # TODO This set is empty
    # No exception raised, so the operation completed successfully and
    # we return the entities added to the nodes
    return srv6_entities


def get_srv6_entities(srv6_entities, grpc_channels=None, first_match=False):
    '''
    Retrieve a set of SRv6 entities (e.g. paths, behaviors, tunnels).

    :param srv6_entities: A set containing the entities to get.
    :type srv6_entities: set
    :param grpc_channels: A list containing references to open gRPC channels.
                          This parameter can be used to reuse open channels
                          in order to improve the efficiency. To update a
                          SRv6 entity from a node, we first check if we have
                          an active gRPC channel to the node. If a channel is
                          available can use it, otherwise we need to open a
                          new channel to the node.
    :type grpc_channels: list, optional
    :return: A set of retrieved entities.
    :rtype: set
    '''
    # If the persistency is enabled on the controller, we first look up the
    # entities in the database
    # If an entity does not exist an exception will be raised
    # The entities are augmented with the information contained into the db
    if utils.persistency_enabled():
        # Iterate on the entity handlers
        for handlers in srv6_handlers:
            # Take the augmenter
            augmenter = handlers['augment_entities']
            # Augment the entities
            augmenter(srv6_entities, first_match=first_match)
        # Done, we have retrieved the results from the database
        return srv6_entities
    # Initialize grpc_channels, if it is None
    grpc_channels = grpc_channels if grpc_channels is not None else []
    # Convert the grpc_channels list to a dict
    # This allows to make the access to the data structure simpler
    address_to_channel = dict()
    for grpc_channel in grpc_channels:
        # Extract the IP address of the target of the gRPC channel from the
        # channel
        import re
        search_results = re.finditer(r'\[.*?\]', grpc_channel._channel.target().decode())
        for item in search_results:
            grpc_address = \
                str(item.group(0))
            if grpc_address[0] == '[':
                grpc_address = grpc_address[1:]
            if grpc_address[-1] == ']':
                grpc_address = grpc_address[:-1]
            grpc_address = \
                str(ip_address(grpc_address))
            break
        # Add the mapping IP address - channel to the address_to_channel dict
        address_to_channel[grpc_address] = grpc_channel
    # Dict containing the SRv6ManagerRequest objects indexed by the IP address
    # of the target
    requests = dict()
    # Iterate on the entity handlers
    for handlers in srv6_handlers:
        # Extract the encoder
        encoder = handlers['encode_entities']
        # Encode the entities
        # This will convert the SRv6 entities to gRPC representations and will
        # add these representation to the request message
        encoder(srv6_entities, requests)
    # The entities processed by the encoder are removed from the srv6_entities
    # set; as we expect that all the entities have been processed by the
    # encoders, we chack that the srv6_entities is empty
    if len(srv6_entities) != 0:
        logger.error('Not all the entities have been processed')
        raise utils.InvalidArgumentError
    # Initialize the set of the retrieved entities
    srv6_entities = set()
    # Send the requests
    for grpc_address, request in requests.items():
        # Retrieve the channel to the gRPC address from the address_to_channel
        # dict; if no channel is present, grpc_channel will be set to None
        grpc_channel = address_to_channel.get(ip_address(grpc_address))
        # Flag used to indicate whether the channel must be closed or not
        # after the RPC
        close_channel = False
        try:
            # If no channel is available we need to open a new one
            if grpc_channel is None:
                # Get the channel
                grpc_channel = utils.get_grpc_session(grpc_address, 12345)  # FIXME
                # Enable the close flag to state that the channel must be
                # closed after the RPC
                close_channel = True
            # Get the reference of the stub
            stub = srv6_manager_pb2_grpc.SRv6ManagerStub(grpc_channel)
            # Get the SRv6 entities
            res = stub.Get(request)
            # Get the status code of the gRPC operation
            response = res.status
        except grpc.RpcError as err:
            # An error occurred during the gRPC operation
            # Parse the error and return it
            response = parse_grpc_error(err)
        finally:
            # Close the channel, if required
            if close_channel:
                grpc_channel.close()
        # Check if response is success; if not, we raise an exception
        utils.raise_exception_on_error(response)
        # No exception raised, so the operation completed successfully and
        # we return the entities retrieved from the nodes
        #
        # Decode the entities
        #
        # Iterate on the entity handlers
        for handlers in srv6_handlers:
            # Extract the decoder
            decoder = handlers['decode_entities']
            # Decode the entities
            # This will convert the gRPC represnetation to SRv6 entities and
            # will add these representation to the srv6_entities set
            decoder(srv6_entities, res)
    # Return the entities
    return srv6_entities


def change_srv6_entities(srv6_entities, grpc_channels=None):
    '''
    Update a set of SRv6 entities (e.g. paths, behaviors, tunnels).

    :param srv6_entities: A set containing the entities to update.
    :type srv6_entities: set
    :param grpc_channels: A list containing references to open gRPC channels.
                          This parameter can be used to reuse open channels
                          in order to improve the efficiency. To update a
                          SRv6 entity from a node, we first check if we have
                          an active gRPC channel to the node. If a channel is
                          available can use it, otherwise we need to open a
                          new channel to the node.
    :type grpc_channels: list, optional
    :return: A set of updated entities.
    :rtype: set
    '''
    raise NotImplementedError


def del_srv6_entities(srv6_entities, grpc_channels=None, first_match=False):
    '''
    Delete a set of SRv6 entities (e.g. paths, behaviors, tunnels).

    :param srv6_entities: A set containing the entities to remove.
    :type srv6_entities: set
    :param grpc_channels: A list containing references to open gRPC channels.
                          This parameter can be used to reuse open channels
                          in order to improve the efficiency. To remove a
                          SRv6 entity from a node, we first check if we have
                          an active gRPC channel to the node. If a channel is
                          available can use it, otherwise we need to open a
                          new channel to the node.
    :type grpc_channels: list, optional
    :param first_match: If set, only the first match will be removed
                        (default: False).
    :type first_match: bool, optional
    :return: A set of removed entities.
    :rtype: set
    '''
    # If the persistency is enabled on the controller, we first look up the
    # entities in the database
    # If an entity does not exist an exception will be raised
    # The entities are augmented with the information contained into the db
    if utils.persistency_enabled():
        # Iterate on the entity handlers
        for handlers in srv6_handlers:
            # Take the augmenter
            augmenter = handlers['augment_entities']
            # Augment the entities
            augmenter(srv6_entities, first_match=first_match)
    # Initialize grpc_channels, if it is None
    grpc_channels = grpc_channels if grpc_channels is not None else []
    # Convert the grpc_channels list to a dict
    # This allows to make the access to the data structure simpler
    address_to_channel = dict()
    for grpc_channel in grpc_channels:
        # Extract the IP address of the target of the gRPC channel from the
        # channel
        import re
        search_results = re.finditer(r'\[.*?\]', grpc_channel._channel.target().decode())
        for item in search_results:
            grpc_address = \
                str(item.group(0))
            if grpc_address[0] == '[':
                grpc_address = grpc_address[1:]
            if grpc_address[-1] == ']':
                grpc_address = grpc_address[:-1]
            grpc_address = \
                str(ip_address(grpc_address))
            break
        # Add the mapping IP address - channel to the address_to_channel dict
        address_to_channel[grpc_address] = grpc_channel
    # Dict containing the SRv6ManagerRequest objects indexed by the IP address
    # of the target
    requests = dict()
    # Iterate on the entity handlers
    for handlers in srv6_handlers:
        # Extract the encoder
        encoder = handlers['encode_entities']
        # Encode the entities
        # This will convert the SRv6 entities to gRPC representations and will
        # add these representation to the request message
        encoder(srv6_entities, requests)
    # The entities processed by the encoder are removed from the srv6_entities
    # set; as we expect that all the entities have been processed by the
    # encoders, we chack that the srv6_entities is empty
    if len(srv6_entities) != 0:
        logger.error('Not all the entities have been processed')
        raise utils.InvalidArgumentError
    # Send the requests
    for grpc_address, request in requests.items():
        # Retrieve the channel to the gRPC address from the address_to_channel
        # dict; if no channel is present, grpc_channel will be set to None
        grpc_channel = address_to_channel.get(ip_address(grpc_address))
        # Flag used to indicate whether the channel must be closed or not
        # after the RPC
        close_channel = False
        try:
            # If no channel is available we need to open a new one
            if grpc_channel is None:
                # Get the channel
                grpc_channel = utils.get_grpc_session(grpc_address, 12345)  # FIXME
                # Enable the close flag to state that the channel must be
                # closed after the RPC
                close_channel = True
            # Get the reference of the stub
            stub = srv6_manager_pb2_grpc.SRv6ManagerStub(grpc_channel)
            # Remove the SRv6 entities
            response = stub.Remove(request)
            # Get the status code of the gRPC operation
            response = response.status
        except grpc.RpcError as err:
            # An error occurred during the gRPC operation
            # Parse the error and return it
            response = parse_grpc_error(err)
        finally:
            # Close the channel, if required
            if close_channel:
                grpc_channel.close()
        # Check if response is success; if not, we raise an exception
        utils.raise_exception_on_error(response)
    # Iterate on the entity handlers
    for handlers in srv6_handlers:
        # Extract the db remover
        db_remover = handlers['remove_entities_from_db']
        # Remove the entities from the database
        db_remover(srv6_entities)        # TODO
    # No exception raised, so the operation completed successfully and
    # we return the entities removed from the nodes
    return srv6_entities


def handle_srv6_entities(operation, srv6_entities, grpc_channels=None,
                         first_match=False):
    '''
    Create, get, change or delete a set of SRv6 entities (e.g. paths,
    behaviors, tunnels).

    :param operation: The operation to perform (i.e. add, get, change or del)
    :type: str
    :param srv6_entities: A set containing the entities to create or
                          manipulate.
    :type srv6_entities: set
    :param grpc_channels: A list containing references to open gRPC channels.
                          This parameter can be used to reuse open channels
                          in order to improve the efficiency. To install a
                          SRv6 entity in a node, we first check if we have an
                          active gRPC channel to the node. If a channel is
                          available can use it, otherwise we need to open a
                          new channel to the node.
    :type grpc_channels: list, optional
    :param first_match: If set, only the first match will be returned by the
                        get operation or removed by the del operation
                        (default: False).
    :type first_match: bool, optional
    :return: A set of entities added, retrieved, updated or removed.
    :rtype: set
    '''
    # Dispatch the operation
    if operation == 'add':
        # "Add" operation
        return add_srv6_entities(srv6_entities, grpc_channels)
    if operation == 'get':
        # "Get" operation
        return get_srv6_entities(srv6_entities, grpc_channels, first_match)
    if operation == 'change':
        # "Change" operation
        return change_srv6_entities(srv6_entities, grpc_channels)
    if operation == 'del':
        # "Delete" operation
        return del_srv6_entities(srv6_entities, grpc_channels, first_match)
    # If we reach this point, the operation is unknown
    logger.error('Invalid action')
    raise utils.InvalidArgumentError


def handle_srv6_path(operation, channel, destination, segments=None,
                     device='', encapmode="encap", table=-1, metric=-1,
                     bsid_addr='', fwd_engine='Linux'):
    '''
    Handle a SRv6 Path.
    This function has been deprecated. Use handle_srv6_entities instead.
    '''
    import re
    search_results = re.finditer(r'\[.*?\]', channel._channel.target().decode())
    for item in search_results:
        grpc_address = \
            str(item.group(0))
        if grpc_address[0] == '[':
            grpc_address = grpc_address[1:]
        if grpc_address[-1] == ']':
            grpc_address = grpc_address[:-1]
        grpc_address = \
            str(ip_address(grpc_address))
        break
    sr_path = srv6_path.SRv6Path(
        grpc_address=grpc_address,
        destination=destination,
        segments=segments,
        device=device,
        encapmode=encapmode,
        table=table,
        metric=metric,
        bsid_addr=bsid_addr,
        fwd_engine=srv6_manager_pb2.FwdEngine.Value(fwd_engine)
    )
    handle_srv6_entities(
        operation=operation,
        srv6_entities=[sr_path],
        grpc_channels=[channel]
    )
    return commons_pb2.STATUS_SUCCESS


def handle_srv6_policy(operation, channel, bsid_addr, segments=None,
                       table=-1, metric=-1, fwd_engine='Linux'):
    '''
    Handle a SRv6 Policy.
    This function has been deprecated. Use handle_srv6_entities instead.
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
                srv6_segment.segment = segment
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
                srv6_segment.segment = segment
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
    Handle a SRv6 behavior.
    This function has been deprecated. Use handle_srv6_entities instead.
    '''
    # pylint: disable=too-many-arguments, too-many-locals
    #
    if action == 'End':
        action = srv6_manager_pb2.SRv6Action.Value('END')
        behavior = srv6_behavior.SRv6EndBehavior()
    elif action == 'End.X':
        action = srv6_manager_pb2.SRv6Action.Value('END_X')
        behavior = srv6_behavior.SRv6EndXBehavior()
        behavior.nexthop = nexthop
    elif action == 'End.T':
        action = srv6_manager_pb2.SRv6Action.Value('END_T')
        behavior = srv6_behavior.SRv6EndTBehavior()
        behavior.lookup_table = lookup_table
    elif action == 'End.DX4':
        action = srv6_manager_pb2.SRv6Action.Value('END_DX4')
        behavior = srv6_behavior.SRv6EndDX4Behavior()
        behavior.nexthop = nexthop
    elif action == 'End.DX6':
        action = srv6_manager_pb2.SRv6Action.Value('END_DX6')
        behavior = srv6_behavior.SRv6EndDX6Behavior()
        behavior.nexthop = nexthop
    elif action == 'End.DX2':
        action = srv6_manager_pb2.SRv6Action.Value('END_DX2')
        behavior = srv6_behavior.SRv6EndDX2Behavior()
        behavior.interface = interface
    elif action == 'End.DT4':
        action = srv6_manager_pb2.SRv6Action.Value('END_DT4')
        behavior = srv6_behavior.SRv6EndDT4Behavior()
        behavior.lookup_table = lookup_table
    elif action == 'End.DT6':
        action = srv6_manager_pb2.SRv6Action.Value('END_DT6')
        behavior = srv6_behavior.SRv6EndDT6Behavior()
        behavior.lookup_table = lookup_table
    elif action == 'End.B6':
        action = srv6_manager_pb2.SRv6Action.Value('END_B6')
        behavior = srv6_behavior.SRv6EndB6Behavior()
        behavior.segments = segments
    elif action == 'End.B6.Encaps':
        action = srv6_manager_pb2.SRv6Action.Value('END_B6_ENCAPS')
        behavior = srv6_behavior.SRv6EndB6EncapsBehavior()
        behavior.segments = segments
    else:
        logger.error('Unrecognizer action: %s', action)
        raise utils.InvalidArgumentError
    # Fill the remaining fields
    behavior.segment = segment
    behavior.action = action
    behavior.device: device
    behavior.table: table
    behavior.metric: metric
    behavior.fwd_engine = fwd_engine
    # Handle the entities
    handle_srv6_entities(
        operation=operation,
        srv6_entities=[behavior],
        grpc_channels=[channel]
    )
    # Return the response
    return commons_pb2.STATUS_SUCCESS


class SRv6Exception(Exception):
    '''
    Generic SRv6 Exception.
    '''


def create_uni_srv6_tunnel(ingress_channel, egress_channel,
                           destination, segments, localseg=None,
                           bsid_addr='', fwd_engine='Linux'):
    '''
    Create a unidirectional SRv6 tunnel from <ingress> to <egress>.
    This function has been deprecated. Use handle_srv6_entities instead.

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
    This function has been deprecated. Use handle_srv6_entities instead.

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
    This function has been deprecated. Use handle_srv6_entities instead.

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
    This function has been deprecated. Use handle_srv6_entities instead.

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


def register_handlers():
    '''
    This function will register the handlers for the different SRv6 entities
    '''
    srv6_path.register_handlers(srv6_handlers)
    srv6_behavior.register_handlers(srv6_handlers)
    srv6_tunnel.register_handlers(srv6_handlers)


# Register the handlers when this module is imported/loaded
register_handlers()
