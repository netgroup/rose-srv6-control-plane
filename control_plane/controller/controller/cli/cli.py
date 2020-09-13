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


'''
Implementation of a CLI for the SRv6 Controller.
'''

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
import sys
from argparse import ArgumentParser
from cmd import Cmd
from pathlib import Path

# python-dotenv dependencies
from dotenv import load_dotenv
from pkg_resources import resource_filename

# Controller dependencies
from controller.db_utils.arangodb import arangodb_driver
from controller import srv6_usid
from controller.cli import srv6_cli, srv6pm_cli, topo_cli
from controller.db_utils.arangodb.init_db import init_srv6_usid_db

# Folder containing this script
BASE_PATH = os.path.dirname(os.path.realpath(__file__))


# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)

# Configure logging level for urllib3
logging.getLogger('urllib3').setLevel(logging.WARNING)

# Default path to the .env file
DEFAULT_ENV_FILE_PATH = resource_filename(__name__, '../config/controller.env')
# Default value for debug mode
DEFAULT_DEBUG = False

# Path where to save the history file
# We save it to in the same folder of this script
HISTORY_FILE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 '.controller_history')
# Maximum length (in lines) of the history file
# If the history file exceeds this limit, it is truncated
HISTORY_FILE_LENGTH = 1000

# Set line delimiters, required for the auto-completion feature
readline.set_completer_delims(' \t\n')


class CustomCmd(Cmd):
    '''
    This class extends the python class Cmd and implements a handler
    for CTRL+C and CTRL+D
    '''

    # History file
    histfile = os.path.join(HISTORY_FILE_PATH)
    # History size
    histfile_size = HISTORY_FILE_LENGTH

    def preloop(self):
        '''
        Hook method offered by the Cmd library, executed once when cmdloop()
        is called.
        '''
        # If history persistency is enabled, readline library has been
        # imported and the history file already exists...
        if readline and os.path.exists(self.histfile):
            # ...read the history from the history file
            readline.read_history_file(self.histfile)

    def postloop(self):
        '''
        Hook method offered by the Cmd library executed once when cmdloop() is
        about to return. In this method we write the history to the history
        file.
        '''
        # If history persistency is enabled and readline library has been
        # imported
        if readline:
            # Set the number of lines to save in the history file
            # If the history file exceeds the length limit, the history file
            # is truncated
            readline.set_history_length(self.histfile_size)
            # Write the history to the history file
            readline.write_history_file(self.histfile)

    def cmdloop(self, intro=None):
        '''
        CLI loop that accepts commands from the user and dispatch them to the
        methods.

        :param intro: Intro string to be issued before the first prompt.
        :type intro: str, optional
        '''
        # pylint: disable=no-self-use
        #
        # Loop implementing the interpreter for the commands
        while True:
            try:
                # Start CLI loop that accepts commands from the user and
                # dispatch them to the methods
                super(CustomCmd, self).cmdloop(intro=intro)
                break
            except KeyboardInterrupt:
                # Handle CTRL+C
                print('^C')
            except Exception as err:    # pylint: disable=broad-except
                # When an exception is raised, we log the traceback
                # and keep the CLI open and ready to receive next comands
                #
                # We need mute pylint 'broad-except' in order to
                # avoid annoying warnings
                logging.exception(err)
                print()

    def emptyline(self):
        '''
        Method called when an empty line is entered in response to the prompt.
        By default, it repeats the last nonempty command entered. To avoid the
        execution of the last nonempty command, we override this method and
        leave it blank.
        '''
        # pylint: disable=no-self-use

    def default(self, line):
        '''
        Method called on an input line when the command prefix is not
        recognized.

        :param line: The command.
        :type line: str
        :return: True if the command is "quit", False if the command is
                 unrecognized.
        :rtype: bool
        '''
        # If the user entered "x" or "q", exit
        if line in ['x', 'q']:
            return self.do_exit(line)
        # Command unrecognized
        print('Unrecognized command: {}'.format(line))
        return False

    def do_exit(self, args):
        '''
        Go new line on exit.

        :param args: The arguments passed to the command.
        :type args: str
        :return: True.
        :rtype: bool
        '''
        # pylint: disable=unused-argument, no-self-use
        #
        # Print new line and return
        print()
        return True

    def help_exit(self):
        '''
        Help message for exit callback.
        '''
        # pylint: disable=no-self-use
        #
        # Print the help message
        print('exit the application. Shorthand: x q Ctrl-D.')

    # Register handler for the "exit" command
    do_EOF = do_exit
    # Register help for the "exit" command
    help_EOF = help_exit


class ControllerCLITopology(CustomCmd):
    '''
    Topology subsection.
    Subsection of the CLI containing several topology related functions.
    '''

    # Prompt string
    prompt = 'controller(topology)> '

    def do_show_nodes(self, args):
        '''
        Retrieve the nodes from ArangoDB and print the list of the available
        nodes.

        :param args: The argument passed to this command.
        :type args: str
        :return: False in order to leave the CLI subsection open.
        :rtype: bool
        '''
        # pylint: disable=no-self-use, unused-argument
        #
        # Extract the ArangoDB params from the environment variables
        arango_url = os.getenv('ARANGO_URL')
        arango_user = os.getenv('ARANGO_USER')
        arango_password = os.getenv('ARANGO_PASSWORD')
        # Connect to ArangoDB
        client = arangodb_driver.connect_arango(
            url=arango_url)     # TODO keep arango connection open
        # Connect to the "srv6_usid" db
        database = arangodb_driver.connect_srv6_usid_db(
            client=client,
            username=arango_user,
            password=arango_password
        )
        # Extract the nodes configuration stored in the "srv6_usid" database
        nodes_dict = arangodb_driver.get_nodes_config(database)
        # Print the available nodes
        srv6_cli.print_nodes(nodes_dict=nodes_dict)
        # Return False in order to keep the CLI subsection open after the
        # command execution
        return False

    def do_load_nodes_config(self, args):
        '''
        Read the nodes configuration from a YAML file and load it to a Arango
        database.

        :param args: The argument passed to this command.
        :type args: str
        :return: False in order to leave the CLI subsection open.
        :rtype: bool
        '''
        # pylint: disable=no-self-use
        #
        # Parse arguments
        try:
            args = srv6_cli.parse_arguments_load_nodes_config(
                prog='load_nodes_config',
                args=args.split(' ')
            )
        except SystemExit:
            # In case of errors during the parsing, SystemExit will be raised
            # and the process will be terminated
            # In order to avoid the process to be terminated, we handle this
            # exception and we return "False" to leave the CLI subsection open
            return False
        # Extract the ArangoDB params from the environment variables
        arango_url = os.getenv('ARANGO_URL')
        arango_user = os.getenv('ARANGO_USER')
        arango_password = os.getenv('ARANGO_PASSWORD')
        # Connect to ArangoDB
        client = arangodb_driver.connect_arango(
            url=arango_url)     # TODO keep arango connection open
        # Connect to the "srv6_usid" db
        database = arangodb_driver.connect_srv6_usid_db(
            client=client,
            username=arango_user,
            password=arango_password
        )
        # Push the nodes configuration to the database
        arangodb_driver.insert_nodes_config(database, srv6_usid.read_nodes(
            args.nodes_file)[0])
        # Return False in order to keep the CLI subsection open after the
        # command execution
        return False

    def do_extract(self, args):
        '''
        Extract the network topology from a set of nodes running the ISIS
        protocol.

        :param args: The argument passed to this command.
        :type args: str
        :return: False in order to leave the CLI subsection open.
        :rtype: bool
        '''
        # pylint: disable=no-self-use
        #
        # Parse the arguments
        try:
            args = (topo_cli
                    .parse_arguments_topology_information_extraction_isis(
                        prog='extract', args=args.split(' ')))
        except SystemExit:
            # In case of errors during the parsing, SystemExit will be raised
            # and the process will be terminated
            # In order to avoid the process to be terminated, we handle this
            # exception and we return "False" to leave the CLI subsection open
            return False
        # Extract the topology
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
        # Return False in order to keep the CLI subsection open after the
        # command execution
        return False

    def do_load_on_arango(self, args):
        '''
        Read nodes and edges YAML files and upload the topology on ArangoDB.

        :param args: The argument passed to this command.
        :type args: str
        :return: False in order to leave the CLI subsection open.
        :rtype: bool
        '''
        # pylint: disable=no-self-use
        #
        # Parse the arguments
        try:
            args = topo_cli.parse_arguments_load_topo_on_arango(
                prog='load_on_arango',
                args=args.split(' ')
            )
        except SystemExit:
            # In case of errors during the parsing, SystemExit will be raised
            # and the process will be terminated
            # In order to avoid the process to be terminated, we handle this
            # exception and we return "False" to leave the CLI subsection open
            return False
        # Load the topology on Arango database
        topo_cli.load_topo_on_arango(
            arango_url=args.arango_url,
            arango_user=args.arango_user,
            arango_password=args.arango_password,
            nodes_yaml=args.nodes_yaml,
            edges_yaml=args.edges_yaml,
            verbose=args.verbose
        )
        # Return False in order to keep the CLI subsection open after the
        # command execution
        return False

    def do_extract_and_load_on_arango(self, args):
        '''
        Extract the network topology from a set of nodes running ISIS
        and upload it on ArangoDB.

        :param args: The argument passed to this command.
        :type args: str
        :return: False in order to leave the CLI subsection open.
        :rtype: bool
        '''
        # pylint: disable=no-self-use
        #
        # Parse the arguments
        try:
            arg = (topo_cli
                   .parse_arguments_extract_topo_from_isis_and_load_on_arango(
                       prog='extract_and_load_on_arango', args=args.split(' '))
                   )
        except SystemExit:
            # In case of errors during the parsing, SystemExit will be raised
            # and the process will be terminated
            # In order to avoid the process to be terminated, we handle this
            # exception and we return "False" to leave the CLI subsection open
            return False
        # Extract the topology from a set of nodes running the ISIS protocol
        # and load the extracted topology on a Arango database
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
        # Return False in order to keep the CLI subsection open after the
        # command execution
        return False

    def complete_show_nodes(self, text, line, start_idx, end_idx):
        '''
        Auto-completion for show_nodes command.

        :param text: The string prefix we are attempting to match: all
                     returned matches begin with it.
        :type text: str
        :param line: The current input line with leading whitespace removed.
        :type line: str
        :param start_idx: The beginning index of the prefix text.
        :type start_idx: int
        :param end_idx: The ending index of the prefix text.
        :type end_idx: int
        :return: A list containing all the possible matches.
        :rtype: list
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
        # Call auto-completion function and return a list of possible
        # arguments
        return srv6_cli.complete_print_nodes(text, prev_text)

    def complete_load_nodes_config(self, text, line, start_idx, end_idx):
        '''
        Auto-completion for load_nodes_config command.

        :param text: The string prefix we are attempting to match: all
                     returned matches begin with it.
        :type text: str
        :param line: The current input line with leading whitespace removed.
        :type line: str
        :param start_idx: The beginning index of the prefix text.
        :type start_idx: int
        :param end_idx: The ending index of the prefix text.
        :type end_idx: int
        :return: A list containing all the possible matches.
        :rtype: list
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
        # Call auto-completion function and return a list of possible
        # arguments
        return srv6_cli.complete_load_nodes_config(text, prev_text)

    def complete_extract(self, text, line, start_idx, end_idx):
        '''
        Auto-completion for extract command.

        :param text: The string prefix we are attempting to match: all
                     returned matches begin with it.
        :type text: str
        :param line: The current input line with leading whitespace removed.
        :type line: str
        :param start_idx: The beginning index of the prefix text.
        :type start_idx: int
        :param end_idx: The ending index of the prefix text.
        :type end_idx: int
        :return: A list containing all the possible matches.
        :rtype: list
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
        # Call auto-completion function and return a list of possible
        # arguments
        return topo_cli.complete_topology_information_extraction_isis(
            text, prev_text)

    def complete_load_on_arango(self, text, line, start_idx, end_idx):
        '''
        Auto-completion for load_on_arango command.

        :param text: The string prefix we are attempting to match: all
                     returned matches begin with it.
        :type text: str
        :param line: The current input line with leading whitespace removed.
        :type line: str
        :param start_idx: The beginning index of the prefix text.
        :type start_idx: int
        :param end_idx: The ending index of the prefix text.
        :type end_idx: int
        :return: A list containing all the possible matches.
        :rtype: list
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
        # Call auto-completion function and return a list of possible
        # arguments
        return topo_cli.complete_load_topo_on_arango(text, prev_text)

    def complete_extract_and_load_on_arango(self, text,
                                            line, start_idx, end_idx):
        '''
        Auto-completion for extract_and_load_on_arango command.

        :param text: The string prefix we are attempting to match: all
                     returned matches begin with it.
        :type text: str
        :param line: The current input line with leading whitespace removed.
        :type line: str
        :param start_idx: The beginning index of the prefix text.
        :type start_idx: int
        :param end_idx: The ending index of the prefix text.
        :type end_idx: int
        :return: A list containing all the possible matches.
        :rtype: list
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
        # Call auto-completion function and return a list of possible
        # arguments
        return (topo_cli
                .complete_extract_topo_from_isis_and_load_on_arango(
                    text, prev_text))

    def help_show_nodes(self):
        '''
        Show help usage for show_nodes config command.
        '''
        # pylint: disable=no-self-use
        #
        # Print the help usage
        srv6_cli.parse_arguments_print_nodes(
            prog='show_nodes',
            args=['--help']
        )

    def help_load_nodes_config(self):
        '''
        Show help usage for load_nodes_config command.
        '''
        # pylint: disable=no-self-use
        #
        # Print the help usage
        srv6_cli.parse_arguments_load_nodes_config(
            prog='load_nodes_config',
            args=['--help']
        )

    def help_extract(self):
        '''
        Show help usage for extract command.
        '''
        # pylint: disable=no-self-use
        #
        # Print the help usage
        topo_cli.parse_arguments_topology_information_extraction_isis(
            prog='extract',
            args=['--help']
        )

    def help_load_on_arango(self):
        '''
        Show help usage for load_topo_on_arango.
        '''
        # pylint: disable=no-self-use
        #
        # Print the help usage
        topo_cli.parse_arguments_load_topo_on_arango(
            prog='load_on_arango',
            args=['--help']
        )

    def help_extract_and_load_on_arango(self):
        '''
        Show help usage for extract_and_load_on_arango.
        '''
        # pylint: disable=no-self-use
        #
        # Print the help usage
        topo_cli.parse_arguments_extract_topo_from_isis_and_load_on_arango(
            prog='extract_and_load_on_arango',
            args=['--help']
        )


class ControllerCLISRv6PMConfiguration(CustomCmd):
    '''
    srv6pm->Configuration subsection.
    Subsection of the CLI containing several functions for SRv6 Performance
    Monitoring configuration.
    '''

    # Prompt string
    prompt = 'controller(srv6pm-configuration)> '

    def do_set(self, args):
        '''
        Set the configuation for an experiment. Before running an experiment
        you need to set the configuration.

        :param args: The arguments passed to the command.
        :type args: str
        :return: False.
        :rtype: bool
        '''
        # pylint: disable=no-self-use
        #
        # Parse the arguments
        try:
            args = srv6pm_cli.parse_arguments_set_configuration(
                prog='start',
                args=args.split(' ')
            )
        except SystemExit:
            # In case of errors during the parsing, SystemExit will be raised
            # and the process will be terminated
            # In order to avoid the process to be terminated, we handle this
            # exception and we return "False" to leave the CLI subsection open
            return False
        # Set the configuration
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
        # Return False in order to keep the CLI subsection open after the
        # command execution
        return False

    def do_reset(self, args):
        '''
        Clear the configuration and reset the nodes.

        :param args: The arguments passed to the command.
        :type args: str
        :return: False.
        :rtype: bool
        '''
        # pylint: disable=no-self-use
        #
        # Parse the arguments
        try:
            args = srv6pm_cli.parse_arguments_reset_configuration(
                prog='start',
                args=args.split(' ')
            )
        except SystemExit:
            # In case of errors during the parsing, SystemExit will be raised
            # and the process will be terminated
            # In order to avoid the process to be terminated, we handle this
            # exception and we return "False" to leave the CLI subsection open
            return False
        # Clear the configuration
        srv6pm_cli.reset_configuration(
            sender=args.sender_ip,
            reflector=args.reflector_ip,
            sender_port=args.sender_port,
            reflector_port=args.reflector_port,
        )
        # Return False in order to keep the CLI subsection open after the
        # command execution
        return False

    def complete_set(self, text, line, start_idx, end_idx):
        '''
        Auto-completion for set command.

        :param text: The string prefix we are attempting to match: all
                     returned matches begin with it.
        :type text: str
        :param line: The current input line with leading whitespace removed.
        :type line: str
        :param start_idx: The beginning index of the prefix text.
        :type start_idx: int
        :param end_idx: The ending index of the prefix text.
        :type end_idx: int
        :return: A list containing all the possible matches.
        :rtype: list
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
        return srv6pm_cli.complete_set_configuration(text, prev_text)

    def complete_reset(self, text, line, start_idx, end_idx):
        '''
        Auto-completion for reset command.

        :param text: The string prefix we are attempting to match: all
                     returned matches begin with it.
        :type text: str
        :param line: The current input line with leading whitespace removed.
        :type line: str
        :param start_idx: The beginning index of the prefix text.
        :type start_idx: int
        :param end_idx: The ending index of the prefix text.
        :type end_idx: int
        :return: A list containing all the possible matches.
        :rtype: list
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
        return srv6pm_cli.complete_reset_configuration(text, prev_text)

    def help_set(self):
        '''
        Show help usagte for set operation.
        '''
        # pylint: disable=no-self-use
        #
        # Show the help usage
        srv6pm_cli.parse_arguments_set_configuration(
            prog='start',
            args=['--help']
        )

    def help_reset(self):
        '''
        Show help usage for reset operation.
        '''
        # pylint: disable=no-self-use
        #
        # Show the help usage
        srv6pm_cli.parse_arguments_reset_configuration(
            prog='start',
            args=['--help']
        )


class ControllerCLISRv6PMExperiment(CustomCmd):
    '''
    srv6pm->experiment subsection.
    Subsection of the CLI containing several functions for SRv6 Performance
    Monitoring experiments.
    '''

    # Prompt string
    prompt = 'controller(srv6pm-experiment)> '

    def do_start(self, args):
        '''Start an experiment'''
        # pylint: disable=no-self-use
        #
        # Parse the arguments
        try:
            args = srv6pm_cli.parse_arguments_start_experiment(
                prog='start',
                args=args.split(' ')
            )
        except SystemExit:
            # In case of errors during the parsing, SystemExit will be raised
            # and the process will be terminated
            # In order to avoid the process to be terminated, we handle this
            # exception and we return "False" to leave the CLI subsection open
            return False
        # Start an experiment
        srv6pm_cli.start_experiment(
            sender=args.sender_ip,
            reflector=args.reflector_ip,
            sender_port=args.sender_port,
            reflector_port=args.reflector_port,
            send_refl_dest=args.send_refl_dest,
            refl_send_dest=args.refl_send_dest,
            send_refl_sidlist=args.send_refl_sidlist,
            refl_send_sidlist=args.refl_send_sidlist,
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
        # Return False in order to keep the CLI subsection open after the
        # command execution
        return False

    def do_show(self, args):
        '''
        Show results of a running experiment.

        :param args: The arguments passed to the command.
        :type args: str
        :return: False.
        :rtype: bool
        '''
        # pylint: disable=no-self-use
        #
        # Parse the arguments
        try:
            args = srv6pm_cli.parse_arguments_get_experiment_results(
                prog='show',
                args=args.split(' ')
            )
        except SystemExit:
            # In case of errors during the parsing, SystemExit will be raised
            # and the process will be terminated
            # In order to avoid the process to be terminated, we handle this
            # exception and we return "False" to leave the CLI subsection open
            return False
        # Get results
        srv6pm_cli.get_experiment_results(
            sender=args.sender_ip,
            reflector=args.reflector_ip,
            sender_port=args.sender_port,
            reflector_port=args.reflector_port,
            send_refl_sidlist=args.send_refl_sidlist,
            refl_send_sidlist=args.refl_send_sidlist
        )
        # Return False in order to keep the CLI subsection open after the
        # command execution
        return False

    def do_stop(self, args):
        '''
        Stop a running experiment.

        :param args: The arguments passed to the command.
        :type args: str
        :return: False.
        :rtype: bool
        '''
        # pylint: disable=no-self-use
        #
        # Parse the arguments
        try:
            args = srv6pm_cli.parse_arguments_stop_experiment(
                prog='stop',
                args=args.split(' ')
            )
        except SystemExit:
            # In case of errors during the parsing, SystemExit will be raised
            # and the process will be terminated
            # In order to avoid the process to be terminated, we handle this
            # exception and we return "False" to leave the CLI subsection open
            return False
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
        # Return False in order to keep the CLI subsection open after the
        # command execution
        return False

    def complete_start(self, text, line, start_idx, end_idx):
        '''
        Auto-completion for start command.

        :param text: The string prefix we are attempting to match: all
                     returned matches begin with it.
        :type text: str
        :param line: The current input line with leading whitespace removed.
        :type line: str
        :param start_idx: The beginning index of the prefix text.
        :type start_idx: int
        :param end_idx: The ending index of the prefix text.
        :type end_idx: int
        :return: A list containing all the possible matches.
        :rtype: list
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
        # Call auto-completion function and return a list of possible
        # arguments
        return srv6pm_cli.complete_start_experiment(text, prev_text)

    def complete_show(self, text, line, start_idx, end_idx):
        '''
        Auto-completion for show command.

        :param text: The string prefix we are attempting to match: all
                     returned matches begin with it.
        :type text: str
        :param line: The current input line with leading whitespace removed.
        :type line: str
        :param start_idx: The beginning index of the prefix text.
        :type start_idx: int
        :param end_idx: The ending index of the prefix text.
        :type end_idx: int
        :return: A list containing all the possible matches.
        :rtype: list
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
        # Call auto-completion function and return a list of possible
        # arguments
        return srv6pm_cli.complete_get_experiment_results(text, prev_text)

    def complete_stop(self, text, line, start_idx, end_idx):
        '''
        Auto-completion for stop command.

        :param text: The string prefix we are attempting to match: all
                     returned matches begin with it.
        :type text: str
        :param line: The current input line with leading whitespace removed.
        :type line: str
        :param start_idx: The beginning index of the prefix text.
        :type start_idx: int
        :param end_idx: The ending index of the prefix text.
        :type end_idx: int
        :return: A list containing all the possible matches.
        :rtype: list
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
        # Call auto-completion function and return a list of possible
        # arguments
        return srv6pm_cli.complete_stop_experiment(text, prev_text)

    def help_start(self):
        '''
        Show help usage for start operation.
        '''
        # pylint: disable=no-self-use
        #
        # Print the help usage
        srv6pm_cli.parse_arguments_start_experiment(
            prog='start',
            args=['--help']
        )

    def help_show(self):
        '''
        Show help usasge for show operation.
        '''
        # pylint: disable=no-self-use
        #
        # Print the help usage
        srv6pm_cli.parse_arguments_get_experiment_results(
            prog='show',
            args=['--help']
        )

    def help_stop(self):
        '''
        Show help usage for stop operation.
        '''
        # pylint: disable=no-self-use
        #
        # Print the help usage
        srv6pm_cli.parse_arguments_stop_experiment(
            prog='stop',
            args=['--help']
        )


class ControllerCLISRv6PM(CustomCmd):
    '''
    srv6pm subcommmand.
    Subsection of the CLI containing several functions for SRv6 Performance
    Monitoring.
    '''

    # Prompt string
    prompt = 'controller(srv6pm)> '

    def do_experiment(self, args):
        '''
        Enter srv6pm-experiment subsection.

        :param args: The arguments passed to the command.
        :type args: str
        :return: False.
        :rtype: bool
        '''
        # pylint: disable=no-self-use, unused-argument
        #
        # Start SRv6 PM Experiment command loop
        sub_cmd = ControllerCLISRv6PMExperiment()
        sub_cmd.cmdloop()

    def do_configuration(self, args):
        '''
        Enter srv6pm-configuration subsection.

        :param args: The arguments passed to the command.
        :type args: str
        :return: False.
        :rtype: bool
        '''
        # pylint: disable=no-self-use, unused-argument
        #
        # Start SRv6 PM Experiment command loop
        sub_cmd = ControllerCLISRv6PMConfiguration()
        sub_cmd.cmdloop()


class ControllerCLISRv6(CustomCmd):
    '''
    srv6 subsection.
    Subsection of the CLI containing several functions for SRv6.
    '''

    # Prompt string
    prompt = 'controller(srv6)> '

    def do_path(self, args):
        '''
        Handle a SRv6 path.

        :param args: The arguments passed to the command.
        :type args: str
        :return: False.
        :rtype: bool
        '''
        # pylint: disable=no-self-use
        #
        # Parse the arguments
        try:
            args = srv6_cli.parse_arguments_srv6_path(
                prog='path',
                args=args.split(' ')
            )
        except SystemExit:
            # In case of errors during the parsing, SystemExit will be raised
            # and the process will be terminated
            # In order to avoid the process to be terminated, we handle this
            # exception and we return "False" to leave the CLI subsection open
            return False
        # Handle the SRv6 path
        srv6_cli.handle_srv6_path(
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
        # Return False in order to keep the CLI subsection open after the
        # command execution
        return False

    def do_behavior(self, args):
        '''
        Handle a SRv6 behavior.

        :param args: The arguments passed to the command.
        :type args: str
        :return: False.
        :rtype: bool
        '''
        # pylint: disable=no-self-use
        #
        # Parse the arguments
        try:
            args = srv6_cli.parse_arguments_srv6_behavior(
                prog='behavior',
                args=args.split(' ')
            )
        except SystemExit:
            # In case of errors during the parsing, SystemExit will be raised
            # and the process will be terminated
            # In order to avoid the process to be terminated, we handle this
            # exception and we return "False" to leave the CLI subsection open
            return False
        # Handle SRv6 behavior
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
            metric=args.metric,
            fwd_engine=args.fwd_engine
        )
        # Return False in order to keep the CLI subsection open after the
        # command execution
        return False

    def do_unitunnel(self, args):
        '''
        Handle a SRv6 unidirectional tunnel.

        :param args: The arguments passed to the command.
        :type args: str
        :return: False.
        :rtype: bool
        '''
        # pylint: disable=no-self-use
        #
        # Parse the arguments
        try:
            args = srv6_cli.parse_arguments_srv6_unitunnel(
                prog='unitunnel',
                args=args.split(' ')
            )
        except SystemExit:
            # In case of errors during the parsing, SystemExit will be raised
            # and the process will be terminated
            # In order to avoid the process to be terminated, we handle this
            # exception and we return "False" to leave the CLI subsection open
            return False
        # Handle SRv6 unidirectional tunnel
        srv6_cli.handle_srv6_unitunnel(
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
        # Return False in order to keep the CLI subsection open after the
        # command execution
        return False

    def do_biditunnel(self, args):
        '''
        Handle a SRv6 bidirectional tunnel.

        :param args: The arguments passed to the command.
        :type args: str
        :return: False.
        :rtype: bool
        '''
        # pylint: disable=no-self-use
        #
        # Parse the arguments
        try:
            args = srv6_cli.parse_arguments_srv6_biditunnel(
                prog='biditunnel',
                args=args.split(' ')
            )
        except SystemExit:
            # In case of errors during the parsing, SystemExit will be raised
            # and the process will be terminated
            # In order to avoid the process to be terminated, we handle this
            # exception and we return "False" to leave the CLI subsection open
            return False
        # Handle SRv6 bidirectional tunnel
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
            localseg_rl=args.localseg_rl,
            bsid_addr=args.bsid_addr,
            fwd_engine=args.fwd_engine
        )
        # Return False in order to keep the CLI subsection open after the
        # command execution
        return False

    def do_usid_policy(self, args):
        '''
        Handle a SRv6 uSID policy.

        :param args: The arguments passed to the command.
        :type args: str
        :return: False.
        :rtype: bool
        '''
        # pylint: disable=no-self-use, unused-argument
        #
        # Parse the arguments
        try:
            args = srv6_cli.parse_arguments_srv6_usid_policy(
                prog='usid_policy',
                args=args.split(' ')
            )
        except SystemExit:
            # In case of errors during the parsing, SystemExit will be raised
            # and the process will be terminated
            # In order to avoid the process to be terminated, we handle this
            # exception and we return "False" to leave the CLI subsection open
            return False
        # Extract the ArangoDB params from the environment variables
        arango_url = os.getenv('ARANGO_URL')
        arango_user = os.getenv('ARANGO_USER')
        arango_password = os.getenv('ARANGO_PASSWORD')
        # Connect to ArangoDB
        client = arangodb_driver.connect_arango(
            url=arango_url)     # TODO keep arango connection open
        # Connect to the "srv6_usid" db
        database = arangodb_driver.connect_srv6_usid_db(
            client=client,
            username=arango_user,
            password=arango_password
        )
        # Retrieve the nodes configuration from the database
        nodes_dict = arangodb_driver.get_nodes_config(database)
        # Handle the uSID policy
        srv6_cli.handle_srv6_usid_policy(
            operation=args.op,
            nodes_dict=nodes_dict,
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
        srv6_cli.print_nodes(nodes_dict=nodes_dict)
        # Return False in order to keep the CLI subsection open after the
        # command execution
        return False

    def complete_path(self, text, line, start_idx, end_idx):
        '''
        Auto-completion for path command.

        :param text: The string prefix we are attempting to match: all
                     returned matches begin with it.
        :type text: str
        :param line: The current input line with leading whitespace removed.
        :type line: str
        :param start_idx: The beginning index of the prefix text.
        :type start_idx: int
        :param end_idx: The ending index of the prefix text.
        :type end_idx: int
        :return: A list containing all the possible matches.
        :rtype: list
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
        # Call auto-completion function and return a list of possible
        # arguments
        return srv6_cli.complete_srv6_path(text, prev_text)

    def complete_behavior(self, text, line, start_idx, end_idx):
        '''
        Auto-completion for behavior command.

        :param text: The string prefix we are attempting to match: all
                     returned matches begin with it.
        :type text: str
        :param line: The current input line with leading whitespace removed.
        :type line: str
        :param start_idx: The beginning index of the prefix text.
        :type start_idx: int
        :param end_idx: The ending index of the prefix text.
        :type end_idx: int
        :return: A list containing all the possible matches.
        :rtype: list
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
        # Call auto-completion function and return a list of possible
        # arguments
        return srv6_cli.complete_srv6_behavior(text, prev_text)

    def complete_unitunnel(self, text, line, start_idx, end_idx):
        '''
        Auto-completion for unitunnel command.

        :param text: The string prefix we are attempting to match: all
                     returned matches begin with it.
        :type text: str
        :param line: The current input line with leading whitespace removed.
        :type line: str
        :param start_idx: The beginning index of the prefix text.
        :type start_idx: int
        :param end_idx: The ending index of the prefix text.
        :type end_idx: int
        :return: A list containing all the possible matches.
        :rtype: list
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
        # Call auto-completion function and return a list of possible
        # arguments
        return srv6_cli.complete_srv6_unitunnel(text, prev_text)

    def complete_biditunnel(self, text, line, start_idx, end_idx):
        '''
        Auto-completion for biditunnel command.

        :param text: The string prefix we are attempting to match: all
                     returned matches begin with it.
        :type text: str
        :param line: The current input line with leading whitespace removed.
        :type line: str
        :param start_idx: The beginning index of the prefix text.
        :type start_idx: int
        :param end_idx: The ending index of the prefix text.
        :type end_idx: int
        :return: A list containing all the possible matches.
        :rtype: list
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
        # Call auto-completion function and return a list of possible
        # arguments
        return srv6_cli.complete_srv6_biditunnel(text, prev_text)

    def complete_usid_policy(self, text, line, start_idx, end_idx):
        '''
        Auto-completion for usid_policy command.

        :param text: The string prefix we are attempting to match: all
                     returned matches begin with it.
        :type text: str
        :param line: The current input line with leading whitespace removed.
        :type line: str
        :param start_idx: The beginning index of the prefix text.
        :type start_idx: int
        :param end_idx: The ending index of the prefix text.
        :type end_idx: int
        :return: A list containing all the possible matches.
        :rtype: list
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
        # Call auto-completion function and return a list of possible
        # arguments
        return srv6_cli.complete_usid_policy(text, prev_text)

    def help_path(self):
        '''
        Show help usage for path command.
        '''
        # pylint: disable=no-self-use
        #
        # Show the help usage
        srv6_cli.parse_arguments_srv6_path(
            prog='path',
            args=['--help']
        )

    def help_behavior(self):
        '''
        Show help usage for behavior command.
        '''
        # pylint: disable=no-self-use
        #
        # Show the help usage
        srv6_cli.parse_arguments_srv6_behavior(
            prog='behavior',
            args=['--help']
        )

    def help_unitunnel(self):
        '''
        Show help usage for unitunnel command.
        '''
        # pylint: disable=no-self-use
        #
        # Show the help usage
        srv6_cli.parse_arguments_srv6_unitunnel(
            prog='unitunnel',
            args=['--help']
        )

    def help_biditunnel(self):
        '''
        Show help usage for biditunnel command.
        '''
        # pylint: disable=no-self-use
        #
        # Show the help usage
        srv6_cli.parse_arguments_srv6_biditunnel(
            prog='biditunnel',
            args=['-help']
        )

    def help_usid_policy(self):
        '''
        Show help usage for usid_policy command.
        '''
        # pylint: disable=no-self-use
        #
        # Show the help usage
        srv6_cli.parse_arguments_usid_policy(
            prog='usid_policy',
            args=['--help']
        )


class ControllerCLI(CustomCmd):
    '''
    Controller CLI entry point.
    '''

    # Prompt string
    prompt = 'controller> '
    # Intro message
    intro = 'Welcome! Type ? to list commands'

    def do_exit(self, args):
        '''
        Exit from the CLI.

        :param args: The arguments passed to the command.
        :type args: str
        :return: True.
        :rtype: bool
        '''
        # pylint: disable=no-self-use, unused-argument
        #
        # Print bye message and return
        print('Bye')
        return True

    def do_srv6(self, args):
        '''
        Enter srv6 subsection.

        :param args: The arguments passed to the command.
        :type args: str
        '''
        # pylint: disable=no-self-use, unused-argument
        #
        # Start the SRv6 command loop
        sub_cmd = ControllerCLISRv6()
        sub_cmd.cmdloop()

    def do_srv6pm(self, args):
        '''
        Enter srv6pm subsection.

        :param args: The arguments passed to the command.
        :type args: str
        '''
        # pylint: disable=no-self-use, unused-argument
        #
        # Start the SRv6 PM command loop
        sub_cmd = ControllerCLISRv6PM()
        sub_cmd.cmdloop()

    def do_topology(self, args):
        '''
        Enter topology subsection.

        :param args: The arguments passed to the command.
        :type args: str
        '''
        # pylint: disable=no-self-use, unused-argument
        #
        # Start the Topology command loop
        sub_cmd = ControllerCLITopology()
        sub_cmd.cmdloop()

    def default(self, line):
        '''
        Default behavior.

        :param line: The command.
        :type line: str
        :return: True if the command is "quit", False if the command is
                 unrecognized.
        :rtype: bool
        '''
        # If the user entered "x" or "q", exit
        if line in ['x', 'q']:
            return self.do_exit(line)
        # Command unrecognized
        print('Unrecognized command: {}'.format(line))
        return False

    # Register handler for the "exit" command
    do_EOF = do_exit


# Class representing the configuration
class Config:
    '''
    Class implementing configuration for the Controller.
    '''

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
        '''
        Load configuration from a .env file

        :param env_file: The path and the name of the .env file containing the
                         nodes configuration.
        :type env_file: str
        '''
        # Load configuration from .env file
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
        '''
        Validate current configuration.

        :return: True if the configuraation is valid, False otherwise.
        :rtype: bool
        '''
        # pylint: disable=no-self-use
        #
        # Validate configuration
        # TODO
        logger.info('*** Validating configuration')
        success = True
        # Return result
        return success

    def print_config(self):
        '''
        Pretty print current configuration.
        '''
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
        '''
        Import dependencies.
        '''


# Parse options
def parse_arguments():
    '''
    Command-line arguments parser.
    '''
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
    '''
    Entry point for this module.
    '''
    # Parse command-line arguments
    args = parse_arguments()
    # Path to the .env file containing the parameters for the node manager'
    env_file = args.env_file
    # Initialize database
    init_srv6_usid_db()
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
