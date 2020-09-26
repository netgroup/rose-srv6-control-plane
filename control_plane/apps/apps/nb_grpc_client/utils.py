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
# Utilities functions used by gRPC client
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
Utilities functions used by gRPC client.
'''

# Proto dependencies
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


STATUS_CODE_TO_DESC = {
    STATUS_SUCCESS: 'Operation completed successfully',
    STATUS_OPERATION_NOT_SUPPORTED: 'Error: Operation not supported',
    STATUS_BAD_REQUEST: 'Error: Bad request',
    STATUS_INTERNAL_ERROR: 'Error: Internal error',
    STATUS_INVALID_GRPC_REQUEST: 'Error: Invalid gRPC request',
    STATUS_FILE_EXISTS: 'Error: Entity already exists',
    STATUS_NO_SUCH_PROCESS: 'Error: Entity not found',
    STATUS_INVALID_ACTION: 'Error: Invalid action',
    STATUS_GRPC_SERVICE_UNAVAILABLE: 'Error: Unreachable grPC server',
    STATUS_GRPC_UNAUTHORIZED: 'Error: Unauthorized',
    STATUS_NOT_CONFIGURED: 'Error: Not configured',
    STATUS_ALREADY_CONFIGURED: 'Error: Already configured',
    STATUS_NO_SUCH_DEVICE: 'Error: Device not found',
}


class InvalidArgumentError(Exception):
    '''
    Invalid argument.
    '''


def raise_exception_on_error(error_code):   # TODO exeptions more specific
    if error_code == STATUS_SUCCESS:
        return
    if error_code == STATUS_OPERATION_NOT_SUPPORTED:
        raise InvalidArgumentError
    if error_code == STATUS_BAD_REQUEST:
        raise InvalidArgumentError
    if error_code == STATUS_INTERNAL_ERROR:
        raise InvalidArgumentError
    if error_code == STATUS_INVALID_GRPC_REQUEST:
        raise InvalidArgumentError
    if error_code == STATUS_FILE_EXISTS:
        raise InvalidArgumentError
    if error_code == STATUS_NO_SUCH_PROCESS:
        raise InvalidArgumentError
    if error_code == STATUS_INVALID_ACTION:
        raise InvalidArgumentError
    if error_code == STATUS_GRPC_SERVICE_UNAVAILABLE:
        raise InvalidArgumentError
    if error_code == STATUS_GRPC_UNAUTHORIZED:
        raise InvalidArgumentError
    if error_code == STATUS_NOT_CONFIGURED:
        raise InvalidArgumentError
    if error_code == STATUS_ALREADY_CONFIGURED:
        raise InvalidArgumentError
    if error_code == STATUS_NO_SUCH_DEVICE:
        raise InvalidArgumentError
    