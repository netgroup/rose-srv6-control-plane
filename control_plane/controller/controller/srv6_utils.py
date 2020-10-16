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
import os

import grpc
from six import text_type

# Proto dependencies
import commons_pb2
import srv6_manager_pb2
# Controller dependencies
import srv6_manager_pb2_grpc
from controller import arangodb_driver
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


def del_srv6_path_db(channel, destination, segments=None,
                     device='', encapmode="encap", table=-1, metric=-1,
                     bsid_addr='', fwd_engine='linux', key=None,
                     update_db=True, db_conn=None):
    if not os.getenv('ENABLE_PERSISTENCY') in ['true', 'True']:
        return commons_pb2.STATUS_INTERNAL_ERROR
    # gRPC address
    grpc_address = None
    if channel is not None:
        grpc_address = utils.grpc_chan_to_addr_port(channel)[0]
    # gRPC port number
    grpc_port = None
    if channel is not None:
        grpc_port = utils.grpc_chan_to_addr_port(channel)[1]
    # Find the paths matching the params
    srv6_paths = arangodb_driver.find_srv6_path(
        database=db_conn,
        key=key,
        grpc_address=grpc_address,
        grpc_port=grpc_port,
        destination=destination,
        segments=segments,
        device=device,
        encapmode=encapmode,
        table=table,
        metric=metric,
        bsid_addr=bsid_addr,
        fwd_engine=fwd_engine
    )
    if len(srv6_paths) == 0:
        # Entity not found
        logger.error('Entity not found')
        return commons_pb2.STATUS_NO_SUCH_PROCESS
    # Remove the paths
    for srv6_path in srv6_paths:
        # Initialize segments list
        if srv6_path['segments'] is None:
            segments = []
        # Create request message
        request = srv6_manager_pb2.SRv6ManagerRequest()
        # Create a new SRv6 path request
        path_request = request.srv6_path_request       # pylint: disable=no-member
        # Create a new path
        path = path_request.paths.add()
        # Set destination
        path.destination = text_type(srv6_path['destination'])
        # Set device
        # If the device is not specified (i.e. empty string),
        # it will be chosen by the gRPC server
        path.device = text_type(srv6_path['device'])
        # Set table ID
        # If the table ID is not specified (i.e. table=-1),
        # the main table will be used
        path.table = int(srv6_path['table'])
        # Set metric (i.e. preference value of the route)
        # If the metric is not specified (i.e. metric=-1),
        # the decision is left to the Linux kernel
        path.metric = int(srv6_path['metric'])
        # Set the BSID address (required for VPP)
        path.bsid_addr = str(srv6_path['bsid_addr'])
        # Forwarding engine (Linux or VPP)
        try:
            path_request.fwd_engine = srv6_manager_pb2.FwdEngine.Value(
                srv6_path['fwd_engine'].upper())
        except ValueError:
            logger.error('Invalid forwarding engine: %s', srv6_path['fwd_engine'])
            return commons_pb2.STATUS_INTERNAL_ERROR
        # Set encapmode
        path.encapmode = text_type(srv6_path['encapmode'])
        if len(srv6_path['segments']) == 0:
            logger.error('*** Missing segments for seg6 route')
            return commons_pb2.STATUS_INTERNAL_ERROR
        # Iterate on the segments and build the SID list
        for segment in srv6_path['segments']:
            # Append the segment to the SID list
            srv6_segment = path.sr_path.add()
            srv6_segment.segment = text_type(segment)
        # Get gRPC channel
        channel = utils.get_grpc_session(
            server_ip=srv6_path['grpc_address'],
            server_port=srv6_path['grpc_port']
        )
        # Get the reference of the stub
        stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
        # Remove the SRv6 path
        response = stub.Remove(request)
        # Get the status code of the gRPC operation
        response = response.status
        # Remove the path from the db
        arangodb_driver.delete_srv6_path(
            database=db_conn,
            key=srv6_path['_key'],
            grpc_address=srv6_path['grpc_address'],
            grpc_port=srv6_path['grpc_port'],
            destination=srv6_path['destination'],
            segments=srv6_path['segments'],
            device=srv6_path['device'],
            encapmode=srv6_path['encapmode'],
            table=srv6_path['table'],
            metric=srv6_path['metric'],
            bsid_addr=srv6_path['bsid_addr'],
            fwd_engine=srv6_path['fwd_engine']
        )
    # Done, return the reply
    return response


def handle_srv6_path(operation, channel, destination, segments=None,
                     device='', encapmode="encap", table=-1, metric=-1,
                     bsid_addr='', fwd_engine='linux', key=None,
                     update_db=True, db_conn=None):
    '''
    Handle a SRv6 Path
    '''
    # pylint: disable=too-many-locals, too-many-arguments, too-many-branches
    #
    # Check if a SRv6 path with the same key already exists
    if operation == 'add' and key is not None and \
            os.getenv('ENABLE_PERSISTENCY') in ['true', 'True']:
        paths = arangodb_driver.find_srv6_path(
            database=db_conn,
            key=key
        )
        if len(paths) > 0:
            logger.error('An entity with key %s already exists', key)
            raise utils.InvalidArgumentError
    #
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
    if fwd_engine == 'vpp' and operation == 'add':
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
        if res != commons_pb2.STATUS_SUCCESS:
            logger.error('Cannot create SRv6 policy: error %s', res)
            utils.raise_exception_on_error(res)
    # Forwarding engine (Linux or VPP)
    try:
        if fwd_engine != '':
            path_request.fwd_engine = srv6_manager_pb2.FwdEngine.Value(fwd_engine.upper())
        else:
            # By default, if forwarding engine is not specified, we use
            # Linux forwarding engine
            path_request.fwd_engine = srv6_manager_pb2.FwdEngine.Value('LINUX')
    except ValueError:
        logger.error('Invalid forwarding engine: %s', fwd_engine)
        raise utils.InvalidArgumentError
    try:
        # Fill the request depending on the operation
        # and send the request
        if operation == 'add':
            # Get the reference of the stub
            stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
            # Set encapmode
            if encapmode != '':
                path.encapmode = text_type(encapmode)
            else:
                # By default, if encap mode is not specified, we use
                # 'encap' mode
                path.encapmode = 'encap'
            if len(segments) == 0:
                logger.error('*** Missing segments for seg6 route')
                utils.raise_exception_on_error(
                    commons_pb2.STATUS_INTERNAL_ERROR)
            # Iterate on the segments and build the SID list
            for segment in segments:
                # Append the segment to the SID list
                srv6_segment = path.sr_path.add()
                srv6_segment.segment = text_type(segment)
            # Create the SRv6 path
            response = stub.Create(request)
            # Raise an exception if an error occurred
            utils.raise_exception_on_error(response.status)
            # Store the path to the database
            if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True'] and \
                    update_db:
                # Save the policy to the db
                arangodb_driver.insert_srv6_path(
                    database=db_conn,
                    key=key,
                    grpc_address=utils.grpc_chan_to_addr_port(channel)[0],
                    grpc_port=utils.grpc_chan_to_addr_port(channel)[1],
                    destination=destination,
                    segments=segments,
                    device=device,
                    encapmode=encapmode,
                    table=table,
                    metric=metric,
                    bsid_addr=bsid_addr,
                    fwd_engine=fwd_engine
                )
            return
        elif operation == 'get':
            if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True']:
                # Find the paths
                return arangodb_driver.find_srv6_path(
                   database=db_conn,
                   key=key if key != '' else None,
                   grpc_address=utils.grpc_chan_to_addr_port(channel)[0] if channel is not None else None,
                   grpc_port=utils.grpc_chan_to_addr_port(channel)[1] if channel is not None else None,
                   destination=destination if destination != '' else None,
                   segments=segments if segments != [''] else None,
                   device=device if device != '' else None,
                   encapmode=encapmode if encapmode != '' else None,
                   table=table if table != -1 else None,
                   metric=metric if metric != -1 else None,
                   bsid_addr=bsid_addr if bsid_addr != '' else None,
                   fwd_engine=fwd_engine if fwd_engine != '' else None
                )
            else:
                # Get the reference of the stub
                stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
                # Get the SRv6 path
                response = stub.Get(request)
                # Raise an exception if an error occurred
                utils.raise_exception_on_error(response.status)
                # Return the paths
                return response.paths
        elif operation == 'change':
            # Get the reference of the stub
            stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
            # Set encapmode
            path.encapmode = text_type(encapmode)
            # Iterate on the segments and build the SID list
            for segment in segments:
                # Append the segment to the SID list
                srv6_segment = path.sr_path.add()
                srv6_segment.segment = text_type(segment)
            # Update the SRv6 path
            response = stub.Update(request)
            # Raise an exception if an error occurred
            utils.raise_exception_on_error(response.status)
            # Remove the path from the database
            if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True'] and \
                    update_db:
                # Save the policy to the db
                arangodb_driver.update_srv6_path(
                    database=db_conn,
                    key=key,
                    grpc_address=utils.grpc_chan_to_addr_port(channel)[0],
                    grpc_port=utils.grpc_chan_to_addr_port(channel)[1],
                    destination=destination,
                    segments=segments,
                    device=device,
                    encapmode=encapmode,
                    table=table,
                    metric=metric,
                    bsid_addr=bsid_addr,
                    fwd_engine=fwd_engine
                )
            return
        elif operation == 'del':
            # Remove the SRv6 path
            if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True'] and \
                    update_db:
                response = del_srv6_path_db(
                    channel=channel,
                    key=key if key != '' else None,
                    destination=destination if destination != '' else None,
                    segments=segments if segments != [''] else None,
                    device=device if device != '' else None,
                    encapmode=encapmode if encapmode != '' else None,
                    table=table if table != -1 else None,
                    metric=metric if metric != -1 else None,
                    bsid_addr=bsid_addr if bsid_addr != '' else None,
                    fwd_engine=fwd_engine if fwd_engine != '' else None,
                    update_db=update_db,
                    db_conn=db_conn
                )
                # Raise an exception if an error occurred
                utils.raise_exception_on_error(response)
            else:
                # Get the reference of the stub
                stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
                # Remove the SRv6 path
                response = stub.Remove(request)
                # Raise an exception if an error occurred
                utils.raise_exception_on_error(response.status)
            return
        else:
            # Operation not supported
            logger.error('Operation not supported')
            # Raise an exception
            utils.raise_exception_on_error(
                commons_pb2.STATUS_OPERATION_NOT_SUPPORTED)
    except grpc.RpcError as err:
        # An error occurred during the gRPC operation
        # Parse the error and return it
        response = parse_grpc_error(err)
        # Raise an exception
        utils.raise_exception_on_error(response)


def handle_srv6_policy(operation, channel, bsid_addr, segments=None,
                       table=-1, metric=-1, fwd_engine='linux'):
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
            fwd_engine.upper())
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


def del_srv6_behavior_db(channel, segment, action='', device='',
                         table=-1, nexthop="", lookup_table=-1,
                         interface="", segments=None, metric=-1,
                         fwd_engine='linux', key=None, update_db=True,
                         db_conn=None):
    if not os.getenv('ENABLE_PERSISTENCY') in ['true', 'True']:
        return commons_pb2.STATUS_INTERNAL_ERROR
    # gRPC address
    grpc_address = None
    if channel is not None:
        grpc_address = utils.grpc_chan_to_addr_port(channel)[0]
    # gRPC port number
    grpc_port = None
    if channel is not None:
        grpc_port = utils.grpc_chan_to_addr_port(channel)[1]
    # Find the behaviors matching the params
    srv6_behaviors = arangodb_driver.find_srv6_behavior(
        database=db_conn,
        grpc_address=grpc_address,
        grpc_port=grpc_port,
        segment=segment,
        action=action,
        device=device,
        table=table,
        nexthop=nexthop,
        lookup_table=lookup_table,
        interface=interface,
        segments=segments,
        metric=metric,
        fwd_engine=fwd_engine,
        key=key
    )
    if len(srv6_behaviors) == 0:
        # Entity not found
        logger.error('Entity not found')
        return commons_pb2.STATUS_NO_SUCH_PROCESS
    # Remove the behaviors
    for srv6_behavior in srv6_behaviors:
        # Initialize segments list
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
        behavior.segment = srv6_behavior['segment']
        # Set the table where the seg6local must be inserted
        # If the table ID is not specified (i.e. table=-1),
        # the main table will be used
        behavior.table = srv6_behavior['table']
        # Set device
        # If the device is not specified (i.e. empty string),
        # it will be chosen by the gRPC server
        behavior.device = srv6_behavior['device']
        # Set metric (i.e. preference value of the route)
        # If the metric is not specified (i.e. metric=-1),
        # the decision is left to the Linux kernel
        behavior.metric = srv6_behavior['metric']
        # Set the action for the seg6local route
        behavior.action = text_type(srv6_behavior['action'])
        # Set the nexthop for the L3 cross-connect actions
        # (e.g. End.DX4, End.DX6)
        behavior.nexthop = text_type(srv6_behavior['nexthop'])
        # Set the table for the "decap and table lookup" actions
        # (e.g. End.DT4, End.DT6)
        behavior.lookup_table = int(srv6_behavior['lookup_table'])
        # Set the inteface for the L2 cross-connect actions
        # (e.g. End.DX2)
        behavior.interface = text_type(srv6_behavior['interface'])
        # Set the segments for the binding SID actions
        # (e.g. End.B6, End.B6.Encaps)
        for seg in srv6_behavior['segments']:
            # Create a new segment
            srv6_segment = behavior.segs.add()
            srv6_segment.segment = text_type(seg)
        # Forwarding engine (Linux or VPP)
        try:
            behavior_request.fwd_engine = srv6_manager_pb2.FwdEngine.Value(
                srv6_behavior['fwd_engine'].upper())
        except ValueError:
            logger.error('Invalid forwarding engine: %s', fwd_engine)
            return commons_pb2.STATUS_INTERNAL_ERROR
        # Get gRPC channel
        channel = utils.get_grpc_session(
            server_ip=srv6_behavior['grpc_address'],
            server_port=srv6_behavior['grpc_port']
        )
        # Get the reference of the stub
        stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
        # Remove the SRv6 path
        response = stub.Remove(request)
        # Get the status code of the gRPC operation
        response = response.status
        # Remove the path from the db
        arangodb_driver.delete_srv6_behavior(
            database=db_conn,
            key=srv6_behavior['_key'],
            grpc_address=srv6_behavior['grpc_address'],
            grpc_port=srv6_behavior['grpc_port'],
            segment=srv6_behavior['segment'],
            action=srv6_behavior['action'],
            device=srv6_behavior['device'],
            table=srv6_behavior['table'],
            nexthop=srv6_behavior['nexthop'],
            lookup_table=srv6_behavior['lookup_table'],
            interface=srv6_behavior['interface'],
            segments=srv6_behavior['segments'],
            metric=srv6_behavior['metric'],
            fwd_engine=srv6_behavior['fwd_engine']
        )
    # Done, return the reply
    return response


def handle_srv6_behavior(operation, channel, segment, action='', device='',
                         table=-1, nexthop="", lookup_table=-1,
                         interface="", segments=None, metric=-1,
                         fwd_engine='linux', key=None, update_db=True,
                         db_conn=None):
    '''
    Handle a SRv6 behavior
    '''
    # pylint: disable=too-many-arguments, too-many-locals
    #
    # Check if a SRv6 behavior with the same key already exists
    if operation == 'add' and key is not None and \
            os.getenv('ENABLE_PERSISTENCY') in ['true', 'True']:
        behaviors = arangodb_driver.find_srv6_behavior(
            database=db_conn,
            key=key
        )
        if len(behaviors) > 0:
            logger.error('An entity with key %s already exists', key)
            raise utils.InvalidArgumentError
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
            fwd_engine.upper())
    except ValueError:
        logger.error('Invalid forwarding engine: %s', fwd_engine)
        raise utils.InvalidArgumentError
    try:
        # Fill the request depending on the operation
        # and send the request
        if operation == 'add':
            if action == '':
                logger.error('*** Missing action for seg6local route')
                utils.raise_exception_on_error(
                    commons_pb2.STATUS_INTERNAL_ERROR)
            # Get the reference of the stub
            stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
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
            # Raise an exception if an error occurred
            utils.raise_exception_on_error(response.status)
            # Store the path to the database
            if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True'] and \
                    update_db:
                # Save the behavior to the db
                arangodb_driver.insert_srv6_behavior(
                    database=db_conn,
                    key=key,
                    grpc_address=utils.grpc_chan_to_addr_port(channel)[0],
                    grpc_port=utils.grpc_chan_to_addr_port(channel)[1],
                    segment=segment,
                    action=action,
                    device=device,
                    table=table,
                    nexthop=nexthop,
                    lookup_table=lookup_table,
                    interface=interface,
                    segments=segments,
                    metric=metric,
                    fwd_engine=fwd_engine
                )
            return
        elif operation == 'get':
            if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True']:
                # Find the behaviors
                return arangodb_driver.find_srv6_behavior(
                   database=db_conn,
                   key=key if key != '' else None,
                   grpc_address=utils.grpc_chan_to_addr_port(channel)[0] if channel is not None else None,
                   grpc_port=utils.grpc_chan_to_addr_port(channel)[1] if channel is not None else None,
                   segment=segment if segment != '' else None,
                   action=action if action != '' else None,
                   device=device if device != '' else None,
                   table=table if table != -1 else None,
                   nexthop=nexthop if nexthop != '' else None,
                   lookup_table=lookup_table if lookup_table != -1 else None,
                   interface=interface if interface != '' else None,
                   segments=segments if segments != [''] else None,
                   metric=metric if metric != -1 else None,
                   fwd_engine=fwd_engine if fwd_engine != '' else None
                )
            else:
                # Get the reference of the stub
                stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
                # Get the SRv6 behavior
                response = stub.Get(request)
                # Raise an exception if an error occurred
                utils.raise_exception_on_error(response.status)
                # Return the paths
                return response.paths
        elif operation == 'change':
            # Get the reference of the stub
            stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
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
            # Raise an exception if an error occurred
            utils.raise_exception_on_error(response.status)
            # Remove the path from the database
            if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True'] and \
                    update_db:
                # Save the behavior to the db
                arangodb_driver.update_srv6_behavior(
                    database=db_conn,
                    key=key,
                    grpc_address=utils.grpc_chan_to_addr_port(channel)[0],
                    grpc_port=utils.grpc_chan_to_addr_port(channel)[1],
                    segment=segment,
                    action=action,
                    device=device,
                    table=table,
                    nexthop=nexthop,
                    lookup_table=lookup_table,
                    interface=interface,
                    segments=segments,
                    metric=metric,
                    fwd_engine=fwd_engine
                )
            return
        elif operation == 'del':
            # Remove the SRv6 behavior
            if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True'] and \
                    update_db:
                response = del_srv6_behavior_db(
                    channel=channel,
                    key=key if key != '' else None,
                    segment=segment if segment != '' else None,
                    action=action if action != '' else None,
                    device=device if device != '' else None,
                    table=table if table != -1 else None,
                    nexthop=nexthop if nexthop != '' else None,
                    lookup_table=lookup_table if lookup_table != -1 else None,
                    interface=interface if interface != '' else None,
                    segments=segments if segments != [''] else None,
                    metric=metric if metric != -1 else None,
                    fwd_engine=fwd_engine if fwd_engine != '' else None,
                    update_db=update_db,
                    db_conn=db_conn
                )
                # Raise an exception if an error occurred
                utils.raise_exception_on_error(response)
            else:
                # Get the reference of the stub
                stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
                # Remove the SRv6 behavior
                response = stub.Remove(request)
                # Raise an exception if an error occurred
                utils.raise_exception_on_error(response.status)
        else:
            # Operation not supported
            logger.error('Operation not supported')
            # Raise an exception
            utils.raise_exception_on_error(
                commons_pb2.STATUS_OPERATION_NOT_SUPPORTED)
    except grpc.RpcError as err:
        # An error occurred during the gRPC operation
        # Parse the error and return it
        response = parse_grpc_error(err)
        # Raise an exception
        utils.raise_exception_on_error(response)


class SRv6Exception(Exception):
    '''
    Generic SRv6 Exception.
    '''


def create_uni_srv6_tunnel(ingress_channel, egress_channel,
                           destination, segments, localseg=None,
                           bsid_addr='', fwd_engine='linux', key=None,
                           update_db=True, db_conn=None):
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
    # pylint: disable=too-many-arguments
    #
    # Check if a SRv6 tunnel with the same key already exists
    if key is not None and \
            os.getenv('ENABLE_PERSISTENCY') in ['true', 'True']:
        paths = arangodb_driver.find_srv6_tunnel(
            database=db_conn,
            key=key
        )
        if len(paths) > 0:
            logger.error('An entity with key %s already exists', key)
            raise utils.InvalidArgumentError
    # Add seg6 route to <ingress> to steer the packets sent to the
    # <destination> through the SID list <segments>
    #
    # Equivalent to the command:
    #    ingress: ip -6 route add <destination> encap seg6 mode encap \
    #            segs <segments> dev <device>
    handle_srv6_path(
        operation='add',
        channel=ingress_channel,
        destination=destination,
        segments=segments,
        bsid_addr=bsid_addr,
        fwd_engine=fwd_engine,
        update_db=False,
        db_conn=db_conn
    )
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
        handle_srv6_behavior(
            operation='add',
            channel=egress_channel,
            segment=localseg,
            action='End.DT6',
            lookup_table=254,
            fwd_engine=fwd_engine,
            update_db=False,
            db_conn=db_conn
        )
    # Add the tunnel to the database
    if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True'] and \
            update_db:
        # Save the tunnel to the db
        arangodb_driver.insert_srv6_tunnel(
            database=db_conn,
            l_grpc_address=utils.grpc_chan_to_addr_port(ingress_channel)[0],
            l_grpc_port=utils.grpc_chan_to_addr_port(ingress_channel)[1],
            r_grpc_address=utils.grpc_chan_to_addr_port(egress_channel)[0],
            r_grpc_port=utils.grpc_chan_to_addr_port(egress_channel)[1],
            sidlist_lr=segments,
            dest_lr=destination,
            localseg_lr=localseg,
            bsid_addr=bsid_addr,
            fwd_engine=fwd_engine,
            is_unidirectional=True,
            key=key
        )


def create_srv6_tunnel(node_l_channel, node_r_channel,
                       sidlist_lr, sidlist_rl, dest_lr, dest_rl,
                       localseg_lr=None, localseg_rl=None,
                       bsid_addr='', fwd_engine='linux', update_db=True,
                       key=None, db_conn=None):
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
    # Check if a SRv6 tunnel with the same key already exists
    if key is not None and \
            os.getenv('ENABLE_PERSISTENCY') in ['true', 'True']:
        paths = arangodb_driver.find_srv6_tunnel(
            database=db_conn,
            key=key
        )
        if len(paths) > 0:
            logger.error('An entity with key %s already exists', key)
            raise utils.InvalidArgumentError
    # Create a unidirectional SRv6 tunnel from <node_l> to <node_r>
    create_uni_srv6_tunnel(
        ingress_channel=node_l_channel,
        egress_channel=node_r_channel,
        destination=dest_lr,
        segments=sidlist_lr,
        localseg=localseg_lr,
        bsid_addr=bsid_addr,
        fwd_engine=fwd_engine,
        update_db=False,
        db_conn=db_conn
    )
    # Create a unidirectional SRv6 tunnel from <node_r> to <node_l>
    create_uni_srv6_tunnel(
        ingress_channel=node_r_channel,
        egress_channel=node_l_channel,
        destination=dest_rl,
        segments=sidlist_rl,
        localseg=localseg_rl,
        bsid_addr=bsid_addr,
        fwd_engine=fwd_engine,
        update_db=False,
        db_conn=db_conn
    )
    # Add the tunnel to the database
    if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True'] and \
            update_db:
        # Save the tunnel to the db
        arangodb_driver.insert_srv6_tunnel(
            database=db_conn,
            l_grpc_address=utils.grpc_chan_to_addr_port(node_l_channel)[0],
            l_grpc_port=utils.grpc_chan_to_addr_port(node_l_channel)[1],
            r_grpc_address=utils.grpc_chan_to_addr_port(node_r_channel)[0],
            r_grpc_port=utils.grpc_chan_to_addr_port(node_r_channel)[1],
            sidlist_lr=sidlist_lr,
            sidlist_rl=sidlist_rl,
            dest_lr=dest_lr,
            dest_rl=dest_rl,
            localseg_lr=localseg_lr,
            localseg_rl=localseg_rl,
            bsid_addr=bsid_addr,
            fwd_engine=fwd_engine,
            is_unidirectional=False,
            key=key
        )


def del_uni_srv6_tunnel_db(ingress_channel, egress_channel, destination,
                           localseg=None, bsid_addr='', fwd_engine='linux',
                           ignore_errors=False, key=None, db_conn=None):
    if not os.getenv('ENABLE_PERSISTENCY') in ['true', 'True']:
        return commons_pb2.STATUS_INTERNAL_ERROR
    # Find the tunnels matching the params
    srv6_tunnels = arangodb_driver.find_srv6_tunnel(
        database=db_conn,
        key=key,
        l_grpc_address=utils.grpc_chan_to_addr_port(ingress_channel)[0],
        l_grpc_port=utils.grpc_chan_to_addr_port(ingress_channel)[1],
        r_grpc_address=utils.grpc_chan_to_addr_port(egress_channel)[0],
        r_grpc_port=utils.grpc_chan_to_addr_port(egress_channel)[1],
        dest_lr=destination,
        localseg_lr=localseg,
        bsid_addr=bsid_addr,
        fwd_engine=fwd_engine,
        is_unidirectional=True
    )
    if len(srv6_tunnels) == 0:
        # Entity not found
        logger.error('Entity not found')
        return commons_pb2.STATUS_NO_SUCH_PROCESS
    # Remove the tunnels
    for srv6_tunnel in srv6_tunnels:
        # Get a gRPC channel to the ingress node
        ingress_channel = utils.get_grpc_session(
            server_ip=srv6_tunnel['l_grpc_address'],
            server_port=srv6_tunnel['l_grpc_port']
        )
        # Get a gRPC channel to the egress node
        egress_channel = utils.get_grpc_session(
            server_ip=srv6_tunnel['r_grpc_address'],
            server_port=srv6_tunnel['r_grpc_port']
        )
        # Remove seg6 route from <ingress> to steer the packets sent to
        # <destination> through the SID list <segments>
        #
        # Equivalent to the command:
        #    ingress: ip -6 route del <destination> encap seg6 mode encap \
        #             segs <segments> dev <device>
        res = handle_srv6_path(     # FIXME res = None
            operation='del',
            channel=ingress_channel,
            destination=srv6_tunnel['dest_lr'],
            bsid_addr=srv6_tunnel['bsid_addr'],
            fwd_engine=srv6_tunnel['fwd_engine'],
            update_db=False,
            db_conn=db_conn
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
            res = handle_srv6_behavior(     # FIXME res = None
                operation='del',
                channel=egress_channel,
                segment=srv6_tunnel['localseg_lr'],
                fwd_engine=srv6_tunnel['fwd_engine'],
                update_db=False,
                db_conn=db_conn
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
        # Remove the path from the db
        arangodb_driver.delete_srv6_tunnel(
            database=db_conn,
            key=srv6_tunnel['_key'],
            l_grpc_address=srv6_tunnel['l_grpc_address'],
            l_grpc_port=srv6_tunnel['l_grpc_port'],
            r_grpc_address=srv6_tunnel['r_grpc_address'],
            r_grpc_port=srv6_tunnel['r_grpc_port'],
            dest_lr=srv6_tunnel['dest_lr'],
            localseg_lr=srv6_tunnel['localseg_lr'],
            bsid_addr=srv6_tunnel['bsid_addr'],
            fwd_engine=srv6_tunnel['fwd_engine'],
            is_unidirectional=True
        )
        # Success
        return commons_pb2.STATUS_SUCCESS


def destroy_uni_srv6_tunnel(ingress_channel, egress_channel, destination,
                            localseg=None, bsid_addr='', fwd_engine='linux',
                            ignore_errors=False, key=None, update_db=True,
                            db_conn=None):
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
    # pylint: disable=too-many-arguments
    #
    # Remove the SRv6 behavior
    if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True'] and update_db:
        res = del_uni_srv6_tunnel_db(
            ingress_channel=ingress_channel,
            egress_channel=egress_channel,
            destination=destination,
            localseg=localseg,
            bsid_addr=bsid_addr,
            fwd_engine=fwd_engine,
            ignore_errors=ignore_errors,
            key=key,
            db_conn=db_conn
        )
        # Raise an exception if an error occurred
        utils.raise_exception_on_error(res)
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
        fwd_engine=fwd_engine,
        update_db=False,
        db_conn=db_conn
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
            # Raise an exception if an error occurred
            utils.raise_exception_on_error(res)
    elif res != commons_pb2.STATUS_SUCCESS:
        # Raise an exception if an error occurred
        utils.raise_exception_on_error(res)
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
            fwd_engine=fwd_engine,
            update_db=False,
            db_conn=db_conn
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
                # Raise an exception if an error occurred
                utils.raise_exception_on_error(res)
        elif res != commons_pb2.STATUS_SUCCESS:
            # Raise an exception if an error occurred
            utils.raise_exception_on_error(res)


def del_bidi_srv6_tunnel_db(node_l_channel, node_r_channel,
                            dest_lr, dest_rl, localseg_lr=None,
                            localseg_rl=None, bsid_addr='',
                            fwd_engine='linux', ignore_errors=False,
                            key=None, db_conn=None):
    if not os.getenv('ENABLE_PERSISTENCY') in ['true', 'True']:
        return commons_pb2.STATUS_INTERNAL_ERROR
    # Find the tunnels matching the params
    srv6_tunnels = arangodb_driver.find_srv6_tunnel(
        database=db_conn,
        key=key,
        l_grpc_address=utils.grpc_chan_to_addr_port(node_l_channel)[0],
        l_grpc_port=utils.grpc_chan_to_addr_port(node_l_channel)[1],
        r_grpc_address=utils.grpc_chan_to_addr_port(node_r_channel)[0],
        r_grpc_port=utils.grpc_chan_to_addr_port(node_r_channel)[1],
        dest_lr=dest_lr,
        dest_rl=dest_rl,
        localseg_lr=localseg_lr,
        localseg_rl=localseg_rl,
        bsid_addr=bsid_addr,
        fwd_engine=fwd_engine,
        is_unidirectional=False
    )
    if len(srv6_tunnels) == 0:
        # Entity not found
        logger.error('Entity not found')
        return commons_pb2.STATUS_NO_SUCH_PROCESS
    # Remove the tunnels
    for srv6_tunnel in srv6_tunnels:
        # Get a gRPC channel to the ingress node
        node_l_channel = utils.get_grpc_session(
            server_ip=srv6_tunnel['l_grpc_address'],
            server_port=srv6_tunnel['l_grpc_port']
        )
        # Get a gRPC channel to the egress node
        node_r_channel = utils.get_grpc_session(
            server_ip=srv6_tunnel['r_grpc_address'],
            server_port=srv6_tunnel['r_grpc_port']
        )
        # Remove unidirectional SRv6 tunnel from <node_l> to <node_r>
        res = destroy_uni_srv6_tunnel(
            ingress_channel=node_l_channel,
            egress_channel=node_r_channel,
            destination=srv6_tunnel['dest_lr'],
            localseg=srv6_tunnel['localseg_lr'],
            ignore_errors=ignore_errors,
            bsid_addr=srv6_tunnel['bsid_addr'],
            fwd_engine=srv6_tunnel['fwd_engine'],
            update_db=False,
            db_conn=db_conn
        )
        # If an error occurred, abort the operation
        if res != commons_pb2.STATUS_SUCCESS:
            return res
        # Remove unidirectional SRv6 tunnel from <node_r> to <node_l>
        res = destroy_uni_srv6_tunnel(
            ingress_channel=node_r_channel,
            egress_channel=node_l_channel,
            destination=srv6_tunnel['dest_rl'],
            localseg=srv6_tunnel['localseg_rl'],
            ignore_errors=ignore_errors,
            bsid_addr=srv6_tunnel['bsid_addr'],
            fwd_engine=srv6_tunnel['fwd_engine'],
            update_db=False,
            db_conn=db_conn
        )
        # If an error occurred, abort the operation
        if res != commons_pb2.STATUS_SUCCESS:
            return res
        # Remove the path from the db
        arangodb_driver.delete_srv6_tunnel(
            database=db_conn,
            key=srv6_tunnel['_key'],
            l_grpc_address=srv6_tunnel['l_grpc_address'],
            l_grpc_port=srv6_tunnel['l_grpc_port'],
            r_grpc_address=srv6_tunnel['r_grpc_address'],
            r_grpc_port=srv6_tunnel['r_grpc_port'],
            dest_lr=srv6_tunnel['dest_lr'],
            dest_rl=srv6_tunnel['dest_rl'],
            localseg_lr=srv6_tunnel['localseg_lr'],
            localseg_rl=srv6_tunnel['localseg_rl'],
            bsid_addr=srv6_tunnel['bsid_addr'],
            fwd_engine=srv6_tunnel['fwd_engine'],
            is_unidirectional=False
        )
        # Success
        return commons_pb2.STATUS_SUCCESS


def destroy_srv6_tunnel(node_l_channel, node_r_channel,
                        dest_lr, dest_rl, localseg_lr=None, localseg_rl=None,
                        bsid_addr='', fwd_engine='linux',
                        ignore_errors=False, key=None, update_db=True,
                        db_conn=None):
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
    # Remove the SRv6 behavior
    if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True'] and \
            update_db:
        res = del_bidi_srv6_tunnel_db(
            node_l_channel=node_l_channel,
            node_r_channel=node_r_channel,
            dest_lr=dest_lr,
            dest_rl=dest_rl,
            localseg_lr=localseg_lr,
            localseg_rl=localseg_rl,
            bsid_addr=bsid_addr,
            fwd_engine=fwd_engine,
            key=key,
            ignore_errors=ignore_errors,
            db_conn=db_conn
        )
        # Raise an exception if an error occurred
        utils.raise_exception_on_error(res)
    # Remove unidirectional SRv6 tunnel from <node_l> to <node_r>
    res = destroy_uni_srv6_tunnel(
        ingress_channel=node_l_channel,
        egress_channel=node_r_channel,
        destination=dest_lr,
        localseg=localseg_lr,
        ignore_errors=ignore_errors,
        bsid_addr=bsid_addr,
        fwd_engine=fwd_engine,
        update_db=False,
        db_conn=db_conn
    )
    # Raise an exception if an error occurred
    utils.raise_exception_on_error(res)
    # Remove unidirectional SRv6 tunnel from <node_r> to <node_l>
    res = destroy_uni_srv6_tunnel(
        ingress_channel=node_r_channel,
        egress_channel=node_l_channel,
        destination=dest_rl,
        localseg=localseg_rl,
        ignore_errors=ignore_errors,
        bsid_addr=bsid_addr,
        fwd_engine=fwd_engine,
        update_db=False,
        db_conn=db_conn
    )
    # Raise an exception if an error occurred
    utils.raise_exception_on_error(res)


def get_uni_srv6_tunnel(ingress_channel, egress_channel,
                        destination, segments, localseg=None,
                        bsid_addr='', fwd_engine='linux', key=None,
                        db_conn=None):
    '''
    Get a unidirectional SRv6 tunnel from <ingress> to <egress>

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
    if os.getenv('ENABLE_PERSISTENCY') not in ['true', 'True']:
        logger.error('Get tunnel requires ENABLE_PERSISTENCY')
        raise utils.InvalidArgumentError
    # Retrieve the tunnel from the database
    #
    # Retrieve the tunnel from the db
    return arangodb_driver.find_srv6_tunnel(
        database=db_conn,
        key=key if key != '' else None,
        l_grpc_address=utils.grpc_chan_to_addr_port(ingress_channel)[0] if ingress_channel is not None else None,
        l_grpc_port=utils.grpc_chan_to_addr_port(ingress_channel)[1] if ingress_channel is not None else None,
        r_grpc_address=utils.grpc_chan_to_addr_port(egress_channel)[0] if egress_channel is not None else None,
        r_grpc_port=utils.grpc_chan_to_addr_port(egress_channel)[1] if egress_channel is not None else None,
        sidlist_lr=list(segments) if len(segments) > 0 else None,
        sidlist_rl=None,
        dest_lr=destination if destination != '' else None,
        dest_rl=None,
        localseg_lr=localseg if localseg != '' else None,
        localseg_rl=None,
        bsid_addr=bsid_addr if bsid_addr != '' else None,
        fwd_engine=fwd_engine if fwd_engine != '' else None,
        is_unidirectional=True
    )


def get_srv6_tunnel(node_l_channel, node_r_channel,
                       sidlist_lr, sidlist_rl, dest_lr, dest_rl,
                       localseg_lr=None, localseg_rl=None,
                       bsid_addr='', fwd_engine='linux', update_db=True,
                       key=None, db_conn=None):
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
    if os.getenv('ENABLE_PERSISTENCY') not in ['true', 'True']:
        logger.error('Get tunnel requires ENABLE_PERSISTENCY')
        raise utils.InvalidArgumentError
    # Retrieve the tunnel from the database
    #
    # Retrieve the tunnel from the db
    return arangodb_driver.find_srv6_tunnel(
        database=db_conn,
        key=key if key != '' else None,
        l_grpc_address=utils.grpc_chan_to_addr_port(node_l_channel)[0] if node_l_channel is not None else None,
        l_grpc_port=utils.grpc_chan_to_addr_port(node_l_channel)[1] if node_l_channel is not None else None,
        r_grpc_address=utils.grpc_chan_to_addr_port(node_r_channel)[0] if node_r_channel is not None else None,
        r_grpc_port=utils.grpc_chan_to_addr_port(node_r_channel)[1] if node_r_channel is not None else None,
        sidlist_lr=list(sidlist_lr) if len(sidlist_lr) > 0 else None,
        sidlist_rl=list(sidlist_rl) if len(sidlist_rl) > 0 else None,
        dest_lr=dest_lr if dest_lr != '' else None,
        dest_rl=dest_rl if dest_rl != '' else None,
        localseg_lr=localseg_lr if localseg_lr != '' else None,
        localseg_rl=localseg_rl if localseg_rl != '' else None,
        bsid_addr=bsid_addr if bsid_addr != '' else None,
        fwd_engine=fwd_engine if fwd_engine != '' else None,
        is_unidirectional=False
    )
