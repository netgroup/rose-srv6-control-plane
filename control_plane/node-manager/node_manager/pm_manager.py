#!/usr/bin/python


'''
Implementation of SRv6 PM Manager
'''

# General imports
import atexit
import logging
import os
import sys
from concurrent import futures
from datetime import timedelta
from threading import Event

# gRPC dependencies
import grpc

# Proto dependencies
import commons_pb2
import srv6pmCommons_pb2
import srv6pmReflector_pb2
import srv6pmSender_pb2
import srv6pmService_pb2_grpc

# import srv6pmServiceController_pb2
# import srv6pmServiceController_pb2_grpc

# SRv6 data-plane dependencies
try:
    from data_plane.twamp.twamp_demon import SessionSender
    from data_plane.twamp.twamp_demon import SessionReflector
    from data_plane.twamp.twamp_demon import TestPacketReceiver
    from data_plane.twamp.twamp_demon import EbpfInterf
except ImportError:
    print('rose-srv6-data-plane is required to run this module'
          'Is it installed?')
    sys.exit(-2)
# from data_plane.twamp.twamp_demon import IpSetInterf


# Folder containing this script
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

# SRv6 PFPLM dependencies
SRV6_PM_XDP_EBPF_PATH = os.getenv('SRV6_PM_XDP_EBPF_PATH', None)
if SRV6_PM_XDP_EBPF_PATH is None:
    print('SRV6_PM_XDP_EBPF_PATH environment variable not set')
    sys.exit(-2)
SRV6_PFPLM_PATH = os.path.join(SRV6_PM_XDP_EBPF_PATH, 'srv6-pfplm/')
sys.path.append(SRV6_PFPLM_PATH)


# '''##################################### GRPC CONTROLLER'''


class TWAMPController(srv6pmService_pb2_grpc.SRv6PMServicer):
    '''gRPC request handler'''

    def __init__(self, session_sender=None,
                 session_reflector=None, packet_receiver=None):
        self.sender = session_sender
        self.reflector = session_reflector
        self.packet_receiver = packet_receiver
        self.driver = None
        self.pm_driver = None
        # Check if node is already configured
        if self.sender is None and self.reflector is None and \
                self.packet_receiver is None:
            # Not yet configured. Configuration should be injected
            # by the controller before starting measurement
            self.configured = False
        elif self.sender is not None and self.reflector is not None and \
                self.packet_receiver is not None:
            # The node has be configured 'statically'
            self.configured = True
        else:
            # Partial configuration is not allowed
            print('Invalid configuration for TWAMPController\n')
            sys.exit(-2)

    def startExperimentSender(self, request, context):
        '''Start an experiment as sender'''

        print('GRPC CONTROLLER: startExperimentSender')
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
            res = self.sender.start_meas(
                meas_id=request.measure_id,
                sidList=request.sdlist,
                revSidList=request.sdlistreverse,
                # inInterface=in_interfaces[0],   # Currently we support 1 intf
                # outInterface=out_interfaces[0]   # Currently we support 1
                # intf
            )
            if res == 1:
                status = commons_pb2.StatusCode.Value('STATUS_SUCCESS')
            else:
                status = commons_pb2.StatusCode.Value(
                    'STATUS_INTERNAL_ERROR')
        return srv6pmSender_pb2.StartExperimentSenderReply(status=status)

    def stopExperimentSender(self, request, context):
        '''Stop an experiment running on sender'''

        print('GRPC CONTROLLER: stopExperimentSender')
        # Check if the node has been configured
        if not self.configured:
            # Node not configured
            status = commons_pb2.StatusCode.Value(
                'STATUS_NOT_CONFIGURED')
        else:
            # Node configured
            #
            # Stop measurement process
            self.sender.stop_meas(request.sdlist)
            status = commons_pb2.StatusCode.Value('STATUS_SUCCESS')
        return srv6pmCommons_pb2.StopExperimentReply(status=status)

    def startExperimentReflector(self, request, context):
        '''Start an experiment as reflector'''

        print('GRPC CONTROLLER: startExperimentReflector')
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
            self.reflector.start_meas(
                sidList=request.sdlist,
                revSidList=request.sdlistreverse,
                # inInterface=request.in_interfaces[0],
                # outInterface=request.out_interfaces[0]
            )
            status = commons_pb2.StatusCode.Value('STATUS_SUCCESS')
        return srv6pmReflector_pb2.StartExperimentReflectorReply(status=status)

    def stopExperimentReflector(self, request, context):
        '''Stop an experiment on the reflector'''

        print('GRPC CONTROLLER: startExperimentReflector')
        # Check if the node has been configured
        if not self.configured:
            # Node not configured
            status = commons_pb2.StatusCode.Value(
                'STATUS_NOT_CONFIGURED')
        else:
            # Node configured
            #
            # Stop measurement process
            self.reflector.stop_meas(request.sdlist)
            status = commons_pb2.StatusCode.Value('STATUS_SUCCESS')
        return srv6pmCommons_pb2.StopExperimentReply(status=status)

    def retriveExperimentResults(self, request, context):
        '''Retrieve results from the sender'''

        print('GRPC CONTROLLER: retriveExperimentResults')
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
            last_meas, meas_id = self.sender.get_meas(request.sdlist)

            if bool(last_meas):
                response = srv6pmCommons_pb2.ExperimentDataResponse()
                response.status = commons_pb2.StatusCode.Value(
                    'STATUS_SUCCESS')
                data = (response                # pylint: disable=no-member
                        .measurement_data.add())
                data.meas_id = meas_id
                data.ssSeqNum = last_meas['sssn']
                data.ssTxCounter = last_meas['ssTXc']
                data.rfRxCounter = last_meas['rfRXc']
                data.fwColor = last_meas['fwColor']

                data.rfSeqNum = last_meas['rfsn']
                data.rfTxCounter = last_meas['rfTXc']
                data.ssRxCounter = last_meas['ssRXc']
                data.rvColor = last_meas['rvColor']
            else:
                status = commons_pb2.StatusCode.Value(
                    'STATUS_INTERNAL_ERROR')
                response = srv6pmCommons_pb2.ExperimentDataResponse(
                    status=status)

        return response

    def setConfiguration(self, request, context):
        '''Inject the configuration on the node'''

        print('GRPC CONTROLLER: setConfiguration')
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
        in_interfaces = request.in_interfaces
        out_interfaces = request.out_interfaces
        self.pm_driver = request.pm_driver  # eBPF or IPSET
        # Initialize driver eBPF/IPSET
        if self.pm_driver == srv6pmCommons_pb2.eBPF:
            self.driver = EbpfInterf(
                in_interfaces=in_interfaces,
                out_interfaces=out_interfaces
            )
            atexit.register(self.driver.stop)
        elif self.pm_driver == srv6pmCommons_pb2.IPSet:
            # self.driver = IpSetInterf()
            # IPSET driver not yet implemented
            status = commons_pb2.StatusCode.Value(
                'STATUS_OPERATION_NOT_SUPPORTED')
            return srv6pmCommons_pb2.SetConfigurationReply(status=status)
        else:
            print('Invalid PM Driver: %s' % self.pm_driver)
            status = commons_pb2.StatusCode.Value('STATUS_INTERNAL_ERROR')
            return srv6pmCommons_pb2.SetConfigurationReply(status=status)
        # Init stop events
        session_sender_stop_event = Event()
        session_reflector_stop_event = Event()
        packet_receiver_stop_event = Event()
        # PUNT interface
        recv_interf = 'punt0'
        # Initialize sender
        self.sender = SessionSender(self.driver, session_sender_stop_event)
        # Initialize reflector
        self.reflector = SessionReflector(self.driver,
                                          session_reflector_stop_event)
        # Initialize packet receiver
        self.packet_receiver = TestPacketReceiver(
            interface=recv_interf,
            session_sender=self.sender,
            session_reflector=self.reflector,
            ss_udp_port=ss_udp_port,
            refl_udp_port=refl_udp_port,
            stop_event=packet_receiver_stop_event
        )
        # Set sender and reflector params
        self.packet_receiver.ss_udp_port = ss_udp_port
        self.packet_receiver.refl_udp_port = refl_udp_port
        self.reflector.ss_udp_port = ss_udp_port
        self.reflector.refl_udp_port = refl_udp_port
        self.sender.ss_udp_port = ss_udp_port
        self.sender.refl_udp_port = refl_udp_port
        self.sender.interval = int(interval)
        self.sender.margin = timedelta(milliseconds=int(margin))
        self.sender.num_color = int(number_of_color)
        # Start reflector thread
        self.reflector.start()
        # Start sender thread
        self.sender.start()
        # Start packet receiver thread
        self.packet_receiver.start()
        # Set 'configured' flag
        self.configured = True
        # Create the response
        status = commons_pb2.StatusCode.Value('STATUS_SUCCESS')
        return srv6pmCommons_pb2.SetConfigurationReply(status=status)

    def resetConfiguration(self, request, context):
        '''Clear the current configuration'''

        print('GRPC CONTROLLER: resetConfiguration')
        # Check if this node is not configured:
        if not self.configured:
            status = commons_pb2.StatusCode.Value('STATUS_NOT_CONFIGURED')
            return srv6pmCommons_pb2.SetConfigurationReply(status=status)
        if self.reflector.started_meas or \
                self.sender.started_meas:
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
        self.packet_receiver.stop_event.set()
        self.packet_receiver = None
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
    '''Attach PM Manager gRPC server to an existing server'''

    srv6pmService_pb2_grpc.add_SRv6PMServicer_to_server(
        TWAMPController(), server)


def serve(ip_addr, gprc_port, recv_interf, epbf_out_interf, epbf_in_interf):
    '''Start gRPC server'''

    driver = EbpfInterf(
        in_interfaces=epbf_in_interf,
        out_interfaces=epbf_out_interf
    )
    # driver = IpSetInterf()

    sessionsender = SessionSender(driver)
    sessionreflector = SessionReflector(driver)
    packet_recv = TestPacketReceiver(
        recv_interf, sessionsender, sessionreflector)
    sessionreflector.start()
    sessionsender.start()
    packet_recv.start()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    srv6pmService_pb2_grpc.add_SRv6PMServicer_to_server(
        TWAMPController(sessionsender, sessionreflector, packet_recv), server)
    server.add_insecure_port(
        '[{ip}]:{port}'.format(
            ip=ip_addr, port=gprc_port))
    # server.add_insecure_port('{ip}:{port}'.format(ip=ipaddr,port=gprcPort))
    print('\n-------------- Start Demon --------------\n')
    server.start()
    server.wait_for_termination()


def __main():
    '''Entry point for this module'''

    ip_addr = sys.argv[1]
    gprc_port = sys.argv[2]
    node_id = sys.argv[3]
    if node_id == 'd':
        recv_interf = 'punt0'
        epbf_out_interf = 'r8-r6_egr'
        ebpf_in_interf = 'r8-r6'
    elif node_id == 'e':
        recv_interf = 'punt0'
        epbf_out_interf = 'r1-r2_egr'
        ebpf_in_interf = 'r1-r2'
    else:
        sys.exit(-1)

    logging.basicConfig()
    serve(ip_addr, gprc_port, recv_interf, epbf_out_interf, ebpf_in_interf)


if __name__ == '__main__':
    __main()
