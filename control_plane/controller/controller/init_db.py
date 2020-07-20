#!/usr/python

import os

from controller import arangodb_driver


# ArangoDB params
ARANGO_URL = os.getenv('ARANGO_URL', 'http://localhost:8529')
ARANGO_USER = os.getenv('ARANGO_USER', 'root')
ARANGO_PASSWORD = os.getenv('ARANGO_PASSWORD', '12345678')


if __name__ == '__main__':
    # Connect to ArangoDB
    client = arangodb_driver.connect_arango(url=ARANGO_URL)
    # Initialize SRv6 uSID database
    arangodb_driver.init_srv6_usid_db(
        client=client,
        arango_url=ARANGO_URL,
        arango_username=ARANGO_USER,
        arango_password=ARANGO_PASSWORD
    )
    # Initialize uSID policies collection
    arangodb_driver.init_usid_policies_collection(
        client=client,
        arango_url=ARANGO_URL,
        arango_username=ARANGO_USER,
        arango_password=ARANGO_PASSWORD
    )
