from arango import ArangoClient
import yaml

USER = "root"
PASSWORD = "12345678"
ARANGO_URL = "http://localhost:8529"

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

# Create a new vertex collection named "routers" if it does not exist.
# This returns an API wrapper for "routers" vertex collection.
if topo_graph.has_vertex_collection('routers'):
    routers = topo_graph.vertex_collection('routers')
else:
    routers = topo_graph.create_vertex_collection('routers')

# Create a new vertex collection named "provider_hosts" if it does not exist.
# This returns an API wrapper for "provider_hosts" vertex collection.
if topo_graph.has_vertex_collection('provider_hosts'):
    hosts = topo_graph.vertex_collection('provider_hosts')
else:
    hosts = topo_graph.create_vertex_collection('provider_hosts')

# Create an edge definition named "core_links". This creates any missing
# collections and returns an API wrapper for "core_links" edge collection.
if topo_graph.has_edge_definition('core_links'):
    core_links = topo_graph.edge_collection("core_links")
else:
    core_links = topo_graph.create_edge_definition(
        edge_collection='core_links',
        from_vertex_collections=['routers'],
        to_vertex_collections=['routers']
    )

# Create an edge definition named "provider_host_links". This creates any missing
# collections and returns an API wrapper for "provider_host_links" edge collection.
if topo_graph.has_edge_definition('provider_host_links'):
    host_links = topo_graph.edge_collection("provider_host_links")
else:
    host_links = topo_graph.create_edge_definition(
        edge_collection='provider_host_links',
        from_vertex_collections=['routers', 'provider_hosts'],
        to_vertex_collections=['provider_hosts', 'routers']
    )

##############################################
############### populate graph ###############
##############################################

# nodes
with open('nodes.yaml') as f:
    nodes_dict = yaml.load(f, Loader=yaml.FullLoader)
    for node in nodes_dict:
        if node["type"] == "router":
            if not routers.has(node["_key"]):
                routers.insert(node)
            else:  # only specified fields are changed
                routers.update(node)
        elif node["type"] == "host":
            if not hosts.has(node["_key"]):
                hosts.insert(node)
            else:  # only specified fields are changed
                hosts.update(node)
        else:
            print("node type error")


# edges
with open('edges_2_collections.yaml') as f:
    edges_dict = yaml.load(f, Loader=yaml.FullLoader)
    for edge in edges_dict:
        if edge["type"] == "core":
            core_links.insert(edge)      # no control on key
        elif edge["type"] == "host":
            host_links.insert(edge)      # no control on key
        else:
            print("edge type error")
