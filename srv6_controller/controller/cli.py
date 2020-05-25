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
# Implementation of a CLI for the SRv6 Controller
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


import os

# Activate virtual environment if a venv path has been specified in .venv
# This must be executed only if this file has been executed as a
# script (instead of a module)
if __name__ == '__main__':
    # Check if .venv file exists
    if os.path.exists('.venv'):
        with open('.venv', 'r') as venv_file:
            # Get virtualenv path from .venv file
            venv_path = venv_file.read().rstrip()
        # Get path of the activation script
        venv_path = os.path.join(venv_path, 'bin/activate_this.py')
        if not os.path.exists(venv_path):
            print('Virtual environment path specified in .venv '
                  'points to an invalid path\n')
            exit(-2)
        with open(venv_path) as f:
            # Read the activation script
            code = compile(f.read(), venv_path, 'exec')
            # Execute the activation script to activate the venv
            exec(code, {'__file__': venv_path})


import fire

import utils
import srv6_controller
import ti_extraction


def handle_srv6_path(op, grpc_address, grpc_port, destination, segments="",
                     device='', encapmode="encap", table=-1, metric=-1):
    with srv6_controller.get_grpc_session(grpc_address, grpc_port) as channel:
        res = srv6_controller.handle_srv6_path(
            op=op,
            channel=channel,
            destination=destination,
            segments=segments.split(','),
            device=device,
            encapmode=encapmode,
            table=table,
            metric=metric
        )
        if res == 0:
            print('OK')
        else:
            print('Error')


def handle_srv6_behavior(op, grpc_address, grpc_port, segment, action='',
                         device='', table=-1, nexthop="", lookup_table=-1,
                         interface="", segments="", metric=-1):
    with srv6_controller.get_grpc_session(grpc_address, grpc_port) as channel:
        res = srv6_controller.handle_srv6_behavior(
            op=op,
            channel=channel,
            segment=segment,
            action=action,
            device=device,
            table=table,
            nexthop=nexthop,
            lookup_table=lookup_table,
            interface=interface,
            segments=segments.split(','),
            metric=metric
        )
        if res == 0:
            print('OK')
        else:
            print('Error')


def extract_topo_from_isis(isis_nodes, nodes_yaml, edges_yaml, verbose=False):
    srv6_controller.extract_topo_from_isis(
        isis_nodes=isis_nodes.split(','),
        nodes_yaml=nodes_yaml,
        edges_yaml=edges_yaml,
        verbose=verbose
    )


def load_topo_on_arango(arango_url, user, password,
                        nodes_yaml, edges_yaml, verbose=False):
    srv6_controller.load_topo_on_arango(
        arango_url=arango_url,
        user=user,
        password=password,
        nodes_yaml=nodes_yaml,
        edges_yaml=edges_yaml,
        verbose=verbose)


def extract_topo_from_isis_and_load_on_arango(isis_nodes, arango_url=None,
                                              arango_user=None,
                                              arango_password=None,
                                              nodes_yaml=None, edges_yaml=None,
                                              period=0, verbose=False):
    srv6_controller.extract_topo_from_isis_and_load_on_arango(
        isis_nodes=isis_nodes,
        arango_url=arango_url,
        arango_user=arango_user,
        arango_password=arango_password,
        nodes_yaml=nodes_yaml,
        edges_yaml=edges_yaml,
        period=period,
        verbose=verbose
    )


def topology_information_extraction_isis(routers, period, isisd_pwd,
                                         topo_file_json=None,
                                         nodes_file_yaml=None,
                                         edges_file_yaml=None,
                                         topo_graph=None, verbose=False):
    ti_extraction.topology_information_extraction_isis(
        routers=routers,
        period=period,
        isisd_pwd=isisd_pwd,
        topo_file_json=topo_file_json,
        nodes_file_yaml=nodes_file_yaml,
        edges_file_yaml=edges_file_yaml,
        topo_graph=topo_graph,
        verbose=verbose
    )


if __name__ == '__main__':
    srv6 = {
        'path': handle_srv6_path,
        'behavior': handle_srv6_behavior
    }

    topo_utils = {
        'extract_from_isis': extract_topo_from_isis,
        'load_on_arango': load_topo_on_arango
    }

    fire.Fire({
        'srv6': srv6,
        'topo_utils': topo_utils
    })
