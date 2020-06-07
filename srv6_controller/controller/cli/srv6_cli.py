#!/usr/bin/python

##############################################################################################
# Copyright (C) 2020 Carmine Scarpitta - (Consortium GARR and University of Rome "Tor Vergata")
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
# Implementation of SRv6 Controller
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


from argparse import ArgumentParser
import sys

# Path of the controller
CONTROLLER_PATH = '../'

# Controller dependencies
sys.path.append(CONTROLLER_PATH)
import srv6_utils
import utils

# Default CA certificate path
DEFAULT_CERTIFICATE = 'cert_server.pem'


def handle_srv6_path(op, grpc_address, grpc_port, destination, segments="",
                     device='', encapmode="encap", table=-1, metric=-1):
    with utils.get_grpc_session(grpc_address, grpc_port) as channel:
        res = srv6_utils.handle_srv6_path(
            op=op,
            channel=channel,
            destination=destination,
            segments=segments.split(','),
            device=device,
            encapmode=encapmode,
            table=table,
            metric=metric
        )
        if res == 0:
            print('OK')
        else:
            print('Error')


def handle_srv6_behavior(op, grpc_address, grpc_port, segment, action='',
                         device='', table=-1, nexthop="", lookup_table=-1,
                         interface="", segments="", metric=-1):
    with utils.get_grpc_session(grpc_address, grpc_port) as channel:
        res = srv6_utils.handle_srv6_behavior(
            op=op,
            channel=channel,
            segment=segment,
            action=action,
            device=device,
            table=table,
            nexthop=nexthop,
            lookup_table=lookup_table,
            interface=interface,
            segments=segments.split(','),
            metric=metric
        )
        if res == 0:
            print('OK')
        else:
            print('Error')


def handle_srv6_unitunnel(op, ingress_ip, ingress_port,
                          egress_ip, egress_port,
                          destination, segments, localseg=None):
    with utils.get_grpc_session(ingress_ip, ingress_port) as ingress_channel, \
            utils.get_grpc_session(egress_ip, egress_port) as egress_channel:
        if op == 'add':
            res = srv6_utils.__create_uni_srv6_tunnel(
                ingress_channel=ingress_channel,
                egress_channel=egress_channel,
                destination=destination,
                segments=segments.split(','),
                localseg=localseg
            )
            if res == 0:
                print('OK')
            else:
                print('Error')
        elif op == 'del':
            res = srv6_utils.__destroy_uni_srv6_tunnel(
                op=op,
                ingress_channel=ingress_channel,
                egress_channel=egress_channel,
                destination=destination,
                localseg=localseg
            )
            if res == 0:
                print('OK')
            else:
                print('Error')
        else:
            print('Invalid op %s' % op)


def handle_srv6_biditunnel(op, node_l_ip, node_l_port,
                           node_r_ip, node_r_port,
                           sidlist_lr, sidlist_rl, dest_lr, dest_rl,
                           localseg_lr=None, localseg_rl=None):
    with utils.get_grpc_session(node_l_ip, node_l_port) as node_l_channel, \
            utils.get_grpc_session(node_r_ip, node_r_port) as node_r_channel:
        if op == 'add':
            res = srv6_utils.__create_srv6_tunnel(
                node_l_channel=node_l_channel,
                node_r_channel=node_r_channel,
                sidlist_lr=sidlist_lr.split(','),
                sidlist_rl=sidlist_rl.split(','),
                dest_lr=dest_lr,
                dest_rl=dest_rl,
                localseg_lr=localseg_lr,
                localseg_rl=localseg_rl
            )
            if res == 0:
                print('OK')
            else:
                print('Error')
        elif op == 'del':
            res = srv6_utils.__destroy_srv6_tunnel(
                node_l_channel=node_l_channel,
                node_r_channel=node_r_channel,
                dest_lr=dest_lr,
                dest_rl=dest_rl,
                localseg_lr=localseg_lr,
                localseg_rl=localseg_rl
            )
            if res == 0:
                print('OK')
            else:
                print('Error')
        else:
            print('Invalid op %s' % op)


# Parse options
def parse_arguments_srv6_path(prog=sys.argv[0], args=None):
    # Get parser
    parser = ArgumentParser(
        prog=prog, description='gRPC Southbound APIs for SRv6 Controller'
    )
    parser.add_argument(
        '-g', '--grpc-ip', dest='grpc_ip', action='store',
        required=True, help='IP of the gRPC server'
    )
    parser.add_argument(
        '-r', '--grpc-port', dest='grpc_port', action='store',
        required=True, help='Port of the gRPC server'
    )
    parser.add_argument(
        '-s', '--secure', action='store_true', help='Activate secure mode'
    )
    parser.add_argument(
        '-c', '--server-cert', dest='server_cert', action='store',
        default=DEFAULT_CERTIFICATE, help='CA certificate file'
    )
    parser.add_argument(
        '--op', dest='op', action='store', required=True,
        help='Operation'
    )
    parser.add_argument(
        '--destination', dest='destination', action='store', required=True,
        help='Destination'
    )
    parser.add_argument(
        '--segments', dest='segments', action='store', required=True,
        help='Segments', default=''
    )
    parser.add_argument(
        '--device', dest='device', action='store', help='Device',
        default=''
    )
    parser.add_argument(
        '--encapmode', dest='encapmode', action='store',
        help='Encap mode', choices=['encap', 'inline', 'l2encap'],
        default='encap'
    )
    parser.add_argument(
        '--table', dest='table', action='store',
        help='Table', type=int, default=-1
    )
    parser.add_argument(
        '--metric', dest='metric', action='store',
        help='Metric', type=int, default=-1
    )
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Activate debug logs'
    )
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# Parse options
def parse_arguments_srv6_behavior(prog=sys.argv[0], args=None):
    # Get parser
    parser = ArgumentParser(
        prog=prog, description='gRPC Southbound APIs for SRv6 Controller'
    )
    parser.add_argument(
        '-g', '--grpc-ip', dest='grpc_ip', action='store',
        required=True, help='IP of the gRPC server'
    )
    parser.add_argument(
        '-r', '--grpc-port', dest='grpc_port', action='store',
        required=True, help='Port of the gRPC server'
    )
    parser.add_argument(
        '-s', '--secure', action='store_true', help='Activate secure mode'
    )
    parser.add_argument(
        '-c', '--server-cert', dest='server_cert', action='store',
        default=DEFAULT_CERTIFICATE, help='CA certificate file'
    )
    parser.add_argument(
        '--op', dest='op', action='store', required=True,
        help='Operation'
    )
    parser.add_argument(
        '--segment', dest='segment', action='store', required=True,
        help='Segment'
    )
    parser.add_argument(
        '--action', dest='action', action='store', required=True,
        help='Action', default=''
    )
    parser.add_argument(
        '--device', dest='device', action='store', help='Device',
        default=''
    )
    parser.add_argument(
        '--table', dest='table', action='store',
        help='Table', type=int, default=-1
    )
    parser.add_argument(
        '--nexthop', dest='nexthop', action='store',
        help='Next-hop', default=''
    )
    parser.add_argument(
        '--lookup-table', dest='lookup_table', action='store',
        help='Lookup Table', type=int, default=-1
    )
    parser.add_argument(
        '--interface', dest='interface', action='store',
        help='Interface', default=''
    )
    parser.add_argument(
        '--segments', dest='segments', action='store',
        help='Segments', default=''
    )
    parser.add_argument(
        '--metric', dest='metric', action='store',
        help='Metric', type=int, default=-1
    )
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Activate debug logs'
    )
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# Parse options
def parse_arguments_srv6_unitunnel(prog=sys.argv[0], args=None):
    # Get parser
    parser = ArgumentParser(
        prog=prog, description='gRPC Southbound APIs for SRv6 Controller'
    )
    parser.add_argument(
        '--op', dest='op', action='store', required=True,
        help='Operation'
    )
    parser.add_argument(
        '--ingress-grpc-ip', dest='ingress_grpc_ip', action='store',
        required=True, help='IP of the gRPC server'
    )
    parser.add_argument(
        '--egress-grpc-ip', dest='egress_grpc_ip', action='store',
        required=True, help='IP of the gRPC server'
    )
    parser.add_argument(
        '--ingress-grpc-port', dest='ingress_grpc_port', action='store',
        required=True, help='Port of the gRPC server'
    )
    parser.add_argument(
        '--egress-grpc-port', dest='egress_grpc_port', action='store',
        required=True, help='Port of the gRPC server'
    )
    parser.add_argument(
        '-s', '--secure', action='store_true', help='Activate secure mode'
    )
    parser.add_argument(
        '-c', '--server-cert', dest='server_cert', action='store',
        default=DEFAULT_CERTIFICATE, help='CA certificate file'
    )
    parser.add_argument(
        '--dest', dest='dest', action='store', required=True,
        help='Destination'
    )
    parser.add_argument(
        '--localseg', dest='localseg', action='store',
        help='Local segment', default=None
    )
    parser.add_argument(
        '--sidlist', dest='sidlist', action='store',
        help='SID list', required=True
    )
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Activate debug logs'
    )
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# Parse options
def parse_arguments_srv6_biditunnel(prog=sys.argv[0], args=None):
    # Get parser
    parser = ArgumentParser(
        prog=prog, description='gRPC Southbound APIs for SRv6 Controller'
    )
    parser.add_argument(
        '--op', dest='op', action='store', required=True,
        help='Operation'
    )
    parser.add_argument(
        '--left-grpc-ip', dest='l_grpc_ip', action='store',
        required=True, help='IP of the gRPC server'
    )
    parser.add_argument(
        '--right-grpc-ip', dest='r_grpc_ip', action='store',
        required=True, help='IP of the gRPC server'
    )
    parser.add_argument(
        '--left-grpc-port', dest='l_grpc_port', action='store',
        required=True, help='Port of the gRPC server'
    )
    parser.add_argument(
        '--right-grpc-port', dest='r_grpc_port', action='store',
        required=True, help='Port of the gRPC server'
    )
    parser.add_argument(
        '-s', '--secure', action='store_true', help='Activate secure mode'
    )
    parser.add_argument(
        '-c', '--server-cert', dest='server_cert', action='store',
        default=DEFAULT_CERTIFICATE, help='CA certificate file'
    )
    parser.add_argument(
        '--left-right-dest', dest='dest_lr', action='store', required=True,
        help='Left to Right destination'
    )
    parser.add_argument(
        '--right-left-dest', dest='dest_rl', action='store', required=True,
        help='Right to Left destination'
    )
    parser.add_argument(
        '--left-right-localseg', dest='localseg_lr', action='store',
        help='Left to Right Local segment', default=None
    )
    parser.add_argument(
        '--right-left-localseg', dest='localseg_rl', action='store',
        help='Right to Left Local segment', default=None
    )
    parser.add_argument(
        '--left-right-sidlist', dest='sidlist_lr', action='store',
        help='Left to Right SID list', required=True
    )
    parser.add_argument(
        '--right-left-sidlist', dest='sidlist_rl', action='store',
        help='Right to Left SID list', required=True
    )
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Activate debug logs'
    )
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args
