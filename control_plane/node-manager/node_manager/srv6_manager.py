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
# Implementation of SRv6 Manager
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#

"""This module provides an implementation of a SRv6 Manager"""


import logging
# General imports
import os
import sys
import time
from argparse import ArgumentParser
from concurrent import futures
from socket import AF_INET, AF_INET6

# gRPC dependencies
import grpc

# Proto dependencies
import commons_pb2
import srv6_manager_pb2
import srv6_manager_pb2_grpc
# Node manager dependencies
from node_manager.utils import get_address_family
from node_manager.srv6_mgr_linux import SRv6ManagerLinux
# from node_manager.srv6_mgr_vpp import SRv6ManagerVPP      TODO

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
LOGGER = logging.getLogger(__name__)
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


class SRv6Manager(srv6_manager_pb2_grpc.SRv6ManagerServicer):
    """gRPC request handler"""

    def __init__(self):
        # SRv6 Manager for Linux Forwarding Engine
        self.srv6_mgr_linux = SRv6ManagerLinux()
        # SRv6 Manager for VPP Forwarding Engine
        self.srv6_mgr_vpp = None
        # self.srv6_mgr_vpp = SRv6ManagerVPP()      TODO

    def handle_srv6_path_request(self, operation, request, context):
        # pylint: disable=unused-argument
        """Handler for SRv6 paths"""

        LOGGER.debug('config received:\n%s', request)
        # Extract forwarding engine
        fwd_engine = request.fwd_engine
        # Perform operation
        if fwd_engine == srv6_manager_pb2.FwdEngine.Value('Linux'):
            # Linux forwarding engine
            return self.srv6_mgr_linux.handle_srv6_path_request(operation,
                                                                request,
                                                                context)
        if fwd_engine == srv6_manager_pb2.FwdEngine.Value('VPP'):
            # VPP forwarding engine
            return self.srv6_mgr_vpp.handle_srv6_path_request(operation,
                                                              request,
                                                              context)     # TODO gestire caso VPP non abilitato o non disponibile
        # Unknown forwarding engine
        return srv6_manager_pb2.SRv6ManagerReply(
            status=commons_pb2.StatusCode.Value('STATUS_INTERNAL_ERROR'))       # TODO creare un errore specifico

    def handle_srv6_behavior_request(self, operation, request, context):
        # pylint: disable=unused-argument
        """Handler for SRv6 behaviors"""

        LOGGER.debug('config received:\n%s', request)
        # Extract forwarding engine
        fwd_engine = request.fwd_engine
        # Perform operation
        if fwd_engine == srv6_manager_pb2.FwdEngine.Value('Linux'):
            # Linux forwarding engine
            return self.srv6_mgr_linux.handle_srv6_behavior_request(operation,
                                                                    request,
                                                                    context)
        if fwd_engine == srv6_manager_pb2.FwdEngine.Value('VPP'):
            # VPP forwarding engine
            # TODO gestire caso VPP non abilitato o non disponibile
            return self.srv6_mgr_vpp.handle_srv6_behavior_request(operation,
                                                                  request,
                                                                  context)
        # Unknown forwarding engine
        return srv6_manager_pb2.SRv6ManagerReply(
            status=commons_pb2.StatusCode.Value('STATUS_INTERNAL_ERROR'))       # TODO creare un errore specifico

    def execute(self, operation, request, context):
        """This function dispatch the gRPC requests based
        on the entity carried in them"""

        # Handle operation
        # The operation to be executed depends on
        # the entity carried by the request message
        res = self.handle_srv6_path_request(
            operation, request.srv6_path_request, context)
        if res.status == commons_pb2.STATUS_SUCCESS:
            res = self.handle_srv6_behavior_request(
                operation, request.srv6_behavior_request, context)
        return res

    def Create(self, request, context):
        # pylint: disable=invalid-name
        """RPC used to create a SRv6 entity"""

        # Handle Create operation
        return self.execute('add', request, context)

    def Get(self, request, context):
        # pylint: disable=invalid-name
        """RPC used to get a SRv6 entity"""

        # Handle Create operation
        return self.execute('get', request, context)

    def Update(self, request, context):
        # pylint: disable=invalid-name
        """RPC used to change a SRv6 entity"""

        # Handle Remove operation
        return self.execute('change', request, context)

    def Remove(self, request, context):
        # pylint: disable=invalid-name
        """RPC used to remove a SRv6 entity"""

        # Handle Remove operation
        return self.execute('del', request, context)


# Start gRPC server
def start_server(grpc_ip=DEFAULT_GRPC_IP,
                 grpc_port=DEFAULT_GRPC_PORT,
                 secure=DEFAULT_SECURE,
                 certificate=DEFAULT_CERTIFICATE,
                 key=DEFAULT_KEY):
    """Start a gRPC server"""

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
        LOGGER.fatal('Invalid gRPC address: %s', grpc_ip)
        sys.exit(-2)
    # Create the server and add the handlers
    grpc_server = grpc.server(futures.ThreadPoolExecutor())
    (srv6_manager_pb2_grpc
     .add_SRv6ManagerServicer_to_server(SRv6Manager(), grpc_server))
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
    LOGGER.info('*** Listening gRPC on address %s', server_addr)
    grpc_server.start()
    while True:
        time.sleep(5)


# Check whether we have root permission or not
# Return True if we have root permission, False otherwise
def check_root():
    """ Return True if this program is executed as root,
    False otherwise"""

    return os.getuid() == 0


# Parse options
def parse_arguments():
    """Command-line arguments parser"""

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


def __main():
    """Entry point for this script"""

    args = parse_arguments()
    # Setup properly the secure mode
    secure = args.secure
    # gRPC server IP
    grpc_ip = args.grpc_ip
    # gRPC server port
    grpc_port = args.grpc_port
    # Server certificate
    certificate = args.server_cert
    # Server key
    key = args.server_key
    # Setup properly the logger
    if args.debug:
        LOGGER.setLevel(level=logging.DEBUG)
    else:
        LOGGER.setLevel(level=logging.INFO)
    # Debug settings
    server_debug = LOGGER.getEffectiveLevel() == logging.DEBUG
    logging.info('SERVER_DEBUG: %s', str(server_debug))
    # This script must be run as root
    if not check_root():
        LOGGER.critical('*** %s must be run as root.\n', sys.argv[0])
        sys.exit(1)
    # Start the server
    start_server(grpc_ip, grpc_port, secure, certificate, key)


if __name__ == '__main__':
    __main()
