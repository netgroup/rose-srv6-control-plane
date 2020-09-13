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
# Utilities to manipulate SRv6 paths
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
This module provides a collection of utilities useful to manipulate SRv6
paths.
'''

# General imports
from dataclasses import dataclass
from enum import Enum
from ipaddress import ip_address
import logging
import os
from six import text_type

# Proto dependencies
import srv6_manager_pb2
# Controller dependencies
from controller import utils
from controller.db_utils.arangodb import arangodb_driver


# Global variables definition
#
#
# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)


class EncapMode(Enum):
    INLINE = 1
    ENCAP = 2
    L2ENCAP = 3


class FwdEngine(Enum):
    LINUX = srv6_manager_pb2.FwdEngine.Value('Linux')
    VPP = srv6_manager_pb2.FwdEngine.Value('VPP')


@dataclass
class SRv6Path:
    '''
    This class is used to encode a SRv6 path.

    :param key: Key associated to the SRv6 path, used to identify uniquely the
                path. This corresponds to the key associated to the path in
                the database.
    :type key: int, optional
    :param node_address: The IP address of the node where this path needs to
                         be enforced.
    :type node_address: str, optional
    :param destination: The destination prefix of the SRv6 path. This can be
                        an IP address or a subnet.
    :type destination: str, optional
    :param segments: The SID list associated to the SRv6 path.
    :type segments: list, optional
    :param device: Device of the SRv6 route. If not provided, the device
                   is selected automatically by the node.
    :type device: str, optional
    :param encapmode: The encap mode to use for the path, i.e. "inline" or
                      "encap" (default: encap).
    :type encapmode: str, optional
    :param table: Routing table containing the SRv6 route. If not provided,
                  the decision is left to the forwarding engine.
    :type table: int, optional
    :param metric: Metric for the SRv6 route. If not provided, the decision is
                   left to the forwarding engine.
    :type metric: int, optional
    :param bsid_addr: The Binding SID to be used for the route (only required
                      for VPP).
    :type bsid_addr: str, optional
    :param fwd_engine: Forwarding engine for the SRv6 route (default: Linux).
    :type fwd_engine: str, optional
    '''
    key: int = None
    grpc_address: str = None
    destination: str = None
    segments: list = None
    device: str = None
    encapmode: EncapMode = None
    table: int = None
    metric: int = None
    bsid_addr: str = None
    fwd_engine: FwdEngine = None


def encode_srv6_paths(srv6_entities, requests):
    '''
    Encode a set of SRv6 paths in a gRPC-compatible representation and add
    this representation to the SRv6 Manager request.

    :param srv6_entities: A set of SRv6 entities
                          (class `controller.srv6_utils.SRv6Entity`).
    :type srv6_entities: set.
    :param requests: Mapping IP address to SRv6ManagerRequest.
    :type requests: dict
    :raises controller.utils.InvalidArgumentError: You provided an invalid
                                                   argument.
    '''
    # Iterate on the SRv6 entities
    for srv6_entity in srv6_entities:
        # Select the entities of type "SRv6Path"
        if not isinstance(srv6_entity, SRv6Path):
            # Skip entities that are not SRv6 paths
            continue
        print('processing****************')
        if str(ip_address(srv6_entity.grpc_address)) not in requests:
            # Create request message
            requests[str(ip_address(srv6_entity.grpc_address))] = \
                srv6_manager_pb2.SRv6ManagerRequest()
        # Extract the SRv6 path request from the general request
        path_request = requests[                  # pylint: disable=no-member
            str(ip_address(srv6_entity.grpc_address))].srv6_path_request
        # Create a new path
        path = path_request.paths.add()
        # Set destination
        if srv6_entity.destination is None:
            logger.error('Invalid argument: destination cannot be None')
            raise utils.InvalidArgumentError
        path.destination = text_type(srv6_entity.destination)
        # Set device (required only for the Linux forwarding engine, not
        # for VPP)
        # If the device is not specified (i.e. empty string),
        # the decision is left to the forwarding engine
        path.device = srv6_entity.device \
            if srv6_entity.device is not None else ''
        # Set table ID
        # If the table ID is not specified (i.e. table=-1),
        # the decision is left to the forwarding engine
        path.table = srv6_entity.table \
            if srv6_entity.table is not None else -1
        # Set metric (i.e. preference value of the route)
        # If the metric is not specified (i.e. metric=-1),
        # the decision is left to the forwarding engine
        path.metric = srv6_entity.metric \
            if srv6_entity.metric is not None else -1
        # Set the BSID address (required only for VPP; if the Linux
        # forwarding engine is used, this field is leaved blank)
        path.bsid_addr = srv6_entity.bsid_addr \
            if srv6_entity.bsid_addr is not None else ''
        # Forwarding engine (Linux or VPP)
        # By default, we use Linux if the forwarding engine field is not
        # specified
        path_request.fwd_engine = srv6_entity.fwd_engine \
            if srv6_entity.fwd_engine is not None else FwdEngine.LINUX
        # Set encapmode
        # By default, we use "encap" if the encapmode field is not
        # specified
        path.encapmode = srv6_entity.encapmode \
            if srv6_entity.encapmode is not None else EncapMode.ENCAP
        # At least one segment is required for add operation
        if srv6_entity.segments is None or len(srv6_entity.segments) == 0:
            logger.error('*** Missing segments for seg6 route')
            raise utils.InvalidArgumentError
        # Iterate on the segments and build the SID list
        for segment in srv6_entity.segments:
            # Append the segment to the SID list
            srv6_segment = path.sr_path.add()
            srv6_segment.segment = text_type(segment)
        # Remove the entity from the entities set
        srv6_entities.remove(srv6_entity)


def decode_srv6_paths(srv6_entities, response):
    '''
    Decode a set of SRv6 paths represented as a gRPC-compatible
    representation.

    :param srv6_entities: The set to which the SRv6 paths must be added to.
    :type srv6_entities: set.
    :param response: The SRv6 Manager response from which the entities must be
                     extracted.
    :type response: class `srv6_manager_pb2.SRv6ManagerReply`
    :raises controller.utils.InvalidArgumentError: You provided an invalid
                                                   argument.
    '''
    # Iterate on the SRv6 paths containined in the response message
    for sr_path in response.paths:
        # Create a new path
        path = SRv6Path(
            key=None,
            grpc_address=None,
            destination=sr_path.destination,
            segments=sr_path.segments,
            device=sr_path.device,
            encapmode=sr_path.encapmode,
            table=sr_path.table,
            metric=sr_path.metric,
            bsid_addr=sr_path.bsid_addr,
            fwd_engine=sr_path.fwd_engine
        )
        # Add the SRv6 path to the srv6_entities set
        srv6_entities.add(path)


def augment_srv6_paths(srv6_entities, first_match=False):
    '''
    Take a set of SRv6 entities, iterate on the SRv6 paths, search them in the
    database and fill the missing fields with the information found in the
    database.

    :param srv6_entities: A set of SRv6 entities
                          (class `controller.srv6_utils.SRv6Entity`).
    :type srv6_entities: set.
    :param first_match: If True, only the first match is returned
                        (default: False).
    :type first_match: bool, optional
    '''
    # Connect to ArangoDB
    # FIXME crash if arangodb_driver not imported
    # TODO keep arango connection open
    client = arangodb_driver.connect_arango(
        url=os.getenv('ARANGO_URL'))
    # Connect to the "srv6_usid" db
    database = arangodb_driver.connect_srv6_usid_db(
        client=client,
        username=os.getenv('ARANGO_USER'),
        password=os.getenv('ARANGO_PASSWORD')
    )
    # Iterate on the SRv6 entities
    for srv6_entity in srv6_entities:
        # Select entities of type "SRv6Path"
        if not isinstance(srv6_entity, SRv6Path):
            # Skip entities that are not SRv6 Paths
            continue
        # Get the SRv6 paths from the database
        srv6_paths = arangodb_driver.find_srv6_path(
            database=database,
            key=srv6_entity.key,
            grpc_address=srv6_entity.grpc_address,
            destination=srv6_entity.grpc_address,
            segments=srv6_entity.grpc_address,
            device=srv6_entity.grpc_address,
            encapmode=srv6_entity.grpc_address,
            table=srv6_entity.grpc_address,
            metric=srv6_entity.grpc_address,
            bsid_addr=srv6_entity.grpc_address,
            fwd_engine=srv6_entity.grpc_address
        )
        srv6_paths = list(srv6_paths)
        # If no results, the entity does not exist on the database
        if len(srv6_paths) == 0:
            raise utils.EntityNotFoundError
        # Remove the entity from the entities set
        srv6_entities.remove(srv6_entity)
        # Add the new entities retrieved from the database
        for srv6_path in srv6_paths:
            # Build the entity
            srv6_path = SRv6Path(
                key=srv6_path.key,
                grpc_address=srv6_path.grpc_address,
                destination=srv6_path.grpc_address,
                segments=srv6_path.grpc_address,
                device=srv6_path.grpc_address,
                encapmode=srv6_path.grpc_address,
                table=srv6_path.grpc_address,
                metric=srv6_path.grpc_address,
                bsid_addr=srv6_path.grpc_address,
                fwd_engine=srv6_path.grpc_address
            )
            # Add to the set
            srv6_entities.add(srv6_path)
            if first_match:
                # If first_match is set, we return after the first result
                break


def do_srv6_paths_exist(srv6_entities):
    '''
    Check if all the SRv6 paths in the provided entities set exist in the
    database.

    :param srv6_entities: A set of SRv6 entities
                          (class `controller.srv6_utils.SRv6Entity`).
    :type srv6_entities: set.
    :return: True if all the paths exist, False otherwise.
    :rtype: bool
    '''
    try:
        # Try to augment the SRv6 entities
        augment_srv6_paths(srv6_entities, first_match=True)
    except utils.EntityNotFoundError:
        # An entity has not been found, so we return False
        return False
    # If no exception is raised, all the paths exist in the database
    return True


def save_to_db(srv6_entities):
    '''
    Write the SRv6 paths to the database.

    :param srv6_entities: A set of SRv6 entities
                          (class `controller.srv6_utils.SRv6Entity`).
    :type srv6_entities: set.
    '''
    # Connect to ArangoDB
    # FIXME crash if arangodb_driver not imported
    # TODO keep arango connection open
    client = arangodb_driver.connect_arango(
        url=os.getenv('ARANGO_URL'))
    # Connect to the "srv6_usid" db
    database = arangodb_driver.connect_srv6_usid_db(
        client=client,
        username=os.getenv('ARANGO_USER'),
        password=os.getenv('ARANGO_PASSWORD')
    )
    # Iterate on the SRv6 entities
    for srv6_entity in srv6_entities:
        # Select entities of type "SRv6Path"
        if not isinstance(srv6_entity, SRv6Path):
            # Skip entities that are not SRv6 Paths
            continue
        # Save the SRv6 path to the database
        arangodb_driver.insert_srv6_path(
            database=database,
            grpc_address=srv6_entity.grpc_address,
            destination=srv6_entity.destination,
            segments=srv6_entity.segments,
            device=srv6_entity.device,
            encapmode=srv6_entity.encapmode,
            table=srv6_entity.table,
            metric=srv6_entity.metric,
            bsid_addr=srv6_entity.bsid_addr,
            fwd_engine=srv6_entity.fwd_engine
        )


def remove_from_db(srv6_entities):
    '''
    Remove the SRv6 paths from the database.

    :param srv6_entities: A set of SRv6 entities
                          (class `controller.srv6_utils.SRv6Entity`).
    :type srv6_entities: set.
    '''
    # Connect to ArangoDB
    # FIXME crash if arangodb_driver not imported
    # TODO keep arango connection open
    client = arangodb_driver.connect_arango(
        url=os.getenv('ARANGO_URL'))
    # Connect to the "srv6_usid" db
    database = arangodb_driver.connect_srv6_usid_db(
        client=client,
        username=os.getenv('ARANGO_USER'),
        password=os.getenv('ARANGO_PASSWORD')
    )
    # Iterate on the SRv6 entities
    for srv6_entity in srv6_entities:
        # Select entities of type "SRv6Path"
        if not isinstance(srv6_entity, SRv6Path):
            # Skip entities that are not SRv6 Paths
            continue
        # Remove the SRv6 path from the database
        arangodb_driver.delete_srv6_path(
            database=database,
            key=srv6_entity.key,
            grpc_address=srv6_entity.grpc_address,
            destination=srv6_entity.destination,
            segments=srv6_entity.segments,
            device=srv6_entity.device,
            encapmode=srv6_entity.encapmode,
            table=srv6_entity.table,
            metric=srv6_entity.metric,
            bsid_addr=srv6_entity.bsid_addr,
            fwd_engine=srv6_entity.fwd_engine
        )


def register_handlers(handlers):
    handlers.append({
        'name': 'srv6_path',
        'augment_entities': augment_srv6_paths,
        'do_entities_exist': do_srv6_paths_exist,
        'encode_entities': encode_srv6_paths,
        'decode_entities': decode_srv6_paths,
        'save_entities_to_db': save_to_db,
        'remove_entities_from_db': remove_from_db
    })
