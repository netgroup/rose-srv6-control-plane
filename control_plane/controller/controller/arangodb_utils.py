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
# ArangoDB utils
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


# General imports
import logging
import time
from pyaml import yaml

# Import topology extraction utility functions
from controller.ti_extraction import connect_and_extract_topology_isis
from controller.ti_extraction import dump_topo_yaml
# DB update modules
from db_update import arango_db


# Global variables definition
#
# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)


def save_yaml_dump(obj, filename):
    # Save file
    with open(filename, 'w') as outfile:
        yaml.dump(obj, outfile)


def load_yaml_dump(filename):
    # Load YAML file
    with open(filename, 'r') as infile:
        return yaml.safe_load(infile)


def fill_ip_addresses(nodes, addresses_yaml):
    # Read IP addresses information from a YAML file and
    # add addresses to the nodes
    logger.info('*** Filling nodes YAML file with IP addresses')
    # Open hosts file
    with open(addresses_yaml, 'r') as infile:
        addresses = yaml.safe_load(infile.read())
    # Parse addresses
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
    # Read hosts information from a YAML file and
    # add hosts to the nodes and edges lists
    logger.info('*** Adding hosts to the topology')
    # Open hosts file
    with open(hosts_yaml, 'r') as infile:
        hosts = yaml.safe_load(infile.read())
    # Add hosts and links
    for host in hosts:
        # Add host
        nodes.append({
            '_key': host['name'],
            'type': 'host',
            'ip_address': host['ip_address']
        })
        # Add edge (host to router)
        edges.append({
            '_key': '%s-dir1' % host['ip_address'].replace('/', '-'),
            '_from': 'nodes/%s' % host['name'],
            '_to': 'nodes/%s' % host['gw'],
            'type': 'edge'
        })
        # Add edge (router to host)
        # This is required because we work with
        # unidirectional edges
        edges.append({
            '_key': '%s-dir2' % host['ip_address'].replace('/', '-'),
            '_to': 'nodes/%s' % host['gw'],
            '_from': 'nodes/%s' % host['name'],
            'type': 'edge'
        })
    logger.info('*** Nodes YAML updated\n')
    logger.info('*** Edges YAML updated\n')
    # Return the updated nodes and edges lists
    return nodes, edges


def initialize_db(arango_url, arango_user, arango_password, verbose=False):
    # Wrapper function
    return arango_db.initialize_db(
        arango_url=arango_url,
        arango_user=arango_user,
        arango_password=arango_password
    )


def extract_topo_from_isis(isis_nodes, isisd_pwd,
                           nodes_yaml, edges_yaml, 
                           addrs_yaml=None, hosts_yaml=None, verbose=False):
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
        return
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


def load_topo_on_arango(arango_url, user, password,
                        nodes, edges,
                        nodes_collection, edges_collection,
                        verbose=False):
    # Load the topology on Arango DB
    arango_db.populate(
        nodes=nodes_collection,
        edges=edges_collection,
        nodes_dict=nodes,
        edges_dict=edges
    )


def extract_topo_from_isis_and_load_on_arango(isis_nodes, isisd_pwd,
                                              arango_url=None,
                                              arango_user=None,
                                              arango_password=None,
                                              nodes_yaml=None, edges_yaml=None,
                                              addrs_yaml=None, hosts_yaml=None,
                                              period=0, verbose=False):
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
    while (True):
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
