#!/usr/bin/python

##############################################################################################
# Copyright (C) 2020 Carmine Scarpitta - (Consortium GARR and University of Rome 'Tor Vergata')
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
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Example showing the removal of a SRv6 tunnel
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


# Imports
import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Folder containing this script
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

# Folder containing the files auto-generated from proto files
PROTO_PATH = os.path.join(BASE_PATH, '../protos/gen-py/')

# Folder containing the controller
CONTROLLER_PATH = os.path.join(BASE_PATH, '../controller/')

# Environment variables have priority over hardcoded paths
# If an environment variable is set, we must use it instead of
# the hardcoded constant

# PROTO_PATH
if os.getenv('PROTO_PATH') is not None:
    # Check if the PROTO_PATH variable is set
    if os.getenv('PROTO_PATH') == '':
        print('Error : Set PROTO_PATH variable in .env\n')
        sys.exit(-2)
    # Check if the PROTO_PATH variable points to an existing folder
    if not os.path.exists(PROTO_PATH):
        print('Error : PROTO_PATH variable in '
              '.env points to a non existing folder')
        sys.exit(-2)
    # PROTO_PATH in .env is correct. We use it.
    PROTO_PATH = os.getenv('PROTO_PATH')
else:
    # PROTO_PATH in .env is not set, we use the hardcoded path
    #
    # Check if the PROTO_PATH variable is set
    if PROTO_PATH == '':
        print('Error : Set PROTO_PATH variable in .env or %s' % sys.argv[0])
        sys.exit(-2)
    # Check if the PROTO_PATH variable points to an existing folder
    if not os.path.exists(PROTO_PATH):
        print('Error : PROTO_PATH variable in '
              '%s points to a non existing folder' % sys.argv[0])
        print('Error : Set PROTO_PATH variable in .env or %s\n' % sys.argv[0])
        sys.exit(-2)

# CONTROLLER_PATH
if os.getenv('CONTROLLER_PATH') is not None:
    # Check if the CONTROLLER_PATH variable is set
    if os.getenv('CONTROLLER_PATH') == '':
        print('Error : Set CONTROLLER_PATH variable in .env\n')
        sys.exit(-2)
    # Check if the CONTROLLER_PATH variable points to an existing folder
    if not os.path.exists(CONTROLLER_PATH):
        print('Error : CONTROLLER_PATH variable in '
              '.env points to a non existing folder')
        sys.exit(-2)
    # CONTROLLER_PATH in .env is correct. We use it.
    CONTROLLER_PATH = os.getenv('CONTROLLER_PATH')
else:
    # CONTROLLER_PATH in .env is not set, we use the hardcoded path
    #
    # Check if the CONTROLLER_PATH variable is set
    if CONTROLLER_PATH == '':
        print('Error : Set CONTROLLER_PATH variable in .env or %s' % sys.argv[0])
        sys.exit(-2)
    # Check if the CONTROLLER_PATH variable points to an existing folder
    if not os.path.exists(CONTROLLER_PATH):
        print('Error : CONTROLLER_PATH variable in '
              '%s points to a non existing folder' % sys.argv[0])
        print('Error : Set CONTROLLER_PATH variable in .env or %s\n' % sys.argv[0])
        sys.exit(-2)

# Proto dependencies
sys.path.append(PROTO_PATH)
import srv6_manager_pb2

# Controller dependencies
sys.path.append(CONTROLLER_PATH)
from srv6_controller import handle_srv6_path, handle_srv6_behavior
from srv6_controller import get_grpc_session


# Global variables definition
#
#
# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)
#
# Port of the gRPC server
GRPC_PORT = 12345


def remove_tunnel_r1r4r8():
    # +--------------------------------------------------------------------+
    # |          Remove a bidirectional tunnel between h11 and h83         |
    # |              passing through router r4 (r1---r4---r8)              |
    # +--------------------------------------------------------------------+
    logger.info('*** Attempting to remove tunnel r1---r4---r8')
    # IP addresses
    r1 = 'fcff:1::1'
    r8 = 'fcff:8::1'
    # Open gRPC channels
    with get_grpc_session(r1, GRPC_PORT) as r1_chan, \
            get_grpc_session(r8, GRPC_PORT) as r8_chan:
        # +---------------------------------------------------------------+
        # |         Remove tunnel from r1 to r8 for fd00:0:83::/64        |
        # +---------------------------------------------------------------+
        logger.info('******* Removing tunnel from r1 to r8 for fd00:0:83::/64')
        #
        # Decap route on r8
        # on r8: ip -6 route del fcff:8::100 dev r8-h83 metric 200
        logger.info('*********** Removing decap route')
        res = handle_srv6_behavior(
            op='del',
            channel=r8_chan,
            segment='fcff:8::100',
            device='r8-h83',
            metric=100
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Decap route removed successfully')
        else:
            logger.error('*********** Error while removing decap route')
        #
        # Encap route on r1
        # on r1: ip -6 route del fd00:0:83::/64 dev r1-h11 metric 200
        logger.info('*********** Removing encap route')
        res = handle_srv6_path(
            op='del',
            channel=r1_chan,
            destination='fd00:0:83::/64',
            device='r1-h11',
            metric=100
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Encap route removed successfully')
        else:
            logger.error('*********** Error while removing encap route')
        #
        #
        # +---------------------------------------------------------------+
        # |         Remove tunnel from r8 to r1 for fd00:0:11::/64        |
        # +---------------------------------------------------------------+
        logger.info('******* Removing tunnel from r8 to r1 for fd00:0:11::/64')
        #
        # Decap route on r1
        # on r1: ip -6 route del fcff:1::100 dev r1-h11 metric 200
        logger.info('*********** Removing decap route')
        res = handle_srv6_behavior(
            op='del',
            channel=r1_chan,
            segment='fcff:1::100',
            device='r1-h11',
            metric=100
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Decap route removed successfully')
        else:
            logger.error('*********** Error while removing decap route')
        #
        # Encap route on r8
        # on r8: ip -6 route del fd00:0:11::/64 dev r8-h83 metric 200
        logger.info('*********** Removing encap route')
        res = handle_srv6_path(
            op='del',
            channel=r8_chan,
            destination='fd00:0:11::/64',
            device='r8-h83',
            metric=100
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Encap route removed successfully')
        else:
            logger.error('*********** Error while removing encap route')
        #
        #
        # +---------------------------------------------------------------+
        # |                             Done                              |
        # +---------------------------------------------------------------+
        print()


if __name__ == '__main__':
    # Run example
    remove_tunnel_r1r4r8()