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
# File containing several constants used in different scripts
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
This file contains several constants used in different scripts
'''

# Proto dependencies
from srv6_manager_pb2 import FwdEngine  # pylint: disable=no-name-in-module
from commons_pb2 import (STATUS_SUCCESS,
                         STATUS_OPERATION_NOT_SUPPORTED,
                         STATUS_BAD_REQUEST,
                         STATUS_INTERNAL_ERROR,
                         STATUS_INVALID_GRPC_REQUEST,
                         STATUS_FILE_EXISTS,
                         STATUS_NO_SUCH_PROCESS,
                         STATUS_INVALID_ACTION,
                         STATUS_GRPC_SERVICE_UNAVAILABLE,
                         STATUS_GRPC_UNAUTHORIZED,
                         STATUS_NOT_CONFIGURED,
                         STATUS_ALREADY_CONFIGURED,
                         STATUS_NO_SUCH_DEVICE)

# Forwarding Engine
FWD_ENGINE = {
    'vpp': FwdEngine.Value('VPP'),
    'linux': FwdEngine.Value('LINUX'),
    'p4': FwdEngine.Value('P4'),
}  # pylint: disable=no-member

# Status codes
STATUS_CODE = {
    'STATUS_SUCCESS': STATUS_SUCCESS,
    'STATUS_OPERATION_NOT_SUPPORTED': STATUS_OPERATION_NOT_SUPPORTED,
    'STATUS_BAD_REQUEST': STATUS_BAD_REQUEST,
    'STATUS_INTERNAL_ERROR': STATUS_INTERNAL_ERROR,
    'STATUS_INVALID_GRPC_REQUEST': STATUS_INVALID_GRPC_REQUEST,
    'STATUS_FILE_EXISTS': STATUS_FILE_EXISTS,
    'STATUS_NO_SUCH_PROCESS': STATUS_NO_SUCH_PROCESS,
    'STATUS_INVALID_ACTION': STATUS_INVALID_ACTION,
    'STATUS_GRPC_SERVICE_UNAVAILABLE': STATUS_GRPC_SERVICE_UNAVAILABLE,
    'STATUS_GRPC_UNAUTHORIZED': STATUS_GRPC_UNAUTHORIZED,
    'STATUS_NOT_CONFIGURED': STATUS_NOT_CONFIGURED,
    'STATUS_ALREADY_CONFIGURED': STATUS_ALREADY_CONFIGURED,
    'STATUS_NO_SUCH_DEVICE': STATUS_NO_SUCH_DEVICE,
}

# Status description
STATUS_MSG = {
    'STATUS_SUCCESS': 'Operation completed successfully',
    'STATUS_OPERATION_NOT_SUPPORTED': 'Operation not supported',
    'STATUS_BAD_REQUEST': 'Bad request',
    'STATUS_INTERNAL_ERROR': 'Internal error',
    'STATUS_INVALID_GRPC_REQUEST': 'Invalid gRPC request',
    'STATUS_FILE_EXISTS': 'Entity already exists',
    'STATUS_NO_SUCH_PROCESS': 'Entity not found',
    'STATUS_INVALID_ACTION': 'Invalid action',
    'STATUS_GRPC_SERVICE_UNAVAILABLE': 'Unreachable grPC server',
    'STATUS_GRPC_UNAUTHORIZED': 'Unauthorized',
    'STATUS_NOT_CONFIGURED': 'Not configured',
    'STATUS_ALREADY_CONFIGURED': 'Already configured',
    'STATUS_NO_SUCH_DEVICE': 'Device not found',
}
