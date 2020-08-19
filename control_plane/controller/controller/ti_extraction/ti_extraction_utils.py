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


'''
Topology Information Extraction utilities.
'''

# General imports
import json
import logging
import os
import sys

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
# defined in this module. You can override the default values by passing
# your custom argments to the functions
#
# JSON file containing the exported topology
DEFAULT_TOPOLOGY_FILE = '/tmp/topology.json'
# YAML file containing the exported nodes
DEFAULT_NODES_YAML_FILE = '/tmp/nodes.yaml'
# YAML file containing the exported edges
DEFAULT_EDGES_YAML_FILE = '/tmp/edges.yaml'
# Interval between two consecutive extractions (in seconds)
DEFAULT_TOPO_EXTRACTION_PERIOD = 0
# DOT file containing an intermediate representation of the toplogy used to
# draw the topology graph
DOT_FILE_TOPO_GRAPH = '/tmp/topology.dot'
# Define whether the verbose mode is enabled or not by default
DEFAULT_VERBOSE = False


class OptionalModuleNotLoadedError(Exception):
    '''
    The requested feature depends on an optional module that has not been
    loaded.
    '''


# Utility function to dump relevant information of the topology to a JSON file
def dump_topo_json(graph, topo_file):
    '''
    Export the topology graph to a JSON file.

    :param graph: The graph to be exported.
    :type graph: class: `networkx.Graph`
    :param topo_file: The path and the name of the output JSON file.
    :type topo_file: str
    :return: True.
    :rtype: bool
    :raises OptionalModuleNotLoadedError: The NetworkX module required by
                                          dump_topo_json has not has not been
                                          loaded. Is it installed?
    '''
    # Export the topology to a JSON file
    logger.debug('*** Exporting topology to %s', topo_file)
    # This function depends on the NetworkX library, which is a
    # optional dependency for this script
    #
    # Check if the NetworkX library has been imported
    if 'networkx' not in sys.modules:
        logger.critical('NetworkX library required by dump_topo_json() '
                        'has not been imported. Is it installed?')
        raise OptionalModuleNotLoadedError
    # Export NetworkX object to a json file (json dump of the topology)
    #
    # Convert the graph to a node-link format that is suitable for JSON
    # serialization
    json_topology = json_graph.node_link_data(graph)
    # Remove useless information from the links
    # A link has the following properties:
    #    - source, the source of the link
    #    - target, the destination of the link
    #    - type, the type of the link (i.e. 'core' or 'edge')
    json_topology['links'] = [{
        'source': link['source'],
        'target': link['target'],
        'type': link.get('type')
    } for link in json_topology['links']]
    # Remove useless information from the nodes
    # IP address is unknown because it is not contained in the nodes
    # information, therefore we set it to None
    # You can do post-process on the JSON file to add the IP addresses of the
    # nodes
    # A node has the following properites:
    #    - id, an identifier for the node
    #    - ip_address, for the routers the loopback address, for the hosts the
    #                  the IP address of an interface
    #    - type, the type of the node (i.e. 'router' or 'host')
    #    - ext_reachability, the System ID of the node      # TODO check this!
    json_topology['nodes'] = [{
        'id': node['id'],
        'ip_address': None,
        'type': node.get('type'),
        'ext_reachability': node.get('ext_reachability')
    } for node in json_topology['nodes']]
    # Export the topology to a JSON file
    with open(topo_file, 'w') as outfile:
        json.dump(json_topology, outfile, sort_keys=True, indent=2)
    # Done, return
    logger.info('*** Topology exported\n')
    return True


def dump_topo_yaml(nodes, edges, node_to_systemid=None,
                   nodes_file_yaml=None, edges_file_yaml=None):
    '''
    Export the topology graph to a YAML file and return YAML-like
    representations of the nodes and the edges.

    :param nodes: List of nodes. Each node is represented as a string (e.g.
                  the hostname).
    :type nodes: set
    :param edges: List of edges. The edges are represented as tuples
                  (node_left, node_right, ip_address), where node_left and
                  node_right are the endpoints of the edge and ip_address is
                  the IP address of the subnet associated to the edge.
    :type edges: set
    :param node_to_systemid: A dict mapping hostnames to System IDs. If this
                             argument is not provided, the System ID
                             information is not exported.
    :type node_to_systemid: dict, optional
    :param nodes_file_yaml: The path and the name of the output YAML file
                            containing the nodes. If this argument is not
                            provided, the nodes are not exported to a file.
    :type nodes_file_yaml: str, optional
    :param edges_file_yaml: The path and the name of the output YAML file
                            containing the edges. If this argument is not
                            provided, the edges are not exported to a file.
    :type edges_file_yaml: str, optional
    :return: A pair (nodes, edges), where nodes is a list containing the nodes
             represented as dicts and edges is a list containing the edges
             represented as dicts.
             A node has the following fields:
                 - _key, an identifier for the node
                 - ip_address, for the routers the loopback address, for the
                               hosts the the IP address of an interface
                 - type, the type of the node (i.e. 'router' or 'host')
                 - ext_reachability, the System ID of the node
             A link has the following fields:
                 - _key, an identifier for the edge
                 - _from, the source of the link
                 - _to, the destination of the link
                 - type, the type of the link (i.e. 'core' or 'edge')
    :rtype: tuple
    :raises OptionalModuleNotLoadedError: The pyaml module required by
                                          dump_topo_yaml has not has not been
                                          loaded. Is it installed?
    '''
    # Export the topology to a YAML file
    logger.debug('*** Exporting topology to YAML file')
    # This function depends on the pyaml library, which is a
    # optional dependency for this script
    #
    # Check if the pyaml library has been imported
    if 'pyaml' not in sys.modules:
        logger.critical('pyaml library required by dump_topo_yaml() '
                        'has not been imported. Is it installed?')
        raise OptionalModuleNotLoadedError
    # node_to_systemid is a optional argument
    # If not passed, we init it to an empty dict and the System ID information
    # is not exported
    if node_to_systemid is None:
        node_to_systemid = dict()
    # Export nodes in YAML format
    # A node has the following properites:
    #    - _key, an identifier for the node
    #    - ip_address, for the routers the loopback address, for the hosts the
    #                  the IP address of an interface
    #    - type, the type of the node (i.e. 'router' or 'host')
    #    - ext_reachability, the System ID of the node      # TODO check this!
    # IP address is unknown because it is not contained in the nodes
    # information, therefore we set it to None
    # You can do post-process on the JSON file to add the IP addresses of the
    # nodes
    nodes_yaml = [{
        '_key': node,
        'type': 'router',
        'ip_address': None,
        'ext_reachability': node_to_systemid.get(node)
    } for node in nodes]
    # Write nodes to a YAML file
    if nodes_file_yaml is not None:
        logger.debug('*** Exporting topology nodes to %s', nodes_file_yaml)
        with open(nodes_file_yaml, 'w') as outfile:
            yaml.dump(nodes_yaml, outfile)
    # Export edges in YAML format
    # A link has the following properties:
    #    - _key, an identifier for the edge
    #    - _from, the source of the link
    #    - _to, the destination of the link
    #    - type, the type of the link (i.e. 'core' or 'edge')
    # Character '/' is not accepted in key string in arango, using
    # '-' instead
    # Since the edges are unidirectional, for each link in the graph we need
    # two separate edges
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
    # Write edges to a YAML file
    if edges_file_yaml is not None:
        logger.debug('*** Exporting topology edges to %s', edges_file_yaml)
        with open(edges_file_yaml, 'w') as outfile:
            yaml.dump(edges_yaml, outfile)
    # Done, return a YAML like representation of the nodes and the edges
    # Both nodes and edges are lists of entities containing the properities
    # described in the above comments
    logger.info('Topology exported\n')
    return nodes_yaml, edges_yaml


# Build NetworkX Topology graph
def build_topo_graph(nodes, edges):
    '''
    Take a set of nodes and a set of edges and build a NetworkX topology
    graph.

    :param nodes: List of nodes. Each node is represented as a string (e.g.
                  the hostname).
    :type nodes: set
    :param edges: List of edges. The edges are represented as tuples
                  (node_left, node_right, ip_address), where node_left and
                  node_right are the endpoints of the edge and ip_address is
                  the IP address of the subnet associated to the edge.
    :type edges: set
    :return: The network graph.
    :rtype: class: `networkx.Graph`
    :raises OptionalModuleNotLoadedError: The NetworkX module required by
                                          build_topo_graph has not been
                                          loaded. Is it installed?
    '''
    # This function generates a NetworkX graph starting from a set of nodes
    # and a set of edges
    logger.debug('*** Building topology graph')
    # This function depends on the NetworkX library, which is a
    # optional dependency for this script
    #
    # Check if the NetworkX library has been imported
    if 'networkx' not in sys.modules:
        logger.critical('NetworkX library required by build_topo_graph() '
                        'has not been imported. Is it installed?')
        return None
    # Generate an empty NetworkX graph
    graph = nx.Graph()
    # Add nodes to the graph
    for node in nodes:
        graph.add_node(node)
    # Add edges to the graph
    # Only node_left and node_right are added to the graph, ip_address is
    # ignored
    for edge in edges:
        graph.add_edge(edge[0], edge[1])
    # Return the NetworkX graph
    logger.info('*** Graph builded successfully\n')
    return graph


# Utility function to export the NetworkX graph as an image file
def draw_topo(graph, svg_topo_file, dot_topo_file=DOT_FILE_TOPO_GRAPH):
    '''
    Export the NetworkX graph to a SVG image.

    :param graph: The graph to be exported.
    :type graph: class: `networkx.Graph`
    :param svg_topo_file: The path and the name of the output .svg file.
    :type svg_topo_file: str
    :param dot_topo_file: The path and the name of the .dot file required to
                          draw the graph. This is just a temporary file with
                          containing an intermediate representation of the
                          topology (default: /tmp/topology.dot).
    :type dot_topo_file: str, optional
    :return: True.
    :rtype: bool
    :raises OptionalModuleNotLoadedError: NetworkX or pygraph modules required
                                          by draw_topo has not been loaded.
                                          Are they installed?
    '''
    # This function exports the topology graph as an image file (in svg
    # format)
    logger.debug('*** Saving topology graph image to %s', svg_topo_file)
    # This function depends on the NetworkX and pygraphviz libraries, which
    # are optional dependencies for this script
    #
    # Check if the NetworkX library has been imported
    if 'networkx' not in sys.modules:
        logger.critical('NetworkX library required by draw_topo() '
                        'has not been imported. Is it installed?')
        raise OptionalModuleNotLoadedError
    # Check if the pygraphviz library has been imported
    if 'pygraphviz' not in sys.modules:
        logger.critical('pygraphviz library required by draw_topo() '
                        'has not been imported. Is it installed?')
        raise OptionalModuleNotLoadedError
    # Create dot topology file, an intermediate representation
    # of the topology used to export as an image
    write_dot(graph, dot_topo_file)
    # Convert .dot to .svg
    os.system('dot -Tsvg %s -o %s' % (dot_topo_file, svg_topo_file))
    logger.info('*** Topology exported\n')
    # Done, return
    return True
