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


"""
Topology Information Extraction utilities
"""

# General imports
import errno
import json
import logging
import os
import re
import socket
import sys
import telnetlib
import time
from argparse import ArgumentParser

# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)

# Optional imports:
#     NetworkX      - only required to export the topology in JSON format
#                     and to draw the topology
#     pyaml         - only required to export the topology in YAML format
#     pygraphviz    - only required to export the topology to an image file
try:
    import networkx as nx
    from networkx.drawing.nx_agraph import write_dot
    from networkx.readwrite import json_graph
except ImportError:
    logger.warning('networkx library is not installed')
try:
    from pyaml import yaml
except ImportError:
    logger.warning('pyaml library is not installed')
try:
    import pygraphviz  # pylint: disable=unused-import # noqa: F401
except ImportError:
    logger.warning('pygraphviz library is not installed')


# Global variables definition
#
#
# The following parameters are the default arguments used by the functions
# defined in this module. You can override the default values by providing
# by providing the parameters to the function when you call them
#
# Filename for the exported topology
DEFAULT_TOPOLOGY_FILE = '/tmp/topology.json'
# File containing the nodes
DEFAULT_NODES_YAML_FILE = '/tmp/nodes.yaml'
# File containing the edges
DEFAULT_EDGES_YAML_FILE = '/tmp/edges.yaml'
# Interval between two consecutive extractions (in seconds)
DEFAULT_TOPO_EXTRACTION_PERIOD = 0
# In our experiment we use 'zebra' as default password for isisd
DEFAULT_ISISD_PASSWORD = 'zebra'
# Dot file used to draw the topology graph
DOT_FILE_TOPO_GRAPH = '/tmp/topology.dot'
# Define whether the verbose mode is enabled or not by default
DEFAULT_VERBOSE = False


class OptionalModuleNotLoadedError(Exception):
    """
    The requested feature depends on an optional module that has not been
    loaded
    """


# Utility function to dump relevant information of the topology
def dump_topo_json(graph, topo_file):
    """
    Dump the graph to a JSON file

    :param graph: The graph to be exported
    :type graph: class: `networkx.Graph`
    :param topo_file: The path and the name of the JSON file
    :type topo_file: str
    :return: True
    :rtype: bool
    :raises OptionalModuleNotLoadedError: The NetworkX module required by
                                          dump_topo_json has not has not been
                                          loaded. Is it installed?
    """
    # Export the topology to a JSON file
    logger.debug('*** Exporting topology to %s', topo_file)
    #
    # This function depends on the NetworkX library, which is a
    # optional dependency for this script
    #
    # Check if the NetworkX library has been imported
    if 'networkx' not in sys.modules:
        logger.critical('NetworkX library required by dump_topo_json() '
                        'has not been imported. Is it installed?')
        raise OptionalModuleNotLoadedError
    # Export NetworkX object into a json file (json dump of the topology)
    #
    # Convert the graph to a node-link format that is suitable for JSON
    # serialization
    json_topology = json_graph.node_link_data(graph)
    # Remove useless information from the links
    json_topology['links'] = [{
        'source': link['source'],
        'target': link['target'],
        'type': link.get('type')
    } for link in json_topology['links']]
    # Remove useless information from the nodes
    # IP address is unknown because it is not conrained in the nodes
    # information, so we set it to None
    json_topology['nodes'] = [{
        'id': node['id'],
        'ip_address': None,
        'type': node.get('type'),
        'ext_reachability': node.get('ext_reachability')
    } for node in json_topology['nodes']]
    # Export the topology to a JSON file
    with open(topo_file, 'w') as outfile:
        json.dump(json_topology, outfile, sort_keys=True, indent=2)
    logger.info('*** Topology exported\n')
    return True


def dump_topo_yaml(nodes, edges, node_to_systemid,
                   nodes_file_yaml=None, edges_file_yaml=None):
    """
    Dump the provided set of nodes and edges to a dict representation.
    Optionally, nodes and edges are exported as YAML file
    """
    #
    # This function depends on the pyaml library, which is a
    # optional dependency for this script
    #
    # Check if the pyaml library has been imported
    if 'pyaml' not in sys.modules:
        logger.critical('pyaml library required by dump_topo_yaml() '
                        'has not been imported. Is it installed?')
        return None, None
    # Export nodes in YAML format
    nodes_yaml = [{
        '_key': node,
        'type': 'router',
        'ip_address': None,
        'ext_reachability': node_to_systemid[node]
    } for node in nodes]
    # Write nodes to file
    if nodes_file_yaml is not None:
        logger.info('*** Exporting topology nodes to %s', nodes_file_yaml)
        with open(nodes_file_yaml, 'w') as outfile:
            yaml.dump(nodes_yaml, outfile)
    # Export edges in YAML format
    # Character '/' is not accepted in key strign in arango, using
    # '-' instead
    edges_yaml = [{
        '_key': '%s-dir1' % edge[2].replace('/', '-'),
        '_from': 'nodes/%s' % edge[0],
        '_to': 'nodes/%s' % edge[1],
        'type': 'core'
    } for edge in edges] + [{
        '_key': '%s-dir2' % edge[2].replace('/', '-'),
        '_from': 'nodes/%s' % edge[1],
        '_to': 'nodes/%s' % edge[0],
        'type': 'core'
    } for edge in edges]
    # Write edges to file
    if edges_file_yaml is not None:
        logger.info('*** Exporting topology edges to %s', edges_file_yaml)
        with open(edges_file_yaml, 'w') as outfile:
            yaml.dump(edges_yaml, outfile)
    logger.info('Topology exported\n')
    return nodes_yaml, edges_yaml


def connect_telnet(router, port):
    """
    Establish a telnet connection to a router on a given port
    """
    #
    # Establish a telnet connection to the router
    try:
        # Init telnet
        telnet_conn = telnetlib.Telnet(router, port, 3)
        # Connection established
        return telnet_conn
    except socket.timeout:
        # Timeout expired
        logging.error('Error: cannot establish a connection '
                      'to %s on port %s\n', str(router), str(port))
    except socket.error as err:
        # Socket error
        if err.errno != errno.EINTR:
            logging.error('Error: cannot establish a connection '
                          'to %s on port %s\n', str(router), str(port))
    return None


# Build NetworkX Topology graph
def build_topo_graph(nodes, edges):
    """
    Convert nodes and edges to a NetworkX graph
    """
    #
    # This function depends on the NetworkX library, which is a
    # optional dependency for this script
    #
    # Check if the NetworkX library has been imported
    if 'networkx' not in sys.modules:
        logger.critical('NetworkX library required by build_topo_graph() '
                        'has not been imported. Is it installed?')
        return None
    logger.info('*** Building topology graph')
    # Topology graph
    graph = nx.Graph()
    # Add nodes to the graph
    for node in nodes:
        graph.add_node(node)
    # Add edges to the graph
    for edge in edges:
        graph.add_edge(edge[0], edge[1])
    # Return the networkx graph
    logger.info('Graph builded successfully\n')
    return graph


# Utility function to export the network graph as an image file
def draw_topo(graph, svg_topo_file, dot_topo_file=DOT_FILE_TOPO_GRAPH):
    """
    Export the NetworkX graph to a SVG image
    """
    #
    # This function depends on the NetworkX library, which is a
    # optional dependency for this script
    #
    # Check if the NetworkX library has been imported
    if 'networkx' not in sys.modules:
        logger.critical('NetworkX library required by draw_topo() '
                        'has not been imported. Is it installed?')
        return
    if 'pygraphviz' not in sys.modules:
        logger.critical('pygraphviz library required by dump_topo_yaml() '
                        'has not been imported. Is it installed?')
        return
    # Create dot topology file, an intermediate representation
    # of the topology used to export as an image
    logger.info('*** Saving topology graph image to %s', svg_topo_file)
    write_dot(graph, dot_topo_file)
    os.system('dot -Tsvg %s -o %s' % (dot_topo_file, svg_topo_file))
    logger.info('Topology exported\n')


def connect_and_extract_topology_isis(ips_ports,
                                      isisd_pwd=DEFAULT_ISISD_PASSWORD,
                                      verbose=DEFAULT_VERBOSE):
    """
    Establish a telnet connection to isisd process running on a router
    and extract the network topology from the router
    """
    #
    # pylint: disable=too-many-branches, too-many-locals, too-many-statements
    # ISIS password
    password = isisd_pwd
    # Let's parse the input
    routers = []
    ports = []
    # First create the chunk
    for ip_port in ips_ports:
        # Then parse the chunk
        data = ip_port.split("-")
        routers.append(data[0])
        ports.append(data[1])
    # Connect to a router and extract the topology
    for router, port in zip(routers, ports):
        print("\n********* Connecting to %s-%s *********" % (router, port))
        # Init telnet and try to establish a connection to the router
        try:
            telnet_conn = telnetlib.Telnet(router, port)
        except socket.error:
            print("Error: cannot establish a connection to " +
                  str(router) + " on port " + str(port) + "\n")
            continue
        #
        # Extract router hostnames
        #
        # Insert isisd password
        if password:
            telnet_conn.read_until(b"Password: ")
            telnet_conn.write(password.encode('ascii') + b"\r\n")
        try:
            # terminal length set to 0 to not have interruptions
            telnet_conn.write(b"terminal length 0" + b"\r\n")
            # Get routing info from isisd database
            telnet_conn.write(b"show isis hostname" + b"\r\n")
            # Close
            telnet_conn.write(b"q" + b"\r\n")
            # Get results
            hostname_details = telnet_conn.read_all().decode('ascii')
        except BrokenPipeError:
            logger.error('Broken pipe. Is the password correct?')
            continue
        finally:
            # Close telnet
            telnet_conn.close()
        #
        # Extract router database
        #
        # Init telnet and try to establish a connection to the router
        try:
            telnet_conn = telnetlib.Telnet(router, port)
        except socket.error:
            print("Error: cannot establish a connection to " +
                  str(router) + " on port " + str(port) + "\n")
            continue
        # Insert isisd password
        if password:
            telnet_conn.read_until(b"Password: ")
            telnet_conn.write(password.encode('ascii') + b"\r\n")
        # terminal length set to 0 to not have interruptions
        telnet_conn.write(b"terminal length 0" + b"\r\n")
        # Get routing info from isisd database
        telnet_conn.write(b"show isis database detail" + b"\r\n")
        # Close
        telnet_conn.write(b"q" + b"\r\n")
        # Get results
        database_details = telnet_conn.read_all().decode('ascii')
        # Close telnet
        telnet_conn.close()
        # Set of System IDs
        system_ids = set()
        # Set of hostnames
        hostnames = set()
        # Mapping System ID to hostname
        system_id_to_hostname = dict()
        # Mapping hostname to System ID
        hostname_to_system_id = dict()
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
        # Mapping hostname to reachability
        reachability_info = dict()
        # Process isis database
        hostname = None
        # IPv6 subnet addresses of edges
        ipv6_reachability = dict()
        for line in database_details.splitlines():
            # Get hostname
            match = re.search('Hostname: (\\S+)', line)
            if match:
                # Extract hostname
                hostname = match.group(1)
                # Update reachability info dict
                reachability_info[hostname] = set()
            # Get extended reachability
            match = re.search(
                'Extended Reachability: (\\d+.\\d+.\\d+).\\d+', line)
            if match:
                # Extract extended reachability info
                reachability = match.group(1)
                # Update reachability info dict
                if reachability != hostname_to_system_id[hostname]:
                    reachability_info[hostname].add(reachability)
            #   IPv6 Reachability: fcf0:0:6:8::/64 (Metric: 10)
            match = re.search('IPv6 Reachability: (.+/\\d{1,3})', line)
            if match:
                ip_addr = match.group(1)
                if ip_addr not in ipv6_reachability:
                    # Update IPv6 reachability dict
                    ipv6_reachability[ip_addr] = list()
                # add hostname to hosts list of the ip address in the ipv6
                # reachability dict
                ipv6_reachability[ip_addr].append(hostname)
        # Build the topology graph
        #
        # Nodes
        nodes = hostnames
        # Edges
        _edges = set()
        # Edges with subnet IP address
        edges = set()
        for hostname, system_ids in reachability_info.items():
            for system_id in system_ids:
                _edges.add((hostname, system_id_to_hostname[system_id]))
        for ip_addr in ipv6_reachability:
            # Edge link is bidirectional in this case
            # Only take IP addresses of links between 2 nodes
            if len(ipv6_reachability[ip_addr]) == 2:
                (node1, node2) = ipv6_reachability[ip_addr]
                edges.add((node1, node2, ip_addr))
                _edges.remove((node1, node2))
                _edges.remove((node2, node1))
        for (node1, node2) in _edges.copy():
            edges.add((node1, node2, None))
            _edges.remove((node1, node2))
            _edges.remove((node2, node1))
        # Print nodes and edges
        if verbose:
            print('Topology extraction completed\n')
            print("Nodes:", nodes)
            print("Edges:", edges)
            print("***************************************")
        # Return topology information
        return nodes, edges, hostname_to_system_id
    # No router available to extract the topology
    return None, None, None


def topology_information_extraction_isis(routers, period, isisd_pwd,
                                         topo_file_json=None,
                                         nodes_file_yaml=None,
                                         edges_file_yaml=None,
                                         topo_graph=None,
                                         verbose=DEFAULT_VERBOSE):
    """
    Run Topology Information Extraction from a set of routers.
    Optionally export the topology to a JSON file, YAML file or SVG image
    """
    #
    # pylint: disable=too-many-arguments
    # Topology Information Extraction
    while True:
        # Extract the topology information
        nodes, edges, node_to_systemid = \
            connect_and_extract_topology_isis(
                routers, isisd_pwd, verbose)
        # Build and export the topology graph
        if topo_file_json is not None or topo_graph is not None:
            # Builg topology graph
            graph = build_topo_graph(nodes, edges)
            # Dump relevant information of the network graph to a JSON file
            if topo_file_json is not None:
                dump_topo_json(graph, topo_file_json)
            # Export the network graph as an image file
            if topo_graph is not None:
                draw_topo(graph, topo_graph)
        # Dump relevant information of the network graph to a YAML file
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


# Parse command line options and dump results
def parse_arguments():
    """
    Command-line arguments parser
    """
    # Initialize parser
    parser = ArgumentParser(
        description='Topology Information Extraction (from ISIS) '
        'module for SRv6 Controller'
    )
    # ip:port of the routers
    parser.add_argument(
        '-n', '--node-ips', action='store', dest='nodes', required=True,
        help='Comma-separated <ip-port> pairs, where ip is the IP address of '
        'the router and port is the telnet port of the isisd daemon '
        '(e.g. 2000::1-2606,2000::2-2606,2000::3-2606)'
    )
    # Topology Information Extraction period
    parser.add_argument(
        '-p', '--period', dest='period', type=int,
        default=DEFAULT_TOPO_EXTRACTION_PERIOD, help='Polling period '
        '(in seconds); a zero value means a single extraction'
    )
    # Path of topology file (JSON)
    parser.add_argument(
        '-t', '--topology-json', dest='topo_file_json', action='store',
        default=DEFAULT_TOPOLOGY_FILE, help='JSON file of the extracted '
        'topology'
    )
    # Path of nodes file (YAML)
    parser.add_argument(
        '-r', '--nodes-yaml', dest='nodes_file_yaml', action='store',
        default=DEFAULT_NODES_YAML_FILE,
        help='YAML file of the nodes extracted from the topology'
    )
    # Path of edges file (YAML)
    parser.add_argument(
        '-e', '--edges-yaml', dest='edges_file_yaml', action='store',
        default=DEFAULT_EDGES_YAML_FILE,
        help='JSON file of the edges extracted from the topology'
    )
    # Path of topology graph
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
    """
    Entry point for this module
    """
    #
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
    # Get topology filename JSON
    topo_file_json = args.topo_file_json
    # Get nodes filename YAML
    nodes_file_yaml = args.nodes_file_yaml
    # Get edges filename YAML
    edges_file_yaml = args.edges_file_yaml
    # Get topology graph image filename
    topo_graph = args.topo_graph
    if topo_graph is not None and \
            not topo_graph.endswith('.svg'):
        # Add file extension
        topo_graph = '%s.%s' % (topo_graph, 'svg')
    # Nodes
    nodes = args.nodes
    nodes = nodes.split(',')
    # Get period between two extractions
    period = args.period
    # Verbose mode
    verbose = args.verbose
    # isisd password
    pwd = args.password
    # Extract topology and build network graph
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
