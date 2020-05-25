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

# Imports
import sys
from ipaddress import IPv6Interface
from pyaml import yaml
import re
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Folder containing this script
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

# Folder containing the controller
CONTROLLER_PATH = os.path.join(BASE_PATH, '../controller/')

# Environment variables have priority over hardcoded paths
# If an environment variable is set, we must use it instead of
# the hardcoded constant

# CONTROLLER_PATH
if os.getenv('CONTROLLER_PATH') is not None:
    # Check if the CONTROLLER_PATH variable is set
    if os.getenv('CONTROLLER_PATH') == '':
        print('Error : Set CONTROLLER_PATH variable in .env\n')
        sys.exit(-2)
    # Check if the CONTROLLER_PATH variable points to an existing folder
    if not os.path.exists(CONTROLLER_PATH):
        print('Error : CONTROLLER_PATH variable in '
              '.env points to a non existing folder')
        sys.exit(-2)
    # CONTROLLER_PATH in .env is correct. We use it.
    CONTROLLER_PATH = os.getenv('CONTROLLER_PATH')
else:
    # CONTROLLER_PATH in .env is not set, we use the hardcoded path
    #
    # Check if the CONTROLLER_PATH variable is set
    if CONTROLLER_PATH == '':
        print('Error : Set CONTROLLER_PATH variable in .env or %s' % sys.argv[0])
        sys.exit(-2)
    # Check if the CONTROLLER_PATH variable points to an existing folder
    if not os.path.exists(CONTROLLER_PATH):
        print('Error : CONTROLLER_PATH variable in '
              '%s points to a non existing folder' % sys.argv[0])
        print('Error : Set CONTROLLER_PATH variable in .env or %s\n' % sys.argv[0])
        sys.exit(-2)

# Controller dependencies
sys.path.append(CONTROLLER_PATH)
from srv6_controller import extract_topo_from_isis_and_load_on_arango


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
