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
# Implementation of SRv6 Controller
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


"""
SRv6 utilities for Controller CLI.
"""

# General imports
import pprint
import sys
from argparse import ArgumentParser

# Controller dependencies
from apps.cli import utils as cli_utils
from apps.nb_grpc_client import utils as grpc_utils
from apps.nb_grpc_client import srv6_manager
from apps.nb_grpc_client import topo_manager

# Default CA certificate path
DEFAULT_CERTIFICATE = 'cert_server.pem'


def handle_srv6_usid_policy(controller_channel, operation,
                            lr_destination, rl_destination, nodes_lr=None,
                            nodes_rl=None, table=-1, metric=-1, _id=None,
                            l_grpc_ip=None, l_grpc_port=None,
                            l_fwd_engine=None, r_grpc_ip=None,
                            r_grpc_port=None, r_fwd_engine=None,
                            decap_sid=None, locator=None):
    """
    Handle a SRv6 uSID policy.
    """
    # pylint: disable=too-many-arguments
    #
    # Perform the operation
    # If an error occurs during the operation, an exception will be raised
    return srv6_manager.handle_srv6_usid_policy(
        controller_channel=controller_channel,
        operation=operation,
        lr_destination=lr_destination,
        rl_destination=rl_destination,
        nodes_lr=nodes_lr.split(',') if nodes_lr is not None else None,
        nodes_rl=nodes_rl.split(',') if nodes_rl is not None else None,
        table=table,
        metric=metric,
        _id=_id,
        l_grpc_ip=l_grpc_ip,
        l_grpc_port=l_grpc_port,
        l_fwd_engine=l_fwd_engine,
        r_grpc_ip=r_grpc_ip,
        r_grpc_port=r_grpc_port,
        r_fwd_engine=r_fwd_engine,
        decap_sid=decap_sid,
        locator=locator
    )


def handle_srv6_path(controller_channel, operation, grpc_address, grpc_port,
                     destination, segments="", device='', encapmode="encap",
                     table=-1, metric=-1, bsid_addr='', fwd_engine='linux',
                     key=''):
    """
    Handle a SRv6 path.
    """
    # pylint: disable=too-many-arguments
    #
    # Perform the operation
    # If an error occurs during the operation, an exception will be raised
    srv6_paths = srv6_manager.handle_srv6_path(
        controller_channel=controller_channel,
        operation=operation,
        grpc_address=grpc_address,
        grpc_port=grpc_port,
        destination=destination,
        segments=segments.split(','),
        device=device,
        encapmode=encapmode,
        table=table,
        metric=metric,
        bsid_addr=bsid_addr,
        fwd_engine=fwd_engine,
        key=key
    )
    # If the operation is "get", print the SRv6 paths returned by the node
    if operation == 'get':
        if len(srv6_paths) == 0:
            print('Path not found\n')
        else:
            pprint.pprint(srv6_paths)


def handle_srv6_behavior(controller_channel, operation, grpc_address,
                         grpc_port, segment, action='', device='', table=-1,
                         nexthop="", lookup_table=-1, interface="",
                         segments="", metric=-1, fwd_engine='linux', key=''):
    """
    Handle a SRv6 behavior.
    """
    # pylint: disable=too-many-arguments
    #
    # Perform the operation
    # If an error occurs during the operation, an exception will be raised
    srv6_behaviors = srv6_manager.handle_srv6_behavior(
        controller_channel=controller_channel,
        operation=operation,
        grpc_address=grpc_address,
        grpc_port=grpc_port,
        segment=segment,
        action=action,
        device=device,
        table=table,
        nexthop=nexthop,
        lookup_table=lookup_table,
        interface=interface,
        segments=segments.split(','),
        metric=metric,
        fwd_engine=fwd_engine,
        key=key
    )
    # If the operation is "get", print the SRv6 behaviors returned by the node
    if operation == 'get':
        if len(srv6_behaviors) == 0:
            print('Behavior not found\n')
        else:
            pprint.pprint(srv6_behaviors)


def handle_srv6_unitunnel(controller_channel, operation, ingress_ip,
                          ingress_port, egress_ip, egress_port,
                          destination, segments=None, localseg=None,
                          bsid_addr='', fwd_engine='linux', key=''):
    """
    Handle a SRv6 unidirectional tunnel.
    """
    # pylint: disable=too-many-arguments
    if operation not in ['add', 'del', 'get']:
        # Invalid operation
        raise grpc_utils.InvalidArgumentError
    # Perform the operation
    # If an error occurs during the operation, an exception will be raised
    srv6_tunnels = srv6_manager.handle_srv6_unitunnel(
        controller_channel=controller_channel,
        operation=operation,
        ingress_ip=ingress_ip,
        ingress_port=ingress_port,
        egress_ip=egress_ip,
        egress_port=egress_port,
        destination=destination,
        segments=segments.split(',') if segments is not None else None,
        localseg=localseg,
        bsid_addr=bsid_addr,
        fwd_engine=fwd_engine,
        key=key
    )
    # If the operation is "get", print the SRv6 tunnels returned by the node
    if operation == 'get':
        if len(srv6_tunnels) == 0:
            print('Tunnel not found\n')
        else:
            pprint.pprint(srv6_tunnels)


def handle_srv6_biditunnel(controller_channel, operation, node_l_ip,
                           node_l_port, node_r_ip, node_r_port,
                           dest_lr, dest_rl, sidlist_lr=None, sidlist_rl=None,
                           localseg_lr=None, localseg_rl=None,
                           bsid_addr='', fwd_engine='linux', key=''):
    """
    Handle SRv6 bidirectional tunnel.
    """
    # pylint: disable=too-many-arguments,too-many-locals
    if operation not in ['add', 'del', 'get']:
        # Invalid operation
        raise grpc_utils.InvalidArgumentError
    # Perform the operation
    # If an error occurs during the operation, an exception will be raised
    srv6_tunnels = srv6_manager.handle_srv6_biditunnel(
        controller_channel=controller_channel,
        operation=operation,
        node_l_ip=node_l_ip,
        node_l_port=node_l_port,
        node_r_ip=node_r_ip,
        node_r_port=node_r_port,
        sidlist_lr=sidlist_lr.split(',') if sidlist_lr is not None else None,
        sidlist_rl=sidlist_rl.split(',') if sidlist_rl is not None else None,
        dest_lr=dest_lr,
        dest_rl=dest_rl,
        localseg_lr=localseg_lr,
        localseg_rl=localseg_rl,
        bsid_addr=bsid_addr,
        fwd_engine=fwd_engine,
        key=key
    )    
    # If the operation is "get", print the SRv6 tunnels returned by the node
    if operation == 'get':
        if len(srv6_tunnels) == 0:
            print('Tunnel not found\n')
        else:
            pprint.pprint(srv6_tunnels)


def args_srv6_usid_policy():
    """
    Command-line arguments for the srv6_usid_policy command
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    - is_path, a boolean flag indicating whether the argument is a path or not
    """
    return [
        {
            'args': ['--secure'],
            'kwargs': {'action': 'store_true', 'help': 'Activate secure mode'}
        }, {
            'args': ['--server-cert'],
            'kwargs': {'dest': 'server_cert', 'action': 'store',
                       'default': DEFAULT_CERTIFICATE,
                       'help': 'CA certificate file'},
            'is_path': True
        }, {
            'args': ['--op'],
            'kwargs': {'dest': 'op', 'action': 'store', 'required': True,
                       'help': 'Operation'}
        }, {
            'args': ['--lr-destination'],
            'kwargs': {'dest': 'lr_destination', 'action': 'store',
                       'help': 'Left to Right Destination'}
        }, {
            'args': ['--rl-destination'],
            'kwargs': {'dest': 'rl_destination', 'action': 'store',
                       'help': 'Right to Left Destination'}
        }, {
            'args': ['--nodes'],
            'kwargs': {'dest': 'nodes', 'action': 'store',
                       'help': 'Nodes', 'default': None}
        }, {
            'args': ['--nodes-rev'],
            'kwargs': {'dest': 'nodes_rev', 'action': 'store',
                       'help': 'Reverse nodes list', 'default': None}
        }, {
            'args': ['--table'],
            'kwargs': {'dest': 'table', 'action': 'store',
                       'help': 'Table', 'type': int, 'default': -1}
        }, {
            'args': ['--metric'],
            'kwargs': {'dest': 'metric', 'action': 'store',
                       'help': 'Metric', 'type': int, 'default': -1}
        }, {
            'args': ['--id'],
            'kwargs': {'dest': 'id', 'action': 'store',
                       'help': 'id', 'type': int, 'default': None}
        }, {
            'args': ['--l-grpc-ip'],
            'kwargs': {'dest': 'l_grpc_ip', 'action': 'store',
                       'help': 'gRPC IP address of the left node',
                       'type': str, 'default': None}
        }, {
            'args': ['--l-grpc-port'],
            'kwargs': {'dest': 'l_grpc_port', 'action': 'store',
                       'help': 'gRPC port of the left node',
                       'type': int, 'default': None}
        }, {
            'args': ['--l-fwd-engine'],
            'kwargs': {'dest': 'l_fwd_engine', 'action': 'store',
                       'help': 'Forwarding engine for the left node '
                       '(e.g. Linux or VPP)',
                       'type': str, 'default': None}
        }, {
            'args': ['--r-grpc-ip'],
            'kwargs': {'dest': 'r_grpc_ip', 'action': 'store',
                       'help': 'gRPC IP address of the right node',
                       'type': str, 'default': None}
        }, {
            'args': ['--r-grpc-port'],
            'kwargs': {'dest': 'r_grpc_port', 'action': 'store',
                       'help': 'gRPC port of the right node',
                       'type': int, 'default': None}
        }, {
            'args': ['--r-fwd-engine'],
            'kwargs': {'dest': 'r_fwd_engine', 'action': 'store',
                       'help': 'Forwarding engine for the right node '
                       '(e.g. Linux or VPP)',
                       'type': str, 'default': None}
        }, {
            'args': ['--decap-sid'],
            'kwargs': {'dest': 'decap_sid', 'action': 'store',
                       'help': 'SID used for decap',
                       'type': str, 'default': None}
        }, {
            'args': ['--locator'],
            'kwargs': {'dest': 'locator', 'action': 'store',
                       'help': 'Locator',
                       'type': str, 'default': None}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_srv6_usid_policy(prog=sys.argv[0], args=None):
    """
    Command-line arguments parser for srv6_usid_policy function.
    """
    # Get parser
    parser = ArgumentParser(
        prog=prog, description='gRPC Southbound APIs for SRv6 Controller'
    )
    # Add the arguments to the parser
    for param in args_srv6_usid_policy():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for SRv6 uSID policy
def complete_srv6_usid_policy(text, prev_text):
    """
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.
    """
    # Get arguments for srv6_usid_policy
    args = args_srv6_usid_policy()
    # Paths auto-completion
    if prev_text is not None:
        # Get the list of the arguments requiring a path
        path_args = [arg
                     for param in args
                     for arg in param['args']
                     if param.get('is_path', False)]
        # Check whether the previous argument requires a path or not
        if prev_text in path_args:
            # Auto-complete the path and return the results
            return cli_utils.complete_path(text)
    # Argument is not a path
    #
    # Get the list of the arguments supported by the command
    args = [arg for param in args for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args


def args_srv6_path():
    """
    Command-line arguments for the srv6_path command
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    - is_path, a boolean flag indicating whether the argument is a path or not
    """
    return [
        {
            'args': ['--key'],
            'kwargs': {'dest': 'key', 'action': 'store',
                       'help': 'An id of the SRv6 path', 'default': ''}
        }, {
            'args': ['--grpc-ip'],
            'kwargs': {'dest': 'grpc_ip', 'action': 'store',
                       'help': 'IP of the gRPC server', 'default': ''}
        }, {
            'args': ['--grpc-port'],
            'kwargs': {'dest': 'grpc_port', 'action': 'store', 'type': int,
                       'help': 'Port of the gRPC server', 'default': -1}
        }, {
            'args': ['--secure'],
            'kwargs': {'action': 'store_true', 'help': 'Activate secure mode'}
        }, {
            'args': ['--server-cert'],
            'kwargs': {'dest': 'server_cert', 'action': 'store',
                       'default': DEFAULT_CERTIFICATE,
                       'help': 'CA certificate file'},
            'is_path': True
        }, {
            'args': ['--op'],
            'kwargs': {'dest': 'op', 'action': 'store', 'required': True,
                       'help': 'Operation'}
        }, {
            'args': ['--destination'],
            'kwargs': {'dest': 'destination', 'action': 'store',
                       'help': 'Destination', 'default': ''}
        }, {
            'args': ['--segments'],
            'kwargs': {'dest': 'segments', 'action': 'store',
                       'help': 'Segments', 'default': ''}
        }, {
            'args': ['--device'],
            'kwargs': {'dest': 'device', 'action': 'store', 'help': 'Device',
                       'default': ''}
        }, {
            'args': ['--encapmode'],
            'kwargs': {'dest': 'encapmode', 'action': 'store',
                       'help': 'Encap mode',
                       'choices': ['encap', 'inline', 'l2encap'],
                       'default': ''}
        }, {
            'args': ['--table'],
            'kwargs': {'dest': 'table', 'action': 'store',
                       'help': 'Table', 'type': int, 'default': -1}
        }, {
            'args': ['--metric'],
            'kwargs': {'dest': 'metric', 'action': 'store',
                       'help': 'Metric', 'type': int, 'default': -1}
        }, {
            'args': ['--bsid-addr'],
            'kwargs': {'dest': 'bsid_addr', 'action': 'store',
                       'help': 'BSID address required for VPP', 'default': ''}
        }, {
            'args': ['--fwd-engine'],
            'kwargs': {'dest': 'fwd_engine', 'action': 'store',
                       'help': 'Forwarding engine (Linux or VPP)',
                       'type': str, 'default': ''}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_srv6_path(prog=sys.argv[0], args=None):
    """
    Command-line arguments parser for srv6_path function.
    """
    # Get parser
    parser = ArgumentParser(
        prog=prog, description='gRPC Southbound APIs for SRv6 Controller'
    )
    # Add the arguments to the parser
    for param in args_srv6_path():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for SRv6 Path
def complete_srv6_path(text, prev_text):
    """
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.
    """
    # Get arguments for srv6_path
    args = args_srv6_path()
    # Paths auto-completion
    if prev_text is not None:
        # Get the list of the arguments requiring a path
        path_args = [arg
                     for param in args
                     for arg in param['args']
                     if param.get('is_path', False)]
        # Check whether the previous argument requires a path or not
        if prev_text in path_args:
            # Auto-complete the path and return the results
            return cli_utils.complete_path(text)
    # Argument is not a path
    #
    # Get the list of the arguments supported by the command
    args = [arg for param in args for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args


def args_srv6_behavior():
    """
    Command-line arguments for the srv6_behavior command
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    """
    return [
        {
            'args': ['--key'],
            'kwargs': {'dest': 'key', 'action': 'store',
                       'help': 'An id of the SRv6 behavior', 'default': ''}
        }, {
            'args': ['--grpc-ip'],
            'kwargs': {'dest': 'grpc_ip', 'action': 'store',
                       'help': 'IP of the gRPC server', 'default': ''}
        }, {
            'args': ['--grpc-port'],
            'kwargs': {'dest': 'grpc_port', 'action': 'store', 'type': int,
                       'help': 'Port of the gRPC server',
                       'default': -1}
        }, {
            'args': ['--secure'],
            'kwargs': {'action': 'store_true', 'help': 'Activate secure mode'}
        }, {
            'args': ['--server-cert'],
            'kwargs': {'dest': 'server_cert', 'action': 'store',
                       'default': DEFAULT_CERTIFICATE,
                       'help': 'CA certificate file'},
            'is_path': True
        }, {
            'args': ['--op'],
            'kwargs': {'dest': 'op', 'action': 'store', 'required': True,
                       'help': 'Operation'}
        }, {
            'args': ['--device'],
            'kwargs': {'dest': 'device', 'action': 'store', 'help': 'Device',
                       'default': ''}
        }, {
            'args': ['--table'],
            'kwargs': {'dest': 'table', 'action': 'store',
                       'help': 'Table', 'type': int, 'default': -1}
        }, {
            'args': ['--segment'],
            'kwargs': {'dest': 'segment', 'action': 'store',
                       'help': 'Segment', 'default': ''}
        }, {
            'args': ['--action'],
            'kwargs': {'dest': 'action', 'action': 'store',
                       'help': 'Action', 'default': ''}
        }, {
            'args': ['--nexthop'],
            'kwargs': {'dest': 'nexthop', 'action': 'store',
                       'help': 'Next-hop', 'default': ''}
        }, {
            'args': ['--lookup-table'],
            'kwargs': {'dest': 'lookup_table', 'action': 'store',
                       'help': 'Lookup Table', 'type': int, 'default': -1}
        }, {
            'args': ['--interface'],
            'kwargs': {'dest': 'interface', 'action': 'store',
                       'help': 'Interface', 'default': ''}
        }, {
            'args': ['--segments'],
            'kwargs': {'dest': 'segments', 'action': 'store',
                       'help': 'Segments', 'default': ''}
        }, {
            'args': ['--metric'],
            'kwargs': {'dest': 'metric', 'action': 'store',
                       'help': 'Metric', 'type': int, 'default': -1}
        }, {
            'args': ['--fwd-engine'],
            'kwargs': {'dest': 'fwd_engine', 'action': 'store',
                       'help': 'Forwarding engine (Linux or VPP)',
                       'type': str, 'default': 'linux'}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_srv6_behavior(prog=sys.argv[0], args=None):
    """
    Command-line arguments parser for srv6_behavior function.
    """
    # Get parser
    parser = ArgumentParser(
        prog=prog, description='gRPC Southbound APIs for SRv6 Controller'
    )
    # Add the arguments to the parser
    for param in args_srv6_behavior():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for SRv6 behavior
def complete_srv6_behavior(text, prev_text):
    """
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.
    """
    # Get arguments for srv6_behavior
    args = args_srv6_behavior()
    # Paths auto-completion
    if prev_text is not None:
        # Get the list of the arguments requiring a path
        path_args = [arg
                     for param in args
                     for arg in param['args']
                     if param.get('is_path', False)]
        # Check whether the previous argument requires a path or not
        if prev_text in path_args:
            # Auto-complete the path and return the results
            return cli_utils.complete_path(text)
    # Argument is not a path
    #
    # Get the list of the arguments supported by the command
    args = [arg for param in args for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args


def args_srv6_unitunnel():
    """
    Command-line arguments for the srv6_unitunnel command
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    """
    return [
        {
            'args': ['--op'],
            'kwargs': {'dest': 'op', 'action': 'store', 'required': True,
                       'help': 'Operation'}
        }, {
            'args': ['--key'],
            'kwargs': {'dest': 'key', 'action': 'store',
                       'help': 'An id of the SRv6 tunnel', 'default': ''}
        }, {
            'args': ['--ingress-grpc-ip'],
            'kwargs': {'dest': 'ingress_grpc_ip', 'action': 'store',
                       'default': '', 'help': 'IP of the gRPC server'}
        }, {
            'args': ['--egress-grpc-ip'],
            'kwargs': {'dest': 'egress_grpc_ip', 'action': 'store',
                       'default': '', 'help': 'IP of the gRPC server'}
        }, {
            'args': ['--ingress-grpc-port'],
            'kwargs': {'dest': 'ingress_grpc_port', 'action': 'store',
                       'type': int,
                       'default': -1, 'help': 'Port of the gRPC server'}
        }, {
            'args': ['--egress-grpc-port'],
            'kwargs': {'dest': 'egress_grpc_port', 'action': 'store',
                       'type': int,
                       'default': -1, 'help': 'Port of the gRPC server'}
        }, {
            'args': ['--secure'],
            'kwargs': {'action': 'store_true', 'help': 'Activate secure mode'}
        }, {
            'args': ['--server-cert'],
            'kwargs': {'dest': 'server_cert', 'action': 'store',
                       'default': DEFAULT_CERTIFICATE,
                       'help': 'CA certificate file'},
            'is_path': True
        }, {
            'args': ['--dest'],
            'kwargs': {'dest': 'dest', 'action': 'store', 'default': '',
                       'help': 'Destination'}
        }, {
            'args': ['--localseg'],
            'kwargs': {'dest': 'localseg', 'action': 'store',
                       'help': 'Local segment', 'default': None}
        }, {
            'args': ['--sidlist'],
            'kwargs': {'dest': 'sidlist', 'action': 'store',
                       'help': 'SID list', 'default': None}
        }, {
            'args': ['--bsid-addr'],
            'kwargs': {'dest': 'bsid_addr', 'action': 'store',
                       'help': 'BSID address required for VPP', 'default': ''}
        }, {
            'args': ['--fwd-engine'],
            'kwargs': {'dest': 'fwd_engine', 'action': 'store',
                       'help': 'Forwarding engine (Linux or VPP)',
                       'type': str, 'default': 'linux'}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_srv6_unitunnel(prog=sys.argv[0], args=None):
    """
    Command-line arguments parser for srv6_unitunnel function.
    """
    # Get parser
    parser = ArgumentParser(
        prog=prog, description='gRPC Southbound APIs for SRv6 Controller'
    )
    # Add the arguments to the parser
    for param in args_srv6_unitunnel():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for SRv6 unidirectional tunnel
def complete_srv6_unitunnel(text, prev_text):
    """This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string"""

    # Get arguments for srv6_unitunnel
    args = args_srv6_unitunnel()
    # Paths auto-completion
    if prev_text is not None:
        # Get the list of the arguments requiring a path
        path_args = [arg
                     for param in args
                     for arg in param['args']
                     if param.get('is_path', False)]
        # Check whether the previous argument requires a path or not
        if prev_text in path_args:
            # Auto-complete the path and return the results
            return cli_utils.complete_path(text)
    # Argument is not a path
    #
    # Get the list of the arguments supported by the command
    args = [arg for param in args for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args


def args_srv6_biditunnel():
    """
    Command-line arguments for the srv6_biditunnel command
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    """
    return [
        {
            'args': ['--op'],
            'kwargs': {'dest': 'op', 'action': 'store', 'required': True,
                       'help': 'Operation'}
        }, {
            'args': ['--key'],
            'kwargs': {'dest': 'key', 'action': 'store',
                       'help': 'An id of the SRv6 tunnel', 'default': ''}
        }, {
            'args': ['--left-grpc-ip'],
            'kwargs': {'dest': 'l_grpc_ip', 'action': 'store',
                       'default': '', 'help': 'IP of the gRPC server'}
        }, {
            'args': ['--right-grpc-ip'],
            'kwargs': {'dest': 'r_grpc_ip', 'action': 'store',
                       'default': '', 'help': 'IP of the gRPC server'}
        }, {
            'args': ['--left-grpc-port'],
            'kwargs': {'dest': 'l_grpc_port', 'action': 'store', 'type': int,
                       'default': -1, 'help': 'Port of the gRPC server'}
        }, {
            'args': ['--right-grpc-port'],
            'kwargs': {'dest': 'r_grpc_port', 'action': 'store', 'type': int,
                       'default': -1, 'help': 'Port of the gRPC server'}
        }, {
            'args': ['--secure'],
            'kwargs': {'action': 'store_true', 'help': 'Activate secure mode'}
        }, {
            'args': ['--server-cert'],
            'kwargs': {'dest': 'server_cert', 'action': 'store',
                       'default': DEFAULT_CERTIFICATE,
                       'help': 'CA certificate file'},
            'is_path': True
        }, {
            'args': ['--left-right-dest'],
            'kwargs': {'dest': 'dest_lr', 'action': 'store', 'default': '',
                       'help': 'Left to Right destination'}
        }, {
            'args': ['--right-left-dest'],
            'kwargs': {'dest': 'dest_rl', 'action': 'store', 'default': '',
                       'help': 'Right to Left destination'}
        }, {
            'args': ['--left-right-localseg'],
            'kwargs': {'dest': 'localseg_lr', 'action': 'store',
                       'help': 'Left to Right Local segment', 'default': ''}
        }, {
            'args': ['--right-left-localseg'],
            'kwargs': {'dest': 'localseg_rl', 'action': 'store',
                       'help': 'Right to Left Local segment', 'default': ''}
        }, {
            'args': ['--left-right-sidlist'],
            'kwargs': {'dest': 'sidlist_lr', 'action': 'store',
                       'help': 'Left to Right SID list', 'default': None}
        }, {
            'args': ['--right-left-sidlist'],
            'kwargs': {'dest': 'sidlist_rl', 'action': 'store',
                       'help': 'Right to Left SID list', 'default': None}
        }, {
            'args': ['--bsid-addr'],
            'kwargs': {'dest': 'bsid_addr', 'action': 'store',
                       'help': 'BSID address required for VPP', 'default': ''}
        }, {
            'args': ['--fwd-engine'],
            'kwargs': {'dest': 'fwd_engine', 'action': 'store',
                       'help': 'Forwarding engine (Linux or VPP)',
                       'type': str, 'default': 'linux'}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_srv6_biditunnel(prog=sys.argv[0], args=None):
    """
    Command-line arguments parser for srv6_biditunnel function.
    """
    # Get parser
    parser = ArgumentParser(
        prog=prog, description='gRPC Southbound APIs for SRv6 Controller'
    )
    # Add the arguments to the parser
    for param in args_srv6_biditunnel():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for SRv6 bi-directional tunnel
def complete_srv6_biditunnel(text, prev_text=None):
    """This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string"""

    # Get arguments for srv6_biditunnel
    args = args_srv6_biditunnel()
    # Paths auto-completion
    if prev_text is not None:
        # Get the list of the arguments requiring a path
        path_args = [arg
                     for param in args
                     for arg in param['args']
                     if param.get('is_path', False)]
        # Check whether the previous argument requires a path or not
        if prev_text in path_args:
            # Auto-complete the path and return the results
            return cli_utils.complete_path(text)
    # Argument is not a path
    #
    # Get the list of the arguments supported by the command
    args = [arg for param in args for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args


def args_load_nodes_config():
    """
    Command-line arguments for the srv6_usid command
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    - is_path, a boolean flag indicating whether the argument is a path or not
    """
    return [
        {
            'args': ['--nodes-file'],
            'kwargs': {'dest': 'nodes_file', 'action': 'store',
                       'required': True,
                       'help': 'File containing the mapping '
                               'of name nodes to IP addresses'},
            'is_path': True
        }
    ]


# Parse options
def parse_arguments_load_nodes_config(prog=sys.argv[0], args=None):
    """
    Command-line arguments parser for load_nodes_config function.
    """
    # Get parser
    parser = ArgumentParser(
        prog=prog, description='Load nodes configuration to the database'
    )
    # Add the arguments to the parser
    for param in args_load_nodes_config():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for SRv6 uSID
def complete_load_nodes_config(text, prev_text=None):
    """
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.
    """
    # Get arguments for srv6_biditunnel
    args = args_load_nodes_config()
    # Paths auto-completion
    if prev_text is not None:
        # Get the list of the arguments requiring a path
        path_args = [arg
                     for param in args
                     for arg in param['args']
                     if param.get('is_path', False)]
        # Check whether the previous argument requires a path or not
        if prev_text in path_args:
            # Auto-complete the path and return the results
            return cli_utils.complete_path(text)
    # Argument is not a path
    #
    # Get the list of the arguments supported by the command
    args = [arg for param in args for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args


def args_print_nodes():
    """
    Command-line arguments for the print_nodes command
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    - is_path, a boolean flag indicating whether the argument is a path or not
    """
    return [
    ]


# Parse options
def parse_arguments_print_nodes(prog=sys.argv[0], args=None):
    """
    Command-line arguments parser for print_nodes function.
    """
    # Get parser
    parser = ArgumentParser(
        prog=prog, description='Show the list of the available devices'
    )
    # Add the arguments to the parser
    for param in args_print_nodes():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for SRv6 uSID
def complete_print_nodes(text, prev_text=None):
    """
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.
    """
    # Get arguments for srv6_biditunnel
    args = args_print_nodes()
    # Paths auto-completion
    if prev_text is not None:
        # Get the list of the arguments requiring a path
        path_args = [arg
                     for param in args
                     for arg in param['args']
                     if param.get('is_path', False)]
        # Check whether the previous argument requires a path or not
        if prev_text in path_args:
            # Auto-complete the path and return the results
            return cli_utils.complete_path(text)
    # Argument is not a path
    #
    # Get the list of the arguments supported by the command
    args = [arg for param in args for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args


def print_nodes(controller_channel):
    """
    Print nodes.
    """
    try:
        # Get nodes config
        nodes_config = topo_manager.get_nodes_config(
            controller_channel=controller_channel)
        # Extract node names
        nodes = [node['name'] for node in nodes_config['nodes']]
        # Print the nodes
        print('Available nodes: %s\n' % nodes)
    except grpc_utils.NodesConfigNotLoadedError:
        print('Nodes config not loaded. '
              'Cannot use hostnames as node identifiers.\n')
