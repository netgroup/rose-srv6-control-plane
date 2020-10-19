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
# Controller entry point
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
Entry point for controller.
'''

# General imports
import logging
import os
import sys
from argparse import ArgumentParser
from pathlib import Path

# python-dotenv dependencies
from dotenv import load_dotenv
from pkg_resources import resource_filename

# Controller dependencies
from controller.init_db import init_srv6_usid_db
from controller.nb_grpc_server import grpc_server


# Logger reference
logger = logging.getLogger(__name__)

# Configure logging level for urllib3
logging.getLogger('urllib3').setLevel(logging.WARNING)

# Default path to the .env file
DEFAULT_ENV_FILE_PATH = resource_filename(__name__, '../config/controller.env')
# Default value for debug mode
DEFAULT_DEBUG = False


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
        Load configuration from a .env file.
        '''
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
        '''
        # pylint: disable=no-self-use
        logger.info('*** Validating configuration')
        success = True      # TODO validation
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
    # Start the northbound gRPC server to expose the controller services
    grpc_server.start_server()


if __name__ == '__main__':
    # Start the controller
    __main()
