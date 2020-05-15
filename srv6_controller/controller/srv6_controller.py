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


# General imports
from __future__ import absolute_import, division, print_function
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
import os

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

# Proto dependencies
sys.path.append(PROTO_PATH)
import srv6_manager_pb2
import srv6_manager_pb2_grpc

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


# Build a grpc stub
def get_grpc_session(server_ip, server_port):
    # Get server IP
    server_ip = "ipv6:[%s]:%s" % (server_ip, server_port)
    # If secure we need to establish a channel with the secure endpoint
    if SECURE:
        if CERTIFICATE is None:
            logger.fatal('Certificate required for gRPC secure mode')
            exit(-1)
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


def handle_srv6_path(op, channel, destination, segments=[],
                     device='', encapmode="encap", table=-1, metric=-1):
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


def handle_srv6_behavior(op, channel, segment, action='', device='',
                         table=-1, nexthop="", lookup_table=-1,
                         interface="", segments=[], metric=-1):
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
    # Set table ID
    # If the table ID is not specified (i.e. table=-1),
    # the main table will be used
    behavior.table = int(table)
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
                    user is not None and password is not None:
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


# Parse options
def parse_arguments():
    # Get parser
    parser = ArgumentParser(
        description='SRv6 Controller'
    )
    parser.add_argument(
        '--yaml-output', dest='yaml_output', action='store_true',
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
        verbose=verbose
    )
