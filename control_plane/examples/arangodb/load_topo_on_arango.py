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
import os
import logging

# Controller dependencies
from control_plane.controller.arangodb_utils import extract_topo_from_isis_and_load_on_arango
# from control_plane.controller.arangodb_utils import extract_topo_from_isis
# from control_plane.controller.arangodb_utils import load_topo_on_arango

# Folder containing this script
BASE_PATH = os.path.dirname(os.path.realpath(__file__))


# Global variables definition
#
#
# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)


# Arango DB params
ARANGO_USER = 'root'
ARANGO_PASSWORD = '12345678'
ARANGO_URL = 'http://localhost:8529'
# Topology params
ISIS_NODES = ['fcff:1::1-2608']
NODES_YAML = 'nodes.yaml'
EDGES_YAML = 'edges.yaml'
# Addresses to be added to the topology information
ADDRS_YAML = 'addrs.yaml'
# Hosts to be added to the dumped topology
HOSTS_YAML = 'hosts.yaml'


def extract_topo_and_load_on_arango():
    # Extract topology and load on ArangoDB
    extract_topo_from_isis_and_load_on_arango(
        isis_nodes=ISIS_NODES,
        arango_url=ARANGO_URL,
        arango_user=ARANGO_USER,
        arango_password=ARANGO_PASSWORD,
        nodes_yaml=NODES_YAML,
        edges_yaml=EDGES_YAML,
        addrs_yaml=ADDRS_YAML,
        hosts_yaml=HOSTS_YAML,
        period=0,
        verbose=True
    )


if __name__ == '__main__':
    # Run example
    extract_topo_and_load_on_arango()
