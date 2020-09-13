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
# Topology information extraction
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


# Topology Information Extraction dependencies
from controller.ti_extraction.ti_extraction_utils import DEFAULT_VERBOSE
from controller.ti_extraction.ti_extraction_isis import (
    connect_and_extract_topology_isis,
    topology_information_extraction_isis
)


# Global variables definition
#
#
# The following parameters are the default arguments used by the functions
# defined in this module. You can override the default values by passing
# your custom argments to the functions
#
# In our experiment we use 'zebra' as default password for isisd
DEFAULT_PASSWORD = 'zebra'


class InvalidProtocolError(Exception):
    '''
    The protocol is invalid.
    '''


def connect_and_extract_topology(ips_ports, protocol,
                                 password=DEFAULT_PASSWORD,
                                 verbose=DEFAULT_VERBOSE):
    '''
    Establish a telnet connection to the routing daemon running on a router
    and extract the network topology from the router.
    For redundancy purposes, this function accepts a list of routers.

    :param ips_ports: A list of pairs ip-port representing IP and port of
                      the routers you want to extract the topology from
                      (e.g. ['fcff:1::1-2608', 'fcff:2::1-2608']).
    :type ips_ports: list
    :param protocol: The routing protocol from which you want to extract the
                     topology (currently only 'isis' is supported)
    :type protocol: str
    :param password: The password used to log in to the daemon.
    :type password: str
    :param verbose: Define whether the verbose mode must be enable or not
                    (default: False).
    :type verbose: bool, optional
    :return: A tuple containing the nodes, the edges and the
             hostname-to-SystemID mapping.
             Each node is represented by its hostname.
             The edges are represented as tuples
             (node_left, node_right, ip_address), where node_left and
             node_right are the endpoints of the edge and ip_address is
             the IP address of the subnet associated to the edge.
             The hostname-to-SystemID mapping is a dict.
    :rtype: tuple
    :raises NoISISNodesAvailableError: The provided set of nodes does not
                                       contain any ISIS node.
    :raises InvalidProtocolError: The provided set of nodes does no contain
                                  any ISIS node.
    '''
    # Which protocol?
    if protocol == 'isis':
        # ISIS protocol
        res = connect_and_extract_topology_isis(
            ips_ports=ips_ports,
            password=password,
            verbose=verbose
        )
    else:
        # Unknown protocol
        raise InvalidProtocolError
    # Return the result
    return res


def topology_information_extraction(routers, protocol, period, password,
                                    topo_file_json=None, nodes_file_yaml=None,
                                    edges_file_yaml=None, topo_graph=None,
                                    verbose=DEFAULT_VERBOSE):
    '''
    Extract topological information from a set of routers running a
    routing protocol. The routers must execute an instance of routing
    protocols from the routing suite FRRRouting. This function can be also
    instructed to repeat the extraction at regular intervals.
    Optionally the topology can be exported to a JSON file, YAML file or SVG
    image.

    :param routers: A list of pairs ip-port representing IP and port of
                    the nodes you want to extract the topology from
                    (e.g. ['fcff:1::1-2608', 'fcff:2::1-2608']).
    :type routers: list
    :param protocol: The routing protocol from which you want to extract the
                     topology (currently only 'isis' is supported)
    :type protocol: str
    :param period: The interval between two consecutive extractions. If this
                   arguments is equals to 0, this function performs a single
                   extraction and then returns (default: 0).
    :type period: int, optional
    :param password: The password used to log in to the routing daemon.
    :type d: str
    :param topo_file_json: The path and the name of the output JSON file. If
                           this parameter is not provided, the topology is not
                           exported to a JSON file (default: None).
    :type topo_file_json: str, optional
    :param nodes_file_yaml: The path and the name of the output YAML file
                            containing the nodes. If this parameter is not
                            provided, the nodes are not exported to a YAML
                            file (default: None).
    :type nodes_file_yaml: str, optional
    :param edges_file_yaml: The path and the name of the output YAML file
                            containing the edges. If this parameter is not
                            provided, the edges are not exported to a YAML
                            file (default: None).
    :type edges_file_yaml: str, optional
    :param topo_graph: The path and the name of the output SVG file containing
                       the topology graph exported as image. If this parameter
                       is not provided, the topology is not exported to a SVG
                       file (default: None).
    :type topo_graph: str, optional
    :param verbose: Define whether the verbose mode must be enable or not
                    (default: False).
    :type verbose: bool, optional
    :return: True.
    :rtype: bool
    '''
    # pylint: disable=too-many-arguments
    #
    # Which protocol?
    if protocol == 'isis':
        # ISIS protocol
        res = topology_information_extraction_isis(
            routers=routers,
            period=period,
            password=password,
            topo_file_json=topo_file_json,
            nodes_file_yaml=nodes_file_yaml,
            edges_file_yaml=edges_file_yaml,
            topo_graph=topo_graph,
            verbose=verbose
        )
    else:
        # Unknown protocol
        raise InvalidProtocolError
    # Return the result
    return res
