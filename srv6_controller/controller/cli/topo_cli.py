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
# Implementation of a CLI for the SRv6 Controller
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


from argparse import ArgumentParser
import sys

# Interval between two consecutive extractions (in seconds)
DEFAULT_TOPO_EXTRACTION_PERIOD = 0

# Path of the controller
CONTROLLER_PATH = '../'

# Controller dependencies
sys.path.append(CONTROLLER_PATH)
import arangodb_utils
import ti_extraction


def extract_topo_from_isis(isis_nodes, isisd_pwd,
                           nodes_yaml, edges_yaml, verbose=False):
    arangodb_utils.extract_topo_from_isis(
        isis_nodes=isis_nodes.split(','),
        isisd_pwd=isisd_pwd,
        nodes_yaml=nodes_yaml,
        edges_yaml=edges_yaml,
        verbose=verbose
    )


def load_topo_on_arango(arango_url, arango_user, arango_password,
                        nodes_yaml, edges_yaml, verbose=False):
    arangodb_utils.load_topo_on_arango(
        arango_url=arango_url,
        user=arango_user,
        password=arango_password,
        nodes_yaml=nodes_yaml,
        edges_yaml=edges_yaml,
        verbose=verbose)


def extract_topo_from_isis_and_load_on_arango(isis_nodes, isisd_pwd,
                                              arango_url=None,
                                              arango_user=None,
                                              arango_password=None,
                                              nodes_yaml=None, edges_yaml=None,
                                              period=0, verbose=False):
    arangodb_utils.extract_topo_from_isis_and_load_on_arango(
        isis_nodes=isis_nodes,
        isisd_pwd=isisd_pwd,
        arango_url=arango_url,
        arango_user=arango_user,
        arango_password=arango_password,
        nodes_yaml=nodes_yaml,
        edges_yaml=edges_yaml,
        period=period,
        verbose=verbose
    )


def topology_information_extraction_isis(routers, period, isisd_pwd,
                                         topo_file_json=None,
                                         nodes_file_yaml=None,
                                         edges_file_yaml=None,
                                         topo_graph=None, verbose=False):
    ti_extraction.topology_information_extraction_isis(
        routers=routers,
        period=period,
        isisd_pwd=isisd_pwd,
        topo_file_json=topo_file_json,
        nodes_file_yaml=nodes_file_yaml,
        edges_file_yaml=edges_file_yaml,
        topo_graph=topo_graph,
        verbose=verbose
    )


# Parse options
def parse_arguments_extract_topo_from_isis(prog=sys.argv[0], args=None):
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    parser.add_argument(
        '--isis-nodes', dest='isis_nodes', action='store',
        required=True, help='isis_nodes'
    )
    parser.add_argument(
        '--isisd-pwd', dest='isisd_pwd', action='store',
        help='period'
    )
    parser.add_argument(
        '--nodes-yaml', dest='nodes_yaml', action='store',
        help='nodes_yaml'
    )
    parser.add_argument(
        '--edges-yaml', dest='edges_yaml', action='store',
        help='edges_yaml'
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Enable verbose mode'
    )
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Activate debug logs'
    )
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# Parse options
def parse_arguments_load_topo_on_arango(prog=sys.argv[0], args=None):
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    parser.add_argument(
        '--arango-url', dest='arango_url', action='store',
        help='arango_url'
    )
    parser.add_argument(
        '--arango-user', dest='arango_user', action='store',
        help='arango_user'
    )
    parser.add_argument(
        '--arango-password', dest='arango_password', action='store',
        help='arango_password'
    )
    parser.add_argument(
        '--nodes-yaml', dest='nodes_yaml', action='store',
        help='nodes_yaml'
    )
    parser.add_argument(
        '--edges-yaml', dest='edges_yaml', action='store',
        help='edges_yaml'
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Enable verbose mode'
    )
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Activate debug logs'
    )
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# Parse options
def parse_arguments_extract_topo_from_isis_and_load_on_arango(
        prog=sys.argv[0], args=None):
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    parser.add_argument(
        '--isis-nodes', dest='isis_nodes', action='store',
        required=True, help='isis_nodes'
    )
    parser.add_argument(
        '--isisd-pwd', dest='isisd_pwd', action='store',
        help='period'
    )
    parser.add_argument(
        '--arango-url', dest='arango_url', action='store',
        help='arango_url'
    )
    parser.add_argument(
        '--arango-user', dest='arango_user', action='store',
        help='arango_user'
    )
    parser.add_argument(
        '--arango-password', dest='arango_password', action='store',
        help='arango_password'
    )
    parser.add_argument(
        '--period', dest='period', action='store',
        help='period', type=int, default=DEFAULT_TOPO_EXTRACTION_PERIOD
    )
    parser.add_argument(
        '--nodes-yaml', dest='nodes_yaml', action='store',
        help='nodes_yaml'
    )
    parser.add_argument(
        '--edges-yaml', dest='edges_yaml', action='store',
        help='edges_yaml'
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Enable verbose mode'
    )
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Activate debug logs'
    )
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# Parse options
def parse_arguments_topology_information_extraction_isis(
        prog=sys.argv[0], args=None):
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    parser.add_argument(
        '--routers', dest='routers', action='store',
        required=True, help='routers'
    )
    parser.add_argument(
        '--period', dest='period', action='store',
        help='period', type=int, default=DEFAULT_TOPO_EXTRACTION_PERIOD
    )
    parser.add_argument(
        '--isisd-pwd', dest='isisd_pwd', action='store',
        help='period'
    )
    parser.add_argument(
        '--topo-file-json', dest='topo_file_json', action='store',
        help='topo_file_json'
    )
    parser.add_argument(
        '--nodes-file-yaml', dest='nodes_file_yaml', action='store',
        help='nodes_file_yaml'
    )
    parser.add_argument(
        '--edges-file-yaml', dest='edges_file_yaml', action='store',
        help='edges_file_yaml'
    )
    parser.add_argument(
        '--topo-graph', dest='topo_graph', action='store',
        help='topo_graph'
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Enable verbose mode'
    )
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Activate debug logs'
    )
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args
