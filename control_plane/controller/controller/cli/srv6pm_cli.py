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
# Implementation of a CLI for the SRv6 Controller
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


"""SRv6 PM utilities for Controller CLI"""

import sys
from argparse import ArgumentParser

# Controller dependencies
from controller import srv6_pm, utils
from controller.cli import utils as cli_utils

# Default CA certificate path
DEFAULT_CERTIFICATE = 'cert_server.pem'


def set_configuration(sender, reflector,
                      sender_port, reflector_port, send_udp_port,
                      refl_udp_port, interval_duration, delay_margin,
                      number_of_color, pm_driver):
    """Configure a node"""

    # pylint: disable=too-many-arguments

    with utils.get_grpc_session(sender, sender_port) as sender_channel, \
            utils.get_grpc_session(reflector, reflector_port) as refl_channel:
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
        if res == 0:
            print('OK')
        else:
            print('Error')


def reset_configuration(sender, reflector,
                        sender_port, reflector_port):
    """Clear node configuration"""

    with utils.get_grpc_session(sender, sender_port) as sender_channel, \
            utils.get_grpc_session(reflector, reflector_port) as refl_channel:
        res = srv6_pm.reset_configuration(
            sender_channel=sender_channel,
            reflector_channel=refl_channel
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
    """Start an experiment"""

    # pylint: disable=too-many-arguments, too-many-locals

    with utils.get_grpc_session(sender, sender_port) as sender_channel, \
            utils.get_grpc_session(reflector, reflector_port) as refl_channel:
        res = srv6_pm.start_experiment(
            sender_channel=sender_channel,
            reflector_channel=refl_channel,
            send_refl_dest=send_refl_dest,
            refl_send_dest=refl_send_dest,
            send_refl_sidlist=send_refl_sidlist.split(','),
            refl_send_sidlist=refl_send_sidlist.split(','),
            # Interfaces moved to set_configuration
            # send_in_interfaces=send_in_interfaces,
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
    """Get the results of a running experiment"""

    # pylint: disable=too-many-arguments

    with utils.get_grpc_session(sender, sender_port) as sender_channel, \
            utils.get_grpc_session(reflector, reflector_port) as refl_channel:
        print(srv6_pm.get_experiment_results(
            sender_channel=sender_channel,
            reflector_channel=refl_channel,
            send_refl_sidlist=send_refl_sidlist.split(','),
            refl_send_sidlist=refl_send_sidlist.split(',')
        ))


def stop_experiment(sender, reflector,
                    sender_port, reflector_port, send_refl_dest,
                    refl_send_dest, send_refl_sidlist, refl_send_sidlist,
                    send_refl_localseg=None, refl_send_localseg=None):
    """Stop a running experiment"""

    # pylint: disable=too-many-arguments

    with utils.get_grpc_session(sender, sender_port) as sender_channel, \
            utils.get_grpc_session(reflector, reflector_port) as refl_channel:
        srv6_pm.stop_experiment(
            sender_channel=sender_channel,
            reflector_channel=refl_channel,
            send_refl_dest=send_refl_dest,
            refl_send_dest=refl_send_dest,
            send_refl_sidlist=send_refl_sidlist.split(','),
            refl_send_sidlist=refl_send_sidlist.split(','),
            send_refl_localseg=send_refl_localseg,
            refl_send_localseg=refl_send_localseg
        )


# Command-line arguments for the set_configuration command
# Arguments are represented as a dicts. Each dict has two items:
# - args, a list of names for the argument
# - kwargs, a dict containing the attributes for the argument required by
#   the argparse library
args_set_configuration = [
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
    """Command-line arguments parser for set_configuration function"""

    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    # Add the arguments to the parser
    for param in args_set_configuration:
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for set_configuration
def complete_set_configuration(text, prev_text):
    """This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string"""

    # Paths auto-completion
    if prev_text is not None:
        # Get the list of the arguments requiring a path
        path_args = [arg
                     for param in args_set_configuration
                     for arg in param['args']
                     if param.get('is_path', False)]
        # Check whether the previous argument requires a path or not
        if prev_text in path_args:
            # Auto-complete the path and return the results
            return cli_utils.complete_path(text)
    # Argument is not a path
    #
    # Get the list of the arguments supported by the command
    args = [arg for param in args_set_configuration for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args


# Command-line arguments for the reset_configuration command
# Arguments are represented as a dicts. Each dict has two items:
# - args, a list of names for the argument
# - kwargs, a dict containing the attributes for the argument required by
#   the argparse library
args_reset_configuration = [
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
    """Command-line arguments parser for reset_configuration function"""

    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    # Add the arguments to the parser
    for param in args_reset_configuration:
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for reset_configuration
def complete_reset_configuration(text, prev_text):
    """This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string"""

    # Paths auto-completion
    if prev_text is not None:
        # Get the list of the arguments requiring a path
        path_args = [arg
                     for param in args_reset_configuration
                     for arg in param['args']
                     if param.get('is_path', False)]
        # Check whether the previous argument requires a path or not
        if prev_text in path_args:
            # Auto-complete the path and return the results
            return cli_utils.complete_path(text)
    # Argument is not a path
    #
    # Get the list of the arguments supported by the command
    args = [arg for param in args_reset_configuration for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args


# Command-line arguments for the start_experiment command
# Arguments are represented as a dicts. Each dict has two items:
# - args, a list of names for the argument
# - kwargs, a dict containing the attributes for the argument required by
#   the argparse library
args_start_experiment = [
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
                   'help': 'authentication_mode', 'default': 'HMAC_SHA_256'}
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
    """Command-line arguments parser for start_experiment function"""

    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    # Add the arguments to the parser
    for param in args_start_experiment:
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for start_experiment
def complete_start_experiment(text, prev_text):
    """This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string"""

    # Paths auto-completion
    if prev_text is not None:
        # Get the list of the arguments requiring a path
        path_args = [arg
                     for param in args_start_experiment
                     for arg in param['args']
                     if param.get('is_path', False)]
        # Check whether the previous argument requires a path or not
        if prev_text in path_args:
            # Auto-complete the path and return the results
            return cli_utils.complete_path(text)
    # Argument is not a path
    #
    # Get the list of the arguments supported by the command
    args = [arg for param in args_start_experiment for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args


# Command-line arguments for the get_experiment_results command
# Arguments are represented as a dicts. Each dict has two items:
# - args, a list of names for the argument
# - kwargs, a dict containing the attributes for the argument required by
#   the argparse library
args_get_experiment_results = [
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
    """Command-line arguments parser for get_experiments_results function"""

    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    # Add the arguments to the parser
    for param in args_get_experiment_results:
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for get_experiment_results
def complete_get_experiment_results(text, prev_text):
    """This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string"""

    # Paths auto-completion
    if prev_text is not None:
        # Get the list of the arguments requiring a path
        path_args = [arg
                     for param in args_get_experiment_results
                     for arg in param['args']
                     if param.get('is_path', False)]
        # Check whether the previous argument requires a path or not
        if prev_text in path_args:
            # Auto-complete the path and return the results
            return cli_utils.complete_path(text)
    # Argument is not a path
    #
    # Get the list of the arguments supported by the command
    args = [arg for param in args_get_experiment_results
            for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args


# Command-line arguments for the stop_experiment command
# Arguments are represented as a dicts. Each dict has two items:
# - args, a list of names for the argument
# - kwargs, a dict containing the attributes for the argument required by
#   the argparse library
args_stop_experiment = [
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
    """Command-line arguments parser for stop_experiment function"""

    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    # Add the arguments to the parser
    for param in args_stop_experiment:
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for stop_experiment
def complete_stop_experiment(text, prev_text):
    """This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string"""

    # Paths auto-completion
    if prev_text is not None:
        # Get the list of the arguments requiring a path
        path_args = [arg
                     for param in args_stop_experiment
                     for arg in param['args']
                     if param.get('is_path', False)]
        # Check whether the previous argument requires a path or not
        if prev_text in path_args:
            # Auto-complete the path and return the results
            return cli_utils.complete_path(text)
    # Argument is not a path
    #
    # Get the list of the arguments supported by the command
    args = [arg for param in args_stop_experiment for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args
