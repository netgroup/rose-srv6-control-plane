#!/usr/bin/python

##############################################################################################
# Copyright (C) 2020 Carmine Scarpitta - (Consortium GARR and University of Rome "Tor Vergata")
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
# Implementation of a CLI for the SRv6 Controller
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


from argparse import ArgumentParser
import sys

# Controller dependencies
from control_plane.controller import srv6_pm
from control_plane.controller import utils

# Default CA certificate path
DEFAULT_CERTIFICATE = 'cert_server.pem'


def set_configuration(sender, reflector,
                      sender_port, reflector_port, send_udp_port,
                      refl_udp_port, interval_duration, delay_margin,
                      number_of_color, pm_driver):
    with utils.get_grpc_session(sender, sender_port) as sender_channel, \
            utils.get_grpc_session(reflector, reflector_port) as reflector_channel:
        res = srv6_pm.set_configuration(
            sender_channel=sender_channel,
            reflector_channel=reflector_channel,
            send_udp_port=send_udp_port,
            refl_udp_port=refl_udp_port,
            interval_duration=interval_duration,
            delay_margin=delay_margin,
            number_of_color=number_of_color,
            pm_driver=pm_driver
        )
        if res == 0:
            print('OK')
        else:
            print('Error')


def reset_configuration(sender, reflector,
                        sender_port, reflector_port):
    with utils.get_grpc_session(sender, sender_port) as sender_channel, \
            utils.get_grpc_session(reflector, reflector_port) as reflector_channel:
        res = srv6_pm.reset_configuration(
            sender_channel=sender_channel,
            reflector_channel=reflector_channel
        )
        if res == 0:
            print('OK')
        else:
            print('Error')


def start_experiment(sender, reflector,
                     sender_port, reflector_port, send_refl_dest,
                     refl_send_dest, send_refl_sidlist, refl_send_sidlist,
                     #  send_in_interfaces, refl_in_interfaces,
                     #  send_out_interfaces, refl_out_interfaces,
                     measurement_protocol, measurement_type,
                     authentication_mode, authentication_key,
                     timestamp_format, delay_measurement_mode,
                     padding_mbz, loss_measurement_mode, measure_id=None,
                     send_refl_localseg=None, refl_send_localseg=None,
                     force=False):
    with utils.get_grpc_session(sender, sender_port) as sender_channel, \
            utils.get_grpc_session(reflector, reflector_port) as reflector_channel:
        res = srv6_pm.start_experiment(
            sender_channel=sender_channel,
            reflector_channel=reflector_channel,
            send_refl_dest=send_refl_dest,
            refl_send_dest=refl_send_dest,
            send_refl_sidlist=send_refl_sidlist.split(','),
            refl_send_sidlist=refl_send_sidlist.split(','),
            # send_in_interfaces=send_in_interfaces,        # Moved to set_configuration
            # refl_in_interfaces=refl_in_interfaces,
            # send_out_interfaces=send_out_interfaces,
            # refl_out_interfaces=refl_out_interfaces,
            measurement_protocol=measurement_protocol,
            measurement_type=measurement_type,
            authentication_mode=authentication_mode,
            authentication_key=authentication_key,
            timestamp_format=timestamp_format,
            delay_measurement_mode=delay_measurement_mode,
            padding_mbz=padding_mbz,
            loss_measurement_mode=loss_measurement_mode,
            measure_id=measure_id,
            send_refl_localseg=send_refl_localseg,
            refl_send_localseg=refl_send_localseg,
            force=force
        )
        if res == 0:
            print('OK')
        else:
            print('Error')


def get_experiment_results(sender, reflector,
                           sender_port, reflector_port,
                           send_refl_sidlist, refl_send_sidlist):
    with utils.get_grpc_session(sender, sender_port) as sender_channel, \
            utils.get_grpc_session(reflector, reflector_port) as reflector_channel:
        print(srv6_pm.get_experiment_results(
            sender_channel=sender_channel,
            reflector_channel=reflector_channel,
            send_refl_sidlist=send_refl_sidlist.split(','),
            refl_send_sidlist=refl_send_sidlist.split(',')
        ))


def stop_experiment(sender, reflector,
                    sender_port, reflector_port, send_refl_dest,
                    refl_send_dest, send_refl_sidlist, refl_send_sidlist,
                    send_refl_localseg=None, refl_send_localseg=None):
    with utils.get_grpc_session(sender, sender_port) as sender_channel, \
            utils.get_grpc_session(reflector, reflector_port) as reflector_channel:
        srv6_pm.stop_experiment(
            sender_channel=sender_channel,
            reflector_channel=reflector_channel,
            send_refl_dest=send_refl_dest,
            refl_send_dest=refl_send_dest,
            send_refl_sidlist=send_refl_sidlist.split(','),
            refl_send_sidlist=refl_send_sidlist.split(','),
            send_refl_localseg=send_refl_localseg,
            refl_send_localseg=refl_send_localseg
        )


# Parse options
def parse_arguments_set_configuration(prog=sys.argv[0], args=None):
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    parser.add_argument(
        '--sender-ip', dest='sender_ip', action='store',
        required=True, help='IP of the gRPC server of the sender'
    )
    parser.add_argument(
        '--sender-port', dest='sender_port', action='store',
        required=True, help='Port of the gRPC server of the sender'
    )
    parser.add_argument(
        '--reflector-ip', dest='reflector_ip', action='store',
        required=True, help='IP of the gRPC server of the reflector'
    )
    parser.add_argument(
        '--reflector-port', dest='reflector_port', action='store',
        required=True, help='Port of the gRPC server of the reflector'
    )
    parser.add_argument(
        '-s', '--secure', action='store_true', help='Activate secure mode'
    )
    parser.add_argument(
        '-c', '--server-cert', dest='server_cert', action='store',
        default=DEFAULT_CERTIFICATE, help='CA certificate file'
    )
    parser.add_argument(
        '--send_in_interfaces', dest='send_in_interfaces', action='store',
        help='send_in_interfaces'
    )
    parser.add_argument(
        '--refl_in_interfaces', dest='refl_in_interfaces', action='store',
        help='refl_in_interfaces'
    )
    parser.add_argument(
        '--send_out_interfaces', dest='send_out_interfaces', action='store',
        help='send_out_interfaces'
    )
    parser.add_argument(
        '--refl_out_interfaces', dest='refl_out_interfaces', action='store',
        help='refl_out_interfaces'
    )
    parser.add_argument(
        '--send_udp_port', dest='send_udp_port', action='store',
        help='send_udp_port', type=int
    )
    parser.add_argument(
        '--refl_udp_port', dest='refl_udp_port', action='store',
        help='refl_udp_port', type=int
    )
    parser.add_argument(
        '--interval_duration', dest='interval_duration', action='store',
        help='interval_duration', type=int
    )
    parser.add_argument(
        '--delay_margin', dest='delay_margin', action='store',
        help='delay_margin', type=int
    )
    parser.add_argument(
        '--number_of_color', dest='number_of_color', action='store',
        help='number_of_color', type=int
    )
    parser.add_argument(
        '--pm_driver', dest='pm_driver', action='store',
        help='pm_driver'
    )
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Activate debug logs'
    )
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# Parse options
def parse_arguments_reset_configuration(prog=sys.argv[0], args=None):
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    parser.add_argument(
        '--sender-ip', dest='sender_ip', action='store',
        required=True, help='IP of the gRPC server of the sender'
    )
    parser.add_argument(
        '--sender-port', dest='sender_port', action='store',
        required=True, help='Port of the gRPC server of the sender'
    )
    parser.add_argument(
        '--reflector-ip', dest='reflector_ip', action='store',
        required=True, help='IP of the gRPC server of the reflector'
    )
    parser.add_argument(
        '--reflector-port', dest='reflector_port', action='store',
        required=True, help='Port of the gRPC server of the reflector'
    )
    parser.add_argument(
        '-s', '--secure', action='store_true', help='Activate secure mode'
    )
    parser.add_argument(
        '-c', '--server-cert', dest='server_cert', action='store',
        default=DEFAULT_CERTIFICATE, help='CA certificate file'
    )
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Activate debug logs'
    )
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# Parse options
def parse_arguments_start_experiment(prog=sys.argv[0], args=None):
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    parser.add_argument(
        '--sender-ip', dest='sender_ip', action='store',
        required=True, help='IP of the gRPC server of the sender'
    )
    parser.add_argument(
        '--sender-port', dest='sender_port', action='store',
        required=True, help='Port of the gRPC server of the sender'
    )
    parser.add_argument(
        '--reflector-ip', dest='reflector_ip', action='store',
        required=True, help='IP of the gRPC server of the reflector'
    )
    parser.add_argument(
        '--reflector-port', dest='reflector_port', action='store',
        required=True, help='Port of the gRPC server of the reflector'
    )
    parser.add_argument(
        '-s', '--secure', action='store_true', help='Activate secure mode'
    )
    parser.add_argument(
        '-c', '--server-cert', dest='server_cert', action='store',
        default=DEFAULT_CERTIFICATE, help='CA certificate file'
    )
    parser.add_argument(
        '--send_refl_dest', dest='send_refl_dest', action='store',
        help='send_refl_dest', required=True
    )
    parser.add_argument(
        '--refl_send_dest', dest='refl_send_dest', action='store',
        help='refl_send_dest', required=True
    )
    parser.add_argument(
        '--send_refl_sidlist', dest='send_refl_sidlist', action='store',
        help='send_refl_sidlist', required=True
    )
    parser.add_argument(
        '--refl_send_sidlist', dest='refl_send_sidlist', action='store',
        help='refl_send_sidlist', required=True
    )
    # parser.add_argument(
    #     '--send_in_interfaces', dest='send_in_interfaces', action='store',
    #     help='send_in_interfaces'
    # )
    # parser.add_argument(
    #     '--refl_in_interfaces', dest='refl_in_interfaces', action='store',
    #     help='refl_in_interfaces'
    # )
    # parser.add_argument(
    #     '--send_out_interfaces', dest='send_out_interfaces', action='store',
    #     help='send_out_interfaces'
    # )
    # parser.add_argument(
    #     '--refl_out_interfaces', dest='refl_out_interfaces', action='store',
    #     help='refl_out_interfaces'
    # )
    parser.add_argument(
        '--measurement_protocol', dest='measurement_protocol', action='store',
        help='measurement_protocol', default='TWAMP'
    )
    parser.add_argument(
        '--measurement_type', dest='measurement_type', action='store',
        help='measurement_type', default='LOSS'
    )
    parser.add_argument(
        '--authentication_mode', dest='authentication_mode', action='store',
        help='authentication_mode', default='HMAC_SHA_256'
    )
    parser.add_argument(
        '--authentication_key', dest='authentication_key', action='store',
        help='authentication_key', default=None
    )
    parser.add_argument(
        '--timestamp_format', dest='timestamp_format', action='store',
        help='timestamp_format', default='PTPv2'
    )
    parser.add_argument(
        '--delay_measurement_mode', dest='delay_measurement_mode',
        action='store', help='delay_measurement_mode', default='OneWay'
    )
    parser.add_argument(
        '--padding_mbz', dest='padding_mbz', action='store',
        help='padding_mbz', default=0
    )
    parser.add_argument(
        '--loss_measurement_mode', dest='loss_measurement_mode',
        action='store', help='loss_measurement_mode', default='Inferred'
    )
    parser.add_argument(
        '--measure_id', dest='measure_id', action='store',
        help='measure_id', required=True, type=int
    )
    parser.add_argument(
        '--send_refl_localseg', dest='send_refl_localseg', action='store',
        help='send_refl_localseg', default=None
    )
    parser.add_argument(
        '--refl_send_localseg', dest='refl_send_localseg', action='store',
        help='refl_send_localseg', default=None
    )
    parser.add_argument(
        '--force', dest='force', action='store_true',
        help='force'
    )
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Activate debug logs'
    )
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# Parse options
def parse_arguments_get_experiment_results(prog=sys.argv[0], args=None):
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    parser.add_argument(
        '--sender-ip', dest='sender_ip', action='store',
        required=True, help='IP of the gRPC server of the sender'
    )
    parser.add_argument(
        '--sender-port', dest='sender_port', action='store',
        required=True, help='Port of the gRPC server of the sender'
    )
    parser.add_argument(
        '--reflector-ip', dest='reflector_ip', action='store',
        required=True, help='IP of the gRPC server of the reflector'
    )
    parser.add_argument(
        '--reflector-port', dest='reflector_port', action='store',
        required=True, help='Port of the gRPC server of the reflector'
    )
    parser.add_argument(
        '-s', '--secure', action='store_true', help='Activate secure mode'
    )
    parser.add_argument(
        '-c', '--server-cert', dest='server_cert', action='store',
        default=DEFAULT_CERTIFICATE, help='CA certificate file'
    )
    parser.add_argument(
        '--send_refl_sidlist', dest='send_refl_sidlist', action='store',
        help='send_refl_sidlist', required=True
    )
    parser.add_argument(
        '--refl_send_sidlist', dest='refl_send_sidlist', action='store',
        help='refl_send_sidlist', required=True
    )
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Activate debug logs'
    )
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# Parse options
def parse_arguments_stop_experiment(prog=sys.argv[0], args=None):
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    parser.add_argument(
        '--sender-ip', dest='sender_ip', action='store',
        required=True, help='IP of the gRPC server of the sender'
    )
    parser.add_argument(
        '--sender-port', dest='sender_port', action='store',
        required=True, help='Port of the gRPC server of the sender'
    )
    parser.add_argument(
        '--reflector-ip', dest='reflector_ip', action='store',
        required=True, help='IP of the gRPC server of the reflector'
    )
    parser.add_argument(
        '--reflector-port', dest='reflector_port', action='store',
        required=True, help='Port of the gRPC server of the reflector'
    )
    parser.add_argument(
        '-s', '--secure', action='store_true', help='Activate secure mode'
    )
    parser.add_argument(
        '-c', '--server-cert', dest='server_cert', action='store',
        default=DEFAULT_CERTIFICATE, help='CA certificate file'
    )
    parser.add_argument(
        '--send_refl_dest', dest='send_refl_dest', action='store',
        help='send_refl_dest', required=True
    )
    parser.add_argument(
        '--refl_send_dest', dest='refl_send_dest', action='store',
        help='refl_send_dest', required=True
    )
    parser.add_argument(
        '--send_refl_sidlist', dest='send_refl_sidlist', action='store',
        help='send_refl_sidlist', required=True
    )
    parser.add_argument(
        '--refl_send_sidlist', dest='refl_send_sidlist', action='store',
        help='refl_send_sidlist', required=True
    )
    parser.add_argument(
        '--send_refl_localseg', dest='send_refl_localseg', action='store',
        help='send_refl_localseg'
    )
    parser.add_argument(
        '--refl_send_localseg', dest='refl_send_localseg', action='store',
        help='refl_send_localseg'
    )
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Activate debug logs'
    )
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args
