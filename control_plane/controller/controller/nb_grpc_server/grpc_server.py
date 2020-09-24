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
# Implementation of a gRPC server that provides a Northbound API for the SRv6
# controller
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
This module contains an implementation of a gRPC server that provides a
Northbound API for the SRv6 controller.
'''

# General imports
import logging
import os
import sys
import time
from concurrent import futures
from socket import AF_INET, AF_INET6

# gRPC dependencies
import grpc

# Controller dependencies
import nb_srv6_manager_pb2
import topology_manager_pb2
import srv6pm_manager_pb2
from controller.utils import get_address_family
from controller.nb_grpc_server.srv6_manager import SRv6Manager
from controller.nb_grpc_server.topo_manager import TopologyManager
from controller.nb_grpc_server.srv6pm_manager import SRv6PMManager


# Folder containing this script
BASE_PATH = os.path.dirname(os.path.realpath(__file__))


# Logger reference
logger = logging.getLogger(__name__)
#
# Default parameters for gRPC server
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
# Define whether to enable the debug mode or not
DEFAULT_DEBUG = False


# Start gRPC server
def start_server(grpc_ip=DEFAULT_GRPC_IP,
                 grpc_port=DEFAULT_GRPC_PORT,
                 secure=DEFAULT_SECURE,
                 certificate=DEFAULT_CERTIFICATE,
                 key=DEFAULT_KEY):
    '''
    Start a gRPC server.

    :param grpc_ip: The IP address of the gRPC server (default: ::).
    :type grpc_ip: str, optional
    :param grpc_port: The port number of the gRPC server (default: 12345)
    :type grpc_port: int, optional
    :param secure: Whether to enable or not gRPC secure mode (default: False)
    :type secure: bool, optional
    :param certificate: Filename of the certificate of the gRPC server
                        (default: cert_server.pem)
    :type certificate: str, optional
    :param key: Filename of the private key of the gRPC server
                (default: key_server.pem)
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
        logger.fatal('Invalid gRPC address: %s', grpc_ip)
        sys.exit(-2)
    # Create the server and add the handlers
    grpc_server = grpc.server(futures.ThreadPoolExecutor())
    # Add SRv6 Manager
    nb_srv6_manager_pb2.add_SRv6ManagerServicer_to_server(
        SRv6Manager(), grpc_server)
    # Add Topology Manager
    topology_manager_pb2.add_TopologyManagerServicer_to_server(
        TopologyManager(), grpc_server)
    # Add SRv6-PM Manager
    srv6pm_manager_pb2.add_SRv6PMManagerServicer_to_server(
        SRv6PMManager(), grpc_server)
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
    logger.info('*** Listening gRPC on address %s', server_addr)
    grpc_server.start()
    while True:
        time.sleep(5)
