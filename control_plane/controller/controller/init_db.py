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
import os

# Controller depedencies
from controller import arangodb_driver


# ArangoDB params
ARANGO_URL = os.getenv('ARANGO_URL', 'http://localhost:8529')
ARANGO_USER = os.getenv('ARANGO_USER', 'root')
ARANGO_PASSWORD = os.getenv('ARANGO_PASSWORD', '12345678')


def init_db(db_name):
    '''
    Initialize uSID database and uSID policies collection
    '''
    # Connect to ArangoDB
    client = arangodb_driver.connect_arango(url=ARANGO_URL)
    # Initialize SRv6 uSID database
    arangodb_driver.init_db(
        client=client,
        arango_username=ARANGO_USER,
        arango_password=ARANGO_PASSWORD,
        db_name=db_name
    )


def init_db_collections():
    '''
    Initialize database collections.
    '''
    # Connect to ArangoDB
    client = arangodb_driver.connect_arango(url=ARANGO_URL)
    # Initialize uSID policies collection
    arangodb_driver.init_usid_policies_collection(
        client=client,
        arango_username=ARANGO_USER,
        arango_password=ARANGO_PASSWORD
    )
    # Initialize SRv6 paths collection
    arangodb_driver.init_srv6_paths_collection(
        client=client,
        arango_username=ARANGO_USER,
        arango_password=ARANGO_PASSWORD
    )
    # Initialize SRv6 behaviors collection
    arangodb_driver.init_srv6_behaviors_collection(
        client=client,
        arango_username=ARANGO_USER,
        arango_password=ARANGO_PASSWORD
    )
    # Initialize SRv6 tunnels collection
    arangodb_driver.init_srv6_tunnels_collection(
        client=client,
        arango_username=ARANGO_USER,
        arango_password=ARANGO_PASSWORD
    )
    # Initialize nodes config collection
    arangodb_driver.init_nodes_config_collection(
        client=client,
        arango_username=ARANGO_USER,
        arango_password=ARANGO_PASSWORD
    )


# Entry point for this module
if __name__ == '__main__':
    init_srv6_usid_db()
    init_db_collections()
