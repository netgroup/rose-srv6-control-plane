#!/usr/bin/python

##############################################################################################
# Copyright (C) 2020 Carmine Scarpitta - (Consortium GARR and University of Rome "Tor Vergata")
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


import os

# Activate virtual environment if a venv path has been specified in .venv
# This must be executed only if this file has been executed as a
# script (instead of a module)
if __name__ == '__main__':
    # Check if .venv file exists
    if os.path.exists('.venv'):
        with open('.venv', 'r') as venv_file:
            # Get virtualenv path from .venv file
            venv_path = venv_file.read()
        # Get path of the activation script
        venv_path = os.path.join(venv_path, 'bin/activate_this.py')
        if not os.path.exists(venv_path):
            print('Virtual environment path specified in .venv '
                  'points to an invalid path\n')
            exit(-2)
        with open(venv_path) as f:
            # Read the activation script
            code = compile(f.read(), venv_path, 'exec')
            # Execute the activation script to activate the venv
            exec(code, {'__file__': venv_path})

# General imports
from six import text_type
from dotenv import load_dotenv
import grpc
import logging
import sys

# Load environment variables from .env file
load_dotenv()

# Folder containing this script
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

# Folder containing the files auto-generated from proto files
PROTO_PATH = os.path.join(BASE_PATH, '../protos/gen-py/')

# Environment variables have priority over hardcoded paths
# If an environment variable is set, we must use it instead of
# the hardcoded constant
if os.getenv('PROTO_PATH') is not None:
    # Check if the PROTO_PATH variable is set
    if os.getenv('PROTO_PATH') == '':
        print('Error : Set PROTO_PATH variable in .env\n')
        sys.exit(-2)
    # Check if the PROTO_PATH variable points to an existing folder
    if not os.path.exists(os.getenv('PROTO_PATH')):
        print('Error : PROTO_PATH variable in '
              '.env points to a non existing folder')
        sys.exit(-2)
    # PROTO_PATH in .env is correct. We use it.
    PROTO_PATH = os.getenv('PROTO_PATH')
else:
    # PROTO_PATH in .env is not set, we use the hardcoded path
    #
    # Check if the PROTO_PATH variable is set
    if PROTO_PATH == '':
        print('Error : Set PROTO_PATH variable in .env or %s' % sys.argv[0])
        sys.exit(-2)
    # Check if the PROTO_PATH variable points to an existing folder
    if not os.path.exists(PROTO_PATH):
        print('Error : PROTO_PATH variable in '
              '%s points to a non existing folder' % sys.argv[0])
        print('Error : Set PROTO_PATH variable in .env or %s\n' % sys.argv[0])
        sys.exit(-2)

# Proto dependencies
sys.path.append(PROTO_PATH)
import commons_pb2
import srv6_manager_pb2
import srv6_manager_pb2_grpc

import utils

# Global variables definition
#
#
# ArangoDB default parameters
ARANGO_USER = 'root'
ARANGO_PASSWORD = '12345678'
ARANGO_URL = 'http://localhost:8529'
# Environment variables have priority over hardcoded paths
# If an environment variable is set, we must use it instead of
# the hardcoded constant
ARANGO_USER = os.getenv('ARANGO_USER', default=ARANGO_USER)
ARANGO_PASSWORD = os.getenv('ARANGO_PASSWORD', default=ARANGO_PASSWORD)
ARANGO_URL = os.getenv('ARANGO_URL', default=ARANGO_URL)
# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)
# Default parameters for SRv6 controller
#
# Port of the gRPC server
GRPC_PORT = 12345
# Define whether to use SSL or not for the gRPC client
SECURE = False
# SSL certificate of the root CA
CERTIFICATE = 'client_cert.pem'
# Default ISIS port
DEFAULT_ISIS_PORT = 2608


# Parser for gRPC errors
def parse_grpc_error(e):
    status_code = e.code()
    details = e.details()
    logger.error('gRPC client reported an error: %s, %s'
                 % (status_code, details))
    if grpc.StatusCode.UNAVAILABLE == status_code:
        code = commons_pb2.STATUS_GRPC_SERVICE_UNAVAILABLE
    elif grpc.StatusCode.UNAUTHENTICATED == status_code:
        code = commons_pb2.STATUS_GRPC_UNAUTHORIZED
    else:
        code = commons_pb2.STATUS_INTERNAL_ERROR
    # Return an error message
    return code


def handle_srv6_path(op, channel, destination, segments=[],
                     device='', encapmode="encap", table=-1, metric=-1):
    # Create request message
    request = srv6_manager_pb2.SRv6ManagerRequest()
    # Create a new SRv6 path request
    path_request = request.srv6_path_request
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
        if op == 'add':
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
        elif op == 'get':
            # Get the SRv6 path
            response = stub.Get(request)
        elif op == 'change':
            # Set encapmode
            path.encapmode = text_type(encapmode)
            # Iterate on the segments and build the SID list
            for segment in segments:
                # Append the segment to the SID list
                srv6_segment = path.sr_path.add()
                srv6_segment.segment = text_type(segment)
            # Update the SRv6 path
            response = stub.Update(request)
        elif op == 'del':
            # Remove the SRv6 path
            response = stub.Remove(request)
        # Get the status code of the gRPC operation
        response = response.status
    except grpc.RpcError as e:
        # An error occurred during the gRPC operation
        # Parse the error and return it
        response = parse_grpc_error(e)
    # Return the response
    return response


def handle_srv6_behavior(op, channel, segment, action='', device='',
                         table=-1, nexthop="", lookup_table=-1,
                         interface="", segments=[], metric=-1):
    # Create request message
    request = srv6_manager_pb2.SRv6ManagerRequest()
    # Create a new SRv6 behavior request
    behavior_request = request.srv6_behavior_request
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
        if op == 'add':
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
            for segment in segments:
                # Create a new segment
                srv6_segment = behavior.segs.add()
                srv6_segment.segment = text_type(segment)
            # Create the SRv6 behavior
            response = stub.Create(request)
        elif op == 'get':
            # Get the SRv6 behavior
            response = stub.Get(request)
        elif op == 'change':
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
            for segment in segments:
                # Create a new segment
                srv6_segment = behavior.segs.add()
                srv6_segment.segment = text_type(segment)
            # Update the SRv6 behavior
            response = stub.Update(request)
        elif op == 'del':
            # Remove the SRv6 behavior
            response = stub.Remove(request)
        else:
            logger.error('Invalid operation: %s' % op)
            return None
        # Get the status code of the gRPC operation
        response = response.status
    except grpc.RpcError as e:
        # An error occurred during the gRPC operation
        # Parse the error and return it
        response = parse_grpc_error(e)
    # Return the response
    return response


def __create_uni_srv6_tunnel(ingress_channel, egress_channel,
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
        op='add',
        channel=ingress_channel,
        destination=destination,
        segments=segments
    )
    # Pretty print status code
    utils.__print_status_message(
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
            op='add',
            channel=egress_channel,
            segment=localseg,
            action='End.DT6',
            lookup_table=254
        )
        # Pretty print status code
        utils.__print_status_message(
            status_code=res,
            success_msg='Added SRv6 Behavior',
            failure_msg='Error in add_srv6_behavior()'
        )
        # If an error occurred, abort the operation
        if res != commons_pb2.STATUS_SUCCESS:
            return res
    # Success
    return commons_pb2.STATUS_SUCCESS


def __create_srv6_tunnel(node_l_channel, node_r_channel,
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

    # Create a unidirectional SRv6 tunnel from <node_l> to <node_r>
    res = __create_uni_srv6_tunnel(
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
    res = __create_uni_srv6_tunnel(
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


def __destroy_uni_srv6_tunnel(ingress_channel, egress_channel, destination,
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
        op='del',
        channel=ingress_channel,
        destination=destination
    )
    # Pretty print status code
    utils.__print_status_message(
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
            op='del',
            channel=egress_channel,
            segment=localseg
        )
        # Pretty print status code
        utils.__print_status_message(
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


def __destroy_srv6_tunnel(node_l_channel, node_r_channel,
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

    # Remove unidirectional SRv6 tunnel from <node_l> to <node_r>
    res = __destroy_uni_srv6_tunnel(
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
    res = __destroy_uni_srv6_tunnel(
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
