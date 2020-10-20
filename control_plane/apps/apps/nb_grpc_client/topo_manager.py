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


"""
This module provides an implementation of a Topology Manager for the
Northbound gRPC client.
"""

# General imports
import logging
from enum import Enum
# Proto dependencies
import topology_manager_pb2
import topology_manager_pb2_grpc
from apps.nb_grpc_client import utils


# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)


# ############################################################################
# Routing Protocol
class RoutingProtocol(Enum):
    """
    Routing protocol.
    """
    ISIS = topology_manager_pb2.Protocol.Value('ISIS')


# Mapping python representation of Routing Protocol to gRPC representation
py_to_grpc_routing_protocol = {
    'isis': RoutingProtocol.ISIS
}

# Mapping gRPC representation of Routing Protocol to python representation
grpc_to_py_routing_protocol = {
    v: k for k, v in py_to_grpc_routing_protocol.items()}


# ############################################################################
# Node Type
class NodeType(Enum):
    """
    Node type.
    """
    ROUTER = topology_manager_pb2.NodeType.Value('ROUTER')
    HOST = topology_manager_pb2.NodeType.Value('HOST')


# Mapping python representation of Node Type to gRPC representation
py_to_grpc_node_type = {
    'router': NodeType.ROUTER,
    'host': NodeType.HOST
}

# Mapping gRPC representation of Node Type to python representation
grpc_to_py_node_type = {
    v: k for k, v in py_to_grpc_node_type.items()}


# ############################################################################
# Link Type
class LinkType(Enum):
    """
    Link type.
    """
    CORE = topology_manager_pb2.LinkType.Value('CORE')
    EDGE = topology_manager_pb2.LinkType.Value('EDGE')


# Mapping python representation of Link Type to gRPC representation
py_to_grpc_link_type = {
    'core': LinkType.CORE,
    'edge': LinkType.EDGE
}

# Mapping gRPC representation of Link Type to python representation
grpc_to_py_link_type = {
    v: k for k, v in py_to_grpc_link_type.items()}


# ############################################################################
# gRPC client APIs

def extract_topo_from_isis(controller_channel, isis_nodes, isisd_pwd,
                           addrs_config=None, hosts_config=None,
                           verbose=False):
    """
    Extract the network topology from a set of nodes running
    ISIS protocol.
    """
    # pylint: disable=too-many-arguments
    #
    # Create request message
    request = topology_manager_pb2.TopologyManagerRequest()
    # Set the protocol
    request.protocol = RoutingProtocol.ISIS
    # Set the IS-IS nodes
    for isis_node in isis_nodes.split(','):
        node = request.nodes.add()
        node.address = isis_node.split('-')[0]  # FIXME
        node.port = isis_node.split('-')[1]  # FIXME
    # Set the IS-IS password
    request.password = isisd_pwd
    # Set verbose mode
    request.verbose = verbose
    # Set the addresses configuration
    for addr in addrs_config:
        _addr = request.addrs_config.addrs.add()
        _addr.node = addr['node']
        _addr.ip_address = addr['ip_address']
    # Set the hosts configuration
    for host in hosts_config:
        _host = request.hosts_config.hosts.add()
        _host.name = host['name']
        _host.ip_address = host['ip_address']
        _host.gateway = host['gw']
    # Request message is ready
    #
    # Get the reference of the stub
    stub = topology_manager_pb2_grpc.TopologyManagerStub(controller_channel)
    # Extract the topology
    response = stub.ExtractTopology(request)
    # Check the status code
    utils.raise_exception_on_error(response.status)
    # No errors during the topology extraction
    #
    # Extract the nodes from the gRPC response
    nodes = list()
    for node in response.topology.nodes:
        if node.type not in grpc_to_py_node_type:
            # Invalid node type
            logger.error('Invalid node type: %s', node.type)
            raise utils.InvalidArgumentError
        nodes.append({
            '_key': node.id,
            'ext_reachability': node.ext_reachability,
            'ip_address': node.ip_address,
            'type': grpc_to_py_node_type[node.type]
        })
    # Extract the edges from the gRPC response
    edges = list()
    for edge in response.topology.links:
        if edge.type not in grpc_to_py_link_type:
            # Invalid edge type
            logger.error('Invalid link type: %s', edge.type)
            raise utils.InvalidArgumentError
        edges.append({
            '_key': edge.id,
            '_from': edge.source,
            '_to': edge.target,
            'type': grpc_to_py_link_type[edge.type]
        })
    # Done, return the topology
    return nodes, edges


def load_topo_on_arango(controller_channel, nodes_config, edges_config,
                        verbose=False):
    """
    Load a network topology on a Arango database.
    """
    # pylint: disable=too-many-arguments
    #
    # Create request message
    request = topology_manager_pb2.TopologyManagerRequest()
    # Set verbose mode
    request.verbose = verbose
    # Set the nodes
    for node in nodes_config:
        _node = request.topology.nodes.add()
        _node.id = node['_key']
        if 'ext_reachability' in node:
            _node.ext_reachability = node['ext_reachability']
        if 'ip_address' in node:
            _node.ip_address = node['ip_address']
        if node['type'] not in py_to_grpc_node_type:
            # Invalid node type
            logger.error('Invalid node type %s', node['type'])
            raise utils.InvalidArgumentError
        _node.type = py_to_grpc_node_type[node['type']]
    # Set the edges
    for edge in edges_config:
        _edge = request.topology.links.add()
        _edge.id = edge['_key']
        _edge.source = edge['_from']
        _edge.target = edge['_to']
        if edge['type'] not in py_to_grpc_link_type:
            # Invalid edge type
            logger.error('Invalid link type %s', edge['type'])
            raise utils.InvalidArgumentError
        _edge.type = py_to_grpc_link_type[edge['type']]
    # Request message is ready
    #
    # Get the reference of the stub
    stub = topology_manager_pb2_grpc.TopologyManagerStub(controller_channel)
    # Extract the topology
    response = stub.LoadTopology(request)
    # Check the status code
    utils.raise_exception_on_error(response.status)
    # No errors during the operation
    #
    # Extract the nodes from the gRPC response
    nodes = list()
    for node in response.topology.nodes:
        if node.type not in grpc_to_py_node_type:
            # Invalid node type
            logger.error('Invalid node type: %s', node.type)
            raise utils.InvalidArgumentError
        nodes.append({
            '_key': node.id,
            'ext_reachability': node.ext_reachability,
            'ip_address': node.ip_address,
            'type': grpc_to_py_node_type[node.type]
        })
    # Extract the edges from the gRPC response
    edges = list()
    for edge in response.topology.links:
        if edge.type not in grpc_to_py_link_type:
            # Invalid edge type
            logger.error('Invalid link type: %s', edge.type)
            raise utils.InvalidArgumentError
        edges.append({
            '_key': edge.id,
            '_from': edge.source,
            '_to': edge.target,
            'type': grpc_to_py_link_type[edge.type]
        })
    # Done, return the topology
    return nodes, edges


def extract_topo_from_isis_and_load_on_arango(controller_channel,
                                              isis_nodes, isisd_pwd,
                                              addrs_config=None,
                                              hosts_config=None,
                                              period=0, verbose=False):
    """
    Extract the topology from a set of nodes running ISIS protocol
    and load it on a Arango database
    """
    # pylint: disable=too-many-arguments
    #
    # Create request message
    request = topology_manager_pb2.TopologyManagerRequest()
    # Set the protocol
    request.protocol = RoutingProtocol.ISIS
    # Set the IS-IS nodes
    for isis_node in isis_nodes:
        node = request.nodes.add()
        node.address = isis_node.split('-')[0]  # FIXME
        node.port = int(isis_node.split('-')[1])  # FIXME
    # Set the period (i.e the interval between two consecutive extractions)
    request.period = period
    # Set the IS-IS password
    request.password = isisd_pwd
    # Set verbose mode
    request.verbose = verbose
    # Set the addresses configuration
    if addrs_config is not None:
        for addr in addrs_config:
            _addr = request.addrs_config.addrs.add()
            _addr.node = addr['node']
            _addr.ip_address = addr['ip_address']
    # Set the hosts configuration
    if hosts_config is not None:
        for host in hosts_config:
            _host = request.hosts_config.hosts.add()
            _host.name = host['name']
            _host.ip_address = host['ip_address']
            _host.gateway = host['gw']
    # Request message is ready
    #
    # Get the reference of the stub
    stub = topology_manager_pb2_grpc.TopologyManagerStub(controller_channel)
    # Extract the topology
    for response in stub.ExtractAndLoadTopology(request):
        # Check the status code
        utils.raise_exception_on_error(response.status)
        # No errors during the topology extraction
        #
        # Extract the nodes from the gRPC response
        nodes = list()
        for node in response.topology.nodes:
            if node.type not in grpc_to_py_node_type:
                # Invalid node type
                logger.error('Invalid node type: %s', node.type)
                raise utils.InvalidArgumentError
            nodes.append({
                '_key': node.id,
                'ext_reachability': node.ext_reachability,
                'ip_address': node.ip_address,
                'type': grpc_to_py_node_type[node.type]
            })
        # Extract the edges from the gRPC response
        edges = list()
        for edge in response.topology.links:
            if edge.type not in grpc_to_py_link_type:
                # Invalid link type
                logger.error('Invalid link type: %s', edge.type)
                raise utils.InvalidArgumentError
            edges.append({
                '_key': edge.id,
                '_from': edge.source,
                '_to': edge.target,
                'type': grpc_to_py_link_type[edge.type]
            })
        # Done, return the topology
        yield nodes, edges


def topology_information_extraction_isis(controller_channel,
                                         routers, period, isisd_pwd,
                                         addrs_config=None, hosts_config=None,
                                         verbose=False):
    """
    Run periodical topology extraction
    """
    # pylint: disable=too-many-arguments, unused-argument
    #
    # Create request message
    request = topology_manager_pb2.TopologyManagerRequest()
    # Set the protocol
    request.protocol = RoutingProtocol.ISIS
    # Set the IS-IS nodes
    for isis_node in routers.split(','):
        node = request.nodes.add()
        node.address = isis_node.split('-')[0]  # FIXME
        node.port = isis_node.split('-')[1]  # FIXME
    # Set the IS-IS password
    request.password = isisd_pwd
    # Set the period
    request.period = period
    # Set verbose mode
    request.verbose = verbose
    # Set the addresses configuration
    if addrs_config is not None:
        for addr in addrs_config:
            _addr = request.addrs_config.addrs.add()
            _addr.node = addr['node']
            _addr.ip_address = addr['ip_address']
    # Set the hosts configuration
    if hosts_config is not None:
        for host in hosts_config:
            _host = request.hosts_config.hosts.add()
            _host.name = host['name']
            _host.ip_address = host['ip_address']
            _host.gateway = host['gw']
    # Request message is ready
    #
    # Get the reference of the stub
    stub = topology_manager_pb2_grpc.TopologyManagerStub(controller_channel)
    # Extract the topology
    for response in stub.ExtractAndLoadTopology(request):
        # Check the status code
        utils.raise_exception_on_error(response.status)
        # No errors during the topology extraction
        #
        # Extract the nodes from the gRPC response
        nodes = list()
        for node in response.topology.nodes:
            if node.type not in grpc_to_py_node_type:
                # Invalid node type
                logger.error('Invalid node type: %s', node.type)
                raise utils.InvalidArgumentError
            nodes.append({
                '_key': node.id,
                'ext_reachability': node.ext_reachability,
                'ip_address': node.ip_address,
                'type': grpc_to_py_node_type[node.type]
            })
        # Extract the edges from the gRPC response
        edges = list()
        for edge in response.topology.links:
            if edge.type not in grpc_to_py_link_type:
                # Invalid link type
                logger.error('Invalid link type: %s', edge.type)
                raise utils.InvalidArgumentError
            edges.append({
                '_key': edge.id,
                '_from': edge.source,
                '_to': edge.target,
                'type': grpc_to_py_link_type[edge.type]
            })
        # Done, return the topology
        yield nodes, edges


def push_nodes_config(controller_channel, nodes_config):
    """
    Push nodes configuration.
    """
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
    # Request message is ready
    #
    # Get the reference of the stub
    stub = topology_manager_pb2_grpc.TopologyManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.PushNodesConfig(request)
    # Check the status code and raise an exception if an error occurred
    utils.raise_exception_on_error(response.status)


def get_nodes_config(controller_channel):
    """
    Get nodes configuration.
    """
    # Create request message
    request = topology_manager_pb2.NodesConfigRequest()
    # Get the reference of the stub
    stub = topology_manager_pb2_grpc.TopologyManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.GetNodesConfig(request)
    # Check the status code and raise an exception if an error occurred
    utils.raise_exception_on_error(response.status)
    # No errors during the operation
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
    # Return the nodes config
    return nodes_config
