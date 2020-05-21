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


import os

# Activate virtual environment if a venv path has been specified in .venv
# This must be executed only if this file has been executed as a
# script (instead of a module)
if __name__ == '__main__':
    # Check if .venv file exists
    if os.path.exists('.venv'):
        with open('.venv', 'r') as venv_file:
            # Get virtualenv path from .venv file
            venv_path = venv_file.read()
        # Get path of the activation script
        venv_path = os.path.join(venv_path, 'bin/activate_this.py')
        if not os.path.exists(venv_path):
            print('Virtual environment path specified in .venv '
                  'points to an invalid path\n')
            exit(-2)
        with open(venv_path) as f:
            # Read the activation script
            code = compile(f.read(), venv_path, 'exec')
            # Execute the activation script to activate the venv
            exec(code, {'__file__': venv_path})

# General imports
from dotenv import load_dotenv
import logging
import time

# Load environment variables from .env file
load_dotenv()

# Import topology extraction utility functions
from ti_extraction import connect_and_extract_topology_isis
from ti_extraction import dump_topo_yaml


# Global variables definition
#
#
# ArangoDB default parameters
ARANGO_USER = 'root'
ARANGO_PASSWORD = '12345678'
ARANGO_URL = 'http://localhost:8529'
# Environment variables have priority over hardcoded paths
# If an environment variable is set, we must use it instead of
# the hardcoded constant
ARANGO_USER = os.getenv('ARANGO_USER', default=ARANGO_USER)
ARANGO_PASSWORD = os.getenv('ARANGO_PASSWORD', default=ARANGO_PASSWORD)
ARANGO_URL = os.getenv('ARANGO_URL', default=ARANGO_URL)
# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)
# Default parameters for SRv6 controller
#
# Port of the gRPC server
GRPC_PORT = 12345
# Define whether to use SSL or not for the gRPC client
SECURE = False
# SSL certificate of the root CA
CERTIFICATE = 'client_cert.pem'
# Default ISIS port
DEFAULT_ISIS_PORT = 2608


def extract_topo_from_isis(isis_nodes, nodes_yaml, edges_yaml, verbose=False):
    # Param isis_nodes: list of ip-port
    # (e.g. [2000::1-2608,2000::2-2608])
    #
    # Connect to a node and extract the topology
    nodes, edges, node_to_systemid = connect_and_extract_topology_isis(
        ips_ports=isis_nodes,
        verbose=verbose
    )
    if nodes is None or edges is None or node_to_systemid is None:
        logger.error('Cannot extract topology')
        return
    # Export the topology in YAML format
    dump_topo_yaml(
        nodes=nodes,
        edges=edges,
        node_to_systemid=node_to_systemid,
        nodes_file_yaml=nodes_yaml,
        edges_file_yaml=edges_yaml
    )


def load_topo_on_arango(arango_url, user, password,
                        nodes_yaml, edges_yaml, verbose=False):
    # Load the topology on Arango DB
    # TODO... load_arango(arango_url, user, password, nodes_yaml, edges_yaml)
    pass


def extract_topo_from_isis_and_load_on_arango(isis_nodes, arango_url=None,
                                              arango_user=None,
                                              arango_password=None,
                                              nodes_yaml=None, edges_yaml=None,
                                              period=0, verbose=False):
    # Param isis_nodes: list of ip-port
    # (e.g. [2000::1-2608,2000::2-2608])7
    #
    # Topology Information Extraction
    while (True):
        # Connect to a node and extract the topology
        nodes, edges, node_to_systemid = connect_and_extract_topology_isis(
            ips_ports=isis_nodes,
            verbose=verbose
        )
        if nodes is None or edges is None or node_to_systemid is None:
            logger.error('Cannot extract topology')
        else:
            logger.info('Topology extracted')
            if nodes_yaml is not None and edges_yaml is not None:
                # Export the topology in YAML format
                # This function returns a representation of nodes and
                # edges ready to get uploaded on ArangoDB.
                # Optionally, the nodes and the edges are exported in
                # YAML format, if 'nodes_yaml' and 'edges_yaml' variables
                # are not None
                nodes, edges = dump_topo_yaml(
                    nodes=nodes,
                    edges=edges,
                    node_to_systemid=node_to_systemid,
                    nodes_file_yaml=nodes_yaml,
                    edges_file_yaml=edges_yaml
                )
            if arango_url is not None and \
                    arango_user is not None and arango_password is not None:
                # Load the topology on Arango DB
                load_topo_on_arango(
                    arango_url=arango_url,
                    user=arango_user,
                    password=arango_password,
                    nodes_yaml=nodes,
                    edges_yaml=edges,
                    verbose=verbose
                )
            # Period = 0 means a single extraction
            if period == 0:
                break
        # Wait 'period' seconds between two extractions
        time.sleep(period)
