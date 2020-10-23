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


"""
Control-Plane functionalities for SRv6 Manager
"""

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


# ############################################################################
# Forwarding Engine
class FwdEngine(Enum):
    """
    Forwarding Engine.
    """
    LINUX = nb_commons_pb2.FwdEngine.Value('LINUX')
    VPP = nb_commons_pb2.FwdEngine.Value('VPP')
    P4 = nb_commons_pb2.FwdEngine.Value('P4')


# Mapping python representation of Forwarding Engine to gRPC representation
py_to_grpc_fwd_engine = {
    'linux': FwdEngine.LINUX.value,
    'vpp': FwdEngine.VPP.value,
    'p4': FwdEngine.P4.value
}

# Mapping gRPC representation of Forwarding Engine to python representation
grpc_to_py_fwd_engine = {
    v: k for k, v in py_to_grpc_fwd_engine.items()}


# ############################################################################
# Controller APIs


# Parser for gRPC errors
def parse_grpc_error(err):
    """
    Convert a gRPC error to a status code.

    :param err: The error returned by gRPC.
    :type err: class `grpc.RpcError`
    :return: The status code corresponding to the gRPC error.
    :rtype: int
    """
    # Extract the error code from the gRPC exception
    status_code = err.code()
    # Extract the error details from the gRPC exception
    details = err.details()
    # Log the error
    logger.error('gRPC client reported an error: %s, %s',
                 status_code, details)
    # Return the status code corresponding to the error code
    if grpc.StatusCode.UNAVAILABLE == status_code:
        return commons_pb2.STATUS_GRPC_SERVICE_UNAVAILABLE
    if grpc.StatusCode.UNAUTHENTICATED == status_code:
        return commons_pb2.STATUS_GRPC_UNAUTHORIZED
    return commons_pb2.STATUS_INTERNAL_ERROR


def add_srv6_path(grpc_address, grpc_port, destination,
                  segments=None, device='', encapmode='encap', table=-1,
                  metric=-1, bsid_addr='', fwd_engine='linux', key=None,
                  update_db=True, db_conn=None, channel=None):
    # Segment list is mandatory for "add" operation
    if segments is None or len(segments) == 0:
        logger.error('*** Missing segments for seg6 route')
        raise utils.InvalidArgumentError
    # If database persistency is enabled, we need to check if a SRv6 path with
    # the same key already exists
    if key is not None and \
            os.getenv('ENABLE_PERSISTENCY') in ['true', 'True']:
        # Perform a lookup by key into the database
        paths = arangodb_driver.find_srv6_path(
            database=db_conn,
            key=key
        )
        # Check if we found a path with the same key
        if len(paths) > 0:
            logger.error('An entity with key %s already exists', key)
            raise utils.InvalidArgumentError
    # All checks passed, we are ready to create the SRv6 path
    #
    # In order to add a SRv6 path we need to interact with the node
    # If no gRPC channel has been provided, we need to open a new channel
    # to the node; in this case, grpc_address and grpc_port arguments are
    # required
    if channel is None:
        # Check arguments
        if grpc_address is None or \
                grpc_address == '' or grpc_port is None or grpc_port == -1:
            logger.error('"add" operation requires a gRPC channel or gRPC '
                         'address/port')
            raise utils.InvalidArgumentError
        # Establish a gRPC channel to the destination
        channel = utils.get_grpc_session(grpc_address, grpc_port)
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
    # Set the encapsulation mode
    if encapmode != '':
        # encap mode is an optional argument
        # If it is specified, we use it
        path.encapmode = text_type(encapmode)
    else:
        # By default, if encap mode is not specified, we use
        # 'encap' mode
        path.encapmode = 'encap'
    # Iterate on the segments and build the SID list
    for segment in segments:
        # Append the segment to the SID list
        srv6_segment = path.sr_path.add()
        srv6_segment.segment = text_type(segment)
    # Set the forwarding engine
    try:
        if fwd_engine is not None and fwd_engine != '':
            # Encode fwd engine in a format supported by gRPC
            path_request.fwd_engine = py_to_grpc_fwd_engine(fwd_engine)
        else:
            # By default, if forwarding engine is not specified, we use
            # Linux forwarding engine
            path_request.fwd_engine = FwdEngine.LINUX.value
    except ValueError:
        # An invalid value for fwd_engine has been provided
        logger.error('Invalid forwarding engine: %s', fwd_engine)
        raise utils.InvalidArgumentError
    # VPP forwarding engine requires some extra steps
    if fwd_engine == 'vpp':
        # VPP requires a SRv6 policy associated to the SRv6 path through the
        # BSID address
        # Let's check if we provided a BSID address
        if bsid_addr is None or bsid_addr == '':
            logger.error('"bsid_addr" argument is mandatory for VPP')
            raise utils.InvalidArgumentError
        # Create SRv6 policy
        handle_srv6_policy(
            operation='add',
            channel=channel,
            bsid_addr=bsid_addr,
            segments=segments,
            table=table,
            metric=metric,
            fwd_engine=fwd_engine
        )
    # The other steps are common for both Linux and VPP forwarding engines+
    #
    # Let's create the SRv6 path
    try:
        # Get the reference of the stub
        stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
        # Create the SRv6 path and get the status code
        status = stub.Create(request).status
    except grpc.RpcError as err:
        # An error occurred during the gRPC operation
        # Parse the gRPC error and get the status code
        status = parse_grpc_error(err)
    finally:
        # Raise an exception if an error occurred
        utils.raise_exception_on_error(status)
    # If the persistecy is enable, store the path to the database
    if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True'] and \
            update_db:
        # Save the path to the db
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


def get_srv6_path(grpc_address, grpc_port, destination,
                  segments=None, device='', encapmode='encap', table=-1,
                  metric=-1, bsid_addr='', fwd_engine='linux', key=None,
                  update_db=True, db_conn=None, channel=None):
    # If segment list not provided, initialize it to an empty list
    if segments is None:
        segments = []
    # We need to support two scenarios:
    #  -  Persistency enabled
    #  -  Persistency not enabled
    if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True']:
        # Persistency is enabled
        #
        # Perform a lookup in the database and store the SRv6 paths found
        srv6_paths = arangodb_driver.find_srv6_path(
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
        # Persistency is not enabled
        #
        # We need to interact with the node to retrieve the SRv6 paths
        try:
            # In order to get a SRv6 path we need to interact with the node
            # If no gRPC channel has been provided, we need to open a new channel
            # to the node; in this case, grpc_address and grpc_port arguments are
            # required
            if channel is None:
                if grpc_address is None or \
                        grpc_address == '' or grpc_port is None or grpc_port == -1:
                    logger.error('"get" operation requires a gRPC channel or gRPC '
                                'address/port')
                    raise utils.InvalidArgumentError
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
            # Set the forwarding engine
            try:
                if fwd_engine is not None and fwd_engine != '':
                    # Encode fwd engine in a format supported by gRPC
                    path_request.fwd_engine = py_to_grpc_fwd_engine(fwd_engine)
                else:
                    # By default, if forwarding engine is not specified, we use
                    # Linux forwarding engine
                    path_request.fwd_engine = FwdEngine.LINUX.value
            except ValueError:
                # An invalid value for fwd_engine has been provided
                logger.error('Invalid forwarding engine: %s', fwd_engine)
                raise utils.InvalidArgumentError
            # Get the reference of the stub
            stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
            # Get the SRv6 path
            response = stub.Get(request)
            # Get the status code of the operation
            status = response.status
        except grpc.RpcError as err:
            # An error occurred during the gRPC operation
            # Parse the gRPC error and get the status code
            status = parse_grpc_error(err)
        finally:
            # Raise an exception if an error occurred
            utils.raise_exception_on_error(status)
        # Extract the SRv6 paths from the gRPC response
        srv6_paths = response.paths
    # Return the paths
    return srv6_paths


def change_srv6_path(grpc_address, grpc_port, destination,
                     segments=None, device='', encapmode='encap', table=-1,
                     metric=-1, bsid_addr='', fwd_engine='linux', key=None,
                     update_db=True, db_conn=None, channel=None):
    # In order to add a SRv6 path we need to interact with the node
    # If no gRPC channel has been provided, we need to open a new channel
    # to the node; in this case, grpc_address and grpc_port arguments are
    # required
    if channel is None:
        # Check the arguments
        if grpc_address is None or \
                grpc_address == '' or grpc_port is None or grpc_port == -1:
            logger.error('"change" operation requires a gRPC channel or gRPC '
                         'address/port')
            raise utils.InvalidArgumentError
        channel = utils.get_grpc_session(grpc_address, grpc_port)
    # If segment list not provided, initialize it to an empty list
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
    # Set encapmode
    path.encapmode = text_type(encapmode)
    # Iterate on the segments and build the SID list
    for segment in segments:
        # Append the segment to the SID list
        srv6_segment = path.sr_path.add()
        srv6_segment.segment = text_type(segment)
    # Set the forwarding engine
    try:
        if fwd_engine is not None and fwd_engine != '':
            # Encode fwd engine in a format supported by gRPC
            path_request.fwd_engine = py_to_grpc_fwd_engine(fwd_engine)
        else:
            # By default, if forwarding engine is not specified, we use
            # Linux forwarding engine
            path_request.fwd_engine = FwdEngine.LINUX.value
    except ValueError:
        # An invalid value for fwd_engine has been provided
        logger.error('Invalid forwarding engine: %s', fwd_engine)
        raise utils.InvalidArgumentError
    # Let's update the SRv6 path
    try:
        # Get the reference of the stub
        stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
        # Update the SRv6 path and get the status code
        status = stub.Update(request).status
    except grpc.RpcError as err:
        # An error occurred during the gRPC operation
        # Parse the gRPC error and get the status code
        status = parse_grpc_error(err)
    finally:
        # Raise an exception if an error occurred
        utils.raise_exception_on_error(status)
    # Remove the path from the database
    if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True'] and \
            update_db:
        # Update the path on the db
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


def del_srv6_path(grpc_address, grpc_port, destination,
                  segments=None, device='', encapmode='encap', table=-1,
                  metric=-1, bsid_addr='', fwd_engine='linux', key=None,
                  update_db=True, db_conn=None, channel=None):  # TODO currently channel argument is not used
    # Remove the SRv6 path
    #
    # We need to support two scenarios:
    #  -  Persistency enabled
    #  -  Persistency not enabled
    if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True'] and \
            update_db:
        # Persistency is enabled
        #
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
            raise utils.NoSuchProcessException
    else:
        # Persistency is not enabled
        #
        # The path to be removed is the path specified through the arguments
        srv6_paths = [{
            'destination': destination,
            'device': device,
            'table': table,
            'metric': metric,
            'bsid_addr': bsid_addr,
            'encapmode': encapmode,
            'segments': segments,
            'fwd_engine': fwd_engine,
            '_key': key,
            'grpc_address': grpc_address,
            'grpc_port': grpc_port
        }]
        # Persistency is not enabled, so we don't need to update the database
        update_db = False
    # Let's remove the SRv6 paths
    for srv6_path in srv6_paths:
        # If segment list not provided, initialize it to an empty list
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
        # Set the forwarding engine
        try:
            if fwd_engine is not None and fwd_engine != '':
                # Encode fwd engine in a format supported by gRPC
                path_request.fwd_engine = py_to_grpc_fwd_engine(srv6_path['fwd_engine'])
            else:
                # By default, if forwarding engine is not specified, we use
                # Linux forwarding engine
                path_request.fwd_engine = FwdEngine.LINUX.value
        except ValueError:
            # An invalid value for fwd_engine has been provided
            logger.error('Invalid forwarding engine: %s', fwd_engine)
            raise utils.InvalidArgumentError
        # Set encapmode
        path.encapmode = text_type(srv6_path['encapmode'])
        if len(srv6_path['segments']) == 0:
            logger.error('*** Missing segments for seg6 route')
            raise utils.InvalidArgumentError
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
        try:
            # Get the reference of the stub
            stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
            # Remove the SRv6 path and get the status code
            status = stub.Remove(request).status
        except grpc.RpcError as err:
            # An error occurred during the gRPC operation
            # Parse the gRPC error and get the status code
            status = parse_grpc_error(err)
        finally:
            # Close the channel
            channel.close()
            # Raise an exception if an error occurred
            utils.raise_exception_on_error(status)
        # Remove the path from the db
        if update_db:
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


def handle_srv6_path(operation, grpc_address, grpc_port, destination,
                     segments=None, device='', encapmode="encap", table=-1,
                     metric=-1, bsid_addr='', fwd_engine='linux', key=None,
                     update_db=True, db_conn=None, channel=None):
    """
    Handle a SRv6 Path.
    """
    # Dispatch depending on the operation
    if operation == 'add':
        return add_srv6_path(
            grpc_address=grpc_address,
            grpc_port=grpc_port,
            destination=destination,
            segments=segments,
            device=device,
            encapmode=encapmode,
            table=table,
            metric=metric,
            bsid_addr=bsid_addr,
            fwd_engine=fwd_engine,
            key=key,
            update_db=update_db,
            db_conn=db_conn,
            channel=channel
        )
    if operation == 'get':
        return get_srv6_path(
            grpc_address=grpc_address,
            grpc_port=grpc_port,
            destination=destination,
            segments=segments,
            device=device,
            encapmode=encapmode,
            table=table,
            metric=metric,
            bsid_addr=bsid_addr,
            fwd_engine=fwd_engine,
            key=key,
            update_db=update_db,
            db_conn=db_conn,
            channel=channel
        )
    if operation == 'change':
        return change_srv6_path(
            grpc_address=grpc_address,
            grpc_port=grpc_port,
            destination=destination,
            segments=segments,
            device=device,
            encapmode=encapmode,
            table=table,
            metric=metric,
            bsid_addr=bsid_addr,
            fwd_engine=fwd_engine,
            key=key,
            update_db=update_db,
            db_conn=db_conn,
            channel=channel
        )
    if operation == 'del':
        return del_srv6_path(
            grpc_address=grpc_address,
            grpc_port=grpc_port,
            destination=destination,
            segments=segments,
            device=device,
            encapmode=encapmode,
            table=table,
            metric=metric,
            bsid_addr=bsid_addr,
            fwd_engine=fwd_engine,
            key=key,
            update_db=update_db,
            db_conn=db_conn,
            channel=channel
        )
    # Operation not supported, raise an exception
    logger.error('Operation not supported')
    raise utils.OperationNotSupportedException


def handle_srv6_policy(operation, grpc_address, grpc_port,
                       bsid_addr, segments=None, table=-1, metric=-1,
                       fwd_engine='linux', channel=None):
    """
    Handle a SRv6 Policy.
    """
    # In order to add a SRv6 policy we need to interact with the node
    # If no gRPC channel has been provided, we need to open a new channel
    # to the node; in this case, grpc_address and grpc_port arguments are
    # required
    if channel is None:
        # Check the arguments
        if grpc_address is None or \
                grpc_address == '' or grpc_port is None or grpc_port == -1:
            logger.error('"change" operation requires a gRPC channel or gRPC '
                         'address/port')
            raise utils.InvalidArgumentError
        channel = utils.get_grpc_session(grpc_address, grpc_port)
    # If segment list not provided, initialize it to an empty list
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
    # Iterate on the segments and build the SID list
    for segment in segments:
        # Append the segment to the SID list
        srv6_segment = policy.sr_path.add()
        srv6_segment.segment = text_type(segment)
    # Set the forwarding engine
    try:
        if fwd_engine is not None and fwd_engine != '':
            # Encode fwd engine in a format supported by gRPC
            policy_request.fwd_engine = py_to_grpc_fwd_engine(fwd_engine)
        else:
            # By default, if forwarding engine is not specified, we use
            # Linux forwarding engine
            policy_request.fwd_engine = FwdEngine.LINUX.value
    try:
        # Get the reference of the stub
        stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
        # Fill the request depending on the operation
        # and send the request
        if operation == 'add':
            if len(segments) == 0:
                logger.error('*** Missing segments for seg6 route')
                raise utils.InvalidArgumentError
            # Create the SRv6 path
            response = stub.Create(request)
        elif operation == 'get':
            # Get the SRv6 path
            response = stub.Get(request)
        elif operation == 'change':
            # Update the SRv6 path
            response = stub.Update(request)
        elif operation == 'del':
            # Remove the SRv6 path
            response = stub.Remove(request)
        # Get the status code of the gRPC operation
        status = response.status
    except grpc.RpcError as err:
        # An error occurred during the gRPC operation
        # Parse the error and return it
        status = parse_grpc_error(err)
    finally:
        # Raise an exception if an error occurred
        utils.raise_exception_on_error(status)
    # Extract the SRv6 policies from the gRPC response
    srv6_policies = response.policies
    # Return the response
    return srv6_policies

    
def add_srv6_behavior(grpc_address, grpc_port, segment,
                      action='', device='', table=-1, nexthop="",
                      lookup_table=-1, interface="", segments=None,
                      metric=-1, fwd_engine='linux', key=None,
                      update_db=True, db_conn=None, channel=None):
    # If segment list not provided, initialize it to an empty list
    if segments is None:
        segments = []
    # If database persistency is enabled, we need to check if a SRv6 behavior with
    # the same key already exists
    if key is not None and \
            os.getenv('ENABLE_PERSISTENCY') in ['true', 'True']:
        # Perform a lookup by key into the database
        behaviors = arangodb_driver.find_srv6_behavior(
            database=db_conn,
            key=key
        )
        # Check if we found a behavior with the same key
        if len(behaviors) > 0:
            logger.error('An entity with key %s already exists', key)
            raise utils.InvalidArgumentError
    # All checks passed, we are ready to create the SRv6 behavior
    #
    # In order to add a SRv6 behavior we need to interact with the node
    # If no gRPC channel has been provided, we need to open a new channel
    # to the node; in this case, grpc_address and grpc_port arguments are
    # required
    if channel is None:
        # Check arguments
        if grpc_address is None or \
                grpc_address == '' or grpc_port is None or grpc_port == -1:
            logger.error('"add" operation requires a gRPC channel or gRPC '
                         'address/port')
            raise utils.InvalidArgumentError
        # Establish a gRPC channel to the destination
        channel = utils.get_grpc_session(grpc_address, grpc_port)
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
    # Set the SRv6 action
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
    # Set the forwarding engine
    try:
        if fwd_engine is not None and fwd_engine != '':
            # Encode fwd engine in a format supported by gRPC
            path_request.fwd_engine = py_to_grpc_fwd_engine(fwd_engine)
        else:
            # By default, if forwarding engine is not specified, we use
            # Linux forwarding engine
            path_request.fwd_engine = FwdEngine.LINUX.value
    # Set the forwarding engine
    try:
        if fwd_engine is not None and fwd_engine != '':
            # Encode fwd engine in a format supported by gRPC
            path_request.fwd_engine = py_to_grpc_fwd_engine(fwd_engine)
        else:
            # By default, if forwarding engine is not specified, we use
            # Linux forwarding engine
            path_request.fwd_engine = FwdEngine.LINUX.value
    except ValueError:
        # An invalid value for fwd_engine has been provided
        logger.error('Invalid forwarding engine: %s', fwd_engine)
        raise utils.InvalidArgumentError
    # Let's create the SRv6 path
    try:
        # Get the reference of the stub
        stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
        # Create the SRv6 behavior and get the status code
        status = stub.Create(request).status
    except grpc.RpcError as err:
        # An error occurred during the gRPC operation
        # Parse the gRPC error and get the status code
        status = parse_grpc_error(err)
    finally:
        # Raise an exception if an error occurred
        utils.raise_exception_on_error(status)
    # If the persistecy is enable, store the behavior to the database
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

    
def get_srv6_behavior(grpc_address, grpc_port, segment,
                      action='', device='', table=-1, nexthop="",
                      lookup_table=-1, interface="", segments=None,
                      metric=-1, fwd_engine='linux', key=None,
                      update_db=True, db_conn=None, channel=None):
    # If segment list not provided, initialize it to an empty list
    if segments is None:
        segments = []
    # We need to support two scenarios:
    #  -  Persistency enabled
    #  -  Persistency not enabled
    if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True']:
        # Persistency is enabled
        #
        # Perform a lookup in the database and store the SRv6 behaviors found
        srv6_behaviors = arangodb_driver.find_srv6_behavior(
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
        # Persistency is not enabled
        #
        # We need to interact with the node to retrieve the SRv6 behaviors
        try:
            # In order to get a SRv6 behavior we need to interact with the node
            # If no gRPC channel has been provided, we need to open a new channel
            # to the node; in this case, grpc_address and grpc_port arguments are
            # required
            if channel is None:
                if grpc_address is None or \
                        grpc_address == '' or grpc_port is None or grpc_port == -1:
                    logger.error('"get" operation requires a gRPC channel or gRPC '
                                'address/port')
                    raise utils.InvalidArgumentError
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
            # Set the forwarding engine
            try:
                if fwd_engine is not None and fwd_engine != '':
                    # Encode fwd engine in a format supported by gRPC
                    behavior_request.fwd_engine = py_to_grpc_fwd_engine(fwd_engine)
                else:
                    # By default, if forwarding engine is not specified, we use
                    # Linux forwarding engine
                    behavior_request.fwd_engine = FwdEngine.LINUX.value
            except ValueError:
                # An invalid value for fwd_engine has been provided
                logger.error('Invalid forwarding engine: %s', fwd_engine)
                raise utils.InvalidArgumentError
            # Get the reference of the stub
            stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
            # Get the SRv6 behavior
            response = stub.Get(request)
            # Get the status code of the operation
            status = response.status
        except grpc.RpcError as err:
            # An error occurred during the gRPC operation
            # Parse the gRPC error and get the status code
            status = parse_grpc_error(err)
        finally:
            # Raise an exception if an error occurred
            utils.raise_exception_on_error(status)
        # Extract the SRv6 behaviors from the gRPC response
        srv6_behaviors = response.behaviors
    # Return the behaviors
    return srv6_behaviors


def change_srv6_behavior(grpc_address, grpc_port, segment,
                         action='', device='', table=-1, nexthop="",
                         lookup_table=-1, interface="", segments=None,
                         metric=-1, fwd_engine='linux', key=None,
                         update_db=True, db_conn=None, channel=None):
    # In order to add a SRv6 behavior we need to interact with the node
    # If no gRPC channel has been provided, we need to open a new channel
    # to the node; in this case, grpc_address and grpc_port arguments are
    # required
    if channel is None:
        # Check the arguments
        if grpc_address is None or \
                grpc_address == '' or grpc_port is None or grpc_port == -1:
            logger.error('"change" operation requires a gRPC channel or gRPC '
                         'address/port')
            raise utils.InvalidArgumentError
        channel = utils.get_grpc_session(grpc_address, grpc_port)
    # If segment list not provided, initialize it to an empty list
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
    # Set the forwarding engine
    try:
        if fwd_engine is not None and fwd_engine != '':
            # Encode fwd engine in a format supported by gRPC
            behavior_request.fwd_engine = py_to_grpc_fwd_engine(fwd_engine)
        else:
            # By default, if forwarding engine is not specified, we use
            # Linux forwarding engine
            behavior_request.fwd_engine = FwdEngine.LINUX.value
    except ValueError:
        # An invalid value for fwd_engine has been provided
        logger.error('Invalid forwarding engine: %s', fwd_engine)
        raise utils.InvalidArgumentError
    # Let's update the SRv6 behavior
    try:
        # Get the reference of the stub
        stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
        # Update the SRv6 behavior and get the status code
        status = stub.Update(request).status
    except grpc.RpcError as err:
        # An error occurred during the gRPC operation
        # Parse the gRPC error and get the status code
        status = parse_grpc_error(err)
    finally:
        # Raise an exception if an error occurred
        utils.raise_exception_on_error(status)
    # Remove the behavior from the database
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


def del_srv6_behavior(grpc_address, grpc_port, segment,
                      action='', device='', table=-1, nexthop="",
                      lookup_table=-1, interface="", segments=None,
                      metric=-1, fwd_engine='linux', key=None,
                      update_db=True, db_conn=None, channel=None):
    # Remove the SRv6 behavior
    #
    # We need to support two scenarios:
    #  -  Persistency enabled
    #  -  Persistency not enabled
    if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True'] and \
            update_db:
        # Persistency is enabled
        #
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
            raise utils.NoSuchProcessException
    else:
        # Persistency is not enabled
        #
        # The behavior to be removed is the behavior specified through the arguments
        srv6_behaviors = [{
            '_key': key,
            'grpc_address': grpc_address,
            'grpc_port': grpc_port,
            'segment': segment,
            'action': action,
            'device': device,
            'table': table,
            'nexthop': nexthop,
            'lookup_table': lookup_table,
            'interface': interface,
            'segments': segments,
            'metric': metric,
            'fwd_engine': fwd_engine,
        }]
        # Persistency is not enabled, so we don't need to update the database
        update_db = False
    # Let's remove the SRv6 behaviors
    for srv6_behavior in srv6_behaviors:
        # If segment list not provided, initialize it to an empty list
        if srv6_behavior['segments'] is None:
            segments = []
        # Create request message
        request = srv6_manager_pb2.SRv6ManagerRequest()
        # Create a new SRv6 behavior request
        behavior_request = (request               # pylint: disable=no-member
                            .srv6_behavior_request)
        # Create a new SRv6 behavior
        behavior = behavior_request.behaviors.add()
        # Set local segment for the seg6local route
        behavior.segment = text_type(srv6_path['segment'])
        # Set the device
        # If the device is not specified (i.e. empty string),
        # it will be chosen by the gRPC server
        behavior.device = text_type(srv6_path['device'])
        # Set the table where the seg6local must be inserted
        # If the table ID is not specified (i.e. table=-1),
        # the main table will be used
        behavior.table = int(srv6_path['table'])
        # Set device
        # If the device is not specified (i.e. empty string),
        # it will be chosen by the gRPC server
        behavior.device = text_type(srv6_path['device'])
        # Set metric (i.e. preference value of the route)
        # If the metric is not specified (i.e. metric=-1),
        # the decision is left to the Linux kernel
        behavior.metric = int(srv6_path['metric'])
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
        # Set the forwarding engine
        try:
            if fwd_engine is not None and fwd_engine != '':
                # Encode fwd engine in a format supported by gRPC
                behavior_request.fwd_engine = py_to_grpc_fwd_engine(srv6_path['fwd_engine'])
            else:
                # By default, if forwarding engine is not specified, we use
                # Linux forwarding engine
                behavior_request.fwd_engine = FwdEngine.LINUX.value
        except ValueError:
            # An invalid value for fwd_engine has been provided
            logger.error('Invalid forwarding engine: %s', fwd_engine)
            raise utils.InvalidArgumentError
        # Get gRPC channel
        channel = utils.get_grpc_session(
            server_ip=srv6_path['grpc_address'],
            server_port=srv6_path['grpc_port']
        )
        try:
            # Get the reference of the stub
            stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
            # Remove the SRv6 behavior and get the status code
            status = stub.Remove(request).status
        except grpc.RpcError as err:
            # An error occurred during the gRPC operation
            # Parse the gRPC error and get the status code
            status = parse_grpc_error(err)
        finally:
            # Close the channel
            channel.close()
            # Raise an exception if an error occurred
            utils.raise_exception_on_error(status)
        # Remove the path from the db
        if update_db:
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
            

def handle_srv6_behavior(operation, grpc_address, grpc_port, segment,
                         action='', device='', table=-1, nexthop="",
                         lookup_table=-1, interface="", segments=None,
                         metric=-1, fwd_engine='linux', key=None,
                         update_db=True, db_conn=None, channel=None):
    """
    Handle a SRv6 behavior.
    """
    # Dispatch depending on the operation
    if operation == 'add':
        return add_srv6_behavior(
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
            key=key,
            update_db=update_db,
            db_conn=db_conn,
            channel=channel
        )
    if operation == 'get':
        return get_srv6_behavior(
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
            key=key,
            update_db=update_db,
            db_conn=db_conn,
            channel=channel
        )
    if operation == 'change':
        return change_srv6_behavior(
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
            key=key,
            update_db=update_db,
            db_conn=db_conn,
            channel=channel
        )
    if operation == 'del':
        return del_srv6_behavior(
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
            key=key,
            update_db=update_db,
            db_conn=db_conn,
            channel=channel
        )
    # Operation not supported, raise an exception
    logger.error('Operation not supported')
    raise utils.OperationNotSupportedException


class SRv6Exception(Exception):
    """
    Generic SRv6 Exception.
    """


def create_uni_srv6_tunnel(ingress_ip, ingress_port, egress_ip, egress_port,
                           destination, segments, localseg=None,
                           bsid_addr='', fwd_engine='linux', key=None,
                           update_db=True, db_conn=None,
                           ingress_channel=None, egress_channel=None):
    """
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
    """
    # pylint: disable=too-many-arguments
    #
    # If database persistency is enabled, we need to check if a SRv6 tunnel
    # with the same key already exists
    if key is not None and \
            os.getenv('ENABLE_PERSISTENCY') in ['true', 'True']:
        # Perform a lookup by key into the database
        tunnels = arangodb_driver.find_srv6_tunnel(
            database=db_conn,
            key=key
        )
        # Check if we found a tunnel with the same key
        if len(tunnels) > 0:
            logger.error('An entity with key %s already exists', key)
            raise utils.InvalidArgumentError
    # Establish a gRPC channel, if no channel has been provided
    if ingress_channel is None:
        # Check arguments
        if ingress_ip is None or ingress_ip == '' or \
                ingress_port is None or ingress_port == -1:
            logger.error('"add" operation requires a gRPC channel or gRPC '
                         'address/port')
            raise utils.InvalidArgumentError
        # Establish a gRPC channel to the destination
        ingress_channel = utils.get_grpc_session(ingress_ip, ingress_port)
    if egress_channel is None:
        # Check arguments
        if egress_ip is None or \
                egress_ip == '' or egress_port is None or egress_port == -1:
            logger.error('"add" operation requires a gRPC channel or gRPC '
                         'address/port')
            raise utils.InvalidArgumentError
        # Establish a gRPC channel to the destination
        egress_channel = utils.get_grpc_session(egress_ip, egress_port)
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
    # If the persistecy is enable, store the tunnel to the database
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


def create_srv6_tunnel(node_l_ip, node_l_port, node_r_ip, node_r_port,
                       sidlist_lr, sidlist_rl, dest_lr, dest_rl,
                       localseg_lr=None, localseg_rl=None,
                       bsid_addr='', fwd_engine='linux', update_db=True,
                       key=None, db_conn=None,
                       node_l_channel=None, node_r_channel=None):
    """
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
    """
    # pylint: disable=too-many-arguments
    #
    # If database persistency is enabled, we need to check if a SRv6 tunnel
    # with the same key already exists
    if key is not None and \
            os.getenv('ENABLE_PERSISTENCY') in ['true', 'True']:
        # Perform a lookup by key into the database
        tunnels = arangodb_driver.find_srv6_tunnel(
            database=db_conn,
            key=key
        )
        # Check if we found a tunnel with the same key
        if len(tunnels) > 0:
            logger.error('An entity with key %s already exists', key)
            raise utils.InvalidArgumentError
    # Establish a gRPC channel, if no channel has been provided
    if node_l_channel is None:
        # Check arguments
        if node_l_ip is None or \
                node_l_ip == '' or node_l_port is None or node_l_port == -1:
            logger.error('"add" operation requires a gRPC channel or gRPC '
                         'address/port')
            raise utils.InvalidArgumentError
        # Establish a gRPC channel to the destination
        node_l_channel = utils.get_grpc_session(node_l_ip, node_l_port)
    if node_r_channel is None:
        # Check arguments
        if node_r_ip is None or \
                node_r_ip == '' or node_r_port is None or node_r_port == -1:
            logger.error('"add" operation requires a gRPC channel or gRPC '
                         'address/port')
            raise utils.InvalidArgumentError
        node_r_channel = utils.get_grpc_session(node_r_ip, node_r_port)
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
    # If the persistecy is enable, store the tunnel to the database
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


def destroy_uni_srv6_tunnel(ingress_ip, ingress_port, egress_ip, egress_port,
                            destination, localseg=None, bsid_addr='',
                            fwd_engine='linux', ignore_errors=False, key=None,
                            update_db=True, db_conn=None,
                            ingress_channel=None, egress_channel=None):
    """
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
    """
    # pylint: disable=too-many-arguments
    #
    # We need to support two scenarios:
    #  -  Persistency enabled
    #  -  Persistency not enabled
    if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True'] and update_db:
        # Persistency is enabled
        #
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
            raise utils.NoSuchProcessException
    else:
        # Persistency is not enabled
        #
        # The tunnel to be removed is the tunnel specified through the arguments
        srv6_tunnels = [{
            '_key': key,
            'l_grpc_address': utils.grpc_chan_to_addr_port(node_l_channel)[0],
            'l_grpc_port': utils.grpc_chan_to_addr_port(node_l_channel)[1],
            'r_grpc_address': utils.grpc_chan_to_addr_port(node_r_channel)[0],
            'r_grpc_port': utils.grpc_chan_to_addr_port(node_r_channel)[1],
            'sidlist_lr': None,
            'sidlist_rl': None,
            'dest_lr': dest_lr,
            'dest_rl': dest_rl,
            'localseg_lr': localseg_lr,
            'localseg_rl': localseg_rl,
            'bsid_addr': bsid_addr,
            'fwd_engine': fwd_engine,
            'is_unidirectional': True
        }]
        # Persistency is not enabled, so we don't need to update the database
        update_db = False
    # Let's remove the SRv6 tunnels
    for srv6_tunnel in srv6_tunnels: 
        # Establish a gRPC channel, if no channel has been provided
        if ingress_channel is None:
            # Check arguments
            if ingress_ip is None or \
                    ingress_ip == '' or ingress_port is None or ingress_port == -1:
                logger.error('"add" operation requires a gRPC channel or gRPC '
                            'address/port')
                raise utils.InvalidArgumentError
            # Establish a gRPC channel to the destination
            ingress_channel = utils.get_grpc_session(ingress_ip, ingress_port)
        if egress_channel is None:
            # Check arguments
            if egress_ip is None or \
                    egress_ip == '' or egress_port is None or egress_port == -1:
                logger.error('"add" operation requires a gRPC channel or gRPC '
                            'address/port')
                raise utils.InvalidArgumentError
            # Establish a gRPC channel to the destination
            egress_channel = utils.get_grpc_session(egress_ip, egress_port)
        # Remove seg6 route from <ingress> to steer the packets sent to
        # <destination> through the SID list <segments>
        #
        # Equivalent to the command:
        #    ingress: ip -6 route del <destination> encap seg6 mode encap \
        #             segs <segments> dev <device>
        try:
            handle_srv6_path(
                operation='del',
                channel=ingress_channel,
                destination=srv6_tunnel['dest_lr'],
                bsid_addr=srv6_tunnel['bsid_addr'],
                fwd_engine=srv6_tunnel['fwd_engine'],
                update_db=False,
                db_conn=db_conn
            )
        except utils.NoSuchProcessException:
            # If an error occurred, abort the operation
            # If the 'ignore_errors' flag is set, continue
            if not ignore_errors:
                pass
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
            try:
                handle_srv6_behavior(
                    operation='del',
                    channel=egress_channel,
                    segment=localseg,
                    fwd_engine=fwd_engine,
                    update_db=False,
                    db_conn=db_conn
                )
            except utils.NoSuchProcessException:
                # If an error occurred, abort the operation
                # If the 'ignore_errors' flag is set, continue
                if not ignore_errors:
                    pass
        # Remove the tunnel from the db
        if update_db:
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


def destroy_srv6_tunnel(node_l_ip, node_l_port, node_r_ip, node_r_port,
                        dest_lr, dest_rl, localseg_lr=None, localseg_rl=None,
                        bsid_addr='', fwd_engine='linux',
                        ignore_errors=False, key=None, update_db=True,
                        db_conn=None, node_l_channel=None,
                        node_r_channel=None):
    """
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
    """
    # pylint: disable=too-many-arguments
    #
    # Remove the SRv6 behavior
    #
    # We need to support two scenarios:
    #  -  Persistency enabled
    #  -  Persistency not enabled
    if os.getenv('ENABLE_PERSISTENCY') in ['true', 'True'] and \
            update_db:
        # Persistency is enabled
        #
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
            raise utils.NoSuchProcessException
    else:
        # Persistency is not enabled
        #
        # The tunnel to be removed is the tunnel specified through the arguments
        srv6_tunnels = [{
            '_key': key,
            'l_grpc_address': utils.grpc_chan_to_addr_port(node_l_channel)[0],
            'l_grpc_port': utils.grpc_chan_to_addr_port(node_l_channel)[1],
            'r_grpc_address': utils.grpc_chan_to_addr_port(node_r_channel)[0],
            'r_grpc_port': utils.grpc_chan_to_addr_port(node_r_channel)[1],
            'sidlist_lr': None,
            'sidlist_rl': None,
            'dest_lr': dest_lr,
            'dest_rl': dest_rl,
            'localseg_lr': localseg_lr,
            'localseg_rl': localseg_rl,
            'bsid_addr': bsid_addr,
            'fwd_engine': fwd_engine,
            'is_unidirectional': False
        }]
        # Persistency is not enabled, so we don't need to update the database
        update_db = False
    # Let's remove the SRv6 tunnels
    for srv6_tunnel in srv6_tunnels:
        # Establish a gRPC channel, if no channel has been provided
        if node_l_channel is None:
            # Check arguments
            if node_l_ip is None or \
                    node_l_ip == '' or node_l_port is None or node_l_port == -1:
                logger.error('"add" operation requires a gRPC channel or gRPC '
                            'address/port')
                raise utils.InvalidArgumentError
            # Establish a gRPC channel to the destination
            node_l_channel = utils.get_grpc_session(node_l_ip, node_l_port)
        if node_r_channel is None:
            # Check arguments
            if node_r_ip is None or \
                    node_r_ip == '' or node_r_port is None or node_r_port == -1:
                logger.error('"add" operation requires a gRPC channel or gRPC '
                            'address/port')
                raise utils.InvalidArgumentError
            # Establish a gRPC channel to the destination
            node_r_channel = utils.get_grpc_session(node_r_ip, node_r_port)
        # Remove unidirectional SRv6 tunnel from <node_l> to <node_r>
        destroy_uni_srv6_tunnel(
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
        # Remove unidirectional SRv6 tunnel from <node_r> to <node_l>
        destroy_uni_srv6_tunnel(
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
        # Remove the tunnel from the db
        if update_db:
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


def get_uni_srv6_tunnel(ingress_ip, ingress_port, egress_ip, egress_port,
                        destination, segments, localseg=None,
                        bsid_addr='', fwd_engine='linux', key=None,
                        db_conn=None, ingress_channel=None,
                        egress_channel=None):
    """
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
    """
    # pylint: disable=too-many-arguments
    #
    # This function requires persistency enabled
    if os.getenv('ENABLE_PERSISTENCY') not in ['true', 'True']:
        logger.error('Get tunnel requires ENABLE_PERSISTENCY')
        raise utils.InvalidArgumentError
    # Retrieve the tunnel from the database
    return arangodb_driver.find_srv6_tunnel(
        database=db_conn,
        key=key if key != '' else None,
        l_grpc_address=ingress_ip,
        l_grpc_port=ingress_port,
        r_grpc_address=egress_ip,
        r_grpc_port=egress_port
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


def get_srv6_tunnel(node_l_ip, node_l_port, node_r_ip, node_r_port,
                       sidlist_lr, sidlist_rl, dest_lr, dest_rl,
                       localseg_lr=None, localseg_rl=None,
                       bsid_addr='', fwd_engine='linux', update_db=True,
                       key=None, db_conn=None, node_l_channel=None,
                       node_r_channel=None):
    """
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
    """
    # pylint: disable=too-many-arguments
    #
    # This function requires persistency enabled
    if os.getenv('ENABLE_PERSISTENCY') not in ['true', 'True']:
        logger.error('Get tunnel requires ENABLE_PERSISTENCY')
        raise utils.InvalidArgumentError
    # Retrieve the tunnel from the database
    return arangodb_driver.find_srv6_tunnel(
        database=db_conn,
        key=key if key != '' else None,
        l_grpc_address=node_l_ip,
        l_grpc_port=node_l_port,
        r_grpc_address=node_r_ip,
        r_grpc_port=node_r_port,
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

# TODO close gRPC channel after the execution
