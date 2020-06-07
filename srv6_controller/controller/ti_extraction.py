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
# Topology information extraction
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


from argparse import ArgumentParser
import errno
import logging
import json
import os
import time
import threading
import telnetlib
import re
import socket
import sys
from optparse import OptionParser

# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)

# Optional imports:
#     NetworkX - only required to export the topology in JSON format
#                and to draw the topology
#     pyaml    - only required to export the topology in YAML format
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


# Global variables definition
#
#
# Default topology file
DEFAULT_TOPOLOGY_FILE = '/tmp/topology.json'
# Default nodes file
DEFAULT_NODES_YAML_FILE = '/tmp/nodes.yaml'
# Default edges file
DEFAULT_EDGES_YAML_FILE = '/tmp/edges.yaml'
# Interval between two consecutive extractions (in seconds)
DEFAULT_TOPO_EXTRACTION_PERIOD = 0
# In our experiment we use 'zebra' as default password
DEFAULT_ISISD_PASSWORD = 'zebra'
# Dot file used to draw topology graph
DOT_FILE_TOPO_GRAPH = '/tmp/topology.dot'
# Define whether the verbose mode is enabled or not by default
DEFAULT_VERBOSE = False


# Utility function to dump relevant information of the topology
def dump_topo_json(G, topo_file):
    # This function depends on the NetworkX library, which is a
    # optional dependency for this script
    #
    # Check if the NetworkX library has been imported
    if 'networkx' not in sys.modules:
        logger.critical('NetworkX library required by dump_topo_json()'
                        'has not been imported. Is it installed?')
        return
    # Export NetworkX object into a json file
    # Json dump of the topology
    #
    # Get json topology
    json_topology = json_graph.node_link_data(G)
    # Convert links
    json_topology['links'] = [{
        'source': link['source'],
        'target': link['target'],
        'type': link.get('type')
    } for link in json_topology['links']]
    # Convert nodes
    json_topology['nodes'] = [{
        'id': node['id'],
        'ip_address': None,
        'type': node.get('type'),
        'ext_reachability': node.get('ext_reachability')
    } for node in json_topology['nodes']]
    # Dump the topology
    logger.info('*** Exporting topology to %s' % topo_file)
    with open(topo_file, 'w') as outfile:
        json.dump(json_topology, outfile, sort_keys=True, indent=2)
    logger.info('Topology exported\n')


def dump_topo_yaml(nodes, edges, node_to_systemid, nodes_file_yaml=None, edges_file_yaml=None):
    # This function depends on the pyaml library, which is a
    # optional dependency for this script
    #
    # Check if the pyaml library has been imported
    if 'pyaml' not in sys.modules:
        logger.critical('pyaml library required by dump_topo_yaml()'
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
        logger.info('*** Exporting topology nodes to %s' % nodes_file_yaml)
        with open(nodes_file_yaml, 'w') as outfile:
            yaml.dump(nodes_yaml, outfile)
    # Export edges in YAML format
    edges_yaml = [{
        '_from': 'nodes/%s' % edge[0],
        '_to': 'nodes/%s' % edge[1],
        'type': 'core'
    } for edge in edges]
    # Write edges to file
    if edges_file_yaml is not None:
        logger.info('*** Exporting topology edges to %s' % edges_file_yaml)
        with open(edges_file_yaml, 'w') as outfile:
            yaml.dump(edges_yaml, outfile)
    logger.info('Topology exported\n')
    return nodes_yaml, edges_yaml


# to be used with edges collection containing ip addresses
def dump_topo_yaml_edges_ip(nodes, edges, node_to_systemid, nodes_file_yaml=None, edges_file_yaml=None):
    # This function depends on the pyaml library, which is a
    # optional dependency for this script
    #
    # Check if the pyaml library has been imported
    if 'pyaml' not in sys.modules:
        logger.critical('pyaml library required by dump_topo_yaml()'
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
        logger.info('*** Exporting topology nodes to %s' % nodes_file_yaml)
        with open(nodes_file_yaml, 'w') as outfile:
            yaml.dump(nodes_yaml, outfile)
    # Export edges in YAML format
    edges_yaml = list()
    for edge in edges:
        edges_yaml.append({
                '_key': '%s-dir1' % edge[0],
                '_from': 'nodes/%s' % edge[1],
                '_to': 'nodes/%s' % edge[2],
                'type': 'core'
            })
        edges_yaml.append({
                '_key': '%s-dir2' % edge[0],
                '_from': 'nodes/%s' % edge[2],
                '_to': 'nodes/%s' % edge[1],
                'type': 'core'
            })
    if edges_file_yaml is not None:
        logger.info('*** Exporting topology edges to %s' % edges_file_yaml)
        with open(edges_file_yaml, 'w') as outfile:
            yaml.dump(edges_yaml, outfile)
    logger.info('Topology exported\n')
    return nodes_yaml, edges_yaml


def connect_telnet(router, port):
    # Establish a telnet connection to the router
    try:
        # Init telnet
        tn = telnetlib.Telnet(router, port, 3)
        # Connection established
        return tn
    except socket.timeout:
        # Timeout expired
        logging.error('Error: cannot establish a connection '
                      'to %s on port %s\n' % (str(router), str(port)))
    except socket.error as e:
        # Socket error
        if e.errno != errno.EINTR:
            logging.error('Error: cannot establish a connection '
                          'to %s on port %s\n' % (str(router), str(port)))
    return None


# Build NetworkX Topology graph
def build_topo_graph(nodes, edges):
    # This function depends on the NetworkX library, which is a
    # optional dependency for this script
    #
    # Check if the NetworkX library has been imported
    if 'networkx' not in sys.modules:
        logger.critical('NetworkX library required by build_topo_graph()'
                        'has not been imported. Is it installed?')
        return
    logger.info('*** Building topology graph')
    # Topology graph
    G = nx.Graph()
    # Add nodes to the graph
    for node in nodes:
        G.add_node(node)
    # Add edges to the graph
    for edge in edges:
        G.add_edge(*edge)
    # Return the networkx graph
    logger.info('Graph builded successfully\n')
    return G


# Utility function to export the network graph as an image file
def draw_topo(G, svg_topo_file, dot_topo_file=DOT_FILE_TOPO_GRAPH):
    # This function depends on the NetworkX library, which is a
    # optional dependency for this script
    #
    # Check if the NetworkX library has been imported
    if 'networkx' not in sys.modules:
        logger.critical('NetworkX library required by draw_topo()'
                        'has not been imported. Is it installed?')
        return
    # Create dot topology file, an intermediate representation
    # of the topology used to export as an image
    logger.info('*** Saving topology graph image to %s' % svg_topo_file)
    write_dot(G, dot_topo_file)
    os.system('dot -Tsvg %s -o %s' % (dot_topo_file, svg_topo_file))
    logger.info('Topology exported\n')


def connect_and_extract_topology_isis(ips_ports,
                                      isisd_pwd=DEFAULT_ISISD_PASSWORD,
                                      verbose=DEFAULT_VERBOSE):
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
            tn = telnetlib.Telnet(router, port)
        except socket.error:
            print("Error: cannot establish a connection to " +
                  str(router) + " on port " + str(port) + "\n")
            continue
        #
        # Extract router hostnames
        #
        # Insert isisd password
        if password:
            tn.read_until(b"Password: ")
            tn.write(password.encode('ascii') + b"\r\n")
        # terminal length set to 0 to not have interruptions
        tn.write(b"terminal length 0" + b"\r\n")
        # Get routing info from isisd database
        tn.write(b"show isis hostname" + b"\r\n")
        # Close
        tn.write(b"q" + b"\r\n")
        # Get results
        hostname_details = tn.read_all().decode('ascii')
        # Close telnet
        tn.close()
        #
        # Extract router database
        #
        # Init telnet and try to establish a connection to the router
        try:
            tn = telnetlib.Telnet(router, port)
        except socket.error:
            print("Error: cannot establish a connection to " +
                  str(router) + " on port " + str(port) + "\n")
            continue
        # Insert isisd password
        if password:
            tn.read_until(b"Password: ")
            tn.write(password.encode('ascii') + b"\r\n")
        # terminal length set to 0 to not have interruptions
        tn.write(b"terminal length 0" + b"\r\n")
        # Get routing info from isisd database
        tn.write(b"show isis database detail" + b"\r\n")
        # Close
        tn.write(b"q" + b"\r\n")
        # Get results
        database_details = tn.read_all().decode('ascii')
        # Close telnet
        tn.close()
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
            m = re.search('(\\d+.\\d+.\\d+)\\s+(\\S+)', line)
            if(m):
                # Extract System ID
                system_id = m.group(1)
                # Extract hostname
                hostname = m.group(2)
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
            m = re.search('Hostname: (\S+)', line)
            if (m):
                # Extract hostname
                hostname = m.group(1)
                # Update reachability info dict
                reachability_info[hostname] = set()
            # Get extended reachability
            m = re.search('Extended Reachability: (\\d+.\\d+.\\d+).\\d+', line)
            if(m):
                # Extract extended reachability info
                reachability = m.group(1)
                # Update reachability info dict
                if reachability != hostname_to_system_id[hostname]:
                    reachability_info[hostname].add(reachability)

            #   IPv6 Reachability: fcf0:0:6:8::/64 (Metric: 10)
            m = re.search('IPv6 Reachability: (.+/\\d{1,3})', line)
            if(m):
                ip_add = m.group(1)
                if ip_add not in ipv6_reachability:
                    # Update IPv6 reachability dict
                    ipv6_reachability[ip_add] = list()
                # add hostname to hosts list of the ip address in the ipv6 reachability dict
                ipv6_reachability[ip_add].append(hostname)

        # Build the topology graph
        #
        # Nodes
        nodes = hostnames
        # Edges
        edges = set()
        # Edges with subnet IP address
        edges_ip = set()
        for hostname, system_ids in reachability_info.items():
            for system_id in system_ids:
                edges.add((hostname, system_id_to_hostname[system_id]))
        for ip_add in ipv6_reachability:
            # Edge link is bidirectional in this case
            if len(ipv6_reachability[ip_add]) == 2:     # Only take IP addresses of links between 2 nodes
                (node1, node2) = ipv6_reachability[ip_add]
                ip_add_key = ip_add.replace('/','-')    # Character '/' is not accepted in key strign in arango, using '-' instead
                edges_ip.add((ip_add_key, node1, node2))
        # Print nodes and edges
        if verbose:
            print('Topology extraction completed\n')
            print("Nodes:", nodes)
            print("Edges:", edges)
            print("Edges with IP address:", edges_ip)
            print("***************************************")
        # Return topology information
        return nodes, edges, hostname_to_system_id, edges_ip
    # No router available to extract the topology
    return None, None, None


def topology_information_extraction_isis(routers, period, isisd_pwd,
                                         topo_file_json=None, nodes_file_yaml=None, edges_file_yaml=None,
                                         topo_graph=None, verbose=DEFAULT_VERBOSE):
    # Topology Information Extraction
    while (True):
        # Extract the topology information
        nodes, edges, node_to_systemid, edges_ip = \
            connect_and_extract_topology_isis(
                routers, isisd_pwd, period, verbose)
        # Build and export the topology graph
        if topo_file_json is not None or topo_graph is not None:
            # Builg topology graph
            G = build_topo_graph(nodes, edges)
            # Dump relevant information of the network graph to a JSON file
            if topo_file_json is not None:
                dump_topo_json(G, topo_file_json)
            # Export the network graph as an image file
            if topo_graph is not None:
                draw_topo(G, topo_graph)
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
def parseArguments():
    parser = ArgumentParser(
        description='Topology Information Ex+traction (from ISIS) module for SRv6 '
        'Controller'
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
        default=DEFAULT_TOPO_EXTRACTION_PERIOD,
        help='Polling period (in seconds); a zero value means a single extraction'
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
        default=DEFAULT_NODES_YAML_FILE, help='YAML file of the nodes extracted '
        'from the topology'
    )
    # Path of edges file (YAML)
    parser.add_argument(
        '-e', '--edges-yaml', dest='edges_file_yaml', action='store',
        default=DEFAULT_EDGES_YAML_FILE, help='JSON file of the edges extracted '
        'from the topology'
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


if __name__ == '__main__':
    global verbose
    # Let's parse input parameters
    args = parseArguments()
    # Setup properly the logger
    if args.debug:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.INFO)
    # Debug settings
    server_debug = logger.getEffectiveLevel() == logging.DEBUG
    logger.info('SERVER_DEBUG:' + str(server_debug))
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
