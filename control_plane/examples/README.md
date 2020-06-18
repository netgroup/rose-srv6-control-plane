# Controller APIs and examples

This directory contains several usage examples of the Controller APIs.

The Controller uses the gRPC protocol to interact with the nodes. A gRPC server must be run in each node that you want to control from the Controller.


## APIs

### gRPC server (on the nodes)
To get a list of the parameters supported by the gRPC server, you can run this command:


```
# python node-manager --help
usage: node_manager [-h] [-e ENV_FILE] [-g GRPC_IP] [-r GRPC_PORT] [-s] [-c SERVER_CERT] [-k SERVER_KEY] [-d]

gRPC Southbound APIs for SRv6 Controller

optional arguments:
-h, --help            show this help message and exit
-e ENV_FILE, --env-file ENV_FILE
                        Path to the .env file containing the parameters for the node manager
-g GRPC_IP, --grpc-ip GRPC_IP
                        IP of the gRPC server
-r GRPC_PORT, --grpc-port GRPC_PORT
                        Port of the gRPC server
-s, --secure          Activate secure mode
-c SERVER_CERT, --server-cert SERVER_CERT
                        Server certificate file
-k SERVER_KEY, --server-key SERVER_KEY
                        Server key file
-d, --debug           Activate debug logs
```

### gRPC client (on the Controller)
In order to interact with the controller, you can use the CLI or you can import the Controller modules in your Python application and use the APIs offered by the Controller.

This section describes the Controller APIs.

* get_grpc_session
    ```
    get_grpc_session(server_ip, server_port)
    Create and return a gRPC Channel to a server

    Params:
    server_ip - IP address of the gRPC server
    server_port - port on which the gRPC server is listening
    ```

* handle_srv6_path
    ```
    handle_srv6_path(op, channel, destination, segments=[],
                    device='', encapmode="encap", table=-1, metric=-1)
    Handle seg6 routes

    Params:
    op - add, get, change, del
    channel - the gRPC Channel to the gRPC server
    destination - the destination of the seg6 route
    segments - list of segments
    device - any non-loopback interface
    encapmode - encap, inline, l2encap
    table - routing table where the seg6 route must be inserted
    metric - the metric value associated to the seg6 route
    ```

* handle_srv6_behavior
    ```
    handle_srv6_behavior(op, channel, segment, action='', device='',
                            table=-1, nexthop="", lookup_table=-1,
                            interface="", segments=[], metric=-1)
    Handle seg6local routes

    Params:
    op - add, get, change, del
    channel - the gRPC Channel to the gRPC server
    segment - the destination of the seg6local route (i.e. the SID associated to the route)
    action - the action of the seg6local route (e.g. End.DT6, End.DX2, …)
    nexthop - the nexthop (used by End.DX4, End.DX6)
    lookup_table - the table used by End.DT4 and End.DT6 actions
    interface - the outgoing interface used by End.DX2 action
    segments - list of segments (used by B6.Encaps behavior)
    device - any non-loopback interface
    table - routing table where the seg6 route must be inserted
    metric - the metric value associated to the seg6 route
    ```

* extract_topo_from_isis
    ```
    extract_topo_from_isis(isis_nodes, nodes_yaml, edges_yaml, verbose=False)
    Extract the topology from a set of nodes running ISIS protocol and export nodes and edges of the graph in YAML format

    Params:
    isis_nodes - list of pairs <ip-port> where IP is the IP address of a router running ISIS protocol and port is the port number on which isisd is listening
    nodes_yaml - filename of the nodes
    edges_yaml - filename of the edges
    verbose - define whether the verbose mode should be enabled or not
    ```

* load_topo_on_arango
    ```
    load_topo_on_arango(arango_url, user, password,
                        nodes_yaml, edges_yaml, verbose=False)
    Read nodes and edges from YAML files and load the topology on ArangoDB.

    Params:
    arango_url - the URL of ArangoDB
    user - user of ArangoDB
    password - password of ArangoDB
    nodes_yaml - input file containing the nodes of the topology in YAML format
    edges_yaml - input file containing the edges of the topology in YAML format
    verbose - define whether the verbose mode should be enabled or not
    ```

* extract_topo_from_isis_and_load_on_arango
    ```
    extract_topo_from_isis_and_load_on_arango(isis_nodes, arango_url,
                                            user, password, nodes_yaml,
                                            edges_yaml, verbose=False)
    Extract the topology from ISIS, export it in YAML format and load the topology on ArangoDB.

    Params:
    isis_nodes - list of pair <ip-port> where IP is the IP address of a router running ISIS protocol and port is the port number on which isisd is listening
    nodes_yaml - filename of the nodes
    edges_yaml - filename of the edges
    arango_url - the URL of ArangoDB
    user - user of ArangoDB
    password - password of ArangoDB
    nodes_yaml - input file containing the nodes of the topology in YAML format
    edges_yaml - input file containing the edges of the topology in YAML format
    verbose - define whether the verbose mode should be enabled or not
    ```


### Usage examples

#### Prerequisites
This tutorial assumes that you have installed the Node Manager and the Controller. If you haven't installed them, check the documentation of the Controller and Node Manager.
The following examples are referred to a topology emulated using the open-source emulator Mininet. The topology is available at [SRv6 tutorial](https://github.com/netgroup/rose-srv6-tutorial/tree/master/nets/8r-1c-in-band-isis).

#### Create a bidirectional tunnel between h11 and h83, passing through router r4 – the resulting path is: r1 r2 r3 r4 r6 r8

* implicit decap solution (see examples/create_tunnel_r1r4r8_nodecap.py)

    First, you need to import the python script srv6_controller.py 

    ```python
    from srv6_controller import *
    ```

    Create a gRPC Channel to the gRPC server executed on r1

    ```python
    r1_chan = get_grpc_session(server_ip='fcff:1::1', server_port=12345)
    ```

    Create a gRPC Channel to the gRPC server executed on r8

    ```python
    r8_chan = get_grpc_session(server_ip='fcff:8::1', server_port=12345)
    ```

    1. set tunnel from r1 to r8 for fd00:0:83::/64

        ```python
        handle_srv6_path('add', r1_chan, destination='fd00:0:83::/64', segments=['fcff:4::1', 'fcff:8::1'], device='r1-h11', metric=200)
        ```

        on r8: no explicit decap instruction is needed because net.ipv6.conf.*.seg6_enabled=1 metric 200

    1. set tunnel from r8 to r1 for fd00:0:11::/64

        ```python
        handle_srv6_path('add', r8_chan, destination='fd00:0:11::/64', segments=['fcff:4::1', 'fcff:1::1'], device='r8-h83', metric=200)
        ```

        on r1: no explicit decap instruction is needed because net.ipv6.conf.*.seg6_enabled=1 metric 200

    Close the gRPC Channels

    ```python
    r1_chan.close()
    r8_chan.close()
    ```

    after the tunnel is setup, you can ping from h11 to h83 and vice versa

    ```console
    h11# ping6 fd00:0:83::2
    h83# ping6 fd00:0:11::2
    ```

    on recent versions of Linux kernel (>=5.5) it is also possible to ping the router IP address on 
    the interface with the host, while on previous ones it was not possible due to a bug in the SRv6
    implementation:
    ```console
    h11# ping6 fd00:0:83::1
    ```

    Note that this is not the suggested approach, the explicit configuration of decap instruction
    is preferred, as described hereafter

    we use a decap SID in r8 and in r1 with the End.DT6 behavior, the SID used is fcff:8::100

* Explicit decap (see examples/create_tunnel_r1r4r8.py)

    Note that the implicit decap is not the suggested approach, the explicit configuration of decap instruction is preferred, as described hereafter

    we use a decap SID in r8 and in r1 with the End.DT6 behavior, the SIDs used are fcff:8::100 (in r8) and fcff:1:100 (in r1)

    First, you need to import the python script srv6_controller.py 

    ```python
    from srv6_controller import *
    ```

    Create a gRPC Channel to the gRPC server executed on r1
    
    ```python
    r1_chan = get_grpc_session(server_ip='fcff:1::1', server_port=12345)
    ```

    Create a gRPC Channel to the gRPC server executed on r8
    
    ```python
    r8_chan = get_grpc_session(server_ip='fcff:8::1', server_port=12345)
    ```

    1. set tunnel from r1 to r8 for fd00:0:83::/64

        ```python
        handle_srv6_path('add', r1_chan, destination='fd00:0:83::/64', segments=['fcff:4::1', 'fcff:8::100'], device='r1-h11', metric=200)
        ```

        ```python
        handle_srv6_behavior('add', r8_chan, segment='fcff:8::100', action='End.DT6', lookup_table=254, device='r8-h83', metric=200)
        ```

    1. set tunnel from r8 to r1 for fd00:0:11::/64

        ```python
        handle_srv6_path('add', r8_chan, destination='fd00:0:11::/64', segments=['fcff:4::1', 'fcff:1::100'], device='r8-h83', metric=200)
        ```

        ```python
        handle_srv6_behavior('add', r1_chan, segment='fcff:1::100', action='End.DT6', lookup_table=254, device='r1-h11', metric=200)
        ```

        table 254 corresponds to the "main" routing table

    Close the gRPC Channels

    ```python
    r1_chan.close()
    r8_chan.close()
    ```

#### Create a bidirectional tunnel between h11 and h83, passing through router r7 – the resulting path is: r1 r2 r7 r8

* implicit decap solution (see examples/create_tunnel_r1r7r8_nodecap.py)

    First, you need to import the python script srv6_controller.py 

    ```python
    from srv6_controller import *
    ```

    Create a gRPC Channel to the gRPC server executed on r1
    
    ```python
    r1_chan = get_grpc_session(server_ip='fcff:1::1', server_port=12345)
    ```

    Create a gRPC Channel to the gRPC server executed on r8
    
    ```python
    r8_chan = get_grpc_session(server_ip='fcff:8::1', server_port=12345)
    ```

    1. set tunnel from r1 to r8 for fd00:0:83::/64

        ```python
        handle_srv6_path('add', r1_chan, destination='fd00:0:83::/64', segments=['fcff:7::1', 'fcff:8::1'], device='r1-h11', metric=100)
        ```

        on r8: no explicit decap instruction is needed because net.ipv6.conf.*.seg6_enabled=1 metric 100

    1. set tunnel from r8 to r1 for fd00:0:11::/64

        ```python
        handle_srv6_path('add', r8_chan, destination='fd00:0:11::/64', segments=['fcff:7::1', 'fcff:1::1'], device='r8-h83', metric=100)
        ```

        on r1: no explicit decap instruction is needed because net.ipv6.conf.*.seg6_enabled=1 metric 100

    after the tunnel is setup, you can ping from h11 to h83 and vice versa

    ```console
    h11# ping6 fd00:0:83::2
    h83# ping6 fd00:0:11::2
    ```

    on recent versions of Linux kernel (>=5.5) it is also possible to ping the router IP address on 
    the interface with the host, while on previous ones it was not possible due to a bug in the SRv6
    implementation:
    ```console
    h11# ping6 fd00:0:83::1
    ```

* explicit decap solution (see examples/create_tunnel_r1r7r8)

    Note that implicit decap is not the suggested approach, the explicit configuration of decap instruction
    is preferred, as described hereafter

    we use a decap SID in r8 and in r1 with the End.DT6 behavior, the SIDs used are fcff:8::100 (in r8) and fcff:1::100

    1. set tunnel from r1 to r8 for fd00:0:83::/64

        ```python
        handle_srv6_path('add', r1_chan, destination='fd00:0:83::/64', segments=['fcff:7::1', 'fcff:8::100'], device='r1-h11', metric=100)
        ```

        ```python
        handle_srv6_behavior('add', r8_chan, segment='fcff:8::100', action='End.DT6', lookup_table=254, device='r8-h83', metric=100)
        ```

    1. set tunnel from r8 to r1 for fd00:0:11::/64

        ```python
        handle_srv6_path('add', r8_chan, destination='fd00:0:11::/64', segments=['fcff:7::1', 'fcff:1::100'], device='r8-h83', metric=100)
        ```

        ```python
        handle_srv6_behavior('add', r1_chan, segment='fcff:1::100', action='End.DT6', lookup_table=254, device='r1-h11', metric=100)
        ```

        table 254 corresponds to the "main" routing table

    Close the gRPC Channels

    ```python
    r1_chan.close()
    r8_chan.close()
    ```

#### Path shift

Through metric it is possible to choose between the two paths previously defined that the packets can follow (via r4 or r7).
Due to the previous instructions, the initial route is the shortest path because the value of metric is lower than the other path.
With the next commands it is possible to change the selected path with the one that passes through r4. 

Path shift with implicit decap solution (see examples/path_shift_nodecap.py)
 
1. decreasing the metric value of the r4 route to an intermediate value

    This step is needed to have an always consistent routing table with given values

    ```python
    handle_srv6_path('add', r1_chan, destination='fd00:0:83::/64', segments=['fcff:4::1', 'fcff:8::1'], device='r1-h11', metric=99)
    ```

    ```python
    handle_srv6_path('add', r8_chan, destination='fd00:0:11::/64', segments=['fcff:4::1', 'fcff:1::1'], device='r8-h83', metric=99)
    ```

1. removing old route via r4

    ```python
    handle_srv6_path('del', r1_chan, destination='fd00:0:83::/64', device='r1-h11', metric=200)
    ```

    ```python
    handle_srv6_path('del', r8_chan, destination='fd00:0:11::/64', device='r8-h83', metric=200)
    ```

1. increasing the metric value of the r7 path

    ```python
    handle_srv6_path('add', r1_chan, destination='fd00:0:83::/64', segments=['fcff:7::1', 'fcff:8::1'], device='r1-h11', metric=200)
    ```

    ```python
    handle_srv6_path('add', r8_chan, destination='fd00:0:11::/64', segments=['fcff:7::1', 'fcff:1::1'], device='r8-h83', metric=200)
    ```

1. removing old route via r7

    ```python
    handle_srv6_path('del', r1_chan, destination='fd00:0:83::/64', device='r1-h11', metric=100)
    ```

    ```python
    handle_srv6_path('del', r8_chan, destination='fd00:0:11::/64', device='r8-h83', metric=100)
    ```

1. assign to r4 route a definitive value of the metric

    ```python
    handle_srv6_path('add', r1_chan, destination='fd00:0:83::/64', segments=['fcff:4::1', 'fcff:8::1'], device='r1-h11', metric=100)
    ```

    ```python
    handle_srv6_path('add', r8_chan, destination='fd00:0:11::/64', segments=['fcff:4::1', 'fcff:1::1'], device='r8-h83', metric=100)
    ```

1. delete the r4 route with the intermediate value of the metric

    ```python
    handle_srv6_path('del', r1_chan, destination='fd00:0:83::/64', device='r1-h11', metric=99)
    ```

    ```python
    handle_srv6_path('del', r8_chan, destination='fd00:0:11::/64', device='r8-h83', metric=99)
    ```

To restore r7 path as preferential path, it is possible to repeat all the procedure of point 3 inverting fcff:4::1 with fcff:7::1 and vice versa. 

Path shift with the explicit decap solution (see examples/path_shift.py)

The same result can be achieved with the second technique.

1. decreasing the metric value of the r4 route to an intermediate value

    ```python
    handle_srv6_path('add', r1_chan, destination='fd00:0:83::/64', segments=['fcff:4::1', 'fcff:8::1'], device='r1-h11', metric=99)
    ```

    ```python
    handle_srv6_behavior('add', r8_chan, segment='fcff:8::100', action='End.DT6', lookup_table=254, device='r8-h83', metric=99)
    ```

    ```python
    handle_srv6_path('add', r8_chan, destination='fd00:0:11::/64', segments=['fcff:4::1', 'fcff:1::1'], device='r8-h83', metric=99)
    ```

    ```python
    handle_srv6_behavior('add', r1_chan, segment='fcff:1::100', action='End.DT6', lookup_table=254, device='r1-h11', metric=99)
    ```

1. removing old route via r4

    ```python
    handle_srv6_path('del', r1_chan, destination='fd00:0:83::/64', device='r1-h11', metric=200)
    ```

    ```python
    handle_srv6_behavior('del', r8_chan, segment='fcff:8::100', device='r8-h83', metric=200)
    ```

    ```python
    handle_srv6_path('del', r8_chan, destination='fd00:0:11::/64', device='r8-h83', metric=200)
    ```

    ```python
    handle_srv6_behavior('del', r1_chan, segment='fcff:1::100', device='r1-h11', metric=200)
    ```

1. increasing the metric value of the r7 path

    ```python
    handle_srv6_path('add', r1_chan, destination='fd00:0:83::/64', segments=['fcff:7::1', 'fcff:8::1'], device='r1-h11', metric=200)
    ```

    ```python
    handle_srv6_behavior('add', r8_chan, segment='fcff:8::100', action='End.DT6', lookup_table=254, device='r8-h83', metric=200)
    ```

    ```python
    handle_srv6_path('add', r8_chan, destination='fd00:0:11::/64', segments=['fcff:7::1', 'fcff:1::1'], device='r8-h83', metric=200)
    ```

    ```python
    handle_srv6_behavior('add', r1_chan, segment='fcff:1::100', action='End.DT6', lookup_table=254, device='r1-h11', metric=200)
    ```

1. removing old route via r7

    ```python
    handle_srv6_path('del', r1_chan, destination='fd00:0:83::/64', device='r1-h11', metric=100)
    ```

    ```python
    handle_srv6_behavior('del', r8_chan, segment='fcff:8::100', device='r8-h83', metric=100)
    ```

    ```python
    handle_srv6_path('del', r8_chan, destination='fd00:0:11::/64', device='r8-h83', metric=100)
    ```

    ```python
    handle_srv6_behavior('del', r1_chan, segment='fcff:1::100', device='r1-h11', metric=100)
    ```

1. assign to r4 route a definitive value of the metric

    ```python
    handle_srv6_path('add', r1_chan, destination='fd00:0:83::/64', segments=['fcff:4::1', 'fcff:8::1'], device='r1-h11', metric=100)
    ```

    ```python
    handle_srv6_behavior('add', r8_chan, segment='fcff:8::100', action='End.DT6', lookup_table=254, device='r8-h83', metric=100)
    ```

    ```python
    handle_srv6_path('add', r8_chan, destination='fd00:0:11::/64', segments=['fcff:4::1', 'fcff:1::1'], device='r8-h83', metric=100)
    ```

    ```python
    handle_srv6_behavior('add', r1_chan, segment='fcff:1::100', action='End.DT6', lookup_table=254, device='r1-h11', metric=100)
    ```

1. delete the r4 route with the intermediate value of the metric

    ```python
    handle_srv6_path('del', r1_chan, destination='fd00:0:83::/64', device='r1-h11', metric=99)
    ```

    ```python
    handle_srv6_behavior('del', r8_chan, segment='fcff:8::100', device='r8-h83', metric=99)
    ```

    ```python
    handle_srv6_path('del', r8_chan, destination='fd00:0:11::/64', device='r8-h83', metric=99)
    ```

    ```python
    handle_srv6_behavior('del', r1_chan, segment='fcff:1::100', device='r1-h11', metric=99)
    ```

Also for this technique, it is possible to restore the shortest path as preferential by the inversion of all the commands fcff:4::1 with fcff:7:11 and vice versa.



#### Extract topology and load it on ArangoDB (see examples/load_topo_on_arango.py)

1. Extract the topology and export nodes and edges in YAML format

    ```python
    extract_topo_from_isis(isis_nodes=['fcff:1::1-2608','fcff:2::1-2608'], nodes_yaml='nodes.yaml', edges_yaml='edges.yaml', verbose=True)
    ```

1. Add IP addresses to the topology

    ```python
    # Open nodes file
    with open('nodes.yaml', 'r') as infile:
            nodes = yaml.safe_load(infile.read())
    # Fill addresses
    for node in nodes:
        # New string where the non-digit characters
        # are replaced with the empty string
        nodeid = int(re.sub('\\D', '', node['_key']))
        if nodeid <= 0 or nodeid >= 2**16:
                # Overflow, address out of range
                logging.critical('Network overflow: no space left in the '
                                'loopback subnet for the router %s' % _key)
                return
        # Prefix
        prefix = int(IPv6Interface(u'fcff::/16'))
        # Build the address fcff:xxxx::1/128
        ip_address = str(IPv6Interface(prefix | nodeid << 96 | 1))
        # Update the dict
        node['ip_address'] = ip_address
    # Save the nodes YAML
    with open(nodes_yaml, 'w') as outfile:
        yaml.dump(nodes, outfile)
    ```

1. Add hosts to the topology

    ```python
    # Open nodes file
    with open(nodes_yaml, 'r') as infile:
        nodes = yaml.safe_load(infile.read())
    # Open edges file
    with open(edges_yaml, 'r') as infile:
        edges = yaml.safe_load(infile.read())
    # Add hosts and links
    for host in HOSTS:
        # Add host
        nodes.append({
                '_key': host['name'],
                'type': 'host',
                'ip_address': host['ip_address']
        })
        # Add edge (host to router)
        edges.append({
                '_from': 'nodes/%s' % host['name'],
                '_to': 'nodes/%s' % host['gw'],
                'type': 'edge'
        })
        # Add edge (router to host)
        # This is required because we work with
        # unidirectional edges
        edges.append({
                '_to': 'nodes/%s' % host['gw'],
                '_from': 'nodes/%s' % host['name'],
                'type': 'edge'
        })
    # Update nodes YAML
    with open(nodes_yaml, 'w') as outfile:
        yaml.dump(nodes, outfile)
        logger.info('*** Nodes YAML updated\n')
    # Update edges YAML
    with open(edges_yaml, 'w') as outfile:
        yaml.dump(edges, outfile)
    ```

1. Load the topology on ArangoDB

    ```python
    load_topo_on_arango(arango_url='localhost:8529', user='root', password='12345678', nodes_yaml='nodes.yaml', edges_yaml='edges.yaml', verbose=True)
    ```
