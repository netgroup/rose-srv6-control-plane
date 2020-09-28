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
# Utilities related to the topology management
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
This module provides a collection of utilities related to the topology
management.
'''

# General imports
import os

# Controller dependencies
from controller import arangodb_driver


def load_nodes_config(nodes):
    '''
    Load the nodes configuration to a ArangoDB database.

    :param nodes: The list of nodes to add to the database.
    :type nodes: list
    '''
    # ArangoDB params
    arango_url = os.getenv('ARANGO_URL')
    arango_user = os.getenv('ARANGO_USER')
    arango_password = os.getenv('ARANGO_PASSWORD')
    # Connect to ArangoDB
    client = arangodb_driver.connect_arango(
        url=arango_url)  # TODO keep arango connection open
    # Connect to the db
    database = arangodb_driver.connect_srv6_usid_db(
        client=client,
        username=arango_user,
        password=arango_password
    )
    # Save the nodes configuration to the database
    arangodb_driver.insert_nodes_config(
        database=database,
        nodes=nodes
    )


def get_nodes_config():
    '''
    Retrieve the nodes configuration from a ArangoDB database.

    :return: The list of the nodes.
    :rtype: list
    '''
    # ArangoDB params
    arango_url = os.getenv('ARANGO_URL')
    arango_user = os.getenv('ARANGO_USER')
    arango_password = os.getenv('ARANGO_PASSWORD')
    # Connect to ArangoDB
    client = arangodb_driver.connect_arango(
        url=arango_url)  # TODO keep arango connection open
    # Connect to the db
    database = arangodb_driver.connect_srv6_usid_db(
        client=client,
        username=arango_user,
        password=arango_password
    )
    # Retrieve the nodes configuration from the database
    nodes = arangodb_driver.get_nodes_config(
        database=database
    )
    # Return the nodes
    return nodes
