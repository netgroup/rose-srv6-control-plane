#!/usr/bin/python

##########################################################################
# Copyright (C) 2020 Carmine Scarpitta
# (Consortium GARR and University of Rome 'Tor Vergata')
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
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Implementation of SRv6 Manager
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#

'''
This module provides an implementation of a SRv6 Manager. Currently, it
supports "Linux" and "VPP" as forwarding engine. However, the design of this
module is modular and other forwarding engines can be easily added in the
future.
'''


# General imports
import logging
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
# Node Manager dependencies
from node_manager.utils import get_address_family
from node_manager.srv6_manager.utils import check_root
from node_manager.srv6_mgr_linux import SRv6ManagerLinux
from node_manager.srv6_mgr_vpp import SRv6ManagerVPP  # TODO
# Import constants file
from node_manager.constants import FWD_ENGINE_STR_TO_INT

# Folder containing this script
BASE_PATH = os.path.dirname(os.path.realpath(__file__))


# Global variables definition
#
#
# Logger reference
logging.basicConfig(level=logging.NOTSET)
LOGGER = logging.getLogger(__name__)
#
# Default parameters for SRv6 Manager
#
# Server ip and port
DEFAULT_GRPC_IP = '::'
DEFAULT_GRPC_PORT = 12345
# Debug option
DEFAULT_DEBUG = False
# Secure option
DEFAULT_SECURE = False
# Server certificate
DEFAULT_CERTIFICATE = 'cert_server.pem'
# Server key
DEFAULT_KEY = 'key_server.pem'
# Is VPP support enabled by default?
DEFAULT_ENABLE_VPP = False


class SRv6Manager(srv6_manager_pb2_grpc.SRv6ManagerServicer):
    '''
    gRPC request handler
    '''

    def __init__(self):
        # Define a dict to map Forwarding Engines to their handlers
        # The key of the dict is a numeric code corresponding to the
        # Forwarding Engine, the value is an handler for the Forwarding Engine
        self.fwd_engine = dict()
        # Init SRv6 Manager for Linux Forwarding Engine
        # It allows the SDN Controller to control the Linux Forwarding Engine
        self.fwd_engine[FWD_ENGINE_STR_TO_INT['Linux']] = SRv6ManagerLinux()
        # Init SRv6 Manager for VPP Forwarding Engine, if VPP is enabled
        if os.getenv('ENABLE_VPP', DEFAULT_ENABLE_VPP):
            # It allows the SDN Controller to control the VPP Forwarding Engine
            self.fwd_engine[FWD_ENGINE_STR_TO_INT['VPP']] = SRv6ManagerVPP()

    def handle_srv6_path_request(self, operation, request, context, ret_paths):
        '''
        Handler for SRv6 paths.
        '''
        # pylint: disable=unused-argument
        #
        # Process request
        LOGGER.debug('config received:\n%s', request)
        # Extract forwarding engine
        fwd_engine = request.fwd_engine
        # Perform operation
        if fwd_engine not in self.fwd_engine:
            # Unknown forwarding engine
            LOGGER.error('Unknown Forwarding Engine. '
                         'Make sure that it is enabled in the configuration.')
            return srv6_manager_pb2.SRv6ManagerReply(
                status=commons_pb2.StatusCode.Value('INVALID_FWD_ENGINE'))
        # Dispatch the request to the right Forwarding Engine handler and
        # return the result
        return self.fwd_engine[fwd_engine].handle_srv6_path_request(
            operation=operation,
            request=request,
            context=context,
            ret_paths=ret_paths
        )

    def handle_srv6_policy_request(self, operation, request, context,
                                   ret_policies):
        '''
        Handler for SRv6 policies.
        '''
        # pylint: disable=unused-argument
        #
        # Process request
        LOGGER.debug('config received:\n%s', request)
        # Extract forwarding engine
        fwd_engine = request.fwd_engine
        # Perform operation
        if fwd_engine not in self.fwd_engine:
            # Unknown forwarding engine
            LOGGER.error('Unknown Forwarding Engine.'
                         'Make sure that it is enabled in the configuration.')
            return srv6_manager_pb2.SRv6ManagerReply(
                status=commons_pb2.StatusCode.Value('INVALID_FWD_ENGINE'))
        # Dispatch the request to the right Forwarding Engine handler
        return self.fwd_engine[fwd_engine].handle_srv6_policy_request(
            operation=operation,
            request=request,
            context=context,
            ret_policies=ret_policies
        )

    def handle_srv6_behavior_request(self, operation, request, context,
                                     ret_behaviors):
        '''
        Handler for SRv6 behaviors.
        '''
        # pylint: disable=unused-argument
        #
        # Process request
        LOGGER.debug('config received:\n%s', request)
        # Extract forwarding engine
        fwd_engine = request.fwd_engine
        # Perform operation
        if fwd_engine not in self.fwd_engine:
            # Unknown forwarding engine
            LOGGER.error('Unknown Forwarding Engine.'
                         'Make sure that it is enabled in the configuration.')
            return srv6_manager_pb2.SRv6ManagerReply(
                status=commons_pb2.StatusCode.Value('INVALID_FWD_ENGINE'))
        # Dispatch the request to the right Forwarding Engine handler
        return self.fwd_engine[fwd_engine].handle_srv6_behavior_request(
            peration=operation,
            request=request,
            context=context,
            ret_behaviors=ret_behaviors
        )

    def execute(self, operation, request, context):
        '''
        This function dispatch the gRPC requests based on the entity carried
        in them.
        '''
        # Handle operation
        #
        # The operations to be executed depends on the entity carried by the
        # request message
        reply = srv6_manager_pb2.SRv6ManagerReply(
            status=commons_pb2.STATUS_SUCCESS)
        if request.HasField('srv6_path_request'):
            # The message contains at least one SRv6 Path request, so we pass
            # the request to the SRv6 Path handler
            res = self.handle_srv6_path_request(
                operation=operation,
                request=request.srv6_path_request,
                context=context,
                ret_paths=reply.paths
            )
            if res != commons_pb2.STATUS_SUCCESS:
                # An error occurred
                return srv6_manager_pb2.SRv6ManagerReply(
                    status=res)
        if request.HasField('srv6_policy_request'):
            # The message contains at least one SRv6 Path request, so we pass
            # the request to the SRv6 Policy handler
            res = self.handle_srv6_policy_request(
                operation=operation,
                request=request.srv6_policy_request,
                context=context,
                ret_policies=reply.policies
            )
            if res != commons_pb2.STATUS_SUCCESS:
                # An error occurred
                return srv6_manager_pb2.SRv6ManagerReply(
                    status=res)
        if request.HasField('srv6_behavior_request'):
            # The message contains at least one SRv6 Path request, so we pass
            # the request to the SRv6 Behavior handler
            res = self.handle_srv6_behavior_request(
                operation=operation,
                request=request.srv6_behavior_request,
                context=context,
                ret_behaviors=reply.behaviors
            )
            if res != commons_pb2.STATUS_SUCCESS:
                # An error occurred
                return srv6_manager_pb2.SRv6ManagerReply(
                    status=res)
        # Return the result
        return reply

    def Create(self, request, context):
        '''
        RPC used to create a SRv6 entity.
        '''
        # pylint: disable=invalid-name
        #
        # Handle Create operation
        return self.execute('add', request, context)

    def Get(self, request, context):
        '''
        RPC used to get a SRv6 entity.
        '''
        # pylint: disable=invalid-name
        #
        # Handle Create operation
        return self.execute('get', request, context)

    def Update(self, request, context):
        '''
        RPC used to change a SRv6 entity.
        '''
        # pylint: disable=invalid-name
        #
        # Handle Remove operation
        return self.execute('change', request, context)

    def Remove(self, request, context):
        '''
        RPC used to remove a SRv6 entity.
        '''
        # pylint: disable=invalid-name
        #
        # Handle Remove operation
        return self.execute('del', request, context)


# Start gRPC server
def start_server(grpc_ip=DEFAULT_GRPC_IP,
                 grpc_port=DEFAULT_GRPC_PORT,
                 secure=DEFAULT_SECURE,
                 certificate=DEFAULT_CERTIFICATE,
                 key=DEFAULT_KEY):
    '''
    Start a gRPC server that implements the functionality of a SRv6 Manager.

    :param grpc_ip: The IP address on which the gRPC server will listen for
                    connections (default: "::").
    :type grpc_ip: str, optional
    :param grpc_port: The port number on which the gRPC server will listen for
                    connections (default: 12345).
    :type grpc_port: int, optional
    :param secure: Define whether to enable the gRPC sercure mode; if secure
                   mode is enabled, gRPC will use TLS secured channels instead
                   of TCP channels (default: False).
    :type secure: bool, optional
    :param certificate: The file containing the certificate of the server to
                        be used for the gRPC secure mode. If you don't use the
                        secure mode, you can omit this argument (default:
                        "cert_server.pem").
    :type certificate: str, optional
    :param key: The file containing the key of the server to be used for the
                gRPC secure mode. If you don't use the secure mode, you can
                omit this argument (default: "key_server.pem").
    :type key: str, optional
    '''
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


# Parse options
def parse_arguments():
    '''
    Command-line arguments parser
    '''
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
        '-d', '--debug', action='store_true', help='Activate debug logs',
        default=DEFAULT_DEBUG
    )
    # Parse input parameters
    args = parser.parse_args()
    # Return the arguments
    return args


def __main():
    '''
    Entry point for this script
    '''
    # Parse the arguments
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
