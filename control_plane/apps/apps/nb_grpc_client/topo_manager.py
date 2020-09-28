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
# Implementation of Topology Manager for the Northbound gRPC client
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
This module provides an implementation of a Topology Manager for the
Northbound gRPC client.
'''

# Controller dependencies
import nb_commons_pb2
import topology_manager_pb2
import topology_manager_pb2_grpc
from apps.nb_grpc_client import utils


def extract_topo_from_isis(controller_channel, isis_nodes, isisd_pwd,
                           nodes_yaml, edges_yaml,
                           addrs_yaml=None, hosts_yaml=None,
                           verbose=False):
    '''
    Extract the network topology from a set of nodes running
    ISIS protocol.
    '''
    # pylint: disable=too-many-arguments
    #
    # Create request message
    request = topology_manager_pb2.TopologyManagerRequest()
    # Set the IS-IS nodes
    for isis_node in isis_nodes.split(','):
        node = request.nodes.add()
        node.address = isis_node.split('-')[0]  # FIXME
        node.port = isis_node.split('-')[1]  # FIXME
    # Set the IS-IS password
    request.password = isisd_pwd
    # Set verbose mode
    request.verbose = verbose
    # Get the reference of the stub
    stub = topology_manager_pb2_grpc.TopologyManagerStub(controller_channel)
    # Extract the topology
    response = stub.ExtractTopology(request)
    # Check the status code
    if response.status != nb_commons_pb2.STATUS_SUCCESS:
        return False       # TODO raise an exception?
    # TODO write file
    return True


def load_topo_on_arango(controller_channel, arango_url, arango_user,
                        arango_password, nodes_yaml, edges_yaml,
                        verbose=False):
    '''
    Load a network topology on a Arango database.
    '''
    # pylint: disable=too-many-arguments
    #
    # Read nodes YAML
    nodes = arangodb_utils.load_yaml_dump(nodes_yaml)
    # Read edges YAML
    edges = arangodb_utils.load_yaml_dump(edges_yaml)
    # Create request message
    request = topology_manager_pb2.TopologyManagerRequest()
    # Set the database
    request.db_config.database = topology_manager_pb2.DBConfig.ARANGODB
    # Set the ArangoDB URL
    request.db_config.url = arango_url
    # Set the ArangoDB username
    request.db_config.username = arango_user
    # Set the ArangoDB password
    request.db_config.password = arango_password
    # Set verbose mode
    request.verbose = verbose
    # Get the reference of the stub
    stub = topology_manager_pb2_grpc.TopologyManagerStub(controller_channel)
    # Extract the topology
    response = stub.LoadTopologyOnDatabase(request)
    # Check the status code
    if response.status != nb_commons_pb2.STATUS_SUCCESS:
        return False       # TODO raise an exception?
    return True


def extract_topo_from_isis_and_load_on_arango(controller_channel,
                                              isis_nodes, isisd_pwd,
                                              arango_url=None,
                                              arango_user=None,
                                              arango_password=None,
                                              nodes_yaml=None, edges_yaml=None,
                                              addrs_yaml=None, hosts_yaml=None,
                                              period=0, verbose=False):
    '''
    Extract the topology from a set of nodes running ISIS protocol
    and load it on a Arango database
    '''
    # pylint: disable=too-many-arguments
    #
    # Read nodes YAML
    nodes = arangodb_utils.load_yaml_dump(nodes_yaml)
    # Read edges YAML
    edges = arangodb_utils.load_yaml_dump(edges_yaml)
    # Create request message
    request = topology_manager_pb2.TopologyManagerRequest()
    # Set the database
    request.db_config.database = topology_manager_pb2.DBConfig.ARANGODB
    # Set the ArangoDB URL
    request.db_config.url = arango_url
    # Set the ArangoDB username
    request.db_config.username = arango_user
    # Set the ArangoDB password
    request.db_config.password = arango_password
    # Set verbose mode
    request.verbose = verbose
    # Get the reference of the stub
    stub = topology_manager_pb2_grpc.TopologyManagerStub(controller_channel)
    # Extract the topology
    response = stub.ExtractTopologyAndLoadOnDatabase(request)
    # Check the status code
    if response.status != nb_commons_pb2.STATUS_SUCCESS:
        return False       # TODO raise an exception?
    return True


def topology_information_extraction_isis(controller_channel,
                                         routers, period, isisd_pwd,
                                         topo_file_json=None,
                                         nodes_file_yaml=None,
                                         edges_file_yaml=None,
                                         addrs_yaml=None, hosts_yaml=None,
                                         topo_graph=None, verbose=False):
    '''
    Run periodical topology extraction
    '''
    # pylint: disable=too-many-arguments, unused-argument
    #
    # Read nodes YAML
    nodes = arangodb_utils.load_yaml_dump(nodes_yaml)
    # Read edges YAML
    edges = arangodb_utils.load_yaml_dump(edges_yaml)
    # Create request message
    request = topology_manager_pb2.TopologyManagerRequest()
    # Set the database
    request.db_config.database = topology_manager_pb2.DBConfig.ARANGODB
    # Set the ArangoDB URL
    request.db_config.url = arango_url
    # Set the ArangoDB username
    request.db_config.username = arango_user
    # Set the ArangoDB password
    request.db_config.password = arango_password
    # Set verbose mode
    request.verbose = verbose
    # Get the reference of the stub
    stub = topology_manager_pb2_grpc.TopologyManagerStub(controller_channel)
    # Extract the topology
    response = stub.ExtractTopologyAndLoadOnDatabase(request)
    # Check the status code
    if response.status != nb_commons_pb2.STATUS_SUCCESS:
        return False       # TODO raise an exception?
    return True


def push_nodes_config(controller_channel, nodes_config):
    '''
    Push nodes configuration.
    '''
    # Create request message
    request = topology_manager_pb2.NodesConfigRequest()
    # Set the locator bits
    request.nodes_config.locator_bits = nodes_config['locator_bits']
    # Set the uSID ID bits
    request.nodes_config.locator_bits = nodes_config['usid_id_bits']
    # Add the nodes
    for node in nodes_config['nodes'].values():
        # Create a new node
        _node = request.nodes_config.nodes.add()
        _node.name = node['name']
        _node.grpc_ip = node['grpc_ip']
        _node.grpc_port = node['grpc_port']
        _node.uN = node['uN']
        _node.uDT = node['uDT']
        _node.fwd_engine = node['fwd_engine']
    #
    # Get the reference of the stub
    stub = topology_manager_pb2_grpc.TopologyManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.PushNodesConfig(request)
    # Check the status code and raise an exception if an error occurred
    utils.raise_exception_on_error(response.status)


def get_nodes_config(controller_channel):
    '''
    Get nodes configuration.
    '''
    # Create request message
    request = topology_manager_pb2.NodesConfigRequest()
    # Get the reference of the stub
    stub = topology_manager_pb2_grpc.TopologyManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.GetNodesConfig(request)
    #
    # Extract the nodes config
    nodes_config = {
        'locator_bits': response.nodes_config.locator_bits,
        'usid_id_bits': response.nodes_config.locator_bits,
        'nodes': []
    }
    # Add the nodes
    for node in response.nodes_config.nodes:
        nodes_config['nodes'].append({
            'name': node.name,
            'grpc_ip': node.grpc_ip,
            'grpc_port': node.grpc_port,
            'uN': node.uN,
            'uDT': node.uDT,
            'fwd_engine': node.fwd_engine
        })
    # Check the status code and raise an exception if an error occurred
    utils.raise_exception_on_error(response.status)
    # Return the nodes config
    return nodes_config
