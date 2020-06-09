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
# Implementation of SRv6 Controller
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
# from __future__ import absolute_import, division, print_function
from argparse import ArgumentParser
from concurrent import futures
from threading import Thread
from socket import AF_INET, AF_INET6
from six import text_type
from ipaddress import IPv4Interface, IPv6Interface
from ipaddress import AddressValueError
from dotenv import load_dotenv
import grpc
import logging
import time
import json
import sys
from utils import get_address_family
from pyaml import yaml

# Load environment variables from .env file
load_dotenv()

# Folder containing this script
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

# Folder containing the files auto-generated from proto files
PROTO_PATH = os.path.join(BASE_PATH, '../protos/gen-py/')

# Environment variables have priority over hardcoded paths
# If an environment variable is set, we must use it instead of
# the hardcoded constant
if os.getenv('PROTO_PATH') is not None:
    # Check if the PROTO_PATH variable is set
    if os.getenv('PROTO_PATH') == '':
        print('Error : Set PROTO_PATH variable in .env\n')
        sys.exit(-2)
    # Check if the PROTO_PATH variable points to an existing folder
    if not os.path.exists(PROTO_PATH):
        print('Error : PROTO_PATH variable in '
              '.env points to a non existing folder')
        sys.exit(-2)
    # PROTO_PATH in .env is correct. We use it.
    PROTO_PATH = os.getenv('PROTO_PATH')
else:
    # PROTO_PATH in .env is not set, we use the hardcoded path
    #
    # Check if the PROTO_PATH variable is set
    if PROTO_PATH == '':
        print('Error : Set PROTO_PATH variable in .env or %s' % sys.argv[0])
        sys.exit(-2)
    # Check if the PROTO_PATH variable points to an existing folder
    if not os.path.exists(PROTO_PATH):
        print('Error : PROTO_PATH variable in '
              '%s points to a non existing folder' % sys.argv[0])
        print('Error : Set PROTO_PATH variable in .env or %s\n' % sys.argv[0])
        sys.exit(-2)

# Folder containing the files auto-generated from proto files
ARANGODB_UTILS_PATH = os.path.join(BASE_PATH, '../../db_update')

# Environment variables have priority over hardcoded paths
# If an environment variable is set, we must use it instead of
# the hardcoded constant
if os.getenv('ARANGODB_UTILS_PATH') is not None:
    # Check if the ARANGODB_UTILS_PATH variable is set
    if os.getenv('ARANGODB_UTILS_PATH') == '':
        print('Error : Set ARANGODB_UTILS_PATH variable in .env\n')
        sys.exit(-2)
    # Check if the ARANGODB_UTILS_PATH variable points to an existing folder
    if not os.path.exists(ARANGODB_UTILS_PATH):
        print('Error : ARANGODB_UTILS_PATH variable in '
              '.env points to a non existing folder')
        sys.exit(-2)
    # ARANGODB_UTILS_PATH in .env is correct. We use it.
    ARANGODB_UTILS_PATH = os.getenv('ARANGODB_UTILS_PATH')
else:
    # ARANGODB_UTILS_PATH in .env is not set, we use the hardcoded path
    #
    # Check if the ARANGODB_UTILS_PATH variable is set
    if ARANGODB_UTILS_PATH == '':
        print('Error : Set ARANGODB_UTILS_PATH variable in .env or %s' % sys.argv[0])
        sys.exit(-2)
    # Check if the ARANGODB_UTILS_PATH variable points to an existing folder
    if not os.path.exists(ARANGODB_UTILS_PATH):
        print('Error : ARANGODB_UTILS_PATH variable in '
              '%s points to a non existing folder' % sys.argv[0])
        print('Error : Set ARANGODB_UTILS_PATH variable in .env or %s\n' % sys.argv[0])
        sys.exit(-2)

# Proto dependencies
sys.path.append(PROTO_PATH)
import srv6_manager_pb2
import srv6_manager_pb2_grpc

# ArangoDB dependencies
sys.path.append(ARANGODB_UTILS_PATH)
import arango_db

# Import topology extraction utility functions
from ti_extraction import connect_and_extract_topology_isis
from ti_extraction import dump_topo_yaml
from ti_extraction import dump_topo_yaml_edges_ip


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


# Build a grpc stub
def get_grpc_session(server_ip, server_port):
    # Get family of the gRPC IP
    addr_family = get_address_family(server_ip)
    # Build address depending on the family
    if addr_family == AF_INET:
        # IPv4 address
        server_ip = 'ipv4:%s:%s' % (server_ip, server_port)
    elif addr_family == AF_INET6:
        # IPv6 address
        server_ip =  'ipv6:[%s]:%s' % (server_ip, server_port)
    else:
        # Invalid address
        logger.fatal('Invalid gRPC address: %s' % server_ip)
        return None
    # If secure we need to establish a channel with the secure endpoint
    if SECURE:
        if CERTIFICATE is None:
            logger.fatal('Certificate required for gRPC secure mode')
            return None
        # Open the certificate file
        with open(CERTIFICATE, 'rb') as f:
            certificate = f.read()
        # Then create the SSL credentials and establish the channel
        grpc_client_credentials = grpc.ssl_channel_credentials(certificate)
        channel = grpc.secure_channel(server_ip, grpc_client_credentials)
    else:
        channel = grpc.insecure_channel(server_ip)
    # Return the channel
    return channel


# Parser for gRPC errors
def parse_grpc_error(e):
    status_code = e.code()
    details = e.details()
    logger.error('gRPC client reported an error: %s, %s'
                 % (status_code, details))
    if grpc.StatusCode.UNAVAILABLE == status_code:
        code = srv6_manager_pb2.STATUS_GRPC_SERVICE_UNAVAILABLE
    elif grpc.StatusCode.UNAUTHENTICATED == status_code:
        code = srv6_manager_pb2.STATUS_GRPC_UNAUTHORIZED
    else:
        code = srv6_manager_pb2.STATUS_INTERNAL_ERROR
    # Return an error message
    return code


def handle_srv6_path(op, channel, destination, segments=[], device='', encapmode="encap", table=-1, metric=-1):
    # Create request message
    request = srv6_manager_pb2.SRv6ManagerRequest()
    # Create a new SRv6 path request
    path_request = request.srv6_path_request
    # Create a new path
    path = path_request.paths.add()
    # Set destination
    path.destination = text_type(destination)
    # Set device
    # If the device is not specified (i.e. empty string),
    # it will be chosen by the gRPC server
    path.device = text_type(device)
    # Set table ID
    # If the table ID is not specified (i.e. table=-1),
    # the main table will be used
    path.table = int(table)
    # Set metric (i.e. preference value of the route)
    # If the metric is not specified (i.e. metric=-1),
    # the decision is left to the Linux kernel
    path.metric = int(metric)
    try:
        # Get the reference of the stub
        stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
        # Fill the request depending on the operation
        # and send the request
        if op == 'add':
            # Set encapmode
            path.encapmode = text_type(encapmode)
            if len(segments) == 0:
                logger.error('*** Missing segments for seg6 route')
                return srv6_manager_pb2.STATUS_INTERNAL_ERROR
            # Iterate on the segments and build the SID list
            for segment in segments:
                # Append the segment to the SID list
                srv6_segment = path.sr_path.add()
                srv6_segment.segment = text_type(segment)
            # Create the SRv6 path
            response = stub.Create(request)
        elif op == 'get':
            # Get the SRv6 path
            response = stub.Get(request)
        elif op == 'change':
            # Set encapmode
            path.encapmode = text_type(encapmode)
            # Iterate on the segments and build the SID list
            for segment in segments:
                # Append the segment to the SID list
                srv6_segment = path.sr_path.add()
                srv6_segment.segment = text_type(segment)
            # Update the SRv6 path
            response = stub.Update(request)
        elif op == 'del':
            # Remove the SRv6 path
            response = stub.Remove(request)
        # Get the status code of the gRPC operation
        response = response.status
    except grpc.RpcError as e:
        # An error occurred during the gRPC operation
        # Parse the error and return it
        response = parse_grpc_error(e)
    # Return the response
    return response


def handle_srv6_behavior(op, channel, segment, action='', device='', table=-1, nexthop="", lookup_table=-1, interface="", segments=[], metric=-1):
    # Create request message
    request = srv6_manager_pb2.SRv6ManagerRequest()
    # Create a new SRv6 behavior request
    behavior_request = request.srv6_behavior_request
    # Create a new SRv6 behavior
    behavior = behavior_request.behaviors.add()
    # Set local segment for the seg6local route
    behavior.segment = text_type(segment)
    # Set the device
    # If the device is not specified (i.e. empty string),
    # it will be chosen by the gRPC server
    behavior.device = text_type(device)
    # Set the table where the seg6local must be inserted
    # If the table ID is not specified (i.e. table=-1),
    # the main table will be used
    behavior.table = int(table)
    # Set device
    # If the device is not specified (i.e. empty string),
    # it will be chosen by the gRPC server
    behavior.device = text_type(device)
    # Set metric (i.e. preference value of the route)
    # If the metric is not specified (i.e. metric=-1),
    # the decision is left to the Linux kernel
    behavior.metric = int(metric)
    try:
        # Get the reference of the stub
        stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
        # Fill the request depending on the operation
        # and send the request
        if op == 'add':
            if action == '':
                logger.error('*** Missing action for seg6local route')
                return srv6_manager_pb2.STATUS_INTERNAL_ERROR
            # Set the action for the seg6local route
            behavior.action = text_type(action)
            # Set the nexthop for the L3 cross-connect actions
            # (e.g. End.DX4, End.DX6)
            behavior.nexthop = text_type(nexthop)
            # Set the table for the "decap and table lookup" actions
            # (e.g. End.DT4, End.DT6)
            behavior.lookup_table = int(lookup_table)
            # Set the inteface for the L2 cross-connect actions
            # (e.g. End.DX2)
            behavior.interface = text_type(interface)
            # Set the segments for the binding SID actions
            # (e.g. End.B6, End.B6.Encaps)
            for segment in segments:
                # Create a new segment
                srv6_segment = behavior.segs.add()
                srv6_segment.segment = text_type(segment)
            # Create the SRv6 behavior
            response = stub.Create(request)
        elif op == 'get':
            # Get the SRv6 behavior
            response = stub.Get(request)
        elif op == 'change':
            # Set the action for the seg6local route
            behavior.action = text_type(action)
            # Set the nexthop for the L3 cross-connect actions
            # (e.g. End.DX4, End.DX6)
            behavior.nexthop = text_type(nexthop)
            # Set the table for the "decap and table lookup" actions
            # (e.g. End.DT4, End.DT6)
            behavior.lookup_table = int(lookup_table)
            # Set the inteface for the L2 cross-connect actions
            # (e.g. End.DX2)
            behavior.interface = text_type(interface)
            # Set the segments for the binding SID actions
            # (e.g. End.B6, End.B6.Encaps)
            for segment in segments:
                # Create a new segment
                srv6_segment = behavior.segs.add()
                srv6_segment.segment = text_type(segment)
            # Update the SRv6 behavior
            response = stub.Update(request)
        elif op == 'del':
            # Remove the SRv6 behavior
            response = stub.Remove(request)
        else:
            logger.error('Invalid operation: %s' % op)
            return None
        # Get the status code of the gRPC operation
        response = response.status
    except grpc.RpcError as e:
        # An error occurred during the gRPC operation
        # Parse the error and return it
        response = parse_grpc_error(e)
    # Return the response
    return response


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
        # edges.append({
        #     '_from': 'nodes/%s' % host['name'],
        #     '_to': 'nodes/%s' % host['gw'],
        #     'type': 'edge'
        # })
        # # Add edge (router to host)
        # # This is required because we work with
        # # unidirectional edges
        # edges.append({
        #     '_to': 'nodes/%s' % host['gw'],
        #     '_from': 'nodes/%s' % host['name'],
        #     'type': 'edge'
        # })
    logger.info('*** Nodes YAML updated\n')
    logger.info('*** Edges YAML updated\n')
    # Return the updated nodes and edges lists
    return nodes, edges


def load_topo_on_arango(nodes, edges, nodes_collection,
                        edges_collection, verbose=False):
    # Load the topology on Arango DB
    # arango_db.populate(
    arango_db.populate2(
        nodes=nodes_collection,
        edges=edges_collection,
        nodes_dict=nodes,
        edges_dict=edges
    )


def save_yaml_dump(obj, filename):
    # Save file
    with open(filename, 'w') as outfile:
        yaml.dump(obj, outfile)


def extract_topo_from_isis_and_load_on_arango(isis_nodes, arango_url=None,
                                              arango_user=None,
                                              arango_password=None,
                                              nodes_yaml=None, edges_yaml=None,
                                              addrs_yaml=None,
                                              hosts_yaml=None,
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
        nodes, edges, node_to_systemid, edges_ip = connect_and_extract_topology_isis(
            ips_ports=isis_nodes,
            verbose=verbose,
            hosts_yaml=hosts_yaml
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
            # nodes, edges = dump_topo_yaml(
            nodes, edges_ip = dump_topo_yaml_edges_ip(
                nodes=nodes,
                edges=edges_ip,
                # edges=edges,
                node_to_systemid=node_to_systemid,
                nodes_file_yaml=nodes_yaml,
                edges_file_yaml=edges_yaml
            )
            # Add IP addresses information
            if addrs_yaml is not None:
                fill_ip_addresses(nodes, addrs_yaml)
            # Add hosts information
            if hosts_yaml is not None:
                # add_hosts(nodes, edges, hosts_yaml)
                add_hosts(nodes, edges_ip, hosts_yaml)
            # Save nodes YAML file
            save_yaml_dump(nodes, nodes_yaml)
            # Save edges YAML file
            # save_yaml_dump(edges, edges_yaml)
            save_yaml_dump(edges_ip, edges_yaml)
            # Load the topology on Arango DB
            if arango_url is not None and \
                    arango_user is not None and arango_password is not None:
                load_topo_on_arango(
                    nodes=nodes,
                    # edges=edges,
                    edges=edges_ip,
                    nodes_collection=nodes_collection,
                    edges_collection=edges_collection,
                    verbose=verbose
                )
            # Period = 0 means a single extraction
            if period == 0:
                break
        # Wait 'period' seconds between two extractions
        time.sleep(period)


# Parse options
def parse_arguments():
    # Get parser
    parser = ArgumentParser(
        description='SRv6 Controller'
    )
    parser.add_argument(
        '--yaml-output', dest='yaml_output', action='store',
        default=None,
        help='Path where the topology has to be exported in YAML format'
    )
    parser.add_argument(
        '--update-arango', dest='update_arango', action='store_true',
        default=False,
        help='Define whether to load the topology on ArangoDB or not'
    )
    parser.add_argument(
        '--loop-update', dest='loop_update', action='store', type=int,
        default=0, help='The interval between two consecutive topology '
        'extractions (in seconds)'
    )
    parser.add_argument(
        '--router-list', dest='router_list', action='store', type=str,
        required=True,
        help='Comma-separated list of '
             'routers from which the topology has been extracted'
    )
    parser.add_argument(
        '--isis-port', dest='isis_port', action='store', type=int,
        default=DEFAULT_ISIS_PORT,
        help='Port on which the ISIS daemon is listening'
    )
    parser.add_argument(
        '--hosts-yaml', dest='hosts_yaml', action='store', type=str,
        default=None,
        help='YAML file containing the hosts'
    )
    parser.add_argument(
        '--addrs-yaml', dest='addrs_yaml', action='store', type=str,
        default=None,
        help='YAML file containing the IP addresses'
    )
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Activate debug logs'
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Enable verbose mode'
    )
    # Parse input parameters
    args = parser.parse_args()
    # Return the arguments
    return args


if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()
    # Path where the YAML files have to be stored
    yaml_output = args.yaml_output
    # Define whether to load the topology on ArangoDB or not
    update_arango = args.update_arango
    # Interval between two consecutive topology extractions
    loop_update = args.loop_update
    # Comma-separated list of routers from which the topology
    # has been extracted
    router_list = args.router_list
    # Port on which the ISIS daemon is listening
    isis_port = args.isis_port
    # Hosts YAML filename
    hosts_yaml = args.hosts_yaml
    # IP addresses YAML filename
    addrs_yaml = args.addrs_yaml
    # Define whether enable the verbose mode or not
    verbose = args.verbose
    # Setup properly the logger
    if args.debug:
        logger.setLevel(level=logging.DEBUG)
    else:
        logger.setLevel(level=logging.INFO)
    # Debug settings
    server_debug = logger.getEffectiveLevel() == logging.DEBUG
    logging.info('SERVER_DEBUG:' + str(server_debug))
    # Print configuration
    logger.debug('\n\n****** Controller Configuration ******\n'
                 '  YAML output: %s\n'
                 '  Update Arango: %s\n'
                 '  Loop update: %s\n'
                 '  Router list: %s\n'
                 '  ISIS port: %s\n'
                 '**************************************\n'
                 % (yaml_output, update_arango, loop_update,
                    router_list, isis_port))
    # Parameters
    #
    # IS-IS nodes (e.g. [2000::1-2608,2000::2-2608])
    isis_nodes = list()
    for ip in router_list.split(','):
        isis_nodes.append('%s-%s' % (ip, isis_port))
    # Nodes YAML filename
    nodes_yaml = None
    if yaml_output is not None:
        nodes_yaml = os.path.join(yaml_output, 'nodes.yaml')
    # Edges YAML filename
    edges_yaml = None
    if yaml_output is not None:
        edges_yaml = os.path.join(yaml_output, 'edges.yaml')
    # ArangoDB params
    arango_url = None
    arango_user = None
    arango_password = None
    if update_arango:
        arango_url = ARANGO_URL
        arango_user = ARANGO_USER
        arango_password = ARANGO_PASSWORD
    # Extract topology from ISIS, (optionally) export it in YAML format
    # and (optionally) upload it on ArangoDB
    extract_topo_from_isis_and_load_on_arango(
        isis_nodes=isis_nodes,
        arango_url=arango_url,
        arango_user=arango_user,
        arango_password=arango_password,
        nodes_yaml=nodes_yaml,
        edges_yaml=edges_yaml,
        period=loop_update,
        hosts_yaml=hosts_yaml,
        addrs_yaml=addrs_yaml,
        verbose=verbose
    )
