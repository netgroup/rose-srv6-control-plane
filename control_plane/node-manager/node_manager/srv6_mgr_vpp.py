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

'''
This module provides different VPP-related functionalities for a
SRv6 Manager
'''


# General imports
import logging
import subprocess
import os
import sys

# VPP dependencies
# try:
#     from vpp_papi import VPP
# except ImportError:
#     print('VPP modules not found')
#     sys.exit(-2)

# Proto dependencies
from node_manager.constants import STATUS_CODE

# Folder containing this script
BASE_PATH = os.path.dirname(os.path.realpath(__file__))


# Global variables definition
#
#
# Logger reference
LOGGER = logging.getLogger(__name__)

# Extract socket file name to be used for VPP from env variables
# If not set, we connect to the main instance of VPP
VPP_SOCK_FILE = os.getenv('vpp_sock_file', None)


class SRv6ManagerVPP():
    '''
    This class implements several VPP-related functionalities of a SRv6
    Manager
    '''

    def __init__(self):
        # Socket file for VPP
        self.vpp_sock_file = VPP_SOCK_FILE
        # Register behavior handlers
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

    def exec_vpp_cmd(self, cmd):
        '''
        Helper function used to send a command to VPP through vppctl

        :param cmd: Command to be sent to VPP
        :return: Empty string if the operation completed successfully, or
                 an error message.
        :rtype: str
        '''
        # Start building the command: "vppctl"
        vpp_cmd = ['vppctl']
        # Append the socket file name to the command
        if self.vpp_sock_file is not None:
            vpp_cmd += ['-s', self.vpp_sock_file]
        # Append the request command
        vpp_cmd += [cmd]
        # Finally, send the command to VPP
        return subprocess.check_output(vpp_cmd)

    def handle_srv6_src_addr_request(self, operation, request, context):
        '''
        This function is used to setup the source address used for the SRv6
        encapsulation, equivalent to:

        > set vppctl set sr encaps source addr $VPP_SR_Policy_src_addr
        '''
        # pylint: disable=unused-argument
        #
        LOGGER.debug('Entering handle_srv6_src_addr_request')
        if operation in ['add', 'get', 'del']:
            LOGGER.error('Operation %s not supported', operation)
            return STATUS_CODE['STATUS_OPERATION_NOT_SUPPORTED']
        if operation in ['change']:
            # String representing the command to be sent to VPP
            cmd = 'set sr encaps source addr %s' % str(request.src_addr)
            # Send the command to VPP
            # If success, an empty string will be returned
            # In case of error, the error message is returned
            LOGGER.debug('Sending command to VPP: %s', cmd)
            res = self.exec_vpp_cmd(cmd).decode()
            if res != '':
                # The operation failed
                logging.error('VPP returned an error: %s', res)
                return STATUS_CODE['STATUS_INTERNAL_ERROR']
            # Return the result
            LOGGER.debug('Operation completed successfully')
            return STATUS_CODE['STATUS_SUCCESS']
        # Unknown operation: this is a bug
        LOGGER.error('Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_srv6_policy_request(self, operation, request, context,
                                   ret_policies):
        '''
        This function is used to create, delete or change a SRv6 policy,
        equivalent to:

        > vppctl sr policy add bsid $VPP_SR_Policy_BSID next $srv6_1st_sid
          next $srv6_2nd_sid
        '''
        # pylint: disable=unused-argument
        #
        LOGGER.debug('Entering handle_srv6_policy_request')
        # Perform the operation
        if operation in ['change', 'get']:
            # Currently only "add" and "del" operations are supported
            LOGGER.error('Operation not yet supported: %s', operation)
            return STATUS_CODE['STATUS_OPERATION_NOT_SUPPORTED']
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
                # Table is a optional parameter
                # -1 is the default value that means that no table has
                # been provided
                table = policy.table
                if policy.table == -1:
                    table = None
                # Extract the metric
                # Metric is a optional parameter
                # -1 is the default value that means that no metric has
                # been provided
                metric = policy.metric
                if policy.metric == -1:
                    metric = None
                # Build the command to create or remove the SR policy
                cmd = ('sr policy %s bsid %s' % (operation, bsid_addr))
                # Append segments to the command
                for segment in segments:
                    cmd += ' next %s' % segment
                # Append metric to the command
                if metric is not None:
                    cmd += ' weight %s' % metric
                # Append table to the command
                if table is not None:
                    cmd += ' fib-table %s' % table
                # Send the command to VPP
                # This command returns a empty string in case of success
                # The decode() function is used to convert the response to a
                # string
                LOGGER.debug('Sending command to VPP: %s', cmd)
                res = self.exec_vpp_cmd(cmd).decode()
                if res != '':
                    # The operation failed
                    logging.error('VPP returned an error: %s', res)
                    return STATUS_CODE['STATUS_INTERNAL_ERROR']
            # All the policies have been processed, create the response
            LOGGER.debug('Send response: OK')
            return STATUS_CODE['STATUS_SUCCESS']
        # Unknown operation: this is a bug
        LOGGER.error('Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_srv6_path_request(self, operation, request, context, ret_paths):
        '''
        Handler for SRv6 paths
        '''
        # pylint: disable=unused-argument
        #
        LOGGER.debug('config received:\n%s', request)
        # Perform operation
        if operation in ['change', 'get']:
            # Currently only "add" and "del" operations are supported
            LOGGER.error('Operation not yet supported: %s', operation)
            return STATUS_CODE['STATUS_OPERATION_NOT_SUPPORTED']
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
                # Table is a optional parameter
                # -1 is the default value that means that no table has
                # been provided
                table = path.table
                if path.table == -1:
                    table = None
                # Extract the metric
                # Metric is a optional parameter
                # -1 is the default value that means that no metric has
                # been provided
                metric = path.metric
                if path.metric == -1:
                    metric = None
                # Extract the encap mode
                encapmode = path.encapmode
                # Extract the destination
                destination = str(path.destination)
                # Append "/128" if no prefix len is provided
                if len(destination.split('/')) == 1:
                    destination += '/128'
                # Is a delete operation?
                del_cmd = 'del' if operation == 'del' else ''
                # Build the command to steer packets into a SR policy
                cmd = ('sr steer %s l3 %s via bsid %s'
                       % (del_cmd, destination, bsid_addr))
                # Append metric to the command
                if metric is not None:
                    cmd += ' weight %s' % metric
                # Append table to the command
                if table is not None:
                    cmd += ' fib-table %s' % table
                # Send the command to VPP
                # This command returns a empty string in case of success
                # The decode() function is used to convert the response to a
                # string
                LOGGER.debug('Sending command to VPP: %s', cmd)
                res = self.exec_vpp_cmd(cmd).decode()
                if res != '':
                    # The operation failed
                    logging.error('VPP returned an error: %s', res)
                    return STATUS_CODE['STATUS_INTERNAL_ERROR']
            # All the paths have been processed, create the response
            LOGGER.debug('Send response: OK')
            return STATUS_CODE['STATUS_SUCCESS']
        # Unknown operation: this is a bug
        LOGGER.error('Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_end_behavior_request(self, operation, behavior):
        '''
        Handle seg6local End behavior
        '''
        # Extract params from request
        segment = behavior.segment
        table = behavior.table
        metric = behavior.metric
        # Check optional params
        #
        # Table is a optional parameter
        # -1 is the default value that means that no table has
        # been provided
        table = table if table != -1 else None
        # Metric is a optional parameter
        # -1 is the default value that means that no metric has
        # been provided
        metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'change':
            LOGGER.info('Operation %s is not yet implemented\n', operation)
            return STATUS_CODE['STATUS_OPERATION_NOT_SUPPORTED']
        if operation == 'del':
            # The operation is a "delete"
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            # The operation is a "get"
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add']:
            # The operation is a "add"
            #
            # Build the command to add the behavior
            cmd = ('sr localsid address %s behavior end' % segment)
            # Append table to the command
            if table is not None:
                cmd += ' fib-table %s' % table
            # Send the command to VPP
            # This command returns a empty string in case of success
            # The decode() function is used to convert the response to a
            # string
            LOGGER.debug('Sending command to VPP: %s', cmd)
            res = self.exec_vpp_cmd(cmd).decode()
            if res != '':
                # The operation failed
                logging.error('VPP returned an error: %s', res)
                return STATUS_CODE['STATUS_INTERNAL_ERROR']
            # The behavior has been processed, create the response
            LOGGER.debug('Send response: OK')
            return STATUS_CODE['STATUS_SUCCESS']
        # Unknown operation: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_end_x_behavior_request(self, operation, behavior):
        '''
        Handle seg6local End.X behavior
        '''
        # Extract params from request
        segment = behavior.segment
        interface = behavior.interface
        nexthop = behavior.nexthop
        table = behavior.table
        metric = behavior.metric
        # Check optional params
        #
        # Table is a optional parameter
        # -1 is the default value that means that no table has
        # been provided
        table = table if table != -1 else None
        # Metric is a optional parameter
        # -1 is the default value that means that no metric has
        # been provided
        metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'change':
            LOGGER.info('Operation %s is not yet implemented\n', operation)
            return STATUS_CODE['STATUS_OPERATION_NOT_SUPPORTED']
        if operation == 'del':
            # The operation is a "delete"
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            # The operation is a "get"
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add']:
            # The operation is a "add"
            #
            # Build the command to add the behavior
            cmd = ('sr localsid address %s behavior end.x %s %s'
                   % (segment, interface, nexthop))
            # Append the table to the command
            if table is not None:
                cmd += ' fib-table %s' % table
            # Send the command to VPP
            # This command returns a empty string in case of success
            # The decode() function is used to convert the response to a
            # string
            LOGGER.debug('Sending command to VPP: %s', cmd)
            res = self.exec_vpp_cmd(cmd).decode()
            if res != '':
                # The operation failed
                logging.error('VPP returned an error: %s', res)
                return STATUS_CODE['STATUS_INTERNAL_ERROR']
            # The behavior has been processed, create the response
            LOGGER.debug('Send response: OK')
            return STATUS_CODE['STATUS_SUCCESS']
        # Unknown operation: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_end_t_behavior_request(self, operation, behavior):
        """Handle seg6local End.T behavior"""

        # Extract params from request
        segment = behavior.segment
        lookup_table = behavior.lookup_table
        table = behavior.table
        metric = behavior.metric
        # Check optional params
        #
        # Table is a optional parameter
        # -1 is the default value that means that no table has
        # been provided
        table = table if table != -1 else None
        # Metric is a optional parameter
        # -1 is the default value that means that no metric has
        # been provided
        metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'change':
            LOGGER.info('Operation %s is not yet implemented\n', operation)
            return STATUS_CODE['STATUS_OPERATION_NOT_SUPPORTED']
        if operation == 'del':
            # The operation is a "delete"
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            # The operation is a "get"
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add']:
            # The operation is a "add"
            #
            # Build the command to add the behavior
            cmd = ('sr localsid address %s behavior end.t %s'
                   % (segment, lookup_table))
            # Append the table to the command
            if table is not None:
                cmd += ' fib-table %s' % table
            # Send the command to VPP
            # This command returns a empty string in case of success
            # The decode() function is used to convert the response to a
            # string
            LOGGER.debug('Sending command to VPP: %s', cmd)
            res = self.exec_vpp_cmd(cmd).decode()
            if res != '':
                # The operation failed
                logging.error('VPP returned an error: %s', res)
                return STATUS_CODE['STATUS_INTERNAL_ERROR']
            # The behavior has been processed, create the response
            LOGGER.debug('Send response: OK')
            return STATUS_CODE['STATUS_SUCCESS']
        # Unknown operation: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_end_dx2_behavior_request(self, operation, behavior):
        """Handle seg6local End.DX2 behavior"""

        # Extract params from request
        segment = behavior.segment
        interface = behavior.interface
        table = behavior.table
        metric = behavior.metric
        # Check optional params
        #
        # Table is a optional parameter
        # -1 is the default value that means that no table has
        # been provided
        table = table if table != -1 else None
        # Metric is a optional parameter
        # -1 is the default value that means that no metric has
        # been provided
        metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'change':
            LOGGER.info('Operation %s is not yet implemented\n', operation)
            return STATUS_CODE['STATUS_OPERATION_NOT_SUPPORTED']
        if operation == 'del':
            # The operation is a "delete"
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            # The operation is a "get"
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add']:
            # The operation is a "add"
            #
            # Build the command to add the behavior
            cmd = ('sr localsid address %s behavior end.dx2 %s'
                   % (segment, interface))
            # Append the table to the command
            if table is not None:
                cmd += ' fib-table %s' % table
            # Send the command to VPP
            # This command returns a empty string in case of success
            # The decode() function is used to convert the response to a
            # string
            LOGGER.debug('Sending command to VPP: %s', cmd)
            res = self.exec_vpp_cmd(cmd).decode()
            if res != '':
                # The operation failed
                logging.error('VPP returned an error: %s', res)
                return STATUS_CODE['STATUS_INTERNAL_ERROR']
            # The behavior has been processed, create the response
            LOGGER.debug('Send response: OK')
            return STATUS_CODE['STATUS_SUCCESS']
        # Unknown operation: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_end_dx6_behavior_request(self, operation, behavior):
        """Handle seg6local End.DX6 behavior"""

        # Extract params from request
        segment = behavior.segment
        interface = behavior.interface
        nexthop = behavior.nexthop
        table = behavior.table
        metric = behavior.metric
        # Check optional params
        #
        # Table is a optional parameter
        # -1 is the default value that means that no table has
        # been provided
        table = table if table != -1 else None
        # Metric is a optional parameter
        # -1 is the default value that means that no metric has
        # been provided
        metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'change':
            LOGGER.info('Operation %s is not yet implemented\n', operation)
            return STATUS_CODE['STATUS_OPERATION_NOT_SUPPORTED']
        if operation == 'del':
            # The operation is a "delete"
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            # The operation is a "get"
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add']:
            # The operation is a "add"
            #
            # Build the command to add the behavior
            cmd = ('sr localsid address %s behavior end.dx6 %s %s'
                   % (segment, interface, nexthop))
            # Append the table to the command
            if table is not None:
                cmd += ' fib-table %s' % table
            # Send the command to VPP
            # This command returns a empty string in case of success
            # The decode() function is used to convert the response to a
            # string
            LOGGER.debug('Sending command to VPP: %s', cmd)
            res = self.exec_vpp_cmd(cmd).decode()
            if res != '':
                # The operation failed
                logging.error('VPP returned an error: %s', res)
                return STATUS_CODE['STATUS_INTERNAL_ERROR']
            # The behavior has been processed, create the response
            LOGGER.debug('Send response: OK')
            return STATUS_CODE['STATUS_SUCCESS']
        # Unknown operation: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_end_dx4_behavior_request(self, operation, behavior):
        """Handle seg6local End.DX4 behavior"""

        # Extract params from request
        segment = behavior.segment
        interface = behavior.interface
        nexthop = behavior.nexthop
        table = behavior.table
        metric = behavior.metric
        # Check optional params
        #
        # Table is a optional parameter
        # -1 is the default value that means that no table has
        # been provided
        table = table if table != -1 else None
        # Metric is a optional parameter
        # -1 is the default value that means that no metric has
        # been provided
        metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'change':
            LOGGER.info('Operation %s is not yet implemented\n', operation)
            return STATUS_CODE['STATUS_OPERATION_NOT_SUPPORTED']
        if operation == 'del':
            # The operation is a "delete"
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            # The operation is a "get"
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add']:
            # The operation is a "add"
            #
            # Build the command to add the behavior
            cmd = ('sr localsid address %s behavior end.dx4 %s %s'
                   % (segment, interface, nexthop))
            # Append the table to the command
            if table is not None:
                cmd += ' fib-table %s' % table
            # Send the command to VPP
            # This command returns a empty string in case of success
            # The decode() function is used to convert the response to a
            # string
            LOGGER.debug('Sending command to VPP: %s', cmd)
            res = self.exec_vpp_cmd(cmd).decode()
            if res != '':
                # The operation failed
                logging.error('VPP returned an error: %s', res)
                return STATUS_CODE['STATUS_INTERNAL_ERROR']
            # The behavior has been processed, create the response
            LOGGER.debug('Send response: OK')
            return STATUS_CODE['STATUS_SUCCESS']
        # Unknown operation: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_end_dt6_behavior_request(self, operation, behavior):
        """Handle seg6local End.DT6 behavior"""

        # Extract params from request
        segment = behavior.segment
        lookup_table = behavior.lookup_table
        table = behavior.table
        metric = behavior.metric
        # Check optional params
        #
        # Table is a optional parameter
        # -1 is the default value that means that no table has
        # been provided
        table = table if table != -1 else None
        # Metric is a optional parameter
        # -1 is the default value that means that no metric has
        # been provided
        metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'change':
            LOGGER.info('Operation %s is not yet implemented\n', operation)
            return STATUS_CODE['STATUS_OPERATION_NOT_SUPPORTED']
        if operation == 'del':
            # The operation is a "delete"
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            # The operation is a "get"
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add']:
            # The operation is a "add"
            #
            # Build the command to add the behavior
            cmd = ('sr localsid address %s behavior end.dt6 %s'
                   % (segment, lookup_table))
            # Append the table to the command
            if table is not None:
                cmd += ' fib-table %s' % table
            # Send the command to VPP
            # This command returns a empty string in case of success
            # The decode() function is used to convert the response to a
            # string
            LOGGER.debug('Sending command to VPP: %s', cmd)
            res = self.exec_vpp_cmd(cmd).decode()
            if res != '':
                # The operation failed
                logging.error('VPP returned an error: %s', res)
                return STATUS_CODE['STATUS_INTERNAL_ERROR']
            # The behavior has been processed, create the response
            LOGGER.debug('Send response: OK')
            return STATUS_CODE['STATUS_SUCCESS']
        # Unknown operation: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_end_dt4_behavior_request(self, operation, behavior):
        """Handle seg6local End.DT4 behavior"""

        # Extract params from request
        segment = behavior.segment
        lookup_table = behavior.lookup_table
        table = behavior.table
        metric = behavior.metric
        # Check optional params
        #
        # Table is a optional parameter
        # -1 is the default value that means that no table has
        # been provided
        table = table if table != -1 else None
        # Metric is a optional parameter
        # -1 is the default value that means that no metric has
        # been provided
        metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'change':
            LOGGER.info('Operation %s is not yet implemented\n', operation)
            return STATUS_CODE['STATUS_OPERATION_NOT_SUPPORTED']
        if operation == 'del':
            # The operation is a "delete"
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            # The operation is a "get"
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add']:
            # The operation is a "add"
            #
            # Build the command to add the behavior
            cmd = ('sr localsid address %s behavior end.dt4 %s'
                   % (segment, lookup_table))
            # Append the table to the command
            if table is not None:
                cmd += ' fib-table %s' % table
            # Send the command to VPP
            # This command returns a empty string in case of success
            # The decode() function is used to convert the response to a
            # string
            LOGGER.debug('Sending command to VPP: %s', cmd)
            res = self.exec_vpp_cmd(cmd).decode()
            if res != '':
                # The operation failed
                logging.error('VPP returned an error: %s', res)
                return STATUS_CODE['STATUS_INTERNAL_ERROR']
            # The behavior has been processed, create the response
            LOGGER.debug('Send response: OK')
            return STATUS_CODE['STATUS_SUCCESS']
        # Unknown operation: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_end_b6_behavior_request(self, operation, behavior):
        """Handle seg6local End.B6 behavior"""

        # # Extract params from request
        # segment = behavior.segment
        # table = behavior.table
        # metric = behavior.metric
        # # Check optional params
        # #
        # # Table is a optional parameter
        # # -1 is the default value that means that no table has
        # # been provided
        # table = table if table != -1 else None
        # # Metric is a optional parameter
        # # -1 is the default value that means that no metric has
        # # been provided
        # metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'change':
            LOGGER.info('Operation %s is not yet implemented\n', operation)
            return STATUS_CODE['STATUS_OPERATION_NOT_SUPPORTED']
        if operation == 'del':
            # The operation is a "delete"
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            # The operation is a "get"
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add']:
            # The operation is a "add" or "change"
            #
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
            # res = self.exec_vpp_cmd(cmd).decode()
            # if res != '':
            #     # The operation failed
            #     logging.error('VPP returned an error: %s' % res)
            #     return srv6_manager_pb2.SRv6ManagerReply(
            #         status=STATUS_CODE['STATUS_INTERNAL_ERROR'])
            LOGGER.info('End.B6 behavior is not yet implemented\n')
            return STATUS_CODE['STATUS_OPERATION_NOT_SUPPORTED']
        # Unknown operation: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_end_b6_encaps_behavior_request(self, operation, behavior):
        """Handle seg6local End.B6.Encaps behavior"""

        # # Extract params from request
        # segment = behavior.segment
        # table = behavior.table
        # metric = behavior.metric
        # # Check optional params
        # #
        # # Table is a optional parameter
        # # -1 is the default value that means that no table has
        # # been provided
        # table = table if table != -1 else None
        # # Metric is a optional parameter
        # # -1 is the default value that means that no metric has
        # # been provided
        # metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'del':
            # The operation is a "delete"
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            # The operation is a "get"
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add', 'change']:
            # The operation is a "add" or "change"
            #
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
            # res = self.exec_vpp_cmd(cmd).decode()
            # if res != '':
            #     # The operation failed
            #     logging.error('VPP returned an error: %s' % res)
            #     return srv6_manager_pb2.SRv6ManagerReply(
            #         status=STATUS_CODE['STATUS_INTERNAL_ERROR'])
            LOGGER.info('End.B6.Encaps behavior is not yet implemented\n')
            return STATUS_CODE['STATUS_OPERATION_NOT_SUPPORTED']
        # Unknown operation: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_un_behavior_request(self, operation, behavior):
        """Handle seg6local End behavior"""

        # # Extract params from request
        # segment = behavior.segment
        # table = behavior.table
        # metric = behavior.metric
        # # Check optional params
        # #
        # # Table is a optional parameter
        # # -1 is the default value that means that no table has
        # # been provided
        # table = table if table != -1 else None
        # # Metric is a optional parameter
        # # -1 is the default value that means that no metric has
        # # been provided
        # metric = metric if metric != -1 else None
        # Perform the operation
        if operation == 'del':
            # The operation is a "delete"
            return self.handle_srv6_behavior_del_request(behavior)
        if operation == 'get':
            # The operation is a "get"
            return self.handle_srv6_behavior_get_request(behavior)
        if operation in ['add', 'change']:
            # The operation is a "add" or "change"
            #
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
            return STATUS_CODE['STATUS_OPERATION_NOT_SUPPORTED']
        # Unknown operation: this is a bug
        LOGGER.error('BUG - Unrecognized operation: %s', operation)
        sys.exit(-1)

    def handle_srv6_behavior_del_request(self, behavior):
        """Delete a route"""

        # Extract params
        segment = behavior.segment
        table = behavior.table if behavior.table != -1 else None
        # metric = behavior.metric if behavior.metric != -1 else None
        # Build the command
        cmd = ('sr localsid del address %s' % segment)
        # Add the table
        if table is not None:
            cmd += ' fib-table %s' % table
        # Execute the command
        LOGGER.debug('Sending command to VPP: %s', cmd)
        res = self.exec_vpp_cmd(cmd).decode()
        if res != '':
            # The operation failed
            logging.error('VPP returned an error: %s', res)
            return STATUS_CODE['STATUS_INTERNAL_ERROR']
        # Return success
        return STATUS_CODE['STATUS_SUCCESS']

    def handle_srv6_behavior_get_request(self, behavior):
        # pylint checks on this method are temporary disabled
        # pylint: disable=no-self-use, unused-argument
        """Get a route"""

        LOGGER.info('get opertion not yet implemented\n')
        return STATUS_CODE['STATUS_OPERATION_NOT_SUPPORTED']

    def dispatch_srv6_behavior(self, operation, behavior):
        """Pass the request to the right handler"""

        # Get the handler
        handler = self.behavior_handlers.get(behavior.action)
        # Pass the behavior to the handler
        if handler is not None:
            return handler(operation, behavior)
        # Error
        LOGGER.error('Error: Unrecognized action: %s', behavior.action)
        return STATUS_CODE['STATUS_INVALID_ACTION']

    def handle_srv6_behavior_request(self, operation, request, context,
                                     ret_behaviors):
        # pylint: disable=unused-argument
        """Handler for SRv6 behaviors"""
        LOGGER.debug('config received:\n%s', request)
        # Let's process the request
        for behavior in request.behaviors:
            if operation == 'del':
                res = self.handle_srv6_behavior_del_request(behavior)
                return res
            if operation == 'get':
                res = self.handle_srv6_behavior_get_request(behavior)
                return res
            # Pass the request to the right handler
            res = self.dispatch_srv6_behavior(operation, behavior)
            if res != STATUS_CODE['STATUS_SUCCESS']:
                return res
        # and create the response
        LOGGER.debug('Send response: OK')
        return STATUS_CODE['STATUS_SUCCESS']
