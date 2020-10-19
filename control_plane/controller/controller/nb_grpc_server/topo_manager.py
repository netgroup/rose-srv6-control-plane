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
Northbound gRPC server. The Topology Manager implements different
control plane functionalities to extract and manage the network topology.
'''

# General imports
import logging
import os
from enum import Enum
# Proto dependencies
import nb_commons_pb2
import topology_manager_pb2
import topology_manager_pb2_grpc
# Controller dependencies
from controller import arangodb_utils
from controller import arangodb_driver
from controller import topo_utils
from controller.ti_extraction import connect_and_extract_topology_isis
from controller.ti_extraction import dump_topo_yaml

# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)


# Dict used to convert the python representation of node type to gRPC
# representation
node_type_to_grpc_repr = {
    'router': 'ROUTER',
    'host': 'HOST'
}
# Dict used to convert the gRPC representation of node type to python
# representation
grpc_repr_to_node_type = {v: k for k, v in node_type_to_grpc_repr.items()}

# Dict used to convert the python representation of edge type to gRPC
# representation
edge_type_to_grpc_repr = {
    'core': 'CORE',
    'edge': 'EDGE'
}
# Dict used to convert the gRPC representation of edge type to python
# representation
grpc_repr_to_edge_type = {v: k for k, v in edge_type_to_grpc_repr.items()}


class RoutingProtocol(Enum):
    """
    Enumeration for routing protocol.
    """
    ISIS = topology_manager_pb2.Protocol.Value('ISIS')


class TopoManagerException(Exception):
    """
    Generic topology manager exception.
    """
    pass


def extract_topology_isis(nodes, password, addrs_config=None,
                          hosts_config=None, verbose=False):
    '''
    Extract the network topology from a set of nodes running
    the IS-IS protocol.

    :param nodes: A list of nodes running the IS-IS protocol. Each node is
                  represented by a string containing its IP address and the
                  port on which the IS-IS daemon is listening separated by a
                  comma character.
                  (e.g. ['2000::1-2608', '2000::2-2608']).
    :type nodes: list
    :param password: The password used to log in to the IS-IS daemon.
    :type password: str
    :param addrs_config: Dict containing the addressing plan to assign to the
                         extracted topology. If not provided, the IP address
                         information is not added to the extracted topology.
    :type addrs_config: dict, optional
    :param hosts_config: Dict containing the hosts configuration to assign to
                         the extracted topology. If not provided, the hosts
                         information is not added to the extracted topology.
    :type hosts_config: dict, optional
    :param verbose: Define whether to enable or not the verbose mode
                    (default: False).
    :type verbose: bool, optional
    :return: Tuple containing two items. The first element is the list of
             nodes and the second item is the list of edges. Both nodes and
             edges representation are suitable for exporting to a YAML file.
    :rtype: tuple
    '''
    # Try to establish a connection to a node in the nodes list and extract
    # the topology
    nodes, edges, node_to_systemid = connect_and_extract_topology_isis(
        ips_ports=nodes,
        isisd_pwd=password,
        verbose=verbose
    )
    # Nodes, edges and node_to_systemid should be not None
    # If one of these elements is None, something went wrong in the topology
    # extraction process
    if nodes is None or edges is None or node_to_systemid is None:
        logger.error('Cannot extract topology')
        raise TopoManagerException('Cannot extract topology')
    # Convert the extracted topology (i.e. nodes and edges) to a intermediate
    # representation suitable for exporting to a YAML file
    nodes, edges = dump_topo_yaml(
        nodes=nodes,
        edges=edges,
        node_to_systemid=node_to_systemid
    )
    # Add IP addresses information
    if addrs_config is not None:
        arangodb_utils.fill_ip_addresses_from_list(nodes, addrs_config)
    # Add hosts information
    if hosts_config is not None:
        arangodb_utils.add_hosts_from_list(nodes, edges, hosts_config)
    # Return a representation of nodes and edges suitable for export in YAML
    # format
    return nodes, edges


class TopologyManager(topology_manager_pb2_grpc.TopologyManagerServicer):
    '''
    gRPC request handler.
    '''

    def __init__(self, db_client=None):
        """
        Topology Manager init method.

        :param db_client: ArangoDB client.
        :type db_client: class: `arango.client.ArangoClient`
        """
        # Establish a connection to the "topology" database
        # We will keep the connection open forever
        self.db_conn = arangodb_driver.connect_db(
            client=db_client,
            db_name='topology',
            username=os.getenv('ARANGO_USER'),
            password=os.getenv('ARANGO_PASSWORD')
        )
        # Init database and return nodes and edges collection
        self.nodes_collection, self.edges_collection = \
            arangodb_utils.initialize_db(
                arango_url=os.getenv('ARANGO_URL'),
                arango_user=os.getenv('ARANGO_USER'),
                arango_password=os.getenv('ARANGO_PASSWORD')
            )  # TODO reuse the existing db connection

    def ExtractTopology(self, request, context):
        '''
        Extract the network topology from a set of nodes running
        a distance vector routing protocol (e.g. IS-IS).
        '''
        # pylint: disable=too-many-arguments
        #
        # Create the reply message
        response = topology_manager_pb2.TopologyManagerReply()
        #
        # Extract the parameters from the gRPC request
        #
        # Param isis_nodes: list of ip-port
        # (e.g. [2000::1-2608,2000::2-2608])
        nodes = list()
        for node in request.nodes:
            nodes.append('%s-%s' % (node.address, node.port))
        # Addresses configuration
        addrs_config = list()
        for addr_config in request.addrs_config.addrs:
            addrs_config.append({
                'node': addr_config.node,
                'ip_address': addr_config.ip_address
            })
        # Hosts configuration
        hosts_config = list()
        for host_config in request.hosts_config.hosts:
            hosts_config.append({
                'name': host_config.name,
                'ip_address': host_config.ip_address,
                'gw': host_config.gateway
            })
        # Dispatch based on the routing protocol
        if request.protocol == RoutingProtocol.ISIS:
            # Requested extraction from ISIS protocol
            #
            # Extract the topolgy
            nodes, edges = extract_topology_isis(
                nodes=nodes,
                password=request.password,
                addrs_config=addrs_config,
                hosts_config=hosts_config,
                verbose=request.verbose)
            # Add the nodes to the response message
            for node in nodes:
                # Add a new node to the response message
                _node = response.topology.nodes.add()
                # Fill "key" field
                _node.id = node['_key']
                # Fill "ext_reachability" field
                if 'ext_reachability' in node:
                    _node.ext_reachability = node['ext_reachability']
                # Fill "ip_address" field
                if 'ip_address' in node:
                    _node.ip_address = node['ip_address']
                # Set node type (e.g. "ROUTER" or "HOST")
                _node.type = topology_manager_pb2.NodeType.Value(
                    node_type_to_grpc_repr[node['type']])
            # Add the edges to the response message
            for edge in edges:
                # Add a new edge to the response message
                _edge = response.topology.links.add()
                # Fill "key" field
                _edge.id = edge['_key']
                # Fill "from" field
                _edge.source = edge['_from']
                # Fill "to" field
                _edge.target = edge['_to']
                # Set edge type (e.g. "CORE" or "EDGE")
                _edge.type = topology_manager_pb2.LinkType.Value(
                    edge_type_to_grpc_repr[edge['type']])
            # Set status code
            response.status = nb_commons_pb2.STATUS_SUCCESS
            # Send the reply
            return response
        # Unknown or unsupported routing protocol
        logger.error('Unknown/Unsupported routing protocol: %s',
                     topology_manager_pb2.Protocol.Name(request.protocol))
        return topology_manager_pb2_grpc.TopologyManagerReply(
            status=nb_commons_pb2.STATUS_OPERATION_NOT_SUPPORTED
        )

    def LoadTopology(self, request, context):
        '''
        Load a network topology on a Arango database.
        '''
        # pylint: disable=too-many-arguments
        #
        # Extract the parameters from the gRPC request
        #
        # Extract the nodes from the gRPC request
        nodes = list()
        for node in request.topology.nodes:
            nodes.append({
                '_key': node.id,
                'ext_reachability': node.ext_reachability,
                'ip_address': node.ip_address,
                'type': grpc_repr_to_node_type[
                    topology_manager_pb2.NodeType.Name(node.type)]
            })
        # Extract the edges from the gRPC request
        edges = list()
        for edge in request.topology.links:
            edges.append({
                '_key': edge.id,
                '_from': edge.source,
                '_to': edge.target,
                'type': grpc_repr_to_edge_type[
                    topology_manager_pb2.LinkType.Name(edge.type)]
            })
        # Load nodes and edges on ArangoDB
        arangodb_utils.load_topo_on_arango(
            arango_url=None,  # FIXME: unused argument, to be fixed
            user=None,  # FIXME: unused argument, to be fixed
            password=None,  # FIXME: unused argument, to be fixed
            nodes=nodes,
            edges=edges,
            nodes_collection=self.nodes_collection,
            edges_collection=self.edges_collection,
            verbose=request.verbose
        )
        # Done, return the reply
        return topology_manager_pb2.TopologyManagerReply(
            status=nb_commons_pb2.STATUS_SUCCESS)

    def ExtractAndLoadTopology(self, request, context):
        '''
        Extract the topology from a set of nodes running a distance vector
        routing protocol (e.g. IS-IS) and load it on a Arango database.
        This is a stream RPC.
        '''
        # pylint: disable=too-many-arguments
        #
        # Create the reply message
        response = topology_manager_pb2.TopologyManagerReply()
        #
        # Extract the parameters from the gRPC request
        #
        # Param isis_nodes: list of ip-port
        # (e.g. [2000::1-2608,2000::2-2608])
        nodes = list()
        for node in request.nodes:
            nodes.append('%s-%s' % (node.address, node.port))
        # Addresses configuration
        addrs_config = list()
        for addr_config in request.addrs_config.addrs:
            addrs_config.append({
                'node': addr_config.node,
                'ip_address': addr_config.ip_address
            })
        # If no addrs config specified, we set the variable to None
        # as required by "extract_topo_from_isis_and_load_on_arango_stream()"
        # which is invoked below
        if len(addrs_config) == 0:
            addrs_config = None
        # Hosts configuration
        hosts_config = list()
        for host_config in request.hosts_config.hosts:
            hosts_config.append({
                'name': host_config.name,
                'ip_address': host_config.ip_address,
                'gw': host_config.gateway
            })
        # If no hosts config specified, we set the variable to None
        # as required by "extract_topo_from_isis_and_load_on_arango_stream()"
        # which is invoked below
        if len(hosts_config) == 0:
            hosts_config = None
        # Dispatch based on the routing protocol
        if request.protocol == RoutingProtocol.ISIS:
            # ISIS protocol
            #
            # Extract the topology and load it on the Arango database
            try:
                for nodes, edges in arangodb_utils.extract_topo_from_isis_and_load_on_arango_stream(
                    isis_nodes=nodes,
                    isisd_pwd=request.password,
                    nodes_collection=self.nodes_collection,
                    edges_collection=self.edges_collection,
                    addrs_config=addrs_config,
                    hosts_config=hosts_config,
                    period=request.period,
                    verbose=request.verbose
                ):
                    # Set the nodes
                    for node in nodes:
                        # Add a new node to the response message
                        _node = response.topology.nodes.add()
                        # Fill "key" field
                        _node.id = node['_key']
                        # Fill "ext_reachability" field
                        if node.get('ext_reachability') is not None:
                            _node.ext_reachability = node['ext_reachability']
                        # Fill "ip_address" field
                        if node.get('ip_address') is not None:
                            _node.ip_address = node['ip_address']
                        # Set node type (e.g. "ROUTER" or "HOST")
                        _node.type = topology_manager_pb2.NodeType.Value(
                            node_type_to_grpc_repr[node['type']])
                    # Set the edges
                    for edge in edges:
                        # Add the edges to the response message
                        _edge = response.topology.links.add()
                        # Fill "key" field
                        _edge.id = edge['_key']
                        # Fill "from" field
                        _edge.source = edge['_from']
                        # Fill "to" field
                        _edge.target = edge['_to']
                        # Set edge type (e.g. "CORE" or "EDGE")
                        _edge.type = topology_manager_pb2.LinkType.Value(
                            edge_type_to_grpc_repr[edge['type']])
                    # Set status code
                    response.status = nb_commons_pb2.STATUS_SUCCESS
                    # Send the reply
                    yield response
            except arangodb_utils.TopologyExtractionException as err:
                # Something went wrong in topology extraction
                logger.error('Error in topology extraction: ', str(err))
                response.status = nb_commons_pb2.STATUS_INTERNAL_ERROR
                return response
        else:
            # Unknown or unsupported routing protocol
            logger.error('Unknown/Unsupported routing protocol: %s',
                         topology_manager_pb2.Protocol.Name(request.protocol))
            response.status = nb_commons_pb2.STATUS_OPERATION_NOT_SUPPORTED
            return response

    def PushNodesConfig(self, request, context):
        '''
        Load nodes configuration. Configuration consists of:
        -    locator_bits: an integer representing the number of bits in the
             locator part of the SID;
        -    usid_id_bits: an integer representing the number of bits in the
             MicroSID identifier part of the SID;
        -    nodes: a list of nodes represented as dicts containing the
             following fields:
             -    name: name of the node;
             -    grpc_ip: gRPC address of the node;
             -    grpc_port: gRPC port number of the node;
             -    uN: uN SID;
             -    uDT: uDT SID (used for the decap operation),
             -    fwd_engine: forwarding engine.
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
        # Load the nodes configuration on the database
        topo_utils.load_nodes_config(nodes_config)
        # Create reply message
        return topology_manager_pb2.NodesConfigReply(
            status=nb_commons_pb2.STATUS_SUCCESS
        )

    def GetNodesConfig(self, request, context):
        '''
        Retrieve nodes configuration. Configuration consists of:
        -    locator_bits: an integer representing the number of bits in the
             locator part of the SID;
        -    usid_id_bits: an integer representing the number of bits in the
             MicroSID identifier part of the SID;
        -    nodes: a list of nodes represented as dicts containing the
             following fields:
             -    name: name of the node;
             -    grpc_ip: gRPC address of the node;
             -    grpc_port: gRPC port number of the node;
             -    uN: uN SID;
             -    uDT: uDT SID (used for the decap operation),
             -    fwd_engine: forwarding engine.
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
                # Create a new node
                _node = response.nodes_config.nodes.add()
                # Fill "name" field
                _node.name = node['name']
                # Fill "grpc_ip" field
                _node.grpc_ip = node['grpc_ip']
                # Fill "grpc_port" field
                _node.grpc_port = node['grpc_port']
                # Fill "uN" field
                _node.uN = node['uN']
                # Fill "uDT" field
                _node.uDT = node['uDT']
                # Fill "fwd_engine" field
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
