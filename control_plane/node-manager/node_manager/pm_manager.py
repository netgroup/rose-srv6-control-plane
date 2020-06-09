#!/usr/bin/python


import atexit
import os
from concurrent import futures
import sys
import grpc
import logging

# Proto dependencies
import commons_pb2
import srv6pmCommons_pb2
import srv6pmReflector_pb2
import srv6pmSender_pb2
import srv6pmService_pb2_grpc
# import srv6pmServiceController_pb2
# import srv6pmServiceController_pb2_grpc

# SRv6 data-plane dependencies
from data_plane.twamp.twamp_demon import SessionSender
from data_plane.twamp.twamp_demon import SessionReflector
from data_plane.twamp.twamp_demon import TestPacketReceiver
from data_plane.twamp.twamp_demon import EbpfInterf
from data_plane.twamp.twamp_demon import IpSetInterf


# Folder containing this script
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

# SRv6 PFPLM dependencies
SRV6_PM_XDP_EBPF_PATH = os.getenv('SRV6_PM_XDP_EBPF_PATH', None)
if SRV6_PM_XDP_EBPF_PATH is None:
    print('SRV6_PM_XDP_EBPF_PATH environment variable not set')
    exit(-2)
SRV6_PFPLM_PATH = os.path.join(SRV6_PM_XDP_EBPF_PATH, 'srv6-pfplm/')
sys.path.append(SRV6_PFPLM_PATH)


'''##################################### GRPC CONTROLLER'''


class TWAMPController(srv6pmService_pb2_grpc.SRv6PMServicer):
    def __init__(self, SessionSender=None, SessionReflector=None, packetReceiver=None):
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
            # in_interfaces = list()
            # for interface in request.in_interfaces:
            #     in_interfaces.append(interface)
            # # Extract outgoing interfaces from the gRPC message
            # out_interfaces = list()
            # for interface in request.out_interfaces:
            #     out_interfaces.append(interface)
            # Start measurement process
            res = self.sender.startMeas(
                meas_id=request.measure_id,
                sidList=request.sdlist,
                revSidList=request.sdlistreverse,
                # inInterface=in_interfaces[0],   # Currently we support 1 intf
                # outInterface=out_interfaces[0]   # Currently we support 1 intf
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
            # in_interfaces = list()
            # for interface in request.in_interfaces:
            #     in_interfaces.append(interface)
            # # Extract outgoing interfaces from the gRPC message
            # out_interfaces = list()
            # for interface in request.out_interfaces:
            #     out_interfaces.append(interface)
            # Start measurement process
            self.reflector.startMeas(
                sidList=request.sdlist,
                revSidList=request.sdlistreverse,
                # inInterface=request.in_interfaces[0],   # Currently we support 1 intf
                # outInterface=request.out_interfaces[0]   # Currently we support 1 intf
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
            response = srv6pmCommons_pb2.ExperimentDataResponse(
                status=status)
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
        # Check if this node is already configured
        if self.configured:
            status = commons_pb2.StatusCode.Value('STATUS_ALREADY_CONFIGURED')
            return srv6pmCommons_pb2.SetConfigurationReply(status=status)
        # Extract parameters from the gRPC request
        interval = request.color_options.interval_duration
        margin = request.color_options.delay_margin
        number_of_color = request.color_options.numbers_of_color
        ss_udp_port = request.ss_udp_port
        if ss_udp_port is None:
            ss_udp_port = 1206
        refl_udp_port = request.refl_udp_port
        if refl_udp_port is None:
            refl_udp_port = 1205
        pm_driver = request.pm_driver  # eBPF or IPSET
        in_interfaces = request.in_interfaces
        out_interfaces = request.out_interfaces
        self.pm_driver = pm_driver
        # Initialize driver eBPF/IPSET
        if self.pm_driver == srv6pmCommons_pb2.eBPF:
            self.driver = EbpfInterf(
                in_interfaces=in_interfaces,
                out_interfaces=out_interfaces
            )
            atexit.register(self.driver.stop)
        elif self.pm_driver == srv6pmCommons_pb2.IPSet:
            self.driver = IpSetInterf()
        else:
            print('Invalid PM Driver: %s' % self.pm_driver)
            status = commons_pb2.StatusCode.Value('STATUS_INTERNAL_ERROR')
            return srv6pmCommons_pb2.SetConfigurationReply(status=status)
        # Init stop events
        session_sender_stop_event = Event()
        session_reflector_stop_event = Event()
        packet_receiver_stop_event = Event()
        # PUNT interface
        recvInterf = 'punt0'
        # Initialize sender
        self.sender = SessionSender(self.driver, session_sender_stop_event)
        # Initialize reflector
        self.reflector = SessionReflector(self.driver,
                                                 session_reflector_stop_event)
        # Initialize packet receiver
        self.packetRecv = TestPacketReceiver(
            interface=recvInterf,
            sender=self.sender,
            reflector=self.reflector,
            ss_udp_port=ss_udp_port,
            refl_udp_port=refl_udp_port,
            stop_event=packet_receiver_stop_event
        )
        # Set sender and reflector params
        self.packetRecv.ss_udp_port = ss_udp_port
        self.packetRecv.refl_udp_port = refl_udp_port
        self.reflector.ss_udp_port = ss_udp_port
        self.reflector.refl_udp_port = refl_udp_port
        self.sender.ss_udp_port = ss_udp_port
        self.sender.refl_udp_port = refl_udp_port
        self.sender.interval = int(interval)
        self.sender.margin = timedelta(milliseconds=int(margin))
        self.sender.numColor = int(number_of_color)
        # Start reflector thread
        self.reflector.start()
        # Start sender thread
        self.sender.start()
        # Start packet receiver thread
        self.packetRecv.start()
        # Set 'configured' flag
        self.configured = True
        # Create the response
        status = commons_pb2.StatusCode.Value('STATUS_SUCCESS')
        return srv6pmCommons_pb2.SetConfigurationReply(status=status)

    def resetConfiguration(self, request, context):
        print("GRPC CONTROLLER: resetConfiguration")
        # Check if this node is not configured:
        if not self.configured:
            status = commons_pb2.StatusCode.Value('STATUS_NOT_CONFIGURED')
            return srv6pmCommons_pb2.SetConfigurationReply(status=status)
        if self.reflector.startedMeas or \
                self.sender.startedMeas:
            print('Sender / Reflector running. Cannot reset configuration')
            status = commons_pb2.StatusCode.Value('STATUS_INTERNAL_ERROR')
            return srv6pmCommons_pb2.SetConfigurationReply(status=status)
        # Stop reflector thread
        self.reflector.stop_event.set()
        self.reflector = None
        # Stop sender thread
        self.sender.stop_event.set()
        self.sender = None
        # Stop packet receiver thread
        self.packetRecv.stop_event.set()
        self.packetRecv = None
        # Unload eBPF program
        if self.pm_driver == srv6pmCommons_pb2.eBPF:
            atexit.unregister(self.driver.stop)
        self.driver.stop()
        # Set 'configured' flag
        self.configured = False
        # Create the response
        status = commons_pb2.StatusCode.Value('STATUS_SUCCESS')
        return srv6pmCommons_pb2.SetConfigurationReply(status=status)


# def add_pm_manager_to_server(server):
#     recvInterf = 'punt0'

#     driver = EbpfInterf()
#     # driver = IpSetInterf()

#     sessionsender = SessionSender(driver)
#     sessionreflector = SessionReflector(driver)
#     packetRecv = TestPacketReceiver(
#         recvInterf, sessionsender, sessionreflector)
#     sessionreflector.start()
#     sessionsender.start()
#     packetRecv.start()


def add_pm_manager_to_server(server):
    srv6pmService_pb2_grpc.add_SRv6PMServicer_to_server(
        TWAMPController(), server)


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
