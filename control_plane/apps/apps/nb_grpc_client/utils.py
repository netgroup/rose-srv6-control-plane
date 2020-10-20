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
# Utilities functions used by gRPC client
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


"""
Utilities functions used by gRPC client.
"""

# General imports
import logging
from ipaddress import AddressValueError, IPv4Interface, IPv6Interface
from socket import AF_INET, AF_INET6

# gRPC dependencies
import grpc

# Proto dependencies
from commons_pb2 import (STATUS_SUCCESS,
                         STATUS_OPERATION_NOT_SUPPORTED,
                         STATUS_BAD_REQUEST,
                         STATUS_INTERNAL_ERROR,
                         STATUS_INVALID_GRPC_REQUEST,
                         STATUS_FILE_EXISTS,
                         STATUS_NO_SUCH_PROCESS,
                         STATUS_INVALID_ACTION,
                         STATUS_GRPC_SERVICE_UNAVAILABLE,
                         STATUS_GRPC_UNAUTHORIZED,
                         STATUS_NOT_CONFIGURED,
                         STATUS_ALREADY_CONFIGURED,
                         STATUS_NO_SUCH_DEVICE)

# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)


STATUS_CODE_TO_DESC = {
    STATUS_SUCCESS: 'Operation completed successfully',
    STATUS_OPERATION_NOT_SUPPORTED: 'Error: Operation not supported',
    STATUS_BAD_REQUEST: 'Error: Bad request',
    STATUS_INTERNAL_ERROR: 'Error: Internal error',
    STATUS_INVALID_GRPC_REQUEST: 'Error: Invalid gRPC request',
    STATUS_FILE_EXISTS: 'Error: Entity already exists',
    STATUS_NO_SUCH_PROCESS: 'Error: Entity not found',
    STATUS_INVALID_ACTION: 'Error: Invalid action',
    STATUS_GRPC_SERVICE_UNAVAILABLE: 'Error: Unreachable grPC server',
    STATUS_GRPC_UNAUTHORIZED: 'Error: Unauthorized',
    STATUS_NOT_CONFIGURED: 'Error: Not configured',
    STATUS_ALREADY_CONFIGURED: 'Error: Already configured',
    STATUS_NO_SUCH_DEVICE: 'Error: Device not found',
}


class InvalidArgumentError(Exception):
    """
    Invalid argument.
    """


class NodesConfigNotLoadedError(Exception):
    """
    NodesConfigNotLoadedError
    """


def raise_exception_on_error(error_code):   # TODO exeptions more specific
    if error_code == STATUS_SUCCESS:
        return
    if error_code == STATUS_OPERATION_NOT_SUPPORTED:
        raise InvalidArgumentError
    if error_code == STATUS_BAD_REQUEST:
        raise InvalidArgumentError
    if error_code == STATUS_INTERNAL_ERROR:
        raise InvalidArgumentError
    if error_code == STATUS_INVALID_GRPC_REQUEST:
        raise InvalidArgumentError
    if error_code == STATUS_FILE_EXISTS:
        raise InvalidArgumentError
    if error_code == STATUS_NO_SUCH_PROCESS:
        raise InvalidArgumentError
    if error_code == STATUS_INVALID_ACTION:
        raise InvalidArgumentError
    if error_code == STATUS_GRPC_SERVICE_UNAVAILABLE:
        raise InvalidArgumentError
    if error_code == STATUS_GRPC_UNAUTHORIZED:
        raise InvalidArgumentError
    if error_code == STATUS_NOT_CONFIGURED:
        raise NodesConfigNotLoadedError
    if error_code == STATUS_ALREADY_CONFIGURED:
        raise InvalidArgumentError
    if error_code == STATUS_NO_SUCH_DEVICE:
        raise InvalidArgumentError
    raise InvalidArgumentError


# Utiliy function to check if the IP
# is a valid IPv6 address
def validate_ipv6_address(ip_address):
    """
    Return True if the provided IP address is a valid IPv6 address
    """
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
    """
    Return True if the provided IP address is a valid IPv4 address
    """
    if ip_address is None:
        return False
    try:
        IPv4Interface(ip_address)
        return True
    except AddressValueError:
        return False


# Utiliy function to get the IP address family
def get_address_family(ip_address):
    """
    Return the family of the provided IP address
    or None if the IP is invalid
    """
    if validate_ipv6_address(ip_address):
        # IPv6 address
        return AF_INET6
    if validate_ipv4_address(ip_address):
        # IPv4 address
        return AF_INET
    # Invalid address
    return None


# Build a grpc stub
def get_grpc_session(server_ip, server_port, secure=False, certificate=None):
    """
    Create a Channel to a server.

    :param server_ip: The IP address of the gRPC server
    :type server_ip: str
    :param server_port: The port of the gRPC server
    :type server_port: int
    :return: The requested gRPC Channel or None if the operation has failed.
    :rtype: class: `grpc._channel.Channel`
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
        # Hostname or invalid address
        # We try to treat the address as a hostname
        server_ip = '%s:%s' % (server_ip, server_port)
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


action_to_grpc_repr = {
    'End': 'END',
    'End.X': 'END_x',
    'End.T': 'END_T',
    'End.DX4': 'END_DX4',
    'End.DX6': 'END_DX6',
    'End.DX2': 'END_DX2',
    'End.DT4': 'END_DT4',
    'End.DT6': 'END_DT6',
    'End.B6': 'END_B6',
    'End.B6.Encaps': 'END_B6_ENCAPS'
}

grpc_repr_to_action = {v: k for k, v in action_to_grpc_repr.items()}

node_type_to_grpc_repr = {
    'router': 'ROUTER',
    'host': 'HOST'
}

grpc_repr_to_node_type = {v: k for k, v in node_type_to_grpc_repr.items()}

edge_type_to_grpc_repr = {
    'core': 'CORE',
    'edge': 'EDGE'
}

grpc_repr_to_edge_type = {v: k for k, v in edge_type_to_grpc_repr.items()}
