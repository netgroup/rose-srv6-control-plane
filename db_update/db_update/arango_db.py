#!/usr/bin/python

"""ArangoDB utilities"""

import yaml
from arango import ArangoClient

USER = "root"
PASSWORD = "12345678"
ARANGO_URL = "http://localhost:8529"
NODES_FILE = "nodes_hc.yaml"
EDGES_FILE = "edges_hc.yaml"


def initialize_db(
        arango_url=ARANGO_URL,
        arango_user=USER,
        arango_password=PASSWORD):
    """Initialize database"""

    # Initialize the ArangoDB client.
    client = ArangoClient(hosts=arango_url)

    # Connect to "_system" database as root user.
    # This returns an API wrapper for "_system" database.
    sys_db = client.db(
        '_system',
        username=arango_user,
        password=arango_password)

    # Reset database if already existing
    if sys_db.has_database('srv6_pm'):
        # sys_db.delete_database('srv6_pm')
        # sys_db.create_database('srv6_pm')
        pass
    else:
        sys_db.create_database('srv6_pm')

    # Connect to "srv6_pm" database as root user.
    # This returns an API wrapper for "srv6_pm" database.
    database = client.db('srv6_pm', username=arango_user,
                         password=arango_password)

    # Get the API wrapper for graph "topology".
    if database.has_graph('topology'):
        topo_graph = database.graph('topology')
    else:
        topo_graph = database.create_graph('topology')

    # Create a new vertex collection named "nodes" if it does not exist.
    # This returns an API wrapper for "nodes" vertex collection.
    if topo_graph.has_vertex_collection('nodes'):
        nodes = topo_graph.vertex_collection('nodes')
    else:
        nodes = topo_graph.create_vertex_collection('nodes')

    # Create an edge definition named "edges". This creates any missing
    # collections and returns an API wrapper for "edges" edge collection.
    if topo_graph.has_edge_definition('edges'):
        edges = topo_graph.edge_collection("edges")
    else:
        edges = topo_graph.create_edge_definition(
            edge_collection='edges',
            from_vertex_collections=['nodes'],
            to_vertex_collections=['nodes']
        )

    return nodes, edges


# ##############################################
# ############### populate graph ###############
# ##############################################

def populate_yaml(nodes, edges, nodes_file=NODES_FILE, edges_file=EDGES_FILE):
    """Populate database from YAML files"""

    # nodes
    with open(nodes_file) as file:
        nodes_dict = yaml.load(file, Loader=yaml.FullLoader)
        for node in nodes_dict:
            if not nodes.has(node["_key"]):
                nodes.insert(node)
            else:  # only specified fields are changed
                nodes.update(node)

    # edges
    with open(edges_file) as file:
        edges_dict = yaml.load(file, Loader=yaml.FullLoader)
        for edge in edges_dict:
            edges.insert(edge)      # no control on key


def populate(nodes, edges, nodes_dict, edges_dict):
    """Populate database from nodes and edges dicts"""

    # nodes
    for node in nodes_dict:
        if not nodes.has(node["_key"]):
            nodes.insert(node)
        else:  # only specified fields are changed
            nodes.update(node)

    # edges
    for edge in edges_dict:
        edges.insert(edge)      # no control on key


def populate2(nodes, edges, nodes_dict, edges_dict):
    """Populate database from nodes and edges dicts"""

    # nodes
    for node in nodes_dict:
        if not nodes.has(node["_key"]):
            nodes.insert(node)
        else:  # only specified fields are changed
            nodes.update(node)

    # edges
    for edge in edges_dict:
        # Cannot work now, because edge links do not have a key
        if not edges.has(edge["_key"]):  # key is ip address of subnet
            edges.insert(edge)
        else:  # only specified fields are changed
            edges.update(edge)


def populate_yaml2(nodes, edges, nodes_file=NODES_FILE, edges_file=EDGES_FILE):
    """Populate database from YAML"""

    # nodes
    with open(nodes_file) as file:
        nodes_dict = yaml.load(file, Loader=yaml.FullLoader)
        for node in nodes_dict:
            if not nodes.has(node["_key"]):
                nodes.insert(node)
            else:  # only specified fields are changed
                nodes.update(node)

    # edges
    with open(edges_file) as file:
        edges_dict = yaml.load(file, Loader=yaml.FullLoader)
        for edge in edges_dict:
            if not edges.has(edge["_key"]):  # key is ip address of subnet
                edges.insert(edge)
            else:  # only specified fields are changed
                edges.update(edge)
