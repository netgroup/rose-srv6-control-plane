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
# Collection of SRv6 Performance Measurement utilities for the Controller CLI
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
SRv6 PM utilities for Controller CLI.
'''

# General imports
import logging
import sys
from argparse import ArgumentParser

# Controller dependencies
from controller import srv6_pm, utils
from controller.cli import utils as cli_utils

# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)

# Default CA certificate path
DEFAULT_CERTIFICATE = 'cert_server.pem'


def set_configuration(sender, reflector,
                      sender_port, reflector_port, send_udp_port,
                      refl_udp_port, interval_duration, delay_margin,
                      number_of_color, pm_driver):
    '''
    Configure a node for a SRv6 Performance Measurement experiment.

    :param sender: The IP address of the gRPC server on the sender.
    :type sender: str
    :param sender_port: The port of the gRPC server on the sender.
    :type sender_port: int
    :param reflector: The IP address of the gRPC server on the reflector.
    :type reflector: str
    :param reflector_port: The port of the gRPC server on the reflector.
    :type reflector_port: int
    :param send_udp_port: The destination UDP port used by the sender
    :type send_udp_port: int
    :param refl_udp_port: The destination UDP port used by the reflector
    :type refl_udp_port: int
    :param interval_duration: The duration of the interval
    :type interval_duration: int
    :param delay_margin: The delay margin
    :type delay_margin: int
    :param number_of_color: The number of the color
    :type number_of_color: int
    :param pm_driver: The driver to use for the experiments (i.e. eBPF or
                      IPSet).
    :type pm_driver: str
    '''
    # pylint: disable=too-many-arguments

    # Establish a gRPC Channel to the sender and a gRPC Channel to the
    # reflector
    logger.debug('Trying to establish a connection to the sender %s on '
                 'port %s', sender, sender_port)
    logger.debug('Trying to establish a connection to the reflector %s on '
                 'port %s', reflector, reflector_port)
    with utils.get_grpc_session(sender, sender_port) as sender_channel, \
            utils.get_grpc_session(reflector, reflector_port) as refl_channel:
        # Send the set_configuration request
        logger.debug('Trying to set the configuration')
        res = srv6_pm.set_configuration(
            sender_channel=sender_channel,
            reflector_channel=refl_channel,
            send_udp_port=send_udp_port,
            refl_udp_port=refl_udp_port,
            interval_duration=interval_duration,
            delay_margin=delay_margin,
            number_of_color=number_of_color,
            pm_driver=pm_driver
        )
        # Convert the status code to a human-readable textual description and
        # print the description
        logger.info('Set configuration returned %s - %s\n\n', res,
                    utils.STATUS_CODE_TO_DESC[res])


def reset_configuration(sender, reflector,
                        sender_port, reflector_port):
    '''
    Reset the configuration for a SRv6 Performance Measurement experiment.

    :param sender: The IP address of the gRPC server on the sender.
    :type sender: str
    :param sender_port: The port of the gRPC server on the sender.
    :type sender_port: int
    :param reflector: The IP address of the gRPC server on the reflector.
    :type reflector: str
    :param reflector_port: The port of the gRPC server on the reflector.
    :type reflector_port: int
    '''
    # Establish a gRPC Channel to the sender and a gRPC Channel to the
    # reflector
    logger.debug('Trying to establish a connection to the sender %s on '
                 'port %s', sender, sender_port)
    logger.debug('Trying to establish a connection to the reflector %s on '
                 'port %s', reflector, reflector_port)
    with utils.get_grpc_session(sender, sender_port) as sender_channel, \
            utils.get_grpc_session(reflector, reflector_port) as refl_channel:
        # Send the reset_configuration request
        logger.debug('Trying to reset the configuration')
        res = srv6_pm.reset_configuration(
            sender_channel=sender_channel,
            reflector_channel=refl_channel
        )
        # Convert the status code to a human-readable textual description and
        # print the description
        logger.info('Reset configuration returned %s - %s\n\n', res,
                    utils.STATUS_CODE_TO_DESC[res])


def start_experiment(sender, reflector,
                     sender_port, reflector_port, send_refl_dest,
                     refl_send_dest, send_refl_sidlist, refl_send_sidlist,
                     measurement_protocol, measurement_type,
                     authentication_mode, authentication_key,
                     timestamp_format, delay_measurement_mode,
                     padding_mbz, loss_measurement_mode, measure_id=None,
                     send_refl_localseg=None, refl_send_localseg=None,
                     force=False):
    '''
    Start an experiment.

    :param sender: The IP address of the gRPC server on the sender.
    :type sender: str
    :param sender_port: The port of the gRPC server on the sender.
    :type sender_port: int
    :param reflector: The IP address of the gRPC server on the reflector.
    :type reflector: str
    :param reflector_port: The port of the gRPC server on the reflector.
    :type reflector_port: int
    :param send_refl_dest: The destination of the SRv6 path
                           sender->reflector
    :type send_refl_dest: str
    :param refl_send_dest: The destination of the SRv6 path
                           reflector->sender
    :type refl_send_dest: str
    :param send_refl_sidlist: The SID list to be used for the path
                              sender->reflector
    :type send_refl_sidlist:  list
    :param refl_send_sidlist: The SID list to be used for the path
                              reflector->sender
    :type refl_send_sidlist: list
    :param measurement_protocol: The measurement protocol (i.e. TWAMP
                                 or STAMP)
    :type measurement_protocol: str
    :param measurement_type: The measurement type (i.e. delay or loss)
    :type measurement_type: str
    :param authentication_mode: The authentication mode (i.e. HMAC_SHA_256)
    :type authentication_mode: str
    :param authentication_key: The authentication key
    :type authentication_key: str
    :param timestamp_format: The Timestamp Format (i.e. PTPv2 or NTP)
    :type timestamp_format: str
    :param delay_measurement_mode: Delay measurement mode (i.e. one-way,
                                   two-way or loopback mode)
    :type delay_measurement_mode: str
    :param padding_mbz: The padding size
    :type padding_mbz: int
    :param loss_measurement_mode: The loss measurement mode (i.e. Inferred
                                  or Direct mode)
    :type loss_measurement_mode: str
    :param measure_id: Identifier for the experiment (default is None).
                        automatically generated.
    :type measure_id: int, optional
    :param send_refl_localseg: The local segment associated to the End.DT6
                               (decap) function for the path
                               sender->reflector (default is None).
                               If the argument 'send_localseg' isn't passed
                               in, the seg6local End.DT6 route is not created.
    :type send_refl_localseg: str, optional
    :param refl_send_localseg: The local segment associated to the End.DT6
                               (decap) function for the path
                               reflector->sender (default is None).
                               If the argument 'send_localseg' isn't passed
                               in, the seg6local End.DT6 route is not created.
    :type refl_send_localseg: str, optional
    :param force: If set, force the controller to start an experiment if a
                  SRv6 path for the destination already exists. The old SRv6
                  path is replaced with the new one (default is False).
    :type force: bool, optional
    '''
    # pylint: disable=too-many-arguments, too-many-locals
    #
    # Establish a gRPC Channel to the sender and a gRPC Channel to the
    # reflector
    logger.debug('Trying to establish a connection to the sender %s on '
                 'port %s', sender, sender_port)
    logger.debug('Trying to establish a connection to the reflector %s on '
                 'port %s', reflector, reflector_port)
    with utils.get_grpc_session(sender, sender_port) as sender_channel, \
            utils.get_grpc_session(reflector, reflector_port) as refl_channel:
        # Send the start_experiment request
        res = srv6_pm.start_experiment(
            sender_channel=sender_channel,
            reflector_channel=refl_channel,
            send_refl_dest=send_refl_dest,
            refl_send_dest=refl_send_dest,
            send_refl_sidlist=send_refl_sidlist.split(','),
            refl_send_sidlist=refl_send_sidlist.split(','),
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
        # Convert the status code to a human-readable textual description and
        # print the description
        logger.info('start_experiment returned %s - %s\n\n', res,
                    utils.STATUS_CODE_TO_DESC[res])


def get_experiment_results(sender, reflector,
                           sender_port, reflector_port,
                           send_refl_sidlist, refl_send_sidlist):
    '''
    Get the results of a running experiment.

    :param sender: The IP address of the gRPC server on the sender.
    :type sender: str
    :param sender_port: The port of the gRPC server on the sender.
    :type sender_port: int
    :param reflector: The IP address of the gRPC server on the reflector.
    :type reflector: str
    :param reflector_port: The port of the gRPC server on the reflector.
    :type reflector_port: int
    :param send_refl_sidlist: The SID list to be used for the path
                              sender->reflector
    :type send_refl_sidlist: list
    :param refl_send_sidlist: The SID list to be used for the path
                              reflector->sender
    :type refl_send_sidlist: list
    :raises controller.utils.NoMeasurementDataAvailableError: If an error
                                                              occurred while
                                                              retrieving the
                                                              results.
    '''
    # pylint: disable=too-many-arguments
    #
    # Establish a gRPC Channel to the sender and a gRPC Channel to the
    # reflector
    logger.debug('Trying to establish a connection to the sender %s on '
                 'port %s', sender, sender_port)
    logger.debug('Trying to establish a connection to the reflector %s on '
                 'port %s', reflector, reflector_port)
    with utils.get_grpc_session(sender, sender_port) as sender_channel, \
            utils.get_grpc_session(reflector, reflector_port) as refl_channel:
        # Get and print the experiment results
        logger.info(srv6_pm.get_experiment_results(
            sender_channel=sender_channel,
            reflector_channel=refl_channel,
            send_refl_sidlist=send_refl_sidlist.split(','),
            refl_send_sidlist=refl_send_sidlist.split(',')
        ))


def stop_experiment(sender, reflector,
                    sender_port, reflector_port, send_refl_dest,
                    refl_send_dest, send_refl_sidlist, refl_send_sidlist,
                    send_refl_localseg=None, refl_send_localseg=None):
    '''
    Stop a running experiment.

    :param sender: The IP address of the gRPC server on the sender.
    :type sender: str
    :param sender_port: The port of the gRPC server on the sender.
    :type sender_port: int
    :param reflector: The IP address of the gRPC server on the reflector.
    :type reflector: str
    :param reflector_port: The port of the gRPC server on the reflector.
    :type reflector_port: int
    :param send_refl_dest: The destination of the SRv6 path
                           sender->reflector
    :type send_refl_dest: str
    :param refl_send_dest: The destination of the SRv6 path
                           reflector->sender
    :type refl_send_dest: str
    :param send_refl_sidlist: The SID list used for the path
                              sender->reflector
    :type send_refl_sidlist: list
    :param refl_send_sidlist: The SID list used for the path
                              reflector->sender
    :type refl_send_sidlist: list
    :param send_refl_localseg: The local segment associated to the End.DT6
                               (decap) function for the path sender->reflector
                               (default is None). If the argument
                               'send_localseg' isn't passed in, the seg6local
                               End.DT6 route is not removed.
    :type send_refl_localseg: str, optional
    :param refl_send_localseg: The local segment associated to the End.DT6
                              (decap) function for the path reflector->sender
                              (default is None). If the argument
                              'send_localseg' isn't passed in, the seg6local
                              End.DT6 route is not removed.
    :type refl_send_localseg: str, optional
    '''
    # pylint: disable=too-many-arguments
    #
    # Establish a gRPC Channel to the sender and a gRPC Channel to the
    # reflector
    logger.debug('Trying to establish a connection to the sender %s on '
                 'port %s', sender, sender_port)
    logger.debug('Trying to establish a connection to the reflector %s on '
                 'port %s', reflector, reflector_port)
    with utils.get_grpc_session(sender, sender_port) as sender_channel, \
            utils.get_grpc_session(reflector, reflector_port) as refl_channel:
        # Send the stop_experiment request
        res = srv6_pm.stop_experiment(
            sender_channel=sender_channel,
            reflector_channel=refl_channel,
            send_refl_dest=send_refl_dest,
            refl_send_dest=refl_send_dest,
            send_refl_sidlist=send_refl_sidlist.split(','),
            refl_send_sidlist=refl_send_sidlist.split(','),
            send_refl_localseg=send_refl_localseg,
            refl_send_localseg=refl_send_localseg
        )
        # Convert the status code to a human-readable textual description and
        # print the description
        logger.info('start_experiment returned %s - %s\n\n', res,
                    utils.STATUS_CODE_TO_DESC[res])


def args_set_configuration():
    '''
    Command-line arguments for the set_configuration command.
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library.

    :return: The list of the arguments.
    :rtype: list
    '''
    return [
        {
            'args': ['--sender-ip'],
            'kwargs': {'dest': 'sender_ip', 'action': 'store',
                       'required': True,
                       'help': 'IP of the gRPC server of the sender'}
        }, {
            'args': ['--sender-port'],
            'kwargs': {'dest': 'sender_port', 'action': 'store',
                       'required': True,
                       'help': 'Port of the gRPC server of the sender'}
        }, {
            'args': ['--reflector-ip'],
            'kwargs': {'dest': 'reflector_ip', 'action': 'store',
                       'required': True,
                       'help': 'IP of the gRPC server of the reflector'}
        }, {
            'args': ['--reflector-port'],
            'kwargs': {'dest': 'reflector_port', 'action': 'store',
                       'required': True,
                       'help': 'Port of the gRPC server of the reflector'}
        }, {
            'args': ['--secure'],
            'kwargs': {'action': 'store_true', 'help': 'Activate secure mode'}
        }, {
            'args': ['--server-cert'],
            'kwargs': {'dest': 'server_cert', 'action': 'store',
                       'default': DEFAULT_CERTIFICATE,
                       'help': 'CA certificate file'},
            'is_path': True
        }, {
            'args': ['--send_in_interfaces'],
            'kwargs': {'dest': 'send_in_interfaces', 'action': 'store',
                       'help': 'send_in_interfaces'}
        }, {
            'args': ['--refl_in_interfaces'],
            'kwargs': {'dest': 'refl_in_interfaces', 'action': 'store',
                       'help': 'refl_in_interfaces'}
        }, {
            'args': ['--send_out_interfaces'],
            'kwargs': {'dest': 'send_out_interfaces', 'action': 'store',
                       'help': 'send_out_interfaces'}
        }, {
            'args': ['--refl_out_interfaces'],
            'kwargs': {'dest': 'refl_out_interfaces', 'action': 'store',
                       'help': 'refl_out_interfaces'}
        }, {
            'args': ['--send_udp_port'],
            'kwargs': {'dest': 'send_udp_port', 'action': 'store',
                       'help': 'send_udp_port', 'type': int}
        }, {
            'args': ['--refl_udp_port'],
            'kwargs': {'dest': 'refl_udp_port', 'action': 'store',
                       'help': 'refl_udp_port', 'type': int}
        }, {
            'args': ['--interval_duration'],
            'kwargs': {'dest': 'interval_duration', 'action': 'store',
                       'help': 'interval_duration', 'type': int}
        }, {
            'args': ['--delay_margin'],
            'kwargs': {'dest': 'delay_margin', 'action': 'store',
                       'help': 'delay_margin', 'type': int}
        }, {
            'args': ['--number_of_color'],
            'kwargs': {'dest': 'number_of_color', 'action': 'store',
                       'help': 'number_of_color', 'type': int}
        }, {
            'args': ['--pm_driver'],
            'kwargs': {'dest': 'pm_driver', 'action': 'store',
                       'help': 'pm_driver'}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_set_configuration(prog=sys.argv[0], args=None):
    '''
    Command-line arguments parser for set_configuration function.

    :param prog: The name of the program (default: sys.argv[0])
    :type prog: str, optional
    :param args: List of strings to parse. If None, the list is taken from
                 sys.argv (default: None).
    :type args: list, optional
    :return: Return the namespace populated with the argument strings.
    :rtype: argparse.Namespace
    '''
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    # Add the arguments to the parser
    for param in args_set_configuration():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for set_configuration
def complete_set_configuration(text, prev_text):
    '''
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.

    :param text: The text to be auto-completed.
    :type text: str
    :param prev_text: The argument that comes before the text to be
                      auto-completed.
    :type prev_text: str
    :return: A list containing the possible words for the auto-completion.
    :rtype: list
    '''
    # Get the arguments for set_configuration
    args = args_set_configuration()
    # Paths auto-completion
    if prev_text is not None:
        # Get the list of the arguments requiring a path
        path_args = [arg
                     for param in args
                     for arg in param['args']
                     if param.get('is_path', False)]
        # Check whether the previous argument requires a path or not
        if prev_text in path_args:
            # Auto-complete the path and return the results
            return cli_utils.complete_path(text)
    # Argument is not a path
    #
    # Get the list of the arguments supported by the command
    args = [arg for param in args for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args


def args_reset_configuration():
    '''
    Command-line arguments for the reset_configuration command.
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library.

    :return: The list of the arguments.
    :rtype: list
    '''
    return [
        {
            'args': ['--sender-ip'],
            'kwargs': {'dest': 'sender_ip', 'action': 'store',
                       'required': True,
                       'help': 'IP of the gRPC server of the sender'}
        }, {
            'args': ['--sender-port'],
            'kwargs': {'dest': 'sender_port', 'action': 'store',
                       'required': True,
                       'help': 'Port of the gRPC server of the sender'}
        }, {
            'args': ['--reflector-ip'],
            'kwargs': {'dest': 'reflector_ip', 'action': 'store',
                       'required': True,
                       'help': 'IP of the gRPC server of the reflector'}
        }, {
            'args': ['--reflector-port'],
            'kwargs': {'dest': 'reflector_port', 'action': 'store',
                       'required': True,
                       'help': 'Port of the gRPC server of the reflector'}
        }, {
            'args': ['--secure'],
            'kwargs': {'action': 'store_true', 'help': 'Activate secure mode'}
        }, {
            'args': ['--server-cert'],
            'kwargs': {'dest': 'server_cert', 'action': 'store',
                       'default': DEFAULT_CERTIFICATE,
                       'help': 'CA certificate file'},
            'is_path': True
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_reset_configuration(prog=sys.argv[0], args=None):
    '''
    Command-line arguments parser for reset_configuration function.

    :param prog: The name of the program (default: sys.argv[0])
    :type prog: str, optional
    :param args: List of strings to parse. If None, the list is taken from
                 sys.argv (default: None).
    :type args: list, optional
    :return: Return the namespace populated with the argument strings.
    :rtype: argparse.Namespace
    '''
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    # Add the arguments to the parser
    for param in args_reset_configuration():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for reset_configuration
def complete_reset_configuration(text, prev_text):
    '''
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.

    :param text: The text to be auto-completed.
    :type text: str
    :param prev_text: The argument that comes before the text to be
                      auto-completed.
    :type prev_text: str
    :return: A list containing the possible words for the auto-completion.
    :rtype: list
    '''
    # Get the arguments for reset_configuration
    args = args_reset_configuration()
    # Paths auto-completion
    if prev_text is not None:
        # Get the list of the arguments requiring a path
        path_args = [arg
                     for param in args
                     for arg in param['args']
                     if param.get('is_path', False)]
        # Check whether the previous argument requires a path or not
        if prev_text in path_args:
            # Auto-complete the path and return the results
            return cli_utils.complete_path(text)
    # Argument is not a path
    #
    # Get the list of the arguments supported by the command
    args = [arg for param in args for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args


def args_start_experiment():
    '''
    Command-line arguments for the start_experiment command.
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
    the argparse library.

    :return: The list of the arguments.
    :rtype: list
    '''
    return [
        {
            'args': ['--sender-ip'],
            'kwargs': {'dest': 'sender_ip', 'action': 'store',
                       'required': True,
                       'help': 'IP of the gRPC server of the sender'}
        }, {
            'args': ['--sender-port'],
            'kwargs': {'dest': 'sender_port', 'action': 'store',
                       'required': True,
                       'help': 'Port of the gRPC server of the sender'}
        }, {
            'args': ['--reflector-ip'],
            'kwargs': {'dest': 'reflector_ip', 'action': 'store',
                       'required': True,
                       'help': 'IP of the gRPC server of the reflector'}
        }, {
            'args': ['--reflector-port'],
            'kwargs': {'dest': 'reflector_port', 'action': 'store',
                       'required': True,
                       'help': 'Port of the gRPC server of the reflector'}
        }, {
            'args': ['--secure'],
            'kwargs': {'action': 'store_true',
                       'help': 'Activate secure mode'}
        }, {
            'args': ['--server-cert'],
            'kwargs': {'dest': 'server_cert', 'action': 'store',
                       'default': DEFAULT_CERTIFICATE,
                       'help': 'CA certificate file'},
            'is_path': True
        }, {
            'args': ['--send_refl_dest'],
            'kwargs': {'dest': 'send_refl_dest', 'action': 'store',
                       'help': 'send_refl_dest', 'required': True}
        }, {
            'args': ['--refl_send_dest'],
            'kwargs': {'dest': 'refl_send_dest', 'action': 'store',
                       'help': 'refl_send_dest', 'required': True}
        }, {
            'args': ['--send_refl_sidlist'],
            'kwargs': {'dest': 'send_refl_sidlist', 'action': 'store',
                       'help': 'send_refl_sidlist', 'required': True}
        }, {
            'args': ['--refl_send_sidlist'],
            'kwargs': {'dest': 'refl_send_sidlist', 'action': 'store',
                       'help': 'refl_send_sidlist', 'required': True}
        }, {
            'args': ['--measurement_protocol'],
            'kwargs': {'dest': 'measurement_protocol', 'action': 'store',
                       'help': 'measurement_protocol', 'default': 'TWAMP'}
        }, {
            'args': ['--measurement_type'],
            'kwargs': {'dest': 'measurement_type', 'action': 'store',
                       'help': 'measurement_type', 'default': 'LOSS'}
        }, {
            'args': ['--authentication_mode'],
            'kwargs': {'dest': 'authentication_mode', 'action': 'store',
                       'help': 'authentication_mode',
                       'default': 'HMAC_SHA_256'}
        }, {
            'args': ['--authentication_key'],
            'kwargs': {'dest': 'authentication_key', 'action': 'store',
                       'help': 'authentication_key', 'default': None}
        }, {
            'args': ['--timestamp_format'],
            'kwargs': {'dest': 'timestamp_format', 'action': 'store',
                       'help': 'timestamp_format', 'default': 'PTPv2'}
        }, {
            'args': ['--delay_measurement_mode'],
            'kwargs': {'dest': 'delay_measurement_mode',
                       'action': 'store',
                       'help': 'delay_measurement_mode', 'default': 'OneWay'}
        }, {
            'args': ['--padding_mbz'],
            'kwargs': {'dest': 'padding_mbz', 'action': 'store',
                       'help': 'padding_mbz', 'default': 0}
        }, {
            'args': ['--loss_measurement_mode'],
            'kwargs': {'dest': 'loss_measurement_mode',
                       'action': 'store',
                       'help': 'loss_measurement_mode', 'default': 'Inferred'}
        }, {
            'args': ['--measure_id'],
            'kwargs': {'dest': 'measure_id', 'action': 'store',
                       'help': 'measure_id', 'required': True, 'type': int}
        }, {
            'args': ['--send_refl_localseg'],
            'kwargs': {'dest': 'send_refl_localseg', 'action': 'store',
                       'help': 'send_refl_localseg', 'default': None}
        }, {
            'args': ['--refl_send_localseg'],
            'kwargs': {'dest': 'refl_send_localseg', 'action': 'store',
                       'help': 'refl_send_localseg', 'default': None}
        }, {
            'args': ['--force'],
            'kwargs': {'dest': 'force', 'action': 'store_true',
                       'help': 'force'}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_start_experiment(prog=sys.argv[0], args=None):
    '''
    Command-line arguments parser for start_experiment function.

    :param prog: The name of the program (default: sys.argv[0])
    :type prog: str, optional
    :param args: List of strings to parse. If None, the list is taken from
                 sys.argv (default: None).
    :type args: list, optional
    :return: Return the namespace populated with the argument strings.
    :rtype: argparse.Namespace
    '''
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    # Add the arguments to the parser
    for param in args_start_experiment():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for start_experiment
def complete_start_experiment(text, prev_text):
    '''
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.

    :param text: The text to be auto-completed.
    :type text: str
    :param prev_text: The argument that comes before the text to be
                      auto-completed.
    :type prev_text: str
    :return: A list containing the possible words for the auto-completion.
    :rtype: list
    '''
    # Get the arguments for start_experiment
    args = args_start_experiment()
    # Paths auto-completion
    if prev_text is not None:
        # Get the list of the arguments requiring a path
        path_args = [arg
                     for param in args
                     for arg in param['args']
                     if param.get('is_path', False)]
        # Check whether the previous argument requires a path or not
        if prev_text in path_args:
            # Auto-complete the path and return the results
            return cli_utils.complete_path(text)
    # Argument is not a path
    #
    # Get the list of the arguments supported by the command
    args = [arg for param in args for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args


def args_get_experiment_results():
    '''
    Command-line arguments for the get_experiment_results command.
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library.

    :return: The list of the arguments.
    :rtype: list
    '''
    return [
        {
            'args': ['--sender-ip'],
            'kwargs': {'dest': 'sender_ip', 'action': 'store',
                       'required': True,
                       'help': 'IP of the gRPC server of the sender'}
        }, {
            'args': ['--sender-port'],
            'kwargs': {'dest': 'sender_port', 'action': 'store',
                       'required': True,
                       'help': 'Port of the gRPC server of the sender'}
        }, {
            'args': ['--reflector-ip'],
            'kwargs': {'dest': 'reflector_ip', 'action': 'store',
                       'required': True,
                       'help': 'IP of the gRPC server of the reflector'}
        }, {
            'args': ['--reflector-port'],
            'kwargs': {'dest': 'reflector_port', 'action': 'store',
                       'required': True,
                       'help': 'Port of the gRPC server of the reflector'}
        }, {
            'args': ['--secure'],
            'kwargs': {'action': 'store_true', 'help': 'Activate secure mode'}
        }, {
            'args': ['--server-cert'],
            'kwargs': {'dest': 'server_cert', 'action': 'store',
                       'default': DEFAULT_CERTIFICATE,
                       'help': 'CA certificate file'},
            'is_path': True
        }, {
            'args': ['--send_refl_sidlist'],
            'kwargs': {'dest': 'send_refl_sidlist', 'action': 'store',
                       'help': 'send_refl_sidlist', 'required': True}
        }, {
            'args': ['--refl_send_sidlist'],
            'kwargs': {'dest': 'refl_send_sidlist', 'action': 'store',
                       'help': 'refl_send_sidlist', 'required': True}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_get_experiment_results(prog=sys.argv[0], args=None):
    '''
    Command-line arguments parser for get_experiments_results function.

    :param prog: The name of the program (default: sys.argv[0])
    :type prog: str, optional
    :param args: List of strings to parse. If None, the list is taken from
                 sys.argv (default: None).
    :type args: list, optional
    :return: Return the namespace populated with the argument strings.
    :rtype: argparse.Namespace
    '''
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    # Add the arguments to the parser
    for param in args_get_experiment_results():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for get_experiment_results
def complete_get_experiment_results(text, prev_text):
    '''
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.

    :param text: The text to be auto-completed.
    :type text: str
    :param prev_text: The argument that comes before the text to be
                      auto-completed.
    :type prev_text: str
    :return: A list containing the possible words for the auto-completion.
    :rtype: list
    '''
    # Get the arguments for get_experiment_results
    args = args_get_experiment_results()
    # Paths auto-completion
    if prev_text is not None:
        # Get the list of the arguments requiring a path
        path_args = [arg
                     for param in args
                     for arg in param['args']
                     if param.get('is_path', False)]
        # Check whether the previous argument requires a path or not
        if prev_text in path_args:
            # Auto-complete the path and return the results
            return cli_utils.complete_path(text)
    # Argument is not a path
    #
    # Get the list of the arguments supported by the command
    args = [arg for param in args
            for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args


def args_stop_experiment():
    '''
    Command-line arguments for the stop_experiment command.
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library.

    :return: The list of the arguments.
    :rtype: list
    '''
    return [
        {
            'args': ['--sender-ip'],
            'kwargs': {'dest': 'sender_ip', 'action': 'store',
                       'required': True,
                       'help': 'IP of the gRPC server of the sender'}
        }, {
            'args': ['--sender-port'],
            'kwargs': {'dest': 'sender_port', 'action': 'store',
                       'required': True,
                       'help': 'Port of the gRPC server of the sender'}
        }, {
            'args': ['--reflector-ip'],
            'kwargs': {'dest': 'reflector_ip', 'action': 'store',
                       'required': True,
                       'help': 'IP of the gRPC server of the reflector'}
        }, {
            'args': ['--reflector-port'],
            'kwargs': {'dest': 'reflector_port', 'action': 'store',
                       'required': True,
                       'help': 'Port of the gRPC server of the reflector'}
        }, {
            'args': ['--secure'],
            'kwargs': {'action': 'store_true', 'help': 'Activate secure mode'}
        }, {
            'args': ['--server-cert'],
            'kwargs': {'dest': 'server_cert', 'action': 'store',
                       'default': DEFAULT_CERTIFICATE,
                       'help': 'CA certificate file'},
            'is_path': True
        }, {
            'args': ['--send_refl_dest'],
            'kwargs': {'dest': 'send_refl_dest', 'action': 'store',
                       'help': 'send_refl_dest', 'required': True}
        }, {
            'args': ['--refl_send_dest'],
            'kwargs': {'dest': 'refl_send_dest', 'action': 'store',
                       'help': 'refl_send_dest', 'required': True}
        }, {
            'args': ['--send_refl_sidlist'],
            'kwargs': {'dest': 'send_refl_sidlist', 'action': 'store',
                       'help': 'send_refl_sidlist', 'required': True}
        }, {
            'args': ['--refl_send_sidlist'],
            'kwargs': {'dest': 'refl_send_sidlist', 'action': 'store',
                       'help': 'refl_send_sidlist', 'required': True}
        }, {
            'args': ['--send_refl_localseg'],
            'kwargs': {'dest': 'send_refl_localseg', 'action': 'store',
                       'help': 'send_refl_localseg'}
        }, {
            'args': ['--refl_send_localseg'],
            'kwargs': {'dest': 'refl_send_localseg', 'action': 'store',
                       'help': 'refl_send_localseg'}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_stop_experiment(prog=sys.argv[0], args=None):
    '''
    Command-line arguments parser for stop_experiment function.

    :param prog: The name of the program (default: sys.argv[0])
    :type prog: str, optional
    :param args: List of strings to parse. If None, the list is taken from
                 sys.argv (default: None).
    :type args: list, optional
    :return: Return the namespace populated with the argument strings.
    :rtype: argparse.Namespace
    '''
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    # Add the arguments to the parser
    for param in args_stop_experiment():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for stop_experiment
def complete_stop_experiment(text, prev_text):
    '''
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.

    :param text: The text to be auto-completed.
    :type text: str
    :param prev_text: The argument that comes before the text to be
                      auto-completed.
    :type prev_text: str
    :return: A list containing the possible words for the auto-completion.
    :rtype: list
    '''
    # Get the arguments for stop_experiment
    args = args_stop_experiment()
    # Paths auto-completion
    if prev_text is not None:
        # Get the list of the arguments requiring a path
        path_args = [arg
                     for param in args
                     for arg in param['args']
                     if param.get('is_path', False)]
        # Check whether the previous argument requires a path or not
        if prev_text in path_args:
            # Auto-complete the path and return the results
            return cli_utils.complete_path(text)
    # Argument is not a path
    #
    # Get the list of the arguments supported by the command
    args = [arg for param in args for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args
