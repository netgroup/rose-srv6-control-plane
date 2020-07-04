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


"""SRv6 utilities for Controller CLI"""

import sys
from argparse import ArgumentParser

# Controller dependencies
from controller import srv6_utils, utils
from controller.cli import utils as cli_utils

# Default CA certificate path
DEFAULT_CERTIFICATE = 'cert_server.pem'


def handle_srv6_usid_policy(
        operation,
        grpc_address,
        grpc_port,
        node_to_addr_filename,
        destination,
        nodes="",
        device='',
        encapmode="encap",
        table=-1,
        metric=-1):
    """Handle a SRv6 uSID policy"""

    # pylint: disable=too-many-arguments

    with utils.get_grpc_session(grpc_address, grpc_port) as channel:
        res = srv6_utils.handle_srv6_usid_policy(
            operation=operation,
            channel=channel,
            node_to_addr_filename=node_to_addr_filename,
            destination=destination,
            nodes=nodes.split(','),
            device=device,
            encapmode=encapmode,
            table=table,
            metric=metric
        )
        if res == 0:
            print('OK')
        else:
            print('Error')


def handle_srv6_path(
        operation,
        grpc_address,
        grpc_port,
        destination,
        segments="",
        device='',
        encapmode="encap",
        table=-1,
        metric=-1):
    """Handle a SRv6 path"""

    # pylint: disable=too-many-arguments

    with utils.get_grpc_session(grpc_address, grpc_port) as channel:
        res = srv6_utils.handle_srv6_path(
            operation=operation,
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


def handle_srv6_behavior(
        operation,
        grpc_address,
        grpc_port,
        segment,
        action='',
        device='',
        table=-1,
        nexthop="",
        lookup_table=-1,
        interface="",
        segments="",
        metric=-1):
    """Handle a SRv6 behavior"""

    # pylint: disable=too-many-arguments

    with utils.get_grpc_session(grpc_address, grpc_port) as channel:
        res = srv6_utils.handle_srv6_behavior(
            operation=operation,
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


def handle_srv6_unitunnel(operation, ingress_ip, ingress_port,
                          egress_ip, egress_port,
                          destination, segments, localseg=None):
    """Handle a SRv6 unidirectional tunnel"""

    # pylint: disable=too-many-arguments

    with utils.get_grpc_session(ingress_ip, ingress_port) as ingress_channel, \
            utils.get_grpc_session(egress_ip, egress_port) as egress_channel:
        if operation == 'add':
            res = srv6_utils.create_uni_srv6_tunnel(
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
        elif operation == 'del':
            res = srv6_utils.destroy_uni_srv6_tunnel(
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
            print('Invalid operation %s' % operation)


def handle_srv6_biditunnel(operation, node_l_ip, node_l_port,
                           node_r_ip, node_r_port,
                           sidlist_lr, sidlist_rl, dest_lr, dest_rl,
                           localseg_lr=None, localseg_rl=None):
    """Handle SRv6 bidirectional tunnel"""

    # pylint: disable=too-many-arguments

    with utils.get_grpc_session(node_l_ip, node_l_port) as node_l_channel, \
            utils.get_grpc_session(node_r_ip, node_r_port) as node_r_channel:
        if operation == 'add':
            res = srv6_utils.create_srv6_tunnel(
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
        elif operation == 'del':
            res = srv6_utils.destroy_srv6_tunnel(
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
            print('Invalid operation %s' % operation)


def args_srv6_usid_policy():
    '''
    Command-line arguments for the srv6_usid_policy command
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    - is_path, a boolean flag indicating whether the argument is a path or not
    '''

    return [
        {
            'args': ['--grpc-ip'],
            'kwargs': {'dest': 'grpc_ip', 'action': 'store',
                       'required': True, 'help': 'IP of the gRPC server'}
        }, {
            'args': ['--grpc-port'],
            'kwargs': {'dest': 'grpc_port', 'action': 'store',
                       'required': True, 'help': 'Port of the gRPC server'}
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
                       'required': True, 'help': 'Destination'}
        }, {
            'args': ['--nodes'],
            'kwargs': {'dest': 'nodes', 'action': 'store', 'required': True,
                       'help': 'Nodes', 'default': ''}
        }, {
            'args': ['--device'],
            'kwargs': {'dest': 'device', 'action': 'store', 'help': 'Device',
                       'default': ''}
        }, {
            'args': ['--encapmode'],
            'kwargs': {'dest': 'encapmode', 'action': 'store',
                       'help': 'Encap mode',
                       'choices': ['encap', 'inline', 'l2encap'],
                       'default': 'encap'}
        }, {
            'args': ['--table'],
            'kwargs': {'dest': 'table', 'action': 'store',
                       'help': 'Table', 'type': int, 'default': -1}
        }, {
            'args': ['--metric'],
            'kwargs': {'dest': 'metric', 'action': 'store',
                       'help': 'Metric', 'type': int, 'default': -1}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_srv6_usid_policy(prog=sys.argv[0], args=None):
    """Command-line arguments parser for srv6_usid_policy function"""

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
    """This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string"""

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
    '''
    Command-line arguments for the srv6_path command
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    - is_path, a boolean flag indicating whether the argument is a path or not
    '''

    return [
        {
            'args': ['--grpc-ip'],
            'kwargs': {'dest': 'grpc_ip', 'action': 'store',
                       'required': True, 'help': 'IP of the gRPC server'}
        }, {
            'args': ['--grpc-port'],
            'kwargs': {'dest': 'grpc_port', 'action': 'store',
                       'required': True, 'help': 'Port of the gRPC server'}
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
                       'required': True, 'help': 'Destination'}
        }, {
            'args': ['--segments'],
            'kwargs': {'dest': 'segments', 'action': 'store', 'required': True,
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
                       'default': 'encap'}
        }, {
            'args': ['--table'],
            'kwargs': {'dest': 'table', 'action': 'store',
                       'help': 'Table', 'type': int, 'default': -1}
        }, {
            'args': ['--metric'],
            'kwargs': {'dest': 'metric', 'action': 'store',
                       'help': 'Metric', 'type': int, 'default': -1}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_srv6_path(prog=sys.argv[0], args=None):
    """Command-line arguments parser for srv6_path function"""

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
    """This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string"""

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
    '''
    Command-line arguments for the srv6_behavior command
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    '''

    return [
        {
            'args': ['--grpc-ip'],
            'kwargs': {'dest': 'grpc_ip', 'action': 'store',
                       'required': True, 'help': 'IP of the gRPC server'}
        }, {
            'args': ['--grpc-port'],
            'kwargs': {'dest': 'grpc_port', 'action': 'store',
                       'required': True, 'help': 'Port of the gRPC server'}
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
            'kwargs': {'dest': 'segment', 'action': 'store', 'required': True,
                       'help': 'Segment'}
        }, {
            'args': ['--action'],
            'kwargs': {'dest': 'action', 'action': 'store', 'required': True,
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
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_srv6_behavior(prog=sys.argv[0], args=None):
    """Command-line arguments parser for srv6_behavior function"""

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
    """This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string"""

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
    '''
    Command-line arguments for the srv6_unitunnel command
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    '''

    return [
        {
            'args': ['--op'],
            'kwargs': {'dest': 'op', 'action': 'store', 'required': True,
                       'help': 'Operation'}
        }, {
            'args': ['--ingress-grpc-ip'],
            'kwargs': {'dest': 'ingress_grpc_ip', 'action': 'store',
                       'required': True, 'help': 'IP of the gRPC server'}
        }, {
            'args': ['--egress-grpc-ip'],
            'kwargs': {'dest': 'egress_grpc_ip', 'action': 'store',
                       'required': True, 'help': 'IP of the gRPC server'}
        }, {
            'args': ['--ingress-grpc-port'],
            'kwargs': {'dest': 'ingress_grpc_port', 'action': 'store',
                       'required': True, 'help': 'Port of the gRPC server'}
        }, {
            'args': ['--egress-grpc-port'],
            'kwargs': {'dest': 'egress_grpc_port', 'action': 'store',
                       'required': True, 'help': 'Port of the gRPC server'}
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
            'kwargs': {'dest': 'dest', 'action': 'store', 'required': True,
                       'help': 'Destination'}
        }, {
            'args': ['--localseg'],
            'kwargs': {'dest': 'localseg', 'action': 'store',
                       'help': 'Local segment', 'default': None}
        }, {
            'args': ['--sidlist'],
            'kwargs': {'dest': 'sidlist', 'action': 'store',
                       'help': 'SID list', 'required': True}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_srv6_unitunnel(prog=sys.argv[0], args=None):
    """Command-line arguments parser for srv6_unitunnel function"""

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
    '''
    Command-line arguments for the srv6_biditunnel command
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    '''

    return [
        {
            'args': ['--op'],
            'kwargs': {'dest': 'op', 'action': 'store', 'required': True,
                       'help': 'Operation'}
        }, {
            'args': ['--left-grpc-ip'],
            'kwargs': {'dest': 'l_grpc_ip', 'action': 'store',
                       'required': True, 'help': 'IP of the gRPC server'}
        }, {
            'args': ['--right-grpc-ip'],
            'kwargs': {'dest': 'r_grpc_ip', 'action': 'store',
                       'required': True, 'help': 'IP of the gRPC server'}
        }, {
            'args': ['--left-grpc-port'],
            'kwargs': {'dest': 'l_grpc_port', 'action': 'store',
                       'required': True, 'help': 'Port of the gRPC server'}
        }, {
            'args': ['--right-grpc-port'],
            'kwargs': {'dest': 'r_grpc_port', 'action': 'store',
                       'required': True, 'help': 'Port of the gRPC server'}
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
            'kwargs': {'dest': 'dest_lr', 'action': 'store', 'required': True,
                       'help': 'Left to Right destination'}
        }, {
            'args': ['--right-left-dest'],
            'kwargs': {'dest': 'dest_rl', 'action': 'store', 'required': True,
                       'help': 'Right to Left destination'}
        }, {
            'args': ['--left-right-localseg'],
            'kwargs': {'dest': 'localseg_lr', 'action': 'store',
                       'help': 'Left to Right Local segment', 'default': None}
        }, {
            'args': ['--right-left-localseg'],
            'kwargs': {'dest': 'localseg_rl', 'action': 'store',
                       'help': 'Right to Left Local segment', 'default': None}
        }, {
            'args': ['--left-right-sidlist'],
            'kwargs': {'dest': 'sidlist_lr', 'action': 'store',
                       'help': 'Left to Right SID list', 'required': True}
        }, {
            'args': ['--right-left-sidlist'],
            'kwargs': {'dest': 'sidlist_rl', 'action': 'store',
                       'help': 'Right to Left SID list', 'required': True}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_srv6_biditunnel(prog=sys.argv[0], args=None):
    """Command-line arguments parser for srv6_biditunnel function"""

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


def args_srv6_usid():
    '''
    Command-line arguments for the srv6_usid command
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    - is_path, a boolean flag indicating whether the argument is a path or not
    '''

    return [
        {
            'args': ['--addrs-file'],
            'kwargs': {'dest': 'addrs_file', 'action': 'store',
                       'required': True, 'help': 'File containing the mapping '
                       'of name nodes to IP addresses'},
            'is_path': True
        }
    ]


# Parse options
def parse_arguments_srv6_usid(prog=sys.argv[0], args=None):
    """Command-line arguments parser for srv6_biditunnel function"""

    # Get parser
    parser = ArgumentParser(
        prog=prog, description='uSID'
    )
    # Add the arguments to the parser
    for param in args_srv6_usid():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for SRv6 bi-directional tunnel
def complete_srv6_usid(text, prev_text=None):
    """This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string"""

    # Get arguments for srv6_biditunnel
    args = args_srv6_usid()
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


def print_node_to_addr_mapping(node_to_addr_filename):
    srv6_utils.print_node_to_addr_mapping(node_to_addr_filename)
