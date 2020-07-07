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
# Implementation of SRv6 Manager
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#

"""This module provides an implementation of a SRv6 Manager"""


import logging
# General imports
import os
import fnmatch
import sys
from socket import AF_INET6

# pyroute2 dependencies
from pyroute2 import IPRoute
from pyroute2.netlink.exceptions import NetlinkError
from pyroute2.netlink.rtnl.ifinfmsg import IFF_LOOPBACK

# VPP dependencies
from vpp_papi import VPP    # TODO put the import in try-except block

# Proto dependencies
import commons_pb2
import srv6_manager_pb2
import srv6_manager_pb2_grpc

# Load environment variables from .env file
# load_dotenv()

# Folder containing this script
BASE_PATH = os.path.dirname(os.path.realpath(__file__))


# Global variables definition
#
#
# Netlink error codes
NETLINK_ERROR_NO_SUCH_PROCESS = 3
NETLINK_ERROR_FILE_EXISTS = 17
NETLINK_ERROR_NO_SUCH_DEVICE = 19
NETLINK_ERROR_OPERATION_NOT_SUPPORTED = 95
# Logger reference
LOGGER = logging.getLogger(__name__)
#
# Default parameters for SRv6 manager
#
# Server ip and port
DEFAULT_GRPC_IP = '::'
DEFAULT_GRPC_PORT = 12345
# Debug option
SERVER_DEBUG = False
# Secure option
DEFAULT_SECURE = False
# Server certificate
DEFAULT_CERTIFICATE = 'cert_server.pem'
# Server key
DEFAULT_KEY = 'key_server.pem'


def parse_netlink_error(err):
    """Convert the errors returned by Netlink in gRPC status codes"""

    if err.code == NETLINK_ERROR_FILE_EXISTS:
        LOGGER.warning('Netlink error: File exists')
        return commons_pb2.STATUS_FILE_EXISTS
    if err.code == NETLINK_ERROR_NO_SUCH_PROCESS:
        LOGGER.warning('Netlink error: No such process')
        return commons_pb2.STATUS_NO_SUCH_PROCESS
    if err.code == NETLINK_ERROR_NO_SUCH_DEVICE:
        LOGGER.warning('Netlink error: No such device')
        return commons_pb2.STATUS_NO_SUCH_DEVICE
    if err.code == NETLINK_ERROR_OPERATION_NOT_SUPPORTED:
        LOGGER.warning('Netlink error: Operation not supported')
        return commons_pb2.STATUS_OPERATION_NOT_SUPPORTED
    LOGGER.warning('Generic internal error: %s', err)
    return commons_pb2.STATUS_INTERNAL_ERROR


class SRv6Manager(srv6_manager_pb2_grpc.SRv6ManagerServicer):
    """gRPC request handler"""

    def __init__(self):
        # Setup VPP
        self.vpp = vpp_init()
        # Non-loopback interfaces
        self.non_loopback_interfaces = list()
        # Loopback interfaces
        self.loopback_interfaces = list()
        # Mapping interface name to interface index
        self.interface_to_idx = dict()
        # Resolve the interfaces
        for link in self.ip_route.get_links():
            # Check the IFF_LOOPBACK flag of the interfaces
            # and make separation between loopback interfaces and
            # non-loopback interfaces
            if not link.get('flags') & IFF_LOOPBACK == 0:
                self.loopback_interfaces.append(
                    link.get_attr('IFLA_IFNAME'))
            else:
                self.non_loopback_interfaces.append(
                    link.get_attr('IFLA_IFNAME'))
        # Build mapping interface to index
        interfaces = self.loopback_interfaces + self.non_loopback_interfaces
        # Iterate on the interfaces
        for interface in interfaces:
            # Add interface index
            self.interface_to_idx[interface] = \
                self.ip_route.link_lookup(ifname=interface)[0]
        # Behavior handlers
        self.behavior_handlers = {
            'End': self.handle_end_behavior_request,
            'End.X': self.handle_end_x_behavior_request,
            'End.T': self.handle_end_t_behavior_request,
            'End.DX2': self.handle_end_dx2_behavior_request,
            'End.DX6': self.handle_end_dx6_behavior_request,
            'End.DX4': self.handle_end_dx4_behavior_request,
            'End.DT6': self.handle_end_dt6_behavior_request,
            'End.DT4': self.handle_end_dt4_behavior_request,
            'End.B6': self.handle_end_b6_behavior_request,
            'End.B6.Encaps': self.handle_end_b6_encaps_behavior_request,
        }

    def vpp_init(self):
        # first, construct a vpp instance from vpp json api files
        # this will be a header for all python vpp scripts
        # directory containing all the json api files.
        # if vpp is installed on the system, these will be in /usr/share/vpp/api/
        vpp_json_dir = os.environ['VPP'] + \
            '/build-root/install-vpp_debug-native/vpp/share/vpp/api/core'
        # construct a list of all the json api files
        jsonfiles = []
        for root, dirnames, filenames in os.walk(vpp_json_dir):
            for filename in fnmatch.filter(filenames, '*.api.json'):
                jsonfiles.append(os.path.join(vpp_json_dir, filename))
        if not jsonfiles:
            print('Error: no json api files found')
            exit(-1)
        # use all those files to create vpp.
        # Note that there will be no vpp method available before vpp.connect()
        self.vpp = VPP(jsonfiles)
        self.vpp.connect('papi-example')
        # None
        # You're all set.
        # You can check the list of available methods by calling dir(vpp)
        # show vpp version
        rv = self.vpp.api.show_version()
        LOGGER.info('VPP version =', rv.version.decode().rstrip('\0x00'))

    def vpp_uninit(self):
        # Disconnect from VPP
        res = self.vpp.disconnect()
        # If r == 0: success
        return res == 0

    def handle_srv6_path_request(self, operation, request, context):
        # pylint: disable=unused-argument
        """Handler for SRv6 paths"""

        LOGGER.debug('config received:\n%s', request)
        # Perform operation
        if operation in ['change']:
            return srv6_manager_pb2.SRv6ManagerReply(
                status=commons_pb2.STATUS_OPERATION_NOT_SUPPORTED)
        if operation == 'get':
            return srv6_manager_pb2.SRv6ManagerReply(
                status=commons_pb2.STATUS_OPERATION_NOT_SUPPORTED)
        if operation in ['add']:
            # Let's push the routes
            for path in request.paths:
                # Extract BSID
                bsid_addr = path.bsid
                # Extract SID list
                segments = []
                for srv6_segment in path.sr_path:
                    segments.append(srv6_segment.segment)
                num_sids = len(segments)
                while len(segments) < 16:
                    segments.append('')
                # segments.reverse()
                table = path.table
                if path.table == -1:
                    table = None
                metric = path.metric
                if path.metric == -1:
                    metric = None
                if path.encapmode == 'encap':
                    is_encap = True
                elif path.encapmode == 'inline':
                    is_encap = False
                else:
                    LOGGER.error('Encap mode not supported')
                    return srv6_manager_pb2.SRv6ManagerReply(
                        status=commons_pb2.STATUS_OPERATION_NOT_SUPPORTED)
                # if segments == []:
                #     segments = ['::']
                # oif = None
                # if path.device != '':
                #     oif = self.interface_to_idx[path.device]
                # elif operation == 'add':
                #     oif = self.interface_to_idx[
                #         self.non_loopback_interfaces[0]]
                # self.ip_route.route(operation, dst=path.destination,
                #                     oif=oif,
                #                     table=table,
                #                     priority=metric,
                #                     encap={'type': 'seg6',
                #                            'mode': path.encapmode,
                #                            'segs': segments})
                # self.vpp.api.sr_set_encap_source(         TODO
                #     encaps_source = src_addr
                # )
                self.vpp.api.sr_policy_add(
                    bsid_addr=bsid_addr,
                    is_encap=is_encap,
                    weight=metric,
                    fib_table=table,
                    sids={
                        "num_sids": num_sids,
                        "sids": segments
                    }
                )
                self.vpp.api.sr_steering_add_del(
                    is_del=0,
                    bsid_addr=bsid_addr,
                    table_id=table,
                    prefix_addr=path.destination.split('/')[0],
                    mask_width=path.destination.split('/')[1]
                    if len(path.destination.split('/')) > 1 else None
                )
        elif operation in ['del']:
            # Let's push the routes
            for path in request.paths:
                # Extract BSID
                bsid_addr = path.bsid
                # Extract SID list
                segments = []
                for srv6_segment in path.sr_path:
                    segments.append(srv6_segment.segment)
                num_sids = len(segments)
                while len(segments) < 16:
                    segments.append('')
                # segments.reverse()
                table = path.table
                if path.table == -1:
                    table = None
                metric = path.metric
                if path.metric == -1:
                    metric = None
                # if segments == []:
                #     segments = ['::']
                # oif = None
                # if path.device != '':
                #     oif = self.interface_to_idx[path.device]
                # elif operation == 'add':
                #     oif = self.interface_to_idx[
                #         self.non_loopback_interfaces[0]]
                # self.ip_route.route(operation, dst=path.destination,
                #                     oif=oif,
                #                     table=table,
                #                     priority=metric,
                #                     encap={'type': 'seg6',
                #                            'mode': path.encapmode,
                #                            'segs': segments})
                self.vpp.api.sr_steering_add_del(
                    is_del=1,
                    bsid_addr=bsid_addr,
                    table_id=table,
                    prefix_addr=path.destination.split('/')[0],
                    mask_width=path.destination.split('/')[1]
                    if len(path.destination.split('/')) > 1 else None
                )
                self.vpp.api.sr_policy_del(
                    bsid_addr=bsid_addr
                )
                # self.vpp.api.sr_set_encap_source(         TODO
                #     encaps_source = src_addr
                # )
        else:
            # Operation unknown: this is a bug
            LOGGER.error('Unrecognized operation: %s', operation)
            sys.exit(-1)
        # and create the response
        LOGGER.debug('Send response: OK')
        return srv6_manager_pb2.SRv6ManagerReply(
            status=commons_pb2.STATUS_SUCCESS)

    def handle_end_behavior_request(self, operation, behavior):
        """Handle seg6local End behavior"""

        # Extract params from request
        segment = behavior.segment
        device = behavior.device
        table = behavior.table
        metric = behavior.metric
        # Check optional params
        device = device if device != '' \
            else self.non_loopback_interfaces[0]
        table = table if table != -1 else None
        metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'del':
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add', 'change']:
            # Build encap info
            encap = {
                'type': 'seg6local',
                'action': 'End'
            }
            # Handle route
            self.ip_route.route(operation, family=AF_INET6,
                                dst=segment,
                                oif=self.interface_to_idx[device],
                                table=table,
                                priority=metric,
                                encap=encap)
            # and create the response
            LOGGER.debug('Send response: OK')
            return commons_pb2.STATUS_SUCCESS
        # Operation unknown: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_end_x_behavior_request(self, operation, behavior):
        """Handle seg6local End.X behavior"""

        # Extract params from request
        segment = behavior.segment
        nexthop = behavior.nexthop
        device = behavior.device
        table = behavior.table
        metric = behavior.metric
        # Check optional params
        device = device if device != '' \
            else self.non_loopback_interfaces[0]
        table = table if table != -1 else None
        metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'del':
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add', 'change']:
            # Build encap info
            encap = {
                'type': 'seg6local',
                'action': 'End.X',
                'nh4': nexthop
            }
            # Handle route
            self.ip_route.route(operation, family=AF_INET6,
                                dst=segment,
                                oif=self.interface_to_idx[device],
                                table=table,
                                priority=metric,
                                encap=encap)
            # and create the response
            LOGGER.debug('Send response: OK')
            return commons_pb2.STATUS_SUCCESS
        # Operation unknown: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_end_t_behavior_request(self, operation, behavior):
        """Handle seg6local End.T behavior"""

        # Extract params from request
        segment = behavior.segment
        lookup_table = behavior.lookup_table
        device = behavior.device
        table = behavior.table
        metric = behavior.metric
        # Check optional params
        device = device if device != '' \
            else self.non_loopback_interfaces[0]
        table = table if table != -1 else None
        metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'del':
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add', 'change']:
            # Build encap info
            encap = {
                'type': 'seg6local',
                'action': 'End.T',
                'table': lookup_table
            }
            # Handle route
            self.ip_route.route(operation, family=AF_INET6,
                                dst=segment,
                                oif=self.interface_to_idx[device],
                                table=table,
                                priority=metric,
                                encap=encap)
            # and create the response
            LOGGER.debug('Send response: OK')
            return commons_pb2.STATUS_SUCCESS
        # Operation unknown: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_end_dx2_behavior_request(self, operation, behavior):
        """Handle seg6local End.DX2 behavior"""

        # Extract params from request
        segment = behavior.segment
        interface = behavior.interface
        device = behavior.device
        table = behavior.table
        metric = behavior.metric
        # Check optional params
        device = device if device != '' \
            else self.non_loopback_interfaces[0]
        table = table if table != -1 else None
        metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'del':
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add', 'change']:
            # Build encap info
            encap = {
                'type': 'seg6local',
                'action': 'End.DX2',
                'oif': interface
            }
            # Handle route
            self.ip_route.route(operation, family=AF_INET6,
                                dst=segment,
                                oif=self.interface_to_idx[device],
                                table=table,
                                priority=metric,
                                encap=encap)
            # and create the response
            LOGGER.debug('Send response: OK')
            return commons_pb2.STATUS_SUCCESS
        # Operation unknown: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_end_dx6_behavior_request(self, operation, behavior):
        """Handle seg6local End.DX6 behavior"""

        # Extract params from request
        segment = behavior.segment
        nexthop = behavior.nexthop
        device = behavior.device
        table = behavior.table
        metric = behavior.metric
        # Check optional params
        device = device if device != '' \
            else self.non_loopback_interfaces[0]
        table = table if table != -1 else None
        metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'del':
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add', 'change']:
            # Build encap info
            encap = {
                'type': 'seg6local',
                'action': 'End.DX6',
                'nh4': nexthop
            }
            # Handle route
            self.ip_route.route(operation, family=AF_INET6,
                                dst=segment,
                                oif=self.interface_to_idx[device],
                                table=table,
                                priority=metric,
                                encap=encap)
            # and create the response
            LOGGER.debug('Send response: OK')
            return commons_pb2.STATUS_SUCCESS
        # Operation unknown: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_end_dx4_behavior_request(self, operation, behavior):
        """Handle seg6local End.DX4 behavior"""

        # Extract params from request
        segment = behavior.segment
        nexthop = behavior.nexthop
        device = behavior.device
        table = behavior.table
        metric = behavior.metric
        # Check optional params
        device = device if device != '' \
            else self.non_loopback_interfaces[0]
        table = table if table != -1 else None
        metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'del':
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add', 'change']:
            # Build encap info
            encap = {
                'type': 'seg6local',
                'action': 'End.DX4',
                'nh4': nexthop
            }
            # Handle route
            self.ip_route.route(operation, family=AF_INET6,
                                dst=segment,
                                oif=self.interface_to_idx[device],
                                table=table,
                                priority=metric,
                                encap=encap)
            # and create the response
            LOGGER.debug('Send response: OK')
            return commons_pb2.STATUS_SUCCESS
        # Operation unknown: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_end_dt6_behavior_request(self, operation, behavior):
        """Handle seg6local End.DT6 behavior"""

        # Extract params from request
        segment = behavior.segment
        lookup_table = behavior.lookup_table
        device = behavior.device
        table = behavior.table
        metric = behavior.metric
        # Check optional params
        device = device if device != '' \
            else self.non_loopback_interfaces[0]
        table = table if table != -1 else None
        metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'del':
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add', 'change']:
            # Build encap info
            encap = {
                'type': 'seg6local',
                'action': 'End.DT6',
                'table': lookup_table
            }
            # Handle route
            self.ip_route.route(operation, family=AF_INET6,
                                dst=segment,
                                oif=self.interface_to_idx[device],
                                table=table,
                                priority=metric,
                                encap=encap)
            # and create the response
            LOGGER.debug('Send response: OK')
            return commons_pb2.STATUS_SUCCESS
        # Operation unknown: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_end_dt4_behavior_request(self, operation, behavior):
        """Handle seg6local End.DT4 behavior"""

        # Extract params from request
        segment = behavior.segment
        lookup_table = behavior.lookup_table
        device = behavior.device
        table = behavior.table
        metric = behavior.metric
        # Check optional params
        device = device if device != '' \
            else self.non_loopback_interfaces[0]
        table = table if table != -1 else None
        metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'del':
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add', 'change']:
            # Build encap info
            encap = {
                'type': 'seg6local',
                'action': 'End.DT4',
                'table': lookup_table
            }
            # Handle route
            self.ip_route.route(operation, family=AF_INET6,
                                dst=segment,
                                oif=self.interface_to_idx[device],
                                table=table,
                                priority=metric,
                                encap=encap)
            # and create the response
            LOGGER.debug('Send response: OK')
            return commons_pb2.STATUS_SUCCESS
        # Operation unknown: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_end_b6_behavior_request(self, operation, behavior):
        """Handle seg6local End.B6 behavior"""

        # Extract params from request
        segment = behavior.segment
        device = behavior.device
        table = behavior.table
        metric = behavior.metric
        # Check optional params
        device = device if device != '' \
            else self.non_loopback_interfaces[0]
        table = table if table != -1 else None
        metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'del':
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add', 'change']:
            # Rebuild segments
            segments = []
            for srv6_segment in behavior.segs:
                segments.append(srv6_segment.segment)
            # pyroute2 requires the segments in reverse order
            segments.reverse()
            # Build encap info
            encap = {
                'type': 'seg6local',
                'action': 'End.B6',
                'srh': {'segs': segments}
            }
            # Handle route
            self.ip_route.route(operation, family=AF_INET6,
                                dst=segment,
                                oif=self.interface_to_idx[device],
                                table=table,
                                priority=metric,
                                encap=encap)
            # and create the response
            LOGGER.debug('Send response: OK')
            return commons_pb2.STATUS_SUCCESS
        # Operation unknown: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_end_b6_encaps_behavior_request(self, operation, behavior):
        """Handle seg6local End.B6.Encaps behavior"""

        # Extract params from request
        segment = behavior.segment
        device = behavior.device
        table = behavior.table
        metric = behavior.metric
        # Check optional params
        device = device if device != '' \
            else self.non_loopback_interfaces[0]
        table = table if table != -1 else None
        metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'del':
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add', 'change']:
            # Rebuild segments
            segments = []
            for srv6_segment in behavior.segs:
                segments.append(srv6_segment.segment)
            # pyroute2 requires the segments in reverse order
            segments.reverse()
            # Build encap info
            encap = {
                'type': 'seg6local',
                'action': 'End.B6.Encaps',
                'srh': {'segs': segments}
            }
            # Handle route
            self.ip_route.route(operation, family=AF_INET6,
                                dst=segment,
                                oif=self.interface_to_idx[device],
                                table=table,
                                priority=metric,
                                encap=encap)
            # and create the response
            LOGGER.debug('Send response: OK')
            return commons_pb2.STATUS_SUCCESS
        # Operation unknown: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_srv6_behavior_del_request(self, behavior):
        """Delete a route"""

        # Extract params
        segment = behavior.segment
        device = behavior.device if behavior.device != '' \
            else self.non_loopback_interfaces[0]
        table = behavior.table if behavior.table != -1 else None
        metric = behavior.metric if behavior.metric != -1 else None
        # Remove the route
        self.ip_route.route('del', family=AF_INET6,
                            oif=device, dst=segment,
                            table=table, priority=metric)
        # Return success
        return commons_pb2.STATUS_SUCCESS

    def handle_srv6_behavior_get_request(self, behavior):
        # pylint checks on this method are temporary disabled
        # pylint: disable=no-self-use, unused-argument
        """Get a route"""

        LOGGER.info('get opertion not yet implemented\n')
        return commons_pb2.STATUS_OPERATION_NOT_SUPPORTED

    def dispatch_srv6_behavior(self, operation, behavior):
        """Pass the request to the right handler"""

        # Get the handler
        handler = self.behavior_handlers.get(behavior.action)
        # Pass the behavior to the handler
        if handler is not None:
            return handler(operation, behavior)
        # Error
        LOGGER.error('Error: Unrecognized action: %s', behavior.action)
        return srv6_manager_pb2.SRv6ManagerReply(
            status=commons_pb2.STATUS_INVALID_ACTION)

    def handle_srv6_behavior_request(self, operation, request, context):
        # pylint: disable=unused-argument
        """Handler for SRv6 behaviors"""

        LOGGER.debug('config received:\n%s', request)
        # Let's process the request
        try:
            for behavior in request.behaviors:
                # Pass the request to the right handler
                res = self.dispatch_srv6_behavior(operation, behavior)
                if res != commons_pb2.STATUS_SUCCESS:
                    return srv6_manager_pb2.SRv6ManagerReply(status=res)
            # and create the response
            LOGGER.debug('Send response: OK')
            return srv6_manager_pb2.SRv6ManagerReply(
                status=commons_pb2.STATUS_SUCCESS)
        except NetlinkError as err:
            return srv6_manager_pb2.SRv6ManagerReply(
                status=parse_netlink_error(err))
