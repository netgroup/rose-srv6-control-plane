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
# Utils for controller
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


"""This module contains a collection of utilities used by Controller"""

# General imports
import logging
from ipaddress import AddressValueError, IPv4Interface, IPv6Interface
from socket import AF_INET, AF_INET6

# gRPC dependencies
import grpc

# Proto dependencies
import commons_pb2

# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)


# Utiliy function to check if the IP
# is a valid IPv6 address


def validate_ipv6_address(ip_address):
    """Return True if the provided IP address is a valid IPv6 address"""

    if ip_address is None:
        return False
    try:
        IPv6Interface(ip_address)
        return True
    except AddressValueError:
        return False


# Utiliy function to check if the IP
# is a valid IPv4 address
def validate_ipv4_address(ip_address):
    """Return True if the provided IP address is a valid IPv4 address"""

    if ip_address is None:
        return False
    try:
        IPv4Interface(ip_address)
        return True
    except AddressValueError:
        return False


# Utiliy function to get the IP address family
def get_address_family(ip_address):
    """Return the family of the provided IP address
    or None if the IP is invalid"""

    if validate_ipv6_address(ip_address):
        # IPv6 address
        return AF_INET6
    if validate_ipv4_address(ip_address):
        # IPv4 address
        return AF_INET
    # Invalid address
    return None


# Utiliy function to check if the IP
# is a valid IP address
def validate_ip_address(ip_address):
    """Return True if the provided IP address
    is a valid IPv4 or IPv6 address"""

    return validate_ipv4_address(ip_address) or \
        validate_ipv6_address(ip_address)


# Build a grpc stub
def get_grpc_session(server_ip, server_port, secure=False, certificate=None):
    """Create a Channel to a server.

    Parameters
    ----------
    server_ip : str
        The IP address of the gRPC server
    server_port : int
        The port of the gRPC server

    Returns
    -------
    The requested gRPC Channel or None if the operation has failed.
    """

    # Get family of the gRPC IP
    addr_family = get_address_family(server_ip)
    # Build address depending on the family
    if addr_family == AF_INET:
        # IPv4 address
        server_ip = 'ipv4:%s:%s' % (server_ip, server_port)
    elif addr_family == AF_INET6:
        # IPv6 address
        server_ip = 'ipv6:[%s]:%s' % (server_ip, server_port)
    else:
        # Invalid address
        logger.fatal('Invalid gRPC address: %s', server_ip)
        return None
    # If secure we need to establish a channel with the secure endpoint
    if secure:
        if certificate is None:
            logger.fatal('Certificate required for gRPC secure mode')
            return None
        # Open the certificate file
        with open(certificate, 'rb') as certificate_file:
            certificate = certificate_file.read()
        # Then create the SSL credentials and establish the channel
        grpc_client_credentials = grpc.ssl_channel_credentials(certificate)
        channel = grpc.secure_channel(server_ip, grpc_client_credentials)
    else:
        channel = grpc.insecure_channel(server_ip)
    # Return the channel
    return channel


# Human-readable gRPC return status
status_code_to_str = {
    commons_pb2.STATUS_SUCCESS: 'Success',
    commons_pb2.STATUS_OPERATION_NOT_SUPPORTED: ('Operation '
                                                 'not supported'),
    commons_pb2.STATUS_BAD_REQUEST: 'Bad request',
    commons_pb2.STATUS_INTERNAL_ERROR: 'Internal error',
    commons_pb2.STATUS_INVALID_GRPC_REQUEST: 'Invalid gRPC request',
    commons_pb2.STATUS_FILE_EXISTS: 'An entity already exists',
    commons_pb2.STATUS_NO_SUCH_PROCESS: 'Entity not found',
    commons_pb2.STATUS_INVALID_ACTION: 'Invalid seg6local action',
    commons_pb2.STATUS_GRPC_SERVICE_UNAVAILABLE: ('gRPC service not '
                                                  'available'),
    commons_pb2.STATUS_GRPC_UNAUTHORIZED: 'Unauthorized',
    commons_pb2.STATUS_NOT_CONFIGURED: 'Node not configured'
}


def print_status_message(status_code, success_msg, failure_msg):
    """Print success or failure message depending of the status code
        returned by a gRPC operation.

    Parameters
    ----------
    status_code : int
        The status code returned by the gRPC operation
    success_msg : str
        The message to print in case of success
    failure_msg : str
        The message to print in case of error
    """

    if status_code == commons_pb2.STATUS_SUCCESS:
        # Success
        print('%s (status code %s - %s)'
              % (success_msg, status_code,
                 status_code_to_str.get(status_code, 'Unknown')))
    else:
        # Error
        print('%s (status code %s - %s)'
              % (failure_msg, status_code,
                 status_code_to_str.get(status_code, 'Unknown')))
