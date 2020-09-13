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
# Utilities to manipulate SRv6 behaviors
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
This module provides a collection of utilities useful to manipulate SRv6
behaviors.
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


class FwdEngine(Enum):
    LINUX = srv6_manager_pb2.FwdEngine.Value('Linux')
    VPP = srv6_manager_pb2.FwdEngine.Value('VPP')


class SRv6Action(Enum):
    UNSPEC = srv6_manager_pb2.SRv6Action.Value('UNSPEC')
    END = srv6_manager_pb2.SRv6Action.Value('END')
    END_X = srv6_manager_pb2.SRv6Action.Value('END_X')
    END_T = srv6_manager_pb2.SRv6Action.Value('END_T')
    END_DX4 = srv6_manager_pb2.SRv6Action.Value('END_DX4')
    END_DX6 = srv6_manager_pb2.SRv6Action.Value('END_DX6')
    END_DX2 = srv6_manager_pb2.SRv6Action.Value('END_DX2')
    END_DT4 = srv6_manager_pb2.SRv6Action.Value('END_DT4')
    END_DT6 = srv6_manager_pb2.SRv6Action.Value('END_DT6')
    END_B6 = srv6_manager_pb2.SRv6Action.Value('END_B6')
    END_B6_ENCAPS = srv6_manager_pb2.SRv6Action.Value('END_B6_ENCAPS')


@dataclass
class SRv6Behavior:
    '''
    This class is used to encode a SRv6 behavior.
    '''
    segment: str = None
    action: SRv6Action = None
    device: str = None
    table: int = None
    metric: int = None
    fwd_engine: FwdEngine = None


@dataclass
class SRv6EndBehavior(SRv6Behavior):
    '''
    This class is used to encode a SRv6 End behavior.
    '''


@dataclass
class SRv6EndXBehavior(SRv6Behavior):
    '''
    This class is used to encode a SRv6 End.X behavior.
    '''
    nexthop: str = None


@dataclass
class SRv6EndTBehavior(SRv6Behavior):
    '''
    This class is used to encode a SRv6 End.T behavior.
    '''
    lookup_table: int = None


@dataclass
class SRv6EndDX4Behavior(SRv6Behavior):
    '''
    This class is used to encode a SRv6 End.DX4 behavior.
    '''
    nexthop: str = None


@dataclass
class SRv6EndDX6Behavior(SRv6Behavior):
    '''
    This class is used to encode a SRv6 End.DX6 behavior.
    '''
    nexthop: str = None


@dataclass
class SRv6EndDX2Behavior(SRv6Behavior):
    '''
    This class is used to encode a SRv6 End.DX2 behavior.
    '''
    interface: str = None


@dataclass
class SRv6EndDT4Behavior(SRv6Behavior):
    '''
    This class is used to encode a SRv6 End.DT4 behavior.
    '''
    lookup_table: int = None


@dataclass
class SRv6EndDT6Behavior(SRv6Behavior):
    '''
    This class is used to encode a SRv6 End.DT6 behavior.
    '''
    lookup_table: int = None


@dataclass
class SRv6EndB6Behavior(SRv6Behavior):
    '''
    This class is used to encode a SRv6 End.B6 behavior.
    '''
    segments: list = None


@dataclass
class SRv6EndB6EncapsBehavior(SRv6Behavior):
    '''
    This class is used to encode a SRv6 End.B6.Encaps behavior.
    '''
    segments: list = None


def encode_srv6_behaviors(srv6_entities, requests):
    '''
    Encode a set of SRv6 behaviors in a gRPC-compatible representation and add
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
        # Select the entities of type "SRv6Behavior"
        if not isinstance(srv6_entity, SRv6Behavior):
            # Skip entities that are not SRv6 behaviors
            continue
        if str(ip_address(srv6_entity.grpc_address)) not in requests:
            # Create request message
            requests[str(ip_address(srv6_entity.grpc_address))] = srv6_manager_pb2.SRv6ManagerRequest()
        # Extract the SRv6 behavior request from the general request
        behavior_request = requests[str(ip_address(srv6_entity.grpc_address))].srv6_behavior_request       # pylint: disable=no-member
        # Create a new SRv6 behavior
        behavior = behavior_request.behaviors.add()
        # Set local segment for the seg6local route
        behavior.segment = text_type(srv6_entity.segment)
        # Set the device
        # If the device is not specified (i.e. empty string),
        # the decision is left to the forwarding engine
        behavior.device = text_type(srv6_entity.device)
        # Set the table where the seg6local must be inserted
        # If the table ID is not specified (i.e. table=-1),
        # the decision is left to the forwarding engine
        behavior.table = int(srv6_entity.table)
        # Set device (required only for the Linux forwarding engine, not
        # for VPP)
        # If the device is not specified (i.e. empty string),
        # the decision is left to the forwarding engine
        behavior.device = text_type(srv6_entity.device)
        # Set metric (i.e. preference value of the route)
        # If the metric is not specified (i.e. metric=-1),
        # the decision is left to the forwarding engine
        behavior.metric = int(srv6_entity.metric)
        # Forwarding engine (Linux or VPP)
        # By default, we use Linux if the forwarding engine field is not
        # specified
        behavior_request.fwd_engine = srv6_entity.fwd_engine \
            if srv6_entity.fwd_engine is not None else FwdEngine.LINUX
        # Set the action for the seg6local route
        behavior_request.action = srv6_entity.action \
            if srv6_entity.action is not None else SRv6Action.UNSPEC
        # Set the fields action-dependent
        #
        # Parameters for End
        if isinstance(srv6_entity, SRv6EndBehavior):
            if srv6_entity.action != SRv6Action.END:
                raise utils.InvalidArgumentError
        # Parameters for End.X
        if isinstance(srv6_entity, SRv6EndXBehavior):
            if srv6_entity.action != SRv6Action.END_X:
                raise utils.InvalidArgumentError
            # Set the nexthop for the L3 cross-connect actions
            # (e.g. End.DX4, End.DX6)
            behavior.nexthop = text_type(srv6_entity.nexthop)
        # Parameters for End.T
        if isinstance(srv6_entity, SRv6EndTBehavior):
            if srv6_entity.action != SRv6Action.END_T:
                raise utils.InvalidArgumentError
            # Set the table for the "decap and table lookup" actions
            # (e.g. End.DT4, End.DT6)
            behavior.lookup_table = int(srv6_entity.lookup_table)
        # Parameters for End.DX4
        if isinstance(srv6_entity, SRv6EndDX4Behavior):
            if srv6_entity.action != SRv6Action.END_DX4:
                raise utils.InvalidArgumentError
            # Set the nexthop for the L3 cross-connect actions
            # (e.g. End.DX4, End.DX6)
            behavior.nexthop = text_type(srv6_entity.nexthop)
        # Parameters for End.DX6
        if isinstance(srv6_entity, SRv6EndDX6Behavior):
            if srv6_entity.action != SRv6Action.END_DX6:
                raise utils.InvalidArgumentError
            # Set the nexthop for the L3 cross-connect actions
            # (e.g. End.DX4, End.DX6)
            behavior.nexthop = text_type(srv6_entity.nexthop)
        # Parameters for End.DX2
        if isinstance(srv6_entity, SRv6EndDX2Behavior):
            if srv6_entity.action != SRv6Action.END_DX2:
                raise utils.InvalidArgumentError
            # Set the inteface for the L2 cross-connect actions
            # (e.g. End.DX2)
            behavior.interface = text_type(srv6_entity.interface)
        # Parameters for End.DT4
        if isinstance(srv6_entity, SRv6EndDT4Behavior):
            if srv6_entity.action != SRv6Action.END_DT4:
                raise utils.InvalidArgumentError
            # Set the table for the "decap and table lookup" actions
            # (e.g. End.DT4, End.DT6)
            behavior.lookup_table = int(srv6_entity.lookup_table)
        # Parameters for End.DT6
        if isinstance(srv6_entity, SRv6EndDT6Behavior):
            if srv6_entity.action != SRv6Action.END_DT6:
                raise utils.InvalidArgumentError
            # Set the table for the "decap and table lookup" actions
            # (e.g. End.DT4, End.DT6)
            behavior.lookup_table = int(srv6_entity.lookup_table)
        # Parameters for End.B6
        if isinstance(srv6_entity, SRv6EndB6Behavior):
            if srv6_entity.action != SRv6Action.END_B6:
                raise utils.InvalidArgumentError
            # Set the segments for the binding SID actions
            # (e.g. End.B6, End.B6.Encaps)
            for seg in srv6_entity.segments:
                # Create a new segment
                srv6_segment = behavior.segs.add()
                srv6_segment.segment = text_type(seg)
        # Parameters for End.B6.Encaps
        if isinstance(srv6_entity, SRv6EndB6EncapsBehavior):
            if srv6_entity.action != SRv6Action.END_B6_ENCAPS:
                raise utils.InvalidArgumentError
            # Set the segments for the binding SID actions
            # (e.g. End.B6, End.B6.Encaps)
            for seg in srv6_entity.segments:
                # Create a new segment
                srv6_segment = behavior.segs.add()
                srv6_segment.segment = text_type(seg)


def decode_srv6_behaviors(srv6_entities, response):
    '''
    Decode a set of SRv6 behaviors represented as a gRPC-compatible
    representation.

    :param srv6_entities: The set to which the SRv6 behaviors must be added
                          to.
    :type srv6_entities: set.
    :param response: The SRv6 Manager response from which the entities must be
                     extracted.
    :type response: class `srv6_manager_pb2.SRv6ManagerReply`
    :raises controller.utils.InvalidArgumentError: You provided an invalid
                                                   argument.
    '''
    # Iterate on the SRv6 behaviors containined in the response message
    for sr_behavior in response.paths:
        # Create a new behavior
        if sr_behavior.action == srv6_manager_pb2.SRv6Action.Value('END'):
            behavior = SRv6EndBehavior()
        elif sr_behavior.action == srv6_manager_pb2.SRv6Action.Value('END_X'):
            behavior = SRv6EndXBehavior()
            behavior.nexthop = sr_behavior.nexthop
        elif sr_behavior.action == srv6_manager_pb2.SRv6Action.Value('END_T'):
            behavior = SRv6EndTBehavior()
            behavior.lookup_table = sr_behavior.lookup_table
        elif sr_behavior.action == srv6_manager_pb2.SRv6Action.Value('END_DX4'):
            behavior = SRv6EndDX4Behavior()
            behavior.nexthop = sr_behavior.nexthop
        elif sr_behavior.action == srv6_manager_pb2.SRv6Action.Value('END_DX6'):
            behavior = SRv6EndDX6Behavior()
            behavior.nexthop = sr_behavior.nexthop
        elif sr_behavior.action == srv6_manager_pb2.SRv6Action.Value('END_DX2'):
            behavior = SRv6EndDX2Behavior()
            behavior.interface = sr_behavior.interface
        elif sr_behavior.action == srv6_manager_pb2.SRv6Action.Value('END_DT4'):
            behavior = SRv6EndDT4Behavior()
            behavior.lookup_table = sr_behavior.lookup_table
        elif sr_behavior.action == srv6_manager_pb2.SRv6Action.Value('END_DT6'):
            behavior = SRv6EndDT6Behavior()
            behavior.lookup_table = sr_behavior.lookup_table
        elif sr_behavior.action == srv6_manager_pb2.SRv6Action.Value('END_B6'):
            behavior = SRv6EndB6Behavior()
            behavior.segments = sr_behavior.segments
        elif sr_behavior.action == srv6_manager_pb2.SRv6Action.Value('END_B6_ENCAPS'):
            behavior = SRv6EndB6EncapsBehavior()
            behavior.segments = sr_behavior.segments
        else:
            logger.error('Unrecognizer action: %s', sr_behavior.action)
            raise utils.InvalidArgumentError
        # Fill the remaining fields
        behavior.segment = sr_behavior.segment
        behavior.action = sr_behavior.action
        behavior.device: sr_behavior.device
        behavior.table: sr_behavior.table
        behavior.metric: sr_behavior.metric
        behavior.fwd_engine = sr_behavior.fwd_engine
        # Add the SRv6 behavior to the srv6_entities set
        srv6_entities.add(behavior)


def augment_srv6_behaviors(srv6_entities, first_match=False):
    '''
    Take a set of SRv6 entities, iterate on the SRv6 behaviors, search them in
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
        # Select entities of type "SRv6Behavior"
        if not isinstance(srv6_entity, SRv6Behavior):
            # Skip entities that are not SRv6 behaviors
            continue
        # Get the SRv6 behaviors from the database
        srv6_behaviors = arangodb_driver.find_srv6_behavior(
            database=database,
            grpc_address=srv6_entity.grpc_address,
            segment=srv6_entity.segment,
            action=srv6_entity.action,
            device=srv6_entity.device,
            table=srv6_entity.table,
            nexthop=srv6_entity.nexthop,
            lookup_table=srv6_entity.lookup_table,
            interface=srv6_entity.interface,
            segments=srv6_entity.segments,
            metric=srv6_entity.metric,
            fwd_engine=srv6_entity.fwd_engine
        )
        srv6_behaviors = list(srv6_behaviors)
        # If no results, the entity does not exist on the database
        if len(srv6_behaviors) == 0:
            raise utils.EntityNotFoundError
        # Remove the entity from the entities set
        srv6_entities.remove(srv6_entity)
        # Add the new entities retrieved from the database
        for srv6_behavior in srv6_behaviors:
            # Parameters action specific
            nexthop = None
            lookup_table = None
            interface = None
            segments = None
            # Parameters for End
            if isinstance(srv6_behavior, SRv6EndBehavior):
                # End requires no parameter
                pass
            # Parameters for End.X
            if isinstance(srv6_behavior, SRv6EndXBehavior):
                # Set the nexthop for the L3 cross-connect actions
                # (e.g. End.DX4, End.DX6)
                nexthop = text_type(srv6_behavior.nexthop)
            # Parameters for End.T
            if isinstance(srv6_behavior, SRv6EndTBehavior):
                # Set the table for the "decap and table lookup" actions
                # (e.g. End.DT4, End.DT6)
                lookup_table = int(srv6_behavior.lookup_table)
            # Parameters for End.DX4
            if isinstance(srv6_behavior, SRv6EndDX4Behavior):
                # Set the nexthop for the L3 cross-connect actions
                # (e.g. End.DX4, End.DX6)
                nexthop = text_type(srv6_behavior.nexthop)
            # Parameters for End.DX6
            if isinstance(srv6_behavior, SRv6EndDX6Behavior):
                # Set the nexthop for the L3 cross-connect actions
                # (e.g. End.DX4, End.DX6)
                nexthop = text_type(srv6_behavior.nexthop)
            # Parameters for End.DX2
            if isinstance(srv6_behavior, SRv6EndDX2Behavior):
                # Set the inteface for the L2 cross-connect actions
                # (e.g. End.DX2)
                interface = text_type(srv6_behavior.interface)
            # Parameters for End.DT4
            if isinstance(srv6_behavior, SRv6EndDT4Behavior):
                # Set the table for the "decap and table lookup" actions
                # (e.g. End.DT4, End.DT6)
                lookup_table = int(srv6_behavior.lookup_table)
            # Parameters for End.DT6
            if isinstance(srv6_behavior, SRv6EndDT6Behavior):
                # Set the table for the "decap and table lookup" actions
                # (e.g. End.DT4, End.DT6)
                lookup_table = int(srv6_behavior.lookup_table)
            # Parameters for End.B6
            if isinstance(srv6_behavior, SRv6EndB6Behavior):
                # Set the segments for the binding SID actions
                # (e.g. End.B6, End.B6.Encaps)
                for seg in srv6_behavior.segments:
                    segments = text_type(seg)
            # Parameters for End.B6.Encaps
            if isinstance(srv6_behavior, SRv6EndB6EncapsBehavior):
                # Set the segments for the binding SID actions
                # (e.g. End.B6, End.B6.Encaps)
                for seg in srv6_behavior.segments:
                    segments = text_type(seg)
            # Build the entity
            srv6_behavior = SRv6Behavior(
                key=srv6_behavior.key,
                grpc_address=srv6_behavior.grpc_address,
                segment=srv6_behavior.segment,
                action=srv6_behavior.action,
                device=srv6_behavior.device,
                table=srv6_behavior.table,
                nexthop=nexthop,
                lookup_table=lookup_table,
                interface=interface,
                segments=segments,
                metric=srv6_behavior.metric,
                fwd_engine=srv6_behavior.fwd_engine
            )
            # Add to the set
            srv6_entities.add(srv6_behavior)
            if first_match:
                # If first_match is set, we return after the first result
                break


def do_srv6_behaviors_exist(srv6_entities):
    '''
    Check if all the SRv6 behaviors in the provided entities set exist in the
    database.

    :param srv6_entities: A set of SRv6 entities
                          (class `controller.srv6_utils.SRv6Entity`).
    :type srv6_entities: set.
    :return: True if all the behaviors exist, False otherwise.
    :rtype: bool
    '''
    try:
        # Try to augment the SRv6 behaviors
        augment_srv6_behaviors(srv6_entities, first_match=True)
    except utils.EntityNotFoundError:
        # An entity has not been found, so we return False
        return False
    # If no exception is raised, all the behaviors exist in the database
    return True


def save_to_db(srv6_entities):
    '''
    Write the SRv6 behaviors to the database.

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
        # Select entities of type "SRv6Behavior"
        if not isinstance(srv6_entity, SRv6Behavior):
            # Skip entities that are not SRv6 behaviors
            continue
        # Parameters action specific
        nexthop = None
        lookup_table = None
        interface = None
        segments = None
        # Parameters for End
        if isinstance(srv6_entity, SRv6EndBehavior):
            # End requires no parameter
            pass
        # Parameters for End.X
        if isinstance(srv6_entity, SRv6EndXBehavior):
            # Set the nexthop for the L3 cross-connect actions
            # (e.g. End.DX4, End.DX6)
            nexthop = text_type(srv6_entity.nexthop)
        # Parameters for End.T
        if isinstance(srv6_entity, SRv6EndTBehavior):
            # Set the table for the "decap and table lookup" actions
            # (e.g. End.DT4, End.DT6)
            lookup_table = int(srv6_entity.lookup_table)
        # Parameters for End.DX4
        if isinstance(srv6_entity, SRv6EndDX4Behavior):
            # Set the nexthop for the L3 cross-connect actions
            # (e.g. End.DX4, End.DX6)
            nexthop = text_type(srv6_entity.nexthop)
        # Parameters for End.DX6
        if isinstance(srv6_entity, SRv6EndDX6Behavior):
            # Set the nexthop for the L3 cross-connect actions
            # (e.g. End.DX4, End.DX6)
            nexthop = text_type(srv6_entity.nexthop)
        # Parameters for End.DX2
        if isinstance(srv6_entity, SRv6EndDX2Behavior):
            # Set the inteface for the L2 cross-connect actions
            # (e.g. End.DX2)
            interface = text_type(srv6_entity.interface)
        # Parameters for End.DT4
        if isinstance(srv6_entity, SRv6EndDT4Behavior):
            # Set the table for the "decap and table lookup" actions
            # (e.g. End.DT4, End.DT6)
            lookup_table = int(srv6_entity.lookup_table)
        # Parameters for End.DT6
        if isinstance(srv6_entity, SRv6EndDT6Behavior):
            # Set the table for the "decap and table lookup" actions
            # (e.g. End.DT4, End.DT6)
            lookup_table = int(srv6_entity.lookup_table)
        # Parameters for End.B6
        if isinstance(srv6_entity, SRv6EndB6Behavior):
            # Set the segments for the binding SID actions
            # (e.g. End.B6, End.B6.Encaps)
            for seg in srv6_entity.segments:
                segments = text_type(seg)
        # Parameters for End.B6.Encaps
        if isinstance(srv6_entity, SRv6EndB6EncapsBehavior):
            # Set the segments for the binding SID actions
            # (e.g. End.B6, End.B6.Encaps)
            for seg in srv6_entity.segments:
                segments = text_type(seg)
        # Save the SRv6 behavior to the database
        arangodb_driver.insert_srv6_behavior(
            database=database,
            grpc_address=srv6_entity.grpc_address,
            segment=srv6_entity.segment,
            action=srv6_entity.action,
            device=srv6_entity.device,
            table=srv6_entity.table,
            nexthop=nexthop,
            lookup_table=lookup_table,
            interface=interface,
            segments=segments,
            metric=srv6_entity.metric,
            fwd_engine=srv6_entity.fwd_engine
        )


def remove_from_db(srv6_entities):
    '''
    Remove the SRv6 behaviors from the database.

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
        # Select entities of type "SRv6Behavior"
        if not isinstance(srv6_entity, SRv6Behavior):
            # Skip entities that are not SRv6 behaviors
            continue
        # Parameters action specific
        nexthop = None
        lookup_table = None
        interface = None
        segments = None
        # Parameters for End
        if isinstance(srv6_entity, SRv6EndBehavior):
            # End requires no parameter
            pass
        # Parameters for End.X
        if isinstance(srv6_entity, SRv6EndXBehavior):
            # Set the nexthop for the L3 cross-connect actions
            # (e.g. End.DX4, End.DX6)
            nexthop = text_type(srv6_entity.nexthop)
        # Parameters for End.T
        if isinstance(srv6_entity, SRv6EndTBehavior):
            # Set the table for the "decap and table lookup" actions
            # (e.g. End.DT4, End.DT6)
            lookup_table = int(srv6_entity.lookup_table)
        # Parameters for End.DX4
        if isinstance(srv6_entity, SRv6EndDX4Behavior):
            # Set the nexthop for the L3 cross-connect actions
            # (e.g. End.DX4, End.DX6)
            nexthop = text_type(srv6_entity.nexthop)
        # Parameters for End.DX6
        if isinstance(srv6_entity, SRv6EndDX6Behavior):
            # Set the nexthop for the L3 cross-connect actions
            # (e.g. End.DX4, End.DX6)
            nexthop = text_type(srv6_entity.nexthop)
        # Parameters for End.DX2
        if isinstance(srv6_entity, SRv6EndDX2Behavior):
            # Set the inteface for the L2 cross-connect actions
            # (e.g. End.DX2)
            interface = text_type(srv6_entity.interface)
        # Parameters for End.DT4
        if isinstance(srv6_entity, SRv6EndDT4Behavior):
            # Set the table for the "decap and table lookup" actions
            # (e.g. End.DT4, End.DT6)
            lookup_table = int(srv6_entity.lookup_table)
        # Parameters for End.DT6
        if isinstance(srv6_entity, SRv6EndDT6Behavior):
            # Set the table for the "decap and table lookup" actions
            # (e.g. End.DT4, End.DT6)
            lookup_table = int(srv6_entity.lookup_table)
        # Parameters for End.B6
        if isinstance(srv6_entity, SRv6EndB6Behavior):
            # Set the segments for the binding SID actions
            # (e.g. End.B6, End.B6.Encaps)
            for seg in srv6_entity.segments:
                segments = text_type(seg)
        # Parameters for End.B6.Encaps
        if isinstance(srv6_entity, SRv6EndB6EncapsBehavior):
            # Set the segments for the binding SID actions
            # (e.g. End.B6, End.B6.Encaps)
            for seg in srv6_entity.segments:
                segments = text_type(seg)
        # Remove the SRv6 behavior from the database
        arangodb_driver.delete_srv6_behavior(
            database=database,
            key=srv6_entity.key,
            grpc_address=srv6_entity.grpc_address,
            segment=srv6_entity.segment,
            action=srv6_entity.action,
            device=srv6_entity.device,
            table=srv6_entity.table,
            nexthop=nexthop,
            lookup_table=lookup_table,
            interface=interface,
            segments=segments,
            metric=srv6_entity.metric,
            fwd_engine=srv6_entity.fwd_engine
        )


def register_handlers(handlers):
    handlers.append({
        'name': 'srv6_behavior',
        'augment_entities': augment_srv6_behaviors,
        'do_entities_exist': do_srv6_behaviors_exist,
        'encode_entities': encode_srv6_behaviors,
        'decode_entities': decode_srv6_behaviors,
        'save_entities_to_db': save_to_db,
        'remove_entities_from_db': remove_from_db
    })
