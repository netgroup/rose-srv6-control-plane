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
# Implementation of SRv6 Manager
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


# General imports
import os
import sys
import logging
import time
from concurrent import futures
from argparse import ArgumentParser
from socket import AF_INET, AF_INET6

# pyroute2 dependencies
from pyroute2.netlink.rtnl.ifinfmsg import IFF_LOOPBACK
from pyroute2.netlink.exceptions import NetlinkError
from pyroute2 import IPRoute

# gRPC dependencies
import grpc

# Proto dependencies
import srv6_manager_pb2
import srv6_manager_pb2_grpc

# Node manager dependencies
from node_manager.utils import get_address_family

# Proto commons dependencies
import commons_pb2

# General imports
# pyroute2 dependencies

# Load environment variables from .env file
# load_dotenv()

# Folder containing this script
BASE_PATH = os.path.dirname(os.path.realpath(__file__))


# Global variables definition
#
#
# Netlink error codes
NETLINK_ERROR_NO_SUCH_PROCESS = 3
NETLINK_ERROR_FILE_EXISTS = 17
NETLINK_ERROR_NO_SUCH_DEVICE = 19
NETLINK_ERROR_OPERATION_NOT_SUPPORTED = 95
# Logger reference
logger = logging.getLogger(__name__)
#
# Default parameters for SRv6 manager
#
# Server ip and port
DEFAULT_GRPC_IP = '::'
DEFAULT_GRPC_PORT = 12345
# Debug option
SERVER_DEBUG = False
# Secure option
DEFAULT_SECURE = False
# Server certificate
DEFAULT_CERTIFICATE = 'cert_server.pem'
# Server key
DEFAULT_KEY = 'key_server.pem'


def parse_netlink_error(self, err):
    if err.code == NETLINK_ERROR_FILE_EXISTS:
        logger.warning('Netlink error: File exists')
        return commons_pb2.STATUS_FILE_EXISTS
    elif err.code == NETLINK_ERROR_NO_SUCH_PROCESS:
        logger.warning('Netlink error: No such process')
        return commons_pb2.STATUS_NO_SUCH_PROCESS
    elif err.code == NETLINK_ERROR_NO_SUCH_DEVICE:
        logger.warning('Netlink error: No such device')
        return commons_pb2.STATUS_NO_SUCH_DEVICE
    elif err.code == NETLINK_ERROR_OPERATION_NOT_SUPPORTED:
        logger.warning('Netlink error: Operation not supported')
        return commons_pb2.STATUS_OPERATION_NOT_SUPPORTED
    else:
        logger.warning(f'Generic internal error: {err}')
        srv6_manager_pb2.STATUS_INTERNAL_ERROR


class SRv6Manager(srv6_manager_pb2_grpc.SRv6ManagerServicer):
    """gRPC request handler"""

    def __init__(self):
        # Setup ip route
        self.ip_route = IPRoute()
        # Non-loopback interfaces
        self.non_loopback_interfaces = list()
        # Loopback interfaces
        self.loopback_interfaces = list()
        # Mapping interface name to interface index
        self.interface_to_idx = dict()
        # Resolve the interfaces
        for link in self.ip_route.get_links():
            # Check the IFF_LOOPBACK flag of the interfaces
            # and make separation between loopback interfaces and
            # non-loopback interfaces
            if not link.get('flags') & IFF_LOOPBACK == 0:
                self.loopback_interfaces.append(
                    link.get_attr('IFLA_IFNAME'))
            else:
                self.non_loopback_interfaces.append(
                    link.get_attr('IFLA_IFNAME'))
        # Build mapping interface to index
        interfaces = self.loopback_interfaces + self.non_loopback_interfaces
        # Iterate on the interfaces
        for interface in interfaces:
            # Add interface index
            self.interface_to_idx[interface] = \
                self.ip_route.link_lookup(ifname=interface)[0]

    def HandleSRv6PathRequest(self, operation, request, context):
        logger.debug(f'config received:\n{request}')
        # Perform operation
        try:
            if operation in ['add', 'change', 'del']:
                # Let's push the routes
                for path in request.paths:
                    # Rebuild segments
                    segments = []
                    for srv6_segment in path.sr_path:
                        segments.append(srv6_segment.segment)
                    segments.reverse()
                    table = path.table
                    if path.table == -1:
                        table = None
                    metric = path.metric
                    if path.metric == -1:
                        metric = None
                    if segments == []:
                        segments = ['::']
                    oif = None
                    if path.device != '':
                        oif = self.interface_to_idx[path.device]
                    elif operation == 'add':
                        oif = self.interface_to_idx[
                            self.non_loopback_interfaces[0]]
                    self.ip_route.route(operation, dst=path.destination,
                                        oif=oif,
                                        table=table,
                                        priority=metric,
                                        encap={'type': 'seg6',
                                               'mode': path.encapmode,
                                               'segs': segments})
            elif operation == 'get':
                return srv6_manager_pb2.SRv6ManagerReply(
                    status=commons_pb2.STATUS_OPERATION_NOT_SUPPORTED)
            else:
                # Operation unknown: this is a bug
                logger.error(f'Unrecognized operation: {operation}')
                sys.exit(-1)
            # and create the response
            logger.debug('Send response: OK')
            return srv6_manager_pb2.SRv6ManagerReply(
                status=commons_pb2.STATUS_SUCCESS)
        except NetlinkError as err:
            return srv6_manager_pb2.SRv6ManagerReply(
                status=self.parse_netlink_error(err))

    def HandleSRv6BehaviorRequest(self, operation, request, context):
        logger.debug(f'config received:\n{request}')
        # Let's process the request
        try:
            for behavior in request.behaviors:
                # Extract params from request
                segment = behavior.segment
                action = behavior.action
                nexthop = behavior.nexthop
                lookup_table = behavior.lookup_table
                interface = behavior.interface
                device = behavior.device
                table = behavior.table
                metric = behavior.metric
                # Check optional params
                nexthop = nexthop if nexthop != '' else None
                lookup_table = lookup_table if lookup_table != -1 else None
                interface = interface if interface != '' else None
                device = device if device != '' \
                    else self.non_loopback_interfaces[0]
                table = table if table != -1 else None
                metric = metric if metric != -1 else None
                # Perform operation
                if operation == 'del':
                    # Delete a route
                    self.ip_route.route(operation, family=AF_INET6,
                                        dst=segment,
                                        table=table, priority=metric)
                elif operation == 'get':
                    return srv6_manager_pb2.SRv6ManagerReply(
                        status=commons_pb2.STATUS_OPERATION_NOT_SUPPORTED)
                elif operation in ['add', 'change']:
                    # Add a new route
                    # Fill encap dict with the parameters of the behavior
                    if action == 'End':
                        encap = {}
                    elif action == 'End.X':
                        encap = {'nh6': nexthop}
                    elif action == 'End.T':
                        encap = {'table': lookup_table}
                    elif action == 'End.DX2':
                        encap = {'oif': interface}
                    elif action == 'End.DX6':
                        encap = {'nh6': nexthop}
                    elif action == 'End.DX4':
                        encap = {'nh4': nexthop}
                    elif action == 'End.DT6':
                        encap = {'table': lookup_table}
                    elif action == 'End.DT4':
                        encap = {'table': lookup_table}
                    elif action == 'End.B6':
                        # Rebuild segments
                        segments = []
                        for srv6_segment in behavior.segs:
                            segments.append(srv6_segment.segment)
                        # pyroute2 requires the segments in reverse order
                        segments.reverse()
                        # Parameters of End.B6 behavior
                        encap = {'srh': {'segs': segments}}
                    elif action == 'End.B6.Encaps':
                        # Rebuild segments
                        segments = []
                        for srv6_segment in behavior.segs:
                            segments.append(srv6_segment.segment)
                        # pyroute2 requires the segments in reverse order
                        segments.reverse()
                        # Parameters of End.B6 behavior
                        encap = {'srh': {'segs': segments}}
                    else:
                        logger.debug('Error: Unrecognized action')
                        return srv6_manager_pb2.SRv6ManagerReply(
                            status=commons_pb2.STATUS_INVALID_ACTION)
                    # Finalize encap dict
                    encap['type'] = 'seg6local'
                    encap['action'] = action
                    # Create/Change the seg6local route
                    self.ip_route.route(operation, family=AF_INET6,
                                        dst=segment,
                                        oif=self.interface_to_idx[device],
                                        table=table,
                                        priority=metric,
                                        encap=encap)
                else:
                    # Operation unknown: this is a bug
                    logger.error(f'BUG - Unrecognized operation: {operation}')
                    sys.exit(-1)
            # and create the response
            logger.debug('Send response: OK')
            return srv6_manager_pb2.SRv6ManagerReply(
                status=commons_pb2.STATUS_SUCCESS)
        except NetlinkError as err:
            return srv6_manager_pb2.SRv6ManagerReply(
                status=self.parse_netlink_error(err))

    def Execute(self, operation, request, context):
        # Handle operation
        # The operation to be executed depends on
        # the entity carried by the request message
        res = self.HandleSRv6PathRequest(
            operation, request.srv6_path_request, context)
        if res.status == commons_pb2.STATUS_SUCCESS:
            res = self.HandleSRv6BehaviorRequest(
                operation, request.srv6_behavior_request, context)
        return res

    def Create(self, request, context):
        # Handle Create operation
        return self.Execute('add', request, context)

    def Get(self, request, context):
        # Handle Create operation
        return self.Execute('get', request, context)

    def Update(self, request, context):
        # Handle Remove operation
        return self.Execute('change', request, context)

    def Remove(self, request, context):
        # Handle Remove operation
        return self.Execute('del', request, context)


# Start gRPC server
def start_server(grpc_ip=DEFAULT_GRPC_IP,
                 grpc_port=DEFAULT_GRPC_PORT,
                 secure=DEFAULT_SECURE,
                 certificate=DEFAULT_CERTIFICATE,
                 key=DEFAULT_KEY):
    # Get family of the gRPC IP
    addr_family = get_address_family(grpc_ip)
    # Build address depending on the family
    if addr_family == AF_INET:
        # IPv4 address
        server_addr = '%s:%s' % (grpc_ip, grpc_port)
    elif addr_family == AF_INET6:
        # IPv6 address
        server_addr = '[%s]:%s' % (grpc_ip, grpc_port)
    else:
        # Invalid address
        logger.fatal(f'Invalid gRPC address: {grpc_ip}')
        sys.exit(-2)
    # Create the server and add the handlers
    grpc_server = grpc.server(futures.ThreadPoolExecutor())
    (srv6_manager_pb2_grpc
        .add_SRv6ManagerServicer_to_server(
            SRv6Manager(), grpc_server)
     )
    # If secure we need to create a secure endpoint
    if secure:
        # Read key and certificate
        with open(key, 'rb') as key_file:
            key = key_file.read()
        with open(certificate, 'rb') as certificate_file:
            certificate = certificate_file.read()
        # Create server ssl credentials
        grpc_server_credentials = (grpc
                                   .ssl_server_credentials(((key,
                                                             certificate),)))
        # Create a secure endpoint
        grpc_server.add_secure_port(server_addr, grpc_server_credentials)
    else:
        # Create an insecure endpoint
        grpc_server.add_insecure_port(server_addr)
    # Start the loop for gRPC
    logger.info(f'*** Listening gRPC on address {server_addr}')
    grpc_server.start()
    while True:
        time.sleep(5)


# Check whether we have root permission or not
# Return True if we have root permission, False otherwise
def check_root():
    return os.getuid() == 0


# Parse options
def parse_arguments():
    # Get parser
    parser = ArgumentParser(
        description='gRPC Southbound APIs for SRv6 Controller'
    )
    parser.add_argument(
        '-g', '--grpc-ip', dest='grpc_ip', action='store',
        default=DEFAULT_GRPC_IP, help='IP of the gRPC server'
    )
    parser.add_argument(
        '-r', '--grpc-port', dest='grpc_port', action='store',
        default=DEFAULT_GRPC_PORT, help='Port of the gRPC server'
    )
    parser.add_argument(
        '-s', '--secure', action='store_true', help='Activate secure mode'
    )
    parser.add_argument(
        '-c', '--server-cert', dest='server_cert', action='store',
        default=DEFAULT_CERTIFICATE, help='Server certificate file'
    )
    parser.add_argument(
        '-k', '--server-key', dest='server_key',
        action='store', default=DEFAULT_KEY, help='Server key file'
    )
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Activate debug logs'
    )
    # Parse input parameters
    args = parser.parse_args()
    # Return the arguments
    return args


if __name__ == '__main__':
    _args = parse_arguments()
    # Setup properly the secure mode
    _secure = _args.secure
    # gRPC server IP
    _grpc_ip = _args.grpc_ip
    # gRPC server port
    _grpc_port = _args.grpc_port
    # Server certificate
    _certificate = _args.server_cert
    # Server key
    _key = _args.server_key
    # Setup properly the logger
    if _args.debug:
        logger.setLevel(level=logging.DEBUG)
    else:
        logger.setLevel(level=logging.INFO)
    # Debug settings
    server_debug = logger.getEffectiveLevel() == logging.DEBUG
    logging.info('SERVER_DEBUG:', str(server_debug))
    # This script must be run as root
    if not check_root():
        logger.critical(f'*** {sys.argv[0]} must be run as root.\n')
        sys.exit(1)
    # Start the server
    start_server(_grpc_ip, _grpc_port, _secure, _certificate, _key)
