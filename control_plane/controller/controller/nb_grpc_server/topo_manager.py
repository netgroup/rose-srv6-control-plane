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
# Implementation of Topology Manager for the Northbound gRPC server
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
This module provides an implementation of a Topology Manager for the
Northbound gRPC server.
'''

# General imports
import logging
import os
import sys
from argparse import ArgumentParser

# Controller dependencies
import nb_commons_pb2
import topology_manager_pb2
import topology_manager_pb2_grpc
from controller import arangodb_utils
from controller import arangodb_driver
from controller import topo_utils
from controller.ti_extraction import connect_and_extract_topology_isis
from apps.cli import utils as cli_utils

# Logger reference
logger = logging.getLogger(__name__)


class TopologyManager(topology_manager_pb2_grpc.TopologyManagerServicer):
    '''
    gRPC request handler.
    '''

    def ExtractTopology(self, request, context):
        '''
        Extract the network topology from a set of nodes running
        ISIS protocol.
        '''
        # pylint: disable=too-many-arguments
        #
        # Extract the parameters from the gRPC request
        #
        # Param isis_nodes: list of ip-port
        # (e.g. [2000::1-2608,2000::2-2608])
        nodes = list()
        for node in request.nodes:
            nodes.append('%s-%s' % (node.address, node.port))
        # Password of the routing protocol
        password = request.password
        # Verbose mode
        verbose = request.verbose
        #
        # TODO check if ISIS...
        # Connect to a node and extract the topology
        nodes, edges, node_to_systemid = connect_and_extract_topology_isis(
            ips_ports=nodes,
            isisd_pwd=password,
            verbose=verbose
        )
        if nodes is None or edges is None or node_to_systemid is None:
            logger.error('Cannot extract topology')
            return  # FIXME we should return an error
        # Export the topology in YAML format
        nodes, edges = dump_topo_yaml(
            nodes=nodes,
            edges=edges,
            node_to_systemid=node_to_systemid
        )
        # Add IP addresses information
        if addrs_yaml is not None:
            fill_ip_addresses(nodes, addrs_yaml)    # FIXME
        # Add hosts information
        if hosts_yaml is not None:
            # add_hosts(nodes, edges, hosts_yaml)
            add_hosts(nodes, edges, hosts_yaml)     # FIXME
        # Save nodes YAML file
        if nodes_yaml is not None:
            save_yaml_dump(nodes, nodes_yaml)       # FIXME
        # Save edges YAML file
        if edges_yaml is not None:
            save_yaml_dump(edges, edges_yaml)       # FIXME

    def LoadTopologyOnDatabase(self, request, context):
        '''
        Load a network topology on a Arango database.
        '''
        # pylint: disable=too-many-arguments
        #
        # Extract the parameters from the gRPC request
        #
        # ArangoDB URL
        arango_url = request.db_config.url
        # ArangoDB username
        arango_user = request.db_config.username
        # ArangoDB password
        arango_password = request.db_config.password
        # Verbose mode
        verbose = request.verbose
        #
        # Init database
        nodes_collection, edges_collection = arangodb_utils.initialize_db(
            arango_url=arango_url,
            arango_user=arango_user,
            arango_password=arango_password
        )
        # Read nodes YAML
        nodes = arangodb_utils.load_yaml_dump(nodes_yaml)
        # Read edges YAML
        edges = arangodb_utils.load_yaml_dump(edges_yaml)
        # Load nodes and edges on ArangoDB
        arangodb_utils.load_topo_on_arango(
            arango_url=arango_url,
            user=arango_user,
            password=arango_password,
            nodes=nodes,
            edges=edges,
            nodes_collection=nodes_collection,
            edges_collection=edges_collection,
            verbose=verbose
        )

    def extract_topo_from_isis_and_load_on_arango(self, request, context):
        '''
        Extract the topology from a set of nodes running ISIS protocol
        and load it on a Arango database.
        '''
        # pylint: disable=too-many-arguments
        #
        # Extract the parameters from the gRPC request
        #
        # Param isis_nodes: list of ip-port
        # (e.g. [2000::1-2608,2000::2-2608])
        nodes = list()
        for node in request.nodes:
            nodes.append('%s-%s' % (node.address, node.port))
        # Password of the routing protocol
        password = request.password
        # ArangoDB URL
        arango_url = request.db_config.url
        # ArangoDB username
        arango_user = request.db_config.username
        # ArangoDB password
        arango_password = request.db_config.password
        # Interval between two consecutive extractions
        period = request.period
        # Verbose mode
        verbose = request.verbose
        #
        # Extract the topology
        arangodb_utils.extract_topo_from_isis_and_load_on_arango(
            isis_nodes=nodes,
            isisd_pwd=password,
            arango_url=arango_url,
            arango_user=arango_user,
            arango_password=arango_password,
            nodes_yaml=nodes_yaml,
            edges_yaml=edges_yaml,
            addrs_yaml=addrs_yaml,
            hosts_yaml=hosts_yaml,
            period=period,
            verbose=verbose
        )

    def topology_information_extraction_isis(self, request, context):
        '''
        Run periodical topology extraction.
        '''
        # pylint: disable=too-many-arguments, unused-argument
        #
        # Extract the parameters from the gRPC request
        #
        # Param isis_nodes: list of ip-port
        # (e.g. [2000::1-2608,2000::2-2608])
        nodes = list()
        for node in request.nodes:
            nodes.append('%s-%s' % (node.address, node.port))
        # Password of the routing protocol
        password = request.password
        # ArangoDB URL
        arango_url = request.db_config.url
        # ArangoDB username
        arango_user = request.db_config.username
        # ArangoDB password
        arango_password = request.db_config.password
        # Interval between two consecutive extractions
        period = request.period
        # Verbose mode
        verbose = request.verbose
        #
        # Extract the topology
        arangodb_utils.extract_topo_from_isis_and_load_on_arango(
            isis_nodes=nodes,
            isisd_pwd=password,
            arango_url=arango_url,
            arango_user=arango_user,
            arango_password=arango_password,
            nodes_yaml=None,    # TODO
            edges_yaml=None,    # TODO
            addrs_yaml=None,    # TODO
            hosts_yaml=None,    # TODO
            period=period,
            verbose=verbose
        )

    def PushNodesConfig(self, request, context):
        '''
        Load nodes configuration.
        '''
        # Nodes configuration
        nodes_config = {
            'locator_bits': request.nodes_config.locator_bits,
            'usid_id_bits': request.nodes_config.usid_id_bits,
            'nodes': []
        }
        # Iterate on the nodes
        for node in request.nodes_config.nodes:
            # Append the node to the nodes list
            nodes_config['nodes'].append({
                'name': node.name,
                'grpc_ip': node.grpc_ip,
                'grpc_port': node.grpc_port,
                'uN': node.uN,
                'uDT': node.uDT,
                'fwd_engine': node.fwd_engine
            })
        # Load the nodes on the database
        topo_utils.load_nodes_config(nodes_config)
        # Create reply message
        return topology_manager_pb2.NodesConfigReply(
            status=nb_commons_pb2.STATUS_SUCCESS
        )

    def GetNodesConfig(self, request, context):
        '''
        Retrieve nodes configuration.
        '''
        # Create reply message
        response = topology_manager_pb2.NodesConfigReply()
        try:
            # Retrieve nodes configuration from the database
            nodes_config = topo_utils.get_nodes_config()
            # Set locator bits
            response.nodes_config.locator_bits = nodes_config['locator_bits']
            # Set uSID ID bits
            response.nodes_config.usid_id_bits = nodes_config['usid_id_bits']
            # Iterate on the nodes
            for node in nodes_config['nodes']:
                _node = response.nodes_config.nodes.add()
                _node.name = node['name']
                _node.grpc_ip = node['grpc_ip']
                _node.grpc_port = node['grpc_port']
                _node.uN = node['uN']
                _node.uDT = node['uDT']
                _node.fwd_engine = node['fwd_engine']
            # Set status code
            response.status = nb_commons_pb2.STATUS_SUCCESS
        except arangodb_driver.NodesConfigNotLoadedError:
            # Nodes configuration not loaded
            response.status = nb_commons_pb2.STATUS_NOT_CONFIGURED
        finally:
            # Done, return the reply
            return response


# TODO fix errors
