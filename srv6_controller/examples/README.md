# SRv6 tutorial controller

This directory contains code examples for SRv6 controller for the topology 8r-1c-in-band-isis contained in draft-srv6-tutorial (https://github.com/netgroup/draft-srv6-tutorial)

```
- create_tunnel_r1r4r8
Create a bidirectional SRv6 tunnel with metric 200 between h11 and h83 passing through router r4.

- create_tunnel_r1r7r8
Create a bidirectional SRv6 tunnel with metric 100 between h11 and h83 passing through router r7.

- shift_path
By executing create_tunnel_r1r4r8 and create_tunnel_r1r7r8 the path selected for the packets is r1---r7---r8 because the value of the metric is lower than the other path. This example shows how it is possible to choose between the two paths by changing the metric.

- remove_tunnel_r1r4r8
Remove the bidirectional SRv6 tunnel with metric 100 between h11 and h83 passing through router r4.

- remove_tunnel_r1r7r8
Remove the bidirectional SRv6 tunnel with metric 200 between h11 and h83 passing through router r7.

- load_topo_on_arango
Extract the network topology from a node running ISIS, export it in YAML format, perform some manipulation and load the topology on Arango DB.

```

