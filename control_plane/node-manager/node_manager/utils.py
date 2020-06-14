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
# Utils for node manager
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


"""This module contains several utility functions for node manager"""

from ipaddress import AddressValueError, IPv4Interface, IPv6Interface
from socket import AF_INET, AF_INET6


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
