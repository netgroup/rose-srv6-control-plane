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
# Utils for controller
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


import grpc
import logging
from socket import AF_INET, AF_INET6
from ipaddress import IPv4Interface, IPv6Interface, AddressValueError

# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)


# Utiliy function to check if the IP
# is a valid IPv6 address


def validate_ipv6_address(ip):
    if ip is None:
        return False
    try:
        IPv6Interface(ip)
        return True
    except AddressValueError:
        return False


# Utiliy function to check if the IP
# is a valid IPv4 address
def validate_ipv4_address(ip):
    if ip is None:
        return False
    try:
        IPv4Interface(ip)
        return True
    except AddressValueError:
        return False


# Utiliy function to get the IP address family
def get_address_family(ip):
    if validate_ipv6_address(ip):
        # IPv6 address
        return AF_INET6
    elif validate_ipv4_address(ip):
        # IPv4 address
        return AF_INET
    else:
        # Invalid address
        return None


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
        logger.fatal('Invalid gRPC address: %s' % server_ip)
        return None
    # If secure we need to establish a channel with the secure endpoint
    if secure:
        if certificate is None:
            logger.fatal('Certificate required for gRPC secure mode')
            return None
        # Open the certificate file
        with open(certificate, 'rb') as f:
            certificate = f.read()
        # Then create the SSL credentials and establish the channel
        grpc_client_credentials = grpc.ssl_channel_credentials(certificate)
        channel = grpc.secure_channel(server_ip, grpc_client_credentials)
    else:
        channel = grpc.insecure_channel(server_ip)
    # Return the channel
    return channel
