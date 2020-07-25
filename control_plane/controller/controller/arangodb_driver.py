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
# Driver for ArangoDB
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
ArangoDB driver
'''

# pylint: disable=too-many-arguments


# python-arango dependencies
from arango import ArangoClient


class NodesConfigNotLoadedError(Exception):
    '''
    NodesConfigNotLoadedError
    '''


def connect_arango(url):
    '''
    Initialize the ArangoDB client.

    :param url: ArangoDB URL or list of URLs.
    :type url: str
    :return: ArangoDB client
    :rtype: arango.client.ArangoClient
    '''
    return ArangoClient(hosts=url)


def connect_db(client, db_name, username, password):
    '''
    Connect to a Arango database.

    :param db_name: Database name.
    :type db_name: str
    :param username: Username for basic authentication.
    :type username: str
    :param password: Password for basic authentication.
    :type password: str
    :return: Standard database API wrapper.
    :rtype: arango.database.StandardDatabase
    '''
    # Connect to "db_name" database.
    return client.db(db_name, username=username, password=password)


def connect_srv6_usid_db(client, username, password):
    '''
    Connect to "srv6_usid" database.

    :param client: ArangoDB client.
    :type client: arango.client.ArangoClient
    :param username: Username for basic authentication.
    :type username: str
    :param password: Password for basic authentication.
    :type password: str
    :return: Standard database API wrapper.
    :rtype: arango.database.StandardDatabase
    '''
    # Connect to "srv6_usid" database.
    return connect_db(client=client, db_name='srv6_usid',
                      username=username, password=password)


def init_srv6_usid_db(client, arango_username, arango_password, force=False):
    '''
    Initialize "srv6_usid" database.

    :param client: ArangoDB client.
    :type client: arango.client.ArangoClient
    :param arango_username: Username for basic authentication.
    :type arango_username: str
    :param arango_password: Password for basic authentication.
    :type arango_password: str
    :param force: By default the database is not re-initialized if it already
                  exists. If this param is True, clear the database before the
                  initialization if it already exists.
    :type force: bool
    :return: True if the operation completed successfully, False if an error
             occurred.
    :rtype: bool
    :raises arango.exceptions.DatabaseCreateError: If create fails.
    '''
    # Connect to "_system" database as root user.
    # This returns an API wrapper for "_system" database.
    sys_db = connect_db(
        client=client,
        db_name='_system',
        username=arango_username,
        password=arango_password
    )
    # Create "srv6_usid" database, if it does not exist
    if sys_db.has_database('srv6_usid'):
        # The database already exists
        if force:
            # If force is True, reinizialize it
            sys_db.delete_database(name='srv6_usid')
            is_success = sys_db.create_database(name='srv6_usid')
        else:
            # If force is False, return the database without re-init it
            is_success = sys_db.collection(name='srv6_usid')
    else:
        # The database does not exist, create a new one
        is_success = sys_db.create_database(name='srv6_usid')
    # Return True if the database has been initialized successfully,
    # False otherwise
    return is_success


def init_usid_policies_collection(client, arango_username, arango_password,
                                  force=False):
    '''
    Initialize "usid_policies" collection.

    :param client: ArangoDB client.
    :type client: arango.client.ArangoClient
    :param arango_username: Username for basic authentication.
    :type arango_username: str
    :param arango_password: Password for basic authentication.
    :type arango_password: str
    :param force: By default the collection is not re-initialized if it
                  already exists. If this param is True, clear the collection
                  before the initialization if it already exists.
    :type force: bool
    :return: Standard collection API wrapper.
    :rtype: arango.collection.StandardCollection
    :raises arango.exceptions.CollectionCreateError: If create fails.
    '''
    # Connect to "srv6_usid" database as root user.
    # This returns an API wrapper for "srv6_usid" database.
    database = connect_srv6_usid_db(
        client=client,
        username=arango_username,
        password=arango_password
    )
    # Get the API wrapper for database "usid_policies".
    database = client.db('srv6_usid', username=arango_username,
                         password=arango_password)
    # Create "usid_policies" collection, if it does not exist
    if database.has_collection('usid_policies'):
        # The collection already exists
        if force:
            # If force is True, reinizialize it
            database.delete_collection(name='usid_policies')
            usid_policies = database.create_collection(name='usid_policies')
        else:
            # If force is False, return the collection without re-init it
            usid_policies = database.collection(name='usid_policies')
    else:
        # The collection does not exist, create a new one
        usid_policies = database.create_collection(name='usid_policies')
    # Return the "usid_policies" collection
    return usid_policies


def insert_usid_policy(database, lr_dst, rl_dst, lr_nodes, rl_nodes,
                       table=None, metric=None, l_grpc_ip=None,
                       l_grpc_port=None, l_fwd_engine=None,
                       r_grpc_ip=None, r_grpc_port=None,
                       r_fwd_engine=None, decap_sid=None, locator=None):
    '''
    Insert a uSID policy into the 'usid_policies' collection of a Arango
    database.

    :param database: Database where the uSID policy must be saved.
    :type database: arango.database.StandardDatabase
    :param lr_dst: Destination (IP address or network prefix) for the
                   left-to-right path.
    :type lr_dst: str
    :param rl_dst: Destination (IP address or network prefix) for the
                   right-to-left path.
    :type rl_dst: str
    :param lr_nodes: List of nodes (names or uN sids) making the left-to-right
                     path.
    :type lr_nodes: list
    :param rl_nodes: List of nodes (names or uN sids) making the right-to-left
                     path.
    :type rl_nodes: list
    :param table: FIB table where the policy must be saved.
    :type table: int, optional
    :param metric: Metric (weight) to be used for the policy.
    :type metric: int, optional
    :param l_grpc_ip: gRPC IP address of the left node, required if the left
                      node is expressed numerically in the nodes list.
    :type l_grpc_ip: str, optional
    :param l_grpc_port: gRPC port of the left node, required if the left
                        node is expressed numerically in the nodes list.
    :type l_grpc_port: str, optional
    :param l_fwd_engine: forwarding engine of the left node, required if the
                         left node is expressed numerically in the nodes list.
    :type l_fwd_engine: str, optional
    :param r_grpc_ip: gRPC IP address of the right node, required if the right
                      node is expressed numerically in the nodes list.
    :type r_grpc_ip: str, optional
    :param r_grpc_port: gRPC port of the right node, required if the right
                        node is expressed numerically in the nodes list.
    :type r_grpc_port: str, optional
    :param r_fwd_engine: Forwarding engine of the right node, required if the
                         right node is expressed numerically in the nodes
                         list.
    :type r_fwd_engine: str, optional
    :param decap_sid: uSID used for the decap behavior (End.DT6).
    :type decap_sid: str, optional
    :param locator: Locator prefix (e.g. 'fcbb:bbbb::').
    :type locator: str, optional
    :return: True.
    :rtype: bool
    :raises arango.exceptions.arango.exceptions.DocumentInsertError: If insert
                                                                     fails.
    '''
    # Build a dict-representation of the uSID policy
    policy = {
        'lr_dst': lr_dst,
        'rl_dst': rl_dst,
        'lr_nodes': lr_nodes,
        'rl_nodes': rl_nodes,
        'table': table,
        'metric': metric,
        'l_grpc_ip': l_grpc_ip,
        'l_grpc_port': l_grpc_port,
        'l_fwd_engine': l_fwd_engine,
        'r_grpc_ip': r_grpc_ip,
        'r_grpc_port': r_grpc_port,
        'r_fwd_engine': r_fwd_engine,
        'decap_sid': decap_sid,
        'locator': locator
    }
    # Get the uSID policy collection
    # This returns an API wrapper for "usid_policies" collection
    usid_policies = database.collection(name='usid_policies')
    # Insert the policy
    # The parameter silent is set to True to avoid to return document metadata
    # This allows us to sav resources
    return usid_policies.insert(document=policy, silent=True)


def find_usid_policy(database, key=None, lr_dst=None,
                     rl_dst=None, lr_nodes=None, rl_nodes=None,
                     table=None, metric=None):
    '''
    Find a uSID policy in the 'usid_policies' collection of a Arango database.

    :param database: Database where to lookup the uSID policy.
    :type database: arango.database.StandardDatabase
    :param key: Key of the searched document.
    :type key: int, optional
    :param lr_dst: Destination (IP address or network prefix) for the
                   left-to-right path.
    :type lr_dst: str, optional
    :param rl_dst: Destination (IP address or network prefix) for the
                   right-to-left path.
    :type rl_dst: str, optional
    :param lr_nodes: List of nodes making the left-to-right path.
    :type lr_nodes: list, optional
    :param rl_nodes: List of nodes making the right-to-left path.
    :type rl_nodes: list, optional
    :param table: FIB table where the policy is saved.
    :type table: int, optional
    :param metric: Metric (weight) of the policy.
    :type metric: int, optional
    :return: Document cursor.
    :rtype: arango.cursor.Cursor
    :raises arango.exceptions.DocumentGetError: If retrieval fails.
    '''
    # Get the uSID policy collection
    # This returns an API wrapper for "usid_policies" collection
    usid_policies = database.collection('usid_policies')
    # Build a dict representation of the policy
    policy = dict()
    if key is not None:
        policy['_key'] = str(key)
    if lr_dst is not None:
        policy['lr_dst'] = lr_dst
    if rl_dst is not None:
        policy['rl_dst'] = rl_dst
    if lr_nodes is not None:
        policy['lr_nodes'] = lr_nodes
    if rl_nodes is not None:
        policy['rl_nodes'] = rl_nodes
    if table is not None:
        policy['table'] = table
    if metric is not None:
        policy['metric'] = metric
    # Find the policy
    # Return all documents that match the given filters
    return usid_policies.find(filters=policy)


def update_usid_policy(database, key=None, lr_dst=None, rl_dst=None,
                       lr_nodes=None, rl_nodes=None, table=None, metric=None):
    '''
    Update a uSID policy into a ArangoDB database.

    :param database: Database where the uSID policy to be updated is saved.
    :type database: arango.database.StandardDatabase
    :param key: Key of the searched document.
    :type key: int, optional
    :param lr_dst: Destination (IP address or network prefix) for the
                   left-to-right path.
    :type lr_dst: str, optional
    :param rl_dst: Destination (IP address or network prefix) for the
                   right-to-left path.
    :type rl_dst: str, optional
    :param lr_nodes: List of nodes making the left-to-right path.
    :type lr_nodes: list, optional
    :param rl_nodes: List of nodes making the right-to-left path.
    :type rl_nodes: list, optional
    :param table: FIB table where the policy must be saved.
    :type table: int, optional
    :param metric: Metric (weight) to be used for the policy.
    :type metric: int, optional
    :return: True.
    :rtype: bool
    :raises arango.exceptions.DocumentUpdateError: If update fails.
    :raises arango.exceptions.DocumentRevisionError: If revisions mismatch.
    '''
    # Operation not yet implemented
    raise NotImplementedError


def delete_usid_policy(database, key, lr_dst=None,
                       rl_dst=None, lr_nodes=None, rl_nodes=None,
                       table=None, metric=None, ignore_missing=False):
    '''
    Remove a uSID policy from the 'usid_policies' collection of a ArangoDB
    database.

    :param database: Database where the uSID policy to be updated is saved.
    :type database: arango.database.StandardDatabase
    :param key: Key of the document to be deleted.
    :type key: int
    :param lr_dst: Destination (IP address or network prefix) for the
                   left-to-right path.
    :type lr_dst: str, optional
    :param rl_dst: Destination (IP address or network prefix) for the
                   right-to-left path.
    :type rl_dst: str, optional
    :param lr_nodes: List of nodes making the left-to-right path.
    :type lr_nodes: list, optional
    :param rl_nodes: List of nodes making the right-to-left path.
    :type rl_nodes: list, optional
    :param table: FIB table where the policy is saved.
    :type table: int, optional
    :param metric: Metric (weight) used for the policy.
    :type metric: int, optional
    :return: True if the document matching the search criteria
             has been removed, or False if the document was not found and
             ignore_missing was set to True.
    :rtype: bool
    :raises arango.exceptions.DocumentDeleteError: If delete fails.
    :raises arango.exceptions.DocumentRevisionError: If revisions mismatch.
    '''
    # Get the uSID policy collection
    # This returns an API wrapper for "usid_policies" collection
    usid_policies = database.collection('usid_policies')
    # Build a dict representation of the policy
    policy = dict()
    if key is not None:
        policy['_key'] = key
    if lr_dst is not None:
        policy['lr_dst'] = lr_dst
    if rl_dst is not None:
        policy['rl_dst'] = rl_dst
    if lr_nodes is not None:
        policy['lr_nodes'] = lr_nodes
    if rl_nodes is not None:
        policy['rl_nodes'] = rl_nodes
    if table is not None:
        policy['table'] = table
    if metric is not None:
        policy['metric'] = metric
    # Remove the policy
    # Return True if the document matching the search criteria
    # has been removed, or False if the document was not found and
    # ignore_missing was set to True
    return usid_policies.delete(document=policy,
                                ignore_missing=ignore_missing)


def insert_nodes_config(database, nodes):
    '''
    Load nodes configuration on a database.

    :param database: Database where the nodes configuration must be saved.
    :type database: arango.database.StandardDatabase
    :param nodes: Dictionary containing the nodes configuration. For each
                  entry in the dict the following fields are expected:
                  - name: name (or identifier) of the node
                  - grpc_ip: IP address of the gRPC server
                  - grpc_port: port of the gRPC server
                  - uN: uN sid
                  - uDT: uDT sid used for the decap
                  - fwd_engine: forwarding engine (e.g. VPP or Linux)
    :type nodes: dict
    :return: True.
    :rtype: bool
    '''
    # Delete the collection if it already exists
    database.delete_collection(name='nodes_config', ignore_missing=True)
    # Create a new 'nodes_config' collection
    nodes_config = database.create_collection(name='nodes_config')
    # Insert the nodes config
    return nodes_config.insert(document=list(nodes.values()), silent=True)


def get_nodes_config(database):
    '''
    Get the nodes configuration saved to a database.

    :param database: Database where the nodes configuration is saved.
    :type database: arango.database.StandardDatabase
    :return: Dict reresentation of the nodes saved to the db. For a
             of the node entries, see :func:`insert_nodes_config`.
    :rtype: dict
    :raises controller.arangodb_driver.NodesConfigNotLoadedError: If nodes are
                                                                  not loaded
                                                                  on db.
    '''
    # Does the collection 'nodes_config' exist?
    if not database.has_collection('nodes_config'):
        raise NodesConfigNotLoadedError
    # Get the 'nodes_config' collection
    nodes_config = database.collection(name='nodes_config')
    # Have nodes been loaded loaded?
    if nodes_config.count() == 0:
        raise NodesConfigNotLoadedError
    # Get the nodes
    nodes = nodes_config.find(filters={})
    # Convert the nodes list to a dict representation
    return {node['name']: node for node in nodes}
