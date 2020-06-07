#!/usr/bin/python

import os

# Activate virtual environment if a venv path has been specified in .venv
# This must be executed only if this file has been executed as a
# script (instead of a module)
if __name__ == '__main__':
    # Check if .venv file exists
    if os.path.exists('.venv'):
        with open('.venv', 'r') as venv_file:
            # Get virtualenv path from .venv file
            # and remove trailing newline chars
            venv_path = venv_file.read().rstrip()
        # Get path of the activation script
        venv_path = os.path.join(venv_path, 'bin/activate_this.py')
        if not os.path.exists(venv_path):
            print('Virtual environment path specified in .venv '
                  'points to an invalid path\n')
            exit(-2)
        with open(venv_path) as f:
            # Read the activation script
            code = compile(f.read(), venv_path, 'exec')
            # Execute the activation script to activate the venv
            exec(code, {'__file__': venv_path})

from concurrent import futures
import sys
import grpc
import logging
from threading import Thread
import sched
import time
from datetime import datetime, timedelta
import math

import subprocess
import shlex

from scapy.all import send, sniff
from scapy.layers.inet import UDP
from scapy.layers.inet6 import IPv6, IPv6ExtHdrSegmentRouting

# Folder containing this script
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

# Add PROTO folder
PROTO_PATH = os.getenv('PROTO_PATH', None)
if PROTO_PATH is None:
    print('PROTO_PATH environment variable not set')
    exit(-2)
sys.path.append(PROTO_PATH)

# SRv6 PFPLM dependencies
SRV6_PM_XDP_EBPF_PATH = os.getenv('SRV6_PM_XDP_EBPF_PATH', None)
if SRV6_PM_XDP_EBPF_PATH is None:
    print('SRV6_PM_XDP_EBPF_PATH environment variable not set')
    exit(-2)
SRV6_PFPLM_PATH = os.path.join(SRV6_PM_XDP_EBPF_PATH, 'srv6-pfplm/')
sys.path.append(SRV6_PFPLM_PATH)

# SRv6 PFPLM dependencies
ROSE_SRV6_DATA_PLANE_PATH = os.getenv('ROSE_SRV6_DATA_PLANE_PATH', None)
if ROSE_SRV6_DATA_PLANE_PATH is None:
    print('ROSE_SRV6_DATA_PLANE_PATH environment variable not set')
    exit(-2)
TWAMP_PATH = os.path.join(ROSE_SRV6_DATA_PLANE_PATH, 'twamp/')
sys.path.append(TWAMP_PATH)
import twamp
from twamp_demon import SessionSender
from twamp_demon import SessionReflector
from twamp_demon import TestPacketReceiver
from twamp_demon import EbpfInterf
from twamp_demon import IpSetInterf


# FRPC protocol
import commons_pb2
import srv6pmCommons_pb2
import srv6pmReflector_pb2
import srv6pmSender_pb2
import srv6pmService_pb2_grpc
import srv6pmServiceController_pb2
import srv6pmServiceController_pb2_grpc


'''##################################### GRPC CONTROLLER'''


class TWAMPController(srv6pmService_pb2_grpc.SRv6PMServicer):
    def __init__(self, SessionSender, SessionReflector, packetReceiver):
        self.port_server = 20000
        self.sender = SessionSender
        self.reflector = SessionReflector
        self.packetReceiver = packetReceiver
        # Configured flag
        self.configured = False

    def startExperimentSender(self, request, context):
        print("GRPC CONTROLLER: startExperimentSender")
        # Check if the node has been configured
        if not self.configured:
            # Node not configured
            status = commons_pb2.StatusCode.Value(
                'STATUS_NOT_CONFIGURED')
        else:
            # Node configured
            #
            # Extract incoming interfaces from the gRPC message
            in_interfaces = list()
            for interface in request.in_interfaces:
                in_interfaces.append(interface)
            # Extract outgoing interfaces from the gRPC message
            out_interfaces = list()
            for interface in request.out_interfaces:
                out_interfaces.append(interface)
            # Start measurement process
            res = self.sender.startMeas(
                meas_id=request.measure_id,
                sidList=request.sdlist,
                revSidList=request.sdlistreverse,
                inInterface=in_interfaces[0],   # Currently we support 1 intf
                outInterface=out_interfaces[0]   # Currently we support 1 intf
            )
            if res == 1:
                status = commons_pb2.StatusCode.Value('STATUS_SUCCESS')
            else:
                status = commons_pb2.StatusCode.Value(
                    'STATUS_INTERNAL_ERROR')
        return srv6pmSender_pb2.StartExperimentSenderReply(status=status)

    def stopExperimentSender(self, request, context):
        print("GRPC CONTROLLER: stopExperimentSender")
        # Check if the node has been configured
        if not self.configured:
            # Node not configured
            status = commons_pb2.StatusCode.Value(
                'STATUS_NOT_CONFIGURED')
        else:
            # Node configured
            #
            # Stop measurement process
            self.sender.stopMeas(request.sdlist)
            status = commons_pb2.StatusCode.Value('STATUS_SUCCESS')
        return srv6pmCommons_pb2.StopExperimentReply(status=status)

    def startExperimentReflector(self, request, context):
        print("GRPC CONTROLLER: startExperimentReflector")
        # Check if the node has been configured
        if not self.configured:
            # Node not configured
            status = commons_pb2.StatusCode.Value(
                'STATUS_NOT_CONFIGURED')
        else:
            # Node configured
            #
            # Extract incoming interfaces from the gRPC message
            in_interfaces = list()
            for interface in request.in_interfaces:
                in_interfaces.append(interface)
            # Extract outgoing interfaces from the gRPC message
            out_interfaces = list()
            for interface in request.out_interfaces:
                out_interfaces.append(interface)
            # Start measurement process
            self.reflector.startMeas(
                sidList=request.sdlist,
                revSidList=request.sdlistreverse,
                inInterface=request.in_interfaces[0],   # Currently we support 1 intf
                outInterface=request.out_interfaces[0]   # Currently we support 1 intf
            )
            status = commons_pb2.StatusCode.Value('STATUS_SUCCESS')
        return srv6pmReflector_pb2.StartExperimentReflectorReply(status=status)

    def stopExperimentReflector(self, request, context):
        print("GRPC CONTROLLER: startExperimentReflector")
        # Check if the node has been configured
        if not self.configured:
            # Node not configured
            status = commons_pb2.StatusCode.Value(
                'STATUS_NOT_CONFIGURED')
        else:
            # Node configured
            #
            # Stop measurement process
            self.reflector.stopMeas(request.sdlist)
            status = commons_pb2.StatusCode.Value('STATUS_SUCCESS')
        return srv6pmCommons_pb2.StopExperimentReply(status=status)

    def retriveExperimentResults(self, request, context):
        print("GRPC CONTROLLER: retriveExperimentResults")
        # Check if the node has been configured
        if not self.configured:
            # Node not configured
            status = commons_pb2.StatusCode.Value(
                'STATUS_NOT_CONFIGURED')
        else:
            # Node configured
            #
            # Retrieve experiment results
            lastMeas, meas_id = self.sender.getMeas(request.sdlist)

            if bool(lastMeas):
                response = srv6pmCommons_pb2.ExperimentDataResponse()
                response.status = commons_pb2.StatusCode.Value(
                    'STATUS_SUCCESS')
                data = response.measurement_data.add()
                data.meas_id = meas_id
                data.ssSeqNum = lastMeas['sssn']
                data.ssTxCounter = lastMeas['ssTXc']
                data.rfRxCounter = lastMeas['rfRXc']
                data.fwColor = lastMeas['fwColor']

                data.rfSeqNum = lastMeas['rfsn']
                data.rfTxCounter = lastMeas['rfTXc']
                data.ssRxCounter = lastMeas['ssRXc']
                data.rvColor = lastMeas['rvColor']
            else:
                status = commons_pb2.StatusCode.Value(
                    'STATUS_INTERNAL_ERROR')
                response = srv6pmCommons_pb2.ExperimentDataResponse(
                    status=status)

        return response

    def setConfiguration(self, request, context):
        print("GRPC CONTROLLER: setConfiguration")
        # Extract parameters from the gRPC request
        interval = request.color_options.interval_duration
        margin = request.color_options.delay_margin
        number_of_color = request.color_options.numbers_of_color
        ss_udp_port = request.ss_udp_port
        refl_udp_port = request.refl_udp_port
        # pm_driver = request.pm_driver  # eBPF or IPSET TODO Currently unused
        # Set sender and reflector params
        self.packetReceiver.ss_udp_port = ss_udp_port
        self.packetReceiver.refl_udp_port = refl_udp_port
        self.reflector.ss_udp_port = ss_udp_port
        self.reflector.refl_udp_port = refl_udp_port
        self.sender.ss_udp_port = ss_udp_port
        self.sender.refl_udp_port = refl_udp_port
        self.sender.interval = int(interval)
        self.sender.margin = timedelta(milliseconds=int(margin))
        self.sender.numColor = int(number_of_color)
        # Set 'configured' flag
        self.configured = True
        # Create the response
        status = commons_pb2.StatusCode.Value('STATUS_SUCCESS')
        return srv6pmCommons_pb2.SetConfigurationReply(status=status)


def add_pm_manager_to_server(server):
    recvInterf = 'punt0'

    driver = EbpfInterf()
    # driver = IpSetInterf()

    sessionsender = SessionSender(driver)
    sessionreflector = SessionReflector(driver)
    packetRecv = TestPacketReceiver(
        recvInterf, sessionsender, sessionreflector)
    sessionreflector.start()
    sessionsender.start()
    packetRecv.start()

    srv6pmService_pb2_grpc.add_SRv6PMServicer_to_server(
        TWAMPController(sessionsender, sessionreflector, packetRecv), server)


def serve(ipaddr, gprcPort, recvInterf, epbfOutInterf, epbfInInterf):
    driver = EbpfInterf()
    # driver = IpSetInterf()

    sessionsender = SessionSender(driver)
    sessionreflector = SessionReflector(driver)
    packetRecv = TestPacketReceiver(
        recvInterf, sessionsender, sessionreflector)
    sessionreflector.start()
    sessionsender.start()
    packetRecv.start()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    srv6pmService_pb2_grpc.add_SRv6PMServicer_to_server(
        TWAMPController(sessionsender, sessionreflector, packetRecv), server)
    server.add_insecure_port("[{ip}]:{port}".format(ip=ipaddr, port=gprcPort))
    # server.add_insecure_port("{ip}:{port}".format(ip=ipaddr,port=gprcPort))
    print("\n-------------- Start Demon --------------\n")
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    ipaddr = sys.argv[1]
    gprcPort = sys.argv[2]
    nodeID = sys.argv[3]
    if nodeID == "d":
        recvInterf = "punt0"
        epbfOutInterf = "r8-r6_egr"
        epbfInInterf = "r8-r6"
    elif nodeID == "e":
        recvInterf = "punt0"
        epbfOutInterf = "r1-r2_egr"
        epbfInInterf = "r1-r2"
    else:
        exit(-1)

    logging.basicConfig()
    serve(ipaddr, gprcPort, recvInterf, epbfOutInterf, epbfInInterf)
