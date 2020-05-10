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
# Example showing how the topology can be extracted from a network
# running ISIS protocol and how the topology can imported on Arango DB
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


# Imports
from ipaddress import IPv6Interface
from pyaml import yaml
import re
import logging

# SRv6 Controller dependencies
controller_path = '../'
if controller_path == '':
    print('Error : Set controller_path variable in load_topo_on_arango.py')
    sys.exit(-2)

if not os.path.exists(controller_path):
    print('Error : controller_path variable in '
          'load_topo_on_arango.py points to a non existing folder\n')
    sys.exit(-2)

sys.path.append(srv6_controller)
from srv6_controller import extract_topo_from_isis
from srv6_controller import load_topo_on_arango


# Global variables definition
#
#
# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)


# Arango DB params
USER = 'root'
PASSWORD = '12345678'
ARANGO_URL = 'localhost:8529'
# Topology params
ISIS_NODES = ['fcff:1::1-2608']
NODES_YAML = 'nodes.yaml'
EDGES_YAML = 'edges.yaml'

# Hosts to be added to the dumped topology
HOSTS = [
    {
        'name': 'hdc1',
        'ip_address': 'fcff:2:1::2/48',
        'gw': 'r2'
    },
    {
        'name': 'hdc2',
        'ip_address': 'fcff:8:1::2/48',
        'gw': 'r8'
    },
    {
        'name': 'hdc3',
        'ip_address': 'fcff:5:1::2/48',
        'gw': 'r5'
    }
]


def fill_ip_addresses(nodes_yaml):
    # In our testbed, the loopback address assigned
    # to a router is  fcff:xxxx::1/128, where xxxx
    # is the ID of the router
    #
    logger.info('*** Filling nodes YAML file with IP addresses')
    # Open nodes file
    with open(nodes_yaml, 'r') as infile:
        nodes = yaml.safe_load(infile.read())
    # Fill addresses
    for node in nodes:
        # New string where the non-digit characters
        # are replaced with the empty string
        nodeid = int(re.sub('\\D', '', node['_key']))
        if nodeid <= 0 or nodeid >= 2**16:
            # Overflow, address out of range
            logging.critical('Network overflow: no space left in the '
                             'loopback subnet for the router %s' % _key)
            return
        # Prefix
        prefix = int(IPv6Interface(u'fcff::/16'))
        # Build the address fcff:xxxx::1/128
        ip_address = str(IPv6Interface(prefix | nodeid << 96 | 1))
        # Update the dict
        node['ip_address'] = ip_address
    # Save the nodes YAML
    with open(nodes_yaml, 'w') as outfile:
        yaml.dump(nodes, outfile)
    logger.info('*** Nodes YAML updated\n')


def add_hosts(nodes_yaml, edges_yaml):
    # In our testbed, we have three hosts named hdc1,
    # hdc2, hdc3
    #
    logger.info('*** Adding hosts to the topology')
    # Open nodes file
    with open(nodes_yaml, 'r') as infile:
        nodes = yaml.safe_load(infile.read())
    # Open edges file
    with open(edges_yaml, 'r') as infile:
        edges = yaml.safe_load(infile.read())
    # Add hosts and links
    for host in HOSTS:
        # Add host
        nodes.append({
            '_key': host['name'],
            'type': 'host',
            'ip_address': host['ip_address']
        })
        # Add edge (host to router)
        edges.append({
            '_from': 'nodes/%s' % host['name'],
            '_to': 'nodes/%s' % host['gw'],
            'type': 'edge'
        })
        # Add edge (router to host)
        # This is required because we work with
        # unidirectional edges
        edges.append({
            '_to': 'nodes/%s' % host['gw'],
            '_from': 'nodes/%s' % host['name'],
            'type': 'edge'
        })
    # Update nodes YAML
    with open(nodes_yaml, 'w') as outfile:
        yaml.dump(nodes, outfile)
    logger.info('*** Nodes YAML updated\n')
    # Update edges YAML
    with open(edges_yaml, 'w') as outfile:
        yaml.dump(edges, outfile)
    logger.info('*** Edges YAML updated\n')


def extract_topo_and_load_on_arango():
    # Extract topology
    extract_topo_from_isis(
        isis_nodes=ISIS_NODES,
        nodes_yaml=NODES_YAML,
        edges_yaml=EDGES_YAML,
        verbose=True
    )
    # Add IP addresses
    fill_ip_addresses(
        nodes_yaml=NODES_YAML
    )
    # Add hosts
    add_hosts(
        nodes_yaml=NODES_YAML,
        edges_yaml=EDGES_YAML
    )
    # Load on Arango
    load_topo_on_arango(
        arango_url=ARANGO_URL,
        user=USER,
        password=PASSWORD,
        nodes_yaml=NODES_YAML,
        edges_yaml=EDGES_YAML,
        verbose=True
    )


if __name__ == '__main__':
    # Run example
    extract_topo_and_load_on_arango()
