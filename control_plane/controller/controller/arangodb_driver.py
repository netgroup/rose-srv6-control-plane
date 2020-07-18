#!/usr/bin/python

"""ArangoDB utilities"""

from arango import ArangoClient

USER = "root"
PASSWORD = "12345678"
ARANGO_URL = "http://localhost:8529"


def connect_arango(url):
    # Initialize the ArangoDB client.
    return ArangoClient(hosts=url)


def connect_db(client, db_name, username, password):
    # Connect to "db_name" database.
    return client.db(db_name, username=username, password=password)


def connect_srv6_usid_db(client, username, password):
    # Connect to "srv6_usid" database.
    return connect_db(client=client, db_name='srv6_usid',
                      username=username, password=password)


def init_srv6_usid_db(client, arango_url, arango_username, arango_password):
    # Connect to "_system" database as root user.
    # This returns an API wrapper for "_system" database.
    sys_db = connect_db(
        client=client,
        db_name='_system',
        username=arango_username,
        password=arango_password
    )
    # Reset database if already existing
    if sys_db.has_database('srv6_usid'):
        # sys_db.delete_database('srv6_pm')
        # sys_db.create_database('srv6_pm')
        pass
    else:
        sys_db.create_database('srv6_usid')


def init_usid_policies_collection(client, arango_url,
                                  arango_username, arango_password):
    # Connect to "srv6_usid" database as root user.
    # This returns an API wrapper for "srv6_pm" database.
    database = connect_srv6_usid_db(
        client=client,
        username=arango_username,
        password=arango_password
    )
    database = client.db('srv6_usid', username=arango_username,
                         password=arango_password)
    # Get the API wrapper for graph "usid_policies".
    if database.has_collection('usid_policies'):
        # usid_policies = database.collection('usid_policies')
        pass
    else:
        database.create_collection('usid_policies')


# ##############################################
# ############# Insert uSID policy #############
# ##############################################

def insert_usid_policy(database, lr_dst, rl_dst, lr_nodes, rl_nodes,
                       table=None, metric=None):
    '''
    Insert a uSID policy into a ArangoDB database
    '''
    # Get the uSID policy collection
    usid_policies = database.collection('usid_policies')
    # Insert the policy
    usid_policies.insert({
        'lr_dst': lr_dst,
        'rl_dst': rl_dst,
        'lr_nodes': lr_nodes,
        'rl_nodes': rl_nodes,
        'table': table,
        'table': metric,
    })


# ##############################################
# ############### Get uSID policy ##############
# ##############################################

def find_usid_policy(database, key=None, lr_dst=None,
                     rl_dst=None, lr_nodes=None, rl_nodes=None,
                     table=None, metric=None):
    '''
    Find a uSID policy in a database
    '''
    # Get the uSID policy collection
    usid_policies = database.collection('usid_policies')
    # Dict representation of the policy
    policy = dict()
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
    if key is not None:
        policy['_key'] = str(key)
    # Find the policy
    return usid_policies.find(policy)


# ##############################################
# ############# Update uSID policy #############
# ##############################################

def update_usid_policy(database, lr_dst, rl_dst, lr_nodes, rl_nodes,
                       table=None, metric=None):
    '''
    Update a uSID policy into a ArangoDB database
    '''
    # Not yet implemented


# ##############################################
# ############# Delete uSID policy #############
# ##############################################

def delete_usid_policy(database, key=None, lr_dst=None,
                       rl_dst=None, lr_nodes=None, rl_nodes=None,
                       table=None, metric=None):
    '''
    Insert a uSID policy into a ArangoDB database
    '''
    # Get the uSID policy collection
    usid_policies = database.collection('usid_policies')
    # Dict representation of the policy
    policy = dict()
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
    if key is not None:
        policy['_key'] = key
    # Remove the policy
    return usid_policies.delete(policy)
