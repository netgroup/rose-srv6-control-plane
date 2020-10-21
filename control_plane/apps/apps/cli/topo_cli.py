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


"""
ArangoDB utilities for Controller CLI.
"""

# General imports
import sys
import yaml
from argparse import ArgumentParser

# Controller dependencies
from apps.nb_grpc_client import topo_manager
from apps.cli import utils as cli_utils

# Interval between two consecutive extractions (in seconds)
DEFAULT_TOPO_EXTRACTION_PERIOD = 0


def extract_topo_from_isis(controller_channel, isis_nodes, isisd_pwd,
                           nodes_yaml, edges_yaml,
                           addrs_yaml=None, hosts_yaml=None,
                           verbose=False):
    """
    Extract the network topology from a set of nodes running
    ISIS protocol.
    """
    # pylint: disable=too-many-arguments
    #
    # Read addresses configuration from YAML file
    addrs_config = cli_utils.load_yaml_dump(addrs_yaml)
    # Read hosts configuration from YAML file
    hosts_config = cli_utils.load_yaml_dump(hosts_yaml)
    # Extract the network topology
    nodes, edges = topo_manager.extract_topo_from_isis(
        controller_channel=controller_channel,
        isis_nodes=isis_nodes,
        isisd_pwd=isisd_pwd,
        addrs_config=addrs_config,
        hosts_config=hosts_config,
        verbose=verbose
    )
    # Save nodes to a YAML file
    if nodes_yaml is not None:
        cli_utils.save_yaml_dump(nodes, nodes_yaml)
    # Save edges to a YAML file
    if edges_yaml is not None:
        cli_utils.save_yaml_dump(edges, edges_yaml)
    # Print the extracted topology
    if verbose:
        # Print the nodes
        print('\nNodes: %s\n' % nodes)
        # Print the edges
        print('\nEdges: %s\n' % edges)


def load_topo_on_arango(controller_channel, nodes_yaml, edges_yaml,
                        verbose=False):
    """
    Load a network topology on a Arango database.
    """
    # pylint: disable=too-many-arguments
    #
    # Read nodes YAML
    nodes = cli_utils.load_yaml_dump(nodes_yaml)
    # Read edges YAML
    edges = cli_utils.load_yaml_dump(edges_yaml)
    # Load nodes and edges on ArangoDB
    topo_manager.load_topo_on_arango(
        controller_channel=controller_channel,
        nodes_config=nodes,
        edges_config=edges,
        verbose=verbose
    )


def extract_topo_from_isis_and_load_on_arango(controller_channel,
                                              isis_nodes, isisd_pwd, period=0,
                                              nodes_yaml=None, edges_yaml=None,
                                              addrs_yaml=None, hosts_yaml=None,
                                              verbose=False):
    """
    Extract the topology from a set of nodes running ISIS protocol
    and load it on a Arango database.
    """
    # pylint: disable=too-many-arguments
    #
    # Read addresses configuration from YAML file
    addrs_config = cli_utils.load_yaml_dump(addrs_yaml)
    # Read hosts configuration from YAML file
    hosts_config = cli_utils.load_yaml_dump(hosts_yaml)
    # Start periodic extraction
    for nodes, edges in topo_manager.extract_topo_from_isis_and_load_on_arango(
                controller_channel=controller_channel,
                isis_nodes=isis_nodes,
                isisd_pwd=isisd_pwd,
                addrs_config=addrs_config,
                hosts_config=hosts_config,
                period=period,
                verbose=verbose
            ):
        # Save nodes to a YAML file
        if nodes_yaml is not None:
            cli_utils.save_yaml_dump(nodes, nodes_yaml)
        # Save edges to a YAML file
        if edges_yaml is not None:
            cli_utils.save_yaml_dump(edges, edges_yaml)
        # Print the extracted topology
        if verbose:
            # Print the nodes
            print('\nNodes: %s\n' % nodes)
            # Print the edges
            print('\nEdges: %s\n' % edges)
            # Separation line
            print('\n******************************\n')


def topology_information_extraction_isis(controller_channel,
                                         routers, period=0, isisd_pwd='',
                                         topo_file_json=None,
                                         nodes_file_yaml=None,
                                         edges_file_yaml=None,
                                         addrs_yaml=None, hosts_yaml=None,
                                         topo_graph=None, verbose=False):
    """
    Run periodical topology extraction.
    """
    # Read addresses configuration from YAML file
    addrs_config = None
    if addrs_yaml is not None:
        addrs_config = cli_utils.load_yaml_dump(addrs_yaml)
    # Read hosts configuration from YAML file
    hosts_config = None
    if hosts_yaml is not None:
        hosts_config = cli_utils.load_yaml_dump(hosts_yaml)
    # pylint: disable=too-many-arguments, unused-argument
    for nodes, edges in topo_manager.extract_topo_from_isis_and_load_on_arango(
                controller_channel=controller_channel,
                isis_nodes=routers,
                isisd_pwd=isisd_pwd,
                addrs_config=addrs_config,
                hosts_config=hosts_config,
                period=period,
                verbose=verbose
            ):
        # Save nodes to a YAML file
        if nodes_file_yaml is not None:
            cli_utils.save_yaml_dump(nodes, nodes_file_yaml)
        # Save edges to a YAML file
        if edges_file_yaml is not None:
            cli_utils.save_yaml_dump(edges, edges_file_yaml)
        # Print the extracted topology
        if verbose:
            # Print the nodes
            print('\nNodes: %s\n' % nodes)
            # Print the edges
            print('\nEdges: %s\n' % edges)
            # Separation line
            print('\n******************************\n')


def push_nodes_config(controller_channel, nodes_config_filename):
    """
    Push nodes configuration.
    """
    # Read nodes config from YAML file
    try:
        nodes_config = cli_utils.load_yaml_dump(nodes_config_filename)
    except yaml.YAMLError as err:
        print(err)
    # Push nodes confiiguration to the controller
    topo_manager.push_nodes_config(
        controller_channel=controller_channel,
        nodes_config=nodes_config
    )


def get_nodes_config(controller_channel):
    """
    Get nodes configuration.
    """
    # Get nodes configuration
    nodes_config = topo_manager.get_nodes_config(
        controller_channel=controller_channel
    )
    # Print nodes configuration
    print(nodes_config)


def args_extract_topo_from_isis():
    """
    Command-line arguments for the extract_topo_from_isis command
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    """
    return [
        {
            'args': ['--isis-nodes'],
            'kwargs': {'dest': 'isis_nodes', 'action': 'store',
                       'required': True, 'help': 'isis_nodes'}
        }, {
            'args': ['--isisd-pwd'],
            'kwargs': {'dest': 'isisd_pwd', 'action': 'store',
                       'help': 'period'}
        }, {
            'args': ['--nodes-yaml'],
            'kwargs': {'dest': 'nodes_yaml', 'action': 'store',
                       'help': 'nodes_yaml'},
            'is_path': True
        }, {
            'args': ['--edges-yaml'],
            'kwargs': {'dest': 'edges_yaml', 'action': 'store',
                       'help': 'edges_yaml'},
            'is_path': True
        }, {
            'args': ['--addrs-yaml'],
            'kwargs': {'dest': 'addrs_yaml', 'action': 'store',
                       'help': 'addrs_yaml', 'default': None},
            'is_path': True
        }, {
            'args': ['--hosts-yaml'],
            'kwargs': {'dest': 'hosts_yaml', 'action': 'store',
                       'help': 'hosts_yaml', 'default': None},
            'is_path': True
        }, {
            'args': ['--verbose'],
            'kwargs': {'action': 'store_true', 'help': 'Enable verbose mode'}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_extract_topo_from_isis(prog=sys.argv[0], args=None):
    """
    Command-line arguments parser for topolgy extraction function.
    """
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    # Add the arguments to the parser
    for param in args_extract_topo_from_isis():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for extract_topo_from_isis
def complete_extract_topo_from_isis(text, prev_text):
    """
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.
    """
    # Get arguments from extract_topo_from_isis
    args = args_extract_topo_from_isis()
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
    args = [arg
            for param in args
            for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args


def args_load_topo_on_arango():
    """
    Command-line arguments for the load_topo_on_arango command
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    """
    return [
        {
            'args': ['--nodes-yaml'],
            'kwargs': {'dest': 'nodes_yaml', 'action': 'store',
                       'help': 'nodes_yaml'},
            'is_path': True
        }, {
            'args': ['--edges-yaml'],
            'kwargs': {'dest': 'edges_yaml', 'action': 'store',
                       'help': 'edges_yaml'},
            'is_path': True
        }, {
            'args': ['--verbose'],
            'kwargs': {'action': 'store_true', 'help': 'Enable verbose mode'}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_load_topo_on_arango(prog=sys.argv[0], args=None):
    """
    Command-line arguments parser for load on Arango function.
    """
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    # Add the arguments to the parser
    for param in args_load_topo_on_arango():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for load_topo_on_arango
def complete_load_topo_on_arango(text, prev_text):
    """
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.
    """
    # Get arguments for load_topo_on_arango
    args = args_load_topo_on_arango()
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


def args_extract_topo_from_isis_and_load_on_arango():
    """
    Command-line arguments for the extract_topo_from_isis_and_load_on_arango
    command. Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    """
    return [
        {
            'args': ['--isis-nodes'],
            'kwargs': {'dest': 'isis_nodes', 'action': 'store',
                       'required': True, 'help': 'isis_nodes'}
        }, {
            'args': ['--isisd-pwd'],
            'kwargs': {'dest': 'isisd_pwd', 'action': 'store',
                       'help': 'period'}
        }, {
            'args': ['--period'],
            'kwargs': {'dest': 'period', 'action': 'store',
                       'help': 'period', 'type': int,
                       'default': DEFAULT_TOPO_EXTRACTION_PERIOD}
        }, {
            'args': ['--nodes-yaml'],
            'kwargs': {'dest': 'nodes_yaml', 'action': 'store',
                       'help': 'nodes_yaml'},
            'is_path': True
        }, {
            'args': ['--edges-yaml'],
            'kwargs': {'dest': 'edges_yaml', 'action': 'store',
                       'help': 'edges_yaml'},
            'is_path': True
        }, {
            'args': ['--addrs-yaml'],
            'kwargs': {'dest': 'addrs_yaml', 'action': 'store',
                       'help': 'addrs_yaml', 'default': None},
            'is_path': True
        }, {
            'args': ['--hosts-yaml'],
            'kwargs': {'dest': 'hosts_yaml', 'action': 'store',
                       'help': 'hosts_yaml', 'default': None},
            'is_path': True
        }, {
            'args': ['--verbose'],
            'kwargs': {'action': 'store_true', 'help': 'Enable verbose mode'}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_extract_topo_from_isis_and_load_on_arango(
        prog=sys.argv[0], args=None):
    """
    Command-line arguments parser for
    extract_topo_from_isis_and_load_on_arango function.
    """
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    # Add the arguments to the parser
    for param in args_extract_topo_from_isis_and_load_on_arango():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for extract_topo_from_isis_and_load_on_arango
def complete_extract_topo_from_isis_and_load_on_arango(text, prev_text):
    """
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.
    """
    # Get arguments for extract_topo_from_isis_and_load_on_arango
    args = args_extract_topo_from_isis_and_load_on_arango()
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


def args_topology_information_extraction_isis():
    """
    Command-line arguments for the topology_information_extraction_isis
    command. Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    """
    return [
        {
            'args': ['--routers'],
            'kwargs': {'dest': 'routers', 'action': 'store',
                       'required': True, 'help': 'routers'}
        }, {
            'args': ['--period'],
            'kwargs': {'dest': 'period', 'action': 'store',
                       'help': 'period', 'type': int,
                       'default': DEFAULT_TOPO_EXTRACTION_PERIOD}
        }, {
            'args': ['--isisd-pwd'],
            'kwargs': {'dest': 'isisd_pwd', 'action': 'store',
                       'help': 'period'}
        }, {
            'args': ['--topo-file-json'],
            'kwargs': {'dest': 'topo_file_json', 'action': 'store',
                       'help': 'topo_file_json'},
            'is_path': True
        }, {
            'args': ['--nodes-file-yaml'],
            'kwargs': {'dest': 'nodes_file_yaml', 'action': 'store',
                       'help': 'nodes_file_yaml'},
            'is_path': True
        }, {
            'args': ['--edges-file-yaml'],
            'kwargs': {'dest': 'edges_file_yaml', 'action': 'store',
                       'help': 'edges_file_yaml'},
            'is_path': True
        }, {
            'args': ['--addrs-yaml'],
            'kwargs': {'dest': 'addrs_yaml', 'action': 'store',
                       'help': 'addrs_yaml', 'default': None},
            'is_path': True
        }, {
            'args': ['--hosts-yaml'],
            'kwargs': {'dest': 'hosts_yaml', 'action': 'store',
                       'help': 'hosts_yaml', 'default': None},
            'is_path': True
        }, {
            'args': ['--topo-graph'],
            'kwargs': {'dest': 'topo_graph', 'action': 'store',
                       'help': 'topo_graph'},
            'is_path': True
        }, {
            'args': ['--verbose'],
            'kwargs': {'action': 'store_true', 'help': 'Enable verbose mode'}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_topology_information_extraction_isis(
        prog=sys.argv[0], args=None):
    """
    Command-line arguments parser for topology information extraction
    function.
    """
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    # Add the arguments to the parser
    for param in args_topology_information_extraction_isis():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for topology_information_extraction_isis
def complete_topology_information_extraction_isis(text, prev_text):
    """
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.
    """
    # Get arguments for topology_information_extraction_isis
    args = args_topology_information_extraction_isis()
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


def args_push_nodes_config():
    """
    Command-line arguments for the args_push_nodes_config command
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    """
    return [
        {
            'args': ['--nodes-config-filename'],
            'kwargs': {'dest': 'nodes_config_filename', 'action': 'store',
                       'required': True, 'help': 'nodes_config_filename'}
        }, {
            'args': ['--verbose'],
            'kwargs': {'action': 'store_true', 'help': 'Enable verbose mode'}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_push_nodes_config(prog=sys.argv[0], args=None):
    """
    Command-line arguments parser for topolgy extraction function.
    """
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    # Add the arguments to the parser
    for param in args_push_nodes_config():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for push_nodes_config
def complete_push_nodes_config(text, prev_text):
    """
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.
    """
    # Get arguments from push_nodes_config
    args = args_push_nodes_config()
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
    args = [arg
            for param in args
            for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args


def args_get_nodes_config():
    """
    Command-line arguments for the args_get_nodes_config command
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library
    """
    return [
        {
            'args': ['--verbose'],
            'kwargs': {'action': 'store_true', 'help': 'Enable verbose mode'}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_get_nodes_config(prog=sys.argv[0], args=None):
    """
    Command-line arguments parser for topolgy extraction function.
    """
    # Get parser
    parser = ArgumentParser(
        prog=prog, description=''
    )
    # Add the arguments to the parser
    for param in args_get_nodes_config():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for get_nodes_config
def complete_get_nodes_config(text, prev_text):
    """
    This function receives a string as argument and returns
    a list of parameters candidate for the auto-completion of the string.
    """
    # Get arguments from get_nodes_config
    args = args_get_nodes_config()
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
    args = [arg
            for param in args
            for arg in param['args']]
    # Return the matching arguments
    if text:
        return [
            arg for arg in args
            if arg.startswith(text)
        ]
    # No argument provided: return all the available arguments
    return args
