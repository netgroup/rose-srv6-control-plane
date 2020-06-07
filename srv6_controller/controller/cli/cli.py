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


from . import topo_cli
from . import srv6pm_cli
from . import srv6_cli
from dotenv import load_dotenv
from pathlib import Path
import logging
from cmd import Cmd
import sys
from argparse import ArgumentParser
import os

# Folder containing this script
BASE_PATH = os.path.dirname(os.path.realpath(__file__))


# Logger reference
logger = logging.getLogger(__name__)

# import utils
# import srv6_controller
# import ti_extraction
# import srv6_pm

# ArangoDB params
ARANGO_USER = None
ARANGO_PASSWORD = None
ARANGO_URL = None
# Kafka params
KAFKA_SERVERS = None
# Default path to the .env file
DEFAULT_ENV_FILE_PATH = os.path.join(BASE_PATH, '../.env')
# Default value for debug mode
DEFAULT_DEBUG = False


class CustomCmd(Cmd):

    def cmdloop(self, intro=None):
        while True:
            try:
                super(CustomCmd, self).cmdloop(intro=intro)
                break
            except KeyboardInterrupt:
                print("^C")

    def emptyline(self):
        pass

    def default(self, inp):
        if inp == 'x' or inp == 'q':
            return self.do_exit(inp)

        print("Unrecognized command: {}".format(inp))

    def do_exit(self, args):
        print()     # New line
        return True

    def help_exit(self):
        print('exit the application. Shorthand: x q Ctrl-D.')

    do_EOF = do_exit
    help_EOF = help_exit


class ControllerCLITopology(CustomCmd):
    prompt = "controller(topology)> "

    def do_extract(self, args):
        try:
            args = topo_cli.parse_arguments_topology_information_extraction_isis(
                prog='extract',
                args=args.split(' ')
            )
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        topo_cli.topology_information_extraction_isis(
            routers=args.routers.split(','),
            period=args.period,
            isisd_pwd=args.isisd_pwd,
            topo_file_json=args.topo_file_json,
            nodes_file_yaml=args.nodes_file_yaml,
            edges_file_yaml=args.edges_file_yaml,
            topo_graph=args.topo_graph,
            verbose=args.verbose
        )

    def do_load_on_arango(self, args):
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

    def do_extract_and_load_on_arango(self, args):
        try:
            args = topo_cli.parse_arguments_extract_topo_from_isis_and_load_on_arango(
                prog='extract_and_load_on_arango',
                args=args.split(' ')
            )
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        topo_cli.extract_topo_from_isis_and_load_on_arango(
            isis_nodes=args.isis_nodes.split(','),
            isisd_pwd=args.isisd_pwd,
            arango_url=args.arango_url,
            arango_user=args.arango_user,
            arango_password=args.arango_password,
            nodes_yaml=args.nodes_yaml,
            edges_yaml=args.edges_yaml,
            period=args.period,
            verbose=args.verbose
        )


class ControllerCLISRv6PMConfiguration(CustomCmd):
    prompt = "controller(srv6pm-configuration)> "

    def do_set(self, args):
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

    def do_reset(self, args):
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

    def help_path(self):
        srv6_cli.parse_arguments_srv6_path()

    def help_behavior(self):
        srv6_cli.parse_arguments_srv6_behavior()

    def help_tunnel(self):
        srv6_cli.parse_arguments_srv6_tunnel()


class ControllerCLISRv6PMExperiment(CustomCmd):
    prompt = "controller(srv6pm-experiment)> "

    def do_start(self, args):
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
            # send_in_interfaces=args.send_in_interfaces,       # Moved to set_configuration
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

    def do_show(self, args):
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

    def do_stop(self, args):
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

    def help_path(self):
        srv6_cli.parse_arguments_srv6_path()

    def help_behavior(self):
        srv6_cli.parse_arguments_srv6_behavior()

    def help_tunnel(self):
        srv6_cli.parse_arguments_srv6_tunnel()


class ControllerCLISRv6PM(CustomCmd):
    prompt = "controller(srv6pm)> "

    def do_experiment(self, args):
        sub_cmd = ControllerCLISRv6PMExperiment()
        sub_cmd.cmdloop()

    def do_configuration(self, args):
        sub_cmd = ControllerCLISRv6PMConfiguration()
        sub_cmd.cmdloop()


class ControllerCLISRv6(CustomCmd):
    prompt = "controller(srv6)> "

    def do_path(self, args):
        try:
            args = srv6_cli.parse_arguments_srv6_path(
                prog='path',
                args=args.split(' ')
            )
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        srv6_cli.handle_srv6_path(
            op=args.op,
            grpc_address=args.grpc_ip,
            grpc_port=args.grpc_port,
            destination=args.destination,
            segments=args.segments,
            device=args.device,
            encapmode=args.encapmode,
            table=args.table,
            metric=args.metric
        )

    def do_behavior(self, args):
        try:
            args = srv6_cli.parse_arguments_srv6_behavior(
                prog='behavior',
                args=args.split(' ')
            )
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        srv6_cli.handle_srv6_behavior(
            op=args.op,
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

    def do_unitunnel(self, args):
        try:
            args = srv6_cli.parse_arguments_srv6_unitunnel(
                prog='tunnel',
                args=args.split(' ')
            )
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        srv6_cli.handle_srv6_unitunnel(
            op=args.op,
            ingress_ip=args.ingress_grpc_ip,
            ingress_port=args.ingress_grpc_port,
            egress_ip=args.egress_grpc_ip,
            egress_port=args.egress_grpc_port,
            destination=args.dest,
            segments=args.sidlist,
            localseg=args.localseg
        )

    def do_biditunnel(self, args):
        try:
            args = srv6_cli.parse_arguments_srv6_biditunnel(
                prog='tunnel',
                args=args.split(' ')
            )
        except SystemExit:
            return False  # This workaround avoid exit in case of errors
        srv6_cli.handle_srv6_biditunnel(
            op=args.op,
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

    def help_path(self):
        srv6_cli.parse_arguments_srv6_path()

    def help_behavior(self):
        srv6_cli.parse_arguments_srv6_behavior()

    def help_tunnel(self):
        srv6_cli.parse_arguments_srv6_tunnel()


class ControllerCLI(CustomCmd):
    prompt = 'controller> '
    intro = "Welcome! Type ? to list commands"

    def do_exit(self, inp):
        print("Bye")
        return True

    def do_srv6(self, args):
        sub_cmd = ControllerCLISRv6()
        sub_cmd.cmdloop()

    def do_srv6pm(self, args):
        sub_cmd = ControllerCLISRv6PM()
        sub_cmd.cmdloop()

    def do_topology(self, args):
        sub_cmd = ControllerCLITopology()
        sub_cmd.cmdloop()

    def default(self, inp):
        if inp == 'x' or inp == 'q':
            return self.do_exit(inp)

        print("Unrecognized command: {}".format(inp))

    do_EOF = do_exit


# Class representing the configuration
class Config:
    # Folder containing the files auto-generated from proto files
    PROTO_PATH = None
    # ArangoDB username
    ARANGO_USER = None
    # ArangoDB password
    ARANGO_PASSWORD = None
    # ArangoDB URL
    ARANGO_URL = None
    # Configure Kafka servers
    KAFKA_SERVERS = None
    # Define whether to enable the debug mode or not
    DEBUG = DEFAULT_DEBUG

    # Load configuration from .env file
    def load_config(self, env_file):
        logger.info('*** Loading configuration from %s' % env_file)
        # Path to the .env file
        env_path = Path(env_file)
        # Load environment variables from .env file
        load_dotenv(dotenv_path=env_path)
        # Folder containing the files auto-generated from proto files
        if os.getenv('PROTO_PATH') is not None:
            self.PROTO_PATH = os.getenv('PROTO_PATH')
        # ArangoDB username
        if os.getenv('ARANGO_USER') is not None:
            self.ARANGO_USER = os.getenv('ARANGO_USER')
        # ArangoDB password
        if os.getenv('ARANGO_PASSWORD') is not None:
            self.ARANGO_PASSWORD = os.getenv('ARANGO_PASSWORD')
        # ArangoDB URL
        if os.getenv('ARANGO_URL') is not None:
            self.ARANGO_URL = os.getenv('ARANGO_URL')
        # Kafka servers
        if os.getenv('KAFKA_SERVERS') is not None:
            self.KAFKA_SERVERS = os.getenv('KAFKA_SERVERS')
        # Define whether to enable the debug mode or not
        if os.getenv('DEBUG') is not None:
            self.DEBUG = os.getenv('DEBUG')
            # Values provided in .env files are returned as strings
            # We need to convert them to bool
            if self.DEBUG.lower() == 'true':
                self.DEBUG = True
            elif self.DEBUG.lower() == 'false':
                self.DEBUG = False
            else:
                # Invalid value for this parameter
                self.DEBUG = None

    def validate_config(self):
        logger.info('*** Validating configuration')
        success = True
        # Validate PROTO_PATH
        if self.PROTO_PATH is None:
            logger.critical('Set PROTO_PATH variable in configuration file '
                            '(.env file)')
            success = False
        if self.PROTO_PATH is not None and \
                not os.path.exists(self.PROTO_PATH):
            logger.critical('PROTO_PATH variable in .env points '
                            'to a non existing folder: %s' % self.PROTO_PATH)
            success = False
        # Return result
        return success

    def import_dependencies(self):
        # Append proto path
        sys.path.append(self.PROTO_PATH)


# Parse options
def parse_arguments():
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
    global ARANGO_USER, ARANGO_PASSWORD, ARANGO_URL, KAFKA_SERVERS
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
        config.DEBUG = args.debug
    else:
        logger.setLevel(level=logging.INFO)
    # Debug settings
    server_debug = logger.getEffectiveLevel() == logging.DEBUG
    logging.info('SERVER_DEBUG:' + str(server_debug))
    # Validate configuration
    if not config.validate_config():
        logger.critical('Invalid configuration\n')
        exit(-2)
    # Import dependencies
    config.import_dependencies()
    # Extract parameters from the configuration
    ARANGO_USER = config.ARANGO_USER
    ARANGO_PASSWORD = config.ARANGO_PASSWORD
    ARANGO_URL = config.ARANGO_URL
    KAFKA_SERVERS = config.KAFKA_SERVERS
    # Start the CLI
    ControllerCLI().cmdloop()


if __name__ == '__main__':
    __main()
