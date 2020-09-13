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
# Collection of topology utilities for the Controller CLI
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
ArangoDB utilities for Controller CLI.
'''

# General imports
import logging
import os
import sys
from argparse import ArgumentParser

# Controller dependencies
from controller.db_utils.arangodb import arangodb_utils
from controller.cli import utils as cli_utils

# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)

# Interval between two consecutive extractions (in seconds)
DEFAULT_TOPO_EXTRACTION_PERIOD = 0


def extract_topo_from_isis(isis_nodes, isisd_pwd,
                           nodes_yaml, edges_yaml,
                           addrs_yaml=None, hosts_yaml=None,
                           verbose=False):
    '''
    Extract the network topology from a set of nodes running ISIS protocol.
    The extracted topology can be exported to a YAML file (two separate YAML
    files for nodes and edges). Optionally, you can enrich the extracted
    topology with IP addresses and other hosts by creating your own addresses
    and hosts YAML files.

    :param isis_nodes: A list of pairs ip-port representing IP and port of
                       the ISIS nodes you want to extract the topology from
                       (e.g. ['fcff:1::1-2608', 'fcff:2::1-2608']).
    :type isis_nodes: list
    :param isisd_pwd: The password used to log in to isisd.
    :type isisd_pwd: str
    :param nodes_yaml: The path and the name of the output YAML file
                       containing the nodes. If this parameter is not
                       provided, the nodes are not exported to a YAML file
                       (default: None).
    :type nodes_yaml: str, optional
    :param edges_yaml: The path and the name of the output YAML file
                       containing the edges. If this parameter is not
                       provided, the edges are not exported to a YAML file
                       (default: None).
    :type edges_yaml: str, optional
    :param addrs_yaml: The path and the name of the YAML file containing the
                       addresses of the nodes. If this argument is not passed,
                       the addresses are not added to the exported topology.
    :type addrs_yaml: str, optional
    :param hosts_yaml: The path and the name of the YAML file containing the
                       hosts. If this argument is not passed, the hosts are
                       not added to the exported topology.
    :type hosts_yaml: str, optional
    :param verbose: Define whether to enable the verbose mode or not
                    (default: False).
    :type verbose: bool, optional
    :raises controller.db_utils.arangodb.arangodb_utils  \\
            .TopologyInformationExtractionError: Error while attempting to
                                                extract the topology.
    '''
    # pylint: disable=too-many-arguments
    #
    # Extract the  topology
    logger.debug('Trying to extract the topology')
    arangodb_utils.extract_topo_from_isis(
        isis_nodes=isis_nodes.split(','),
        isisd_pwd=isisd_pwd,
        nodes_yaml=nodes_yaml,
        edges_yaml=edges_yaml,
        addrs_yaml=addrs_yaml,
        hosts_yaml=hosts_yaml,
        verbose=verbose
    )
    logger.info('Topology extraction completed successfully')


def load_topo_on_arango(arango_url, arango_user, arango_password,
                        nodes_yaml, edges_yaml, verbose=False):
    '''
    Load a network topology on a Arango database.

    :param arango_url: The URL of the ArangoDB.
    :type arango_url: str
    :param arango_user: The username used to access the ArangoDB.
    :type arango_user: str
    :param arango_password: The password used to access the ArangoDB.
    :type arango_password: str
    :param nodes_yaml: Set of nodes.
    :type nodes_yaml: set
    :param edges_yaml: Set of edges.
    :type edges_yaml: set
    :param verbose: Define whether to enable the verbose mode or not
                    (default: False).
    :type verbose: bool, optional
    '''
    # pylint: disable=too-many-arguments
    #
    # Init database
    logger.debug('Initializing database')
    nodes_collection, edges_collection = arangodb_utils.initialize_db(
        arango_url=arango_url,
        arango_user=arango_user,
        arango_password=arango_password
    )
    # Read nodes YAML
    logger.debug('Loading nodes YAML')
    nodes = arangodb_utils.load_yaml_dump(nodes_yaml)
    # Read edges YAML
    logger.debug('Loading edges YAML')
    edges = arangodb_utils.load_yaml_dump(edges_yaml)
    # Load nodes and edges on ArangoDB
    logger.debug('Loading topology on ArangoDB')
    arangodb_utils.load_topo_on_arango(
        arango_url=arango_url,
        user=arango_user,
        password=arango_password,
        nodes=nodes,
        edges=edges,
        nodes_collection=nodes_collection,
        edges_collection=edges_collection,
        verbose=verbose
    )
    logger.info('Topology loaded on ArangoDB successfully')


def extract_topo_from_isis_and_load_on_arango(isis_nodes, isisd_pwd,
                                              arango_url=None,
                                              arango_user=None,
                                              arango_password=None,
                                              nodes_yaml=None, edges_yaml=None,
                                              addrs_yaml=None, hosts_yaml=None,
                                              period=0, verbose=False):
    '''
    Extract the network topology from a set of nodes running ISIS protocol
    and upload it on a database. The extracted topology can be exported to a
    YAML file (two separate YAML files for nodes and edges). Optionally, you
    can enrich the extracted topology with IP addresses and other hosts by
    creating your own addresses and hosts YAML files.

    :param isis_nodes: A list of pairs ip-port representing IP and port of
                       the ISIS nodes you want to extract the topology from
                       (e.g. ['fcff:1::1-2608', 'fcff:2::1-2608']).
    :type isis_nodes: list
    :param isisd_pwd: The password used to log in to isisd.
    :type isisd_pwd: str
    :param arango_url: The URL of the ArangoDB.
    :type arango_url: str
    :param arango_user: The username used to access the ArangoDB.
    :type arango_user: str
    :param arango_password: The password used to access the ArangoDB.
    :type arango_password: str
    :param nodes_yaml: The path and the name of the output YAML file
                       containing the nodes. If this parameter is not
                       provided, the nodes are not exported to a YAML file
                       (default: None).
    :type nodes_yaml: str, optional
    :param edges_yaml: The path and the name of the output YAML file
                       containing the edges. If this parameter is not
                       provided, the edges are not exported to a YAML file
                       (default: None).
    :type edges_yaml: str, optional
    :param addrs_yaml: The path and the name of the YAML file containing the
                       addresses of the nodes. If this argument is not passed,
                       the addresses are not added to the exported topology.
    :type addrs_yaml: str, optional
    :param hosts_yaml: The path and the name of the YAML file containing the
                       hosts. If this argument is not passed, the hosts are
                       not added to the exported topology.
    :type hosts_yaml: str, optional
    :param period: The interval between two consecutive extractions. If this
                   arguments is equals to 0, this function performs a single
                   extraction and then returns (default: 0).
    :type period: int, optional
    :param verbose: Define whether to enable the verbose mode or not
                    (default: False).
    :type verbose: bool, optional
    '''
    # pylint: disable=too-many-arguments
    #
    # Extract the topology and load it on ArangoDB
    logger.debug('Extracting topology and loading on ArangoDB')
    arangodb_utils.extract_topo_from_isis_and_load_on_arango(
        isis_nodes=isis_nodes,
        isisd_pwd=isisd_pwd,
        arango_url=arango_url,
        arango_user=arango_user,
        arango_password=arango_password,
        nodes_yaml=nodes_yaml,
        edges_yaml=edges_yaml,
        addrs_yaml=addrs_yaml,
        hosts_yaml=hosts_yaml,
        period=period,
        verbose=verbose
    )
    logger.info('Topology extracted and loaded on ArangoDB')


def topology_information_extraction_isis(routers, period, isisd_pwd,
                                         topo_file_json=None,
                                         nodes_file_yaml=None,
                                         edges_file_yaml=None,
                                         addrs_yaml=None, hosts_yaml=None,
                                         topo_graph=None, verbose=False):
    '''
    Run periodical topology extraction.

    :param routers: A list of pairs ip-port representing IP and port of
                       the ISIS nodes you want to extract the topology from
                       (e.g. ['fcff:1::1-2608', 'fcff:2::1-2608']).
    :type routers: list
    :param period: The interval between two consecutive extractions. If this
                   arguments is equals to 0, this function performs a single
                   extraction and then returns (default: 0).
    :type period: int, optional
    :param isisd_pwd: The password used to log in to isisd.
    :type isisd_pwd: str
    :param arango_url: The URL of the ArangoDB.
    :type arango_url: str
    :param arango_user: The username used to access the ArangoDB.
    :type arango_user: str
    :param arango_password: The password used to access the ArangoDB.
    :type arango_password: str
    :param topo_file_json: The path and the name of the output JSON file
                           containing the topology. If this parameter is not
                           provided, the topology is not exported to a JSON
                           file (default: None).
    :type topo_file_json: str, optional
    :param nodes_file_yaml: The path and the name of the output YAML file
                            containing the nodes. If this parameter is not
                            provided, the nodes are not exported to a YAML
                            file (default: None).
    :type nodes_file_yaml: str, optional
    :param edges_file_yaml: The path and the name of the output YAML file
                            containing the edges. If this parameter is not
                            provided, the edges are not exported to a YAML
                            file (default: None).
    :type edges_file_yaml: str, optional
    :param addrs_yaml: The path and the name of the YAML file containing the
                       addresses of the nodes. If this argument is not passed,
                       the addresses are not added to the exported topology.
    :type addrs_yaml: str, optional
    :param hosts_yaml: The path and the name of the YAML file containing the
                       hosts. If this argument is not passed, the hosts are
                       not added to the exported topology.
    :type hosts_yaml: str, optional
    :param topo_graph: The path and the name of the output SVG file (image).
                       If this parameter is not provided, the topology is not
                       exported as image (default: None).
    :type topo_graph: str, optional
    :param verbose: Define whether to enable the verbose mode or not
                    (default: False).
    :type verbose: bool, optional
    '''
    # pylint: disable=too-many-arguments, unused-argument
    #
    # Extract the topology and load it on ArangoDB
    logger.debug('Extracting topology and loading on ArangoDB')
    arangodb_utils.extract_topo_from_isis_and_load_on_arango(
        isis_nodes=routers,
        isisd_pwd=isisd_pwd,
        nodes_yaml=nodes_file_yaml,
        edges_yaml=edges_file_yaml,
        addrs_yaml=addrs_yaml,
        hosts_yaml=hosts_yaml,
        period=period,
        verbose=verbose
    )
    logger.info('Topology extracted and loaded on ArangoDB')


def args_extract_topo_from_isis():
    '''
    Command-line arguments for the extract_topo_from_isis command.
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library.

    :return: The list of the arguments.
    :rtype: list
    '''
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
    '''
    Command-line arguments parser for topolgy extraction function.

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
    for param in args_extract_topo_from_isis():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for extract_topo_from_isis
def complete_extract_topo_from_isis(text, prev_text):
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
    '''
    Command-line arguments for the load_topo_on_arango command.
    Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library.

    :return: The list of the arguments.
    :rtype: list
    '''
    return [
        {
            'args': ['--arango-url'],
            'kwargs': {'dest': 'arango_url', 'action': 'store',
                       'help': 'arango_url',
                       'default': os.getenv('ARANGO_URL')}
        }, {
            'args': ['--arango-user'],
            'kwargs': {'dest': 'arango_user', 'action': 'store',
                       'help': 'arango_user',
                       'default': os.getenv('ARANGO_USER')}
        }, {
            'args': ['--arango-password'],
            'kwargs': {'dest': 'arango_password', 'action': 'store',
                       'help': 'arango_password',
                       'default': os.getenv('ARANGO_PASSWORD')}
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
            'args': ['--verbose'],
            'kwargs': {'action': 'store_true', 'help': 'Enable verbose mode'}
        }, {
            'args': ['--debug'],
            'kwargs': {'action': 'store_true', 'help': 'Activate debug logs'}
        }
    ]


# Parse options
def parse_arguments_load_topo_on_arango(prog=sys.argv[0], args=None):
    '''
    Command-line arguments parser for load on Arango function.

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
    for param in args_load_topo_on_arango():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for load_topo_on_arango
def complete_load_topo_on_arango(text, prev_text):
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
    '''
    Command-line arguments for the extract_topo_from_isis_and_load_on_arango.
    command. Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library.

    :return: The list of the arguments.
    :rtype: list
    '''
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
            'args': ['--arango-url'],
            'kwargs': {'dest': 'arango_url', 'action': 'store',
                       'help': 'arango_url',
                       'default': os.getenv('ARANGO_URL')}
        }, {
            'args': ['--arango-user'],
            'kwargs': {'dest': 'arango_user', 'action': 'store',
                       'help': 'arango_user',
                       'default': os.getenv('ARANGO_USER')}
        }, {
            'args': ['--arango-password'],
            'kwargs': {'dest': 'arango_password', 'action': 'store',
                       'help': 'arango_password',
                       'default': os.getenv('ARANGO_PASSWORD')}
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
    '''Command-line arguments parser for
    extract_topo_from_isis_and_load_on_arango function.

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
    for param in args_extract_topo_from_isis_and_load_on_arango():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for extract_topo_from_isis_and_load_on_arango
def complete_extract_topo_from_isis_and_load_on_arango(text, prev_text):
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
    '''
    Command-line arguments for the topology_information_extraction_isis.
    command. Arguments are represented as a dicts. Each dict has two items:
    - args, a list of names for the argument
    - kwargs, a dict containing the attributes for the argument required by
      the argparse library.

    :return: The list of the arguments.
    :rtype: list
    '''
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
    '''
    Command-line arguments parser for topology information extraction
    function.

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
    for param in args_topology_information_extraction_isis():
        parser.add_argument(*param['args'], **param['kwargs'])
    # Parse input parameters
    args = parser.parse_args(args)
    # Return the arguments
    return args


# TAB-completion for topology_information_extraction_isis
def complete_topology_information_extraction_isis(text, prev_text):
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
