#!/usr/bin/python

"""ArangoDB utilities"""

import yaml
from arango import ArangoClient

USER = "root"
PASSWORD = "12345678"
ARANGO_URL = "http://localhost:8529"
NODES_FILE = "nodes_hc.yaml"
EDGES_FILE = "edges_hc.yaml"

# Initialize the ArangoDB client.
client = ArangoClient(hosts=ARANGO_URL)

# Connect to "_system" database as root user.
# This returns an API wrapper for "_system" database.
sys_db = client.db('_system', username=USER, password=PASSWORD)

# Reset database if already existing
if sys_db.has_database('srv6_pm'):
    sys_db.delete_database('srv6_pm')
    sys_db.create_database('srv6_pm')
else:
    sys_db.create_database('srv6_pm')

# Connect to "srv6_pm" database as root user.
# This returns an API wrapper for "srv6_pm" database.
db = client.db('srv6_pm', username=USER, password=PASSWORD)

# Get the API wrapper for graph "topology".
if db.has_graph('topology'):
    topo_graph = db.graph('topology')
else:
    topo_graph = db.create_graph('topology')

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


# ##############################################
# ############### populate graph ###############
# ##############################################

# nodes
with open(NODES_FILE) as f:
    nodes_dict = yaml.load(f, Loader=yaml.FullLoader)
    for node in nodes_dict:
        if not nodes.has(node["_key"]):
            nodes.insert(node)
        else:  # only specified fields are changed
            nodes.update(node)

# edges
with open(EDGES_FILE) as f:
    edges_dict = yaml.load(f, Loader=yaml.FullLoader)
    for edge in edges_dict:
        edges.insert(edge)      # no control on key
