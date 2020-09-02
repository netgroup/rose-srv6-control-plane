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
# Utils for SDN Controller
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
This module contains a collection of utilities used by Controller
'''

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


class InvalidArgumentError(Exception):
    '''
    Invalid argument.
    '''


class PolicyNotFoundError(Exception):
    '''
    Policy not found.
    '''


class NoMeasurementDataAvailableError(Exception):
    '''
    No measurement data are available.
    '''


# Utiliy function to check if an IP address is a valid IPv6 address
def validate_ipv6_address(ip_address):
    '''
    Return True if the provided IP address is a valid IPv6 address.

    :param ip_address: The IP address to validate.
    :type ip_address: str
    :return: True if the IP address is a valid IPv6 address, False otherwise.
    :rtype: bool
    '''
    if ip_address is None:
        # No address provided
        return False
    try:
        # Try to cast the provided argument to an IPv6Interface object
        IPv6Interface(ip_address)
        # If the cast gives no exceptions, the argument is a valid IPv6
        # address
        return True
    except AddressValueError:
        # If the cast results in a AddressValueError exception, the provided
        # argument is not a IPv6 address
        return False


# Utiliy function to check if the IP
# is a valid IPv4 address
def validate_ipv4_address(ip_address):
    '''
    Return True if the provided IP address is a valid IPv4 address.

    :param ip_address: The IP address to validate.
    :type ip_address: str
    :return: True if the IP address is a valid IPv4 address, False otherwise.
    :rtype: bool
    '''
    if ip_address is None:
        # No address provided
        return False
    try:
        # Try to cast the provided argument to an IPv4Interface object
        IPv4Interface(ip_address)
        # If the cast gives no exceptions, the argument is a valid IPv4
        # address
        return True
    except AddressValueError:
        # If the cast results in a AddressValueError exception, the provided
        # argument is not a IPv4 address
        return False


# Utiliy function to get the IP address family
def get_address_family(ip_address):
    '''
    Return the family of the provided IP address or None if the IP is invalid.

    :param ip_address: The IP address to validate.
    :type ip_address: str
    :return: An integer representing the address family. This can be:
                 - socket.AF_INET (for IPv4 address family)
                 - socket.AF_INET6 (for IPv6 address family)
    :rtype: int
    '''
    # Is an IPv6 address?
    if validate_ipv6_address(ip_address):
        return AF_INET6
    # Is an IPv4 address?
    if validate_ipv4_address(ip_address):
        return AF_INET
    # Invalid address
    return None


# Utiliy function to check if an IP address is a valid IP address (IPv6
# address or IPv4 address)
def validate_ip_address(ip_address):
    '''
    Return True if the provided IP address
    is a valid IPv4 or IPv6 address

    :param ip_address: The IP address to validate.
    :type ip_address: str
    :return: True if the IP address is a valid IP address, False otherwise.
    :rtype: bool
    '''
    # Is a valid IPv6 address or IPv4 address?
    return validate_ipv4_address(ip_address) or \
        validate_ipv6_address(ip_address)


# Build a grpc stub
def get_grpc_session(server_ip, server_port, secure=False, certificate=None):
    '''
    Create a gRPC Channel to a server.

    :param server_ip: The IP address of the gRPC server.
    :type server_ip: str
    :param server_port: The port of the gRPC server.
    :type server_port: int
    :param secure: Define whether to use a secure channel instead of a
                   unsecure one. Secure channels use TLS instead of TCP.
    :type secure: bool, optional
    :param certificate: File containing the certificate needed for the secure
                        mode.
    :type certificate: str, optional
    :return: The requested gRPC Channel or None if the operation has failed.
    :rtype: class: `grpc._channel.Channel`
    :raises InvalidArgumentError: Either the gRPC address or the certificate
                                  file are invalid.
    '''
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
        raise InvalidArgumentError
    # If secure we need to establish a channel with the secure endpoint
    if secure:
        # Secure mode requires a certificate file (certificate of a
        # Certification Authority)
        if certificate is None:
            logger.fatal('Certificate is required for gRPC secure mode')
            raise InvalidArgumentError
        # Open the certificate file
        with open(certificate, 'rb') as certificate_file:
            certificate = certificate_file.read()
        # Then create the SSL credentials and establish the channel
        grpc_client_credentials = grpc.ssl_channel_credentials(certificate)
        channel = grpc.secure_channel(server_ip, grpc_client_credentials)
    else:
        # Secure mode is disabled, establish a insecure channel
        channel = grpc.insecure_channel(server_ip)
    # Return the channel
    return channel


# Human-readable representation of the gRPC return statuses
# This is used to convert the status codes returned by the gRPCs into textual
# human-readable descriptions
status_code_to_str = {
    STATUS_SUCCESS: 'Success',
    STATUS_OPERATION_NOT_SUPPORTED: 'Operation not supported',
    STATUS_BAD_REQUEST: 'Bad request',
    STATUS_INTERNAL_ERROR: 'Internal error',
    STATUS_INVALID_GRPC_REQUEST: 'Invalid gRPC request',
    STATUS_FILE_EXISTS: 'An entity already exists',
    STATUS_NO_SUCH_PROCESS: 'Entity not found',
    STATUS_INVALID_ACTION: 'Invalid seg6local action',
    STATUS_GRPC_SERVICE_UNAVAILABLE: 'gRPC service not available',
    STATUS_GRPC_UNAUTHORIZED: 'Unauthorized',
    STATUS_NOT_CONFIGURED: 'Node not configured'
}


def print_status_message(status_code, success_msg, failure_msg):
    '''
    Print success or failure message depending of the status code
    returned by a gRPC operation.

    :param status_code: The status code returned by the gRPC operation
    :type status_code: int
    :param success_msg: The message to print in case of success
    :type success_msg: str
    :param failure_msg: The message to print in case of error
    :type failure_msg: str
    '''
    #
    if status_code == STATUS_SUCCESS:
        # Success
        logger.info('%s (status code %s - %s)'
                    % (success_msg, status_code,
                       status_code_to_str.get(status_code, 'Unknown')))
    else:
        # Error
        logger.error('%s (status code %s - %s)'
                     % (failure_msg, status_code,
                        status_code_to_str.get(status_code, 'Unknown')))


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
