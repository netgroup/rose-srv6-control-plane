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

# General imports
import os
import sys
from cmd import Cmd
import logging
from argparse import ArgumentParser
from pathlib import Path
from pkg_resources import resource_filename

# python-dotenv dependencies
from dotenv import load_dotenv

# Controller dependencies
from controller.cli import topo_cli
from controller.cli import srv6pm_cli
from controller.cli import srv6_cli

# Folder containing this script
BASE_PATH = os.path.dirname(os.path.realpath(__file__))


# Logger reference
logger = logging.getLogger(__name__)

# import utils
# import srv6_controller
# import ti_extraction
# import srv6_pm

# Default path to the .env file
DEFAULT_ENV_FILE_PATH = resource_filename(__name__, '../config/controller.env')
# Default value for debug mode
DEFAULT_DEBUG = False


class CustomCmd(Cmd):
    """This class extends the python class Cmd and implements a handler
    for CTRL+C and CTRL+D"""

    def cmdloop(self, intro=None):
        """ Command loop"""

        # pylint: disable=no-self-use

        while True:
            try:
                super(CustomCmd, self).cmdloop(intro=intro)
                break
            except KeyboardInterrupt:
                print("^C")

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
        return True

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
            arango_url=args.arango_url,
            arango_user=args.arango_user,
            arango_password=args.arango_password,
            nodes_yaml=args.nodes_yaml,
            edges_yaml=args.edges_yaml,
            verbose=args.verbose
        )
        return True

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
            isis_nodes=arg.isis_nodes.split(','),
            isisd_pwd=arg.isisd_pwd,
            arango_url=arg.arango_url,
            arango_user=arg.arango_user,
            arango_password=arg.arango_password,
            nodes_yaml=arg.nodes_yaml,
            edges_yaml=arg.edges_yaml,
            addrs_yaml=arg.addrs_yaml,
            hosts_yaml=arg.hosts_yaml,
            period=arg.period,
            verbose=arg.verbose
        )
        return True

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
        return True

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
            sender=args.sender_ip,
            reflector=args.reflector_ip,
            sender_port=args.sender_port,
            reflector_port=args.reflector_port,
        )
        return True

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
        return True

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
            sender=args.sender_ip,
            reflector=args.reflector_ip,
            sender_port=args.sender_port,
            reflector_port=args.reflector_port,
            send_refl_sidlist=args.send_refl_sidlist,
            refl_send_sidlist=args.refl_send_sidlist
        )
        return True

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
        return True

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
            operation=args.op,
            grpc_address=args.grpc_ip,
            grpc_port=args.grpc_port,
            destination=args.destination,
            segments=args.segments,
            device=args.device,
            encapmode=args.encapmode,
            table=args.table,
            metric=args.metric
        )
        return True

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
            metric=args.metric
        )
        return True

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
            operation=args.op,
            ingress_ip=args.ingress_grpc_ip,
            ingress_port=args.ingress_grpc_port,
            egress_ip=args.egress_grpc_ip,
            egress_port=args.egress_grpc_port,
            destination=args.dest,
            segments=args.sidlist,
            localseg=args.localseg
        )
        return True

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
            localseg_rl=args.localseg_rl
        )
        return True

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


# Class representing the configuration
class Config:
    """Class implementing configuration for the Controller"""

    # ArangoDB username
    arango_user = None
    # ArangoDB password
    arango_password = None
    # ArangoDB URL
    arango_url = None
    # Configure Kafka servers
    kafka_servers = None
    # Define whether to enable the debug mode or not
    debug = DEFAULT_DEBUG

    # Load configuration from .env file
    def load_config(self, env_file):
        """Load configuration from a .env file"""

        logger.info('*** Loading configuration from %s', env_file)
        # Path to the .env file
        env_path = Path(env_file)
        # Load environment variables from .env file
        load_dotenv(dotenv_path=env_path)
        # ArangoDB username
        if os.getenv('ARANGO_USER') is not None:
            self.arango_user = os.getenv('ARANGO_USER')
        # ArangoDB password
        if os.getenv('ARANGO_PASSWORD') is not None:
            self.arango_password = os.getenv('ARANGO_PASSWORD')
        # ArangoDB URL
        if os.getenv('ARANGO_URL') is not None:
            self.arango_url = os.getenv('ARANGO_URL')
        # Kafka servers
        if os.getenv('KAFKA_SERVERS') is not None:
            self.kafka_servers = os.getenv('KAFKA_SERVERS')
        # Define whether to enable the debug mode or not
        if os.getenv('DEBUG') is not None:
            self.debug = os.getenv('DEBUG')
            # Values provided in .env files are returned as strings
            # We need to convert them to bool
            if self.debug.lower() == 'true':
                self.debug = True
            elif self.debug.lower() == 'false':
                self.debug = False
            else:
                # Invalid value for this parameter
                self.debug = None

    def validate_config(self):
        """Validate current configuration"""

        # pylint: disable=no-self-use

        logger.info('*** Validating configuration')
        success = True
        # Return result
        return success

    def print_config(self):
        """Pretty print current configuration"""

        print()
        print('****************** CONFIGURATION ******************')
        print()
        print('ArangoDB URL: %s' % self.arango_url)
        print('ArangoDB username: %s' % self.arango_user)
        print('ArangoDB password: %s' % '************')
        print('Kafka servers: %s' % self.kafka_servers)
        print('Enable debug: %s' % self.debug)
        print()
        print('***************************************************')
        print()
        print()

    def import_dependencies(self):
        """Import dependencies"""


# Parse options
def parse_arguments():
    """Command-line arguments parser"""

    # Get parser
    parser = ArgumentParser(
        description='gRPC Southbound APIs for SRv6 Controller'
    )
    parser.add_argument(
        '-e', '--env-file', dest='env_file', action='store',
        default=DEFAULT_ENV_FILE_PATH, help='Path to the .env file '
        'containing the parameters for the node manager'
    )
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Activate debug logs'
    )
    # Parse input parameters
    args = parser.parse_args()
    # Return the arguments
    return args


def __main():
    """Entry point for this module"""

    # Parse command-line arguments
    args = parse_arguments()
    # Path to the .env file containing the parameters for the node manager'
    env_file = args.env_file
    # Create a new configuration object
    config = Config()
    # Load configuration from .env file
    if env_file is not None and os.path.exists(env_file):
        config.load_config(env_file)
    else:
        logger.warning('Configuration file not found. '
                       'Using default configuration.')
    # Process other command-line arguments
    # and replace the parameters defined in .env file
    # (command-line args have priority over environment variables)
    #
    # Setup properly the logger
    if args.debug:
        logger.setLevel(level=logging.DEBUG)
        config.debug = args.debug
    else:
        logger.setLevel(level=logging.INFO)
    # Debug settings
    server_debug = logger.getEffectiveLevel() == logging.DEBUG
    logging.info('SERVER_DEBUG: %s', str(server_debug))
    # Validate configuration
    if not config.validate_config():
        logger.critical('Invalid configuration\n')
        sys.exit(-2)
    # Import dependencies
    config.import_dependencies()
    # Print configuration
    config.print_config()
    # Start the CLI
    ControllerCLI().cmdloop()


if __name__ == '__main__':
    __main()
