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


"""
This module contains a collection of utilities used by Controller
"""

# General imports
import logging
from ipaddress import AddressValueError, IPv4Interface, IPv6Interface
from ipaddress import ip_address
from socket import AF_INET, AF_INET6
from urllib.parse import urlparse

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


# Utiliy function to check if the IP
# is a valid IP address
def validate_ip_address(ip_address):
    """
    Return True if the provided IP address
    is a valid IPv4 or IPv6 address"""
    #
    return validate_ipv4_address(ip_address) or \
        validate_ipv6_address(ip_address)


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
    """
    Print success or failure message depending of the status code
    returned by a gRPC operation.

    :param status_code: The status code returned by the gRPC operation
    :type status_code: int
    :param success_msg: The message to print in case of success
    :type success_msg: str
    :param failure_msg: The message to print in case of error
    :type failure_msg: str
    """
    #
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


STATUS_CODE_TO_DESC = {
    commons_pb2.STATUS_SUCCESS: 'Operation completed successfully',
    commons_pb2.STATUS_OPERATION_NOT_SUPPORTED: 'Error: Operation not supported',
    commons_pb2.STATUS_BAD_REQUEST: 'Error: Bad request',
    commons_pb2.STATUS_INTERNAL_ERROR: 'Error: Internal error',
    commons_pb2.STATUS_INVALID_GRPC_REQUEST: 'Error: Invalid gRPC request',
    commons_pb2.STATUS_FILE_EXISTS: 'Error: Entity already exists',
    commons_pb2.STATUS_NO_SUCH_PROCESS: 'Error: Entity not found',
    commons_pb2.STATUS_INVALID_ACTION: 'Error: Invalid action',
    commons_pb2.STATUS_GRPC_SERVICE_UNAVAILABLE: 'Error: Unreachable grPC server',
    commons_pb2.STATUS_GRPC_UNAUTHORIZED: 'Error: Unauthorized',
    commons_pb2.STATUS_NOT_CONFIGURED: 'Error: Not configured',
    commons_pb2.STATUS_ALREADY_CONFIGURED: 'Error: Already configured',
    commons_pb2.STATUS_NO_SUCH_DEVICE: 'Error: Device not found',
}


def parse_ip_port(netloc):
    try:
        ip = ip_address(netloc)
        port = None
    except ValueError:
        parsed = urlparse('//{}'.format(netloc))
        ip = ip_address(parsed.hostname)
        port = parsed.port
    return ip, port


def grpc_chan_to_addr_port(channel):
    address, port = parse_ip_port(channel._channel.target().decode())
    return str(address), port


class OperationNotSupportedException(Exception):
    """
    Operation not supported.
    """


class BadRequestException(Exception):
    """
    Bad request.
    """


class InternalError(Exception):
    """
    Internal error.
    """


class InvalidGRPCRequestException(Exception):
    """
    Invalid gRPC request.
    """


class FileExistsException(Exception):
    """
    File already exists.
    """


class NoSuchProcessException(Exception):
    """
    No such process.
    """


class InvalidActionException(Exception):
    """
    Invalid SRv6 action.
    """


class GRPCServiceUnavailableException(Exception):
    """
    gRPC service unavailable.
    """


class GRPCUnauthorizedException(Exception):
    """
    gRPC unauthorized.
    """


class NotConfiguredException(Exception):
    """
    Not configured.
    """


class AlreadyConfiguredException(Exception):
    """
    Already configured.
    """


class NoSuchDevicecException(Exception):
    """
    No such device.
    """


class InvalidArgumentError(Exception):
    """
    Invalid argument.
    """


def raise_exception_on_error(error_code):
    if error_code == commons_pb2.STATUS_SUCCESS:
        return
    if error_code == commons_pb2.STATUS_OPERATION_NOT_SUPPORTED:
        raise OperationNotSupportedException
    if error_code == commons_pb2.STATUS_BAD_REQUEST:
        raise BadRequestException
    if error_code == commons_pb2.STATUS_INTERNAL_ERROR:
        raise InternalError
    if error_code == commons_pb2.STATUS_INVALID_GRPC_REQUEST:
        raise InvalidGRPCRequestException
    if error_code == commons_pb2.STATUS_FILE_EXISTS:
        raise FileExistsException
    if error_code == commons_pb2.STATUS_NO_SUCH_PROCESS:
        raise NoSuchProcessException
    if error_code == commons_pb2.STATUS_INVALID_ACTION:
        raise InvalidActionException
    if error_code == commons_pb2.STATUS_GRPC_SERVICE_UNAVAILABLE:
        raise GRPCServiceUnavailableException
    if error_code == commons_pb2.STATUS_GRPC_UNAUTHORIZED:
        raise GRPCUnauthorizedException
    if error_code == commons_pb2.STATUS_NOT_CONFIGURED:
        raise NotConfiguredException
    if error_code == commons_pb2.STATUS_ALREADY_CONFIGURED:
        raise AlreadyConfiguredException
    if error_code == commons_pb2.STATUS_NO_SUCH_DEVICE:
        raise NoSuchDevicecException
    raise InvalidArgumentError
