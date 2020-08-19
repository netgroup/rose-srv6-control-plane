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
# ArangoDB utils
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
ArangoDB utilities.
'''

# General imports
import ipaddress
import logging
import time

from pyaml import yaml

# Import topology extraction utility functions
from controller.ti_extraction_isis import connect_and_extract_topology_isis
from controller.ti_extraction_utils import dump_topo_yaml
# DB update modules
from db_update import arango_db

# Global variables definition
#
# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)


class TopologyInformationExtractionError(Exception):
    '''
    An error occurred while attempting to extract the network topology.
    '''


def save_yaml_dump(obj, filename):
    '''
    Export an object to a YAML file.

    :param obj: The object to export.
    :type obj: list or dict
    :param filename: The path and the name of the output file.
    :type filename: str
    :return: True.
    :rtype: bool
    '''
    # Export the object to a YAML file
    with open(filename, 'w') as outfile:
        yaml.dump(obj, outfile)
    # Done, return
    return True


def load_yaml_dump(filename):
    '''
    Load a YAML file and return a list or dict representation.

    :param filename: The path and the name of the input file.
    :type filename: str
    :return: A list or dict containing the information extracted from the
             file.
    :rtype: list or dict
    '''
    # Load YAML file
    with open(filename, 'r') as infile:
        return yaml.safe_load(infile)


def fill_ip_addresses(nodes, addresses_yaml):
    '''
    Read the IP addresses of the nodes from a YAML file and add the addresses
    to a nodes list. The matching between the addresses and the nodes is based
    on the nodes key which acts as node identifier.

    :param nodes: List containing the nodes. Each node is represented as dict.
    :type nodes: list
    :param addresses_yaml: The path and name of the input YAML file.
    :type addresses_yaml: str
    :return: The list of the nodes enriched with the IP addresses read from the
             YAML file.
    :rtype: list
    '''
    # Read IP addresses information from a YAML file and add addresses to the
    # nodes
    logger.debug('*** Filling nodes YAML file with IP addresses')
    # Open addresses file
    with open(addresses_yaml, 'r') as infile:
        addresses = yaml.safe_load(infile.read())
    # Parse addresses and build mapping node to address
    node_to_addr = dict()
    for addr in addresses:
        node_to_addr[addr['node']] = addr['ip_address']
    # Fill addresses
    for node in nodes:
        # Update the dict
        node['ip_address'] = node_to_addr[node['_key']]
    logger.info('*** Nodes YAML updated\n')
    # Return the updated nodes list
    return nodes


def add_hosts(nodes, edges, hosts_yaml):
    '''
    Read the hosts from a YAML file and add them to a topology. Topology is
    expressed through its nodes and edges.

    :param nodes: List containing the nodes. Each node is represented as dict.
    :type nodes: list
    :param edges: List containing the edges. Each edge is represented as dict.
    :type edges: list
    :param hosts_yaml: The path and name of the input YAML file.
    :type hosts_yaml: str
    :return: Tuple containing the list of nodes and edges enriched with the
             hosts contained in the YAML file.
    :rtype: tuple
    '''
    # Read hosts information from a YAML file and add hosts to the nodes and
    # edges lists
    logger.debug('*** Adding hosts to the topology')
    # Open hosts file
    with open(hosts_yaml, 'r') as infile:
        hosts = yaml.safe_load(infile.read())
    # Add hosts and links
    for host in hosts:
        # Add host to the nodes list
        nodes.append({
            '_key': host['name'],
            'type': 'host',
            'ip_address': host['ip_address']
        })
        # Get the subnet
        net = str(ipaddress.ip_network(host['ip_address'], strict=False))
        # Add edge (host to router)
        # Character '/' is not accepted in key strign in arango, using
        # '-' instead
        edges.append({
            '_key': '%s-dir1' % net.replace('/', '-'),
            '_from': 'nodes/%s' % host['name'],
            '_to': 'nodes/%s' % host['gw'],
            'type': 'edge'
        })
        # Add edge (router to host)
        # This is required because we work with
        # unidirectional edges
        edges.append({
            '_key': '%s-dir2' % net.replace('/', '-'),
            '_to': 'nodes/%s' % host['gw'],
            '_from': 'nodes/%s' % host['name'],
            'type': 'edge'
        })
    # Return the updated nodes and edges lists
    logger.info('*** Nodes YAML updated\n')
    logger.info('*** Edges YAML updated\n')
    return nodes, edges


def initialize_db(arango_url, arango_user, arango_password, verbose=False):
    '''
    Initialize database.

    :param arango_url: The URL of the ArangoDB.
    :type arango_url: str
    :param arango_user: The username used to access the ArangoDB.
    :type arango_user: str
    :param arango_password: The password used to access the ArangoDB.
    :type arango_password: str
    :param verbose: Define whether to enable the verbose mode or not
                    (default: False).
    :type verbose: bool, optional
    :return: A tuple containing the nodes collection and the edges collection.
    :rtype: tuple
    '''
    # pylint: disable=unused-argument
    #
    # Wrapper function
    return arango_db.initialize_db(
        arango_url=arango_url,
        arango_user=arango_user,
        arango_password=arango_password
    )


def extract_topo_from_isis(isis_nodes, isisd_pwd,
                           nodes_yaml=None, edges_yaml=None,
                           addrs_yaml=None, hosts_yaml=None, verbose=False):
    '''
    Extract the network topology from a set of nodes running ISIS protocol.
    The extracted topology can be exported to a YAML file (two separate YAML
    files for nodes and edges). Optionally, you can enrich the extracted
    topology with IP addresses and other hosts by creating your own addresses
    and hosts YAML files.

    :param isis_nodes: A list of pairs ip-port representing IP and port of
                       the ISIS nodes you want to extract the topology from
                       (e.g. ['fcff:1::1-2608', 'fcff:2::1-2608']).
    :type isis_nodes: list
    :param isisd_pwd: The password used to log in to isisd.
    :type isisd_pwd: str
    :param nodes_yaml: The path and the name of the output YAML file
                       containing the nodes. If this parameter is not
                       provided, the nodes are not exported to a YAML file
                       (default: None).
    :type nodes_yaml: str, optional
    :param edges_yaml: The path and the name of the output YAML file
                       containing the edges. If this parameter is not
                       provided, the edges are not exported to a YAML file
                       (default: None).
    :type edges_yaml: str, optional
    :param addrs_yaml: The path and the name of the YAML file containing the
                       addresses of the nodes. If this argument is not passed,
                       the addresses are not added to the exported topology.
    :type addrs_yaml: str, optional
    :param hosts_yaml: The path and the name of the YAML file containing the
                       hosts. If this argument is not passed, the hosts are
                       not added to the exported topology.
    :type hosts_yaml: str, optional
    :param verbose: Define whether to enable the verbose mode or not
                    (default: False).
    :type verbose: bool, optional
    :raises controller.db_utils.arangodb.arangodb_utils  \\
            .TopologyInformationExtractionError: Error while attempting to
                                                extract the topology.
    '''
    # pylint: disable=too-many-arguments
    #
    # Param isis_nodes: list of ip-port
    # (e.g. [2000::1-2608,2000::2-2608])
    #
    # Connect to a node and extract the topology
    nodes, edges, node_to_systemid = connect_and_extract_topology_isis(
        ips_ports=isis_nodes,
        isisd_pwd=isisd_pwd,
        verbose=verbose
    )
    if nodes is None or edges is None or node_to_systemid is None:
        logger.error('Cannot extract topology')
        raise TopologyInformationExtractionError
    # Export the topology in YAML format
    nodes, edges = dump_topo_yaml(
        nodes=nodes,
        edges=edges,
        node_to_systemid=node_to_systemid
    )
    # Add IP addresses information
    if addrs_yaml is not None:
        fill_ip_addresses(nodes, addrs_yaml)
    # Add hosts information
    if hosts_yaml is not None:
        # add_hosts(nodes, edges, hosts_yaml)
        add_hosts(nodes, edges, hosts_yaml)
    # Save nodes YAML file
    if nodes_yaml is not None:
        save_yaml_dump(nodes, nodes_yaml)
    # Save edges YAML file
    if edges_yaml is not None:
        save_yaml_dump(edges, edges_yaml)
    # Done, return
    return True


def load_topo_on_arango(arango_url, user, password,
                        nodes, edges,
                        nodes_collection, edges_collection,
                        verbose=False):
    '''
    Load a network topology on a database.

    :param arango_url: The URL of the ArangoDB.
    :type arango_url: str
    :param user: The username used to access the ArangoDB.
    :type user: str
    :param password: The password used to access the ArangoDB.
    :type password: str
    :param nodes: Set of nodes.
    :type nodes: set
    :param edges: Set of edges.
    :type edges: set
    :param nodes_collection: Collection of nodes.
    :type nodes_collection: arango.collection.StandardCollection
    :param edges_collection: Collection of edges.
    :type edges_collection: arango.collection.StandardCollection
    :param verbose: Define whether to enable the verbose mode or not
                    (default: False).
    :type verbose: bool, optional
    :return: True.
    :rtype: bool
    '''
    # Current Arango arguments are not used,
    # so we can skip the check
    # pylint: disable=unused-argument, too-many-arguments
    #
    # Load the topology on Arango DB
    arango_db.populate2(
        nodes=nodes_collection,
        edges=edges_collection,
        nodes_dict=nodes,
        edges_dict=edges
    )
    # Done, return
    return True


def extract_topo_from_isis_and_load_on_arango(isis_nodes, isisd_pwd,
                                              arango_url=None,
                                              arango_user=None,
                                              arango_password=None,
                                              nodes_yaml=None, edges_yaml=None,
                                              addrs_yaml=None, hosts_yaml=None,
                                              period=0, verbose=False):
    '''
    Extract the network topology from a set of nodes running ISIS protocol
    and upload it on a database. The extracted topology can be exported to a
    YAML file (two separate YAML files for nodes and edges). Optionally, you
    can enrich the extracted topology with IP addresses and other hosts by
    creating your own addresses and hosts YAML files.

    :param isis_nodes: A list of pairs ip-port representing IP and port of
                       the ISIS nodes you want to extract the topology from
                       (e.g. ['fcff:1::1-2608', 'fcff:2::1-2608']).
    :type isis_nodes: list
    :param isisd_pwd: The password used to log in to isisd.
    :type isisd_pwd: str
    :param arango_url: The URL of the ArangoDB.
    :type arango_url: str
    :param arango_user: The username used to access the ArangoDB.
    :type arango_user: str
    :param arango_password: The password used to access the ArangoDB.
    :type arango_password: str
    :param nodes_yaml: The path and the name of the output YAML file
                       containing the nodes. If this parameter is not
                       provided, the nodes are not exported to a YAML file
                       (default: None).
    :type nodes_yaml: str, optional
    :param edges_yaml: The path and the name of the output YAML file
                       containing the edges. If this parameter is not
                       provided, the edges are not exported to a YAML file
                       (default: None).
    :type edges_yaml: str, optional
    :param addrs_yaml: The path and the name of the YAML file containing the
                       addresses of the nodes. If this argument is not passed,
                       the addresses are not added to the exported topology.
    :type addrs_yaml: str, optional
    :param hosts_yaml: The path and the name of the YAML file containing the
                       hosts. If this argument is not passed, the hosts are
                       not added to the exported topology.
    :type hosts_yaml: str, optional
    :param period: The interval between two consecutive extractions. If this
                   arguments is equals to 0, this function performs a single
                   extraction and then returns (default: 0).
    :type period: int, optional
    :param verbose: Define whether to enable the verbose mode or not
                    (default: False).
    :type verbose: bool, optional
    :return: True.
    :rtype: bool
    '''
    # pylint: disable=too-many-arguments, too-many-locals
    #
    # Param isis_nodes: list of ip-port
    # (e.g. [2000::1-2608,2000::2-2608])
    #
    # Topology Information Extraction
    #
    # Initialize database
    if arango_url is not None and arango_user is not None and \
            arango_password is not None:
        nodes_collection, edges_collection = arango_db.initialize_db(
            arango_url=arango_url,
            arango_user=arango_user,
            arango_password=arango_password
        )
    while True:
        # Connect to a node and extract the topology
        nodes, edges, node_to_systemid = connect_and_extract_topology_isis(
            ips_ports=isis_nodes,
            isisd_pwd=isisd_pwd,
            verbose=verbose
        )
        if nodes is None or edges is None or node_to_systemid is None:
            logger.error('Cannot extract topology')
        else:
            logger.info('Topology extracted')
            # Export the topology in YAML format
            # This function returns a representation of nodes and
            # edges ready to get uploaded on ArangoDB.
            # Optionally, the nodes and the edges are exported in
            # YAML format, if 'nodes_yaml' and 'edges_yaml' variables
            # are not None
            nodes, edges = dump_topo_yaml(
                nodes=nodes,
                edges=edges,
                node_to_systemid=node_to_systemid
            )
            # Add IP addresses information
            if addrs_yaml is not None:
                fill_ip_addresses(nodes, addrs_yaml)
            # Add hosts information
            if hosts_yaml is not None:
                # add_hosts(nodes, edges, hosts_yaml)
                add_hosts(nodes, edges, hosts_yaml)
            # Save nodes YAML file
            if nodes_yaml is not None:
                save_yaml_dump(nodes, nodes_yaml)
            # Save edges YAML file
            if edges_yaml is not None:
                save_yaml_dump(edges, edges_yaml)
            # Load the topology on Arango DB
            if arango_url is not None and \
                    arango_user is not None and arango_password is not None:
                load_topo_on_arango(
                    arango_url=arango_url,
                    user=arango_user,
                    password=arango_password,
                    nodes=nodes,
                    edges=edges,
                    nodes_collection=nodes_collection,
                    edges_collection=edges_collection,
                    verbose=verbose
                )
        # Period = 0 means a single extraction
        if period == 0:
            break
        # Wait 'period' seconds between two extractions
        time.sleep(period)
    # Done, return
    return True
