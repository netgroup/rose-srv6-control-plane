**SRv6 Functions**
----

The Controller supports the creation and management of several types of SRv6 entities. These functions are available under the section **srv6** of the Command-Line Interface.


### Entering the **srv6** section

```console
controller> srv6
controller(srv6)> 
```

Section **srv6** supports the following commands:
```console
  behavior  biditunnel  exit  help  path  unitunnel
```


### behavior

Create, get, change or remove a SRv6 behavior in a node.

```console
controller(srv6)> behavior --help
usage: behavior [-h] -g GRPC_IP -r GRPC_PORT [-s] [--server-cert SERVER_CERT] --op OP
                --segment SEGMENT --action ACTION [--device DEVICE]
                [--table TABLE] [--nexthop NEXTHOP]
                [--lookup-table LOOKUP_TABLE] [--interface INTERFACE]
                [--segments SEGMENTS] [--metric METRIC] [-d]

Create, get, change or remove a SRv6 behavior in a node

optional arguments:
  -h, --help            show this help message and exit
  -g GRPC_IP, --grpc-ip GRPC_IP
                        IP of the gRPC server
  -r GRPC_PORT, --grpc-port GRPC_PORT
                        Port of the gRPC server
  -s, --secure          Activate secure mode
  --server-cert SERVER_CERT
                        CA certificate file
  --op OP               Operation
  --segment SEGMENT     Segment
  --action ACTION       Action
  --device DEVICE       Device
  --table TABLE         Table
  --nexthop NEXTHOP     Next-hop
  --lookup-table LOOKUP_TABLE
                        Lookup Table
  --interface INTERFACE
                        Interface
  --segments SEGMENTS   Segments
  --metric METRIC       Metric
  -d, --debug           Activate debug logs
```


### biditunnel

Create, get, change or remove a bidirectional SRv6 tunnel between two nodes.

```console
controller(srv6)> biditunnel --help
usage: biditunnel [-h] --op OP --left-grpc-ip L_GRPC_IP --right-grpc-ip
                  R_GRPC_IP --left-grpc-port L_GRPC_PORT --right-grpc-port
                  R_GRPC_PORT [-s] [--server-cert SERVER_CERT] --left-right-dest DEST_LR
                  --right-left-dest DEST_RL
                  [--left-right-localseg LOCALSEG_LR]
                  [--right-left-localseg LOCALSEG_RL] --left-right-sidlist
                  SIDLIST_LR --right-left-sidlist SIDLIST_RL [-d]

Create, get, change or remove a bidirectional SRv6 tunnel between two nodes

optional arguments:
  -h, --help            show this help message and exit
  --op OP               Operation
  --left-grpc-ip L_GRPC_IP
                        IP of the gRPC server
  --right-grpc-ip R_GRPC_IP
                        IP of the gRPC server
  --left-grpc-port L_GRPC_PORT
                        Port of the gRPC server
  --right-grpc-port R_GRPC_PORT
                        Port of the gRPC server
  -s, --secure          Activate secure mode
  --server-cert SERVER_CERT
                        CA certificate file
  --left-right-dest DEST_LR
                        Left to Right destination
  --right-left-dest DEST_RL
                        Right to Left destination
  --left-right-localseg LOCALSEG_LR
                        Left to Right Local segment
  --right-left-localseg LOCALSEG_RL
                        Right to Left Local segment
  --left-right-sidlist SIDLIST_LR
                        Left to Right SID list
  --right-left-sidlist SIDLIST_RL
                        Right to Left SID list
  -d, --debug           Activate debug logs
```


### path

Create, get, change or remove a SRv6 path in a node.

```console
controller(srv6)> path --help
usage: path [-h] -g GRPC_IP -r GRPC_PORT [-s] [--server-cert SERVER_CERT] --op OP
            --destination DESTINATION --segments SEGMENTS [--device DEVICE]
            [--encapmode {encap,inline,l2encap}] [--table TABLE]
            [--metric METRIC] [-d]

Create, get, change or remove a SRv6 path in a node

optional arguments:
  -h, --help            show this help message and exit
  -g GRPC_IP, --grpc-ip GRPC_IP
                        IP of the gRPC server
  -r GRPC_PORT, --grpc-port GRPC_PORT
                        Port of the gRPC server
  -s, --secure          Activate secure mode
  --server-cert SERVER_CERT
                        CA certificate file
  --op OP               Operation
  --destination DESTINATION
                        Destination
  --segments SEGMENTS   Segments
  --device DEVICE       Device
  --encapmode {encap,inline,l2encap}
                        Encap mode
  --table TABLE         Table
  --metric METRIC       Metric
  -d, --debug           Activate debug logs
```


### unitunnel

Create, get, change or remove a unidirectional SRv6 tunnel between two nodes.

```console
controller(srv6)> unitunnel --help
usage: unitunnel [-h] --op OP --ingress-grpc-ip INGRESS_GRPC_IP
                 --egress-grpc-ip EGRESS_GRPC_IP --ingress-grpc-port
                 INGRESS_GRPC_PORT --egress-grpc-port EGRESS_GRPC_PORT [-s]
                 [--server-cert SERVER_CERT] --dest DEST [--localseg LOCALSEG] --sidlist
                 SIDLIST [-d]

Create, get, change or remove a unidirectional SRv6 tunnel between two nodes

optional arguments:
  -h, --help            show this help message and exit
  --op OP               Operation
  --ingress-grpc-ip INGRESS_GRPC_IP
                        IP of the gRPC server
  --egress-grpc-ip EGRESS_GRPC_IP
                        IP of the gRPC server
  --ingress-grpc-port INGRESS_GRPC_PORT
                        Port of the gRPC server
  --egress-grpc-port EGRESS_GRPC_PORT
                        Port of the gRPC server
  -s, --secure          Activate secure mode
  --server-cert SERVER_CERT
                        CA certificate file
  --dest DEST           Destination
  --localseg LOCALSEG   Local segment
  --sidlist SIDLIST     SID list
  -d, --debug           Activate debug logs
```


### exit

Exit from this section and return the previous section.

```console
controller(srv6)> exit
```


### help

Show a description of the commands.

```console
controller(srv6)> help
```
