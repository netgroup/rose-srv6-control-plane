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
# Utils for Northbound gRPC server
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
This module contains a collection of utilities used by Northbound gRPC server.
'''

# Proto dependencies
import commons_pb2
import nb_commons_pb2


sb_status_to_nb_status = {
    commons_pb2.STATUS_SUCCESS: nb_commons_pb2.STATUS_SUCCESS,
    commons_pb2.STATUS_OPERATION_NOT_SUPPORTED: nb_commons_pb2.STATUS_OPERATION_NOT_SUPPORTED,
    commons_pb2.STATUS_BAD_REQUEST: nb_commons_pb2.STATUS_BAD_REQUEST,
    commons_pb2.STATUS_INTERNAL_ERROR: nb_commons_pb2.STATUS_INTERNAL_ERROR,
    commons_pb2.STATUS_INVALID_GRPC_REQUEST: nb_commons_pb2.STATUS_INVALID_GRPC_REQUEST,
    commons_pb2.STATUS_FILE_EXISTS: nb_commons_pb2.STATUS_FILE_EXISTS,
    commons_pb2.STATUS_NO_SUCH_PROCESS: nb_commons_pb2.STATUS_NO_SUCH_PROCESS,
    commons_pb2.STATUS_INVALID_ACTION: nb_commons_pb2.STATUS_INVALID_ACTION,
    commons_pb2.STATUS_GRPC_SERVICE_UNAVAILABLE: nb_commons_pb2.STATUS_GRPC_SERVICE_UNAVAILABLE,
    commons_pb2.STATUS_GRPC_UNAUTHORIZED: nb_commons_pb2.STATUS_GRPC_UNAUTHORIZED,
    commons_pb2.STATUS_NOT_CONFIGURED: nb_commons_pb2.STATUS_NOT_CONFIGURED,
    commons_pb2.STATUS_ALREADY_CONFIGURED: nb_commons_pb2.STATUS_ALREADY_CONFIGURED,
    commons_pb2.STATUS_NO_SUCH_DEVICE: nb_commons_pb2.STATUS_NO_SUCH_DEVICE}

action_to_grpc_repr = {
    'End': 'END',
    'End.X': 'END_x',
    'End.T': 'END_T',
    'End.DX4': 'END_DX4',
    'End.DX6': 'END_DX6',
    'End.DX2': 'END_DX2',
    'End.DT4': 'END_DT4',
    'End.DT6': 'END_DT6',
    'End.B6': 'END_B6',
    'End.B6.Encaps': 'END_B6_ENCAPS'
}

grpc_repr_to_action = {v: k for k, v in action_to_grpc_repr.items()}
