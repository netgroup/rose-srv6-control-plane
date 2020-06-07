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
# Example showing how it is possible to switch from a SRv6
# tunnel to another by acting on the metric parameter
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
    if not os.path.exists(os.getenv('PROTO_PATH')):
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
    if not os.path.exists(os.getenv('CONTROLLER_PATH')):
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
        print('Error : Set CONTROLLER_PATH variable in .env or %s' %
              sys.argv[0])
        sys.exit(-2)
    # Check if the CONTROLLER_PATH variable points to an existing folder
    if not os.path.exists(CONTROLLER_PATH):
        print('Error : CONTROLLER_PATH variable in '
              '%s points to a non existing folder' % sys.argv[0])
        print('Error : Set CONTROLLER_PATH variable in .env or %s\n' %
              sys.argv[0])
        sys.exit(-2)

# Proto dependencies
sys.path.append(PROTO_PATH)
import srv6_manager_pb2

# Controller dependencies
sys.path.append(CONTROLLER_PATH)
from controller import handle_srv6_path, handle_srv6_behavior
from controller import get_grpc_session


# Global variables definition
#
#
# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)
#
# Port of the gRPC server
GRPC_PORT = 12345


def shift_path():
    # +--------------------------------------------------------------------+
    # |         Switch from r1---r7---r8 path to r1---r4---r8 path         |
    # |                     by exchanging the metrics                      |
    # +--------------------------------------------------------------------+
    logger.info(
        '*** Attempting to change path from r1---r7---r8 to r1---r4---r8')
    # IP addresses
    r1 = 'fcff:1::1'
    r8 = 'fcff:8::1'
    # Open gRPC channels
    with get_grpc_session(r1, GRPC_PORT) as r1_chan, \
            get_grpc_session(r8, GRPC_PORT) as r8_chan:
        # +---------------------------------------------------------------+
        # |              Decreasing the metric value of the               |
        # |               r4 route to an intermediate value               |
        # +---------------------------------------------------------------+
        logger.info('******* Decreasing the metric value of '
                    'the r4 route to an intermediate value')
        #
        # Encap route on r1
        # on r1: ip -6 route add fd00:0:83::/64 encap seg6 mode encap segs
        #        fcff:4::1,fcff:8:100 dev r1-h11 metric 99
        logger.info('*********** Creating encap route on r1')
        res = handle_srv6_path(
            op='add',
            channel=r1_chan,
            destination='fd00:0:83::/64',
            segments=['fcff:4::1', 'fcff:8::100'],
            device='r1-h11',
            metric=99
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Encap route created successfully')
        else:
            logger.error('*********** Error while creating encap route')
        #
        # Decap route on r8
        # on r8: ip -6 route add fcff:8::100 encap seg6local action End.DT6
        #        table 254 dev r8-h83 metric 99
        logger.info('*********** Creating decap route on r8')
        res = handle_srv6_behavior(
            op='add',
            channel=r8_chan,
            segment='fcff:8::100',
            action='End.DT6',
            lookup_table=254,
            device='r8-h83',
            metric=99
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Decap route created successfully')
        else:
            logger.error('*********** Error while creating decap route')
        #
        # Encap route on r8
        # on r8: ip -6 route add fd00:0:11::/64 encap seg6 mode encap segs
        #        fcff:4::1,fcff:1:100 dev r8-h83 metric 99
        logger.info('*********** Creating encap route on r8')
        res = handle_srv6_path(
            op='add',
            channel=r8_chan,
            destination='fd00:0:11::/64',
            segments=['fcff:4::1', 'fcff:1::100'],
            device='r8-h83',
            metric=99
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Encap route created successfully')
        else:
            logger.error('*********** Error while creating encap route')
        #
        # Decap route on r1
        # on r1: ip -6 route add fcff:1::100 encap seg6local action End.DT6
        #        table 254 dev r1-h11 metric 99
        logger.info('*********** Creating decap route on r1')
        res = handle_srv6_behavior(
            op='add',
            channel=r1_chan,
            segment='fcff:1::100',
            action='End.DT6',
            lookup_table=254,
            device='r1-h11',
            metric=99
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Decap route created successfully')
        else:
            logger.error('*********** Error while creating decap route')
        #
        #
        # +---------------------------------------------------------------+
        # |                   Removing old route via r4                   |
        # +---------------------------------------------------------------+
        logger.info('*** Attempting to remove tunnel r1---r4---r8')
        #
        # Encap route on r1
        # on r1: ip -6 route del fd00:0:83::/64 encap seg6 mode encap segs
        #        fcff:4::1,fcff:8:100 dev r1-h11 metric 200
        logger.info('*********** Removing encap route on r1')
        res = handle_srv6_path(
            op='del',
            channel=r1_chan,
            destination='fd00:0:83::/64',
            device='r1-h11',
            metric=200
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Encap route removed successfully')
        else:
            logger.error('*********** Error while removing encap route')
        #
        # Decap route on r8
        # on r8: ip -6 route del fcff:8::100 encap seg6local action End.DT6
        #        table 254 dev r8-h83 metric 200
        logger.info('*********** Removing decap route on r8')
        res = handle_srv6_behavior(
            op='del',
            channel=r8_chan,
            segment='fcff:8::100',
            device='r8-h83',
            metric=200
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Decap route removed successfully')
        else:
            logger.error('*********** Error while removing decap route')
        #
        # Encap route on r8
        # on r8: ip -6 route del fd00:0:11::/64 encap seg6 mode encap segs
        #        fcff:4::1,fcff:1:100 dev r8-h83 metric 200
        logger.info('*********** Removing encap route on r8')
        res = handle_srv6_path(
            op='del',
            channel=r8_chan,
            destination='fd00:0:11::/64',
            device='r8-h83',
            metric=200
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Encap route removed successfully')
        else:
            logger.error('*********** Error while removing encap route')
        #
        # Decap route on r1
        # on r1: ip -6 route del fcff:1::100 encap seg6local action End.DT6
        #        table 254 dev r1-h11 metric 200
        logger.info('*********** Removing decap route on r1')
        res = handle_srv6_behavior(
            op='del',
            channel=r1_chan,
            segment='fcff:1::100',
            device='r1-h11',
            metric=200
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Decap route removed successfully')
        else:
            logger.error('*********** Error while removing decap route')
        #
        #
        # +----------------------------------------------------------------+
        # |           Increasing the metric value of the r7 path           |
        # +----------------------------------------------------------------+
        logger.info(
            '*** Increasing the metric value of the tunnel r1---r7---r8')
        #
        # Encap route on r1
        # on r1: ip -6 route add fd00:0:83::/64 encap seg6 mode encap segs
        #        fcff:7::1,fcff:8:100 dev r1-h11 metric 200
        logger.info('*********** Creating encap route on r1')
        res = handle_srv6_path(
            op='add',
            channel=r1_chan,
            destination='fd00:0:83::/64',
            segments=['fcff:7::1', 'fcff:8::100'],
            device='r1-h11',
            metric=200
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Encap route created successfully')
        else:
            logger.error('*********** Error while creating encap route')
        #
        # Decap route on r8
        # on r8: ip -6 route add fcff:8::100 encap seg6local action End.DT6
        #        table 254 dev r8-h83 metric 200
        logger.info('*********** Creating decap route on r8')
        res = handle_srv6_behavior(
            op='add',
            channel=r8_chan,
            segment='fcff:8::100',
            action='End.DT6',
            lookup_table=254,
            device='r8-h83',
            metric=200
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Decap route created successfully')
        else:
            logger.error('*********** Error while creating decap route')
        #
        # Encap route on r8
        # on r8: ip -6 route add fd00:0:11::/64 encap seg6 mode encap segs
        #        fcff:7::1,fcff:1:100 dev r8-h83 metric 200
        logger.info('*********** Creating encap route on r8')
        res = handle_srv6_path(
            op='add',
            channel=r8_chan,
            destination='fd00:0:11::/64',
            segments=['fcff:7::1', 'fcff:1::100'],
            device='r8-h83',
            metric=200
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Encap route created successfully')
        else:
            logger.error('*********** Error while creating encap route')
        #
        # Decap route on r1
        # on r1: ip -6 route add fcff:1::100 encap seg6local action End.DT6
        #        table 254 dev r1-h11 metric 200
        logger.info('*********** Creating decap route on r1')
        res = handle_srv6_behavior(
            op='add',
            channel=r1_chan,
            segment='fcff:1::100',
            action='End.DT6',
            lookup_table=254,
            device='r1-h11',
            metric=200
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Decap route created successfully')
        else:
            logger.error('*********** Error while creating decap route')
        #
        #
        # +---------------------------------------------------------------+
        # |                   Removing old route via r7                   |
        # +---------------------------------------------------------------+
        logger.info('*** Attempting to remove tunnel r1---r7---r8')
        # Encap route on r1
        # on r1: ip -6 route del fd00:0:83::/64 encap seg6 mode encap segs
        #        fcff:7::1,fcff:8:100 dev r1-h11 metric 100
        logger.info('*********** Removing encap route on r1')
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
        # Decap route on r8
        # on r8: ip -6 route del fcff:8::100 encap seg6local action End.DT6
        #        table 254 dev r8-h83 metric 100
        logger.info('*********** Removing decap route on r8')
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
        # Encap route on r8
        # on r8: ip -6 route del fd00:0:11::/64 encap seg6 mode encap segs
        #        fcff:7::1,fcff:1:100 dev r8-h83 metric 100
        logger.info('*********** Removing encap route on r8')
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
        # Decap route on r1
        # on r1: ip -6 route del fcff:1::100 encap seg6local action End.DT6
        #        table 254 dev r1-h11 metric 100
        logger.info('*********** Removing decap route on r1')
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
        #
        # +---------------------------------------------------------------+
        # |      Assign to r4 route a definitive value of the metric      |
        # +---------------------------------------------------------------+
        logger.info('*** Assign to r4 route a definitive value of the metric')
        #
        # Encap route on r1
        # on r1: ip -6 route add fd00:0:83::/64 encap seg6 mode encap segs
        #        fcff:4::1,fcff:8:100 dev r1-h11 metric 100
        logger.info('*********** Creating encap route on r1')
        res = handle_srv6_path(
            op='add',
            channel=r1_chan,
            destination='fd00:0:83::/64',
            segments=['fcff:4::1', 'fcff:8::100'],
            device='r1-h11',
            metric=100
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Encap route created successfully')
        else:
            logger.error('*********** Error while creating encap route')
        #
        # Decap route on r8
        # on r8: ip -6 route add fcff:8::100 encap seg6local action End.DT6
        #        table 254 dev r8-h83 metric 100
        logger.info('*********** Creating decap route on r8')
        res = handle_srv6_behavior(
            op='add',
            channel=r8_chan,
            segment='fcff:8::100',
            action='End.DT6',
            lookup_table=254,
            device='r8-h83',
            metric=100
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Decap route created successfully')
        else:
            logger.error('*********** Error while creating decap route')
        #
        # Encap route on r8
        # on r8: ip -6 route add fd00:0:11::/64 encap seg6 mode encap segs
        #        fcff:4::1,fcff:1:100 dev r8-h83 metric 100
        logger.info('*********** Creating encap route on r8')
        res = handle_srv6_path(
            op='add',
            channel=r8_chan,
            destination='fd00:0:11::/64',
            segments=['fcff:4::1', 'fcff:1::100'],
            device='r8-h83',
            metric=100
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Encap route created successfully')
        else:
            logger.error('*********** Error while creating encap route')
        #
        # Decap route on r1
        # on r1: ip -6 route add fcff:1::100 encap seg6local action End.DT6
        #        table 254 dev r1-h11 metric 100
        logger.info('*********** Creating decap route on r1')
        res = handle_srv6_behavior(
            op='add',
            channel=r1_chan,
            segment='fcff:1::100',
            action='End.DT6',
            lookup_table=254,
            device='r1-h11',
            metric=100
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Decap route created successfully')
        else:
            logger.error('*********** Error while creating decap route')
        #
        #
        # +---------------------------------------------------------------+
        # | Delete the r4 route with the intermediate value of the metric |
        # +---------------------------------------------------------------+
        logger.info('*** Delete the r4 route with the intermediate value of '
                    'the metric')
        #
        # Encap route on r1
        # on r1: ip -6 route del fd00:0:83::/64 encap seg6 mode encap segs
        #        fcff:4::1,fcff:8:100 dev r1-h11 metric 99
        logger.info('*********** Removing encap route on r1')
        res = handle_srv6_path(
            op='del',
            channel=r1_chan,
            destination='fd00:0:83::/64',
            device='r1-h11',
            metric=99
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Encap route removed successfully')
        else:
            logger.error('*********** Error while removing encap route')
        #
        # Decap route on r8
        # on r8: ip -6 route del fcff:8::100 encap seg6local action End.DT6
        #        table 254 dev r8-h83 metric 99
        logger.info('*********** Removing decap route on r8')
        res = handle_srv6_behavior(
            op='del',
            channel=r8_chan,
            segment='fcff:8::100',
            device='r8-h83',
            metric=99
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Decap route removed successfully')
        else:
            logger.error('*********** Error while removing decap route')
        #
        # Encap route on r8
        # on r8: ip -6 route del fd00:0:11::/64 encap seg6 mode encap segs
        #        fcff:4::1,fcff:1:100 dev r8-h83 metric 99
        logger.info('*********** Removing encap route on r8')
        res = handle_srv6_path(
            op='del',
            channel=r8_chan,
            destination='fd00:0:11::/64',
            device='r8-h83',
            metric=99
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Encap route removed successfully')
        else:
            logger.error('*********** Error while removing encap route')
        #
        # Decap route on r1
        # on r1: ip -6 route del fcff:1::100 encap seg6local action End.DT6
        #        table 254 dev r1-h11 metric 99
        logger.info('*********** Removing decap route on r1')
        res = handle_srv6_behavior(
            op='del',
            channel=r1_chan,
            segment='fcff:1::100',
            device='r1-h11',
            metric=99
        )
        if res == srv6_manager_pb2.StatusCode.STATUS_SUCCESS:
            logger.info('*********** Decap route removed successfully')
        else:
            logger.error('*********** Error while removing decap route')
        #
        #
        # +---------------------------------------------------------------+
        # |                             Done                              |
        # +---------------------------------------------------------------+
        print()


if __name__ == '__main__':
    # Run example
    shift_path()
