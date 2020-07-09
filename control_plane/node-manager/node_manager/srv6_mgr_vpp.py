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
# from vpp_papi import VPP    # TODO put the import in try-except block

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


def exec_vpp_cmd(cmd):
    import subprocess
    return subprocess.check_output(['vppctl', cmd])


class SRv6ManagerVPP():

    def __init__(self):
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

    def handle_srv6_src_addr_request(self, operation, request, context):   # TODO
        '''
        This function is used to setup the source address used for the SRv6
        encapsulation, equivalent to:

        > set vppctl set sr encaps source addr $VPP_SR_Policy_src_addr
        '''
        # Return value
        res = commons_pb2.STATUS_SUCCESS
        # String representing the command to be sent to VPP
        cmd = 'set sr encaps source addr %s' % str(request.src_addr)
        # Send the command to VPP
        # If success, an empty string will be returned
        LOGGER.debug('Sending command to VPP: %s' % cmd)
        res = exec_vpp_cmd(cmd).decode()
        if res != '':
            # Failure
            logging.error('VPP returned an error: %s' % res)
            res = commons_pb2.STATUS_INTERNAL_ERROR
        return srv6_manager_pb2.SRv6ManagerReply(status=res)

    def handle_srv6_policy_request(self, operation, request, context):
        '''
        This function is used to create, delete or change a SRv6 policy,
        equivalent to:

        > vppctl sr policy add bsid $VPP_SR_Policy_BSID next $srv6_1st_sid
          next $srv6_2nd_sid
        '''
        # Perform the operation
        if operation in ['change', 'get']:
            LOGGER.error('Operation not yet supported: %s' % operation)
            return srv6_manager_pb2.SRv6ManagerReply(
                status=commons_pb2.STATUS_OPERATION_NOT_SUPPORTED)
        if operation in ['add', 'del']:
            # Let's push the routes
            for policy in request.policies:
                # Extract BSID
                bsid_addr = policy.bsid_addr
                # Extract SID list
                segments = []
                for srv6_segment in policy.sr_path:
                    segments.append(srv6_segment.segment)
                # Extract the table
                table = policy.table
                if policy.table == -1:
                    table = None
                # Extract the metric
                metric = policy.metric
                if policy.metric == -1:
                    metric = None
                # Create a SR policy
                # This command returns a empty string in case of success
                cmd = ('sr policy %s bsid %s' % (operation, bsid_addr))
                # Add segments
                for segment in segments:
                    cmd += ' next %s' % segment
                # Add metric
                if metric is not None:
                    cmd += ' weight %s' % metric
                # Add the table
                if table is not None:
                    cmd += ' fib-table %s' % table
                # Execute the command
                LOGGER.debug('Sending command to VPP: %s' % cmd)
                res = exec_vpp_cmd(cmd).decode()
                if res != '':
                    # Failure
                    logging.error('VPP returned an error: %s' % res)
                    return srv6_manager_pb2.SRv6ManagerReply(
                        status=commons_pb2.STATUS_INTERNAL_ERROR)
        else:
            # Operation unknown: this is a bug
            LOGGER.error('Unrecognized operation: %s', operation)
            sys.exit(-1)
        # and create the response
        LOGGER.debug('Send response: OK')
        return srv6_manager_pb2.SRv6ManagerReply(
            status=commons_pb2.STATUS_SUCCESS)

    def handle_srv6_path_request(self, operation, request, context):
        # pylint: disable=unused-argument
        '''
        Handler for SRv6 paths
        '''
        LOGGER.debug('config received:\n%s', request)
        # Perform operation
        if operation in ['change', 'get']:
            LOGGER.error('Operation not yet supported: %s' % operation)
            return srv6_manager_pb2.SRv6ManagerReply(
                status=commons_pb2.STATUS_OPERATION_NOT_SUPPORTED)
        if operation in ['add', 'del']:
            # Let's push the routes
            for path in request.paths:
                # Extract BSID
                bsid_addr = path.bsid_addr
                # Extract SID list
                segments = []
                for srv6_segment in path.sr_path:
                    segments.append(srv6_segment.segment)
                # Extract the table
                table = path.table
                if path.table == -1:
                    table = None
                # Extract the metric
                metric = path.metric
                if path.metric == -1:
                    metric = None
                # Perform operation
                encapmode = path.encapmode
                # Steer packets into a SR policy
                # This command returns a empty string in case of success
                destination = str(path.destination)
                if len(destination.split('/')) == 1:
                    destination += '/128'
                # Is a delete operation?
                del_cmd = 'del' if operation == 'del' else ''
                # Build the command
                cmd = ('sr steer %s l3 %s via bsid %s'
                       % (del_cmd, destination, bsid_addr))
                # Add the metric
                if metric is not None:
                    cmd += ' weight %s' % metric
                # Add the table
                if table is not None:
                    cmd += ' fib-table %s' % table
                # Execute the command
                LOGGER.debug('Sending command to VPP: %s' % cmd)
                res = exec_vpp_cmd(cmd).decode()
                if res != '':
                    # Failure
                    logging.error('VPP returned an error: %s' % res)
                    return srv6_manager_pb2.SRv6ManagerReply(
                        status=commons_pb2.STATUS_INTERNAL_ERROR)
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
            # Build the command
            cmd = ('sr localsid address %s behavior end' % segment)
            # Add the table
            if table is not None:
                cmd += ' fib-table %s' % table
            # Execute the command
            LOGGER.debug('Sending command to VPP: %s' % cmd)
            res = exec_vpp_cmd(cmd).decode()
            if res != '':
                # Failure
                logging.error('VPP returned an error: %s' % res)
                return srv6_manager_pb2.SRv6ManagerReply(
                    status=commons_pb2.STATUS_INTERNAL_ERROR)
        else:
            # Operation unknown: this is a bug
            LOGGER.error('BUG - Unrecognized operation: %s', operation)
            sys.exit(-1)
        # and create the response
        LOGGER.debug('Send response: OK')
        return commons_pb2.STATUS_SUCCESS

    def handle_end_x_behavior_request(self, operation, behavior):
        """Handle seg6local End.X behavior"""

        # Extract params from request
        segment = behavior.segment
        interface = behavior.interface
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
            # Build the command
            cmd = ('sr localsid address %s behavior end.x %s %s'
                   % (segment, interface, nexthop))
            # Add the table
            if table is not None:
                cmd += ' fib-table %s' % table
            # Execute the command
            LOGGER.debug('Sending command to VPP: %s' % cmd)
            res = exec_vpp_cmd(cmd).decode()
            if res != '':
                # Failure
                logging.error('VPP returned an error: %s' % res)
                return srv6_manager_pb2.SRv6ManagerReply(
                    status=commons_pb2.STATUS_INTERNAL_ERROR)
        else:
            # Operation unknown: this is a bug
            LOGGER.error('BUG - Unrecognized operation: %s', operation)
            sys.exit(-1)
        # and create the response
        LOGGER.debug('Send response: OK')
        return commons_pb2.STATUS_SUCCESS

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
            # Build the command
            cmd = ('sr localsid address %s behavior end.t %s'
                   % (segment, lookup_table))
            # Add the table
            if table is not None:
                cmd += ' fib-table %s' % table
            # Execute the command
            LOGGER.debug('Sending command to VPP: %s' % cmd)
            res = exec_vpp_cmd(cmd).decode()
            if res != '':
                # Failure
                logging.error('VPP returned an error: %s' % res)
                return srv6_manager_pb2.SRv6ManagerReply(
                    status=commons_pb2.STATUS_INTERNAL_ERROR)
        else:
            # Operation unknown: this is a bug
            LOGGER.error('BUG - Unrecognized operation: %s', operation)
            sys.exit(-1)
        # and create the response
        LOGGER.debug('Send response: OK')
        return commons_pb2.STATUS_SUCCESS

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
            # Build the command
            cmd = ('sr localsid address %s behavior end.dx2 %s'
                   % (segment, interface))
            # Add the table
            if table is not None:
                cmd += ' fib-table %s' % table
            # Execute the command
            LOGGER.debug('Sending command to VPP: %s' % cmd)
            res = exec_vpp_cmd(cmd).decode()
            if res != '':
                # Failure
                logging.error('VPP returned an error: %s' % res)
                return srv6_manager_pb2.SRv6ManagerReply(
                    status=commons_pb2.STATUS_INTERNAL_ERROR)
        else:
            # Operation unknown: this is a bug
            LOGGER.error('BUG - Unrecognized operation: %s', operation)
            sys.exit(-1)
        # and create the response
        LOGGER.debug('Send response: OK')
        return commons_pb2.STATUS_SUCCESS

    def handle_end_dx6_behavior_request(self, operation, behavior):
        """Handle seg6local End.DX6 behavior"""

        # Extract params from request
        segment = behavior.segment
        interface = behavior.interface
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
            # Build the command
            cmd = ('sr localsid address %s behavior end.dx6 %s %s'
                   % (segment, interface, nexthop))
            # Add the table
            if table is not None:
                cmd += ' fib-table %s' % table
            # Execute the command
            LOGGER.debug('Sending command to VPP: %s' % cmd)
            res = exec_vpp_cmd(cmd).decode()
            if res != '':
                # Failure
                logging.error('VPP returned an error: %s' % res)
                return srv6_manager_pb2.SRv6ManagerReply(
                    status=commons_pb2.STATUS_INTERNAL_ERROR)
        else:
            # Operation unknown: this is a bug
            LOGGER.error('BUG - Unrecognized operation: %s', operation)
            sys.exit(-1)
        # and create the response
        LOGGER.debug('Send response: OK')
        return commons_pb2.STATUS_SUCCESS

    def handle_end_dx4_behavior_request(self, operation, behavior):
        """Handle seg6local End.DX4 behavior"""

        # Extract params from request
        segment = behavior.segment
        interface = behavior.interface
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
            # Build the command
            cmd = ('sr localsid address %s behavior end.dx4 %s %s'
                   % (segment, interface, nexthop))
            # Add the table
            if table is not None:
                cmd += ' fib-table %s' % table
            # Execute the command
            LOGGER.debug('Sending command to VPP: %s' % cmd)
            res = exec_vpp_cmd(cmd).decode()
            if res != '':
                # Failure
                logging.error('VPP returned an error: %s' % res)
                return srv6_manager_pb2.SRv6ManagerReply(
                    status=commons_pb2.STATUS_INTERNAL_ERROR)
        else:
            # Operation unknown: this is a bug
            LOGGER.error('BUG - Unrecognized operation: %s', operation)
            sys.exit(-1)
        # and create the response
        LOGGER.debug('Send response: OK')
        return commons_pb2.STATUS_SUCCESS

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
            # Build the command
            cmd = ('sr localsid address %s behavior end.dt6 %s'
                   % (segment, lookup_table))
            # Add the table
            if table is not None:
                cmd += ' fib-table %s' % table
            # Execute the command
            LOGGER.debug('Sending command to VPP: %s' % cmd)
            res = exec_vpp_cmd(cmd).decode()
            if res != '':
                # Failure
                logging.error('VPP returned an error: %s' % res)
                return srv6_manager_pb2.SRv6ManagerReply(
                    status=commons_pb2.STATUS_INTERNAL_ERROR)
        else:
            # Operation unknown: this is a bug
            LOGGER.error('BUG - Unrecognized operation: %s', operation)
            sys.exit(-1)
        # and create the response
        LOGGER.debug('Send response: OK')
        return commons_pb2.STATUS_SUCCESS

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
            # Build the command
            cmd = ('sr localsid address %s behavior end.dt4 %s'
                   % (segment, lookup_table))
            # Add the table
            if table is not None:
                cmd += ' fib-table %s' % table
            # Execute the command
            LOGGER.debug('Sending command to VPP: %s' % cmd)
            res = exec_vpp_cmd(cmd).decode()
            if res != '':
                # Failure
                logging.error('VPP returned an error: %s' % res)
                return srv6_manager_pb2.SRv6ManagerReply(
                    status=commons_pb2.STATUS_INTERNAL_ERROR)
        else:
            # Operation unknown: this is a bug
            LOGGER.error('BUG - Unrecognized operation: %s', operation)
            sys.exit(-1)
        # and create the response
        LOGGER.debug('Send response: OK')
        return commons_pb2.STATUS_SUCCESS

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
            # segments = []
            # for srv6_segment in behavior.segs:
            #     segments.append(srv6_segment.segment)
            # Build the command
            # cmd = ('sr localsid address %s behavior end.x %s %s'
            #        % (segment, interface, nexthop))
            # # Add the table
            # if table is not None:
            #     cmd += ' fib-table %s' % table
            # # Execute the command
            # LOGGER.debug('Sending command to VPP: %s' % cmd)
            # res = exec_vpp_cmd(cmd).decode()
            # if res != '':
            #     # Failure
            #     logging.error('VPP returned an error: %s' % res)
            #     return srv6_manager_pb2.SRv6ManagerReply(
            #         status=commons_pb2.STATUS_INTERNAL_ERROR)
            LOGGER.info('End.B6 behavior is not yet implemented\n')
            return commons_pb2.STATUS_OPERATION_NOT_SUPPORTED
        else:
            # Operation unknown: this is a bug
            LOGGER.error('BUG - Unrecognized operation: %s', operation)
            sys.exit(-1)
        # and create the response
        LOGGER.debug('Send response: OK')
        return commons_pb2.STATUS_SUCCESS

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
            # segments = []
            # for srv6_segment in behavior.segs:
            #     segments.append(srv6_segment.segment)
            # Build the command
            # cmd = ('sr localsid address %s behavior end.x %s %s'
            #        % (segment, interface, nexthop))
            # # Add the table
            # if table is not None:
            #     cmd += ' fib-table %s' % table
            # # Execute the command
            # LOGGER.debug('Sending command to VPP: %s' % cmd)
            # res = exec_vpp_cmd(cmd).decode()
            # if res != '':
            #     # Failure
            #     logging.error('VPP returned an error: %s' % res)
            #     return srv6_manager_pb2.SRv6ManagerReply(
            #         status=commons_pb2.STATUS_INTERNAL_ERROR)
            LOGGER.info('End.B6.Encaps behavior is not yet implemented\n')
            return commons_pb2.STATUS_OPERATION_NOT_SUPPORTED
        else:
            # Operation unknown: this is a bug
            LOGGER.error('BUG - Unrecognized operation: %s', operation)
            sys.exit(-1)
        # and create the response
        LOGGER.debug('Send response: OK')
        return commons_pb2.STATUS_SUCCESS

    def handle_un_behavior_request(self, operation, behavior):
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
            # # Build encap info
            # encap = {
            #     'type': 'seg6local',
            #     'action': 'uN'
            # }
            # # Handle route
            # self.ip_route.route(operation, family=AF_INET6,
            #                     dst=segment,
            #                     oif=self.interface_to_idx[device],
            #                     table=table,
            #                     priority=metric,
            #                     encap=encap)
            LOGGER.info('uN behavior is not yet implemented\n')
            return commons_pb2.STATUS_OPERATION_NOT_SUPPORTED
        else:
            # Operation unknown: this is a bug
            LOGGER.error('BUG - Unrecognized operation: %s', operation)
            sys.exit(-1)
        # and create the response
        LOGGER.debug('Send response: OK')
        return commons_pb2.STATUS_SUCCESS

    def handle_srv6_behavior_del_request(self, behavior):
        """Delete a route"""

        # Extract params
        segment = behavior.segment
        device = behavior.device if behavior.device != '' \
            else self.non_loopback_interfaces[0]
        device = self.interface_to_idx[device]
        table = behavior.table if behavior.table != -1 else None
        metric = behavior.metric if behavior.metric != -1 else None
        # Build the command
        cmd = ('sr localsid address %s behavior' % segment)
        # Add the table
        if table is not None:
            cmd += ' fib-table %s' % table
        # Execute the command
        LOGGER.debug('Sending command to VPP: %s' % cmd)
        res = exec_vpp_cmd(cmd).decode()
        if res != '':
            # Failure
            logging.error('VPP returned an error: %s' % res)
            return srv6_manager_pb2.SRv6ManagerReply(
                status=commons_pb2.STATUS_INTERNAL_ERROR)
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
        return commons_pb2.STATUS_INVALID_ACTION

    def handle_srv6_behavior_request(self, operation, request, context):
        # pylint: disable=unused-argument
        """Handler for SRv6 behaviors"""

        LOGGER.debug('config received:\n%s', request)
        # Let's process the request
        try:
            for behavior in request.behaviors:
                if operation == 'del':
                    res = self.handle_srv6_behavior_del_request(behavior)
                    return srv6_manager_pb2.SRv6ManagerReply(status=res)
                if operation == 'get':
                    res = self.handle_srv6_behavior_get_request(behavior)
                    return srv6_manager_pb2.SRv6ManagerReply(status=res)
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
