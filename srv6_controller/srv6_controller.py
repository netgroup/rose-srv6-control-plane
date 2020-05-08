#!/usr/bin/python

# General imports
from __future__ import absolute_import, division, print_function
from argparse import ArgumentParser
from concurrent import futures
from threading import Thread
from socket import AF_INET, AF_INET6
from six import text_type
from ipaddress import IPv4Interface, IPv6Interface
from ipaddress import AddressValueError
import grpc
import logging
import time
import json
import sys
import os

# SRv6 Manager dependencies
import srv6_manager_pb2
import srv6_manager_pb2_grpc


# Global variables definition
#
#
# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)
# Default parameters for SRv6 controller
#
# Port of the gRPC server
GRPC_PORT = 12345
# Define whether to use SSL or not for the gRPC client
SECURE = False
# SSL certificate of the root CA
CERTIFICATE = 'client_cert.pem'


# Build a grpc stub
def get_grpc_session(server_ip, server_port):
    # Get server IP
    server_ip = "ipv6:[%s]:%s" % (server_ip, server_port)
    # If secure we need to establish a channel with the secure endpoint
    if SECURE:
        if CERTIFICATE is None:
            logger.fatal('Certificate required for gRPC secure mode')
            exit(-1)
        # Open the certificate file
        with open(CERTIFICATE, 'rb') as f:
            certificate = f.read()
        # Then create the SSL credentials and establish the channel
        grpc_client_credentials = grpc.ssl_channel_credentials(certificate)
        channel = grpc.secure_channel(server_ip, grpc_client_credentials)
    else:
        channel = grpc.insecure_channel(server_ip)
    # Return the channel
    return channel


# Parser for gRPC errors
def parse_grpc_error(e):
    status_code = e.code()
    details = e.details()
    logger.error('gRPC client reported an error: %s, %s'
                 % (status_code, details))
    if grpc.StatusCode.UNAVAILABLE == status_code:
        code = srv6_manager_pb2.STATUS_GRPC_SERVICE_UNAVAILABLE
    elif grpc.StatusCode.UNAUTHENTICATED == status_code:
        code = srv6_manager_pb2.STATUS_GRPC_UNAUTHORIZED
    else:
        code = srv6_manager_pb2.STATUS_INTERNAL_ERROR
    # Return an error message
    return code


def handle_srv6_path(op, channel, destination, segments=[],
                     device='', encapmode="encap", table=-1, metric=-1):
    # Create request message
    request = srv6_manager_pb2.SRv6ManagerRequest()
    # Create a new SRv6 path request
    path_request = request.srv6_path_request
    # Create a new path
    path = path_request.paths.add()
    # Set destination
    path.destination = text_type(destination)
    # Set device
    # If the device is not specified (i.e. empty string),
    # it will be chosen by the gRPC server
    path.device = text_type(device)
    # Set table ID
    # If the table ID is not specified (i.e. table=-1),
    # the main table will be used
    path.table = int(table)
    # Set metric (i.e. preference value of the route)
    # If the metric is not specified (i.e. metric=-1),
    # the decision is left to the Linux kernel
    path.metric = int(metric)
    try:
        # Get the reference of the stub
        stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
        # Fill the request depending on the operation
        # and send the request
        if op == 'add':
            # Set encapmode
            path.encapmode = text_type(encapmode)
            if len(segments) == 0:
                logger.error('*** Missing segments for seg6 route')
                return srv6_manager_pb2.STATUS_INTERNAL_ERROR
            # Iterate on the segments and build the SID list
            for segment in segments:
                # Append the segment to the SID list
                srv6_segment = path.sr_path.add()
                srv6_segment.segment = text_type(segment)
            # Create the SRv6 path
            response = stub.Create(request)
        elif op == 'get':
            # Get the SRv6 path
            response = stub.Get(request)
        elif op == 'change':
            # Set encapmode
            path.encapmode = text_type(encapmode)
            # Iterate on the segments and build the SID list
            for segment in segments:
                # Append the segment to the SID list
                srv6_segment = path.sr_path.add()
                srv6_segment.segment = text_type(segment)
            # Update the SRv6 path
            response = stub.Update(request)
        elif op == 'del':
            # Remove the SRv6 path
            response = stub.Remove(request)
        # Get the status code of the gRPC operation
        response = response.status
    except grpc.RpcError as e:
        # An error occurred during the gRPC operation
        # Parse the error and return it
        response = parse_grpc_error(e)
    # Return the response
    return response


def handle_srv6_behavior(op, channel, segment, action='', device='',
                         table=-1, nexthop="", lookup_table=-1,
                         interface="", segments=[], metric=-1):
    # Create request message
    request = srv6_manager_pb2.SRv6ManagerRequest()
    # Create a new SRv6 behavior request
    behavior_request = request.srv6_behavior_request
    # Create a new SRv6 behavior
    behavior = behavior_request.behaviors.add()
    # Set local segment for the seg6local route
    behavior.segment = text_type(segment)
    # Set the device
    # If the device is not specified (i.e. empty string),
    # it will be chosen by the gRPC server
    behavior.device = text_type(device)
    # Set the table where the seg6local must be inserted
    # If the table ID is not specified (i.e. table=-1),
    # the main table will be used
    behavior.table = int(table)
    # Set device
    # If the device is not specified (i.e. empty string),
    # it will be chosen by the gRPC server
    behavior.device = text_type(device)
    # Set table ID
    # If the table ID is not specified (i.e. table=-1),
    # the main table will be used
    behavior.table = int(table)
    # Set metric (i.e. preference value of the route)
    # If the metric is not specified (i.e. metric=-1),
    # the decision is left to the Linux kernel
    behavior.metric = int(metric)
    try:
        # Get the reference of the stub
        stub = srv6_manager_pb2_grpc.SRv6ManagerStub(channel)
        # Fill the request depending on the operation
        # and send the request
        if op == 'add':
            if action == '':
                logger.error('*** Missing action for seg6local route')
                return srv6_manager_pb2.STATUS_INTERNAL_ERROR
            # Set the action for the seg6local route
            behavior.action = text_type(action)
            # Set the nexthop for the L3 cross-connect actions
            # (e.g. End.DX4, End.DX6)
            behavior.nexthop = text_type(nexthop)
            # Set the table for the "decap and table lookup" actions
            # (e.g. End.DT4, End.DT6)
            behavior.lookup_table = int(lookup_table)
            # Set the inteface for the L2 cross-connect actions
            # (e.g. End.DX2)
            behavior.interface = text_type(interface)
            # Set the segments for the binding SID actions
            # (e.g. End.B6, End.B6.Encaps)
            for segment in segments:
                # Create a new segment
                srv6_segment = behavior.segs.add()
                srv6_segment.segment = text_type(segment)
            # Create the SRv6 behavior
            response = stub.Create(request)
        elif op == 'get':
            # Get the SRv6 behavior
            response = stub.Get(request)
        elif op == 'change':
            # Set the action for the seg6local route
            behavior.action = text_type(action)
            # Set the nexthop for the L3 cross-connect actions
            # (e.g. End.DX4, End.DX6)
            behavior.nexthop = text_type(nexthop)
            # Set the table for the "decap and table lookup" actions
            # (e.g. End.DT4, End.DT6)
            behavior.lookup_table = int(lookup_table)
            # Set the inteface for the L2 cross-connect actions
            # (e.g. End.DX2)
            behavior.interface = text_type(interface)
            # Set the segments for the binding SID actions
            # (e.g. End.B6, End.B6.Encaps)
            for segment in segments:
                # Create a new segment
                srv6_segment = behavior.segs.add()
                srv6_segment.segment = text_type(segment)
            # Update the SRv6 behavior
            response = stub.Update(request)
        elif op == 'del':
            # Remove the SRv6 behavior
            response = stub.Remove(request)
        # Get the status code of the gRPC operation
        response = response.status
    except grpc.RpcError as e:
        # An error occurred during the gRPC operation
        # Parse the error and return it
        response = parse_grpc_error(e)
    # Return the response
    return response


def create_tunnel_r1r4r8():
    # +--------------------------------------------------------------------+
    # |          Create a bidirectional tunnel between h11 and h83         |
    # |              passing through router r4 (r1---r4---r8)              |
    # +--------------------------------------------------------------------+
    logger.info('*** Attempting to create tunnel r1---r4---r8')
    # IP addresses
    r1 = 'fcff:1::1'
    r8 = 'fcff:8::1'
    # Open gRPC channels
    with get_grpc_session(r1, GRPC_PORT) as r1_chan, \
            get_grpc_session(r8, GRPC_PORT) as r8_chan:
        # +---------------------------------------------------------------+
        # |          Set tunnel from r1 to r8 for fd00:0:83::/64          |
        # +---------------------------------------------------------------+
        logger.info('******* Set tunnel from r1 to r8 for fd00:0:83::/64')
        #
        # Encap route on r1
        # on r1: ip -6 route add fd00:0:83::/64 encap seg6 mode encap segs
        #        fcff:4::1,fcff:8::100 dev r1-h11 metric 200
        logger.info('*********** Creating encap route')
        res = handle_srv6_path(
            op='add',
            channel=r1_chan,
            destination='fd00:0:83::/64',
            segments=['fcff:4::1', 'fcff:8::100'],
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
        logger.info('*********** Creating decap route')
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
        #
        # +---------------------------------------------------------------+
        # |          Set tunnel from r8 to r1 for fd00:0:11::/64          |
        # +---------------------------------------------------------------+
        logger.info('******* Set tunnel from r8 to r1 for fd00:0:11::/64')
        #
        # Encap route on r8
        # on r8: ip -6 route add fd00:0:11::/64 encap seg6 mode encap segs
        #        fcff:4::1,fcff:1::100 dev r8-h83 metric 200
        logger.info('*********** Creating encap route')
        res = handle_srv6_path(
            op='add',
            channel=r8_chan,
            destination='fd00:0:11::/64',
            segments=['fcff:4::1', 'fcff:1::100'],
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
        logger.info('*********** Creating decap route')
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
        # |                             Done                              |
        # +---------------------------------------------------------------+
        print()


def create_tunnel_r1r7r8():
    # +--------------------------------------------------------------------+
    # |          Create a bidirectional tunnel between h11 and h83         |
    # |              passing through router r7 (r1---r7---r8)              |
    # +--------------------------------------------------------------------+
    logger.info('*** Attempting to create tunnel r1---r7---r8')
    # IP addresses
    r1 = 'fcff:1::1'
    r8 = 'fcff:8::1'
    # Open gRPC channels
    with get_grpc_session(r1, GRPC_PORT) as r1_chan, \
            get_grpc_session(r8, GRPC_PORT) as r8_chan:
        # +---------------------------------------------------------------+
        # |          Set tunnel from r1 to r8 for fd00:0:83::/64          |
        # +---------------------------------------------------------------+
        logger.info('******* Set tunnel from r1 to r8 for fd00:0:83::/64')
        #
        # Encap route on r1
        # on r1: ip -6 route add fd00:0:83::/64 encap seg6 mode encap segs
        #        fcff:7::1,fcff:8::100 dev r1-h11 metric 100
        logger.info('*********** Creating encap route')
        res = handle_srv6_path(
            op='add',
            channel=r1_chan,
            destination='fd00:0:83::/64',
            segments=['fcff:7::1', 'fcff:8::100'],
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
        logger.info('*********** Creating decap route')
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
        #
        # +---------------------------------------------------------------+
        # |          Set tunnel from r8 to r1 for fd00:0:11::/64          |
        # +---------------------------------------------------------------+
        logger.info('******* Set tunnel from r8 to r1 for fd00:0:11::/64')
        #
        # Encap route on r8
        # on r8: ip -6 route add fd00:0:11::/64 encap seg6 mode encap segs
        #        fcff:7::1,fcff:1::100 dev r8-h83 metric 100
        logger.info('*********** Creating encap route')
        res = handle_srv6_path(
            op='add',
            channel=r8_chan,
            destination='fd00:0:11::/64',
            segments=['fcff:7::1', 'fcff:1::100'],
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
        logger.info('*********** Creating decap route')
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
        # |                             Done                              |
        # +---------------------------------------------------------------+
        print()


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
            metric=200
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
            metric=200
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
            metric=200
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
            metric=200
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


def remove_tunnel_r1r7r8():
    # +--------------------------------------------------------------------+
    # |          Remove a bidirectional tunnel between h11 and h83         |
    # |              passing through router r7 (r1---r7---r8)              |
    # +--------------------------------------------------------------------+
    logger.info('*** Attempting to remove tunnel r1---r7---r8')
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
        # on r8: ip -6 route del fcff:8::100 dev r8-h83 metric 100
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
        # on r1: ip -6 route del fd00:0:83::/64 dev r1-h11 metric 100
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
        # on r1: ip -6 route del fcff:1::100 dev r1-h11 metric 100
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


def shift_path():
    # +--------------------------------------------------------------------+
    # |         Switch from r1---r7---r8 path to r1---r4---r8 path         |
    # |                     by exchanging the metrics                      |
    # +--------------------------------------------------------------------+
    logger.info('*** Attempting to change path from r1---r7---r8 to r1---r4---r8')
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
        logger.info('*** Increasing the metric value of the tunnel r1---r7---r8')
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


# Create tunnel r1---r4---r8
create_tunnel_r1r4r8()
# Create tunnel r1---r7---r8
create_tunnel_r1r7r8()
# Change tunnel
shift_path()
# Remove tunnel r1---r7---r8
remove_tunnel_r1r7r8()
# Remove tunnel r1---r4---r8
remove_tunnel_r1r4r8()
