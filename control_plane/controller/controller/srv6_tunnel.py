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
# Utilities to manipulate SRv6 tunnels
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
This module provides a collection of utilities useful to manipulate SRv6
tunnels.
'''

# General imports
from dataclasses import dataclass
from enum import Enum
import logging
import os
from six import text_type
import socket

# Proto dependencies
import srv6_manager_pb2
# Controller dependencies
from controller import utils
from controller.db_utils.arangodb import arangodb_driver
from controller.srv6_path import SRv6Path
from controller.srv6_path import FwdEngine
from controller.srv6_path import EncapMode
from controller.srv6_path import encode_srv6_paths
from controller.srv6_behavior import SRv6EndDT6Behavior
from controller.srv6_behavior import SRv6EndDT4Behavior
from controller.srv6_behavior import SRv6Action
from controller.srv6_behavior import encode_srv6_behaviors


# Global variables definition
#
#
# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)


@dataclass
class SRv6Tunnel:
    key: int = None


@dataclass
class UnidirectionalSRv6Tunnel(SRv6Tunnel):
    '''
    This class is used to encode a unidirectional SRv6 tunnel between an
    <ingress> node and an <egress> node.

    :param ingress_address: The IP address of the ingress node.
    :type ingress_address: str
    :param egress_address: The IP address of the egress node.
    :type egress_address: str
    :param destination: The destination prefix of the SRv6 path. This can be a
                        IP address or a subnet.
    :type destination: str
    :param segments: The SID list to be applied to the packets going to
                     the destination.
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
    '''
    ingress_address: str = None
    egress_address: str = None
    destination: str = None
    segments: list = None
    localseg: str = None
    bsid_addr: str = None
    fwd_engine: FwdEngine = None


@dataclass
class BidirectionalSRv6Tunnel(SRv6Tunnel):
    '''
    Create a bidirectional SRv6 tunnel between <node_l> and <node_r>.

    :param node_l_address: The IP address of the left endpoint (node_l) of the
                           SRv6 tunnel.
    :type node_l_address: str
    :param node_r_address: The IP address of the right endpoint (node_r) of
                           the SRv6 tunnel.
    :type node_r_address: str
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
    '''
    node_l_address: str = None
    node_r_address: str = None
    sidlist_lr: list = None
    sidlist_rl: list = None
    dest_lr: str = None
    dest_rl: str = None,
    localseg_lr: str = None
    localseg_rl: str = None
    bsid_addr: str = None
    fwd_engine: FwdEngine = None


def encode_uni_srv6_tunnels(srv6_entities, requests):
    '''
    Encode a set of SRv6 tunnels in a gRPC-compatible representation and add
    this representation to the SRv6 Manager request.

    :param srv6_entities: A set of SRv6 entities
                          (class `controller.srv6_utils.SRv6Entity`).
    :type srv6_entities: set.
    :param srv6_manager_request: The SRv6 Manager request to which the
                                 entities must be added to.
    :type srv6_manager_request: class `srv6_manager_pb2.SRv6ManagerRequest`
    :raises controller.utils.InvalidArgumentError: You provided an invalid
                                                   argument.
    '''
    # Iterate on the SRv6 entities
    for srv6_entity in srv6_entities:
        # Select the entities of type "UnidirectionalSRv6Tunnel"
        if not isinstance(srv6_entity, UnidirectionalSRv6Tunnel):
            # Skip entities that are not unidirectional SRv6 tunnels
            continue
        # To realize a unidirectional tunnel we need a SRv6 path and
        # (optionally) a SRv6 End.DT4/End.DT6 behavior
        srv6_path = SRv6Path(
            key=srv6_entity.key,
            grpc_address=srv6_entity.ingress_address,
            destination=srv6_entity.destination,
            segments=srv6_entity.segments,
            encapmode=EncapMode.ENCAP,
            bsid_addr=srv6_entity.bsid_addr,
            fwd_engine=srv6_entity.fwd_engine
        )
        if utils.get_address_family(
                srv6_entity.destination) == socket.AF_INET6:
            srv6_behavior = SRv6EndDT6Behavior(
                segment=srv6_entity.localseg,
                action=SRv6Action.action,
                fwd_engine=srv6_entity.fwd_engine
            )
        elif utils.get_address_family(
                srv6_entity.destination) == socket.AF_INET:
            SRv6EndDT4Behavior(
                segment=srv6_entity.localseg,
                action=SRv6Action.action,
                fwd_engine=srv6_entity.fwd_engine
            )
        else:
            logger.error('Destination is not a valid IP address')
            raise utils.InvalidArgumentError
        # Encode the SRv6 path
        encode_srv6_paths([srv6_path], requests)
        # Encode the SRv6 behavior
        encode_srv6_behaviors([srv6_behavior], requests)
        # Remove the entity from the entities set
        srv6_entities.remove(srv6_entity)


def decode_uni_srv6_tunnels(srv6_entities, response):
    '''
    Decode a set of SRv6 tunnels represented as a gRPC-compatible
    representation.

    :param srv6_entities: The set to which the SRv6 tunnels must be added to.
    :type srv6_entities: set.
    :param response: The SRv6 Manager response from which the entities must be
                     extracted.
    :type response: class `srv6_manager_pb2.SRv6ManagerReply`
    :raises controller.utils.InvalidArgumentError: You provided an invalid
                                                   argument.
    '''
    raise NotImplementedError


def augment_uni_srv6_tunnels(srv6_entities, first_match=False):
    '''
    Take a set of SRv6 entities, iterate on the SRv6 tunnels, search them in
    the database and fill the missing fields with the information found in the
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
        # Select entities of type "UnidirectionalSRv6Tunnel"
        if not isinstance(srv6_entity, UnidirectionalSRv6Tunnel):
            # Skip entities that are not SRv6 unidirectional tunnels
            continue
        # Get the SRv6 tunnels from the database
        srv6_tunnels = arangodb_driver.find_srv6_tunnel(
            database=database,
            key=srv6_entity.key,
            l_grpc_address=srv6_entity.l_grpc_address,
            r_grpc_address=srv6_entity.r_grpc_address,
            sidlist_lr=srv6_entity.sidlist_lr,
            sidlist_rl=srv6_entity.sidlist_rl,
            dest_lr=srv6_entity.dest_lr,
            dest_rl=srv6_entity.dest_rl,
            localseg_lr=srv6_entity.localseg_lr,
            localseg_rl=srv6_entity.localseg_rl,
            bsid_addr=srv6_entity.bsid_addr,
            fwd_engine=srv6_entity.fwd_engine,
            is_unidirectional=True
        )
        srv6_tunnels = list(srv6_tunnels)
        # If no results, the entity does not exist on the database
        if len(srv6_tunnels) == 0:
            raise utils.EntityNotFoundError
        # Remove the entity from the entities set
        srv6_entities.remove(srv6_entity)
        # Add the new entities retrieved from the database
        for srv6_tunnel in srv6_tunnels:
            # Build the entity
            srv6_tunnel = UnidirectionalSRv6Tunnel(
                key=srv6_tunnel.key,
                ingress_address=srv6_tunnel.ingress_address,
                egress_address=srv6_tunnel.egress_address,
                destination=srv6_tunnel.destination,
                segments=srv6_tunnel.segments,
                localseg=srv6_tunnel.localseg,
                bsid_addr=srv6_tunnel.bsid_addr,
                fwd_engine=srv6_tunnel.fwd_engine
            )
            # Add to the set
            srv6_entities.add(srv6_tunnel)
            if first_match:
                # If first_match is set, we return after the first result
                break


def do_uni_srv6_tunnels_exist(srv6_entities):
    '''
    Check if all the SRv6 tunnels in the provided entities set exist in the
    database.

    :param srv6_entities: A set of SRv6 entities
                          (class `controller.srv6_utils.SRv6Entity`).
    :type srv6_entities: set.
    :return: True if all the tunnels exist, False otherwise.
    :rtype: bool
    '''
    try:
        # Try to augment the SRv6 entities
        augment_uni_srv6_tunnels(srv6_entities, first_match=True)
    except utils.EntityNotFoundError:
        # An entity has not been found, so we return False
        return False
    # If no exception is raised, all the tunnels exist in the database
    return True


def save_unitunnel_to_db(srv6_entities):
    '''
    Write the SRv6 tunnels to the database.

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
        # Select entities of type "UnidirectionalSRv6Tunnel"
        if not isinstance(srv6_entity, UnidirectionalSRv6Tunnel):
            # Skip entities that are not unidirectional SRv6 tunnels
            continue
        # Save the SRv6 tunnel to the database
        arangodb_driver.insert_srv6_tunnel(
            database=database,
            l_grpc_address=srv6_entity.ingress_address,
            r_grpc_address=None,
            sidlist_lr=srv6_entity.segments,
            sidlist_rl=None,
            dest_lr=srv6_entity.destination,
            dest_rl=None,
            localseg_lr=srv6_entity.localseg,
            localseg_rl=None,
            bsid_addr=srv6_entity.bsid_addr,
            fwd_engine=srv6_entity.fwd_engine,
            is_unidirectional=True
        )


def remove_unitunnel_from_db(srv6_entities):
    '''
    Remove the SRv6 tunnels from the database.

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
        # Select entities of type "UnidirectionalSRv6Tunnel"
        if not isinstance(srv6_entity, UnidirectionalSRv6Tunnel):
            # Skip entities that are not unidirectional SRv6 tunnels
            continue
        # Remove the SRv6 tunnel from the database
        arangodb_driver.delete_srv6_tunnel(
            database=database,
            key=srv6_entity.key,
            l_grpc_address=srv6_entity.ingress_address,
            r_grpc_address=None,
            sidlist_lr=srv6_entity.segments,
            sidlist_rl=None,
            dest_lr=srv6_entity.destination,
            dest_rl=None,
            localseg_lr=srv6_entity.localseg,
            localseg_rl=None,
            bsid_addr=srv6_entity.bsid_addr,
            fwd_engine=srv6_entity.fwd_engine,
            is_unidirectional=True
        )


def encode_bidi_srv6_tunnels(srv6_entities, srv6_manager_request):
    '''
    Encode a set of SRv6 tunnels in a gRPC-compatible representation and add
    this representation to the SRv6 Manager request.

    :param srv6_entities: A set of SRv6 entities
                          (class `controller.srv6_utils.SRv6Entity`).
    :type srv6_entities: set.
    :param srv6_manager_request: The SRv6 Manager request to which the
                                 entities must be added to.
    :type srv6_manager_request: class `srv6_manager_pb2.SRv6ManagerRequest`
    :raises controller.utils.InvalidArgumentError: You provided an invalid
                                                   argument.
    '''
    # Iterate on the SRv6 entities
    for srv6_entity in srv6_entities:
        # Select the entities of type "BidirectionalSRv6Tunnel"
        if not isinstance(srv6_entity, BidirectionalSRv6Tunnel):
            # Skip entities that are not unidirectional SRv6 tunnels
            continue
        # To realize a unidirectional tunnel we need a SRv6 path and
        # (optionally) a SRv6 End.DT4/End.DT6 behavior for each direction
        srv6_path = SRv6Path(
            key=srv6_entity.key,
            grpc_address=srv6_entity.node_l_address,
            destination=srv6_entity.dest_lr,
            segments=srv6_entity.sidlist_lr,
            encapmode=EncapMode.ENCAP,
            bsid_addr=srv6_entity.bsid_addr,
            fwd_engine=srv6_entity.fwd_engine
        )
        if utils.get_address_family(
                srv6_entity.destination) == socket.AF_INET6:
            srv6_behavior = SRv6EndDT6Behavior(
                segment=srv6_entity.localseg,
                action=SRv6Action.action,
                fwd_engine=srv6_entity.fwd_engine
            )
        elif utils.get_address_family(
                srv6_entity.destination) == socket.AF_INET:
            SRv6EndDT4Behavior(
                segment=srv6_entity.localseg,
                action=SRv6Action.action,
                fwd_engine=srv6_entity.fwd_engine
            )
        else:
            logger.error('Destination is not a valid IP address')
            raise utils.InvalidArgumentError
        srv6_path = SRv6Path(
            key=srv6_entity.key,
            grpc_address=srv6_entity.node_r_address,
            destination=srv6_entity.dest_rl,
            segments=srv6_entity.sidlist_rl,
            encapmode=EncapMode.ENCAP,
            bsid_addr=srv6_entity.bsid_addr,
            fwd_engine=srv6_entity.fwd_engine
        )
        if utils.get_address_family(
                srv6_entity.destination) == socket.AF_INET6:
            srv6_behavior = SRv6EndDT6Behavior(
                segment=srv6_entity.localseg,
                action=SRv6Action.action,
                fwd_engine=srv6_entity.fwd_engine
            )
        elif utils.get_address_family(
                srv6_entity.destination) == socket.AF_INET:
            SRv6EndDT4Behavior(
                segment=srv6_entity.localseg,
                action=SRv6Action.action,
                fwd_engine=srv6_entity.fwd_engine
            )
        else:
            logger.error('Destination is not a valid IP address')
            raise utils.InvalidArgumentError
        # Encode the SRv6 path
        encode_srv6_paths([srv6_path], srv6_manager_request)
        # Encode the SRv6 behavior
        encode_srv6_behaviors([srv6_behavior], srv6_manager_request)
        # Remove the entity from the entities set
        srv6_entities.remove(srv6_entity)


def decode_bidi_srv6_tunnels(srv6_entities, response):
    '''
    Decode a set of SRv6 tunnels represented as a gRPC-compatible
    representation.

    :param srv6_entities: The set to which the SRv6 tunnels must be added to.
    :type srv6_entities: set.
    :param response: The SRv6 Manager response from which the entities must be
                     extracted.
    :type response: class `srv6_manager_pb2.SRv6ManagerReply`
    :raises controller.utils.InvalidArgumentError: You provided an invalid
                                                   argument.
    '''
    raise NotImplementedError


def augment_bidi_srv6_tunnels(srv6_entities, first_match=False):
    '''
    Take a set of SRv6 entities, iterate on the SRv6 tunnels, search them in
    the database and fill the missing fields with the information found in the
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
        # Select entities of type "BidirectionalSRv6Tunnel"
        if not isinstance(srv6_entity, BidirectionalSRv6Tunnel):
            # Skip entities that are not SRv6 bidirectional tunnels
            continue
        # Get the SRv6 tunnels from the database
        srv6_tunnels = arangodb_driver.find_srv6_tunnel(
            database=database,
            key=srv6_entity.key,
            l_grpc_address=srv6_entity.node_l_address,
            r_grpc_address=srv6_entity.node_r_address,
            sidlist_lr=srv6_entity.sidlist_lr,
            sidlist_rl=srv6_entity.sidlist_rl,
            dest_lr=srv6_entity.dest_lr,
            dest_rl=srv6_entity.dest_rl,
            localseg_lr=srv6_entity.localseg_lr,
            localseg_rl=srv6_entity.localseg_rl,
            bsid_addr=srv6_entity.bsid_addr,
            fwd_engine=srv6_entity.fwd_engine,
            is_unidirectional=False
        )
        srv6_tunnels = list(srv6_tunnels)
        # If no results, the entity does not exist on the database
        if len(srv6_tunnels) == 0:
            raise utils.EntityNotFoundError
        # Remove the entity from the entities set
        srv6_entities.remove(srv6_entity)
        # Add the new entities retrieved from the database
        for srv6_tunnel in srv6_tunnels:
            # Build the entity
            srv6_tunnel = BidirectionalSRv6Tunnel(
                key=srv6_tunnel.key,
                node_l_address=srv6_tunnel.l_grpc_address,
                node_r_address=srv6_tunnel.r_grpc_address,
                sidlist_lr=srv6_tunnel.sidlist_lr,
                sidlist_rl=srv6_tunnel.sidlist_rl,
                dest_lr=srv6_tunnel.dest_lr,
                dest_rl=srv6_tunnel.dest_rl,
                localseg_lr=srv6_tunnel.localseg_lr,
                localseg_rl=srv6_tunnel.localseg_rl,
                bsid_addr=srv6_tunnel.bsid_addr,
                fwd_engine=srv6_tunnel.fwd_engine,
                is_unidirectional=False
            )
            # Add to the set
            srv6_entities.add(srv6_tunnel)
            if first_match:
                # If first_match is set, we return after the first result
                break


def do_bidi_srv6_tunnels_exist(srv6_entities):
    '''
    Check if all the SRv6 tunnels in the provided entities set exist in the
    database.

    :param srv6_entities: A set of SRv6 entities
                          (class `controller.srv6_utils.SRv6Entity`).
    :type srv6_entities: set.
    :return: True if all the tunnels exist, False otherwise.
    :rtype: bool
    '''
    try:
        # Try to augment the SRv6 entities
        augment_bidi_srv6_tunnels(srv6_entities, first_match=True)
    except utils.EntityNotFoundError:
        # An entity has not been found, so we return False
        return False
    # If no exception is raised, all the tunnels exist in the database
    return True


def save_biditunnel_to_db(srv6_entities):
    '''
    Write the SRv6 tunnels to the database.

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
        # Select entities of type "BidirectionalSRv6Tunnel"
        if not isinstance(srv6_entity, BidirectionalSRv6Tunnel):
            # Skip entities that are not bidirectional SRv6 tunnels
            continue
        # Save the SRv6 tunnel to the database
        arangodb_driver.insert_srv6_tunnel(
            database=database,
            l_grpc_address=srv6_entity.node_l_address,
            r_grpc_address=srv6_entity.node_r_address,
            sidlist_lr=srv6_entity.sidlist_lr,
            sidlist_rl=srv6_entity.sidlist_rl,
            dest_lr=srv6_entity.dest_lr,
            dest_rl=srv6_entity.dest_rl,
            localseg_lr=srv6_entity.localseg_lr,
            localseg_rl=srv6_entity.localseg_rl,
            bsid_addr=srv6_entity.bsid_addr,
            fwd_engine=srv6_entity.fwd_engine,
            is_unidirectional=False
        )


def remove_biditunnel_from_db(srv6_entities):
    '''
    Remove the SRv6 tunnels from the database.

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
        # Select entities of type "BidirectionalSRv6Tunnel"
        if not isinstance(srv6_entity, BidirectionalSRv6Tunnel):
            # Skip entities that are not bidirectional SRv6 tunnels
            continue
        # Remove the SRv6 tunnel from the database
        arangodb_driver.delete_srv6_tunnel(
            database=database,
            l_grpc_address=srv6_entity.node_l_address,
            r_grpc_address=srv6_entity.node_r_address,
            sidlist_lr=srv6_entity.sidlist_lr,
            sidlist_rl=srv6_entity.sidlist_rl,
            dest_lr=srv6_entity.dest_lr,
            dest_rl=srv6_entity.dest_rl,
            localseg_lr=srv6_entity.localseg_lr,
            localseg_rl=srv6_entity.localseg_rl,
            bsid_addr=srv6_entity.bsid_addr,
            fwd_engine=srv6_entity.fwd_engine,
            is_unidirectional=False
        )


def register_unitunnel_handlers(handlers):
    handlers.append({
        'name': 'uni_srv6_tunnel',
        'augment_entities': augment_uni_srv6_tunnels,
        'do_entities_exist': do_uni_srv6_tunnels_exist,
        'encode_entities': encode_uni_srv6_tunnels,
        'decode_entities': decode_uni_srv6_tunnels,
        'save_entities_to_db': save_unitunnel_to_db,
        'remove_entities_from_db': remove_unitunnel_from_db
    })


def register_biditunnel_handlers(handlers):
    handlers.append({
        'name': 'bidi_srv6_tunnel',
        'augment_entities': augment_bidi_srv6_tunnels,
        'do_entities_exist': do_bidi_srv6_tunnels_exist,
        'encode_entities': encode_bidi_srv6_tunnels,
        'decode_entities': decode_bidi_srv6_tunnels,
        'save_entities_to_db': save_biditunnel_to_db,
        'remove_entities_from_db': remove_biditunnel_from_db
    })


def register_handlers(handlers):
    register_unitunnel_handlers(handlers)
    register_biditunnel_handlers(handlers)
