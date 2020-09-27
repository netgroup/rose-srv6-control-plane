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


def init_srv6_paths_collection(client, arango_username, arango_password,
                               force=False):
    '''
    Initialize "srv6_paths" collection.

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
    # Get the API wrapper for database "srv6_usid".
    database = client.db('srv6_usid', username=arango_username,
                         password=arango_password)
    # Create "srv6_paths" collection, if it does not exist
    if database.has_collection('srv6_paths'):
        # The collection already exists
        if force:
            # If force is True, reinizialize it
            database.delete_collection(name='srv6_paths')
            srv6_paths = database.create_collection(name='srv6_paths')
        else:
            # If force is False, return the collection without re-init it
            srv6_paths = database.collection(name='srv6_paths')
    else:
        # The collection does not exist, create a new one
        srv6_paths = database.create_collection(name='srv6_paths')
    # Return the "srv6_paths" collection
    return srv6_paths


def init_srv6_behaviors_collection(client, arango_username, arango_password,
                                   force=False):
    '''
    Initialize "srv6_behaviors" collection.

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
    # Get the API wrapper for database "srv6_usid".
    database = client.db('srv6_usid', username=arango_username,
                         password=arango_password)
    # Create "srv6_behaviors" collection, if it does not exist
    if database.has_collection('srv6_behaviors'):
        # The collection already exists
        if force:
            # If force is True, reinizialize it
            database.delete_collection(name='srv6_behaviors')
            srv6_behaviors = database.create_collection(name='srv6_behaviors')
        else:
            # If force is False, return the collection without re-init it
            srv6_behaviors = database.collection(name='srv6_behaviors')
    else:
        # The collection does not exist, create a new one
        srv6_behaviors = database.create_collection(name='srv6_behaviors')
    # Return the "srv6_behaviors" collection
    return srv6_behaviors


def init_srv6_tunnels_collection(client, arango_username, arango_password,
                                 force=False):
    '''
    Initialize "srv6_tunnels" collection.

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
    # Get the API wrapper for database "srv6_usid".
    database = client.db('srv6_usid', username=arango_username,
                         password=arango_password)
    # Create "srv6_tunnels" collection, if it does not exist
    if database.has_collection('srv6_tunnels'):
        # The collection already exists
        if force:
            # If force is True, reinizialize it
            database.delete_collection(name='srv6_tunnels')
            srv6_tunnels = database.create_collection(name='srv6_tunnels')
        else:
            # If force is False, return the collection without re-init it
            srv6_tunnels = database.collection(name='srv6_tunnels')
    else:
        # The collection does not exist, create a new one
        srv6_tunnels = database.create_collection(name='srv6_tunnels')
    # Return the "srv6_tunnels" collection
    return srv6_tunnels


def init_srv6_policies_collection(client, arango_username, arango_password,
                                  force=False):
    '''
    Initialize "srv6_policies" collection.

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
    # Get the API wrapper for database "srv6_usid".
    database = client.db('srv6_usid', username=arango_username,
                         password=arango_password)
    # Create "srv6_policies" collection, if it does not exist
    if database.has_collection('srv6_policies'):
        # The collection already exists
        if force:
            # If force is True, reinizialize it
            database.delete_collection(name='srv6_policies')
            srv6_policies = database.create_collection(name='srv6_policies')
        else:
            # If force is False, return the collection without re-init it
            srv6_policies = database.collection(name='srv6_policies')
    else:
        # The collection does not exist, create a new one
        srv6_policies = database.create_collection(name='srv6_policies')
    # Return the "srv6_policies" collection
    return srv6_policies


def init_nodes_config_collection(client, arango_username, arango_password,
                                 force=False):
    '''
    Initialize "nodes_config" collection.

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
    # Get the API wrapper for database "srv6_usid".
    database = client.db('srv6_usid', username=arango_username,
                         password=arango_password)
    # Create "nodes_config" collection, if it does not exist
    if database.has_collection('nodes_config'):
        # The collection already exists
        if force:
            # If force is True, reinizialize it
            database.delete_collection(name='nodes_config')
            nodes_config = database.create_collection(name='nodes_config')
        else:
            # If force is False, return the collection without re-init it
            nodes_config = database.collection(name='nodes_config')
    else:
        # The collection does not exist, create a new one
        nodes_config = database.create_collection(name='nodes_config')
    # Return the "nodes_config" collection
    return nodes_config


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


def insert_srv6_path(database, grpc_address, destination, segments=None,
                     device=None, encapmode=None, table=None, metric=None,
                     bsid_addr=None, fwd_engine=None, key=None):
    '''
    Insert a SRv6 path into the 'srv6_paths' collection of a Arango database.
    :param database: Database where the nodes configuration must be saved.
    :type database: arango.database.StandardDatabase
    :param grpc_address: The IP address of the gRPC server.
    :type grpc_address: str
    :param destination: The destination prefix of the SRv6 path.
                        It can be a IP address or a subnet.
    :type destination: str
    :param segments: The SID list to be applied to the packets going to
                     the destination.
    :type segments: list, optional
    :param device: Device of the SRv6 route.
    :type device: str, optional
    :param encapmode: The encap mode to use for the path, i.e. "inline" or
                      "encap".
    :type encapmode: str, optional
    :param table: Routing table containing the SRv6 route.
    :type table: int, optional
    :param metric: Metric for the SRv6 route.
    :type metric: int, optional
    :param bsid_addr: The Binding SID to be used for the route (only required
                      for VPP).
    :type bsid_addr: str, optional
    :param fwd_engine: Forwarding engine for the SRv6 route.
    :type fwd_engine: str, optional
    :param key: The key of the document in the ArangoDB database.
    :type key: str, optional
    :return: True.
    :rtype: bool
    :raises arango.exceptions.arango.exceptions.DocumentInsertError: If insert
                                                                     fails.
    '''
    # Build a dict-representation of the SRv6 path
    path = {
        'destination': destination,
        'segments': segments,
        'device': device,
        'encapmode': encapmode,
        'table': table,
        'metric': metric,
        'bsid_addr': bsid_addr,
        'fwd_engine': fwd_engine
    }
    # Key argument is optional
    if key is not None:
        path['_key'] = key
    # Get the SRv6 paths collection
    # This returns an API wrapper for "srv6_paths" collection
    srv6_paths = database.collection(name='srv6_paths')
    # Insert the path
    # The parameter silent is set to True to avoid to return document metadata
    # This allows us to save resources
    return srv6_paths.insert(document=path, silent=True)


def find_srv6_path(database, key=None, grpc_address=None, destination=None,
                   segments=None, device=None, encapmode=None, table=None,
                   metric=None, bsid_addr=None, fwd_engine=None):
    '''
    Find a SRv6 path in the 'srv6_paths' collection of a Arango database.
    :param database: Database where to lookup the SRv6 path.
    :type database: arango.database.StandardDatabase
    :param key: Key of the searched document.
    :type key: int, optional
    :param grpc_address: The IP address of the gRPC server.
    :type grpc_address: str, optional
    :param destination: The destination prefix of the SRv6 path.
                        It can be a IP address or a subnet.
    :type destination: str
    :param segments: The SID list to be applied to the packets going to
                     the destination.
    :type segments: list, optional
    :param device: Device of the SRv6 route.
    :type device: str, optional
    :param encapmode: The encap mode to use for the path, i.e. "inline" or
                      "encap".
    :type encapmode: str, optional
    :param table: Routing table containing the SRv6 route.
    :type table: int, optional
    :param metric: Metric for the SRv6 route.
    :type metric: int, optional
    :param bsid_addr: The Binding SID to be used for the route (only required
                      for VPP).
    :type bsid_addr: str, optional
    :param fwd_engine: Forwarding engine for the SRv6 route.
    :type fwd_engine: str, optional
    :return: Document cursor.
    :rtype: arango.cursor.Cursor
    :raises arango.exceptions.DocumentGetError: If retrieval fails.
    '''
    # Get the SRv6 path collection
    # This returns an API wrapper for "srv6_paths" collection
    srv6_paths = database.collection('srv6_paths')
    # Build a dict representation of the path
    path = dict()
    if key is not None:
        path['_key'] = str(key)
    if destination is not None:
        path['destination'] = destination
    if segments is not None:
        path['segments'] = segments
    if device is not None:
        path['device'] = device
    if encapmode is not None:
        path['encapmode'] = encapmode
    if table is not None:
        path['table'] = table
    if metric is not None:
        path['metric'] = metric
    if bsid_addr is not None:
        path['bsid_addr'] = bsid_addr
    if fwd_engine is not None:
        path['fwd_engine'] = fwd_engine
    # Find the path
    # Return all documents that match the given filters
    return srv6_paths.find(filters=path)


def update_srv6_path(database, key=None, grpc_address=None, destination=None,
                     segments=None, device=None, encapmode=None, table=None,
                     metric=None, bsid_addr=None, fwd_engine=None):
    '''
    Update a SRv6 path into a ArangoDB database.
    :param database: Database where the SRv6 path to be updated is saved.
    :type database: arango.database.StandardDatabase
    :param key: Key of the searched document.
    :type key: int, optional
    :param grpc_address: The IP address of the gRPC server.
    :type grpc_address: str, optional
    :param destination: The destination prefix of the SRv6 path.
                        It can be a IP address or a subnet.
    :type destination: str
    :param segments: The SID list to be applied to the packets going to
                     the destination.
    :type segments: list, optional
    :param device: Device of the SRv6 route.
    :type device: str, optional
    :param encapmode: The encap mode to use for the path, i.e. "inline" or
                      "encap".
    :type encapmode: str, optional
    :param table: Routing table containing the SRv6 route.
    :type table: int, optional
    :param metric: Metric for the SRv6 route.
    :type metric: int, optional
    :param bsid_addr: The Binding SID to be used for the route (only required
                      for VPP).
    :type bsid_addr: str, optional
    :param fwd_engine: Forwarding engine for the SRv6 route.
    :type fwd_engine: str, optional
    :return: True.
    :rtype: bool
    :raises arango.exceptions.DocumentUpdateError: If update fails.
    :raises arango.exceptions.DocumentRevisionError: If revisions mismatch.
    '''
    # Operation not yet implemented
    raise NotImplementedError


def delete_srv6_path(database, key, grpc_address=None, destination=None,
                     segments=None, device=None, encapmode=None, table=None,
                     metric=None, bsid_addr=None, fwd_engine=None,
                     ignore_missing=False):
    '''
    Remove a SRv6 path from the 'srv6_paths' collection of a ArangoDB
    database.
    :param database: Database where the SRv6 path to be removed is saved.
    :type database: arango.database.StandardDatabase
    :param key: Key of the document to be deleted.
    :type key: int
    :param grpc_address: The IP address of the gRPC server.
    :type grpc_address: str, optional
    :param destination: The destination prefix of the SRv6 path.
                        It can be a IP address or a subnet.
    :type destination: str
    :param segments: The SID list to be applied to the packets going to
                     the destination.
    :type segments: list, optional
    :param device: Device of the SRv6 route.
    :type device: str, optional
    :param encapmode: The encap mode to use for the path, i.e. "inline" or
                      "encap".
    :type encapmode: str, optional
    :param table: Routing table containing the SRv6 route.
    :type table: int, optional
    :param metric: Metric for the SRv6 route.
    :type metric: int, optional
    :param bsid_addr: The Binding SID to be used for the route (only required
                      for VPP).
    :type bsid_addr: str, optional
    :param fwd_engine: Forwarding engine for the SRv6 route.
    :type fwd_engine: str, optional
    :param ignore_missing: Define whether to ignore errors or not
                           (default: False).
    :type ignore_missing: bool, optional
    :return: True if the document matching the search criteria
             has been removed, or False if the document was not found and
             ignore_missing was set to True.
    :rtype: bool
    :raises arango.exceptions.DocumentDeleteError: If delete fails.
    :raises arango.exceptions.DocumentRevisionError: If revisions mismatch.
    '''
    # Get the SRv6 path collection
    # This returns an API wrapper for "srv6_paths" collection
    srv6_paths = database.collection('srv6_paths')
    # Build a dict representation of the path
    path = dict()
    if key is not None:
        path['_key'] = key
    if destination is not None:
        path['destination'] = destination
    if segments is not None:
        path['segments'] = segments
    if device is not None:
        path['device'] = device
    if encapmode is not None:
        path['encapmode'] = encapmode
    if table is not None:
        path['table'] = table
    if metric is not None:
        path['metric'] = metric
    if bsid_addr is not None:
        path['bsid_addr'] = bsid_addr
    if fwd_engine is not None:
        path['fwd_engine'] = fwd_engine
    # Remove the path
    # Return True if the document matching the search criteria
    # has been removed, or False if the document was not found and
    # ignore_missing was set to True
    return srv6_paths.delete(document=path, ignore_missing=ignore_missing)


def find_and_delete_srv6_path(database, key=None, grpc_address=None,
                              destination=None, segments=None, device=None,
                              encapmode=None, table=None, metric=None,
                              bsid_addr=None, fwd_engine=None,
                              ignore_missing=False):
    '''
    Find and remove a SRv6 path from the 'srv6_paths' collection of a ArangoDB
    database.
    :param database: Database where the SRv6 path to be removed is saved.
    :type database: arango.database.StandardDatabase
    :param key: Key of the document to be deleted.
    :type key: int
    :param grpc_address: The IP address of the gRPC server.
    :type grpc_address: str, optional
    :param destination: The destination prefix of the SRv6 path.
                        It can be a IP address or a subnet.
    :type destination: str
    :param segments: The SID list to be applied to the packets going to
                     the destination.
    :type segments: list, optional
    :param device: Device of the SRv6 route.
    :type device: str, optional
    :param encapmode: The encap mode to use for the path, i.e. "inline" or
                      "encap".
    :type encapmode: str, optional
    :param table: Routing table containing the SRv6 route.
    :type table: int, optional
    :param metric: Metric for the SRv6 route.
    :type metric: int, optional
    :param bsid_addr: The Binding SID to be used for the route (only required
                      for VPP).
    :type bsid_addr: str, optional
    :param fwd_engine: Forwarding engine for the SRv6 route.
    :type fwd_engine: str, optional
    :param ignore_missing: Define whether to ignore errors or not
                           (default: False).
    :type ignore_missing: bool, optional
    :return: True if the document matching the search criteria
             has been removed, or False if the document was not found and
             ignore_missing was set to True.
    :rtype: bool
    :raises arango.exceptions.DocumentDeleteError: If delete fails.
    :raises arango.exceptions.DocumentRevisionError: If revisions mismatch.
    '''
    # Get the SRv6 path collection
    # This returns an API wrapper for "srv6_paths" collection
    srv6_paths = database.collection('srv6_paths')
    # Build a dict representation of the path
    path = dict()
    if key is not None:
        path['_key'] = key
    if destination is not None:
        path['destination'] = destination
    if segments is not None:
        path['segments'] = segments
    if device is not None:
        path['device'] = device
    if encapmode is not None:
        path['encapmode'] = encapmode
    if table is not None:
        path['table'] = table
    if metric is not None:
        path['metric'] = metric
    if bsid_addr is not None:
        path['bsid_addr'] = bsid_addr
    if fwd_engine is not None:
        path['fwd_engine'] = fwd_engine
    # Find the path
    # Return all documents that match the given filters
    paths = srv6_paths.find(filters=path)
    # Remove the path
    # Return True if the document matching the search criteria
    # has been removed, or False if the document was not found and
    # ignore_missing was set to True
    for path in paths:
        srv6_paths.delete(document=path, ignore_missing=ignore_missing)


def insert_srv6_behavior(database, grpc_address, segment, action=None,
                         device=None, table=None, nexthop=None,
                         lookup_table=None, interface=None, segments=None,
                         metric=None, fwd_engine=None):
    '''
    Insert a SRv6 behavior into the 'srv6_behaviors' collection of a Arango
    database.
    :param database: Database where the nodes configuration must be saved.
    :type database: arango.database.StandardDatabase
    :param grpc_address: The IP address of the gRPC server.
    :type grpc_address: str
    :param segment: The local segment of the SRv6 behavior. It can be a IP
                    address or a subnet.
    :type segment: str
    :param action: The SRv6 action associated to the behavior (e.g. End or
                   End.DT6).
    :type action: str, optional
    :param device: Device of the SRv6 route.
    :type device: str, optional
    :param table: Routing table containing the SRv6 route.
    :type table: int, optional
    :param nexthop: The nexthop of cross-connect behaviors (e.g. End.DX4
                    or End.DX6).
    :type nexthop: str, optional
    :param lookup_table: The lookup table for the decap behaviors (e.g.
                         End.DT4 or End.DT6).
    :type lookup_table: int, optional
    :param interface: The outgoing interface for the End.DX2 behavior.
    :type interface: str, optional
    :param segments: The SID list to be applied for the End.B6 behavior.
    :type segments: list, optional
    :param metric: Metric for the SRv6 route.
    :type metric: int, optional
    :param fwd_engine: Forwarding engine for the SRv6 route.
    :type fwd_engine: str, optional
    :return: True.
    :rtype: bool
    :raises arango.exceptions.arango.exceptions.DocumentInsertError: If insert
                                                                     fails.
    '''
    # Build a dict-representation of the SRv6 behavior
    behavior = {
        'segment': segment,
        'action': action,
        'device': device,
        'table': table,
        'nexthop': nexthop,
        'lookup_table': lookup_table,
        'interface': interface,
        'segments': segments,
        'metric': metric,
        'fwd_engine': fwd_engine
    }
    # Get the SRv6 behaviors collection
    # This returns an API wrapper for "srv6_behaviors" collection
    srv6_behaviors = database.collection(name='srv6_behaviors')
    # Insert the behavior
    # The parameter silent is set to True to avoid to return document metadata
    # This allows us to save resources
    return srv6_behaviors.insert(document=behavior, silent=True)


def find_srv6_behavior(database, key=None, grpc_address=None, segment=None,
                       action=None, device=None, table=None, nexthop=None,
                       lookup_table=None, interface=None, segments=None,
                       metric=None, fwd_engine=None):
    '''
    Find a SRv6 behavior in the 'srv6_behaviors' collection of a Arango
    database.
    :param database: Database where to lookup the SRv6 behavior.
    :type database: arango.database.StandardDatabase
    :param key: Key of the searched document.
    :type key: int, optional
    :param grpc_address: The IP address of the gRPC server.
    :type grpc_address: str, optional
    :param segment: The local segment of the SRv6 behavior. It can be a IP
                    address or a subnet.
    :type segment: str
    :param action: The SRv6 action associated to the behavior (e.g. End or
                   End.DT6).
    :type action: str, optional
    :param device: Device of the SRv6 route.
    :type device: str, optional
    :param table: Routing table containing the SRv6 route.
    :type table: int, optional
    :param nexthop: The nexthop of cross-connect behaviors (e.g. End.DX4
                    or End.DX6).
    :type nexthop: str, optional
    :param lookup_table: The lookup table for the decap behaviors (e.g.
                         End.DT4 or End.DT6).
    :type lookup_table: int, optional
    :param interface: The outgoing interface for the End.DX2 behavior.
    :type interface: str, optional
    :param segments: The SID list to be applied for the End.B6 behavior.
    :type segments: list, optional
    :param metric: Metric for the SRv6 route.
    :type metric: int, optional
    :param fwd_engine: Forwarding engine for the SRv6 route.
    :type fwd_engine: str, optional
    :return: Document cursor.
    :rtype: arango.cursor.Cursor
    :raises arango.exceptions.DocumentGetError: If retrieval fails.
    '''
    # Get the SRv6 behavior collection
    # This returns an API wrapper for "srv6_behaviors" collection
    srv6_behaviors = database.collection('srv6_behaviors')
    # Build a dict representation of the behavior
    behavior = dict()
    if key is not None:
        behavior['_key'] = str(key)
    if segment is not None:
        behavior['segment'] = segment
    if action is not None:
        behavior['action'] = action
    if device is not None:
        behavior['device'] = device
    if table is not None:
        behavior['table'] = table
    if nexthop is not None:
        behavior['nexthop'] = nexthop
    if lookup_table is not None:
        behavior['lookup_table'] = lookup_table
    if interface is not None:
        behavior['interface'] = interface
    if segments is not None:
        behavior['segments'] = segments
    if metric is not None:
        behavior['metric'] = metric
    if fwd_engine is not None:
        behavior['fwd_engine'] = fwd_engine
    # Find the behavior
    # Return all documents that match the given filters
    return srv6_behaviors.find(filters=behavior)


def update_srv6_behavior(database, key=None, grpc_address=None, segment=None,
                         action=None, device=None, table=None, nexthop=None,
                         lookup_table=None, interface=None, segments=None,
                         metric=None, fwd_engine=None):
    '''
    Update a SRv6 behavior into a ArangoDB database.
    :param database: Database where the SRv6 behavior to be updated is saved.
    :type database: arango.database.StandardDatabase
    :param key: Key of the searched document.
    :type key: int, optional
    :param grpc_address: The IP address of the gRPC server.
    :type grpc_address: str, optional
    :param segment: The local segment of the SRv6 behavior. It can be a IP
                    address or a subnet.
    :type segment: str
    :param action: The SRv6 action associated to the behavior (e.g. End or
                   End.DT6).
    :type action: str, optional
    :param device: Device of the SRv6 route.
    :type device: str, optional
    :param table: Routing table containing the SRv6 route.
    :type table: int, optional
    :param nexthop: The nexthop of cross-connect behaviors (e.g. End.DX4
                    or End.DX6).
    :type nexthop: str, optional
    :param lookup_table: The lookup table for the decap behaviors (e.g.
                         End.DT4 or End.DT6).
    :type lookup_table: int, optional
    :param interface: The outgoing interface for the End.DX2 behavior.
    :type interface: str, optional
    :param segments: The SID list to be applied for the End.B6 behavior.
    :type segments: list, optional
    :param metric: Metric for the SRv6 route.
    :type metric: int, optional
    :param fwd_engine: Forwarding engine for the SRv6 route.
    :type fwd_engine: str, optional
    :return: True.
    :rtype: bool
    :raises arango.exceptions.DocumentUpdateError: If update fails.
    :raises arango.exceptions.DocumentRevisionError: If revisions mismatch.
    '''
    # Operation not yet implemented
    raise NotImplementedError


def delete_srv6_behavior(database, key, grpc_address=None, segment=None,
                         action=None, device=None, table=None, nexthop=None,
                         lookup_table=None, interface=None, segments=None,
                         metric=None, fwd_engine=None, ignore_missing=False):
    '''
    Remove a SRv6 behavior from the 'srv6_behaviors' collection of a ArangoDB
    database.
    :param database: Database where the SRv6 behavior to be removed is saved.
    :type database: arango.database.StandardDatabase
    :param key: Key of the document to be deleted.
    :type key: int
    :param grpc_address: The IP address of the gRPC server.
    :type grpc_address: str, optional
    :param segment: The local segment of the SRv6 behavior. It can be a IP
                    address or a subnet.
    :type segment: str
    :param action: The SRv6 action associated to the behavior (e.g. End or
                   End.DT6).
    :type action: str, optional
    :param device: Device of the SRv6 route.
    :type device: str, optional
    :param table: Routing table containing the SRv6 route.
    :type table: int, optional
    :param nexthop: The nexthop of cross-connect behaviors (e.g. End.DX4
                    or End.DX6).
    :type nexthop: str, optional
    :param lookup_table: The lookup table for the decap behaviors (e.g.
                         End.DT4 or End.DT6).
    :type lookup_table: int, optional
    :param interface: The outgoing interface for the End.DX2 behavior.
    :type interface: str, optional
    :param segments: The SID list to be applied for the End.B6 behavior.
    :type segments: list, optional
    :param metric: Metric for the SRv6 route.
    :type metric: int, optional
    :param fwd_engine: Forwarding engine for the SRv6 route.
    :type fwd_engine: str, optional
    :param ignore_missing: Define whether to ignore errors or not
                           (default: False).
    :type ignore_missing: bool, optional
    :return: True if the document matching the search criteria
             has been removed, or False if the document was not found and
             ignore_missing was set to True.
    :rtype: bool
    :raises arango.exceptions.DocumentDeleteError: If delete fails.
    :raises arango.exceptions.DocumentRevisionError: If revisions mismatch.
    '''
    # Get the SRv6 behavior collection
    # This returns an API wrapper for "srv6_behaviors" collection
    srv6_behaviors = database.collection('srv6_behaviors')
    # Build a dict representation of the behavior
    behavior = dict()
    if key is not None:
        behavior['_key'] = key
    if segment is not None:
        behavior['segment'] = segment
    if action is not None:
        behavior['action'] = action
    if device is not None:
        behavior['device'] = device
    if table is not None:
        behavior['table'] = table
    if nexthop is not None:
        behavior['nexthop'] = nexthop
    if lookup_table is not None:
        behavior['lookup_table'] = lookup_table
    if interface is not None:
        behavior['interface'] = interface
    if segments is not None:
        behavior['segments'] = segments
    if metric is not None:
        behavior['metric'] = metric
    if fwd_engine is not None:
        behavior['fwd_engine'] = fwd_engine
    # Remove the behavior
    # Return True if the document matching the search criteria
    # has been removed, or False if the document was not found and
    # ignore_missing was set to True
    return srv6_behaviors.delete(document=behavior,
                                 ignore_missing=ignore_missing)


def insert_srv6_tunnel(database, l_grpc_address, r_grpc_address,
                       sidlist_lr=None, sidlist_rl=None, dest_lr=None,
                       dest_rl=None, localseg_lr=None, localseg_rl=None,
                       bsid_addr=None, fwd_engine=None,
                       is_unidirectional=False):
    '''
    Insert a SRv6 tunnel into the 'srv6_tunnels' collection of a Arango
    database.
    :param database: Database where the nodes configuration must be saved.
    :type database: arango.database.StandardDatabase
    :param l_grpc_address: The IP address of the gRPC server on the left node.
    :type l_grpc_address: str
    :param r_grpc_address: The IP address of the gRPC server on the right node.
    :type r_grpc_address: str
    :param sidlist_lr: The SID list to be installed on the packets going
                       from <node_l> to <node_r>.
    :type sidlist_lr: list, optional
    :param sidlist_rl: The SID list to be installed on the packets going
                       from <node_r> to <node_l>.
    :type sidlist_rl: list, optional
    :param dest_lr: The destination prefix of the SRv6 path from <node_l>
                    to <node_r>. It can be a IP address or a subnet.
    :type dest_lr: str, optional
    :param dest_rl: The destination prefix of the SRv6 path from <node_r>
                    to <node_l>. It can be a IP address or a subnet.
    :type dest_rl: str, optional
    :param localseg_lr: The local segment to be associated to the End.DT6
                        seg6local function for the SRv6 path from <node_l>
                        to <node_r>.
    :type localseg_lr: str, optional
    :param localseg_rl: The local segment to be associated to the End.DT6
                        seg6local function for the SRv6 path from <node_r>
                        to <node_l>.
    :type localseg_rl: str, optional
    :param bsid_addr: The Binding SID to be used for the route (only required
                      for VPP).
    :type bsid_addr: str, optional
    :param fwd_engine: Forwarding engine for the SRv6 route.
    :type fwd_engine: str, optional
    :param is_unidirectional: Define whether the tunnel is unidirectional or
                              not (default: False).
    :type is_unidirectional: bool, optional
    :return: True.
    :rtype: bool
    :raises arango.exceptions.arango.exceptions.DocumentInsertError: If insert
                                                                     fails.
    '''
    # Build a dict-representation of the SRv6 tunnel
    tunnel = {
        'sidlist_lr': sidlist_lr,
        'sidlist_rl': sidlist_rl,
        'dest_lr': dest_lr,
        'dest_rl': dest_rl,
        'localseg_lr': localseg_lr,
        'localseg_rl': localseg_rl,
        'bsid_addr': bsid_addr,
        'fwd_engine': fwd_engine,
        'is_unidirectional': is_unidirectional
    }
    # Get the SRv6 tunnels collection
    # This returns an API wrapper for "srv6_tunnels" collection
    srv6_tunnels = database.collection(name='srv6_tunnels')
    # Insert the tunnel
    # The parameter silent is set to True to avoid to return document metadata
    # This allows us to save resources
    return srv6_tunnels.insert(document=tunnel, silent=True)


def find_srv6_tunnel(database, key=None, l_grpc_address=None,
                     r_grpc_address=None, sidlist_lr=None, sidlist_rl=None,
                     dest_lr=None, dest_rl=None, localseg_lr=None,
                     localseg_rl=None, bsid_addr=None, fwd_engine=None,
                     is_unidirectional=False):
    '''
    Find a SRv6 tunnel in the 'srv6_tunnels' collection of a Arango
    database.
    :param database: Database where to lookup the SRv6 tunnel.
    :type database: arango.database.StandardDatabase
    :param key: Key of the searched document.
    :type key: int, optional
    :param l_grpc_address: The IP address of the gRPC server on the left node.
    :type l_grpc_address: str, optional
    :param r_grpc_address: The IP address of the gRPC server on the right node.
    :type r_grpc_address: str, optional
    :param sidlist_lr: The SID list to be installed on the packets going
                       from <node_l> to <node_r>.
    :type sidlist_lr: list, optional
    :param sidlist_rl: The SID list to be installed on the packets going
                       from <node_r> to <node_l>.
    :type sidlist_rl: list, optional
    :param dest_lr: The destination prefix of the SRv6 path from <node_l>
                    to <node_r>. It can be a IP address or a subnet.
    :type dest_lr: str, optional
    :param dest_rl: The destination prefix of the SRv6 path from <node_r>
                    to <node_l>. It can be a IP address or a subnet.
    :type dest_rl: str, optional
    :param localseg_lr: The local segment to be associated to the End.DT6
                        seg6local function for the SRv6 path from <node_l>
                        to <node_r>.
    :type localseg_lr: str, optional
    :param localseg_rl: The local segment to be associated to the End.DT6
                        seg6local function for the SRv6 path from <node_r>
                        to <node_l>.
    :type localseg_rl: str, optional
    :param bsid_addr: The Binding SID to be used for the route (only required
                      for VPP).
    :type bsid_addr: str, optional
    :param fwd_engine: Forwarding engine for the SRv6 route.
    :type fwd_engine: str, optional
    :param is_unidirectional: Define whether the tunnel is unidirectional or
                              not (default: False).
    :type is_unidirectional: bool, optional
    :return: Document cursor.
    :rtype: arango.cursor.Cursor
    :raises arango.exceptions.DocumentGetError: If retrieval fails.
    '''
    # Get the SRv6 tunnel collection
    # This returns an API wrapper for "srv6_tunnels" collection
    srv6_tunnels = database.collection('srv6_tunnels')
    # Build a dict representation of the tunnel
    tunnel = dict()
    if key is not None:
        tunnel['_key'] = str(key)
    if sidlist_lr is not None:
        tunnel['sidlist_lr'] = sidlist_lr
    if sidlist_rl is not None:
        tunnel['sidlist_rl'] = sidlist_rl
    if dest_lr is not None:
        tunnel['dest_lr'] = dest_lr
    if dest_rl is not None:
        tunnel['dest_rl'] = dest_rl
    if localseg_lr is not None:
        tunnel['localseg_lr'] = localseg_lr
    if localseg_rl is not None:
        tunnel['localseg_rl'] = localseg_rl
    if bsid_addr is not None:
        tunnel['bsid_addr'] = bsid_addr
    if fwd_engine is not None:
        tunnel['fwd_engine'] = fwd_engine
    tunnel['is_unidirectional'] = is_unidirectional
    # Find the tunnel
    # Return all documents that match the given filters
    return srv6_tunnels.find(filters=tunnel)


def update_srv6_tunnel(database, key=None, l_grpc_address=None,
                       r_grpc_address=None, sidlist_lr=None, sidlist_rl=None,
                       dest_lr=None, dest_rl=None, localseg_lr=None,
                       localseg_rl=None, bsid_addr=None, fwd_engine=None,
                       is_unidirectional=False):
    '''
    Update a SRv6 tunnel into a ArangoDB database.
    :param database: Database where the SRv6 tunnel to be updated is saved.
    :type database: arango.database.StandardDatabase
    :param key: Key of the searched document.
    :type key: int, optional
    :param l_grpc_address: The IP address of the gRPC server on the left node.
    :type l_grpc_address: str, optional
    :param r_grpc_address: The IP address of the gRPC server on the right node.
    :type r_grpc_address: str, optional
    :param sidlist_lr: The SID list to be installed on the packets going
                       from <node_l> to <node_r>.
    :type sidlist_lr: list, optional
    :param sidlist_rl: The SID list to be installed on the packets going
                       from <node_r> to <node_l>.
    :type sidlist_rl: list, optional
    :param dest_lr: The destination prefix of the SRv6 path from <node_l>
                    to <node_r>. It can be a IP address or a subnet.
    :type dest_lr: str, optional
    :param dest_rl: The destination prefix of the SRv6 path from <node_r>
                    to <node_l>. It can be a IP address or a subnet.
    :type dest_rl: str, optional
    :param localseg_lr: The local segment to be associated to the End.DT6
                        seg6local function for the SRv6 path from <node_l>
                        to <node_r>.
    :type localseg_lr: str, optional
    :param localseg_rl: The local segment to be associated to the End.DT6
                        seg6local function for the SRv6 path from <node_r>
                        to <node_l>.
    :type localseg_rl: str, optional
    :param bsid_addr: The Binding SID to be used for the route (only required
                      for VPP).
    :type bsid_addr: str, optional
    :param fwd_engine: Forwarding engine for the SRv6 route.
    :type fwd_engine: str, optional
    :param is_unidirectional: Define whether the tunnel is unidirectional or
                              not (default: False).
    :type is_unidirectional: bool, optional
    :return: True.
    :rtype: bool
    :raises arango.exceptions.DocumentUpdateError: If update fails.
    :raises arango.exceptions.DocumentRevisionError: If revisions mismatch.
    '''
    # Operation not yet implemented
    raise NotImplementedError


def delete_srv6_tunnel(database, key, l_grpc_address=None,
                       r_grpc_address=None, sidlist_lr=None, sidlist_rl=None,
                       dest_lr=None, dest_rl=None, localseg_lr=None,
                       localseg_rl=None, bsid_addr=None, fwd_engine=None,
                       is_unidirectional=False, ignore_missing=False):
    '''
    Remove a SRv6 tunnel from the 'srv6_tunnels' collection of a ArangoDB
    database.
    :param database: Database where the SRv6 tunnel to be updated is saved.
    :type database: arango.database.StandardDatabase
    :param key: Key of the document to be deleted.
    :type key: int
    :param l_grpc_address: The IP address of the gRPC server on the left node.
    :type l_grpc_address: str, optional
    :param r_grpc_address: The IP address of the gRPC server on the right node.
    :type r_grpc_address: str, optional
    :param sidlist_lr: The SID list to be installed on the packets going
                       from <node_l> to <node_r>.
    :type sidlist_lr: list, optional
    :param sidlist_rl: The SID list to be installed on the packets going
                       from <node_r> to <node_l>.
    :type sidlist_rl: list, optional
    :param dest_lr: The destination prefix of the SRv6 path from <node_l>
                    to <node_r>. It can be a IP address or a subnet.
    :type dest_lr: str, optional
    :param dest_rl: The destination prefix of the SRv6 path from <node_r>
                    to <node_l>. It can be a IP address or a subnet.
    :type dest_rl: str, optional
    :param localseg_lr: The local segment to be associated to the End.DT6
                        seg6local function for the SRv6 path from <node_l>
                        to <node_r>.
    :type localseg_lr: str, optional
    :param localseg_rl: The local segment to be associated to the End.DT6
                        seg6local function for the SRv6 path from <node_r>
                        to <node_l>.
    :type localseg_rl: str, optional
    :param bsid_addr: The Binding SID to be used for the route (only required
                      for VPP).
    :type bsid_addr: str, optional
    :param fwd_engine: Forwarding engine for the SRv6 route.
    :type fwd_engine: str, optional
    :param is_unidirectional: Define whether the tunnel is unidirectional or
                              not (default: False).
    :type is_unidirectional: bool, optional
    :param ignore_missing: Define whether to ignore errors or not
                           (default: False).
    :type ignore_missing: bool, optional
    :return: True if the document matching the search criteria
             has been removed, or False if the document was not found and
             ignore_missing was set to True.
    :rtype: bool
    :raises arango.exceptions.DocumentDeleteError: If delete fails.
    :raises arango.exceptions.DocumentRevisionError: If revisions mismatch.
    '''
    # Get the SRv6 tunnel collection
    # This returns an API wrapper for "srv6_tunnels" collection
    srv6_tunnels = database.collection('srv6_tunnels')
    # Build a dict representation of the tunnel
    tunnel = dict()
    if key is not None:
        tunnel['_key'] = key
    if sidlist_lr is not None:
        tunnel['sidlist_lr'] = sidlist_lr
    if sidlist_rl is not None:
        tunnel['sidlist_rl'] = sidlist_rl
    if dest_lr is not None:
        tunnel['dest_lr'] = dest_lr
    if dest_rl is not None:
        tunnel['dest_rl'] = dest_rl
    if localseg_lr is not None:
        tunnel['localseg_lr'] = localseg_lr
    if localseg_rl is not None:
        tunnel['localseg_rl'] = localseg_rl
    if bsid_addr is not None:
        tunnel['bsid_addr'] = bsid_addr
    if fwd_engine is not None:
        tunnel['fwd_engine'] = fwd_engine
    tunnel['is_unidirectional'] = is_unidirectional
    # Remove the tunnel
    # Return True if the document matching the search criteria
    # has been removed, or False if the document was not found and
    # ignore_missing was set to True
    return srv6_tunnels.delete(document=tunnel,
                               ignore_missing=ignore_missing)
