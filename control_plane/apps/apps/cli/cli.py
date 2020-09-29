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


"""Implementation of a CLI for the SRv6 Controller"""

# This comment avoids the annoying warning "Too many lines in module"
# of pylint. Maybe we should split this module in the future.
#
# pylint: disable=too-many-lines

# General imports
try:
    # Optional dependency, required to support persistency of the command
    # history
    import readline
except ImportError:
    # If 'readline' is not found in the system, history persistency
    # will be disabled
    readline = None
import logging
import os
from argparse import ArgumentParser
from cmd import Cmd

# Controller dependencies
from controller import arangodb_driver
from controller import srv6_usid
from apps.cli import srv6_cli, srv6pm_cli, topo_cli
from apps.nb_grpc_client import utils as nb_utils

# Folder containing this script
BASE_PATH = os.path.dirname(os.path.realpath(__file__))


# Logger reference
logger = logging.getLogger(__name__)

# Default parameters
#
# Controller gRPC address
DEFAULT_CONTROLLER_ADDRESS = 'localhost'
# Controller gRPC port
DEFAULT_CONTROLLER_PORT = 12345


# Set line delimiters, required for the auto-completion feature
readline.set_completer_delims(' \t\n')

# gRPC channel to the controller
CONTROLLER_CHANNEL = None


class CustomCmd(Cmd):
    """This class extends the python class Cmd and implements a handler
    for CTRL+C and CTRL+D"""

    histfile = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            '.controller_history')
    histfile_size = 1000

    def preloop(self):
        if readline and os.path.exists(self.histfile):
            readline.read_history_file(self.histfile)

    def postloop(self):
        if readline:
            readline.set_history_length(self.histfile_size)
            readline.write_history_file(self.histfile)

    def cmdloop(self, intro=None):
        """ Command loop"""

        # pylint: disable=no-self-use

        while True:
            try:
                super(CustomCmd, self).cmdloop(intro=intro)
                break
            except KeyboardInterrupt:
                print("^C")
            except Exception as err:    # pylint: disable=broad-except
                # When an exception is raised, we log the traceback
                # and keep the CLI open and ready to receive next comands
                #
                # We need mute pylint 'broad-except' in order to
                # avoid annoying warnings
                logging.exception(err)
                print()

    def emptyline(self):
        """Avoid to execute the last command if empty line is entered"""

        # pylint: disable=no-self-use

    def default(self, line):
        """Default behavior"""

        if line in ['x', 'q']:
            return self.do_exit(line)

        print("Unrecognized command: {}".format(line))
        return False

    def do_exit(self, args):
        """New line on exit"""

        # pylint: disable=unused-argument, no-self-use

        print()     # New line
        return True

    def help_exit(self):
        """Help message for exit callback"""

        # pylint: disable=no-self-use

        print('exit the application. Shorthand: x q Ctrl-D.')

    do_EOF = do_exit
    help_EOF = help_exit


class ControllerCLITopology(CustomCmd):
    """Topology subsection"""

    prompt = "controller(topology)> "

    def do_show_nodes(self, args):
        """Show nodes"""

        # pylint: disable=no-self-use, unused-argument

        try:
            # args = (srv6_cli
            #         .parse_arguments_print_nodes(
            #             prog='print_nodes', args=args.split(' ')))
            pass
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        # pylint: disable=no-self-use
        #
        # Print the nodes
        srv6_cli.print_nodes(CONTROLLER_CHANNEL)
        # Return False in order to keep the CLI subsection open
        # after the command execution
        return False

    def do_extract(self, args):
        """Extract the network topology"""

        # pylint: disable=no-self-use

        try:
            args = (topo_cli
                    .parse_arguments_topology_information_extraction_isis(
                        prog='extract', args=args.split(' ')))
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        topo_cli.topology_information_extraction_isis(
            controller_channel=CONTROLLER_CHANNEL,
            routers=args.routers.split(','),
            period=args.period,
            isisd_pwd=args.isisd_pwd,
            topo_file_json=args.topo_file_json,
            nodes_file_yaml=args.nodes_file_yaml,
            edges_file_yaml=args.edges_file_yaml,
            addrs_yaml=args.addrs_yaml,
            hosts_yaml=args.hosts_yaml,
            topo_graph=args.topo_graph,
            verbose=args.verbose
        )
        # Return False in order to keep the CLI subsection open
        # after the command execution
        return False

    def do_load_on_arango(self, args):
        """Read nodes and edges YAML files and upload the topology
        on ArangoDB"""

        # pylint: disable=no-self-use

        try:
            args = topo_cli.parse_arguments_load_topo_on_arango(
                prog='load_on_arango',
                args=args.split(' ')
            )
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        topo_cli.load_topo_on_arango(
            controller_channel=CONTROLLER_CHANNEL,
            nodes_yaml=args.nodes_yaml,
            edges_yaml=args.edges_yaml,
            verbose=args.verbose
        )
        # Return False in order to keep the CLI subsection open
        # after the command execution
        return False

    def do_extract_and_load_on_arango(self, args):
        """Extract the network topology from a set of nodes running ISIS
        and upload it on ArangoDB"""

        # pylint: disable=no-self-use

        try:
            arg = (topo_cli
                   .parse_arguments_extract_topo_from_isis_and_load_on_arango(
                       prog='extract_and_load_on_arango', args=args.split(' '))
                   )
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        topo_cli.extract_topo_from_isis_and_load_on_arango(
            controller_channel=CONTROLLER_CHANNEL,
            isis_nodes=arg.isis_nodes.split(','),
            isisd_pwd=arg.isisd_pwd,
            nodes_yaml=arg.nodes_yaml,
            edges_yaml=arg.edges_yaml,
            addrs_yaml=arg.addrs_yaml,
            hosts_yaml=arg.hosts_yaml,
            period=arg.period,
            verbose=arg.verbose
        )
        # Return False in order to keep the CLI subsection open
        # after the command execution
        return False

    def do_push_nodes_config(self, args):
        '''
        Push nodes configuration to the controller.
        '''
        # pylint: disable=no-self-use
        try:
            arg = (topo_cli
                   .parse_arguments_push_nodes_config(
                       prog='push_nodes_config', args=args.split(' '))
                   )
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        topo_cli.push_nodes_config(
            controller_channel=CONTROLLER_CHANNEL,
            nodes_config_filename=arg.nodes_config_filename
        )
        # Return False in order to keep the CLI subsection open
        # after the command execution
        return False

    def do_get_nodes_config(self, args):
        '''
        Get nodes configuration from the controller.
        '''
        # pylint: disable=no-self-use
        # try:
        #     arg = (topo_cli
        #            .parse_arguments_push_nodes_config(
        #                prog='push_nodes_config', args=args.split(' '))
        #            )
        # except SystemExit:
        #     return False  # This workaround avoid exit in case of errors
        topo_cli.get_nodes_config(
            controller_channel=CONTROLLER_CHANNEL
        )
        # Return False in order to keep the CLI subsection open
        # after the command execution
        return False

    def complete_show_nodes(self, text, line, start_idx, end_idx):
        """Auto-completion for show_nodes command"""

        # pylint: disable=no-self-use, unused-argument

        # Get the previous argument in the command
        # Depending on the previous argument, it is possible to
        # complete specific params, such as the paths
        #
        # Split args
        args = line[:start_idx].split(' ')
        # If this is not the first arg, get the previous one
        prev_text = None
        if len(args) > 1:
            prev_text = args[-2]    # [-2] because last element is always ''
        # Call auto-completion function and return a list of
        # possible arguments
        return srv6_cli.complete_print_nodes(text, prev_text)

    def complete_extract(self, text, line, start_idx, end_idx):
        """Auto-completion for extract command"""

        # pylint: disable=no-self-use, unused-argument

        # Get the previous argument in the command
        # Depending on the previous argument, it is possible to
        # complete specific params, such as the paths
        #
        # Split args
        args = line[:start_idx].split(' ')
        # If this is not the first arg, get the previous one
        prev_text = None
        if len(args) > 1:
            prev_text = args[-2]    # [-2] because last element is always ''
        # Call auto-completion function and return a list of
        # possible arguments
        return topo_cli.complete_topology_information_extraction_isis(
            text, prev_text)

    def complete_load_on_arango(self, text, line, start_idx, end_idx):
        """Auto-completion for load_on_arango command"""

        # pylint: disable=no-self-use, unused-argument

        # Get the previous argument in the command
        # Depending on the previous argument, it is possible to
        # complete specific params, such as the paths
        #
        # Split args
        args = line[:start_idx].split(' ')
        # If this is not the first arg, get the previous one
        prev_text = None
        if len(args) > 1:
            prev_text = args[-2]    # [-2] because last element is always ''
        # Call auto-completion function and return a list of
        # possible arguments
        return topo_cli.complete_load_topo_on_arango(text, prev_text)

    def complete_extract_and_load_on_arango(self, text,
                                            line, start_idx, end_idx):
        """Auto-completion for extract_and_load_on_arango command"""

        # pylint: disable=no-self-use, unused-argument

        # Get the previous argument in the command
        # Depending on the previous argument, it is possible to
        # complete specific params, such as the paths
        #
        # Split args
        args = line[:start_idx].split(' ')
        # If this is not the first arg, get the previous one
        prev_text = None
        if len(args) > 1:
            prev_text = args[-2]    # [-2] because last element is always ''
        # Call auto-completion function and return a list of
        # possible arguments
        return (topo_cli
                .complete_extract_topo_from_isis_and_load_on_arango(
                    text, prev_text))

    def complete_push_nodes_config(self, text, line, start_idx, end_idx):
        '''
        Auto-completion for push_nodes_config command.
        '''
        # pylint: disable=no-self-use, unused-argument
        #
        # Get the previous argument in the command
        # Depending on the previous argument, it is possible to
        # complete specific params, such as the paths
        #
        # Split args
        args = line[:start_idx].split(' ')
        # If this is not the first arg, get the previous one
        prev_text = None
        if len(args) > 1:
            prev_text = args[-2]    # [-2] because last element is always ''
        # Call auto-completion function and return a list of
        # possible arguments
        return topo_cli.complete_push_nodes_config(text, prev_text)

    def complete_get_nodes_config(self, text, line, start_idx, end_idx):
        '''
        Auto-completion for get_nodes_config command.
        '''
        # pylint: disable=no-self-use, unused-argument
        #
        # Get the previous argument in the command
        # Depending on the previous argument, it is possible to
        # complete specific params, such as the paths
        #
        # Split args
        args = line[:start_idx].split(' ')
        # If this is not the first arg, get the previous one
        prev_text = None
        if len(args) > 1:
            prev_text = args[-2]    # [-2] because last element is always ''
        # Call auto-completion function and return a list of
        # possible arguments
        return topo_cli.complete_get_nodes_config(text, prev_text)

    def help_show_nodes(self):
        """Show help usage for show_nodes config command"""
        #
        # pylint: disable=no-self-use
        #
        srv6_cli.parse_arguments_print_nodes(
            prog='show_nodes',
            args=['--help']
        )

    def help_extract(self):
        """Show help usage for extract command"""

        # pylint: disable=no-self-use

        topo_cli.parse_arguments_topology_information_extraction_isis(
            prog='extract',
            args=['--help']
        )

    def help_load_on_arango(self):
        """Show help usage for load_topo_on_arango"""

        # pylint: disable=no-self-use

        topo_cli.parse_arguments_load_topo_on_arango(
            prog='load_on_arango',
            args=['--help']
        )

    def help_extract_and_load_on_arango(self):
        """Show help usage for extract_and_load_on_arango"""

        # pylint: disable=no-self-use

        topo_cli.parse_arguments_extract_topo_from_isis_and_load_on_arango(
            prog='extract_and_load_on_arango',
            args=['--help']
        )

    def help_push_nodes_config(self):
        '''
        Show help usage for push_nodes_config.
        '''
        # pylint: disable=no-self-use
        topo_cli.parse_arguments_push_nodes_config(
            prog='push_nodes_config',
            args=['--help']
        )

    def help_get_nodes_config(self):
        '''
        Show help usage for get_nodes_config.
        '''
        # pylint: disable=no-self-use
        topo_cli.parse_arguments_get_nodes_config(
            prog='get_nodes_config',
            args=['--help']
        )


class ControllerCLISRv6PMConfiguration(CustomCmd):
    """srv6pm->Configuration subsection"""

    prompt = "controller(srv6pm-configuration)> "

    def do_set(self, args):
        """Set configuation"""

        # pylint: disable=no-self-use

        try:
            args = srv6pm_cli.parse_arguments_set_configuration(
                prog='start',
                args=args.split(' ')
            )
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        srv6pm_cli.set_configuration(
            controller_channel=CONTROLLER_CHANNEL,
            sender=args.sender_ip,
            reflector=args.reflector_ip,
            sender_port=args.sender_port,
            reflector_port=args.reflector_port,
            send_udp_port=args.send_udp_port,
            refl_udp_port=args.refl_udp_port,
            interval_duration=args.interval_duration,
            delay_margin=args.delay_margin,
            number_of_color=args.number_of_color,
            pm_driver=args.pm_driver
        )
        # Return False in order to keep the CLI subsection open
        # after the command execution
        return False

    def do_reset(self, args):
        """Clear configuration"""

        # pylint: disable=no-self-use

        try:
            args = srv6pm_cli.parse_arguments_reset_configuration(
                prog='start',
                args=args.split(' ')
            )
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        srv6pm_cli.reset_configuration(
            controller_channel=CONTROLLER_CHANNEL,
            sender=args.sender_ip,
            reflector=args.reflector_ip,
            sender_port=args.sender_port,
            reflector_port=args.reflector_port,
        )
        # Return False in order to keep the CLI subsection open
        # after the command execution
        return False

    def complete_set(self, text, line, start_idx, end_idx):
        """Auto-completion for set command"""

        # pylint: disable=no-self-use, unused-argument

        # Get the previous argument in the command
        # Depending on the previous argument, it is possible to
        # complete specific params, such as the paths
        #
        # Split args
        args = line[:start_idx].split(' ')
        # If this is not the first arg, get the previous one
        prev_text = None
        if len(args) > 1:
            prev_text = args[-2]    # [-2] because last element is always ''
        # Call auto-completion function and return a list of
        # possible arguments
        return srv6pm_cli.complete_set_configuration(text, prev_text)

    def complete_reset(self, text, line, start_idx, end_idx):
        """Auto-completion for reset command"""

        # pylint: disable=no-self-use, unused-argument

        # Get the previous argument in the command
        # Depending on the previous argument, it is possible to
        # complete specific params, such as the paths
        #
        # Split args
        args = line[:start_idx].split(' ')
        # If this is not the first arg, get the previous one
        prev_text = None
        if len(args) > 1:
            prev_text = args[-2]    # [-2] because last element is always ''
        # Call auto-completion function and return a list of
        # possible arguments
        return srv6pm_cli.complete_reset_configuration(text, prev_text)

    def help_set(self):
        """Show help usagte for set operation"""

        # pylint: disable=no-self-use

        srv6pm_cli.parse_arguments_set_configuration(
            prog='start',
            args=['--help']
        )

    def help_reset(self):
        """Show help usage for reset operation"""

        # pylint: disable=no-self-use

        srv6pm_cli.parse_arguments_reset_configuration(
            prog='start',
            args=['--help']
        )


class ControllerCLISRv6PMExperiment(CustomCmd):
    """srv6pm->experiment subsection"""

    prompt = "controller(srv6pm-experiment)> "

    def do_start(self, args):
        """Start an experiment"""

        # pylint: disable=no-self-use

        try:
            args = srv6pm_cli.parse_arguments_start_experiment(
                prog='start',
                args=args.split(' ')
            )
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        srv6pm_cli.start_experiment(
            controller_channel=CONTROLLER_CHANNEL,
            sender=args.sender_ip,
            reflector=args.reflector_ip,
            sender_port=args.sender_port,
            reflector_port=args.reflector_port,
            send_refl_dest=args.send_refl_dest,
            refl_send_dest=args.refl_send_dest,
            send_refl_sidlist=args.send_refl_sidlist,
            refl_send_sidlist=args.refl_send_sidlist,
            # Interfaces moved to set_configuration
            # send_in_interfaces=args.send_in_interfaces,
            # refl_in_interfaces=args.refl_in_interfaces,
            # send_out_interfaces=args.send_out_interfaces,
            # refl_out_interfaces=args.refl_out_interfaces,
            measurement_protocol=args.measurement_protocol,
            measurement_type=args.measurement_type,
            authentication_mode=args.authentication_mode,
            authentication_key=args.authentication_key,
            timestamp_format=args.timestamp_format,
            delay_measurement_mode=args.delay_measurement_mode,
            padding_mbz=args.padding_mbz,
            loss_measurement_mode=args.loss_measurement_mode,
            measure_id=args.measure_id,
            send_refl_localseg=args.send_refl_localseg,
            refl_send_localseg=args.refl_send_localseg,
            force=args.force
        )
        # Return False in order to keep the CLI subsection open
        # after the command execution
        return False

    def do_show(self, args):
        """Show results of a running experiment"""

        # pylint: disable=no-self-use

        try:
            args = srv6pm_cli.parse_arguments_get_experiment_results(
                prog='show',
                args=args.split(' ')
            )
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        srv6pm_cli.get_experiment_results(
            controller_channel=CONTROLLER_CHANNEL,
            sender=args.sender_ip,
            reflector=args.reflector_ip,
            sender_port=args.sender_port,
            reflector_port=args.reflector_port,
            send_refl_sidlist=args.send_refl_sidlist,
            refl_send_sidlist=args.refl_send_sidlist
        )
        # Return False in order to keep the CLI subsection open
        # after the command execution
        return False

    def do_stop(self, args):
        """Stop a running experiment"""

        # pylint: disable=no-self-use

        try:
            args = srv6pm_cli.parse_arguments_stop_experiment(
                prog='stop',
                args=args.split(' ')
            )
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        srv6pm_cli.stop_experiment(
            controller_channel=CONTROLLER_CHANNEL,
            sender=args.sender_ip,
            reflector=args.reflector_ip,
            sender_port=args.sender_port,
            reflector_port=args.reflector_port,
            send_refl_sidlist=args.send_refl_sidlist,
            refl_send_sidlist=args.refl_send_sidlist,
            send_refl_dest=args.send_refl_dest,
            refl_send_dest=args.refl_send_dest,
            send_refl_localseg=args.send_refl_localseg,
            refl_send_localseg=args.refl_send_localseg
        )
        # Return False in order to keep the CLI subsection open
        # after the command execution
        return False

    def complete_start(self, text, line, start_idx, end_idx):
        """Auto-completion for start command"""

        # pylint: disable=no-self-use, unused-argument

        # Get the previous argument in the command
        # Depending on the previous argument, it is possible to
        # complete specific params, such as the paths
        #
        # Split args
        args = line[:start_idx].split(' ')
        # If this is not the first arg, get the previous one
        prev_text = None
        if len(args) > 1:
            prev_text = args[-2]    # [-2] because last element is always ''
        # Call auto-completion function and return a list of
        # possible arguments
        return srv6pm_cli.complete_start_experiment(text, prev_text)

    def complete_show(self, text, line, start_idx, end_idx):
        """Auto-completion for show command"""

        # pylint: disable=no-self-use, unused-argument

        # Get the previous argument in the command
        # Depending on the previous argument, it is possible to
        # complete specific params, such as the paths
        #
        # Split args
        args = line[:start_idx].split(' ')
        # If this is not the first arg, get the previous one
        prev_text = None
        if len(args) > 1:
            prev_text = args[-2]    # [-2] because last element is always ''
        # Call auto-completion function and return a list of
        # possible arguments
        return srv6pm_cli.complete_get_experiment_results(text, prev_text)

    def complete_stop(self, text, line, start_idx, end_idx):
        """Auto-completion for stop command"""

        # pylint: disable=no-self-use, unused-argument

        # Get the previous argument in the command
        # Depending on the previous argument, it is possible to
        # complete specific params, such as the paths
        #
        # Split args
        args = line[:start_idx].split(' ')
        # If this is not the first arg, get the previous one
        prev_text = None
        if len(args) > 1:
            prev_text = args[-2]    # [-2] because last element is always ''
        # Call auto-completion function and return a list of
        # possible arguments
        return srv6pm_cli.complete_stop_experiment(text, prev_text)

    def help_start(self):
        """Show help usage for start operation"""

        # pylint: disable=no-self-use

        srv6pm_cli.parse_arguments_start_experiment(
            prog='start',
            args=['--help']
        )

    def help_show(self):
        """Show help usasge for show operation"""

        # pylint: disable=no-self-use

        srv6pm_cli.parse_arguments_get_experiment_results(
            prog='show',
            args=['--help']
        )

    def help_stop(self):
        """Show help usage for stop operation"""

        # pylint: disable=no-self-use

        srv6pm_cli.parse_arguments_stop_experiment(
            prog='stop',
            args=['--help']
        )


class ControllerCLISRv6PM(CustomCmd):
    """srv6pm subcommmand"""

    prompt = "controller(srv6pm)> "

    def do_experiment(self, args):
        """Enter srv6pm-experiment subsection"""

        # pylint: disable=no-self-use, unused-argument

        sub_cmd = ControllerCLISRv6PMExperiment()
        sub_cmd.cmdloop()

    def do_configuration(self, args):
        """Enter srv6pm-configuration subsection"""

        # pylint: disable=no-self-use, unused-argument

        sub_cmd = ControllerCLISRv6PMConfiguration()
        sub_cmd.cmdloop()


class ControllerCLISRv6(CustomCmd):
    """srv6 subsection"""

    prompt = "controller(srv6)> "

    def __init__(self):
        # Print the nodes
        srv6_cli.print_nodes(CONTROLLER_CHANNEL)
        # Init superclass
        super().__init__()

    def do_path(self, args):
        """Handle a SRv6 path"""

        # pylint: disable=no-self-use

        try:
            args = srv6_cli.parse_arguments_srv6_path(
                prog='path',
                args=args.split(' ')
            )
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        srv6_cli.handle_srv6_path(
            controller_channel=CONTROLLER_CHANNEL,
            operation=args.op,
            grpc_address=args.grpc_ip,
            grpc_port=args.grpc_port,
            destination=args.destination,
            segments=args.segments,
            device=args.device,
            encapmode=args.encapmode,
            table=args.table,
            metric=args.metric,
            bsid_addr=args.bsid_addr,
            fwd_engine=args.fwd_engine
        )
        # Return False in order to keep the CLI subsection open
        # after the command execution
        return False

    def do_behavior(self, args):
        """Handle a SRv6 behavior"""

        # pylint: disable=no-self-use

        try:
            args = srv6_cli.parse_arguments_srv6_behavior(
                prog='behavior',
                args=args.split(' ')
            )
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        srv6_cli.handle_srv6_behavior(
            controller_channel=CONTROLLER_CHANNEL,
            operation=args.op,
            grpc_address=args.grpc_ip,
            grpc_port=args.grpc_port,
            segment=args.segment,
            action=args.action,
            device=args.device,
            table=args.table,
            nexthop=args.nexthop,
            lookup_table=args.lookup_table,
            interface=args.interface,
            segments=args.segments,
            metric=args.metric,
            fwd_engine=args.fwd_engine
        )
        # Return False in order to keep the CLI subsection open
        # after the command execution
        return False

    def do_unitunnel(self, args):
        """Handle a SRv6 unidirectional tunnel"""

        # pylint: disable=no-self-use

        try:
            args = srv6_cli.parse_arguments_srv6_unitunnel(
                prog='unitunnel',
                args=args.split(' ')
            )
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        srv6_cli.handle_srv6_unitunnel(
            controller_channel=CONTROLLER_CHANNEL,
            operation=args.op,
            ingress_ip=args.ingress_grpc_ip,
            ingress_port=args.ingress_grpc_port,
            egress_ip=args.egress_grpc_ip,
            egress_port=args.egress_grpc_port,
            destination=args.dest,
            segments=args.sidlist,
            localseg=args.localseg,
            bsid_addr=args.bsid_addr,
            fwd_engine=args.fwd_engine
        )
        # Return False in order to keep the CLI subsection open
        # after the command execution
        return False

    def do_biditunnel(self, args):
        """Handle a SRv6 bidirectional tunnel"""

        # pylint: disable=no-self-use

        try:
            args = srv6_cli.parse_arguments_srv6_biditunnel(
                prog='biditunnel',
                args=args.split(' ')
            )
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        srv6_cli.handle_srv6_biditunnel(
            controller_channel=CONTROLLER_CHANNEL,
            operation=args.op,
            node_l_ip=args.l_grpc_ip,
            node_r_ip=args.r_grpc_ip,
            node_l_port=args.l_grpc_port,
            node_r_port=args.r_grpc_port,
            sidlist_lr=args.sidlist_lr,
            sidlist_rl=args.sidlist_rl,
            dest_lr=args.dest_lr,
            dest_rl=args.dest_rl,
            localseg_lr=args.localseg_lr,
            localseg_rl=args.localseg_rl,
            bsid_addr=args.bsid_addr,
            fwd_engine=args.fwd_engine
        )
        # Return False in order to keep the CLI subsection open
        # after the command execution
        return False

    def do_usid_policy(self, args):
        """Handle a SRv6 uSID policy"""

        # pylint: disable=no-self-use, unused-argument

        try:
            args = srv6_cli.parse_arguments_srv6_usid_policy(
                prog='usid_policy',
                args=args.split(' ')
            )
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        # Handle the uSID policy
        srv6_cli.handle_srv6_usid_policy(
            controller_channel=CONTROLLER_CHANNEL,
            operation=args.op,
            lr_destination=args.lr_destination,
            rl_destination=args.rl_destination,
            nodes_lr=args.nodes,
            nodes_rl=args.nodes_rev,
            table=args.table,
            metric=args.metric,
            _id=args.id,
            l_grpc_ip=args.l_grpc_ip,
            l_grpc_port=args.l_grpc_port,
            l_fwd_engine=args.l_fwd_engine,
            r_grpc_ip=args.r_grpc_ip,
            r_grpc_port=args.r_grpc_port,
            r_fwd_engine=args.r_fwd_engine,
            decap_sid=args.decap_sid,
            locator=args.locator
        )
        # Print nodes available
        srv6_cli.print_nodes()
        # Return False in order to keep the CLI subsection open
        # after the command execution
        return False

    def complete_path(self, text, line, start_idx, end_idx):
        """Auto-completion for path command"""

        # pylint: disable=no-self-use, unused-argument

        # Get the previous argument in the command
        # Depending on the previous argument, it is possible to
        # complete specific params, such as the paths
        #
        # Split args
        args = line[:start_idx].split(' ')
        # If this is not the first arg, get the previous one
        prev_text = None
        if len(args) > 1:
            prev_text = args[-2]    # [-2] because last element is always ''
        # Call auto-completion function and return a list of
        # possible arguments
        return srv6_cli.complete_srv6_path(text, prev_text)

    def complete_behavior(self, text, line, start_idx, end_idx):
        """Auto-completion for behavior command"""

        # pylint: disable=no-self-use, unused-argument

        # Get the previous argument in the command
        # Depending on the previous argument, it is possible to
        # complete specific params, such as the paths
        #
        # Split args
        args = line[:start_idx].split(' ')
        # If this is not the first arg, get the previous one
        prev_text = None
        if len(args) > 1:
            prev_text = args[-2]    # [-2] because last element is always ''
        # Call auto-completion function and return a list of
        # possible arguments
        return srv6_cli.complete_srv6_behavior(text, prev_text)

    def complete_unitunnel(self, text, line, start_idx, end_idx):
        """Auto-completion for unitunnel command"""

        # pylint: disable=no-self-use, unused-argument

        # Get the previous argument in the command
        # Depending on the previous argument, it is possible to
        # complete specific params, such as the paths
        #
        # Split args
        args = line[:start_idx].split(' ')
        # If this is not the first arg, get the previous one
        prev_text = None
        if len(args) > 1:
            prev_text = args[-2]    # [-2] because last element is always ''
        # Call auto-completion function and return a list of
        # possible arguments
        return srv6_cli.complete_srv6_unitunnel(text, prev_text)

    def complete_biditunnel(self, text, line, start_idx, end_idx):
        """Auto-completion for biditunnel command"""

        # pylint: disable=no-self-use, unused-argument

        # Get the previous argument in the command
        # Depending on the previous argument, it is possible to
        # complete specific params, such as the paths
        #
        # Split args
        args = line[:start_idx].split(' ')
        # If this is not the first arg, get the previous one
        prev_text = None
        if len(args) > 1:
            prev_text = args[-2]    # [-2] because last element is always ''
        # Call auto-completion function and return a list of
        # possible arguments
        return srv6_cli.complete_srv6_biditunnel(text, prev_text)

    def complete_usid_policy(self, text, line, start_idx, end_idx):
        """Auto-completion for usid_policy command"""

        # pylint: disable=no-self-use, unused-argument

        # Get the previous argument in the command
        # Depending on the previous argument, it is possible to
        # complete specific params, such as the paths
        #
        # Split args
        args = line[:start_idx].split(' ')
        # If this is not the first arg, get the previous one
        prev_text = None
        if len(args) > 1:
            prev_text = args[-2]    # [-2] because last element is always ''
        # Call auto-completion function and return a list of
        # possible arguments
        return srv6_cli.complete_srv6_usid_policy(text, prev_text)

    def help_path(self):
        """Show help usage for path command"""

        # pylint: disable=no-self-use

        srv6_cli.parse_arguments_srv6_path(
            prog='path',
            args=['--help']
        )

    def help_behavior(self):
        """Show help usage for behavior command"""

        # pylint: disable=no-self-use

        srv6_cli.parse_arguments_srv6_behavior(
            prog='behavior',
            args=['--help']
        )

    def help_unitunnel(self):
        """Show help usage for unitunnel command"""

        # pylint: disable=no-self-use

        srv6_cli.parse_arguments_srv6_unitunnel(
            prog='unitunnel',
            args=['--help']
        )

    def help_biditunnel(self):
        """Show help usage for biditunnel command"""

        # pylint: disable=no-self-use

        srv6_cli.parse_arguments_srv6_biditunnel(
            prog='biditunnel',
            args=['-help']
        )

    def help_usid_policy(self):
        """Show help usage for usid_policy command"""

        # pylint: disable=no-self-use

        srv6_cli.parse_arguments_srv6_usid_policy(
            prog='usid_policy',
            args=['--help']
        )


class ControllerCLI(CustomCmd):
    """Controller CLI entry point"""

    prompt = 'controller> '
    intro = "Welcome! Type ? to list commands"

    def do_exit(self, args):
        """Exit from the CLI"""

        # pylint: disable=no-self-use, unused-argument

        print("Bye")
        return True

    def do_srv6(self, args):
        """Enter srv6 subsection"""

        # pylint: disable=no-self-use, unused-argument

        sub_cmd = ControllerCLISRv6()
        sub_cmd.cmdloop()

    def do_srv6pm(self, args):
        """Enter srv6pm subsection"""

        # pylint: disable=no-self-use, unused-argument

        sub_cmd = ControllerCLISRv6PM()
        sub_cmd.cmdloop()

    def do_topology(self, args):
        """Enter topology subsection"""

        # pylint: disable=no-self-use, unused-argument

        sub_cmd = ControllerCLITopology()
        sub_cmd.cmdloop()

    def default(self, line):
        """Default behavior"""

        if line in ['x', 'q']:
            return self.do_exit(line)

        print("Unrecognized command: {}".format(line))
        return False

    do_EOF = do_exit


# Parse options
def parse_arguments():
    """Command-line arguments parser"""

    # Get parser
    parser = ArgumentParser(
        description='Command Line Interface (CLI)'
    )
    parser.add_argument(
        '-a', '--controller-address', action='store',
        help='Controller IP address', default=DEFAULT_CONTROLLER_ADDRESS
    )
    parser.add_argument(
        '-p', '--controller-port', action='store', help='Controller port',
        default=DEFAULT_CONTROLLER_PORT
    )
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Activate debug logs'
    )
    # Parse input parameters
    args = parser.parse_args()
    # Return the arguments
    return args


def __main():
    '''
    Entry point for this module.
    '''
    global CONTROLLER_CHANNEL
    # Parse command-line arguments
    args = parse_arguments()
    # Controller IP address
    controller_address = args.controller_address
    # Controller port
    controller_port = args.controller_port
    # Setup properly the logger
    if args.debug:
        logger.setLevel(level=logging.DEBUG)
    else:
        logger.setLevel(level=logging.INFO)
    # Debug settings
    server_debug = logger.getEffectiveLevel() == logging.DEBUG
    logging.info('SERVER_DEBUG: %s', str(server_debug))
    # Try to establish a connection to the controller
    CONTROLLER_CHANNEL = nb_utils.get_grpc_session(
        server_ip=controller_address,
        server_port=controller_port
    )
    # Start the CLI
    ControllerCLI().cmdloop()


if __name__ == '__main__':
    __main()
