from arango import ArangoClient

USER = "root"
PASSWORD = "giulio"
ARANGO_URL = "http://192.168.56.101:8529"

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

##############################################
############### populate graph ###############
##############################################

# nodes collection (routers)
file_routers = open("routers.txt", "r")
for line in file_routers:
    [name, ext_reachability, ip_add] = line.split()
    if not nodes.has(name):
        nodes.insert({"_key": name, "type": "router", "ip_address": ip_add, "ext_reachability": ext_reachability})
    else:   # only specified fields are changed
        nodes.update({"_key": name, "type": "router", "ip_address": ip_add, "ext_reachability": ext_reachability})
file_routers.close()

# edges collection (core links)
file_core = open("topologia.txt", "r")
for line in file_core:
    line = line.split()
    router0 = line.pop(0).strip(":")    # router0 has a link to every router in list
    for router in line:
        router = str(router)
        name = router0 + "-" + router
        # print(name, router0, router)
        # if not edges.has(name):       # control on link id not done atm
        edges.insert({'_from': 'nodes/'+router0, '_to': 'nodes/'+router, 'type': 'core'})

# add hosts to node collection and hosts links to edges collection
file_hosts = open("hosts.txt")
for line in file_hosts:
    [host, router, ip_add] = line.split(",")
    if not nodes.has(host):
        nodes.insert({"_key": host, "type": "host", "ip_address": ip_add})
    else:
        nodes.update({"_key": host, "type": "host", "ip_address": ip_add})
    # insert edge in both directions
    edges.insert({'_from': 'nodes/' + host, '_to': 'nodes/' + router, 'type': 'host'})
    edges.insert({'_from': 'nodes/' + router, '_to': 'nodes/' + host, 'type': 'host'})
