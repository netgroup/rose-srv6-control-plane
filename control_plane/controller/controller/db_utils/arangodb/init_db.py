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
# Utilities for the initialization of ArangoDB
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
This module provides a collection of utilities used to initialize a Arango
database
'''

# General imports
import logging
import os

# Controller depedencies
from controller.db_utils.arangodb import arangodb_driver


# Logger reference
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)


# Global variables definition
#
#
# ArangoDB params
ARANGO_URL = os.getenv('ARANGO_URL', 'http://localhost:8529')
ARANGO_USER = os.getenv('ARANGO_USER', 'root')
ARANGO_PASSWORD = os.getenv('ARANGO_PASSWORD', '12345678')


def init_srv6_usid_db(arango_url=ARANGO_URL, arango_user=ARANGO_USER,
                      arango_password=ARANGO_PASSWORD):
    '''
    Initialize uSID database and uSID policies collection.

    :param arango_url: The URL of the ArangoDB. If this argument is not
                       provided, the value assigned to the environment
                       variable ARANGO_URL will be used as URL.
    :type arango_url: str, optional
    :param arango_user: The username used to access the ArangoDB. If this
                        argument is not provided, the value assigned to the
                        environment variable ARANGO_USER will be used as
                        username.
    :type arango_user: str, optional
    :param arango_password: The password used to access the ArangoDB. If this
                        argument is not provided, the value assigned to the
                        environment variable ARANGO_PASSWORD will be used as
                        password.
    :type arango_password: str, optional
    :return: True.
    :rtype: bool
    '''
    logger.debug('*** Initializing SRv6 uSID database')
    # Connect to ArangoDB
    client = arangodb_driver.connect_arango(url=arango_url)
    # Initialize SRv6 uSID database
    arangodb_driver.init_srv6_usid_db(
        client=client,
        arango_username=arango_user,
        arango_password=arango_password
    )
    # Initialize uSID policies collection
    arangodb_driver.init_usid_policies_collection(
        client=client,
        arango_username=arango_user,
        arango_password=arango_password
    )
    logger.info('*** SRv6 uSID database initialized successfully')
    return True


# Entry point for this module
if __name__ == '__main__':
    init_srv6_usid_db()
