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
# Implementation of Node Manager
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


# General imports
import os
import sys
from argparse import ArgumentParser
import logging
import time
import grpc
from concurrent import futures
from socket import AF_INET, AF_INET6
from dotenv import load_dotenv
from pathlib import Path
from pkg_resources import resource_filename

# Node Manager dependencies
from node_manager import utils
from node_manager.utils import get_address_family

# Folder containing this script
BASE_PATH = os.path.dirname(os.path.realpath(__file__))


# Logger reference
logger = logging.getLogger(__name__)
#
# Default parameters for node manager
#
# Server ip and port
DEFAULT_GRPC_IP = '::'
DEFAULT_GRPC_PORT = 12345
# Debug option
SERVER_DEBUG = False
# Secure option
DEFAULT_SECURE = False
# Server certificate
DEFAULT_CERTIFICATE = 'cert_server.pem'
# Server key
DEFAULT_KEY = 'key_server.pem'
# Default path to the .env file
DEFAULT_ENV_FILE_PATH = resource_filename(__name__, 'config/node_manager.env')
# Define whether to enable the debug mode or not
DEFAULT_DEBUG = False


# Start gRPC server
def start_server(grpc_ip=DEFAULT_GRPC_IP,
                 grpc_port=DEFAULT_GRPC_PORT,
                 secure=DEFAULT_SECURE,
                 certificate=DEFAULT_CERTIFICATE,
                 key=DEFAULT_KEY):
    # Get family of the gRPC IP
    addr_family = get_address_family(grpc_ip)
    # Build address depending on the family
    if addr_family == AF_INET:
        # IPv4 address
        server_addr = '%s:%s' % (grpc_ip, grpc_port)
    elif addr_family == AF_INET6:
        # IPv6 address
        server_addr = '[%s]:%s' % (grpc_ip, grpc_port)
    else:
        # Invalid address
        logger.fatal('Invalid gRPC address: %s' % grpc_ip)
        exit(-2)
    # Create the server and add the handlers
    grpc_server = grpc.server(futures.ThreadPoolExecutor())
    # SRv6 Manager
    srv6_manager_pb2_grpc.add_SRv6ManagerServicer_to_server(
            srv6_manager.SRv6Manager(), grpc_server)
    # PM Manager
    try:
        pm_manager.add_pm_manager_to_server(grpc_server)
    except NameError:
        pass
    # If secure we need to create a secure endpoint
    if secure:
        # Read key and certificate
        with open(key, 'rb') as f:
            key = f.read()
        with open(certificate, 'rb') as f:
            certificate = f.read()
        # Create server ssl credentials
        grpc_server_credentials = (grpc
                                   .ssl_server_credentials(((key,
                                                             certificate),)))
        # Create a secure endpoint
        grpc_server.add_secure_port(server_addr, grpc_server_credentials)
    else:
        # Create an insecure endpoint
        grpc_server.add_insecure_port(server_addr)
    # Start the loop for gRPC
    logger.info('*** Listening gRPC on address %s' % server_addr)
    grpc_server.start()
    while True:
        time.sleep(5)


# Check whether we have root permission or not
# Return True if we have root permission, False otherwise
def check_root():
    return os.getuid() == 0


# Class representing the configuration
class Config:
    # Flag indicating whether to enable the SRv6 capabilities or not
    ENABLE_SRV6_MANAGER = True
    # IP address of the gRPC server (:: means any)
    GRPC_IP = DEFAULT_GRPC_IP
    # Port of the gRPC server
    GRPC_PORT = DEFAULT_GRPC_PORT
    # Define whether to enable gRPC secure mode or not
    GRPC_SECURE = DEFAULT_SECURE
    # Path to the certificate of the gRPC server required for the secure mode
    GRPC_SERVER_CERTIFICATE_PATH = DEFAULT_CERTIFICATE
    # Path to the key of the gRPC server required for the secure mode
    GRPC_SERVER_KEY_PATH = DEFAULT_KEY
    # Define whether to enable the debug mode or not
    DEBUG = DEFAULT_DEBUG
    # Define whether to enable SRv6 PM functionalities or not
    ENABLE_SRV6_PM_MANAGER = False
    # Path to the 'srv6-pm-xdp-ebpf' repository
    SRV6_PM_XDP_EBPF_PATH = None
    # Path to the 'rose-srv6-data-plane' repository
    ROSE_SRV6_DATA_PLANE_PATH = None

    # Load configuration from .env file
    def load_config(self, env_file):
        logger.info('*** Loading configuration from %s' % env_file)
        # Path to the .env file
        env_path = Path(env_file)
        # Load environment variables from .env file
        load_dotenv(dotenv_path=env_path)
        # Flag indicating whether to enable the SRv6 capabilities or not
        if os.getenv('ENABLE_SRV6_MANAGER') is not None:
            self.ENABLE_SRV6_MANAGER = os.getenv('ENABLE_SRV6_MANAGER')
            # Values provided in .env files are returned as strings
            # We need to convert them to bool
            if self.ENABLE_SRV6_MANAGER.lower() == 'true':
                self.ENABLE_SRV6_MANAGER = True
            elif self.ENABLE_SRV6_MANAGER.lower() == 'false':
                self.ENABLE_SRV6_MANAGER = False
            else:
                # Invalid value for this parameter
                self.ENABLE_SRV6_MANAGER = None
        # IP address of the gRPC server (:: means any)
        if os.getenv('GRPC_IP') is not None:
            self.GRPC_IP = os.getenv('GRPC_IP')
        # Port of the gRPC server
        if os.getenv('GRPC_PORT') is not None:
            self.GRPC_PORT = int(os.getenv('GRPC_PORT'))
        # Define whether to enable gRPC secure mode or not
        if os.getenv('GRPC_SECURE') is not None:
            self.GRPC_SECURE = os.getenv('GRPC_SECURE')
            # Values provided in .env files are returned as strings
            # We need to convert them to bool
            if self.GRPC_SECURE.lower() == 'true':
                self.GRPC_SECURE = True
            elif self.GRPC_SECURE.lower() == 'false':
                self.GRPC_SECURE = False
            else:
                # Invalid value for this parameter
                self.GRPC_SECURE = None
        # Path to the certificate of the gRPC server required
        # for the secure mode
        if os.getenv('GRPC_SERVER_CERTIFICATE_PATH') is not None:
            self.GRPC_SERVER_CERTIFICATE_PATH = \
                os.getenv('GRPC_SERVER_CERTIFICATE_PATH')
        # Path to the key of the gRPC server required for the secure mode
        if os.getenv('GRPC_SERVER_KEY_PATH') is not None:
            self.GRPC_SERVER_KEY_PATH = os.getenv('GRPC_SERVER_KEY_PATH')
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
        # Define whether to enable SRv6 PM functionalities or not
        if os.getenv('ENABLE_SRV6_PM_MANAGER') is not None:
            self.ENABLE_SRV6_PM_MANAGER = os.getenv('ENABLE_SRV6_PM_MANAGER')
            # Values provided in .env files are returned as strings
            # We need to convert them to bool
            if self.ENABLE_SRV6_PM_MANAGER.lower() == 'true':
                self.ENABLE_SRV6_PM_MANAGER = True
            elif self.ENABLE_SRV6_PM_MANAGER.lower() == 'false':
                self.ENABLE_SRV6_PM_MANAGER = False
            else:
                # Invalid value for this parameter
                self.ENABLE_SRV6_PM_MANAGER = None
        # Path to the 'srv6-pm-xdp-ebpf' repository
        if os.getenv('SRV6_PM_XDP_EBPF_PATH') is not None:
            self.SRV6_PM_XDP_EBPF_PATH = os.getenv('SRV6_PM_XDP_EBPF_PATH')
        # Path to the 'rose-srv6-data-plane' repository
        if os.getenv('ROSE_SRV6_DATA_PLANE_PATH') is not None:
            self.ROSE_SRV6_DATA_PLANE_PATH = \
                os.getenv('ROSE_SRV6_DATA_PLANE_PATH')

    def validate_config(self):
        logger.info('*** Validating configuration')
        success = True
        # Validate gRPC IP address
        if not utils.validate_ip_address(self.GRPC_IP):
            logger.critical('GRPC_IP is an invalid IP address: %s'
                            % self.GRPC_IP)
            success = False
        # Validate gRPC port
        if self.GRPC_PORT <= 0 or self.GRPC_PORT >= 65536:
            logger.critical('GRPC_PORT out of range: %s' % self.GRPC_PORT)
            success = False
        # Validate SRv6 PFPLM configuration parameters
        if self.ENABLE_SRV6_PM_MANAGER:
            # SRv6 PM functionalities depends on SRv6 features
            if not self.ENABLE_SRV6_MANAGER:
                logger.critical('SRv6 PM Manager depends on SRv6 Manager.\n'
                                'To use SRv6 PM functionalities you must set '
                                'ENABLE_SRV6_MANAGER in your configuration')
                success = False
            # Validate SRV6_PM_XDP_EBPF_PATH
            if self.SRV6_PM_XDP_EBPF_PATH is None:
                logger.critical('SRv6 PM Manager requires '
                                'SRV6_PM_XDP_EBPF_PATH. '
                                'Set SRV6_PM_XDP_EBPF_PATH variable in '
                                'configuration file (.env file)')
                success = False
            if self.SRV6_PM_XDP_EBPF_PATH is not None and \
                    not os.path.exists(self.SRV6_PM_XDP_EBPF_PATH):
                logger.critical('SRV6_PM_XDP_EBPF_PATH variable in .env '
                                'points to a non existing folder: %s'
                                % self.SRV6_PM_XDP_EBPF_PATH)
                success = False
            # Validate ROSE_SRV6_DATA_PLANE_PATH
            if self.ROSE_SRV6_DATA_PLANE_PATH is None:
                logger.critical('SRv6 PM Manager requires '
                                'ROSE_SRV6_DATA_PLANE_PATH. '
                                'Set ROSE_SRV6_DATA_PLANE_PATH variable '
                                'in configuration file (.env file)')
                success = False
            if self.ROSE_SRV6_DATA_PLANE_PATH is not None and \
                    not os.path.exists(self.ROSE_SRV6_DATA_PLANE_PATH):
                logger.critical('ROSE_SRV6_DATA_PLANE_PATH variable in '
                                '.env points to a non existing folder: %s'
                                % self.ROSE_SRV6_DATA_PLANE_PATH)
                success = False
        # Validate gRPC secure mode parameters
        if self.GRPC_SECURE:
            # Validate GRPC_SERVER_CERTIFICATE_PATH
            if self.GRPC_SERVER_CERTIFICATE_PATH is None:
                logger.critical('Set GRPC_SERVER_CERTIFICATE_PATH variable '
                                'in configuration file (.env file)')
                success = False
            if not os.path.exists(self.GRPC_SERVER_CERTIFICATE_PATH):
                logger.critical('GRPC_SERVER_CERTIFICATE_PATH variable '
                                'in .env points to a non existing folder: %s'
                                % self.GRPC_SERVER_CERTIFICATE_PATH)
                success = False
            # Validate GRPC_SERVER_KEY_PATH
            if self.GRPC_SERVER_KEY_PATH is None:
                logger.critical('Set GRPC_SERVER_KEY_PATH variable in '
                                'configuration file (.env file)')
                success = False
            if not os.path.exists(self.GRPC_SERVER_KEY_PATH):
                logger.critical('GRPC_SERVER_KEY_PATH variable in .env '
                                'points to a non existing folder: %s'
                                % self.GRPC_SERVER_KEY_PATH)
                success = False
        # Return result
        return success

    def import_dependencies(self):
        global srv6_manager, srv6_manager_pb2_grpc
        global srv6pmService_pb2_grpc, pm_manager
        # SRv6 Manager dependencies
        if self.ENABLE_SRV6_MANAGER:
            from node_manager import srv6_manager
            import srv6_manager_pb2_grpc
        # SRv6 PM dependencies
        if self.ENABLE_SRV6_PM_MANAGER:
            from node_manager import pm_manager
            import srv6pmService_pb2_grpc


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
        '-g', '--grpc-ip', dest='grpc_ip', action='store',
        default=None, help='IP of the gRPC server'
    )
    parser.add_argument(
        '-r', '--grpc-port', dest='grpc_port', action='store',
        default=None, help='Port of the gRPC server'
    )
    parser.add_argument(
        '-s', '--secure', action='store_true', help='Activate secure mode'
    )
    parser.add_argument(
        '-c', '--server-cert', dest='server_cert', action='store',
        default=None, help='Server certificate file'
    )
    parser.add_argument(
        '-k', '--server-key', dest='server_key',
        action='store', default=None, help='Server key file'
    )
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Activate debug logs'
    )
    # Parse input parameters
    args = parser.parse_args()
    # Return the arguments
    return args


def __main():
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
    # Setup properly the secure mode
    secure = args.secure
    if secure:
        config.GRPC_SECURE = secure
    # gRPC server IP
    grpc_ip = args.grpc_ip
    if grpc_ip is not None:
        config.GRPC_IP = grpc_ip
    # gRPC server port
    grpc_port = args.grpc_port
    if grpc_port is not None:
        config.GRPC_PORT = grpc_port
    # Server certificate
    certificate = args.server_cert
    if certificate is not None:
        config.GRPC_SERVER_CERTIFICATE_PATH = certificate
    # Server key
    key = args.server_key
    if key is not None:
        config.GRPC_SERVER_KEY_PATH = key
    # Setup properly the logger
    if args.debug:
        logger.setLevel(level=logging.DEBUG)
        config.DEBUG = args.debug
    else:
        logger.setLevel(level=logging.INFO)
    # Debug settings
    server_debug = logger.getEffectiveLevel() == logging.DEBUG
    logging.info('SERVER_DEBUG:' + str(server_debug))
    # This script must be run as root
    if not check_root():
        print('*** %s must be run as root.\n' % sys.argv[0])
        exit(1)
    # Validate configuration
    if not config.validate_config():
        logger.critical('Invalid configuration\n')
        exit(-2)
    # Import dependencies
    config.import_dependencies()
    # Extract parameters from the configuration
    grpc_ip = config.GRPC_IP
    grpc_port = config.GRPC_PORT
    secure = config.GRPC_SECURE
    certificate = config.GRPC_SERVER_CERTIFICATE_PATH
    key = config.GRPC_SERVER_KEY_PATH
    # Start the server
    start_server(grpc_ip, grpc_port, secure, certificate, key)


if __name__ == '__main__':
    __main()
