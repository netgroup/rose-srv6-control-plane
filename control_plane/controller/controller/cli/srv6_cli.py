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
# Collection of SRv6 utilities for the Controller CLI
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
SRv6 utilities for Controller CLI.
'''

# General imports
import logging
import sys
from argparse import ArgumentParser

# Controller dependencies
from controller import srv6_utils, srv6_usid, utils
from controller.cli import utils as cli_utils

# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)

# Default CA certificate path
DEFAULT_CERTIFICATE = 'cert_server.pem'


def handle_srv6_usid_policy(operation, nodes_dict, lr_destination,
                            rl_destination, nodes_lr=None, nodes_rl=None,
                            table=-1, metric=-1, _id=None, l_grpc_ip=None,
                            l_grpc_port=None, l_fwd_engine=None,
                            r_grpc_ip=None, r_grpc_port=None,
                            r_fwd_engine=None, decap_sid=None, locator=None):
    '''
    Handle a SRv6 uSID policy.

    :param operation: The operation to be performed on the uSID policy
                      (i.e. add, get, change, del).
    :type operation: str
    :param nodes_dict: Dict containing the nodes configuration.
    :type nodes_dict: dict
    :param lr_destination: Destination of the SRv6 route for the left to right
                           path.
    :type lr_destination: str
    :param rl_destination: Destination of the SRv6 route for the right to left
                           path.
    :type rl_destination: str
    :param nodes_lr: Waypoints of the SRv6 route for the right to left path.
    :type nodes_lr: list
    :param nodes_rl: Waypoints of the SRv6 route for the right to leftpath.
    :type nodes_rl: list
    :param table: Routing table containing the SRv6 route. If not provided,
                  the main table (i.e. table 254) will be used.
    :type table: int, optional
    :param metric: Metric for the SRv6 route. If not provided, the default
                   metric will be used.
    :type metric: int, optional
    :param _id: The identifier assigned to a policy, used to get or delete
                a policy by id.
    :type _id: string
    :param l_grpc_ip: gRPC IP address of the left node, required if the left
                      node is expressed numerically in the nodes list.
    :type l_grpc_ip: str, optional
    :param l_grpc_port: gRPC port of the left node, required if the left
                        node is expressed numerically in the nodes list.
    :type l_grpc_port: str, optional
    :param l_fwd_engine: forwarding engine of the left node, required if the
                         left node is expressed numerically in the nodes list.
    :type l_fwd_engine: str, optional
    :param r_grpc_ip: gRPC IP address of the right node, required if the right
                      node is expressed numerically in the nodes list.
    :type r_grpc_ip: str, optional
    :param r_grpc_port: gRPC port of the right node, required if the right
                        node is expressed numerically in the nodes list.
    :type r_grpc_port: str, optional
    :param r_fwd_engine: Forwarding engine of the right node, required if the
                         right node is expressed numerically in the nodes
                         list.
    :type r_fwd_engine: str, optional
    :param decap_sid: uSID used for the decap behavior (End.DT6).
    :type decap_sid: str, optional
    :param locator: Locator prefix (e.g. 'fcbb:bbbb::').
    :type locator: str, optional
    :raises NodeNotFoundError: Node name not found in the mapping file.
    :raises InvalidConfigurationError: The mapping file is not a valid
                                       YAML file.
    :raises TooManySegmentsError: segments arg contains more than 6 segments.
    :raises SIDLocatorError: SID Locator is wrong for one or more segments.
    :raises InvalidSIDError: SID is wrong for one or more segments.
    :raises controller.utils.InvalidArgumentError: You provided an invalid
                                                   argument.
    :raises controller.utils.PolicyNotFoundError: Policy not found.
    '''
    # pylint: disable=too-many-arguments
    #
    # Handle the SRv6 uSID policy
    logger.debug('Trying to handle the SRv6 uSID policy')
    res = srv6_usid.handle_srv6_usid_policy(
        operation=operation,
        nodes_dict=nodes_dict,
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
    # Convert the status code to a human-readable textual description and
    # print the description
    logger.info('handle_srv6_usid_policy returned %s - %s\n\n', res,
                utils.STATUS_CODE_TO_DESC[res])


def handle_srv6_path(operation, grpc_address, grpc_port, destination,
                     segments="", device='', encapmode="encap", table=-1,
                     metric=-1, bsid_addr='', fwd_engine='Linux'):
    '''
    Handle a SRv6 path on a node.

    :param operation: The operation to be performed on the SRv6 path
                      (i.e. add, get, change, del).
    :type operation: str
    :param grpc_address: gRPC IP address of the node.
    :type grpc_address: str
    :param grpc_port: gRPC port of the node.
    :type grpc_port: int
    :param destination: The destination prefix of the SRv6 path.
                        It can be a IP address or a subnet.
    :type destination: str
    :param segments: The SID list to be applied to the packets going to
                     the destination (not required for "get" and "del"
                     operations).
    :type segments: list, optional
    :param device: Device of the SRv6 route. If not provided, the device
                   is selected automatically by the node.
    :type device: str, optional
    :param encapmode: The encap mode to use for the path, i.e. "inline" or
                      "encap" (default: encap).
    :type encapmode: str, optional
    :param table: Routing table containing the SRv6 route. If not provided,
                  the main table (i.e. table 254) will be used.
    :type table: int, optional
    :param metric: Metric for the SRv6 route. If not provided, the default
                   metric will be used.
    :type metric: int, optional
    :param bsid_addr: The Binding SID to be used for the route (only required
                      for VPP).
    :type bsid_addr: str, optional
    :param fwd_engine: Forwarding engine for the SRv6 route (default: Linux).
    :type fwd_engine: str, optional
    :raises controller.utils.InvalidArgumentError: You provided an invalid
                                                   argument.
    '''
    # pylint: disable=too-many-arguments
    #
    # Handle the SRv6 uSID path
    logger.debug('Trying to handle the SRv6 path')
    # Establish a gRPC Channel to the node
    logger.debug('Trying to establish a connection to the node %s on '
                 'port %s', grpc_address, grpc_port)
    with utils.get_grpc_session(grpc_address, grpc_port) as channel:
        # Handle SRv6 path
        res = srv6_utils.handle_srv6_path(
            operation=operation,
            channel=channel,
            destination=destination,
            segments=segments.split(','),
            device=device,
            encapmode=encapmode,
            table=table,
            metric=metric,
            bsid_addr=bsid_addr,
            fwd_engine=fwd_engine
        )
        # Convert the status code to a human-readable textual description and
        # print the description
        logger.info('handle_srv6_path returned %s - %s\n\n', res,
                    utils.STATUS_CODE_TO_DESC[res])


def handle_srv6_behavior(operation, grpc_address, grpc_port, segment,
                         action='', device='', table=-1, nexthop="",
                         lookup_table=-1, interface="", segments="",
                         metric=-1, fwd_engine='Linux'):
    '''
    Handle a SRv6 behavior on a node.

    :param operation: The operation to be performed on the SRv6 path
                      (i.e. add, get, change, del).
    :type operation: str
    :param grpc_address: gRPC IP address of the node.
    :type grpc_address: str
    :param grpc_port: gRPC port of the node.
    :type grpc_port: int
    :param segment: The local segment of the SRv6 behavior. It can be a IP
                    address or a subnet.
    :type segment: str
    :param action: The SRv6 action associated to the behavior (e.g. End or
                   End.DT6), (not required for "get" and "change").
    :type action: str, optional
    :param device: Device of the SRv6 route. If not provided, the device
                   is selected automatically by the node.
    :type device: str, optional
    :param table: Routing table containing the SRv6 route. If not provided,
                  the main table (i.e. table 254) will be used.
    :type table: int, optional
    :param nexthop: The nexthop of cross-connect behaviors (e.g. End.DX4
                    or End.DX6).
    :type nexthop: str, optional
    :param lookup_table: The lookup table for the decap behaviors (e.g.
                         End.DT4 or End.DT6).
    :type lookup_table: int, optional
    :param interface: The outgoing interface for the End.DX2 behavior.
    :type interface: str, optional
    :param segments: The SID list to be applied for the End.B6 behavior.
    :type segments: list, optional
    :param metric: Metric for the SRv6 route. If not provided, the default
                   metric will be used.
    :type metric: int, optional
    :param fwd_engine: Forwarding engine for the SRv6 route (default: Linux).
    :type fwd_engine: str, optional
    '''
    # pylint: disable=too-many-arguments
    #
    # Handle the SRv6 uSID behavior
    logger.debug('Trying to handle the SRv6 behavior')
    # Establish a gRPC Channel to the node
    logger.debug('Trying to establish a connection to the node %s on '
                 'port %s', grpc_address, grpc_port)
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
            metric=metric,
            fwd_engine=fwd_engine
        )
        # Convert the status code to a human-readable textual description and
        # print the description
        logger.info('handle_srv6_behavior returned %s - %s\n\n', res,
                    utils.STATUS_CODE_TO_DESC[res])


def handle_srv6_unitunnel(operation, ingress_ip, ingress_port,
                          egress_ip, egress_port,
                          destination, segments, localseg=None,
                          bsid_addr='', fwd_engine='Linux'):
    '''
    Handle a SRv6 unidirectional tunnel.

    :param ingress_ip: gRPC IP address of the ingress node.
    :type ingress_ip: str
    :param ingress_port: gRPC port of the ingress node.
    :type ingress_port: int
    :param egress_ip: gRPC IP address of the egress node.
    :type egress_ip: str
    :param egress_port: gRPC port of the egress node.
    :type egress_port: int
    :param destination: The destination prefix of the SRv6 tunnel.
                        It can be a IP address or a subnet.
    :type destination: str
    :param segments: The SID list to be applied to the packets going to
                     the destination
    :type segments: list
    :param localseg: The local segment to be associated to the End.DT6
                     seg6local function on the egress node. If the argument
                     'localseg' isn't passed in, the End.DT6 function
                     is not created.
    :type localseg: str, optional
    :param bsid_addr: The Binding SID to be used for the route (only required
                      for VPP).
    :type bsid_addr: str, optional
    :param fwd_engine: Forwarding engine for the SRv6 route. Default: Linux.
    :type fwd_engine: str, optional
    '''
    # pylint: disable=too-many-arguments
    #
    # Handle the SRv6 unidirectional tunnel
    logger.debug('Trying to handle the SRv6 unidirectional tunnel')
    # Establish a gRPC Channel to the ingress and egress nodes
    logger.debug('Trying to establish a connection to the ingress node %s on '
                 'port %s', ingress_ip, ingress_port)
    logger.debug('Trying to establish a connection to the egress node %s on '
                 'port %s', egress_ip, egress_port)
    with utils.get_grpc_session(ingress_ip, ingress_port) as ingress_channel, \
            utils.get_grpc_session(egress_ip, egress_port) as egress_channel:
        if operation == 'add':
            # Create the unidirectional tunnel on the nodes
            res = srv6_utils.create_uni_srv6_tunnel(
                ingress_channel=ingress_channel,
                egress_channel=egress_channel,
                destination=destination,
                segments=segments.split(','),
                localseg=localseg,
                bsid_addr=bsid_addr,
                fwd_engine=fwd_engine
            )
            # Convert the status code to a human-readable textual description
            # and print the description
            logger.info('handle_srv6_behavior returned %s - %s\n\n', res,
                        utils.STATUS_CODE_TO_DESC[res])
        elif operation == 'del':
            # Remove the unidirectional tunnel from the nodes
            res = srv6_utils.destroy_uni_srv6_tunnel(
                ingress_channel=ingress_channel,
                egress_channel=egress_channel,
                destination=destination,
                localseg=localseg,
                bsid_addr=bsid_addr,
                fwd_engine=fwd_engine
            )
            # Convert the status code to a human-readable textual description
            # and print the description
            logger.info('handle_srv6_behavior returned %s - %s\n\n', res,
                        utils.STATUS_CODE_TO_DESC[res])
        else:
            logger.error('Invalid operation %s' % operation)


def handle_srv6_biditunnel(operation, node_l_ip, node_l_port,
                           node_r_ip, node_r_port,
                           sidlist_lr, sidlist_rl, dest_lr, dest_rl,
                           localseg_lr=None, localseg_rl=None,
                           bsid_addr='', fwd_engine='Linux'):
    '''
    Handle SRv6 bidirectional tunnel.

    :param node_l_ip: gRPC IP address of the left node.
    :type node_l_ip: str
    :param node_l_port: gRPC port of the left node.
    :type node_l_port: int
    :param node_r_ip: gRPC IP address of the right node.
    :type node_r_ip: str
    :param node_l_port: gRPC port of the right node.
    :type node_l_port: int
    :param sidlist_lr: The SID list to be applied to the packets going on the
                       left to right path
    :type sidlist_lr: list
    :param sidlist_rl: The SID list to be applied to the packets going on the
                       right to left path
    :type sidlist_rl: list
    :param dest_lr: The destination prefix of the SRv6 left to right path.
                    It can be a IP address or a subnet.
    :type dest_lr: str
    :param dest_rl: The destination prefix of the SRv6 right to left path.
                    It can be a IP address or a subnet.
    :type dest_rl: str
    :param localseg_lr: The local segment to be associated to the End.DT6
                        seg6local function for the left to right path. If the
                        argument 'localseg_lr' isn't passed in, the End.DT6
                        function is not created.
    :type localseg_lr: str, optional
    :param localseg_rl: The local segment to be associated to the End.DT6
                        seg6local function for the right to left path. If the
                        argument 'localseg_lr' isn't passed in, the End.DT6
                        function is not created.
    :type localseg_rl: str, optional
    :param bsid_addr: The Binding SID to be used for the route (only required
                      for VPP).
    :type bsid_addr: str, optional
    :param fwd_engine: Forwarding engine for the SRv6 route. Default: Linux.
    :type fwd_engine: str, optional
    '''
    # pylint: disable=too-many-arguments,too-many-locals
    #
    # Handle the SRv6 bidirectional tunnel
    logger.debug('Trying to handle the SRv6 bidirectional tunnel')
    # Establish a gRPC Channel to the left and right nodes
    logger.debug('Trying to establish a connection to the ingress node %s on '
                 'port %s', node_l_ip, node_l_port)
    logger.debug('Trying to establish a connection to the egress node %s on '
                 'port %s', node_r_ip, node_r_port)
    with utils.get_grpc_session(node_l_ip, node_l_port) as node_l_channel, \
            utils.get_grpc_session(node_r_ip, node_r_port) as node_r_channel:
        if operation == 'add':
            # Create the unidirectional tunnel on the nodes
            res = srv6_utils.create_srv6_tunnel(
                node_l_channel=node_l_channel,
                node_r_channel=node_r_channel,
                sidlist_lr=sidlist_lr.split(','),
                sidlist_rl=sidlist_rl.split(','),
                dest_lr=dest_lr,
                dest_rl=dest_rl,
                localseg_lr=localseg_lr,
                localseg_rl=localseg_rl,
                bsid_addr=bsid_addr,
                fwd_engine=fwd_engine
            )
            # Convert the status code to a human-readable textual description
            # and print the description
            logger.info('handle_srv6_behavior returned %s - %s\n\n', res,
                        utils.STATUS_CODE_TO_DESC[res])
        elif operation == 'del':
            # Remove the unidirectional tunnel from the nodes
            res = srv6_utils.destroy_srv6_tunnel(
                node_l_channel=node_l_channel,
                node_r_channel=node_r_channel,
                dest_lr=dest_lr,
                dest_rl=dest_rl,
                localseg_lr=localseg_lr,
                localseg_rl=localseg_rl,
                bsid_addr=bsid_addr,
                fwd_engine=fwd_engine
            )
            # Convert the status code to a human-readable textual description
            # and print the description
            logger.info('handle_srv6_behavior returned %s - %s\n\n', res,
                        utils.STATUS_CODE_TO_DESC[res])
        else:
            logger.error('Invalid operation %s' % operation)


def args_srv6_usid_policy():
    '''
    Command-line arguments for the srv6_usid_policy command.
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    - is_path, a boolean flag indicating whether the argument is a path or not.

    :return: The list of the arguments.
    :rtype: list
    '''
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
    '''
    Command-line arguments parser for srv6_usid_policy function.

    :param prog: The name of the program (default: sys.argv[0])
    :type prog: str, optional
    :param args: List of strings to parse. If None, the list is taken from
                 sys.argv (default: None).
    :type args: list, optional
    :return: Return the namespace populated with the argument strings.
    :rtype: argparse.Namespace
    '''
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
    '''
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.

    :param text: The text to be auto-completed.
    :type text: str
    :param prev_text: The argument that comes before the text to be
                      auto-completed.
    :type prev_text: str
    :return: A list containing the possible words for the auto-completion.
    :rtype: list
    '''
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
    Command-line arguments for the srv6_path command.
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    - is_path, a boolean flag indicating whether the argument is a path or not.

    :return: The list of the arguments.
    :rtype: list
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
            'args': ['--bsid-addr'],
            'kwargs': {'dest': 'bsid_addr', 'action': 'store',
                       'help': 'BSID address required for VPP', 'default': ''}
        }, {
            'args': ['--fwd-engine'],
            'kwargs': {'dest': 'fwd_engine', 'action': 'store',
                       'help': 'Forwarding engine (Linux or VPP)',
                       'type': str, 'default': 'Linux'}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_srv6_path(prog=sys.argv[0], args=None):
    '''
    Command-line arguments parser for srv6_path function.

    :param prog: The name of the program (default: sys.argv[0])
    :type prog: str, optional
    :param args: List of strings to parse. If None, the list is taken from
                 sys.argv (default: None).
    :type args: list, optional
    :return: Return the namespace populated with the argument strings.
    :rtype: argparse.Namespace
    '''
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
    '''
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.

    :param text: The text to be auto-completed.
    :type text: str
    :param prev_text: The argument that comes before the text to be
                      auto-completed.
    :type prev_text: str
    :return: A list containing the possible words for the auto-completion.
    :rtype: list
    '''
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
    Command-line arguments for the srv6_behavior command.
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library.

    :return: The list of the arguments.
    :rtype: list
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
            'args': ['--fwd-engine'],
            'kwargs': {'dest': 'fwd_engine', 'action': 'store',
                       'help': 'Forwarding engine (Linux or VPP)',
                       'type': str, 'default': 'Linux'}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_srv6_behavior(prog=sys.argv[0], args=None):
    '''
    Command-line arguments parser for srv6_behavior function.

    :param prog: The name of the program (default: sys.argv[0])
    :type prog: str, optional
    :param args: List of strings to parse. If None, the list is taken from
                 sys.argv (default: None).
    :type args: list, optional
    :return: Return the namespace populated with the argument strings.
    :rtype: argparse.Namespace
    '''
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
    '''
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.

    :param text: The text to be auto-completed.
    :type text: str
    :param prev_text: The argument that comes before the text to be
                      auto-completed.
    :type prev_text: str
    :return: A list containing the possible words for the auto-completion.
    :rtype: list
    '''
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
    Command-line arguments for the srv6_unitunnel command.
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library.

    :return: The list of the arguments.
    :rtype: list
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
            'args': ['--bsid-addr'],
            'kwargs': {'dest': 'bsid_addr', 'action': 'store',
                       'help': 'BSID address required for VPP', 'default': ''}
        }, {
            'args': ['--fwd-engine'],
            'kwargs': {'dest': 'fwd_engine', 'action': 'store',
                       'help': 'Forwarding engine (Linux or VPP)',
                       'type': str, 'default': 'Linux'}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_srv6_unitunnel(prog=sys.argv[0], args=None):
    '''
    Command-line arguments parser for srv6_unitunnel function.

    :param prog: The name of the program (default: sys.argv[0])
    :type prog: str, optional
    :param args: List of strings to parse. If None, the list is taken from
                 sys.argv (default: None).
    :type args: list, optional
    :return: Return the namespace populated with the argument strings.
    :rtype: argparse.Namespace
    '''
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
    '''
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.

    :param text: The text to be auto-completed.
    :type text: str
    :param prev_text: The argument that comes before the text to be
                      auto-completed.
    :type prev_text: str
    :return: A list containing the possible words for the auto-completion.
    :rtype: list
    '''
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
    Command-line arguments for the srv6_biditunnel command.
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library.

    :return: The list of the arguments.
    :rtype: list
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
            'args': ['--bsid-addr'],
            'kwargs': {'dest': 'bsid_addr', 'action': 'store',
                       'help': 'BSID address required for VPP', 'default': ''}
        }, {
            'args': ['--fwd-engine'],
            'kwargs': {'dest': 'fwd_engine', 'action': 'store',
                       'help': 'Forwarding engine (Linux or VPP)',
                       'type': str, 'default': 'Linux'}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_srv6_biditunnel(prog=sys.argv[0], args=None):
    '''
    Command-line arguments parser for srv6_biditunnel function.

    :param prog: The name of the program (default: sys.argv[0])
    :type prog: str, optional
    :param args: List of strings to parse. If None, the list is taken from
                 sys.argv (default: None).
    :type args: list, optional
    :return: Return the namespace populated with the argument strings.
    :rtype: argparse.Namespace
    '''
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
    '''
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.

    :param text: The text to be auto-completed.
    :type text: str
    :param prev_text: The argument that comes before the text to be
                      auto-completed.
    :type prev_text: str
    :return: A list containing the possible words for the auto-completion.
    :rtype: list
    '''
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
    '''
    Command-line arguments parser for load_nodes_config function.

    :param prog: The name of the program (default: sys.argv[0])
    :type prog: str, optional
    :param args: List of strings to parse. If None, the list is taken from
                 sys.argv (default: None).
    :type args: list, optional
    :return: Return the namespace populated with the argument strings.
    :rtype: argparse.Namespace
    '''
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
    '''
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.

    :param text: The text to be auto-completed.
    :type text: str
    :param prev_text: The argument that comes before the text to be
                      auto-completed.
    :type prev_text: str
    :return: A list containing the possible words for the auto-completion.
    :rtype: list
    '''
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
    '''
    Command-line arguments for the print_nodes command.
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    - is_path, a boolean flag indicating whether the argument is a path or not.

    :return: The list of the arguments.
    :rtype: list
    '''
    return [
    ]


# Parse options
def parse_arguments_print_nodes(prog=sys.argv[0], args=None):
    '''
    Command-line arguments parser for print_nodes function.

    :param prog: The name of the program (default: sys.argv[0])
    :type prog: str, optional
    :param args: List of strings to parse. If None, the list is taken from
                 sys.argv (default: None).
    :type args: list, optional
    :return: Return the namespace populated with the argument strings.
    :rtype: argparse.Namespace
    '''
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
    '''
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.

    :param text: The text to be auto-completed.
    :type text: str
    :param prev_text: The argument that comes before the text to be
                      auto-completed.
    :type prev_text: str
    :return: A list containing the possible words for the auto-completion.
    :rtype: list
    '''
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


def print_nodes_from_config_file(nodes_filename):
    '''
    This function reads a YAML file containing the nodes configuration and
    print the available nodes.

    :param nodes_filename: The file containing the nodes configuration.
    :type nodes_filename: str
    '''
    srv6_usid.print_nodes_from_config_file(nodes_filename)


def print_nodes(nodes_dict):
    '''
    Print nodes.

    :param nodes_dict: Dict containing the nodes
    :type nodes_dict: dict
    '''
    srv6_usid.print_nodes(nodes_dict=nodes_dict)
