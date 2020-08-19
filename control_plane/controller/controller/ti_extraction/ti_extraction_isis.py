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
# Topology information extraction from ISIS nodes
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
This module contains several utilities useful to extract the Topology
Information Extraction from a set of nodes running the ISIS protocol.
'''

# General imports
import errno
import logging
import re
import socket
import telnetlib
import time
from argparse import ArgumentParser

# Topology Information Extraction dependencies
from controller.ti_extraction.ti_extraction_utils import (
    build_topo_graph,
    dump_topo_json,
    dump_topo_yaml,
    draw_topo,
    DEFAULT_TOPOLOGY_FILE,
    DEFAULT_NODES_YAML_FILE,
    DEFAULT_EDGES_YAML_FILE,
    DEFAULT_TOPO_EXTRACTION_PERIOD,
    DEFAULT_VERBOSE
)

# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)


# Global variables definition
#
#
# The following parameters are the default arguments used by the functions
# defined in this module. You can override the default values by passing
# your custom argments to the functions
#
# In our experiment we use 'zebra' as default password for isisd
DEFAULT_ISISD_PASSWORD = 'zebra'


class NoISISNodesAvailableError(Exception):
    '''
    No ISIS nodes available.
    '''


def connect_and_extract_topology_isis(ips_ports,
                                      isisd_pwd=DEFAULT_ISISD_PASSWORD,
                                      verbose=DEFAULT_VERBOSE):
    '''
    Establish a telnet connection to the isisd process running on a router
    and extract the network topology from the router.
    For redundancy purposes, this function accepts a list of routers.

    :param ips_ports: A list of pairs ip-port representing IP and port of
                      the ISIS nodes you want to extract the topology from
                      (e.g. ['fcff:1::1-2608', 'fcff:2::1-2608']).
    :type ips_ports: list
    :param isisd_pwd: The password used to log in to isisd.
    :type isisd_pwd: str
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
    '''
    # pylint: disable=too-many-branches, too-many-locals, too-many-statements
    #
    # Let's parse the input
    routers = []
    ports = []
    # First create the chunk
    for ip_port in ips_ports:
        # Then parse the chunk
        #
        # Separate IP and port
        data = ip_port.split('-')
        # Append IP to the routers list
        routers.append(data[0])
        # Append port to the ports list
        ports.append(data[1])
    # Connect to a router and extract the topology
    for router, port in zip(routers, ports):
        logger.debug('\n********* Connecting to %s-%s *********',
                     router, port)
        # ####################################################################
        # Extract router hostnames
        try:
            # Init telnet and try to establish a connection to the router
            telnet_conn = telnetlib.Telnet(router, port)
            # Insert isisd password
            if isisd_pwd:
                telnet_conn.read_until(b'Password: ')
                telnet_conn.write(isisd_pwd.encode('ascii') + b'\r\n')
            # Terminal length set to 0 to not have interruptions
            telnet_conn.write(b'terminal length 0' + b'\r\n')
            # Show information about ISIS node
            telnet_conn.write(b'show isis hostname' + b'\r\n')
            # Exit from the isisd console
            telnet_conn.write(b'q' + b'\r\n')
            # Convert the extracted information to a string
            hostname_details = telnet_conn.read_all().decode('ascii')
        except socket.timeout:
            # Cannot establish a connection to isisd: timeout expired
            logging.error('Error: cannot establish a connection '
                          'to %s on port %s\n', router, port)
        except socket.error as err:
            # Cannot establish a connection to isisd: socket error
            if err.errno != errno.EINTR:
                logger.warning('Cannot establish a connection to %s on port'
                               '%s\n', router, port)
            # Let's try to connect to the next router in the list
            continue
        except BrokenPipeError:
            # Telnetlib returned 'BrokenPipeError'
            # This can happen if you entered the wrong password
            logger.error('Broken pipe. Is the password correct?')
            # Let's try to connect to the next router in the list
            continue
        finally:
            # Close telnet
            telnet_conn.close()
        # ####################################################################
        # Extract router database
        try:
            # Init telnet and try to establish a connection to the router
            telnet_conn = telnetlib.Telnet(router, port)
            # Insert isisd password
            if isisd_pwd:
                telnet_conn.read_until(b'Password: ')
                telnet_conn.write(isisd_pwd.encode('ascii') + b'\r\n')
            # Terminal length set to 0 to not have interruptions
            telnet_conn.write(b'terminal length 0' + b'\r\n')
            # Show the ISIS database globally, with details.
            telnet_conn.write(b'show isis database detail' + b'\r\n')
            # Exit from the isisd console
            telnet_conn.write(b'q' + b'\r\n')
            # Convert the extracted information to a string
            database_details = telnet_conn.read_all().decode('ascii')
        except socket.error:
            # Cannot establish a connection to isisd
            logger.warning('Cannot establish a connection to %s on port %s\n',
                           router, port)
            # Let's try to connect to the next router in the list
            continue
        except BrokenPipeError:
            # Telnetlib returned 'BrokenPipeError'
            # This can happen if you entered the wrong password
            logger.error('Broken pipe. Is the password correct?')
            # Let's try to connect to the next router in the list
            continue
        finally:
            # Close telnet
            telnet_conn.close()
        # ####################################################################
        # Process the extracted information
        #
        # Set of System IDs
        system_ids = set()
        # Set of hostnames
        hostnames = set()
        # Mapping System ID to hostname
        system_id_to_hostname = dict()
        # Mapping hostname to System ID
        hostname_to_system_id = dict()
        # Reachability info dict: it maps each node hostname to the System IDs
        # reachable from it
        reachability_info = dict()
        # IPv6 reachability dict: it maps IPv6 subnet addresses of the edges
        # to the hostnames of the ISIS nodes that are able to reach them
        ipv6_reachability = dict()
        # Process hostnames
        for line in hostname_details.splitlines():
            # Get System ID and hostname
            match = re.search('(\\d+.\\d+.\\d+)\\s+(\\S+)', line)
            if match:
                # Extract System ID
                system_id = match.group(1)
                # Extract hostname
                hostname = match.group(2)
                # Update System IDs
                system_ids.add(system_id)
                # Update hostnames
                hostnames.add(hostname)
                # Update mappings
                system_id_to_hostname[system_id] = hostname
                hostname_to_system_id[hostname] = system_id
        # Process the ISIS database
        for line in database_details.splitlines():
            # Extract the hostname
            match = re.search('Hostname: (\\S+)', line)
            if match:
                # Get the hostname
                hostname = match.group(1)
                # Add the hostname to the reachability info dict
                reachability_info[hostname] = set()
            # Extract the extended reachability
            match = re.search(
                'Extended Reachability: (\\d+.\\d+.\\d+).\\d+', line)
            if match:
                # Get the extended reachability info
                reachability = match.group(1)
                # Add reachability info to the dict
                # We exclude the self reachability information from the dict
                if reachability != hostname_to_system_id[hostname]:
                    reachability_info[hostname].add(reachability)
            # IPv6 Reachability, e.g. fcf0:0:6:8::/64 (Metric: 10)
            match = re.search('IPv6 Reachability: (.+/\\d{1,3})', line)
            if match:
                # Extract the IPv6 address
                ip_addr = match.group(1)
                # If not initialized, init IPv6 reachability
                if ip_addr not in ipv6_reachability:
                    # Add IPv6 address to the IPv6 reachability dict
                    ipv6_reachability[ip_addr] = list()
                # Add the hostname to the hosts list of the ip address in the
                # ipv6 reachability dict
                ipv6_reachability[ip_addr].append(hostname)
        # ####################################################################
        # Build the topology graph
        #
        # Nodes set
        nodes = hostnames
        # Edges set used to store temporary information about the edges
        edges_tmp = set()
        # Edges set, containing tuple (node_left, node_right, ip_address)
        # This set is obtained from the edges_tmp set by adding the IPv6
        # address of the subnet for each edge
        edges = set()
        # Process the reachability info dict and build a temporary set of
        # edges
        for hostname, system_ids in reachability_info.items():
            # 'system_ids' is a list containg all the System IDs that are
            # reachable from 'hostname'
            for system_id in system_ids:
                # Translate System ID to hostname and append the edge to the
                # edges set
                # Each edge is represented as a pair (hostname1, hostname2),
                # where the two hostnames are the endpoints of the edge
                edges_tmp.add((hostname, system_id_to_hostname[system_id]))
        # Process the IPv6 reachability info dict and build an edges set
        # containing the edges (obtained from the edges_tmp set) enriched with
        # the IPv6 addresses of their subnets
        for ip_addr in ipv6_reachability:
            # Edge link is bidirectional in this case
            # Only take IP addresses of links between 2 nodes
            if len(ipv6_reachability[ip_addr]) == 2:
                # Take the edge
                (node1, node2) = ipv6_reachability[ip_addr]
                # Add the IP address of the subnet to the edge and append it to
                # the edges set
                edges.add((node1, node2, ip_addr))
                # Remove the edge from the temporary set
                edges_tmp.remove((node1, node2))
                edges_tmp.remove((node2, node1))
        # For the remaining edges, we don't have IPv6 reachability information
        # Therefore we set their IPv6 addresses to None
        for (node1, node2) in edges_tmp.copy():
            # Add the edge to the edges set
            edges.add((node1, node2, None))
            # Remove the edge from the temporary set
            edges_tmp.remove((node1, node2))
            edges_tmp.remove((node2, node1))
        # If the verbose mode is enabled, print nodes and edges extracted from
        # the ISIS node
        if verbose:
            logger.info('Topology extraction completed\n')
            logger.info('Nodes:', nodes)
            logger.info('Edges:', edges)
            logger.info('***************************************')
        # Return topology information
        return nodes, edges, hostname_to_system_id
    # No router available to extract the topology
    logger.error('No ISIS node is available')
    raise NoISISNodesAvailableError


def topology_information_extraction_isis(routers, period, isisd_pwd,
                                         topo_file_json=None,
                                         nodes_file_yaml=None,
                                         edges_file_yaml=None,
                                         topo_graph=None,
                                         verbose=DEFAULT_VERBOSE):
    '''
    Extract topological information from a set of routers running the
    ISIS protocol. The routers must execute an instance of isisd from the
    routing suite FRRRouting. This function can be also instructed to repeat
    the extraction at regular intervals.
    Optionally the topology can be exported to a JSON file, YAML file or SVG
    image.

    :param routers: A list of pairs ip-port representing IP and port of
                    the ISIS nodes you want to extract the topology from
                    (e.g. ['fcff:1::1-2608', 'fcff:2::1-2608']).
    :type routers: list
    :param period: The interval between two consecutive extractions. If this
                   arguments is equals to 0, this function performs a single
                   extraction and then returns (default: 0).
    :type period: int, optional
    :param isisd_pwd: The password used to log in to isisd.
    :type isisd_pwd: str
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
    # Topology Information Extraction
    while True:
        # Extract the topology information form ISIS
        nodes, edges, node_to_systemid = connect_and_extract_topology_isis(
            routers, isisd_pwd, verbose)
        # Build and export the topology graph
        if topo_file_json is not None or topo_graph is not None:
            # Build topology graph
            graph = build_topo_graph(nodes, edges)
            # Export relevant information of the network graph to a JSON file
            if topo_file_json is not None:
                dump_topo_json(graph, topo_file_json)
            # Export the network graph as an image file
            if topo_graph is not None:
                draw_topo(graph, topo_graph)
        # Export relevant information of the network graph to a YAML file
        if nodes_file_yaml is not None or edges_file_yaml:
            dump_topo_yaml(
                nodes=nodes,
                edges=edges,
                node_to_systemid=node_to_systemid,
                nodes_file_yaml=nodes_file_yaml,
                edges_file_yaml=edges_file_yaml
            )
        # Period = 0 means a single extraction
        if period == 0:
            break
        # Wait 'period' seconds between two extractions
        time.sleep(period)
    # Done, return
    return True


# Parse command line options and dump results
def parse_arguments():
    '''
    Command-line arguments parser
    '''
    # Initialize parser
    parser = ArgumentParser(
        description='Topology Information Extraction (from ISIS) '
        'module for SRv6 Controller'
    )
    # Comma-separated <ip-port> pairs of the routers
    parser.add_argument(
        '-n', '--node-ips', action='store', dest='nodes', required=True,
        help='Comma-separated <ip-port> pairs, where ip is the IP address of '
        'the router and port is the telnet port of the isisd daemon '
        '(e.g. 2000::1-2608,2000::2-2608,2000::3-2608)'
    )
    # Interval between two consecutive extractions
    parser.add_argument(
        '-p', '--period', dest='period', type=int,
        default=DEFAULT_TOPO_EXTRACTION_PERIOD, help='Polling period '
        '(in seconds); a zero value means a single extraction'
    )
    # Path of topology file (JSON file)
    parser.add_argument(
        '-t', '--topology-json', dest='topo_file_json', action='store',
        default=DEFAULT_TOPOLOGY_FILE, help='JSON file of the extracted '
        'topology'
    )
    # Path of nodes file (YAML file)
    parser.add_argument(
        '-r', '--nodes-yaml', dest='nodes_file_yaml', action='store',
        default=DEFAULT_NODES_YAML_FILE,
        help='YAML file of the nodes extracted from the topology'
    )
    # Path of edges file (YAML file)
    parser.add_argument(
        '-e', '--edges-yaml', dest='edges_file_yaml', action='store',
        default=DEFAULT_EDGES_YAML_FILE,
        help='YAML file of the edges extracted from the topology'
    )
    # Path of topology graph (SVG file)
    parser.add_argument(
        '-g', '--topo-graph', dest='topo_graph', action='store', default=None,
        help='Image file of the exported NetworkX graph'
    )
    # Password used to log in to isisd daemon
    parser.add_argument(
        '-w', '--password', action='store_true', dest='password',
        default=DEFAULT_ISISD_PASSWORD, help='Password of the isisd daemon'
    )
    # Debug logs
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Activate debug logs'
    )
    # Verbose mode
    parser.add_argument(
        '-v', '--verbose', action='store_true', dest='verbose',
        default=DEFAULT_VERBOSE, help='Enable verbose mode'
    )
    # Parse input parameters
    args = parser.parse_args()
    # Done, return
    return args


def __main():
    '''
    Entry point for this module
    '''
    # Let's parse input parameters
    args = parse_arguments()
    # Setup properly the logger
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    # Debug settings
    server_debug = logger.getEffectiveLevel() == logging.DEBUG
    logger.info('SERVER_DEBUG: %s', str(server_debug))
    # Get the name of the output JSON file
    topo_file_json = args.topo_file_json
    # Get name of the output YAML file where we want to save the nodes of the
    # extracted topology
    nodes_file_yaml = args.nodes_file_yaml
    # Get name of the output YAML file where we want to save the edges of the
    # extracted topology
    edges_file_yaml = args.edges_file_yaml
    # Get name of the output image file
    # Currently we support only svg format
    topo_graph = args.topo_graph
    if topo_graph is not None and not topo_graph.endswith('.svg'):
        # Add file extension
        topo_graph = '%s.%s' % (topo_graph, 'svg')
    # 'nodes' is a string containtaing comma-separated <ip-port> pairs
    # We need to convert this string to a list by splitting elements
    # separated by commas
    nodes = args.nodes
    nodes = nodes.split(',')
    # Get period between two consecutive extractions
    period = args.period
    # Verbose mode
    verbose = args.verbose
    # Password of isisd
    pwd = args.password
    # Extract the topology and build the network graph
    # If period > 0, this function will block forever or until an exception
    # is raised
    # If period = 0, this function will perform a single topology extraction
    # and then it returns
    topology_information_extraction_isis(
        routers=nodes,
        period=period,
        isisd_pwd=pwd,
        topo_file_json=topo_file_json,
        nodes_file_yaml=nodes_file_yaml,
        edges_file_yaml=edges_file_yaml,
        topo_graph=topo_graph,
        verbose=verbose
    )


if __name__ == '__main__':
    __main()
